#!/bin/bash
# PulseRelay Deployment Script for Google Cloud Run

set -e

# Configuration
PROJECT_ID="pulserelay-506715"
REGION="us-central1"
SERVICE_NAME="pulserelay"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=========================================="
echo "PulseRelay Deployment to Google Cloud Run"
echo "=========================================="

# Step 1: Configure project
echo ""
echo "Step 1: Configuring GCP project..."
gcloud config set project ${PROJECT_ID}

# Step 2: Enable required APIs
echo ""
echo "Step 2: Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# Step 3: Create Firestore database
echo ""
echo "Step 3: Creating Firestore database..."
gcloud firestore databases create --location=us-central1 --project=${PROJECT_ID} 2>/dev/null || echo "Firestore database already exists"

# Step 4: Create Pub/Sub topic
echo ""
echo "Step 4: Creating Pub/Sub topic..."
gcloud pubsub topics create pulse-observations --project=${PROJECT_ID} 2>/dev/null || echo "Pub/Sub topic already exists"

# Step 5: Create Pub/Sub subscription
echo ""
echo "Step 5: Creating Pub/Sub subscription..."
gcloud pubsub subscriptions create pulse-observations-sub \
    --topic=pulse-observations \
    --ack-deadline=60 \
    --project=${PROJECT_ID} 2>/dev/null || echo "Pub/Sub subscription already exists"

# Step 6: Build and push Docker image
echo ""
echo "Step 6: Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo ""
echo "Step 7: Pushing Docker image..."
docker push ${IMAGE_NAME}:latest

# Step 8: Deploy to Cloud Run
echo ""
echo "Step 8: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --region=${REGION} \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},GEMINI_MODEL=gemini-2.0-flash" \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10

# Step 9: Get the service URL
echo ""
echo "Step 9: Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Service URL: ${SERVICE_URL}"
echo "Health Check: ${SERVICE_URL}/health"
echo "API Base: ${SERVICE_URL}/api"
echo ""
echo "Firestore collections:"
echo "  - sessions: Patient session data"
echo ""
echo "Pub/Sub:"
echo "  - Topic: pulse-observations"
echo "  - Subscription: pulse-observations-sub"
echo ""
echo "GCP Services Used:"
echo "  - Cloud Run: Application hosting"
echo "  - Firestore: Patient state persistence"
echo "  - Pub/Sub: Event-driven observation processing"
echo "  - Vertex AI/Gemini: Clinical text extraction"
echo "=========================================="
