#!/bin/bash

# Google Cloud Deployment Script for Wayfarer App
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="trip-planner-demo-471815"
SERVICE_NAME="wayfarer-app"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Wayfarer App to Google Cloud Run"
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Build and push the Docker image
echo "🐳 Building and pushing Docker image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars "MYSQL_HOST=35.225.222.139,MYSQL_PORT=3306,MYSQL_DATABASE=trip_planner,MYSQL_USER=trip_planner,VERTEX_AI_PROJECT_ID=trip-planner-demo-471815,VERTEX_AI_LOCATION=us-central1,VERTEX_AI_MODEL=gemini-2.5-pro,GOOGLE_CLIENT_ID=111720869272-q7kjecu971734jbp7i324sme6lrh61vk.apps.googleusercontent.com" \
    --set-secrets "MYSQL_PASSWORD=mysql-password:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest" \
    --add-cloudsql-instances "trip-planner-demo-471815:us-central1:wayfarer-postgresdb"

# Get the service URL
echo "🌐 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🌐 Your app is available at: $SERVICE_URL"
echo ""
echo "📋 Next steps:"
echo "1. Update your Google OAuth redirect URI to: $SERVICE_URL"
echo "2. Test your application"
echo "3. Monitor logs with: gcloud logs tail --follow --service=$SERVICE_NAME"
