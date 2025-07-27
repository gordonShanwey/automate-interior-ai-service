#!/bin/bash

# Simple Cloud Build Setup Script for Interior AI Service
# Sets up one trigger for main branch deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No Google Cloud project configured. Please run 'gcloud auth login' and 'gcloud config set project YOUR_PROJECT_ID'"
    exit 1
fi

print_status "Setting up Cloud Build for project: $PROJECT_ID"

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable aiplatform.googleapis.com

print_success "APIs enabled successfully"

# Create Artifact Registry repository
print_status "Creating Artifact Registry repository..."
gcloud artifacts repositories create interior-ai-service \
    --repository-format=docker \
    --location=europe-north1 \
    --description="Interior AI Service Docker images" \
    --quiet || print_warning "Repository may already exist"

print_success "Artifact Registry repository created"



# Create service account for the Interior AI Service
print_status "Creating service account for Interior AI Service..."
gcloud iam service-accounts create interior-ai-service \
    --display-name="Interior AI Service" \
    --description="Service account for Interior AI Service application" \
    --quiet || print_warning "Interior AI Service account may already exist"

# Grant permissions to the Interior AI Service account
print_status "Granting permissions to Interior AI Service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

print_success "Interior AI Service account permissions granted"

# Create service account for Cloud Build
print_status "Creating service account for Cloud Build..."
gcloud iam service-accounts create cloud-build-deployer \
    --display-name="Cloud Build Deployer" \
    --description="Service account for Cloud Build deployments" \
    --quiet || print_warning "Cloud Build service account may already exist"

# Grant necessary permissions to the Cloud Build service account
print_status "Granting permissions to Cloud Build service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

print_success "Cloud Build service account permissions granted"

# Create Pub/Sub topic
print_status "Creating Pub/Sub topic..."
gcloud pubsub topics create form-submissions-topic \
    --quiet || print_warning "Topic may already exist"

print_success "Pub/Sub topic created: form-submissions-topic"

# Create Pub/Sub subscription for Cloud Run service
print_status "Creating Pub/Sub subscription for Interior AI Service..."

# Get the current Cloud Run service URL
SERVICE_URL=$(gcloud run services describe interior-ai-service --region=europe-north1 --format="value(status.url)" --quiet 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    gcloud pubsub subscriptions create interior-ai-service-subscription \
        --topic=form-submissions-topic \
        --push-endpoint="$SERVICE_URL/webhooks/pubsub" \
        --push-auth-service-account=interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com \
        --quiet || print_warning "Subscription may already exist"
    
    print_success "Pub/Sub subscription created: interior-ai-service-subscription"
    print_success "Push endpoint: $SERVICE_URL/webhooks/pubsub"
else
    print_warning "Cloud Run service not found. Subscription will need to be created manually after deployment."
    print_warning "Command to run after deployment:"
    echo "gcloud pubsub subscriptions create interior-ai-service-subscription \\"
    echo "    --topic=form-submissions-topic \\"
    echo "    --push-endpoint=\$(gcloud run services describe interior-ai-service --region=europe-north1 --format='value(status.url)')/webhooks/pubsub \\"
    echo "    --push-auth-service-account=interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com"
fi

# Note: Cloud Build trigger will be created manually after repository connection
print_status "Skipping Cloud Build trigger creation - will be done manually after repository connection"

# Create and download service account key
print_status "Creating service account key for Interior AI Service..."
gcloud iam service-accounts keys create interior-ai-service-key.json \
    --iam-account=interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com \
    --quiet || print_warning "Key may already exist"

print_success "Service account key created: interior-ai-service-key.json"

# Create secrets in Secret Manager
print_status "Setting up Secret Manager..."
echo "Creating secret in Google Secret Manager..."

# Create the service account credentials secret
gcloud secrets create interior-ai-service-credentials \
    --replication-policy=automatic \
    --quiet || print_warning "Secret may already exist"

# Add the service account key to the secret
cat interior-ai-service-key.json | gcloud secrets versions add interior-ai-service-credentials \
    --data-file=- \
    --quiet || print_warning "Secret version may already exist"

# Create the designer email secret
gcloud secrets create designer-email \
    --replication-policy=automatic \
    --quiet || print_warning "Secret may already exist"

# Add the designer email to the secret
echo "YOUR_DESIGNER_EMAIL@example.com" | gcloud secrets versions add designer-email \
    --data-file=- \
    --quiet || print_warning "Secret version may already exist"

# Create SMTP username secret
gcloud secrets create smtp-username \
    --replication-policy=automatic \
    --quiet || print_warning "Secret may already exist"

# Add the SMTP username to the secret
echo "YOUR_SMTP_USERNAME@gmail.com" | gcloud secrets versions add smtp-username \
    --data-file=- \
    --quiet || print_warning "Secret version may already exist"

# Create SMTP password secret
gcloud secrets create smtp-password \
    --replication-policy=automatic \
    --quiet || print_warning "Secret may already exist"

# Add the SMTP password to the secret
echo "YOUR_SMTP_APP_PASSWORD" | gcloud secrets versions add smtp-password \
    --data-file=- \
    --quiet || print_warning "Secret version may already exist"

print_success "Secrets created and populated"

# Clean up the key file
rm -f interior-ai-service-key.json

# Display next steps
print_success "Cloud Build setup completed!"
echo ""
echo "✅ What was created:"
echo "  - Interior AI Service account: interior-ai-service@$PROJECT_ID.iam.gserviceaccount.com"
echo "  - Cloud Build service account: cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com"
echo "  - Artifact Registry repository: interior-ai-service"
echo "  - Cloud Storage bucket: gs://$PROJECT_ID-cloud-build-artifacts"
echo "  - Secret Manager secrets: interior-ai-service-credentials, designer-email"
echo ""
echo "Next steps:"
echo "1. Connect your GitHub repository to Cloud Build (manually in console)"
echo "2. Create Cloud Build trigger manually with service account: cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com"
echo "3. Test the pipeline by pushing to the 'master' branch"
echo ""
echo "Useful commands:"
echo "  gcloud builds triggers list"
echo "  gcloud builds list"
echo "  gcloud run services list" 