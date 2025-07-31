# 📁 Essential Files for Hugging Face Spaces Upload

## Required Files (Upload these manually):

### Core Application Files:
1. **app.py** - Main Streamlit application
2. **Dockerfile** - Docker container configuration  
3. **requirements.txt** - Python dependencies
4. **README.md** - App documentation with HF Spaces config
5. **start.sh** - Container startup script

### Configuration Files:
6. **.dockerignore** - Docker build optimization
7. **packages.txt** - System dependencies (optional backup)

### Optional Files:
8. **requirements-minimal.txt** - Fallback dependencies
9. **TROUBLESHOOTING.md** - Debug guide

## Files NOT needed on Hugging Face Spaces:
- .gitignore
- .gitattributes  
- test_docker.sh
- test_docker.bat
- test_setup.py
- SETUP_SUMMARY.md
- DEPLOYMENT_GUIDE.md

## Upload Steps:
1. Go to https://huggingface.co/spaces/knnnnn/age-predict
2. Click "Files" tab
3. Click "Add file" → "Upload files"  
4. Drag and drop the required files listed above
5. Commit the changes

## Important Notes:
- Make sure your README.md has the Docker SDK configuration:
  ```yaml
  ---
  sdk: docker
  app_port: 7860
  ---
  ```
- Hugging Face will automatically build the Docker container
- Check the "Logs" tab for any build errors
