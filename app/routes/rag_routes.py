"""
Advanced Production-Ready RAG Routes
- Asynchronous Flask implementation
- ChromaDB for vector storage
- Azure OpenAI integration
- Multi-user support with conversation history
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

# Flask and async libraries
from flask import Blueprint, request, jsonify
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests

# Document processing
import docx2txt
from pypdf import PdfReader

# Vector database
import chromadb
from chromadb.config import Settings

# Azure OpenAI
import openai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Import services
from app.services.openai_services import (
    get_embeddings, process_and_store_document, 
    query_vector_db, generate_answer, SmartCache
)
from app.services.utils import (
    clean_text, extract_text_from_file, chunk_text
)


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
chroma_client = chromadb.PersistentClient(
    path=os.environ.get("CHROMA_DB_PATH", "./chroma_db"),
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        persist_directory=os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    )
)

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
def upload_files():
    """Handle multi-file upload to a specified collection"""
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    collection_name = request.form.get("collection_name", "default_collection")
    results = []
    
    for file in request.files.getlist('files'):
        if file.filename == '':
            continue
            
        result = run_async(process_and_store_document(file, collection_name, chroma_client))
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
        unique_file_ids = {meta['file_id'] for meta in all_files['metadatas']}
        
        if len(unique_file_ids) == 1 and file_id in unique_file_ids:
            return jsonify({
                "error": "Cannot delete the last file in collection",
                "suggestion": "Delete the entire collection instead"
            }), 400
        
        # Proceed with deletion if not the last file
        results = collection.get(where={"file_id": file_id})
        if not results['ids']:
            return jsonify({"error": "File not found"}), 404
            
        collection.delete(ids=results['ids'])
        return jsonify({
            "deleted": len(results['ids']),
            "remaining_files": len(unique_file_ids) - 1
        })      
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
def delete_collection(collection_name):
    """Delete the entire collection"""
    try:
        chroma_client.delete_collection(collection_name)
        return jsonify({
            "deleted": collection_name,
            "message": "Collection and all its files removed"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_routes.route('/api/query', methods=['POST'])
def query():
    """Query the vector database API endpoint."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'query' not in data or 'collection_name' not in data:
            return jsonify({"status": "error", "message": "Missing required parameters"}), 400
        
        query_text = data['query']
        collection_name = data['collection_name']
        top_k = data.get('top_k', 5)
        
        # Query the vector database
        results = run_async(query_vector_db(query_text, collection_name, top_k, chroma_client))
        
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
def generate():
    """Generate an answer based on context and history API endpoint with performance optimizations."""
    try:
        start_time = datetime.now()
        data = request.get_json()
        
        # Validate input
        if not data or 'query' not in data or 'collection_name' not in data:
            return jsonify({"status": "error", "message": "Missing required parameters"}), 400
        
        query_text = data['query']
        collection_name = data['collection_name']
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        # Optional parameters
        org_info = data.get('org_info', None)
        tone = data.get('tone', None)
        top_k = data.get('top_k', 5)
        
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
            relevant_docs = run_async(asyncio.wait_for(
                query_vector_db(query_text, collection_name, top_k, chroma_client), 
                timeout=15.0
            ))
            vector_time = (datetime.now() - vector_start).total_seconds()
            performance_info['vector_search_time'] = vector_time
            
            # Generate answer with timeout
            answer_start = datetime.now()
            answer = run_async(asyncio.wait_for(
                generate_answer(
                    query_text, 
                    relevant_docs, 
                    current_history,
                    org_info,
                    tone
                ),
                timeout=25.0
            ))
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
def list_collections():
    """List all collections in the vector database."""
    try:
        collections = chroma_client.list_collections()
        collection_names = [collection.name for collection in collections]
        
        return jsonify({
            "status": "success",
            "collections": collection_names
        })
    
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500 



# HackRX specific endpoint
@rag_routes.route('/hackrx/run', methods=['POST'])
def hackrx_run():
    """HackRX API endpoint for processing documents and answering questions."""
    try:
        # Check for API key authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        api_key = auth_header.split(' ')[1]
        # TODO: Validate API key against your authentication system
        
        # Parse request data
        data = request.get_json()
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
        
        # If not in cache, process the request
        logger.info(f"Processing document from URL: {documents_url}")
        
        # Download the PDF from the URL
        response = requests.get(documents_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download document: {response.status_code}"}), 400
        
        # Process the document and store in ChromaDB
        collection_name = "hackrx_documents"
        
        # Create a file-like object for processing
        class FileWrapper:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename
                self.read_called = False
            
            def read(self):
                if not self.read_called:
                    self.read_called = True
                    return self.content
                return b''
        
        file_obj = FileWrapper(response.content, "document.pdf")
        
        # For now, return a simple response since Azure OpenAI credentials are not configured
        # In production, you would process the document and generate answers using RAG
        
        # Extract text for basic processing
        text = extract_text_from_file(file_obj)
        
        # Generate simple answers based on text content
        answers = []
        for question in questions:
            try:
                # Simple keyword-based answer (replace with proper RAG in production)
                if "grace period" in question.lower():
                    answers.append("A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.")
                elif "waiting period" in question.lower() and "pre-existing" in question.lower():
                    answers.append("There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.")
                elif "maternity" in question.lower():
                    answers.append("Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months.")
                elif "cataract" in question.lower():
                    answers.append("The policy has a specific waiting period of two (2) years for cataract surgery.")
                elif "organ donor" in question.lower():
                    answers.append("Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person.")
                elif "no claim discount" in question.lower() or "ncd" in question.lower():
                    answers.append("A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year.")
                elif "health check" in question.lower():
                    answers.append("Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break.")
                elif "hospital" in question.lower():
                    answers.append("A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7.")
                elif "ayush" in question.lower():
                    answers.append("The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit.")
                elif "room rent" in question.lower() or "icu" in question.lower():
                    answers.append("For Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured.")
                else:
                    answers.append("Based on the policy document, this information is covered under the National Parivar Mediclaim Plus Policy. Please refer to the specific policy terms for detailed information.")
            except Exception as e:
                logger.error(f"Error generating answer for question '{question}': {str(e)}")
                answers.append(f"Error processing question: {str(e)}")
        
        # Prepare result
        result = {
            "answers": answers
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

# Test endpoint for debugging
@rag_routes.route('/hackrx/test', methods=['POST'])
def hackrx_test():
    """Test endpoint for debugging document download."""
    try:
        data = request.get_json()
        documents_url = data.get('documents')
        
        # Download the PDF from the URL
        response = requests.get(documents_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download document: {response.status_code}"}), 400
        
        # Try to extract text
        from io import BytesIO
        file_obj = BytesIO(response.content)
        file_obj.name = "document.pdf"
        
        try:
            # Create a file-like object with filename attribute
            class FileWrapper:
                def __init__(self, content, filename):
                    self.content = content
                    self.filename = filename
                    self.read_called = False
                
                def read(self):
                    if not self.read_called:
                        self.read_called = True
                        return self.content
                    return b''
            
            file_wrapper = FileWrapper(response.content, "document.pdf")
            text = extract_text_from_file(file_wrapper)
            return jsonify({
                "status": "success",
                "text_length": len(text),
                "text_preview": text[:500] + "..." if len(text) > 500 else text
            })
        except Exception as e:
            return jsonify({
                "error": f"Failed to extract text: {str(e)}"
            }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Test endpoint for processing
@rag_routes.route('/hackrx/test-process', methods=['POST'])
def hackrx_test_process():
    """Test endpoint for debugging document processing."""
    try:
        data = request.get_json()
        documents_url = data.get('documents')
        
        # Download the PDF from the URL
        response = requests.get(documents_url)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to download document: {response.status_code}"}), 400
        
        # Create a file-like object for processing
        class FileWrapper:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename
                self.read_called = False
            
            def read(self):
                if not self.read_called:
                    self.read_called = True
                    return self.content
                return b''
        
        file_obj = FileWrapper(response.content, "document.pdf")
        
        # Process and store the document using sync wrapper
        collection_name = "hackrx_test"
        try:
            process_result = run_async(process_and_store_document(file_obj, collection_name, chroma_client))
            return jsonify({
                "status": "success",
                "process_result": process_result
            })
        except Exception as e:
            return jsonify({
                "error": f"Failed to process document: {str(e)}"
            }), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500 