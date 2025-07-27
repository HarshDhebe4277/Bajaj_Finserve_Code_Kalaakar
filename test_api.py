# test_api.py

import httpx
import asyncio
import os
from dotenv import load_dotenv
import time

# Load environment variables (including your HACKRX_AUTH_TOKEN)
load_dotenv()

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/v1/hackrx/run"
AUTH_TOKEN = os.getenv("HACKRX_AUTH_TOKEN")

if not AUTH_TOKEN:
    print("Error: HACKRX_AUTH_TOKEN environment variable not set. Please check your .env file.")
    exit(1)

# List of all 5 sample document URLs
SAMPLE_DOCUMENT_URLS = [
    # "https://hackrx.in/policies/HDFHLIP23024V072223.pdf",
    # "https://hackrx.in/policies/ICIHLIP22012V012223.pdf",
    "https://hackrx.in/policies/EDLHLGA23009V012223.pdf",
    # "https://hackrx.in/policies/CHOTGDP23004V012223.pdf",
    # "https://hackrx.in/policies/BAJHLIP23020V012223.pdf"
]

# A comprehensive list of questions (you can expand this as needed)
# Including the ones from the problem statement for policy.pdf
SAMPLE_QUESTIONS = [
    # Questions about Air Ambulance Cover
    "What services does the Air Ambulance cover provide?",
    "What is the maximum distance covered for air ambulance services, and how is it calculated if exceeded?",
    "Under what specific medical conditions or emergencies can air ambulance services be availed?",
    "Are there any transfers explicitly excluded from the Air Ambulance cover?",
    "What is the maximum financial liability for claims under the Air Ambulance Benefit?",

    # Questions about Well Mother Cover
    "What type of medical care is covered under the 'Well Mother Cover'?",
    "What are the different periods an insured can choose for the 'Well Mother Cover'?",
    "What are some exclusions under the 'Well Mother Cover'?",

    # Questions about Healthy Baby Expenses / Well Baby Care
    "What expenses are covered under 'Healthy baby expenses / well baby care expenses'?",
    "What does 'Routine Preventive Care Services' for a new born baby typically include?",
]

async def test_api_with_documents():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    async with httpx.AsyncClient(timeout=240.0) as client: # Keep increased timeout
        total_time_taken = 0
        successful_requests = 0
        total_questions_answered = 0

        for doc_url in SAMPLE_DOCUMENT_URLS:
            print(f"\n--- Testing with Document: {doc_url} ---")
            payload = {
                "documents": doc_url,
                "questions": SAMPLE_QUESTIONS
            }

            start_time = time.time()
            try:
                response = await client.post(BASE_URL, headers=headers, json=payload)
                end_time = time.time()
                request_time = end_time - start_time
                total_time_taken += request_time

                print(f"Status Code: {response.status_code}")
                print(f"Response Time: {request_time:.2f} seconds")

                if response.status_code == 200:
                    successful_requests += 1
                    response_data = response.json()
                    if "answers" in response_data and isinstance(response_data["answers"], list):
                        print(f"Received {len(response_data['answers'])} answers.")
                        total_questions_answered += len(response_data['answers'])
                        for i, answer in enumerate(response_data["answers"]):
                            print(f"  Q{i+1}: {SAMPLE_QUESTIONS[i]}")
                            print(f"  A{i+1}: {answer[:200]}..." if len(answer) > 200 else f"  A{i+1}: {answer}")
                            print("-" * 50)
                    else:
                        print("Warning: 'answers' key not found or not a list in response.")
                        print(response_data)
                else:
                    print(f"Error Response: {response.text}")
            except httpx.ConnectError as e:
                print(f"Connection Error: Ensure your FastAPI server is running at {BASE_URL}. Detail: {e}")
                break
            except httpx.TimeoutException as e:
                print(f"Timeout Error: Request timed out after {client.timeout.connect}s. Detail: {e}")
                print(f"Consider increasing the timeout in httpx.AsyncClient if this persists.")
            except httpx.HTTPStatusError as e:
                print(f"HTTP Status Error: Received status {e.response.status_code} for {e.request.url}. Detail: {e}")
                print(f"Response: {e.response.text}")
            except Exception as e:
                print(f"An unexpected Python error occurred during request: {e}")
                print(f"Response (if any): {response.text if 'response' in locals() else 'No response object.'}")
            
            # --- NEW ADDITION FOR RATE LIMIT MANAGEMENT ---
            # Pause for 60 seconds after processing each document, except the last one
            if doc_url != SAMPLE_DOCUMENT_URLS[-1]:
                print(f"\nPausing for 60 seconds to respect Groq API rate limits before next document...")
                await asyncio.sleep(60) # Pause for 60 seconds
            # --- END NEW ADDITION ---

        # This summary block should be outside the for loop
        if successful_requests > 0:
            print("\n--- Summary ---")
            print(f"Total documents tested: {len(SAMPLE_DOCUMENT_URLS)}")
            print(f"Successful API calls: {successful_requests}")
            print(f"Total questions processed: {total_questions_answered}")
            print(f"Average response time per document: {total_time_taken / successful_requests:.2f} seconds")
            print("Remember: Avg response time for evaluation is PER CALL, not total.")
        else:
            print("\nNo successful requests were made.")

if __name__ == "__main__":
    print("Starting API testing...")
    asyncio.run(test_api_with_documents())
    print("API testing complete.")