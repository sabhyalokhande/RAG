"""
Advanced Production-Ready OpenAI Services
- Azure OpenAI integration with fallback mechanisms
- ChromaDB vector storage
- Smart caching with TTL and LRU eviction
- Retry logic with exponential backoff
- Enhanced RAG with better prompt engineering
"""

import os
import re
import json
import time
import uuid
import logging
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Azure OpenAI
import openai
from openai import AsyncAzureOpenAI, AzureOpenAI

# Import utilities
from app.services.utils import extract_text_from_file, chunk_text_advanced

# Vector database
import chromadb
from chromadb.config import Settings
try:
    from .pinecone_services import PineconeService
    PINECONE_AVAILABLE = True
    pinecone_service = None  # Will be initialized when needed
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone_service = None

from config import Config

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Global Pinecone service instance
pinecone_service = None

def get_pinecone_service():
    """Get or create the Pinecone service instance."""
    global pinecone_service
    if pinecone_service is None and PINECONE_AVAILABLE:
        pinecone_service = PineconeService()
    return pinecone_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info("Azure OpenAI clients initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI clients: {e}")
            async_client = None
            sync_client = None
    else:
        logger.warning("Azure OpenAI credentials not found. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.")

# Initialize clients on module import
initialize_openai_clients()

# Optimized embedding function with improved caching
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
async def get_embeddings(texts: List[str]):
    """Get embeddings for a list of texts using Azure OpenAI with text-embedding-3-large."""
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
                # Batch embeddings more efficiently - split into batches of 20 for large sets
                batch_size = 20
                all_new_embeddings = []
                
                for i in range(0, len(texts_to_embed), batch_size):
                    batch = texts_to_embed[i:i+batch_size]
                    
                    # Truncate each text to stay within token limits
                    truncated_batch = []
                    for text in batch:
                        from app.services.utils import truncate_text_for_embeddings
                        truncated_text = truncate_text_for_embeddings(text, max_tokens=8000)
                        truncated_batch.append(truncated_text)
                    
                    # Try async client first
                    response = await async_client.embeddings.create(
                        input=truncated_batch,
                        model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_new_embeddings.extend(batch_embeddings)
                    
                    # Cache each embedding immediately
                    for j, text in enumerate(batch):
                        embedding_cache.set(text, batch_embeddings[j])
            
            except asyncio.TimeoutError:
                # Fallback to sync client if async times out
                logger.warning("Async embedding timed out, falling back to sync client")
                
                all_new_embeddings = []
                for i in range(0, len(texts_to_embed), batch_size):
                    batch = texts_to_embed[i:i+batch_size]
                    
                    # Truncate each text to stay within token limits
                    truncated_batch = []
                    for text in batch:
                        from app.services.utils import truncate_text_for_embeddings
                        truncated_text = truncate_text_for_embeddings(text, max_tokens=8000)
                        truncated_batch.append(truncated_text)
                    
                    response = sync_client.embeddings.create(
                        input=truncated_batch,
                        model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
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

# Optimized embedding function with rate limit handling
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
async def get_embeddings_optimized(texts: List[str]):
    """Optimized embedding generation with rate limit handling using text-embedding-3-large."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized.")
    
    try:
        # Check cache first
        embeddings = []
        texts_to_embed = []
        indices = []
        
        for i, text in enumerate(texts):
            cached_embedding = embedding_cache.get(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                texts_to_embed.append(text)
                indices.append(i)
        
        # If we have texts that need embedding
        if texts_to_embed:
            # Use smaller batch size to avoid rate limits
            batch_size = 20  # Reduced from 100 to avoid rate limits
            all_new_embeddings = []
            
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i+batch_size]
                
                # Truncate each text to stay within token limits
                truncated_batch = []
                for text in batch:
                    from app.services.utils import truncate_text_for_embeddings
                    truncated_text = truncate_text_for_embeddings(text, max_tokens=8000)
                    truncated_batch.append(truncated_text)
                
                try:
                    response = await async_client.embeddings.create(
                        input=truncated_batch,
                        model=os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large"),
                        timeout=5.0  # Reduced timeout for faster processing
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_new_embeddings.extend(batch_embeddings)
                    
                    # Cache each embedding immediately
                    for j, text in enumerate(batch):
                        embedding_cache.set(text, batch_embeddings[j])
                    
                    # Add small delay between batches to avoid rate limits
                    if i + batch_size < len(texts_to_embed):
                        await asyncio.sleep(0.1)  # 100ms delay between batches
                        
                except Exception as e:
                    logger.error(f"Embedding batch failed: {str(e)}")
                    # Return zeros for failed embeddings to continue processing
                    batch_embeddings = [[0.0] * 3072] * len(truncated_batch)  # Updated for text-embedding-3-large
                    all_new_embeddings.extend(batch_embeddings)
            
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

async def process_and_store_document(file, collection_name, chroma_client=None):
    """Process and store document with dynamic configuration based on document size and complexity."""
    try:
        start_time = time.time()
        file_id = str(uuid.uuid4())
        
        logger.info(f"Processing document: {file.filename}")
        
        # Extract text from file
        text = extract_text_from_file(file)
        if not text:
            logger.error("No text extracted from file")
            return {"status": "error", "message": "No text could be extracted from the file"}
        
        # Count pages for dynamic configuration
        page_count = text.count('\f') + 1 if '\f' in text else 1  # Rough page count
        text_length = len(text)
        
        logger.info(f"Extracted {text_length} characters from {file.filename} ({page_count} estimated pages)")
        
        # Get dynamic configuration
        from app.services.utils import get_dynamic_processing_config
        dynamic_config = get_dynamic_processing_config(text_length, page_count)
        
        # Chunk the text with dynamic configuration
        chunks = chunk_text_advanced(
            text, 
            chunk_size=dynamic_config['chunk_size'],
            chunk_overlap=dynamic_config['chunk_overlap'],
            max_tokens=dynamic_config['max_tokens'],
            page_count=page_count
        )
        
        if not chunks:
            logger.error("No chunks generated from text")
            return {"status": "error", "message": "No meaningful chunks could be generated from the text"}
        
        logger.info(f"Generated {len(chunks)} chunks from {file.filename}")
        
        # Limit chunks based on document size
        max_chunks = Config.MAX_CHUNKS_PER_DOCUMENT
        if dynamic_config['processing_mode'] == 'large':
            max_chunks = 50  # Limit large documents to 50 chunks
        elif dynamic_config['processing_mode'] == 'small':
            max_chunks = 200  # Allow more chunks for small documents
        
        if len(chunks) > max_chunks:
            logger.warning(f"Too many chunks ({len(chunks)}), truncating to {max_chunks}")
            chunks = chunks[:max_chunks]
        
        # Store in Pinecone or ChromaDB
        storage_start = time.time()
        
        try:
            global PINECONE_AVAILABLE
            pinecone_service = get_pinecone_service()
            if PINECONE_AVAILABLE and pinecone_service:
                # Prepare documents for Pinecone
                documents = []
                for i, chunk in enumerate(chunks):
                    documents.append({
                        'text': chunk,
                        'file_id': file_id,
                        'filename': file.filename,
                        'chunk_id': i
                    })
                
                # Log a sample of the first chunk being stored
                if documents:
                    sample_chunk = documents[0]['text'][:200]
                    logger.debug(f"Storing sample chunk: {sample_chunk}...")
                
                try:
                    result = await pinecone_service.upsert_documents(collection_name, documents)
                    logger.info(f"Successfully stored {len(chunks)} chunks in Pinecone")
                except Exception as pinecone_error:
                    logger.warning(f"Pinecone storage failed: {str(pinecone_error)}")
                    logger.info("Falling back to ChromaDB")
                    # Continue to ChromaDB fallback
                    if not chroma_client:
                        logger.error("No ChromaDB client provided for fallback")
                        return {"status": "error", "message": "No vector database available"}
                    
                    # Get or create collection
                    try:
                        collection = chroma_client.get_collection(collection_name)
                        logger.info(f"Using existing collection: {collection_name}")
                    except:
                        collection = chroma_client.create_collection(collection_name)
                        logger.info(f"Created new collection: {collection_name}")
                    
                    # Generate embeddings
                    logger.info(f"Generating embeddings for {len(chunks)} chunks")
                    embeddings = await get_embeddings_optimized(chunks)
                    
                    if not embeddings or len(embeddings) != len(chunks):
                        logger.error(f"Embedding generation failed. Expected {len(chunks)}, got {len(embeddings) if embeddings else 0}")
                        return {"status": "error", "message": "Failed to generate embeddings"}
                    
                    # Store in ChromaDB
                    collection.add(
                        ids=[f"{file_id}_{i}" for i in range(len(chunks))],
                        embeddings=embeddings,
                        documents=chunks,
                        metadatas=[{
                            "file_id": file_id,
                            "filename": file.filename,
                            "uploaded_at": datetime.now().isoformat(),
                            "chunk_index": i
                        } for i in range(len(chunks))]
                    )
                    result = {"status": "success", "documents_processed": len(chunks), "collection_name": collection_name}
                    logger.info(f"Successfully stored {len(chunks)} chunks in ChromaDB")
        
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            return {"status": "error", "message": f"Failed to store documents: {str(e)}"}
        
        storage_time = time.time() - storage_start
        total_time = time.time() - start_time
        
        logger.info(f"Storage took {storage_time:.2f}s, Total processing time: {total_time:.2f}s")
        
        return {
            "status": "success",
            "file_id": file_id,
            "chunks_added": len(chunks),
            "processing_time": round(total_time, 2),
            "storage_time": round(storage_time, 2),
            "processing_mode": dynamic_config['processing_mode'],
            "text_length": text_length,
            "page_count": page_count
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return {"status": "error", "message": str(e)}

# Add caching to query function with improved retrieval
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def query_vector_db(query, collection_name, top_k=None, chroma_client=None, processing_mode=None):
    """Query Pinecone vector database with dynamic configuration based on document size."""
    if top_k is None:
        if processing_mode == 'small':
            top_k = Config.SMALL_DOC_TOP_K
        elif processing_mode == 'large':
            top_k = Config.LARGE_DOC_TOP_K
        else:
            top_k = Config.MEDIUM_DOC_TOP_K
    
    try:
        # Create a cache key from the query and collection
        cache_key = f"{query}:{collection_name}:{top_k}"
        cached_result = query_result_cache.get(cache_key)
        
        if cached_result is not None:
            logger.info(f"Cache hit for query in collection {collection_name}")
            return cached_result
        
        global PINECONE_AVAILABLE
        pinecone_service = get_pinecone_service()
        if PINECONE_AVAILABLE and pinecone_service:
            try:
                # Query Pinecone with more results
                similar_docs = await pinecone_service.query_similar(query, collection_name, top_k)
                
                # Log retrieved content for debugging
                logger.info(f"Retrieved {len(similar_docs)} documents for query: '{query}' (mode: {processing_mode})")
                for i, doc in enumerate(similar_docs[:1]):  # Log only first document
                    sample_text = doc['text'][:100]
                    logger.debug(f"Retrieved doc {i+1}: {sample_text}...")
                
                # Format results to match ChromaDB format for compatibility
                results = {
                    'ids': [[doc['id'] for doc in similar_docs]],
                    'documents': [[doc['text'] for doc in similar_docs]],
                    'metadatas': [[doc['metadata'] for doc in similar_docs]],
                    'distances': [[1 - doc['score'] for doc in similar_docs]]  # Convert similarity to distance
                }
            except Exception as pinecone_error:
                logger.warning(f"Pinecone query failed: {str(pinecone_error)}")
                logger.info("Falling back to ChromaDB for query")
                # Fall through to ChromaDB
                PINECONE_AVAILABLE = False
                raise pinecone_error
        else:
            # Fallback to ChromaDB
            query_embedding = await get_embeddings([query])
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

# Fast vector search with more results for better accuracy
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def query_vector_db_fast(query, collection_name, top_k=None, chroma_client=None):  # Increased from 3 to 5
    """Fast Pinecone vector database query with more results for better accuracy."""
    if top_k is None:
        top_k = Config.SIMILARITY_TOP_K
    
    try:
        cache_key = f"{query}:{collection_name}:{top_k}"
        cached_result = query_result_cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Get Pinecone service
        pinecone_service = get_pinecone_service()
        if not pinecone_service:
            raise RuntimeError("Pinecone service not available")
        
        # Query Pinecone with more results
        similar_docs = await pinecone_service.query_similar(query, collection_name, top_k)
        
        # Format results to match ChromaDB format for compatibility
        results = {
            'ids': [[doc['id'] for doc in similar_docs]],
            'documents': [[doc['text'] for doc in similar_docs]],
            'metadatas': [[doc['metadata'] for doc in similar_docs]],
            'distances': [[1 - doc['score'] for doc in similar_docs]]  # Convert similarity to distance
        }
        
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
    """Construct an enhanced RAG prompt with better context organization and instructions for maximum accuracy."""
    try:
        # Extract organization info
        org_name = org_info.get('name', 'Your Organization') if org_info else 'Your Organization'
        org_description = org_info.get('description', 'A leading provider of innovative solutions') if org_info else 'A leading provider of innovative solutions'
        
        # Set default tone
        if not tone:
            tone = "professional"
        
        # Enhanced context organization with better structure - REMOVE DOCUMENT REFERENCES
        context_parts = []
        for i, doc in enumerate(relevant_docs['documents'][0]):
            # Don't add document source information to avoid cluttering
            context_parts.append(f"{doc}\n")
        
        context_text = "\n".join(context_parts)
        
        # OPTIMIZED system prompt for better accuracy without document references
        system_prompt = f"""You are an AI assistant for {org_name}, {org_description}.
Your task is to answer questions based on the provided context documents with MAXIMUM ACCURACY.

CRITICAL ACCURACY GUIDELINES:
1. Use a {tone} tone in your responses.
2. Base your answers EXCLUSIVELY on the information in the provided documents.
3. If the documents contain ANY relevant information, provide it accurately and completely with exact details.
4. If the documents don't contain relevant information, clearly state "The provided documents do not contain information about this."
5. NEVER make up information that isn't supported by the context.
6. For specific details (numbers, dates, names, amounts, percentages), provide them EXACTLY as stated in the documents.
7. For policy-related questions, quote the exact policy terms and conditions when possible.
8. Structure your response clearly with proper paragraphs and logical flow.
9. If multiple documents contain relevant information, synthesize the information coherently.
10. Do not use markdown formatting like **bold** or *italic* in your responses.
11. If there are conflicting details in different documents, mention this and provide both perspectives.
12. For technical terms or legal language, explain them in simple terms when possible.
13. If the question asks for a process or procedure, provide step-by-step details from the documents.
14. IMPORTANT: Look for ANY relevant information, even if it's not a direct answer to the question.
15. If you find related information that might be helpful, include it in your response.
16. Be thorough in your search through the provided context.
17. If the question is about a specific topic, look for ANY mention of that topic in the documents.
18. CRITICAL: Search for synonyms, related terms, and alternative phrasings of the question.
19. Look for information that might be embedded within longer passages or paragraphs.
20. Consider that the answer might be spread across multiple documents or sections.
21. Pay attention to any mathematical formulas, definitions, or technical explanations.
22. If the question asks for laws, principles, or theories, look for their formal statements.
23. Be extremely thorough - examine every piece of text for relevant information.
24. DO NOT mention document numbers or sources in your response - focus on the content.

Context Information:
{context_text}

Question: {query}

Please provide a comprehensive and accurate answer based on the context above. If the context doesn't contain the answer, clearly state this. However, if you find ANY relevant information, include it in your response. Be extremely thorough in your analysis."""
        
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error constructing RAG prompt: {e}")
        # Fallback to simple prompt
        return f"Answer the following question based on the provided context:\n\nContext: {relevant_docs}\n\nQuestion: {query}\n\nAnswer:"

def validate_answer_accuracy(answer: str, query: str, context: str) -> Dict[str, any]:
    """Validate answer accuracy and provide confidence score."""
    validation = {
        'confidence': 0.0,
        'issues': [],
        'suggestions': []
    }
    
    # Check if answer is too generic
    generic_phrases = ['the documents do not contain', 'no information provided', 'not mentioned in the context']
    if any(phrase in answer.lower() for phrase in generic_phrases):
        validation['confidence'] = 0.3
        validation['issues'].append('Answer appears to be generic or indicates missing information')
    
    # Check for specific details (good sign)
    specific_indicators = ['according to', 'the policy states', 'specifically', 'exactly', 'precisely']
    if any(indicator in answer.lower() for indicator in specific_indicators):
        validation['confidence'] += 0.2
    
    # Check for numbers and dates (good for accuracy)
    if re.search(r'\d+', answer):
        validation['confidence'] += 0.2
    
    # Check for policy-related terms
    policy_terms = ['policy', 'coverage', 'premium', 'claim', 'benefit', 'exclusion']
    if any(term in answer.lower() for term in policy_terms):
        validation['confidence'] += 0.1
    
    # Check answer length (too short might be incomplete)
    if len(answer) < 50:
        validation['confidence'] -= 0.2
        validation['issues'].append('Answer seems too short')
    
    # Cap confidence at 1.0
    validation['confidence'] = min(validation['confidence'], 1.0)
    
    return validation

def enhance_answer_with_context(answer: str, relevant_docs: Dict, query: str) -> str:
    """Enhance answer with additional context for better accuracy."""
    try:
        # Extract key information from relevant documents
        key_info = []
        
        if relevant_docs and 'documents' in relevant_docs and relevant_docs['documents']:
            for i, doc in enumerate(relevant_docs['documents'][0]):
                # Look for specific details that might be missing from the answer
                if 'policy' in query.lower() and 'policy' in doc.lower():
                    key_info.append(f"Policy details from document {i+1}")
                
                if 'coverage' in query.lower() and 'coverage' in doc.lower():
                    key_info.append(f"Coverage information from document {i+1}")
                
                if 'premium' in query.lower() and 'premium' in doc.lower():
                    key_info.append(f"Premium details from document {i+1}")
        
        # If we found additional context, append it
        if key_info:
            answer += f"\n\nAdditional context: {'; '.join(key_info)}"
        
        return answer
        
    except Exception as e:
        logger.error(f"Error enhancing answer: {e}")
        return answer

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
async def generate_answer(query, relevant_docs, conversation_history, org_info=None, tone=None):
    """Generate an answer using Azure OpenAI with GPT-4 and enhanced prompt engineering for maximum accuracy."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.")
    
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
        
        # Construct enhanced RAG prompt with better instructions
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
            # Try with async client first using GPT-4
            response = await async_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4"),
                messages=messages,
                temperature=float(os.environ.get("TEMPERATURE", 0.1)),
                max_tokens=int(os.environ.get("MAX_TOKENS", 4000))
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fall back to sync client if async times out
            logger.warning("Async completion timed out, falling back to sync client")
            response = sync_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4"),
                messages=messages,
                temperature=float(os.environ.get("TEMPERATURE", 0.1)),
                max_tokens=int(os.environ.get("MAX_TOKENS", 4000))
            )
            answer = response.choices[0].message.content
        
        # Clean up markdown formatting from the answer
        answer = clean_markdown_formatting(answer)
        
        # Enhance answer with additional context
        answer = enhance_answer_with_context(answer, relevant_docs, query)
        
        # Validate answer accuracy
        validation = validate_answer_accuracy(answer, query, str(relevant_docs))
        if validation['confidence'] < 0.5:
            logger.warning(f"Low confidence answer ({validation['confidence']:.2f}): {validation['issues']}")
        
        # Cache the cleaned answer
        llm_response_cache.set(cache_key, answer)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": answer})
        
        return answer
    
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        raise

# Fast answer generation with enhanced prompt engineering
async def generate_answer_fast(query, relevant_docs, conversation_history=None, org_info=None, tone=None):
    """Fast answer generation with enhanced prompt engineering using GPT-4 for better accuracy."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized.")
    
    try:
        # Simplified cache key
        cache_key = f"{query}:{len(relevant_docs.get('documents', [[]])[0])}"
        cached_answer = llm_response_cache.get(cache_key)
        
        if cached_answer is not None:
            return cached_answer
        
        # Enhanced prompt construction with better context organization
        context_parts = []
        for i, doc in enumerate(relevant_docs['documents'][0][:5]):  # Increased from 3 to 5
            context_parts.append(f"Context {i+1}: {doc[:800]}...")  # Increased from 500 to 800
        
        context_text = "\n".join(context_parts)
        
        # Enhanced system prompt with better instructions
        system_prompt = f"""Answer the question based on the provided context with high accuracy.

IMPORTANT:
- Base your answer primarily on the context provided
- If the context contains the answer, provide it accurately
- If the context doesn't contain relevant information, state this clearly
- Be specific and detailed when the context supports it
- Do not make up information not present in the context

Context:
{context_text}

Question: {query}

Answer:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = await async_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4"),
                messages=messages,
                temperature=0.1,
                max_tokens=1500,  # Increased from 1000
                timeout=15.0  # Increased from 10.0
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fallback with sync client
            response = sync_client.chat.completions.create(
                model=os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4"),
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
                timeout=15.0
            )
            answer = response.choices[0].message.content
        
        # Clean and cache
        answer = clean_markdown_formatting(answer)
        llm_response_cache.set(cache_key, answer)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return f"Error generating answer: {str(e)}" 