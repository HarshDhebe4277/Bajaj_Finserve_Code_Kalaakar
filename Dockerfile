# Dockerfile

# Use an official Python runtime as a parent image.
# We choose a slim-buster image for a smaller footprint, suitable for deployments.
FROM python:3.10-slim-buster

# Set the working directory in the container to /app.
# All subsequent commands will be executed relative to this directory.
WORKDIR /app

# Copy the requirements.txt file into the container at /app.
# This step is done separately to leverage Docker's build cache.
# If only requirements.txt changes, this layer and subsequent layers are rebuilt.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
# --no-cache-dir: Prevents pip from storing cached wheels, reducing image size.
# -r requirements.txt: Installs packages from the requirements file.
# Note: This might still be the largest step due to torch and faiss-cpu binaries.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app.
# This copies main.py, your src/ directory, Procfile, etc.
COPY . .

# Expose port 8000. This informs Docker that the container listens on the specified network port at runtime.
# This is mainly for documentation and doesn't publish the port without -p or --publish.
EXPOSE 8000

# Define the command to run your application when the container starts.
# This command runs Uvicorn, serving your FastAPI app (`app` from `main.py`).
# --host 0.0.0.0: Makes the application accessible from outside the container.
# --port 8000: Specifies the port Uvicorn should listen on.
# Note: For platforms like Render or Railway, they often override $PORT or auto-map to 8000.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]