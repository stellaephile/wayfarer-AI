#!/bin/bash

# Start script for Cloud Run
echo "Starting Wayfarer App..."

# Set environment variables
export STREAMLIT_SERVER_PORT=8080
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_SERVER_RUN_ON_SAVE=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Start Streamlit
echo "Starting Streamlit server..."
exec streamlit run src/app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --server.runOnSave=false --browser.gatherUsageStats=false
