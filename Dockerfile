# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip freeze

# Copy application code
COPY src/ ./src/ 
COPY .streamlit/ ./.streamlit/
#COPY credentials/ ./credentials/
COPY misc/ ./misc/

# Create directory for database and logs
RUN mkdir -p ./data ./logs

# Expose ports (local 8501, Cloud Run 8080)
EXPOSE 8501
EXPOSE 8080

# Health check uses $PORT (works for both local + Cloud Run)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/_stcore/health || exit 1

# Run the app: Cloud Run sets $PORT, local defaults to 8501
CMD ["sh", "-c", "streamlit run src/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
