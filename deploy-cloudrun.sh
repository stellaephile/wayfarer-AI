#!/bin/bash
set -euo pipefail

# ---- CONFIG ----
PROJECT_ID="trip-planner-demo-471815"
REGION="us-central1"
SERVICE_NAME="wayfarer-ai"
REPO_NAME="trip-planner-repo"
IMAGE_NAME="wayfarer-ai"
INSTANCE_CONNECTION="trip-planner-demo-471815:us-central1:wayfarer-postgresdb"  # <-- update if your instance name differs

# ---- BUILD ----
echo "🚀 Building multi-arch Docker image..."
docker build \
  --platform linux/amd64 \
  --no-cache \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  .

# ---- PUSH ----
echo "📦 Pushing image to Artifact Registry..."
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest

# ---- DEPLOY ----
echo "🌍 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances=${INSTANCE_CONNECTION} \
  --set-secrets=MYSQL_PASSWORD=mysql-password:latest \
  --env-vars-file cloud_run.env

echo "✅ Deployment finished!"
echo "👉 Run 'gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID}' to get the URL"
