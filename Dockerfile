# Use Python 3.9 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip freeze

# Copy application code
COPY src/ ./src/
COPY .streamlit/ ./.streamlit/
COPY misc/ ./misc/

# Create directories
RUN mkdir -p /app/data ./logs

# Expose the Cloud Run port (8080 by convention)
EXPOSE 8080
EXPOSE 8501

# Optional: Healthcheck on $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f https://wayfarer-ai-backend-111720869272.us-central1.run.app:$PORT/_stcore/health || exit 1

# Run the Streamlit app, bound to Cloud Run's $PORT
CMD ["sh", "-c", "streamlit run src/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
