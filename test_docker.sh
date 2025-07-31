#!/bin/bash
# Quick test script for Docker deployment

echo "🧪 Testing Docker Setup for Age Detection App"
echo "=============================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop to test locally"
    exit 1
fi

echo "✅ Docker is available"

# Build the Docker image
echo "🔨 Building Docker image..."
if docker build -t age-detection-app-test .; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "🎉 Docker setup is ready!"
echo ""
echo "To test locally:"
echo "docker run -p 7860:7860 age-detection-app-test"
echo ""
echo "Then open: http://localhost:7860"
echo ""
echo "For Hugging Face Spaces deployment:"
echo "1. Create a new Space with SDK=Docker"
echo "2. Push all files to the Space repository"
echo "3. HF will automatically build and deploy"
