# Advanced Production-Ready RAG System

A sophisticated Flask-based RAG (Retrieval-Augmented Generation) system with **Pinecone v7.x** vector database for high-performance similarity search, Azure OpenAI integration with enhanced models, and multi-user support. This system is designed for enterprise-grade document processing and intelligent question answering with superior speed and accuracy.

## 🚀 Quick Start

### Deploy to Google Cloud Run
```bash
# Build and deploy to Google Cloud Run
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rag
gcloud run deploy rag --image gcr.io/YOUR_PROJECT_ID/rag --platform managed --region us-central1 --allow-unauthenticated --port 8080
```

### Deploy to Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Deploy to Google Kubernetes Engine (GKE)
```bash
# Automated deployment
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

### Local Development
```bash
# Clone the repository
git clone <your-repo-url>
cd RAG

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run the application
python run.py
```

## 🎯 Features

### Core Capabilities
- **📄 Multi-Format Document Processing**: PDF, TXT, DOCX with robust text extraction
- **🧠 Intelligent Vector Search**: **Pinecone v7.x**-powered similarity search with gRPC support and superior performance
- **🤖 Enhanced Azure OpenAI Integration**: Enterprise-grade AI with **GPT-4** and **text-embedding-3-large** (3072 dimensions)
- **💬 Multi-Turn Conversations**: Context-aware dialogue with conversation history
- **⚡ High Performance**: Async processing with smart caching and timeout handling
- **🔒 Production Ready**: Comprehensive error handling, logging, and security features

### Advanced Features
- **📊 Smart Caching System**: Multi-level caching with TTL and LRU eviction
- **🔄 Retry Logic**: Exponential backoff with tenacity for reliability
- **📈 Performance Monitoring**: Built-in timing and metrics collection
- **👥 Multi-User Support**: Session management and conversation isolation
- **🗂️ Collection Management**: Organize documents into logical collections
- **🎨 Customizable Responses**: Tone, style, and organization-specific formatting
- **🎯 Enhanced Accuracy**: Improved models and chunking strategies for better results

## 🏗️ Architecture

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Flask App     │    │   Pinecone v7.x │
│   (Postman/UI)  │◄──►│   (Quart)       │◄──►│   Vector Store  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Azure OpenAI   │
                       │   (GPT-4 &      │
                       │   text-embedding│
                       │   -3-large)     │
                       └─────────────────┘
```

### Technology Stack
- **Web Framework**: Quart (async Flask)
- **Vector Database**: **Pinecone v7.x** (primary with gRPC), ChromaDB (fallback)
- **AI Provider**: Azure OpenAI with enhanced models
- **HTTP Client**: httpx (async) with aiohttp fallback
- **Document Processing**: pypdf, python-docx, docx2txt
- **Caching**: Custom SmartCache with TTL and LRU
- **Deployment**: Docker, Google Cloud Run, GKE, Render

## 🔄 Complete RAG Flow

### 1. Document Processing Flow
```
📄 Document Upload
    ↓
🔍 Text Extraction (PDF/DOCX/TXT)
    ↓
✂️  Dynamic Chunking (800-2000 chars with 200 overlap)
    ↓
🧠 Embedding Generation (text-embedding-3-large, 3072 dimensions)
    ↓
💾 Vector Storage (Pinecone v7.x with gRPC)
    ↓
✅ Document Indexed & Ready
```

### 2. Query Processing Flow
```
❓ User Query
    ↓
🔍 Query Embedding Generation
    ↓
🔎 Vector Similarity Search (top_k=8-35 based on doc size)
    ↓
📊 Context Retrieval (relevant chunks)
    ↓
🤖 GPT-4 Answer Generation (with intelligent reasoning)
    ↓
🧹 Response Cleaning (markdown removal)
    ↓
💬 Conversation History Update
    ↓
✅ Intelligent Answer Delivered
```

### 3. HackRX Production Flow
```
📋 Batch Questions + Document URL
    ↓
📥 Document Download & Processing
    ↓
⚡ Parallel Question Processing
    ↓
🧠 Intelligent Reasoning Analysis
    ↓
📊 Performance Metrics Collection
    ↓
💾 Result Caching (1-hour TTL)
    ↓
📤 Batch Answers Delivery
```

### 4. Caching Strategy
```
🔄 Multi-Level Caching:
├── Embedding Cache (24h TTL, 2000 items)
├── Query Result Cache (1h TTL, 500 items)
├── LLM Response Cache (30min TTL, 300 items)
└── HackRX Cache (1h TTL, unlimited)
```

### 5. Performance Optimization
```
⚡ Speed Optimizations:
├── Parallel Processing (8 workers)
├── Batch Embeddings (20 items/batch)
├── Dynamic Configuration (based on doc size)
├── Async Operations (with sync fallback)
└── Smart Timeouts (15s vector, 25s generation)
```

## 📋 API Reference

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "RAG system is running",
  "timestamp": "2025-07-30T17:14:15+00:00"
}
```

### Document Management

#### Upload Files
```http
POST /api/upload
Content-Type: multipart/form-data

files: [file1.pdf, file2.docx, ...]
collection_name: "my_collection"
```

**Response:**
```json
{
  "status": "success",
  "collection": "my_collection",
  "results": [
    {
      "filename": "document.pdf",
      "status": "success",
      "file_id": "uuid-1234",
      "chunks_added": 15,
      "processing_time": 2.3
    }
  ]
}
```

#### List Collections
```http
GET /api/collections
```

#### List Files in Collection
```http
GET /api/collections/{collection_name}/files
```

#### Delete File
```http
DELETE /api/collections/{collection_name}/files/{file_id}
```

#### Delete Collection
```http
DELETE /api/collections/{collection_name}
```

### RAG Operations

#### Vector Search
```http
POST /api/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "collection_name": "my_collection",
  "top_k": 8
}
```

#### Generate Answer
```http
POST /api/generate-answer
Content-Type: application/json

{
  "query": "Explain the main concepts",
  "collection_name": "my_collection",
  "conversation_id": "optional-uuid",
  "org_info": {
    "name": "My Company",
    "description": "AI Solutions Provider"
  },
  "tone": "professional",
  "include_performance_info": true
}
```

**Response:**
```json
{
  "status": "success",
  "answer": "Based on the documents in your collection...",
  "conversation_id": "uuid-5678",
  "performance": {
    "vector_search_time": 0.5,
    "answer_generation_time": 2.1,
    "total_time": 2.6
  },
  "sources": [
    {
      "document": "document.pdf",
      "chunk": "Machine learning is a subset...",
      "similarity_score": 0.95
    }
  ]
}
```

### HackRX API (Production Endpoint)

#### Process Documents and Answer Questions
```http
POST /hackrx/run
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "documents": "https://example.com/document.pdf",
  "questions": [
    "What is the grace period for premium payment?",
    "What is the waiting period for pre-existing diseases?"
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "answers": [
    "A grace period of thirty days is provided for premium payments...",
    "There is a waiting period of thirty-six months for pre-existing conditions..."
  ],
  "processing_time": 7.73,
  "documents_processed": 1,
  "questions_processed": 2
}
```

#### Cache Management
```http
GET /hackrx/cache/status
POST /hackrx/cache/clear
```

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Azure OpenAI account with API key
- **Pinecone v7.x account** with API key (recommended for production)
- Docker (for containerized deployment)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Pinecone v7.x Setup (Recommended)

1. **Create a Pinecone account**:
   - Go to [Pinecone Console](https://app.pinecone.io/)
   - Sign up for a free account
   - Get your API key from the console

2. **Configure Pinecone v7.x**:
   - The system will automatically create an index named `rag-index`
   - Uses **text-embedding-3-large** embeddings (3072 dimensions)
   - Serverless deployment for cost efficiency
   - gRPC support for enhanced performance

3. **Environment Variables**:
   ```env
   PINECONE_API_KEY=your-pinecone-api-key
   PINECONE_CLOUD=aws
   PINECONE_REGION=us-east-1
   PINECONE_INDEX_NAME=rag-index
   PINECONE_DIMENSION=3072
   ```

### 4. Environment Configuration

Create a `.env` file:

```env
# Azure OpenAI Configuration (Enhanced Models)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_COMPLETION=gpt-4
AZURE_DEPLOYMENT_EMBEDDING=text-embedding-3-large

# Pinecone v7.x Configuration (Primary Vector Database)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=rag-index
PINECONE_DIMENSION=3072

# ChromaDB Configuration (Fallback)
CHROMA_DB_PATH=./chroma_db

# Application Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
UPLOAD_FOLDER=./uploads

# Organization Settings
ORG_NAME=Your Organization
ORG_DESCRIPTION=A leading provider of innovative solutions
DEFAULT_TONE=professional

# Enhanced Performance Settings
CHUNK_SIZE=800
CHUNK_OVERLAP=200
MAX_TOKENS=4000
SIMILARITY_TOP_K=8
TEMPERATURE=0.1
```

### 5. Run the Application

#### Local Development
```bash
python run.py
```
Server starts on `http://localhost:5001`

#### Docker
```bash
# Build the image
docker build -t rag .

# Run the container
docker run -p 8080:8080 rag
```

#### Google Cloud Run
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rag

# Deploy to Cloud Run
gcloud run deploy rag \
  --image gcr.io/YOUR_PROJECT_ID/rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

#### Google Kubernetes Engine (GKE)
```bash
# Automated deployment
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# Manual deployment
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-secrets.yaml
```

### 6. Test the Installation
```bash
curl http://localhost:5001/health
```

## 🚀 Enhanced Models & Accuracy Improvements

### Latest Model Updates
- **GPT-4**: Advanced reasoning and answer generation capabilities
- **text-embedding-3-large**: 3072 dimensions (2x larger than text-embedding-3-small)
- **Improved vector dimensions**: Better semantic matching and context understanding

### Accuracy Enhancements
- **Enhanced Text Chunking**: Reduced chunk size to 800 characters for better semantic boundaries
- **Improved Overlap**: Increased to 200 characters for better context preservation
- **Better Retrieval**: Increased default top_k from 5 to 8 for better coverage
- **Enhanced Prompt Engineering**: Specific instructions for policy-related questions
- **Better Context Processing**: Increased context limit to 800 characters per document

## 🚀 Pinecone v7.x Benefits

### Why Pinecone v7.x?
- **⚡ Superior Performance**: 10-100x faster than local vector databases with gRPC support
- **🎯 Higher Accuracy**: Better similarity search with optimized algorithms and enhanced models
- **📈 Scalability**: Handles millions of vectors with ease
- **🔒 Managed Service**: No infrastructure management required
- **💰 Cost Effective**: Pay-per-use pricing with free tier
- **🌐 Global Availability**: Multi-region deployment options
- **🚀 gRPC Support**: Up to 3x faster than HTTP for vector operations

## 📊 Performance Features

### Smart Caching System
- **Embedding Cache**: 24-hour TTL, 2000 items max
- **Query Result Cache**: 1-hour TTL, 500 items max
- **LLM Response Cache**: 30-minute TTL, 300 items max
- **LRU Eviction**: Automatic cleanup of least-used items

### Async Processing
- **Batch Embeddings**: 20 items per batch
- **Timeout Handling**: 15s vector search, 25s answer generation
- **Fallback Mechanisms**: Sync client if async times out

### Memory Management
- **Conversation History**: Limited to 20 messages
- **Document Chunking**: 800 chars with 200 char overlap
- **Context Limiting**: Top 6 recent messages for LLM

## 🔧 Configuration Options

### RAG Settings (Enhanced)
```python
CHUNK_SIZE = 800          # Reduced for better semantic boundaries
CHUNK_OVERLAP = 200       # Increased overlap for better context
MAX_TOKENS = 4000         # LLM response limit
SIMILARITY_TOP_K = 8      # Increased from 5 to 8 for better retrieval
TEMPERATURE = 0.1         # LLM creativity
```

### Cache Settings
```python
embedding_cache = SmartCache(max_size=2000, ttl=24*3600)
query_result_cache = SmartCache(max_size=500, ttl=3600)
llm_response_cache = SmartCache(max_size=300, ttl=1800)
```

## 📁 Project Structure

```
RAG/
├── run.py                 # Main application entry point
├── config.py              # Configuration settings (enhanced models)
├── requirements.txt        # Python dependencies (Pinecone v7.x)
├── Dockerfile             # Container configuration
├── .dockerignore          # Docker ignore patterns
├── .gcloudignore          # Google Cloud ignore patterns
├── cloudbuild.yaml        # Google Cloud Build config
├── deploy-gcp.sh          # Automated GKE deployment script
├── k8s-deployment.yaml    # Kubernetes deployment config
├── k8s-secrets.yaml.template # Kubernetes secrets template
├── README.md              # This documentation
├── DEPLOYMENT.md          # Deployment guide
├── GCP-DEPLOYMENT.md      # GCP deployment guide
├── PINECONE_SETUP.md      # Pinecone v7.x setup guide
├── ACCURACY_IMPROVEMENTS.md # Accuracy improvements documentation
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── routes/
│   │   └── rag_routes.py  # API endpoints
│   └── services/
│       ├── openai_services.py  # Azure OpenAI integration (enhanced)
│       ├── pinecone_services.py # Pinecone v7.x integration
│       └── utils.py       # Utility functions
├── chroma_db/             # Vector database storage (fallback)
├── storage/               # File storage
├── embeddings/            # Embedding cache
├── uploads/               # File uploads
└── rag_system.log         # Application logs
```

## 🚀 Deployment Options

### Google Cloud Run (Recommended)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rag
gcloud run deploy rag --image gcr.io/YOUR_PROJECT_ID/rag --platform managed --region us-central1 --allow-unauthenticated --port 8080
```

### Google Kubernetes Engine (GKE)
```bash
# Automated deployment
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# Manual deployment
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-secrets.yaml
```

### Render
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create new Web Service
4. Select your forked repository
5. Use build command: `pip install -r requirements.txt`
6. Use start command: `gunicorn run:app`
7. Add environment variables

### Docker
```bash
# Build image
docker build -t rag .

# Run container
docker run -p 8080:8080 rag

# With environment variables
docker run -p 8080:8080 -e AZURE_OPENAI_API_KEY=your-key rag
```

### Local Production
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker run:app

# Using Hypercorn
pip install hypercorn
hypercorn run:app --bind 0.0.0.0:8080
```

## 🔍 Monitoring and Logging

### Log Files
- **Application Logs**: `rag_system.log`
- **Performance Metrics**: Built-in timing
- **Error Tracking**: Comprehensive exception handling

### Performance Monitoring
```json
{
  "performance": {
    "vector_search_time": 0.5,
    "answer_generation_time": 2.1,
    "total_time": 2.6,
    "cache_hits": 3,
    "cache_misses": 1
  }
}
```

### Health Check Endpoints
```http
GET /health
```

## 🛡️ Error Handling

### Retry Logic
- **Embedding Generation**: 3 attempts with exponential backoff
- **Vector Search**: 3 attempts with exponential backoff
- **Answer Generation**: 3 attempts with exponential backoff

### Timeout Protection
- **Vector Search**: 15-second timeout
- **Answer Generation**: 25-second timeout
- **Graceful Fallbacks**: Sync client if async fails

### Common Error Codes
- `400`: Bad Request (invalid input)
- `404`: Not Found (collection/file not found)
- `500`: Internal Server Error (processing error)
- `503`: Service Unavailable (timeout/rate limit)

## 📈 Scalability Features

### Multi-Threading
- **Thread Pool**: 8 workers for CPU-bound tasks
- **Async Operations**: Non-blocking I/O
- **Batch Processing**: Efficient API usage

### Memory Optimization
- **LRU Cache**: Automatic cleanup
- **TTL Management**: Expired item removal
- **Context Limiting**: Prevent token overflow

## 🔐 Security Features

### File Handling
- **Secure Temp Files**: Automatic cleanup
- **File Validation**: Format checking
- **Path Sanitization**: Prevent directory traversal

### API Protection
- **Input Validation**: Parameter checking
- **Error Sanitization**: Safe error messages
- **CORS Support**: Cross-origin requests

## 🐛 Troubleshooting

### Common Issues

#### 1. UnicodeDecodeError during gcloud builds submit
**Problem**: Binary files causing encoding issues
**Solution**: Use `.gcloudignore` file to exclude binary files

#### 2. Connection refused in Postman
**Problem**: Port mapping mismatch
**Solution**: 
```bash
# Use correct port mapping
docker run -p 8080:8080 rag
# Then access via http://localhost:8080
```

#### 3. Azure OpenAI API errors
**Problem**: Invalid credentials or endpoint
**Solution**: Verify environment variables:
```bash
echo $AZURE_OPENAI_API_KEY
echo $AZURE_OPENAI_ENDPOINT
```

#### 4. ChromaDB initialization errors
**Problem**: Permission issues with database directory
**Solution**: Ensure write permissions:
```bash
chmod 755 chroma_db/
```

#### 5. Pinecone v7.x connection errors
**Problem**: Invalid API key or environment
**Solution**: Verify Pinecone configuration:
```bash
echo $PINECONE_API_KEY
echo $PINECONE_CLOUD
echo $PINECONE_REGION
```

#### 6. Pinecone index creation fails
**Problem**: Index already exists or quota exceeded
**Solution**: Check Pinecone console and delete existing index if needed

### Debug Mode
```bash
# Enable debug logging
export FLASK_ENV=development
python run.py
```

### Performance Tuning
```python
# Adjust cache sizes for your use case
embedding_cache = SmartCache(max_size=5000, ttl=24*3600)
query_result_cache = SmartCache(max_size=1000, ttl=3600)

# Adjust chunking parameters
CHUNK_SIZE = 800  # Optimized for semantic boundaries
CHUNK_OVERLAP = 200  # Better context preservation
```

## 📚 Examples

### Python Client Example
```python
import requests
import json

# Upload a document
files = {'files': open('document.pdf', 'rb')}
data = {'collection_name': 'my_collection'}
response = requests.post('http://localhost:5001/api/upload', files=files, data=data)
print(response.json())

# Ask a question
query_data = {
    'query': 'What is the main topic?',
    'collection_name': 'my_collection'
}
response = requests.post('http://localhost:5001/api/generate-answer', json=query_data)
print(response.json())
```

### cURL Examples
```bash
# Health check
curl http://localhost:5001/health

# Upload document
curl -X POST http://localhost:5001/api/upload \
  -F "files=@document.pdf" \
  -F "collection_name=my_collection"

# Generate answer
curl -X POST http://localhost:5001/api/generate-answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this about?", "collection_name": "my_collection"}'
```

## 🧹 Code Analysis & Unused Functions

### ✅ **ACTIVE FUNCTIONS** (Used in Main Application)
- `get_embeddings()` - Primary embedding generation
- `get_embeddings_optimized()` - Used in document processing
- `process_and_store_document()` - Document upload and storage
- `query_vector_db()` - Primary vector search
- `generate_answer()` - Main answer generation
- `clean_markdown_formatting()` - Response cleaning
- `construct_rag_prompt()` - Enhanced prompt engineering
- `validate_answer_accuracy()` - Answer validation
- `extract_text_from_file()` - File text extraction
- `chunk_text_advanced()` - Dynamic text chunking
- `get_dynamic_processing_config()` - Dynamic configuration
- `clean_text()` - Text normalization
- `truncate_text_for_embeddings()` - Token limit management

### ⚠️ **UNUSED FUNCTIONS** (Not Used in Main Code)
- `query_vector_db_fast()` - Alternative fast search (imported but not used)
- `generate_answer_fast()` - Alternative fast generation (imported but not used)
- `enhance_context_for_accuracy()` - Context enhancement (defined but not used)
- `prioritize_chunks_by_relevance()` - Chunk prioritization (defined but not used)
- `query_across_namespaces()` - Cross-namespace search (defined but not used)
- `upsert_from_dataframe()` - DataFrame upsert (defined but not used)
- `get_collection_stats()` - Collection statistics (defined but not used)
- `get_index_stats()` - Index statistics (defined but not used)
- `extract_text_from_url()` - URL text extraction (defined but not used)
- `chunk_text_parallel()` - Parallel chunking (defined but not used)
- `chunk_text_standard()` - Standard chunking (used internally)
- `extract_text_parallel()` - Parallel PDF extraction (defined but not used)

### 📊 **TEST FILES** (Development/Testing Only)
- `test_intelligent_reasoning.py` - Intelligent reasoning tests
- `test_accuracy_improvements.py` - Accuracy improvement tests
- `test_hackrx.py` - HackRX endpoint tests
- `test_maximum_accuracy.py` - Maximum accuracy tests
- `test_performance_accuracy.py` - Performance accuracy tests
- `test_scoring_optimization.py` - Scoring optimization tests
- `pinecone_example.py` - Pinecone usage examples

### 🔧 **RECOMMENDATIONS**
1. **Keep Unused Functions**: They provide fallback capabilities and future extensibility
2. **Maintain Test Files**: They are valuable for development and validation
3. **Consider Cleanup**: Remove truly unused functions if they add no value
4. **Documentation**: All functions are well-documented for future use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `rag_system.log`
3. Open an issue on GitHub
4. Contact the development team

---

**Built with ❤️ for enterprise-grade RAG applications with enhanced accuracy and performance** 