#!/bin/bash

# Docker startup script for Hugging Face Spaces

echo "🚀 Starting Age Detection App in Docker..."

# Set environment variables for production
export PYTHONUNBUFFERED=1
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=7860
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Create necessary directories
mkdir -p /home/user/.insightface
mkdir -p /home/user/.streamlit

# Create Streamlit config
cat > /home/user/.streamlit/config.toml << EOF
[server]
headless = true
port = 7860
address = "0.0.0.0"
fileWatcherType = "none"

[browser]
gatherUsageStats = false

[theme]
base = "light"
EOF

echo "📊 Configuration complete. Starting Streamlit app..."

# Start the application
exec streamlit run app.py \
    --server.port=7860 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false
