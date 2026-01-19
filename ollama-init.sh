#!/bin/bash

# ============================================
# LEARNING: Startup Script
# ============================================
# This script runs when the Ollama container starts
# It downloads the Mistral model if it's not already present
# 
# Why a script? Because we need to:
# 1. Wait for Ollama service to be ready
# 2. Download the model (only once)
# 3. Keep the container running

echo "🚀 Starting Ollama service..."

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if Mistral model is already downloaded
if ! ollama list | grep -q "mistral"; then
    echo "📥 Downloading Mistral model (this may take a few minutes)..."
    ollama pull mistral
    echo "✅ Mistral model downloaded successfully!"
else
    echo "✅ Mistral model already present"
fi

# Keep the container running
echo "🎉 Ollama is ready!"
wait
