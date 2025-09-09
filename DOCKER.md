# 🐳 Docker Setup for AI Trip Planner

This guide explains how to run the AI Trip Planner application using Docker and Docker Compose.

## 📋 Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git

## 🚀 Quick Start

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd streamlit-vertexai-demo
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Run with Docker Compose
```bash
# Make the script executable
chmod +x docker-run.sh

# Run the application
./docker-run.sh
```

Or manually:
```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 4. Access the Application
Open your browser and go to: `http://localhost:8501`

## 🏗️ Docker Architecture

### Development Setup
- **Base Image**: Python 3.9-slim
- **Port**: 8501
- **Volumes**: Data persistence for SQLite database
- **Health Check**: Built-in Streamlit health endpoint

### Production Setup
- **Multi-stage Build**: Optimized image size
- **Non-root User**: Enhanced security
- **PostgreSQL**: Production database
- **Redis**: Session management
- **Nginx**: Reverse proxy and load balancing

## 📁 Docker Files

### Core Files
- `Dockerfile` - Development Docker image
- `Dockerfile.prod` - Production Docker image
- `docker-compose.yml` - Development setup
- `docker-compose.prod.yml` - Production setup
- `.dockerignore` - Files to exclude from build

### Configuration Files
- `.streamlit/config.toml` - Streamlit configuration
- `nginx.conf` - Nginx reverse proxy config
- `.env` - Environment variables

## 🔧 Configuration Options

### Environment Variables
```bash
# Google Cloud Configuration
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro

# Database Configuration (Production)
POSTGRES_PASSWORD=your-secure-password

# Application Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Volume Mounts
- `./data:/app/data` - Database and application data
- `./logs:/app/logs` - Application logs
- `./credentials:/app/credentials` - Google Cloud credentials

## 🚀 Deployment Options

### 1. Local Development
```bash
# Simple development setup
docker-compose up --build

# With live reload (if using volume mounts)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### 2. Production Deployment
```bash
# Production setup with PostgreSQL
docker-compose -f docker-compose.prod.yml up -d

# Scale the application
docker-compose -f docker-compose.prod.yml up -d --scale trip-planner=3
```

### 3. Cloud Deployment

#### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-trip-planner
gcloud run deploy --image gcr.io/PROJECT-ID/ai-trip-planner --platform managed
```

#### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t ai-trip-planner .
docker tag ai-trip-planner:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-trip-planner:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-trip-planner:latest
```

#### Azure Container Instances
```bash
# Build and push to Azure Container Registry
az acr build --registry myregistry --image ai-trip-planner .
az container create --resource-group myResourceGroup --name ai-trip-planner --image myregistry.azurecr.io/ai-trip-planner:latest --ports 8501
```

## 🛠️ Development Commands

### Basic Docker Commands
```bash
# Build image
docker build -t ai-trip-planner .

# Run container
docker run -p 8501:8501 ai-trip-planner

# Run with environment file
docker run -p 8501:8501 --env-file .env ai-trip-planner

# Run with volume mounts
docker run -p 8501:8501 -v $(pwd)/data:/app/data ai-trip-planner
```

### Docker Compose Commands
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and start
docker-compose up --build

# Scale services
docker-compose up --scale trip-planner=3
```

### Debugging Commands
```bash
# Access container shell
docker-compose exec trip-planner bash

# View container logs
docker-compose logs trip-planner

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart trip-planner
```

## 🔒 Security Considerations

### Production Security
- Use non-root user in container
- Keep base images updated
- Use secrets management for credentials
- Enable HTTPS with SSL certificates
- Regular security scans

### Credential Management
```bash
# Mount credentials as read-only
docker run -v /path/to/credentials:/app/credentials:ro ai-trip-planner

# Use Docker secrets (Docker Swarm)
echo "your-secret" | docker secret create vertex_ai_key -
```

## 📊 Monitoring and Logging

### Health Checks
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' ai-trip-planner

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' ai-trip-planner
```

### Log Management
```bash
# View logs with timestamps
docker-compose logs -f --timestamps

# Save logs to file
docker-compose logs > app.log

# Rotate logs (add to docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>

# Or use different port
docker run -p 8502:8501 ai-trip-planner
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data
```

#### Container Won't Start
```bash
# Check logs
docker-compose logs trip-planner

# Check container status
docker-compose ps

# Rebuild from scratch
docker-compose down -v
docker-compose up --build --force-recreate
```

#### Database Connection Issues
```bash
# Check if database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U trip_user -d trip_planner
```

## 📈 Performance Optimization

### Resource Limits
```yaml
# Add to docker-compose.yml
services:
  trip-planner:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Caching
```dockerfile
# Optimize Dockerfile for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Build and Deploy
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t ai-trip-planner .
      - name: Run tests
        run: docker run --rm ai-trip-planner python -m pytest
      - name: Deploy
        run: docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)

---

**Happy Containerizing! 🐳**
