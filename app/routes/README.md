# Routes Directory - RAG System with Agentic AI Integration

## Overview
This directory contains the API routes that implement a high-speed RAG (Retrieval-Augmented Generation) system with intelligent agentic AI integration. The system automatically routes requests to specialized agents created by the Agentic Builder.

## Main Components

### 🚀 RAG Routes (`rag_routes.py`)
High-performance API endpoints that integrate with the agentic architecture:

**Key Features:**
- **Speed Optimized**: <60s response times with parallel processing
- **Intelligent Routing**: Automatically detects document types and routes to appropriate agents
- **Agentic Integration**: Seamlessly works with dynamically created agents
- **Parallel Processing**: Multi-threaded document and question processing

**Endpoints:**
- `/health` - System health check
- `/hackrx/run` - Main execution endpoint with agentic routing
- `/hackrx/logs` - Request logging and analytics

## How It Works

### 1. Document Processing
- Accepts various file formats (PDF, DOCX, TXT)
- Processes documents in parallel for speed optimization
- Extracts text and creates vector embeddings
- Stores in ChromaDB for fast retrieval

### 2. Intelligent Agentic Routing
The system automatically:
- Analyzes document content and type
- Routes to appropriate specialized agents (Mission Execution, Medical, Legal, etc.)
- Uses the Agentic Builder to create new agents if needed
- Provides high-confidence responses with agent metadata

### 3. Speed Optimization
- **Parallel Processing**: Multiple questions processed simultaneously
- **Optimized Caching**: Intelligent caching strategies
- **Background Logging**: Non-blocking request logging
- **Thread Pool Management**: Efficient resource utilization

## Agentic Integration

The RAG system seamlessly integrates with the agentic architecture:

```python
# Automatic agent detection and routing
from app.services.agentic_executor_1 import (
    mission_execution_agent, 
    should_use_mission_execution_agent
)

# The system automatically detects document types and routes accordingly
if should_use_mission_execution_agent(query, document_url):
    result = mission_execution_agent.execute_mission()
```

## Performance Features

✅ **Sub-60 Second Response Times**
✅ **Parallel Document Processing**
✅ **Intelligent Caching**
✅ **Background Logging**
✅ **Multi-threaded Operations**
✅ **Automatic Agent Routing**

## Configuration

The system uses environment variables for configuration:
- `CHROMA_DB_PATH`: Vector database storage location
- `MAX_WORKERS_CHUNKING`: Maximum parallel processing threads

## Architecture Benefits

- **No Hardcoded Routing**: Intelligent detection and routing
- **Self-Optimizing**: Learns from request patterns
- **Scalable**: Easy to add new document types and agents
- **High Performance**: Optimized for speed and efficiency
- **Agentic Intelligence**: Leverages specialized AI agents

## Example Request Flow

1. **Document Upload**: User uploads document
2. **Content Analysis**: System analyzes document type and content
3. **Agent Selection**: Routes to appropriate specialized agent
4. **Parallel Processing**: Processes questions simultaneously
5. **Intelligent Response**: Returns high-confidence answers with agent metadata
6. **Learning**: System learns from successful operations

This architecture eliminates the need for hardcoded routing logic while providing intelligent, high-performance document processing capabilities.
