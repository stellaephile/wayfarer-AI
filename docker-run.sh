#!/bin/bash

echo "🐳 AI Trip Planner Docker Setup"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs credentials

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.example .env
    echo "✅ Created .env file. You can edit it to add your Google Cloud credentials."
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

# Start the application
echo "🚀 Starting the application..."
echo "📱 Open your browser and go to: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

# Run the application
docker-compose up
