# 🛠️ Troubleshooting Guide

## Docker Build Issues

### ❌ Problem: "No matching distribution found for numpy==X.X.X"
**Cause**: Package version doesn't exist or isn't compatible with the Python version.

**Solutions**:
1. Use the updated `requirements.txt` with version ranges
2. Try `requirements-minimal.txt` for basic functionality:
   ```dockerfile
   COPY requirements-minimal.txt requirements.txt
   ```

### ❌ Problem: InsightFace installation fails
**Cause**: Missing system dependencies or compilation issues.

**Solutions**:
1. Ensure Dockerfile includes all system packages:
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       build-essential \
       cmake \
       libopenblas-dev \
       liblapack-dev
   ```

2. Use pre-compiled wheels:
   ```dockerfile
   RUN pip install --find-links https://download.pytorch.org/whl/torch_stable.html insightface
   ```

### ❌ Problem: OpenCV import fails
**Cause**: Missing system libraries for OpenCV.

**Solution**: Add to Dockerfile:
```dockerfile
RUN apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1
```

## Hugging Face Spaces Issues

### ❌ Problem: "Application startup timeout"
**Cause**: Model loading takes too long.

**Solutions**:
1. Upgrade to CPU Upgrade or GPU hardware
2. Add loading optimization to app.py:
   ```python
   @st.cache_resource
   def load_model():
       # Model loading code
   ```

### ❌ Problem: "Port not accessible"
**Cause**: Wrong port configuration.

**Solution**: Ensure README.md has:
```yaml
---
sdk: docker
app_port: 7860
---
```

## Alternative Configurations

### Option 1: Use pre-built base image
```dockerfile
FROM python:3.9-slim

# Use a requirements.txt with known working versions
COPY requirements-minimal.txt requirements.txt
```

### Option 2: Multi-stage build
```dockerfile
# Build stage
FROM python:3.9 as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage  
FROM python:3.9-slim
COPY --from=builder /root/.local /root/.local
```

### Option 3: Use Streamlit SDK instead of Docker
Update README.md:
```yaml
---
sdk: streamlit
sdk_version: 1.28.1
app_file: app.py
---
```

## Quick Fixes

### Test locally first:
```bash
# Test Docker build
docker build -t test-app .

# If build fails, try minimal version
docker build -f Dockerfile.minimal -t test-app .
```

### Check package compatibility:
```bash
# In Python environment
pip install --dry-run -r requirements.txt
```

### Debug container:
```bash
# Run container interactively
docker run -it --entrypoint /bin/bash your-image

# Check what went wrong
cat /var/log/dpkg.log
pip list
```

## Working Fallback Configuration

If all else fails, use this minimal setup:

**requirements-simple.txt**:
```
streamlit==1.28.1
opencv-python-headless==4.5.5.64
numpy==1.21.6
pillow==9.5.0
```

**Dockerfile-simple**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements-simple.txt requirements.txt
RUN pip install -r requirements.txt
COPY app.py .
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
```

This should work with basic functionality (without InsightFace initially).
