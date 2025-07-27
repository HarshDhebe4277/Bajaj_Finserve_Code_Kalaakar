# src/vector_db/faiss_manager.py

import faiss
import numpy as np
from typing import List, Dict, Any, Optional

class FAISSManager:
    _instance = None
    _index = None
    _texts = [] # Store original text chunks corresponding to FAISS indices
    _metadatas = [] # Store metadata for each chunk (e.g., source, page number)

    def __new__(cls, dimension: int = 384): # Default dimension for all-MiniLM-L6-v2
        """Ensures only one instance of FAISSManager is created (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(FAISSManager, cls).__new__(cls)
            print(f"Initializing FAISS index with dimension: {dimension}...")
            # FAISS IndexFlatL2 is a simple L2 distance (Euclidean) based index
            # This is suitable for semantic search with normalized embeddings (which all-MiniLM-L6-v2 provides).
            cls._index = faiss.IndexFlatL2(dimension)
            cls._texts = []
            cls._metadatas = []
            print("FAISS index initialized successfully.")
        return cls._instance

    def add_documents(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """
        Adds document embeddings and their corresponding texts/metadatas to the FAISS index.
        """
        if not embeddings or not texts:
            print("No embeddings or texts to add.")
            return

        if len(embeddings) != len(texts):
            raise ValueError("Number of embeddings and texts must match.")
        
        # Convert list of lists to a numpy array, ensure float32 type
        embeddings_np = np.array(embeddings).astype('float32')

        # Add embeddings to the FAISS index
        self._index.add(embeddings_np)

        # Store the original texts and metadatas in parallel lists, indexed by FAISS internal IDs
        # For simplicity, FAISS's internal IDs correspond to the order of addition (0, 1, 2, ...)
        # So we can just append to our lists.
        self._texts.extend(texts)
        if metadatas:
            if len(metadatas) != len(texts):
                raise ValueError("Number of metadatas and texts must match if provided.")
            self._metadatas.extend(metadatas)
        else:
            # If no specific metadata is provided, append empty dicts
            self._metadatas.extend([{} for _ in texts])
        
        print(f"Added {len(embeddings)} documents to FAISS index. Total documents: {self._index.ntotal}.")


    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search in the FAISS index.
        
        Args:
            query_embedding (List[float]): The embedding of the query.
            k (int): The number of nearest neighbors to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing 'text', 'metadata', and 'distance'.
        """
        if self._index.ntotal == 0:
            print("FAISS index is empty. No search performed.")
            return []

        # Convert query embedding to a numpy array of shape (1, dimension) and float32 type
        query_embedding_np = np.array([query_embedding]).astype('float32')

        # Perform the search
        distances, indices = self._index.search(query_embedding_np, k)

        results = []
        # distances and indices are 2D arrays (because we can search multiple queries at once)
        # We're searching one query, so we take the first row [0]
        for i, idx in enumerate(indices[0]):
            if idx == -1: # -1 means no valid result found
                continue
            
            # Retrieve the corresponding text and metadata using the stored index
            text = self._texts[idx]
            metadata = self._metadatas[idx] if idx < len(self._metadatas) else {} # Ensure index is valid
            distance = distances[0][i]

            results.append({
                "text": text,
                "metadata": metadata,
                "distance": float(distance) # Convert numpy float to standard float
            })
        return results

    def reset_index(self):
        """Resets the FAISS index and stored texts/metadatas."""
        self._index.reset()
        self._texts = []
        self._metadatas = []
        print("FAISS index reset.")