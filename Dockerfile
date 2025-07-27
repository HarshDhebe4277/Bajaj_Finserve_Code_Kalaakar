# Dockerfile

# Use an official Python runtime as a parent image.
FROM python:3.10-slim-buster

# Set the working directory in the container to /app.
WORKDIR /app

# --- NEW LINES FOR HUGGING FACE CACHE ---
# Set environment variable to tell Hugging Face Hub where to store cached models.
# This ensures it writes to a writable directory inside our app.
ENV HF_HOME /app/.cache/huggingface
# Create the directory for Hugging Face cache.
RUN mkdir -p /app/.cache/huggingface
# --- END NEW LINES ---

# Copy the requirements.txt file into the container at /app.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app.
COPY . .

# Expose port 8000.
EXPOSE 8000

# Define the command to run your application when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]