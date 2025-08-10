"""
Advanced Production-Ready RAG System
- Asynchronous Quart implementation
- ChromaDB for vector storage
- Azure OpenAI integration
- Multi-user support with conversation history
- Multiple file format support (.txt, .pdf, .docx)
"""

from app import create_app
import os
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Changed from 5000 to 5001
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.use_reloader = debug
    
    asyncio.run(serve(app, config))