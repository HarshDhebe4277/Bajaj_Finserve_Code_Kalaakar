# Dockerfile

# Use an official Python runtime as a parent image.
FROM python:3.10-slim-buster

# Set the working directory in the container to /app.
WORKDIR /app

# Copy the requirements.txt file into the container at /app.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# --- CRITICAL FIX: PRE-CACHE SENTENCE-TRANSFORMERS MODEL DURING BUILD ---
# This ensures the model is present in the expected cache location before the app runs.
# It bypasses runtime permission issues for model download.

# Set the cache directory for Hugging Face models within the writable /app directory.
# This variable is respected by Hugging Face libraries like transformers and sentence-transformers.
ENV TRANSFORMERS_CACHE /app/.cache/huggingface/hub/
ENV HF_HOME /app/.cache/huggingface/ # Ensure HF_HOME is also pointing to the parent cache dir

# Create the Hugging Face cache directory.
RUN mkdir -p /app/.cache/huggingface/hub/

# Download the specific sentence-transformers model directly during the build.
# This ensures it's available and correctly placed without runtime write permissions issues.
# 'resume_download=True' helps with large files or intermittent network issues.
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sentence-transformers/all-MiniLM-L6-v2', cache_dir='/app/.cache/huggingface/hub', resume_download=True)"
# --- END CRITICAL FIX ---

# Copy the rest of your application code into the container at /app.
COPY . .

# Expose port 8000.
EXPOSE 8000

# Define the command to run your application when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]