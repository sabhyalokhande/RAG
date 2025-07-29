# Advanced Production-Ready RAG System

A sophisticated Flask-based RAG (Retrieval-Augmented Generation) system with ChromaDB vector storage, Azure OpenAI integration, and multi-user support.

## 🚀 Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**Or manually deploy to Render:**
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create new Web Service
4. Select your forked repository
5. Use build command: `pip install -r requirements.txt`
6. Use start command: `gunicorn run:app`
7. Add environment variables (see deployment guide)

## 🚀 Features

- **Asynchronous Processing**: High-performance async operations
- **ChromaDB Vector Storage**: Persistent vector database with optimized settings
- **Azure OpenAI Integration**: Enterprise-grade AI with fallback mechanisms
- **Multi-User Support**: Conversation history and session management
- **Advanced Caching**: Smart cache with TTL, LRU eviction, and specialized caches
- **Multiple File Formats**: PDF, TXT, DOCX with robust text extraction
- **Collection Management**: Organize documents into collections
- **Performance Monitoring**: Built-in timing and performance metrics
- **Error Handling**: Comprehensive retry logic and error recovery
- **Production Ready**: Logging, timeouts, and scalability features

## 🏗️ Architecture

### Core Components
- **Flask**: Web framework with CORS support
- **ChromaDB**: Vector database for similarity search
- **Azure OpenAI**: Embeddings and chat completions
- **Smart Caching**: Multi-level caching system
- **Async Processing**: Non-blocking operations

### Advanced Features
- **Retry Logic**: Exponential backoff with tenacity
- **Timeout Handling**: Graceful fallbacks for slow operations
- **Memory Management**: LRU cache eviction and TTL
- **Batch Processing**: Efficient embedding generation
- **Conversation History**: Multi-turn dialogue support

## 📋 API Endpoints

### HackRX API (Production Ready)

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
  "answers": [
    "A grace period of thirty days is provided...",
    "There is a waiting period of thirty-six months..."
  ]
}
```

#### Cache Management
```http
GET /hackrx/cache/status
POST /hackrx/cache/clear
```

### Health Check
```http
GET /health
```

## 🚀 Deployment

### Render Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Environment Variables
```bash
CHROMA_DB_PATH=/opt/render/project/src/chroma_db
FLASK_ENV=production
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
```

### Local Development
```bash
pip install -r requirements.txt
python run.py
```

## 📋 API Endpoints

### Document Management

#### Upload Files
```http
POST /api/upload
Content-Type: multipart/form-data

files: [file1, file2, ...]
collection_name: "my_collection"
```

**Response:**
```json
{
  "collection": "my_collection",
  "results": [
    {
      "filename": "document.pdf",
      "status": "success",
      "file_id": "uuid",
      "chunks_added": 15
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
  "top_k": 5
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
  "answer": "Based on the documents...",
  "conversation_id": "uuid",
  "performance": {
    "vector_search_time": 0.5,
    "answer_generation_time": 2.1,
    "total_time": 2.6
  }
}
```

## 🛠️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
AZURE_DEPLOYMENT_COMPLETION=gpt-4o-mini
AZURE_DEPLOYMENT_EMBEDDING=text-embedding-ada-002

# Application Configuration
SECRET_KEY=your-secret-key
FLASK_ENV=development
CHROMA_DB_PATH=./chroma_db
UPLOAD_FOLDER=./uploads

# Organization Settings
ORG_NAME=Your Organization
ORG_DESCRIPTION=A leading provider of innovative solutions
DEFAULT_TONE=professional
```

### 3. Run the Application
```bash
python run.py
```

The server will start on `http://localhost:5001`

### 4. Test the Server
```bash
curl http://localhost:5001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "RAG system is running",
  "timestamp": "2025-07-29T12:31:57.232360"
}
```

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
- **Document Chunking**: 512 chars with 50 char overlap
- **Context Limiting**: Top 6 recent messages for LLM

## 🔧 Configuration Options

### RAG Settings
```python
CHUNK_SIZE = 512          # Text chunk size
CHUNK_OVERLAP = 50        # Overlap between chunks
MAX_TOKENS = 4000         # LLM response limit
SIMILARITY_TOP_K = 5      # Number of similar docs
TEMPERATURE = 0.1         # LLM creativity
```

### Cache Settings
```python
embedding_cache = SmartCache(max_size=2000, ttl=24*3600)
query_result_cache = SmartCache(max_size=500, ttl=3600)
llm_response_cache = SmartCache(max_size=300, ttl=1800)
```

## 📁 File Structure

```
├── run.py                 # Main application
├── config.py              # Configuration
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── app/
│   └── __init__.py        # Flask app factory
├── chroma_db/             # Vector database storage
├── uploads/               # File uploads
└── rag_system.log         # Application logs
```

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker run:app
```

### Environment Variables for Production
```env
FLASK_ENV=production
CHROMA_DB_PATH=/var/lib/rag/chroma_db
UPLOAD_FOLDER=/var/lib/rag/uploads
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
    "total_time": 2.6
  }
}
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

This advanced RAG system provides enterprise-grade performance, reliability, and scalability for production deployments. 