# ============================================
# LEARNING: What is a Dockerfile?
# ============================================
# A Dockerfile is a recipe that tells Docker how to build your application.
# Each line is an instruction that Docker executes step-by-step.
# Think of it like a cooking recipe: ingredients + steps = final dish

# ============================================
# Step 1: Choose a base image
# ============================================
# FROM: This is like choosing your starting point
# We use python:3.12-slim which is:
# - Official Python image (trusted by millions)
# - Version 3.12 (matches your local Python)
# - "slim" = smaller size (no unnecessary tools)
FROM python:3.12-slim

# ============================================
# Step 2: Set working directory
# ============================================
# WORKDIR: Creates a folder inside the container and moves into it
# Like doing: mkdir /app && cd /app
# All future commands run from this directory
WORKDIR /app

# ============================================
# Step 3: Install system dependencies
# ============================================
# RUN: Executes a command during the build process
# We need these for PDF processing and Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Step 4: Copy and install Python dependencies
# ============================================
# COPY: Copies files from your computer into the container
# We copy requirements.txt FIRST (before code) because:
# - Docker caches each step
# - Dependencies change less often than code
# - This makes rebuilds faster!
COPY requirements.txt .

# Install Python packages
# --no-cache-dir: Don't save downloaded packages (saves space)
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Step 5: Copy application code
# ============================================
# Now we copy the actual backend code
# This happens AFTER installing dependencies for caching efficiency
COPY . .

# ============================================
# Step 6: Create directories for data
# ============================================
# These will store uploaded files and the vector database
RUN mkdir -p data_uploaded faiss_index

# ============================================
# Step 7: Expose the port
# ============================================
# EXPOSE: Documents which port the app uses
# This is like putting a sign on a door: "Service runs on port 8000"
# Note: This doesn't actually open the port, docker-compose does that
EXPOSE 8000

# ============================================
# Step 8: Define the startup command
# ============================================
# CMD: The command to run when the container starts
# This is what actually launches your FastAPI server
# --host 0.0.0.0: Listen on all network interfaces (allows external connections)
# --port 8000: The port to run on
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
