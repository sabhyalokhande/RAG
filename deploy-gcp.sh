#!/bin/bash

# GCP RAG Application Deployment Script
# This script automates the deployment of the RAG application on Google Cloud Platform

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-gcp-project-id"}
REGION=${REGION:-"us-central1"}
CLUSTER_NAME=${CLUSTER_NAME:-"rag-cluster"}
IMAGE_NAME="gcr.io/$PROJECT_ID/rag-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    print_status "All prerequisites are satisfied."
}

# Set up GCP project
setup_project() {
    print_status "Setting up GCP project..."
    
    # Set the project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    gcloud services enable container.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    print_status "GCP project setup complete."
}

# Create GKE cluster
create_cluster() {
    print_status "Creating GKE cluster..."
    
    gcloud container clusters create $CLUSTER_NAME \
        --region=$REGION \
        --num-nodes=2 \
        --machine-type=e2-standard-2 \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade
    
    # Get credentials for the cluster
    gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION
    
    print_status "GKE cluster created successfully."
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    # Build the image
    docker build -t $IMAGE_NAME .
    
    # Configure Docker to use gcloud as a credential helper
    gcloud auth configure-docker
    
    # Push the image
    docker push $IMAGE_NAME
    
    print_status "Docker image built and pushed successfully."
}

# Create Kubernetes secrets
create_secrets() {
    print_status "Creating Kubernetes secrets..."
    
    # Check if secrets file exists
    if [ ! -f "k8s-secrets.yaml" ]; then
        print_warning "k8s-secrets.yaml not found. Please create it with your Azure OpenAI credentials."
        print_status "Example k8s-secrets.yaml:"
        cat << EOF
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
type: Opaque
data:
  azure-openai-api-key: $(echo -n "your-api-key" | base64)
  azure-openai-endpoint: $(echo -n "your-endpoint" | base64)
EOF
        exit 1
    fi
    
    # Apply secrets
    kubectl apply -f k8s-secrets.yaml
    
    print_status "Kubernetes secrets created successfully."
}

# Deploy application
deploy_application() {
    print_status "Deploying application..."
    
    # Update the image name in the deployment file
    sed "s|gcr.io/PROJECT_ID/rag-app:latest|$IMAGE_NAME:latest|g" k8s-deployment.yaml > k8s-deployment-temp.yaml
    
    # Apply the deployment
    kubectl apply -f k8s-deployment-temp.yaml
    
    # Clean up temporary file
    rm k8s-deployment-temp.yaml
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/rag-app
    
    print_status "Application deployed successfully."
}

# Get service URL
get_service_url() {
    print_status "Getting service URL..."
    
    # Wait for external IP
    while [ -z "$EXTERNAL_IP" ]; do
        EXTERNAL_IP=$(kubectl get service rag-app-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        if [ -z "$EXTERNAL_IP" ]; then
            print_status "Waiting for external IP..."
            sleep 10
        fi
    done
    
    print_status "Application is available at: http://$EXTERNAL_IP"
    print_status "Health check endpoint: http://$EXTERNAL_IP/health"
}

# Main deployment function
main() {
    print_status "Starting RAG application deployment on GCP..."
    
    check_prerequisites
    setup_project
    create_cluster
    build_and_push_image
    create_secrets
    deploy_application
    get_service_url
    
    print_status "Deployment completed successfully!"
    print_status "You can now access your RAG application at the URL shown above."
}

# Run main function
main "$@" 