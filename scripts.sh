# ollam setup
export OLLAMA_HOST=0.0.0.0
ollama serve


#!/bin/bash

# 1. Set your Project ID
PROJECT_ID="your-project-id" # <--- CHANGE THIS
gcloud config set project $PROJECT_ID

echo "Enabling required Google Cloud APIs..."

# 2. Enable APIs (Updated with Cloud Build and Artifact Registry)
gcloud services enable \
    compute.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    dns.googleapis.com \
    iap.googleapis.com \
    secretmanager.googleapis.com \
    servicenetworking.googleapis.com \
    cloudresourcemanager.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com

# 3. Create the Artifact Registry Repository
# This is where your 'soccerdata-mcp' and 'n8n' custom images will live.
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create soccer-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for MCP and n8n images"

# 4. Initializing IAP Service Agent
echo "Initializing IAP Service Agent..."
gcloud beta services identity create --service=iap.googleapis.com --project=$PROJECT_ID

# 5. Application Default Credentials
gcloud auth application-default login

echo "Setup complete. You can now run 'terraform init' and 'terraform apply'."

