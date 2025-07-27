# main.py
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import asyncio # NEW: Import asyncio for concurrent tasks
from starlette.concurrency import run_in_threadpool

# Import our utility functions
from src.utils.document_loader import extract_text_from_document
from src.utils.text_splitter import split_text_into_chunks
from src.embeddings.embedding_model import EmbeddingModel
from src.vector_db.faiss_manager import FAISSManager
from src.llm.groq_llm_client import GroqLLMClient

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="HackRx LLM-Powered Query Retrieval System",
    description="An intelligent system for processing documents and answering contextual queries.",
    version="1.0.0"
)

# Global instances of our components - loaded once on app startup
embedding_generator = EmbeddingModel()
faiss_manager = FAISSManager(dimension=384) # Dimension must match embedding model
groq_llm_client = GroqLLMClient()

# --- Configuration ---
REQUIRED_AUTH_TOKEN = os.getenv("HACKRX_AUTH_TOKEN", "ae3c781e80a6b6d0ec74b60585efe1b7c06c17b09b6b332f076692de6dcfd64b")

# --- Pydantic Models for Request and Response ---
class RunRequest(BaseModel):
    documents: str # URL to the document blob
    questions: List[str]

class RunResponse(BaseModel):
    answers: List[str]

# --- API Endpoints ---
@app.post("/api/v1/hackrx/run", response_model=RunResponse, status_code=status.HTTP_200_OK)
async def run_hackrx_submission(request: Request, payload: RunRequest):
    """
    Processes document(s) and answers a list of questions using an LLM-powered retrieval system.
    """
    # Basic Bearer Token Authentication Check
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    try:
        token_type, token = auth_header.split(" ")
        if token_type.lower() != "bearer" or token != REQUIRED_AUTH_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )

    # --- Document Ingestion and Text Extraction ---
    document_url = payload.documents
    print(f"Attempting to extract text from document: {document_url}")
    document_text = await run_in_threadpool(extract_text_from_document, document_url)

    if document_text is None or not document_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not download or extract text from the provided document URL. "
                   "Ensure it's a valid PDF, DOCX, or email link."
        )

    print(f"Successfully extracted text (first 500 chars): {document_text[:500]}...")
    print(f"Total extracted text length: {len(document_text)} characters.")

    # --- Text Chunking ---
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    text_chunks = await run_in_threadpool(
        split_text_into_chunks,
        document_text,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    if not text_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not split the document text into chunks."
        )

    print(f"Document split into {len(text_chunks)} chunks.")

    # --- Embedding Generation for Chunks ---
    print(f"Generating embeddings for {len(text_chunks)} chunks...")
    chunk_embeddings = await run_in_threadpool(embedding_generator.get_embeddings, text_chunks)
    print(f"Generated {len(chunk_embeddings)} embeddings, each with dimension {len(chunk_embeddings[0]) if chunk_embeddings else 0}.")

    # --- FAISS Indexing ---
    faiss_manager.reset_index() # Reset for each new document
    print("FAISS index reset for new document.")
    await run_in_threadpool(faiss_manager.add_documents, chunk_embeddings, text_chunks)
    print(f"Chunks indexed into FAISS. Total indexed documents: {faiss_manager._index.ntotal}")

    # --- Semantic Search and LLM Integration for Each Question (Concurrent) ---
    # This is the NEWLY MODIFIED SECTION for concurrency
    TOP_K_RETRIEVAL = 10 # Reduced back to 5 for better token efficiency and potential latency

    llm_tasks = [] # List to hold all our asynchronous LLM tasks
    for question in payload.questions:
        print(f"\nPreparing task for question: '{question}'")
        
        # Generate embedding for the question
        query_embedding = await run_in_threadpool(embedding_generator.get_embeddings, [question])
        query_embedding_single = query_embedding[0] 

        # Perform semantic search in FAISS
        search_results = await run_in_threadpool(
            faiss_manager.search,
            query_embedding_single,
            k=TOP_K_RETRIEVAL
        )

        if not search_results:
            print(f"No relevant chunks found for question: '{question}'. Creating fallback task.")
            # If no chunks, create a task that immediately returns the 'not found' message
            llm_tasks.append(asyncio.create_task(asyncio.sleep(0, result=f"Information for '{question}' not found in document.")))
            continue # Move to the next question

        retrieved_contexts = [result['text'] for result in search_results]
        print(f"Retrieved {len(retrieved_contexts)} relevant chunks for question.")
        
        # --- Debugging Line (Keep for now, but remove before final submission) ---
        print("--- Retrieved Contexts for this Question ---")
        for i, chunk_text in enumerate(retrieved_contexts):
            print(f"Chunk {i+1} (first 200 chars): {chunk_text[:200]}...")
        print("--- End Retrieved Contexts ---")
        # --- End Debugging Line ---

        # Create an asynchronous task (coroutine) for each LLM call
        # These tasks will run concurrently when awaited by asyncio.gather
        llm_tasks.append(
            asyncio.create_task(
                groq_llm_client.generate_answer(question, retrieved_contexts)
            )
        )

    print(f"\nInitiating concurrent LLM calls for {len(llm_tasks)} questions...")
    # Run all LLM tasks concurrently and gather their results
    final_answers = await asyncio.gather(*llm_tasks)
    print("All LLM calls completed.")

    # Return the collected answers
    return RunResponse(answers=final_answers)

# --- Health Check Endpoint (Optional but good practice) ---
@app.get("/api/v1/health")
async def health_check():
    """
    Checks the health of the API.
    """
    return {"status": "ok", "message": "API is running smoothly!"}