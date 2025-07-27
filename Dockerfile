# Dockerfile

# Use an official Python runtime as a parent image.
FROM python:3.10-slim-buster

# Set the working directory in the container to /app.
WORKDIR /app

# Set environment variables for NLTK data paths and unstructured's NLTK data.
# This tells NLTK itself and the unstructured library where to find/store NLTK data.
ENV NLTK_DATA /app/nltk_data
ENV UNSTRUCTURED_NLTK_DOWNLOAD_PATH /app/nltk_data # NEW: Explicitly for unstructured

# Create the directory for NLTK data.
RUN mkdir -p /app/nltk_data

# Copy the requirements.txt file into the container at /app.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# --- CRITICAL NLTK DATA DOWNLOAD FIX (Ensures data is present before app starts) ---
# Download necessary NLTK data during the Docker build process to the /app/nltk_data directory.
# This ensures they are available at runtime and prevents runtime download attempts/permission errors.
RUN python -c "import nltk; nltk.data.path.append('/app/nltk_data'); nltk.download('punkt', download_dir='/app/nltk_data', quiet=True)"
RUN python -c "import nltk; nltk.data.path.append('/app/nltk_data'); nltk.download('averaged_perceptron_tagger', download_dir='/app/nltk_data', quiet=True)"
# --- END CRITICAL NLTK DATA DOWNLOAD FIX ---

# Copy the rest of your application code into the container at /app.
COPY . .

# Expose port 8000.
EXPOSE 8000

# Define the command to run your application when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]