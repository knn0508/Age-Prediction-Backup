@echo off
REM Quick test script for Docker deployment on Windows

echo 🧪 Testing Docker Setup for Age Detection App
echo ==============================================

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not in PATH
    echo Please install Docker Desktop to test locally
    pause
    exit /b 1
)

echo ✅ Docker is available

REM Build the Docker image
echo 🔨 Building Docker image...
docker build -t age-detection-app-test .
if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    pause
    exit /b 1
)

echo ✅ Docker image built successfully

echo.
echo 🎉 Docker setup is ready!
echo.
echo To test locally:
echo docker run -p 7860:7860 age-detection-app-test
echo.
echo Then open: http://localhost:7860
echo.
echo For Hugging Face Spaces deployment:
echo 1. Create a new Space with SDK=Docker
echo 2. Push all files to the Space repository
echo 3. HF will automatically build and deploy
echo.
pause
