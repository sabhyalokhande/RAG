"""
Optimized RAG Routes for Speed - SPEED OPTIMIZED (<60s)
- Parallel question processing
- Fast document processing
- Optimized caching
- Intelligent reasoning with speed focus
"""

import os
import re
import uuid
import json
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Any
import time
import hashlib

# Quart and async libraries
from quart import Blueprint, request, jsonify
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests

# Document processing
import docx2txt
from pypdf import PdfReader

# Vector database
import chromadb
from chromadb.config import Settings

# Import services
from app.services.openai_services import (
    get_embeddings_parallel, process_and_store_document_fast, 
    query_vector_db_fast, generate_answer_fast, process_questions_parallel
)
from app.services.utils import (
    clean_text, extract_text_from_file, chunk_text_advanced
)
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_system.log")
    ]
)
logger = logging.getLogger(__name__)

# Create blueprint
rag_routes = Blueprint('rag_routes', __name__)

# Initialize ChromaDB with optimized settings
try:
    chroma_client = chromadb.PersistentClient(
        path=os.environ.get("CHROMA_DB_PATH", "./chroma_db"),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=os.environ.get("CHROMA_DB_PATH", "./chroma_db")
        )
    )
    logger.info("ChromaDB initialized for speed optimization")
except Exception as e:
    logger.warning(f"ChromaDB initialization failed: {e}")
    chroma_client = None

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_CHUNKING)

# Cache for HackRX endpoint results
hackrx_cache = {}
CACHE_TTL = Config.CACHE_TTL

def generate_cache_key(documents_url: str, questions: List[str]) -> str:
    """Generate cache key for speed optimization."""
    content = f"{documents_url}:{json.dumps(questions, sort_keys=True)}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached result with speed optimization."""
    if cache_key in hackrx_cache:
        cache_data = hackrx_cache[cache_key]
        if time.time() - cache_data['timestamp'] < CACHE_TTL:
            logger.info(f"Cache hit for key: {cache_key}")
            return cache_data['result']
    return None

def cache_result(cache_key: str, result: Dict):
    """Cache result with speed optimization."""
    hackrx_cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }
    logger.info(f"Cached result for key: {cache_key}")

@rag_routes.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@rag_routes.route('/hackrx/run', methods=['POST'])
async def hackrx_run():
    """Optimized HackRX API endpoint with parallel processing for speed (<60s)."""
    try:
        start_time = time.time()
        
        # Check for API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        api_key = auth_header.split(' ')[1]
        
        # Parse request data
        data = await request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        documents_url = data.get('documents')
        questions = data.get('questions', [])
        
        if not documents_url:
            return jsonify({"error": "Documents URL is required"}), 400
        
        if not questions or not isinstance(questions, list):
            return jsonify({"error": "Questions must be a non-empty list"}), 400
        
        # Generate cache key
        cache_key = generate_cache_key(documents_url, questions)
        
        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for request")
            return jsonify(cached_result)
        
        # Fast document processing
        collection_name = "hackrx_documents"
        logger.info(f"Processing document from URL: {documents_url}")
        
        # Download the PDF from the URL
        logger.info(f"Downloading document from URL: {documents_url}")
        try:
            response = requests.get(documents_url, timeout=Config.REQUEST_TIMEOUT)
            logger.info(f"Download response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to download document: HTTP {response.status_code}")
                return jsonify({"error": f"Failed to download document: {response.status_code}"}), 400
            
            logger.info(f"Successfully downloaded {len(response.content)} bytes")
            
        except Exception as download_error:
            logger.error(f"Error downloading document: {download_error}")
            return jsonify({"error": f"Failed to download document: {str(download_error)}"}), 400
        
        # Create a file-like object for processing
        class FileWrapper:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename
                self.read_called = False
                self.position = 0
            
            def read(self, size=None):
                if not self.read_called:
                    self.read_called = True
                    if size is None:
                        return self.content
                    else:
                        result = self.content[:size]
                        self.content = self.content[size:]
                        return result
                return b''
            
            def seek(self, offset, whence=0):
                if whence == 0:
                    self.position = offset
                elif whence == 1:
                    self.position += offset
                elif whence == 2:
                    self.position = len(self.content) + offset
                return self.position
            
            def tell(self):
                return self.position
        
        file_obj = FileWrapper(response.content, "document.pdf")
        
        # Step 1: Fast document processing
        document_start = time.time()
        print("\n" + "="*80)
        print("📄 FAST DOCUMENT PROCESSING")
        print("="*80)
        print(f"🔗 Downloading from: {documents_url}")
        
        # Process document with parallel operations
        document_result = await process_and_store_document_fast(file_obj, collection_name, chroma_client)
        
        if "error" in document_result:
            logger.error(f"Document processing failed: {document_result['error']}")
            return jsonify({"error": f"Document processing failed: {document_result['error']}"}), 400
        
        document_time = time.time() - document_start
        print(f"✅ Document processed in {document_time:.2f}s")
        print(f"📊 Chunks processed: {document_result.get('chunks_processed', 0)}")
        
        # Step 2: Fast parallel question processing
        questions_start = time.time()
        print("\n" + "="*80)
        print("❓ FAST PARALLEL QUESTION PROCESSING")
        print("="*80)
        print(f"📝 Processing {len(questions)} questions in parallel")
        
        # Process all questions in parallel
        answers = await process_questions_parallel(questions, collection_name, chroma_client)
        
        # Enhanced cleanup and accuracy validation
        import re
        cleaned_answers = []
        for answer in answers:
            cleaned_answer = answer
            
            # Remove literal \n strings
            cleaned_answer = cleaned_answer.replace('\\n', ' ')
            
            # Remove ** characters
            cleaned_answer = cleaned_answer.replace('**', '')
            
            # Remove any remaining backslashes
            cleaned_answer = cleaned_answer.replace('\\', '')
            
            # Remove multiple spaces and normalize
            cleaned_answer = re.sub(r'\s+', ' ', cleaned_answer)
            
            # Remove multiple newlines
            cleaned_answer = re.sub(r'\n\s*\n', '\n', cleaned_answer)
            
            # Final cleanup
            cleaned_answer = cleaned_answer.strip()
            
            # Accuracy validation - ensure answer is substantial
            if len(cleaned_answer) < 10:
                cleaned_answer = "Based on the provided context, I cannot provide a complete answer. Please provide more specific information or clarify your question."
            
            cleaned_answers.append(cleaned_answer)
        
        questions_time = time.time() - questions_start
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("📋 QUESTIONS AND ANSWERS")
        print("="*80)
        
        for i, answer in enumerate(cleaned_answers):
            print(f"\n✅ Q{i+1}: {questions[i]}")
            print(f"✅ A{i+1}: {answer[:200]}..." if len(answer) > 200 else f"✅ A{i+1}: {answer}")
        
        print("\n" + "="*80)
        print("📊 PERFORMANCE SUMMARY")
        print("="*80)
        print(f"📄 Document Processing Time: {document_time:.2f}s")
        print(f"❓ Questions Processing Time: {questions_time:.2f}s")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"📝 Questions Count: {len(questions)}")
        print(f"🎯 Target Time: {Config.TARGET_PROCESSING_TIME}s")
        print(f"⚡ Performance: {'✅ FAST' if total_time <= Config.TARGET_PROCESSING_TIME else '⚠️  SLOW'}")
        print("="*80)
        
        # Prepare result
        result = {
            "answers": cleaned_answers,
            "performance": {
                "document_processing_time": round(document_time, 2),
                "questions_processing_time": round(questions_time, 2),
                "total_time": round(total_time, 2),
                "questions_count": len(questions)
            }
        }
        
        # Cache the result
        cache_result(cache_key, result)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in hackrx/run endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Cache management endpoint
@rag_routes.route('/hackrx/cache/status', methods=['GET'])
def cache_status():
    """Get cache statistics and status."""
    try:
        current_time = time.time()
        active_entries = 0
        expired_entries = 0
        
        for key, data in hackrx_cache.items():
            if current_time - data['timestamp'] < CACHE_TTL:
                active_entries += 1
            else:
                expired_entries += 1
        
        return jsonify({
            "cache_status": {
                "total_entries": len(hackrx_cache),
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "cache_ttl_seconds": CACHE_TTL,
                "memory_usage_mb": len(hackrx_cache) * 0.001  # Rough estimate
            }
        })
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return jsonify({"error": str(e)}), 500

@rag_routes.route('/hackrx/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache."""
    try:
        global hackrx_cache
        hackrx_cache.clear()
        logger.info("Cache cleared successfully")
        return jsonify({"status": "success", "message": "Cache cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": str(e)}), 500

def optimize_for_speed():
    """Apply speed optimizations to routes."""
    global executor
    
    # Optimize thread pool
    executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_CHUNKING)
    
    # Clear caches for fresh start
    hackrx_cache.clear()
    
    logger.info("Speed optimizations applied to routes")

# Initialize optimizations
optimize_for_speed() 