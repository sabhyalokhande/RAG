# GCP Deployment Guide

This guide covers deploying the RAG system on Google Cloud Platform using various services.

## 🚀 Quick Deploy Options

### Option 1: Cloud Run (Recommended)
Fastest deployment with automatic scaling and HTTPS.

### Option 2: Compute Engine
Full control over VM with persistent storage.

### Option 3: GKE (Kubernetes)
For complex deployments with multiple services.

---

## 🎯 Option 1: Cloud Run Deployment

### Prerequisites
- Google Cloud SDK installed
- Project with billing enabled
- APIs enabled: Cloud Run, Cloud Build, Container Registry

### Step 1: Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Build and Deploy
```bash
# Set your project ID
export PROJECT_ID=$(gcloud config get-value project)

# Build and deploy to Cloud Run
gcloud run deploy rag-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars="FLASK_ENV=production" \
  --set-env-vars="PORT=8080"
```

### Step 3: Set Environment Variables
```bash
gcloud run services update rag-api \
  --region us-central1 \
  --set-env-vars="AZURE_OPENAI_API_KEY=your-key" \
  --set-env-vars="AZURE_OPENAI_ENDPOINT=your-endpoint" \
  --set-env-vars="AZURE_OPENAI_API_VERSION=2024-02-15-preview" \
  --set-env-vars="AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini" \
  --set-env-vars="AZURE_DEPLOYMENT_EMBEDDING=text-embedding-3-small" \
  --set-env-vars="GEMINI_API_KEY=your-gemini-key"
```

### Step 4: Test Deployment
```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe rag-api --region us-central1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
```

---

## 🖥️ Option 2: Compute Engine Deployment

### Step 1: Create VM Instance
```bash
gcloud compute instances create-with-container rag-instance \
  --container-image gcr.io/$PROJECT_ID/rag-api:latest \
  --machine-type e2-standard-4 \
  --zone us-central1-a \
  --tags http-server,https-server \
  --metadata-from-file user-data=startup-script.sh
```

### Step 2: Create Startup Script
Create `startup-script.sh`:
```bash
#!/bin/bash
# Install Docker
apt-get update
apt-get install -y docker.io

# Pull and run the container
docker pull gcr.io/PROJECT_ID/rag-api:latest
docker run -d \
  --name rag-api \
  -p 80:8080 \
  -e AZURE_OPENAI_API_KEY=your-key \
  -e AZURE_OPENAI_ENDPOINT=your-endpoint \
  -e FLASK_ENV=production \
  gcr.io/PROJECT_ID/rag-api:latest
```

### Step 3: Create Firewall Rules
```bash
gcloud compute firewall-rules create allow-rag-api \
  --allow tcp:80 \
  --target-tags http-server \
  --source-ranges 0.0.0.0/0
```

---

## 🐳 Option 3: GKE (Kubernetes) Deployment

### Step 1: Create GKE Cluster
```bash
gcloud container clusters create rag-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-standard-4 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10
```

### Step 2: Create Kubernetes Deployment
Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: rag-api
        image: gcr.io/PROJECT_ID/rag-api:latest
        ports:
        - containerPort: 8080
        env:
        - name: FLASK_ENV
          value: "production"
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: azure-openai-key
        - name: AZURE_OPENAI_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: azure-openai-endpoint
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rag-api-service
spec:
  selector:
    app: rag-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Step 3: Create Secrets
```bash
kubectl create secret generic rag-secrets \
  --from-literal=azure-openai-key=your-key \
  --from-literal=azure-openai-endpoint=your-endpoint \
  --from-literal=gemini-api-key=your-gemini-key
```

### Step 4: Deploy to GKE
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## 🔧 Environment Variables

### Required Variables
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_DEPLOYMENT_EMBEDDING=text-embedding-3-small

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key

# Application
FLASK_ENV=production
PORT=8080
```

### Optional Variables
```bash
# Security
SECRET_KEY=your-secret-key

# Storage paths
CHROMA_DB_PATH=/app/chroma_db
UPLOAD_FOLDER=/app/uploads

# Organization settings
ORG_NAME=Your Organization
ORG_DESCRIPTION=AI Solutions Provider
DEFAULT_TONE=professional
```

---

## 📊 Monitoring and Logging

### Cloud Run Logs
```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api"

# Stream logs
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=rag-api"
```

### GKE Logs
```bash
# View pod logs
kubectl logs -f deployment/rag-api

# View service logs
kubectl logs -f service/rag-api-service
```

### Compute Engine Logs
```bash
# View instance logs
gcloud compute instances get-serial-port-output rag-instance --zone us-central1-a
```

---

## 🔒 Security Best Practices

### 1. Use Secret Manager
```bash
# Create secrets
echo -n "your-azure-key" | gcloud secrets create azure-openai-key --data-file=-

# Access in Cloud Run
gcloud run services update rag-api \
  --region us-central1 \
  --set-env-vars="AZURE_OPENAI_API_KEY=projects/$PROJECT_ID/secrets/azure-openai-key/versions/latest"
```

### 2. Enable IAM
```bash
# Grant Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding azure-openai-key \
  --member="serviceAccount:rag-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Network Security
```bash
# Create VPC connector for private services
gcloud compute networks vpc-access connectors create rag-connector \
  --network default \
  --region us-central1 \
  --range 10.8.0.0/28
```

---

## 🚀 CI/CD Pipeline

### Cloud Build Configuration
Create `cloudbuild.yaml`:
```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rag-api:$COMMIT_SHA', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rag-api:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'rag-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/rag-api:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/rag-api:$COMMIT_SHA'
```

### Trigger Build
```bash
# Submit build
gcloud builds submit --config cloudbuild.yaml

# Or create trigger
gcloud builds triggers create github \
  --repo-name=rag-system \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## 💰 Cost Optimization

### Cloud Run Optimization
```bash
# Set appropriate resource limits
gcloud run services update rag-api \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --concurrency 40
```

### Compute Engine Optimization
```bash
# Use preemptible instances for cost savings
gcloud compute instances create-with-container rag-instance \
  --container-image gcr.io/$PROJECT_ID/rag-api:latest \
  --machine-type e2-standard-2 \
  --preemptible
```

---

## 🔍 Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   # Check logs
   gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR"
   ```

2. **Memory issues**
   ```bash
   # Increase memory
   gcloud run services update rag-api --memory 4Gi --region us-central1
   ```

3. **Timeout issues**
   ```bash
   # Increase timeout
   gcloud run services update rag-api --timeout 1800 --region us-central1
   ```

4. **Environment variables not set**
   ```bash
   # Verify environment variables
   gcloud run services describe rag-api --region us-central1 --format="value(spec.template.spec.containers[0].env)"
   ```

### Health Checks
```bash
# Test health endpoint
curl -f https://your-service-url/health

# Check service status
gcloud run services describe rag-api --region us-central1
```

---

## 📈 Scaling

### Auto-scaling Configuration
```bash
# Configure auto-scaling
gcloud run services update rag-api \
  --region us-central1 \
  --min-instances 1 \
  --max-instances 20 \
  --cpu-throttling
```

### Load Testing
```bash
# Install hey for load testing
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 https://your-service-url/health
```

This deployment guide provides comprehensive instructions for deploying your RAG system on Google Cloud Platform with different options based on your needs and scale requirements. 