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

# Helper function to run async functions in a thread
def run_async(coro):
    return asyncio.run(coro)

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