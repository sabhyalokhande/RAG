# 🚀 Deployment Guide for Render

## Prerequisites
- GitHub repository with your code
- Render account (free tier available)

## Deployment Steps

### 1. Connect to Render
1. Go to [render.com](https://render.com)
2. Sign up/Login with your GitHub account
3. Click "New +" and select "Web Service"

### 2. Connect Repository
1. Connect your GitHub repository
2. Select the repository: `sabhyalokhande/influai-rag`

### 3. Configure Service
- **Name**: `influai-rag`
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app`
- **Plan**: `Free`

### 4. Environment Variables
Add these environment variables in Render dashboard:

```
CHROMA_DB_PATH=/opt/render/project/src/chroma_db
FLASK_ENV=production
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
```

### 5. Deploy
1. Click "Create Web Service"
2. Wait for build to complete
3. Your app will be available at: `https://your-app-name.onrender.com`

## API Endpoints

### Health Check
```
GET https://your-app-name.onrender.com/health
```

### HackRX API
```
POST https://your-app-name.onrender.com/hackrx/run
```

### Cache Management
```
GET https://your-app-name.onrender.com/hackrx/cache/status
POST https://your-app-name.onrender.com/hackrx/cache/clear
```

## Postman Collection

### HackRX Run Request
```
POST https://your-app-name.onrender.com/hackrx/run
Headers:
  Content-Type: application/json
  Authorization: Bearer test-api-key

Body:
{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?"
    ]
}
```

## Troubleshooting

### Common Issues
1. **Build fails**: Check if all dependencies are in `requirements.txt`
2. **App crashes**: Check logs in Render dashboard
3. **Environment variables**: Ensure all required env vars are set

### Logs
- View logs in Render dashboard under your service
- Check for any Python errors or missing dependencies

## Performance Notes
- Free tier has limitations on CPU and memory
- Consider upgrading for production use
- Cache TTL is set to 1 hour for optimal performance 