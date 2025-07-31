"""
Advanced Production-Ready RAG Routes
- Asynchronous Flask implementation
- ChromaDB for vector storage
- Azure OpenAI integration
- Multi-user support with conversation history
- Enhanced accuracy with improved chunking and retrieval
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
try:
    from app.services.pinecone_services import pinecone_service
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone_service = None

# Azure OpenAI
import openai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Import services
from app.services.openai_services import (
    get_embeddings, process_and_store_document, 
    query_vector_db, generate_answer, SmartCache,
    get_embeddings_optimized, query_vector_db_fast, generate_answer_fast
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

# Initialize ChromaDB with optimized settings (fallback)
try:
    chroma_client = chromadb.PersistentClient(
        path=os.environ.get("CHROMA_DB_PATH", "./chroma_db"),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=os.environ.get("CHROMA_DB_PATH", "./chroma_db")
        )
    )
    logger.info("ChromaDB initialized as fallback")
except Exception as e:
    logger.warning(f"ChromaDB initialization failed: {e}")
    chroma_client = None

# Create a thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=8)

# In-memory conversation history store (in production, use Redis or a database)
conversation_history = {}

# Cache for HackRX endpoint results
hackrx_cache = {}
CACHE_TTL = 3600  # 1 hour in seconds

# Helper function to run async functions in a thread
def run_async(coro):
    return asyncio.run(coro)

def generate_cache_key(documents_url: str, questions: List[str]) -> str:
    """Generate a unique cache key based on document URL and questions."""
    # Create a hash of the questions to make the key shorter
    questions_hash = hashlib.md5(json.dumps(questions, sort_keys=True).encode()).hexdigest()
    # Create a hash of the document URL
    url_hash = hashlib.md5(documents_url.encode()).hexdigest()
    return f"hackrx:{url_hash}:{questions_hash}"

def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached result if it exists and is not expired."""
    if cache_key in hackrx_cache:
        cached_data = hackrx_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_TTL:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_data['result']
        else:
            # Remove expired cache entry
            del hackrx_cache[cache_key]
            logger.info(f"Cache expired for key: {cache_key}")
    return None

def cache_result(cache_key: str, result: Dict):
    """Cache the result with timestamp."""
    hackrx_cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }
    logger.info(f"Cached result for key: {cache_key}")
    
    # Clean up old cache entries (optional - prevents memory leaks)
    current_time = time.time()
    expired_keys = [
        key for key, data in hackrx_cache.items()
        if current_time - data['timestamp'] > CACHE_TTL
    ]
    for key in expired_keys:
        del hackrx_cache[key]

# Health check endpoint
@rag_routes.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "RAG system is running",
        "timestamp": datetime.now().isoformat()
    })

# File upload endpoint
@rag_routes.route('/api/upload', methods=['POST'])
async def upload_files():
    """Handle multi-file upload to a specified collection"""
    request_files = await request.files
    if 'files' not in request_files:
        return jsonify({"error": "No files provided"}), 400
    
    collection_name = (await request.form).get("collection_name", "default_collection")
    results = []
    
    for file in request_files.getlist('files'):
        if file.filename == '':
            continue
            
        result = await process_and_store_document(file, collection_name, chroma_client)
        results.append({
            "filename": file.filename,
            **result
        })
    
    return jsonify({
        "collection": collection_name,
        "results": results
    })

# Delete all chunks of a specific file from a collection
@rag_routes.route('/api/collections/<collection_name>/files/<file_id>', methods=['DELETE'])
def delete_file(collection_name, file_id):
    """Delete a file with protection against empty collection"""
    try:
        collection = chroma_client.get_collection(collection_name)
        
        # First check if this is the last file
        all_files = collection.get(include=["metadatas"])
        if all_files and 'metadatas' in all_files and all_files['metadatas']:
            unique_file_ids = {meta['file_id'] for meta in all_files['metadatas']}
            
            if len(unique_file_ids) == 1 and file_id in unique_file_ids:
                return jsonify({
                    "error": "Cannot delete the last file in collection",
                    "suggestion": "Delete the entire collection instead"
                }), 400
            
            # Proceed with deletion if not the last file
            results = collection.get(where={"file_id": file_id})
            if not results or not results.get('ids'):
                return jsonify({"error": "File not found"}), 404
                
            collection.delete(ids=results['ids'])
            return jsonify({
                "deleted": len(results['ids']),
                "remaining_files": len(unique_file_ids) - 1
            })
        else:
            return jsonify({"error": "Collection is empty"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# List all unique files in a collection with metadata
@rag_routes.route('/api/collections/<collection_name>/files', methods=['GET'])
def list_files(collection_name):
    """Get all unique files in a collection with metadata"""
    try:
        collection = chroma_client.get_collection(collection_name)
        
        # Get all metadata (paginated if collection is large)
        results = collection.get(include=["metadatas"])
        
        # Aggregate by file_id
        files = {}
        if results and 'metadatas' in results and results['metadatas']:
            for meta in results['metadatas']:
                file_id = meta['file_id']
                if file_id not in files:
                    files[file_id] = {
                        "filename": meta['filename'],
                        "uploaded_at": meta['uploaded_at'],
                        "chunk_count": 1  # Initialize counter
                    }
                else:
                    files[file_id]['chunk_count'] += 1
        
        return jsonify({
            "collection": collection_name,
            "total_files": len(files),
            "files": list(files.values())  # Convert dict to list
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 404 if "not found" in str(e).lower() else 500

# Delete entire collection
@rag_routes.route('/api/collections/<collection_name>', methods=['DELETE'])
async def delete_collection(collection_name):
    """Delete the entire collection"""
    try:
        if PINECONE_AVAILABLE and pinecone_service:
            result = await pinecone_service.delete_collection(collection_name)
            deleted_count = result.get('deleted_count', 0)
        else:
            # Fallback to ChromaDB
            chroma_client.delete_collection(collection_name)
            deleted_count = 0
        
        return jsonify({
            "deleted": collection_name,
            "message": "Collection and all its files removed",
            "deleted_count": deleted_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_routes.route('/api/query', methods=['POST'])
async def query():
    """Query the vector database API endpoint."""
    try:
        data = await request.get_json()
        
        # Validate input
        if not data or 'query' not in data or 'collection_name' not in data:
            return jsonify({"status": "error", "message": "Missing required parameters"}), 400
        
        query_text = data['query']
        collection_name = data['collection_name']
        top_k = data.get('top_k', 8)  # Increased default from 5 to 8
        
        # Query the vector database
        results = await query_vector_db(query_text, collection_name, top_k, chroma_client)
        
        # Format the response
        formatted_results = {
            "matches": []
        }
        
        for i in range(len(results['documents'][0])):
            formatted_results["matches"].append({
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": 1 - results['distances'][0][i]  # Convert distance to similarity score
            })
        
        return jsonify({
            "status": "success",
            "results": formatted_results
        })
    
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@rag_routes.route('/api/generate-answer', methods=['POST'])
async def generate():
    """Generate an answer based on context and history API endpoint with enhanced accuracy."""
    try:
        start_time = datetime.now()
        data = await request.get_json()
        
        # Validate input
        if not data or 'query' not in data or 'collection_name' not in data:
            return jsonify({"status": "error", "message": "Missing required parameters"}), 400
        
        query_text = data['query']
        collection_name = data['collection_name']
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        # Optional parameters
        org_info = data.get('org_info', None)
        tone = data.get('tone', None)
        top_k = data.get('top_k', 8)  # Increased default from 5 to 8
        
        # Performance info
        include_performance_info = data.get('include_performance_info', False)
        performance_info = {}
        
        # Get or initialize conversation history
        if conversation_id not in conversation_history:
            conversation_history[conversation_id] = []
        
        # If history is provided in the request, use it instead
        if 'history' in data and isinstance(data['history'], list):
            current_history = data['history']
        else:
            current_history = conversation_history[conversation_id]
        
        # Set a timeout for the entire operation
        try:
            # Query the vector database with timeout
            vector_start = datetime.now()
            relevant_docs = await asyncio.wait_for(
                query_vector_db(query_text, collection_name, top_k, chroma_client), 
                timeout=15.0
            )
            vector_time = (datetime.now() - vector_start).total_seconds()
            performance_info['vector_search_time'] = vector_time
            
            # Generate answer with timeout
            answer_start = datetime.now()
            answer = await asyncio.wait_for(
                generate_answer(
                    query_text, 
                    relevant_docs, 
                    current_history,
                    org_info,
                    tone
                ),
                timeout=25.0
            )
            answer_time = (datetime.now() - answer_start).total_seconds()
            performance_info['answer_generation_time'] = answer_time
            
            # Store updated history - limit to 20 messages to prevent unbounded growth
            if len(current_history) > 20:
                current_history = current_history[-20:]
            conversation_history[conversation_id] = current_history
            
            total_time = (datetime.now() - start_time).total_seconds()
            performance_info['total_time'] = total_time
            
            response = {
                "status": "success",
                "answer": answer,
                "conversation_id": conversation_id
            }
            
            # Add performance info if requested
            if include_performance_info:
                response["performance"] = performance_info
            
            return jsonify(response)
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out for query: {query_text[:50]}...")
            return jsonify({
                "status": "error", 
                "message": "The request took too long to process. Please try again with a simpler query."
            }), 408
    
    except Exception as e:
        logger.error(f"Error in generate-answer endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@rag_routes.route('/api/collections', methods=['GET'])
async def list_collections():
    """List all collections in the vector database."""
    try:
        if PINECONE_AVAILABLE and pinecone_service:
            collections = await pinecone_service.list_collections()
        else:
            # Fallback to ChromaDB
            collections = chroma_client.list_collections()
            collections = [collection.name for collection in collections]
        
        return jsonify({
            "status": "success",
            "collections": collections
        })
    
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500 

# HackRX specific endpoint with enhanced accuracy
@rag_routes.route('/hackrx/run', methods=['POST'])
async def hackrx_run():
    """Optimized HackRX API endpoint with enhanced accuracy and parallel processing."""
    try:
        start_time = time.time()
        
        # Check for API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        api_key = auth_header.split(' ')[1]
        # TODO: Validate API key against your authentication system
        
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
        
        # Always process the document (no caching check)
        collection_name = "hackrx_documents"  # Define collection name
        logger.info(f"Processing document from URL: {documents_url}")
        
        # Download the PDF from the URL
        logger.info(f"Downloading document from URL: {documents_url}")
        try:
            response = requests.get(documents_url, timeout=30)
            logger.info(f"Download response status: {response.status_code}")
            logger.info(f"Download response headers: {dict(response.headers)}")
            
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
                """Read method that accepts size parameter for PyPDF2 compatibility."""
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
                """Implement seek method for PyPDF2 compatibility."""
                if whence == 0:  # SEEK_SET
                    self.position = offset
                elif whence == 1:  # SEEK_CUR
                    self.position += offset
                elif whence == 2:  # SEEK_END
                    self.position = len(self.content) + offset
                return self.position
            
            def tell(self):
                """Implement tell method for PyPDF2 compatibility."""
                return self.position
        
        file_obj = FileWrapper(response.content, "document.pdf")
        
        # Step 1: Upload and process document (create embeddings)
        document_start = time.time()
        print("\n" + "="*80)
        print("📄 DOCUMENT PROCESSING")
        print("="*80)
        print(f"🔗 Downloading from: {documents_url}")
        
        try:
            # Process and store document in ChromaDB
            result = await process_and_store_document(file_obj, collection_name, chroma_client)
            if result.get('status') != 'success':
                print(f"❌ Document processing failed: {result.get('message', 'Unknown error')}")
                return jsonify({"error": f"Failed to process document: {result.get('message', 'Unknown error')}"}), 500
            
            document_time = time.time() - document_start
            processing_mode = result.get('processing_mode', 'medium')
            text_length = result.get('text_length', 0)
            page_count = result.get('page_count', 0)
            
            print(f"✅ Document processed successfully!")
            print(f"📊 Chunks added: {result.get('chunks_added', 0)}")
            print(f"📄 Processing mode: {processing_mode.upper()}")
            print(f"📏 Document size: {text_length:,} characters, {page_count} pages")
            print(f"⏱️  Processing time: {document_time:.2f}s")
            logger.info(f"Document processed successfully: {result.get('chunks_added', 0)} chunks added in {document_time:.2f}s")
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            logger.error(f"Error processing document: {str(e)}")
            return jsonify({"error": f"Failed to process document: {str(e)}"}), 500
        
        # Step 2: Process questions with dynamic configuration
        questions_start = time.time()
        
        # Get organization info and tone
        org_info = {
            'name': Config.ORG_NAME,
            'description': Config.ORG_DESCRIPTION
        }
        tone = Config.DEFAULT_TONE
        
        async def process_question_parallel(question):
            """Process a single question with dynamic configuration."""
            try:
                # Use dynamic top_k based on processing mode
                if processing_mode == 'small':
                    top_k = Config.SMALL_DOC_TOP_K
                elif processing_mode == 'large':
                    top_k = Config.LARGE_DOC_TOP_K
                else:
                    top_k = Config.MEDIUM_DOC_TOP_K
                
                # Query vector database with dynamic configuration
                relevant_docs = await query_vector_db(question, collection_name, top_k=top_k, chroma_client=chroma_client, processing_mode=processing_mode)
                
                # Generate answer with dynamic configuration
                answer = await generate_answer(question, relevant_docs, [], org_info, tone)
                return answer
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                return f"Error processing question: {str(e)}"
        
        # Process all questions in parallel
        tasks = [process_question_parallel(question) for question in questions]
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions and print Q&A
        final_answers = []
        print("\n" + "="*80)
        print("📋 QUESTIONS AND ANSWERS")
        print("="*80)
        
        for i, result in enumerate(answers):
            if isinstance(result, Exception):
                logger.error(f"Error processing question {i}: {str(result)}")
                answer = f"Error processing question: {str(result)}"
                final_answers.append(answer)
                print(f"\n❌ Q{i+1}: {questions[i]}")
                print(f"❌ A{i+1}: {answer}")
            else:
                final_answers.append(result)
                print(f"\n✅ Q{i+1}: {questions[i]}")
                print(f"✅ A{i+1}: {result}")
        
        questions_time = time.time() - questions_start
        total_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("📊 PERFORMANCE SUMMARY")
        print("="*80)
        print(f"📄 Document Processing Time: {document_time:.2f}s")
        print(f"❓ Questions Processing Time: {questions_time:.2f}s")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print(f"📝 Questions Count: {len(questions)}")
        print(f"📄 Processing Mode: {processing_mode.upper()}")
        print(f"📏 Document Size: {text_length:,} characters, {page_count} pages")
        print(f"🎯 Target Time: {Config.TARGET_PROCESSING_TIME}s")
        print(f"⚡ Performance: {'✅ ON TARGET' if total_time <= Config.TARGET_PROCESSING_TIME else '⚠️  SLOW'}")
        print("="*80)
        
        # Prepare result
        result = {
            "answers": final_answers,
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
                "cache_ttl_hours": CACHE_TTL / 3600
            }
        })
    except Exception as e:
        logger.error(f"Error in cache status endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Cache clear endpoint
@rag_routes.route('/hackrx/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached results."""
    try:
        cleared_count = len(hackrx_cache)
        hackrx_cache.clear()
        logger.info(f"Cleared {cleared_count} cache entries")
        return jsonify({
            "message": f"Cache cleared successfully",
            "cleared_entries": cleared_count
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({"error": str(e)}), 500 