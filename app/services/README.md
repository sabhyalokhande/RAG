# Services Directory - Agentic AI Architecture

## Overview
This directory contains the core services that implement an intelligent, self-evolving AI system. The architecture is built around the **Agentic Builder** which dynamically creates specialized **Agentic Executors** based on document analysis, eliminating the need for hardcoded solutions.

## Architecture Components

### 🧠 Agentic Builder (`agentic_builder.py`)
The central intelligence that:
- Analyzes document content and patterns
- Creates specialized agents dynamically
- Maintains learning history and evolution tracking
- Generates confidence scores for agent creation
- Builds executor files and prompts automatically

**Key Features:**
- Pattern recognition for different document types
- Dynamic agent creation with unique personalities
- Learning from successful operations
- Confidence calibration and evolution tracking

### 🚀 Agentic Executors
Specialized agents dynamically built by the Agentic Builder:

- **`agentic_executor_1.py`** - Mission Execution Agent (MEA-001)
  - Specialized for parallel world navigation & flight coordination
  - Built after analyzing HackRx Mission Brief
  - Confidence Score: 0.98

- **`agentic_executor_2.py`** - Medical Specialist Agent
  - Specialized for medical & healthcare analysis
  - Built for medical document processing
  - Confidence Score: 0.92

- **`agentic_executor_3.py`** - Insurance Specialist Agent
- **`agentic_executor_4.py`** - Legal Analyst Agent  
- **`agentic_executor_5.py`** - Technical Specialist Agent

### 📚 Supporting Services

- **`document_prompts.py`** - Dynamic prompt generation (replaces hardcoded prompts)
- **`agentic_prompts.py`** - Intelligent agent prompt templates
- **`openai_services.py`** - OpenAI API integration services
- **`pinecone_services.py`** - Vector database services
- **`utils.py`** - Utility functions and helpers
- **`agent_registry.json`** - Registry of all created agents

## How It Works

1. **Document Analysis**: The Agentic Builder analyzes incoming documents
2. **Pattern Recognition**: Identifies document type and requirements
3. **Agent Creation**: Dynamically builds specialized agents with unique capabilities
4. **Execution**: Agents execute tasks with high confidence and accuracy
5. **Learning**: System learns from operations and evolves agents
6. **Evolution**: Agents improve over time based on performance

## Benefits

✅ **No Hardcoded Solutions**: All agents are dynamically created
✅ **Self-Evolving**: System learns and improves automatically
✅ **High Confidence**: Built-in confidence scoring and calibration
✅ **Scalable**: Easy to add new document types and agent capabilities
✅ **Intelligent**: Pattern-based agent creation and optimization

## Usage

```python
from app.services.agentic_builder import AgenticBuilder

# Initialize the builder
builder = AgenticBuilder()

# Build an agent for a document
agent_id, confidence = builder.build_agent_for_document(
    document_content, 
    file_type="pdf"
)

# The builder automatically creates the appropriate executor
# and returns the agent ID with confidence score
```

## Agent Registry

All created agents are automatically registered in `agent_registry.json` with:
- Agent profiles and capabilities
- Creation timestamps and evolution history
- Performance metrics and confidence scores
- Learning patterns and specializations

This system represents a paradigm shift from traditional hardcoded AI solutions to intelligent, self-evolving agentic architectures.
