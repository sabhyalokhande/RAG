# 🤖 RAG2 - Intelligent Retrieval-Augmented Generation System

> **🚀 Next-Generation RAG System with Dynamic AI Agent Creation**
> 
> A revolutionary Retrieval-Augmented Generation system that uses an **Agentic Builder AI Brain** to dynamically create specialized agents for different document types, eliminating the need for manual prompt engineering.

## 🌟 **What Makes This Special?**

### **🧠 Agentic Builder - The AI Brain**
- **Automatically analyzes** uploaded documents to understand their content and purpose
- **Dynamically creates** specialized AI agents tailored to each document type
- **Self-evolving** system that learns and improves over time
- **Eliminates static, pre-written prompts** - every document gets its own intelligent agent

### **⚡ Speed Optimized **
- **Parallel processing** for document chunking and embedding generation
- **Intelligent chunking** with semantic boundaries
- **Multi-format support** (PDF, DOCX, PPTX, Excel, CSV, ZIP, Images)
- **Vector database optimization** with Pinecone v7.x and ChromaDB fallback


## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Document      │    │   Agentic        │    │   Specialized   │
│   Upload        │───▶│   Builder        │───▶│   AI Agent      │
│                 │    │   (AI Brain)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAI        │    │   Vector         │    │   Intelligent   │
│   Services      │◀───│   Database       │◀───│   Response      │
│   (RAG Core)    │    │   (Pinecone/     │    │   Generation    │
└─────────────────┘    │   ChromaDB)      │    └─────────────────┘
                       └──────────────────┘
```

## 📁 **Project Structure**

```
RAG2/
├── app/                          # Main application
│   ├── __init__.py              # App factory
│   ├── routes/                   # API endpoints
│   │   └── rag_routes.py        # Main RAG API routes
│   └── services/                 # Core services
│       ├── agentic_builder.py    # 🧠 AI Brain - Creates agents
│       ├── agentic_executor_1.py # 🚀 Mission execution agent
│       ├── document_prompts.py   # 📝 Dynamic prompt system
│       ├── openai_services.py    # 🤖 Azure OpenAI integration
│       ├── pinecone_services.py  # 🗄️ Vector database service
│       ├── utils.py              # ⚙️ Document processing utilities
│       └── hackrx_solver.py      # 🎯 Legacy HackRx solver
├── config.py                     # Configuration management
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
├── deploy-gcp.sh                # GCP deployment script
└── README.md                     # This file
```

## 🔧 **Core Components**

### **1. Agentic Builder (`agentic_builder.py`)**
The **AI Brain** that automatically analyzes uploaded documents and creates specialized AI agents tailored to each document type. It eliminates manual prompt engineering by dynamically generating intelligent agents that understand the specific domain and purpose of documents.

### **2. Agentic Executor (`agentic_executor_1.py`)**
A **specialized agent** created by the Agentic Builder that handles complex mission execution, API integrations, and multi-step workflows based on document instructions and rules.

### **3. Document Prompts (`document_prompts.py`)**
**Intelligent prompt system** that dynamically generates context-aware prompts using the Agentic Builder, replacing static, pre-written prompts with adaptive, document-specific instructions.

### **4. OpenAI Services (`openai_services.py`)**
**Core AI integration** that manages all interactions with Azure OpenAI, including parallel processing, multiple answer generation strategies, and the complete RAG pipeline workflow.

### **5. Pinecone Services (`pinecone_services.py`)**
**Vector database service** that handles high-performance similarity search using Pinecone v7.x with automatic index management and ChromaDB fallback for local development.

### **6. Utilities (`utils.py`)**
**Document processing engine** that handles multi-format file extraction, intelligent text chunking, and parallel processing to optimize performance and accuracy.

### **7. RAG Routes (`rag_routes.py`)**
**API layer** that provides HTTP endpoints for document processing, question answering, and system monitoring, handling the complete user interaction flow.

## 🚀 **Quick Start**

### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/RAG2.git
cd RAG2
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Set Environment Variables**
Create a `.env` file:
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_EMBEDDING=text-embedding-3-large
AZURE_DEPLOYMENT_COMPLETION=gpt-4

# Vector Database
CHROMA_DB_PATH=./chroma_db
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=rag-index

# Gemini API (for image processing)
GEMINI_API_KEY=your_gemini_key
```

### **4. Run the Application**
```bash
python run.py
```

## 📡 **API Endpoints**

### **Health Check**
```bash
GET /health
```

### **Process Document & Answer Questions**
```bash
POST /hackrx/run
Content-Type: application/json

{
  "documents": "https://example.com/document.pdf",
  "questions": [
    "What is the main topic?",
    "What are the key findings?"
  ]
}
```

## 🔬 **Technical Features**

### **Performance Optimization**
- **Speed**: Minimizes processing time
- **Parallel Processing**: Multi-threaded operations
- **Intelligent Caching**: LLM response caching
- **Batch Operations**: Efficient bulk processing

### **Multi-format Support**
- **Documents**: PDF, DOCX, PPTX
- **Data**: Excel, CSV
- **Archives**: ZIP files with recursive extraction
- **Images**: OCR with Gemini API integration

### **Vector Database**
- **Primary**: Pinecone v7.x with gRPC
- **Fallback**: ChromaDB for local development
- **Dimensions**: 3072 (text-embedding-3-large)
- **Metrics**: Cosine similarity

### **AI Models**
- **Embeddings**: text-embedding-3-large (3072 dimensions)
- **Completion**: GPT-4o for advanced reasoning
- **Image Processing**: Gemini 2.0 Flash Exp
- **Fallback**: GPT-4o-mini for cost optimization

### **Google Cloud Platform**
```bash
./deploy-gcp.sh
```

### **Docker**
```bash
docker build -t rag2 .
docker run -p 8080:8080 rag2
```
## 📊 **Performance Metrics**

### **Speed Optimization**
- **Document Processing**: <15 seconds
- **Question Answering**: <15 seconds
- **Total Response Time**: <60 seconds
- **Parallel Processing**: 12+ concurrent workers

### **Accuracy Improvements**
- **Enhanced Models**: GPT-4o + text-embedding-3-large
- **Semantic Matching**: 50% better with 3072 dimensions
- **Context Enhancement**: Intelligent chunk prioritization
- **Dynamic Agents**: Domain-specific expertise

---

## ⚠️ **Important Note**

**Last Commit**: We made our last commit at **12:01** while trying to merge our code into the main branch. 

If you don't want to consider that commit, you can check the **`r3-new-language`** branch - it contains the same code that we just merged into main.

---
