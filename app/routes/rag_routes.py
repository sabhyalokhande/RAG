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
import threading

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
    query_vector_db_fast, generate_answer_fast, process_questions_parallel,
    process_questions_parallel_concise, process_questions_parallel_dynamic
)
from app.services.utils import (
    clean_text, extract_text_from_file, chunk_text_advanced,
    get_raw_data_pptx, get_raw_data_image, get_raw_data_zip
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

# Simple logging lock to prevent file conflicts
log_lock = threading.Lock()

def log_request_background(document_url: str, questions: List[str], answers: List[str]):
    """Log request data to file in background without affecting speed."""
    def write_log():
        try:
            with log_lock:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "document_url": document_url,
                    "questions": questions,
                    "answers": answers
                }
                
                with open("request_logs.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            # Silently fail to not affect performance
            pass
    
    # Run in background thread to avoid blocking
    threading.Thread(target=write_log, daemon=True).start()

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
        # Use unique collection name for each document to avoid conflicts
        import hashlib
        collection_name = f"hackrx_doc_{hashlib.md5(documents_url.encode()).hexdigest()[:8]}"
        logger.info(f"Processing document from URL: {documents_url}")
        logger.info(f"Using collection: {collection_name}")
        
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
            return jsonify({"error": f"Failed to download document: {str(download_error)}"}), 400        # Determine file type and extract text
        logger.info(f"Processing file: {documents_url}")
        
        # Check if it's an image URL (check for image extensions anywhere in the URL before query parameters)
        url_path = documents_url.split('?')[0]  # Remove query parameters
        if any(url_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
            logger.info("Detected image file, using OCR extraction")
            raw_text = get_raw_data_image(documents_url)
            logger.info(f"OCR extracted text length: {len(raw_text)}")
            logger.info(f"OCR extracted text preview: {raw_text[:500]}...")
        else:
            # For PDF and other documents, use existing logic
            logger.info("Processing as PDF document")
            try:
                pdf_reader = PdfReader(BytesIO(response.content))
                raw_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    raw_text += page_text
                    logger.info(f"Extracted text from page {page_num + 1}: {len(page_text)} characters")
                
                logger.info(f"Total PDF text extracted: {len(raw_text)} characters")
            except Exception as pdf_error:
                logger.error(f"Error processing PDF: {pdf_error}")
                raw_text = ""
          # Step 1: Fast document processing
        document_start = time.time()
        print("\n" + "="*80)
        print("📄 FAST DOCUMENT PROCESSING")
        print("="*80)
        print(f"🔗 Processing from: {documents_url}")
        
        # Process document with text directly instead of file_obj
        if not raw_text:
            logger.error("No text extracted from document")
            return jsonify({"error": "No text extracted from document"}), 400
          # Create a simple text wrapper for processing
        class TextWrapper:
            def __init__(self, text, filename="document"):
                self.text = text
                self.filename = filename
            
            def read(self):
                return self.text.encode('utf-8')
        
        # Clear existing collection to ensure fresh data
        try:
            chroma_client.delete_collection(collection_name)
            logger.info(f"Cleared existing collection: {collection_name}")
        except:
            logger.info(f"Collection {collection_name} didn't exist, creating new one")
        
        text_obj = TextWrapper(raw_text)
        document_result = await process_and_store_document_fast(text_obj, collection_name, chroma_client)
        
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
        
        # Process all questions in parallel with document-specific prompts
        answers = await process_questions_parallel(questions, collection_name, chroma_client, document_url=documents_url)
        
        questions_time = time.time() - questions_start
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("📋 QUESTIONS AND ANSWERS")
        print("="*80)
        
        for i, answer in enumerate(answers):
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
            "answers": answers,
            "performance": {
                "document_processing_time": round(document_time, 2),
                "questions_processing_time": round(questions_time, 2),
                "total_time": round(total_time, 2),
                "questions_count": len(questions)
            }
        }
        
        # Cache the result
        cache_result(cache_key, result)
        
        # Log request data in background
        log_request_background(documents_url, questions, answers)
        
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

@rag_routes.route('/hackrx/logs', methods=['GET'])
def get_request_logs():
    """Get recent request logs (last 50 entries)."""
    try:
        logs = []
        if os.path.exists("request_logs.jsonl"):
            with open("request_logs.jsonl", "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get last 50 entries
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                for line in recent_lines:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        continue
        
        return jsonify({
            "total_logs": len(logs),
            "logs": logs
        })
    except Exception as e:
        logger.error(f"Error getting request logs: {e}")
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

@rag_routes.route('/hackrx/upload', methods=['POST'])
async def hackrx_upload():
    """Optimized file upload endpoint for HackRX with new formats support."""
    try:
        # Check for API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        api_key = auth_header.split(' ')[1]
        
        # Parse form data
        form_data = await request.form
        if not form_data:
            return jsonify({"error": "No form data provided"}), 400
        
        # Extract document and questions
        document = form_data.get('document')
        questions = form_data.get('questions', '')
        
        if not document:
            return jsonify({"error": "Document file is required"}), 400
        
        # Validate and process document file
        file_storage = document
        file_name = file_storage.filename
        
        # Save the uploaded file temporarily
        temp_dir = "./temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file_name)
        
        # Update file extension validation
        if not any(file_name.lower().endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.csv', '.xlsx', '.xls', '.pptx', '.png', '.jpg', '.jpeg', '.zip']):
            logger.error("Unsupported file extension")
            return jsonify({"success": False, "message": "Unsupported file extension"}), 400
        
        # Add processing logic for new formats
        elif file_name.lower().endswith('.pptx'):
            raw_text = get_raw_data_pptx(file_path)
        elif file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raw_text = get_raw_data_image(file_path)
        elif file_name.lower().endswith('.zip'):
            raw_text = get_raw_data_zip(file_path)
        
        # For other formats, use existing text extraction
        else:
            raw_text = extract_text_from_file(file_path)
        
        logger.info(f"Extracted raw text from {file_name} ({len(raw_text)} characters)")
        
        # Further processing and question answering logic here...
        
        return jsonify({"success": True, "message": "File uploaded and processed successfully"}), 200
    except Exception as e:
        logger.error(f"Error in hackrx/upload endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500