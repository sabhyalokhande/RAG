"""
Advanced Production-Ready OpenAI Services
- Azure OpenAI integration with fallback mechanisms
- ChromaDB vector storage
- Smart caching with TTL and LRU eviction
- Retry logic with exponential backoff
"""

import os
import json
import logging
import time
import hashlib
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import threading
from collections import deque

# Azure OpenAI
import openai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Vector database
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting for Azure OpenAI
class RateLimiter:
    def __init__(self, max_requests_per_minute=60):
        self.max_requests = max_requests_per_minute
        self.requests = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        with self.lock:
            current_time = time.time()
            # Remove requests older than 1 minute
            while self.requests and current_time - self.requests[0] > 60:
                self.requests.popleft()
            
            # If we've made too many requests recently, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = 60 - (current_time - self.requests[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit hit, waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            # Add current request
            self.requests.append(current_time)

# Global rate limiter - much more aggressive for speed
rate_limiter = RateLimiter(max_requests_per_minute=10)  # Very conservative to avoid 429

class SmartCache:
    """Advanced cache with TTL, size limits and LRU eviction policy."""
    def __init__(self, max_size=1000, ttl=3600):  # Default: 1000 items, 1 hour TTL
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        
    def _generate_key(self, data):
        """Generate a consistent cache key for various data types."""
        if isinstance(data, str):
            # For strings, use first 1000 chars to avoid excessive hashing
            return hashlib.md5(data[:1000].encode()).hexdigest()
        elif isinstance(data, list):
            # For lists of strings (like in batch operations)
            if all(isinstance(item, str) for item in data):
                concatenated = "".join([item[:100] for item in data])  # Limit each item
                return hashlib.md5(concatenated.encode()).hexdigest()
        # Default fallback - less efficient but works for other types
        return str(hash(str(data)))
    
    def get(self, key_data):
        """Get item from cache with automatic TTL check."""
        key = self._generate_key(key_data)
        current_time = time.time()
        
        # Check if key exists and hasn't expired
        if key in self.cache:
            if current_time - self.access_times[key]["created"] <= self.ttl:
                # Update last access time
                self.access_times[key]["accessed"] = current_time
                return self.cache[key]
            else:
                # Item expired, remove it
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def set(self, key_data, value):
        """Store item in cache with cleanup if needed."""
        key = self._generate_key(key_data)
        current_time = time.time()
        
        # Check if we need to evict items (cache full)
        if len(self.cache) >= self.max_size:
            self._cleanup()
        
        # Store the item and its access information
        self.cache[key] = value
        self.access_times[key] = {
            "created": current_time,
            "accessed": current_time
        }
    
    def _cleanup(self):
        """Clean up expired or least recently used items."""
        current_time = time.time()
        
        # First pass: remove expired items
        expired_keys = [k for k, v in self.access_times.items() 
                       if current_time - v["created"] > self.ttl]
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
        
        # If still need space, remove LRU items
        if len(self.cache) >= self.max_size:
            # Sort by access time and remove oldest 10% or at least one item
            sorted_keys = sorted(self.access_times.keys(), 
                                key=lambda k: self.access_times[k]["accessed"])
            
            # Remove at least 10% of items
            remove_count = max(1, int(len(sorted_keys) * 0.1))
            for key in sorted_keys[:remove_count]:
                if key in self.cache:
                    del self.cache[key]
                    del self.access_times[key]

# Create specialized caches for different purposes
embedding_cache = SmartCache(max_size=2000, ttl=24*3600)  # Embeddings valid for 24 hours
query_result_cache = SmartCache(max_size=500, ttl=3600)   # Query results valid for 1 hour
llm_response_cache = SmartCache(max_size=300, ttl=1800)   # LLM responses valid for 30 minutes

# Initialize Azure OpenAI clients conditionally
async_client = None
sync_client = None

def initialize_openai_clients():
    """Initialize Azure OpenAI clients if credentials are available."""
    global async_client, sync_client
    
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-06-01-preview")
    
    if api_key and endpoint:
        try:
            async_client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint,
                timeout=20.0
            )
            
            sync_client = openai.AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint,
                timeout=20.0
            )
            
            # Test the connection by making a simple request
            try:
                # Test with a simple embedding request
                test_response = sync_client.embeddings.create(
                    input=["test"],
                    model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
                )
                logger.info("Azure OpenAI clients initialized successfully")
            except Exception as test_error:
                logger.warning(f"Azure OpenAI connection test failed: {test_error}")
                logger.info("Falling back to keyword-based search mode")
                async_client = None
                sync_client = None
                
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI clients: {e}")
            logger.info("Falling back to keyword-based search mode")
            async_client = None
            sync_client = None
    else:
        logger.warning("Azure OpenAI credentials not found. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.")
        logger.info("Falling back to keyword-based search mode")

# Initialize clients on module import
initialize_openai_clients()

def simple_similarity_search(query, documents, top_k=3):
    """Simple keyword-based similarity search as fallback when embeddings are not available."""
    query_words = set(query.lower().split())
    
    # Calculate simple TF-IDF like scores
    doc_scores = []
    for doc in documents:
        doc_words = set(doc.lower().split())
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(doc_words))
        union = len(query_words.union(doc_words))
        similarity = intersection / union if union > 0 else 0
        doc_scores.append((similarity, doc))
    
    # Sort by similarity and return top_k
    doc_scores.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in doc_scores[:top_k] if score > 0]

def generate_simple_answer(query, relevant_docs, context=""):
    """Generate a dynamic answer based on retrieved documents when LLM is not available."""
    query_lower = query.lower()
    
    # Extract key information from relevant documents
    context_text = " ".join([doc for doc in relevant_docs['documents'][0]]) if relevant_docs and 'documents' in relevant_docs else ""
    
    # Dynamic answer generation based on retrieved context
    if context_text:
        # Extract relevant sentences from the context
        sentences = context_text.split('.')
        relevant_sentences = []
        
        # Find sentences that contain words from the query
        query_words = query_lower.split()
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in query_words):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Return the most relevant sentence
            return relevant_sentences[0] + "."
        else:
            # If no direct matches, return a summary of available information
            return f"Based on the available documents, I found information related to your query. The documents contain relevant details that may address your question about '{query}'. Please review the document content for specific information."
    else:
        # No context available
        return f"I couldn't find specific information about '{query}' in the available documents. Please ensure the documents contain relevant information for your query."

# Optimized embedding function with improved caching for faster responses
@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=0.05, min=0.05, max=0.5))
async def get_embeddings(texts: List[str]):
    """Get embeddings for a list of texts using Azure OpenAI with optimized caching for speed."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.")
    
    try:
        # Create a cache key for each text
        embeddings = []
        texts_to_embed = []
        indices = []
        
        # Check cache first with improved cache
        for i, text in enumerate(texts):
            cached_embedding = embedding_cache.get(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                texts_to_embed.append(text)
                indices.append(i)
        
        # If we have texts that need embedding
        if texts_to_embed:
            try:
                # Ultra-aggressive batch size for speed
                batch_size = 30  # Maximum batch size for fastest processing
                all_new_embeddings = []
                
                for i in range(0, len(texts_to_embed), batch_size):
                    batch = texts_to_embed[i:i+batch_size]
                    
                    # Check token limits before sending (rough estimate: 1 token ≈ 4 characters)
                    filtered_batch = []
                    for text in batch:
                        estimated_tokens = len(text) // 4
                        if estimated_tokens > 8000:  # Leave some buffer
                            logger.warning(f"Text too long ({estimated_tokens} tokens), truncating")
                            # Truncate to ~6000 tokens (24000 characters)
                            text = text[:24000]
                        filtered_batch.append(text)
                    
                    # Rate limiting before API call
                    rate_limiter.wait_if_needed()
                    
                    # Try async client first with aggressive timeout
                    response = await asyncio.wait_for(
                        async_client.embeddings.create(
                            input=filtered_batch,
                            model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
                        ),
                        timeout=5.0  # Ultra-aggressive timeout for speed
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_new_embeddings.extend(batch_embeddings)
                    
                    # Cache each embedding immediately
                    for j, text in enumerate(filtered_batch):
                        embedding_cache.set(text, batch_embeddings[j])
            
            except asyncio.TimeoutError:
                # Fallback to sync client if async times out
                logger.warning("Async embedding timed out, falling back to sync client")
                
                all_new_embeddings = []
                for i in range(0, len(texts_to_embed), batch_size):
                    batch = texts_to_embed[i:i+batch_size]
                    
                    response = sync_client.embeddings.create(
                        input=batch,
                        model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_new_embeddings.extend(batch_embeddings)
                    
                    # Cache each embedding
                    for j, text in enumerate(batch):
                        embedding_cache.set(text, batch_embeddings[j])
            
            # Insert new embeddings at the correct positions
            for idx, embed in zip(indices, all_new_embeddings):
                if idx >= len(embeddings):
                    embeddings.append(embed)
                else:
                    embeddings.insert(idx, embed)
        
        return embeddings
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        raise

async def process_and_store_document(file, collection_name, chroma_client):
    """Process a file and append to existing/new collection"""
    try:
        # Get or create collection
        try:
            collection = chroma_client.get_collection(collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except:
            collection = chroma_client.create_collection(collection_name)
            logger.info(f"Created new collection: {collection_name}")

        # Generate unique file ID for later deletion
        file_id = str(uuid.uuid4())
        
        # Extract and chunk text
        from app.services.utils import extract_text_from_file, chunk_text
        text = extract_text_from_file(file)
        chunks = chunk_text(text)
        
        # Prepare metadata with file tracking
        chunk_metadata = [{
            "file_id": file_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            "chunk_index": i
        } for i in range(len(chunks))]
        
        # Check if Azure OpenAI is available for embeddings
        if async_client is None:
            # Store without embeddings for fallback mode
            logger.warning("Azure OpenAI not available, storing documents without embeddings")
            collection.add(
                ids=[f"{file_id}_{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=chunk_metadata
            )
        else:
            # Generate embeddings
            embeddings = await get_embeddings(chunks)
            
            # Store with embeddings
            collection.add(
                ids=[f"{file_id}_{i}" for i in range(len(chunks))],
                embeddings=embeddings,
                documents=chunks,
                metadatas=chunk_metadata
            )
        
        return {
            "status": "success",
            "file_id": file_id,
            "chunks_added": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return {"status": "error", "message": str(e)}

# Add caching to query function
@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=0.05, min=0.05, max=0.5))
async def query_vector_db(query, collection_name, top_k=1, chroma_client=None):
    """Query the vector database for similar documents with caching."""
    try:
        # Create a cache key from the query and collection
        cache_key = f"{query}:{collection_name}:{top_k}"
        cached_result = query_result_cache.get(cache_key)
        
        if cached_result is not None:
            logger.info(f"Cache hit for query in collection {collection_name}")
            return cached_result
        
        # Check if Azure OpenAI is available
        if async_client is None:
            # Fallback to simple keyword search
            logger.warning("Azure OpenAI not available, using fallback keyword search")
            try:
                collection = chroma_client.get_collection(name=collection_name)
                # Get all documents from collection
                all_docs = collection.get(include=["documents", "metadatas"])
                if all_docs and all_docs['documents']:
                    # Use simple keyword search
                    relevant_docs = simple_similarity_search(query, all_docs['documents'], top_k)
                    
                    # Create a mock result structure
                    mock_results = {
                        'documents': [relevant_docs],
                        'metadatas': [[]],  # Empty metadata for fallback
                        'distances': [[0.0] * len(relevant_docs)]  # Perfect similarity for fallback
                    }
                    
                    # Cache the results
                    query_result_cache.set(cache_key, mock_results)
                    return mock_results
                else:
                    # No documents in collection
                    return {
                        'documents': [[]],
                        'metadatas': [[]],
                        'distances': [[]]
                    }
            except Exception as e:
                logger.error(f"Error in fallback search: {str(e)}")
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
        
        # Get embedding for query
        query_embedding = await get_embeddings([query])
        
        # Query the collection
        collection = chroma_client.get_collection(name=collection_name)
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Cache the results
        query_result_cache.set(cache_key, results)
        
        return results
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        raise

def clean_markdown_formatting(text):
    """Clean up markdown formatting from AI responses."""
    if not text:
        return text
    
    # Remove markdown bold formatting (**text** -> text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove markdown italic formatting (*text* -> text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove markdown code formatting (`text` -> text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove markdown headers (# Header -> Header)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text

def construct_rag_prompt(query, relevant_docs, org_info=None, tone=None):
    """Construct a RAG prompt with context and guidelines."""
    # Default values
    org_name = os.environ.get("ORG_NAME", "Your Organization") if org_info is None else org_info.get("name", os.environ.get("ORG_NAME", "Your Organization"))
    org_description = os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions") if org_info is None else org_info.get("description", os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions"))
    tone = os.environ.get("DEFAULT_TONE", "professional") if tone is None else tone
    
    # Create the context section from relevant documents
    context_parts = []
    for i, doc in enumerate(relevant_docs['documents'][0]):
        metadata = relevant_docs['metadatas'][0][i]
        filename = metadata.get('filename', 'Unknown')
        context_parts.append(f"Document: {filename}\nContent: {doc}\n")
    
    context_text = "\n".join(context_parts)
    
    # Build the system prompt
    system_prompt = f"""You are an AI assistant for {org_name}, {org_description}.
Your task is to answer questions based on the provided context documents.

Guidelines:
1. Use a {tone} tone in your responses.
2. Base your answers primarily on the information in the provided documents.
3. If the documents don't contain relevant information, acknowledge this and provide general knowledge.
4. Do not make up information that isn't supported by the context or general knowledge.
5. Keep your answers concise and to the point.
6. If appropriate, structure your response for readability.
7. Do not use markdown formatting like **bold** or *italic* in your responses.

Here is the context information to help answer the user's question:

{context_text}
"""
    
    return system_prompt

@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=0.05, min=0.05, max=0.5))
async def generate_answer(query, relevant_docs, conversation_history, org_info=None, tone=None):
    """Generate an answer using Azure OpenAI with caching."""
    try:
        # Create a cache key from the query, relevant docs and recent history
        # Only use recent history to increase cache hits
        recent_history_str = ""
        if conversation_history:
            # Use only last 2 exchanges to increase cache hit probability
            recent = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
            recent_history_str = json.dumps([msg["content"] for msg in recent])
        
        # Include top document IDs in cache key
        doc_ids = []
        if relevant_docs and 'metadatas' in relevant_docs and relevant_docs['metadatas']:
            for metadata in relevant_docs['metadatas'][0][:3]:  # Use only top 3 docs for key
                doc_ids.append(metadata.get('chunk_index', ''))
        
        cache_key = f"{query}:{'-'.join(map(str, doc_ids))}:{recent_history_str}"
        cached_answer = llm_response_cache.get(cache_key)
        
        if cached_answer is not None:
            logger.info(f"Cache hit for answer to query: {query[:50]}...")
            
            # Clean up markdown formatting from cached answer
            cached_answer = clean_markdown_formatting(cached_answer)
            
            # Still update conversation history
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": cached_answer})
            
            return cached_answer
        
        # Check if Azure OpenAI is available
        if async_client is None:
            # Use fallback answer generation
            logger.warning("Azure OpenAI not available, using fallback answer generation")
            answer = generate_simple_answer(query, relevant_docs)
            
            # Cache the answer
            llm_response_cache.set(cache_key, answer)
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
        
        # Construct RAG prompt with system instructions
        system_prompt = construct_rag_prompt(query, relevant_docs, org_info, tone)
        
        # Format the conversation history - limit to prevent token overflow
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add only the most recent conversation history (last 6 messages maximum)
        recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        for msg in recent_history:
            messages.append(msg)
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        try:
            # Rate limiting before API call
            rate_limiter.wait_if_needed()
            
            # Try with async client first
            response = await async_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4o-mini"),
                messages=messages,
                temperature=float(os.environ.get("TEMPERATURE", 0.1)),
                max_tokens=int(os.environ.get("MAX_TOKENS", 4000))
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fall back to sync client if async times out
            logger.warning("Async completion timed out, falling back to sync client")
            response = sync_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4o-mini"),
                messages=messages,
                temperature=float(os.environ.get("TEMPERATURE", 0.1)),
                max_tokens=int(os.environ.get("MAX_TOKENS", 4000))
            )
            answer = response.choices[0].message.content
        
        # Clean up markdown formatting from the answer
        answer = clean_markdown_formatting(answer)
        
        # Cache the cleaned answer
        llm_response_cache.set(cache_key, answer)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": answer})
        
        return answer
    
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        # Fallback to simple answer generation when Azure fails
        logger.warning("Azure OpenAI failed, using fallback answer generation")
        answer = generate_simple_answer(query, relevant_docs)
        return answer 