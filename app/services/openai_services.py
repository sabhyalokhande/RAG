"""
Optimized OpenAI Services for RAG System - SPEED OPTIMIZED (<60s)
- Parallel embedding generation
- Fast answer generation
- Optimized vector search
- Intelligent reasoning with speed focus
"""

import os
import json
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Azure OpenAI
import openai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Vector database
import chromadb
from chromadb.config import Settings

# Import configuration
from config import Config

# Import services
try:
    from app.services.pinecone_services import PineconeService
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    PineconeService = None

# Import utilities
from app.services.utils import (
    clean_text, chunk_text_advanced, is_high_quality_chunk,
    enhance_context_for_accuracy, prioritize_chunks_by_relevance,
    truncate_text_for_embeddings, process_chunks_parallel
)

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
async_client = None
sync_client = None
pinecone_service = None

# Thread pools for parallel processing
embedding_executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_EMBEDDINGS)
answer_executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_ANSWERS)

# Cache for LLM responses
llm_response_cache = {}

def get_pinecone_service():
    """Get Pinecone service instance with lazy initialization."""
    global pinecone_service
    if pinecone_service is None and PINECONE_AVAILABLE:
        try:
            pinecone_service = PineconeService()
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone service: {e}")
    return pinecone_service

def initialize_openai_clients():
    """Initialize Azure OpenAI clients with speed optimizations."""
    global async_client, sync_client
    
    try:
        # Debug: Print configuration values
        print("🔧 OPENAI CLIENT INITIALIZATION:")
        print(f"   AZURE_OPENAI_API_KEY: {'✅ Set' if Config.AZURE_OPENAI_API_KEY else '❌ Missing'}")
        print(f"   AZURE_OPENAI_ENDPOINT: {'✅ Set' if Config.AZURE_OPENAI_ENDPOINT else '❌ Missing'}")
        print(f"   AZURE_DEPLOYMENT_EMBEDDING: {Config.AZURE_DEPLOYMENT_EMBEDDING}")
        print(f"   AZURE_DEPLOYMENT_COMPLETION: {Config.AZURE_DEPLOYMENT_COMPLETION}")
        print("="*80)
        
        # Initialize async client
        async_client = AsyncAzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version="2023-06-01-preview",
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        
        # Initialize sync client
        sync_client = openai.AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version="2023-06-01-preview",
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        
        logger.info("Azure OpenAI clients initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI clients: {e}")
        raise

# Initialize clients
initialize_openai_clients()

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def get_embeddings_parallel(texts: List[str]) -> List[List[float]]:
    """Get embeddings with parallel processing for speed optimization."""
    if not texts:
        return []
    
    try:
        # Process texts in parallel batches
        batch_size = Config.BATCH_SIZE_EMBEDDINGS
        
        async def process_batch(batch):
            try:
                response = await async_client.embeddings.create(
                    model=Config.AZURE_DEPLOYMENT_EMBEDDING,
                    input=batch,
                    timeout=Config.EMBEDDING_TIMEOUT
                )
                return [embedding.embedding for embedding in response.data]
            except Exception as e:
                logger.error(f"Error processing embedding batch: {e}")
                return []
        
        # Split texts into batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        
        # Process batches in parallel
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_embeddings = []
        for result in results:
            if isinstance(result, list):
                all_embeddings.extend(result)
            else:
                logger.error(f"Error in batch processing: {result}")
        
        return all_embeddings
        
    except Exception as e:
        logger.error(f"Error in parallel embedding generation: {e}")
        # Fallback to sequential processing
        return await get_embeddings_sequential(texts)

async def get_embeddings_sequential(texts: List[str]) -> List[List[float]]:
    """Sequential embedding generation as fallback."""
    try:
        response = await async_client.embeddings.create(
            model=Config.AZURE_DEPLOYMENT_EMBEDDING,
            input=texts,
            timeout=Config.EMBEDDING_TIMEOUT
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        logger.error(f"Error in sequential embedding generation: {e}")
        return []

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def process_and_store_document_fast(file, collection_name: str, chroma_client=None) -> Dict[str, Any]:
    """Fast document processing with parallel operations."""
    start_time = time.time()
    
    try:
        # Extract text in parallel
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, lambda: file.read().decode('utf-8', errors='ignore'))
        
        if not text:
            return {"error": "No text extracted from document"}
        
        # Clean text
        text = clean_text(text)
        
        # Chunk text in parallel
        chunks = await loop.run_in_executor(None, chunk_text_advanced, text)
        
        # Process chunks in parallel
        processed_chunks = await loop.run_in_executor(None, process_chunks_parallel, chunks, "")
        
        if not processed_chunks:
            return {"error": "No valid chunks generated"}
        
        # Generate embeddings in parallel
        embeddings = await get_embeddings_parallel(processed_chunks)
        
        if not embeddings:
            return {"error": "Failed to generate embeddings"}
        
        # Store in vector database
        if chroma_client:
            collection = chroma_client.get_or_create_collection(collection_name)
            
            # Store in batches for speed
            batch_size = 100
            for i in range(0, len(processed_chunks), batch_size):
                batch_chunks = processed_chunks[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_ids = [f"chunk_{i + j}" for j in range(len(batch_chunks))]
                
                collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_chunks,
                    ids=batch_ids
                )
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "chunks_processed": len(processed_chunks),
            "processing_time": processing_time,
            "collection_name": collection_name
        }
        
    except Exception as e:
        logger.error(f"Error in fast document processing: {e}")
        return {"error": str(e)}

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def query_vector_db_fast(query: str, collection_name: str, top_k: int = None, chroma_client=None) -> Dict[str, Any]:
    """Fast vector database query with speed optimizations."""
    try:
        top_k = top_k or Config.SIMILARITY_TOP_K
        
        # Get query embedding
        query_embedding = await get_embeddings_parallel([query])
        if not query_embedding:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # Query vector database
        if chroma_client:
            collection = chroma_client.get_collection(collection_name)
            
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        
            return results
        else:
            # Fallback to empty results
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
    except Exception as e:
        logger.error(f"Error in fast vector database query: {e}")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

def construct_rag_prompt_fast(query: str, relevant_docs: Dict, org_info=None, tone=None) -> str:
    """Fast RAG prompt construction for speed optimization."""
    try:
        # Extract organization info
        org_name = org_info.get('name', 'Your Organization') if org_info else 'Your Organization'
        org_description = org_info.get('description', 'A leading provider of innovative solutions') if org_info else 'A leading provider of innovative solutions'
        
        # Set default tone
        if not tone:
            tone = "professional"
        
        # Fast context organization - NO DOCUMENT REFERENCES
        context_parts = []
        for doc in relevant_docs['documents'][0]:
            context_parts.append(f"{doc}")
        
        context_text = "\n".join(context_parts)
        
        # FAST INTELLIGENT REASONING prompt
        system_prompt = f"""You are an AI assistant for {org_name}, {org_description}.
Answer questions based on the provided context with INTELLIGENT REASONING.

CRITICAL GUIDELINES:
1. Use a {tone} tone.
2. Base answers on the provided documents using INTELLIGENT REASONING.
3. If documents contain relevant information, analyze it and provide reasoned conclusions.
4. If documents don't contain relevant information, clearly state this.
5. NEVER make up information not supported by the context.
6. Provide specific details (numbers, dates, names, amounts) EXACTLY as stated.
7. For policy questions, analyze the policy language and provide reasoned interpretations.
8. Structure responses clearly with proper paragraphs.
9. If multiple documents contain relevant information, synthesize coherently.
10. Do not use markdown formatting.
11. If there are conflicting details, mention this and provide both perspectives.
12. Explain technical terms in simple terms when possible.
13. For process questions, provide step-by-step details from the documents.
14. Look for ANY relevant information, even if not a direct answer.
15. If you find related information, include it in your response.
16. Be extremely thorough in your search through the provided context.
17. Search for synonyms, related terms, and alternative phrasings.
18. Look for information embedded within longer passages.
19. Consider that answers might be spread across multiple documents.
20. Pay attention to mathematical formulas, definitions, or technical explanations.
21. Look for formal statements of laws, principles, or theories.
22. Be extremely thorough - examine every piece of text.
23. DO NOT mention document numbers or sources in your response.
24. DO NOT add any "Additional context" or document reference lines.
25. DO NOT add any document references or "Additional context" lines to your response.

INTELLIGENT REASONING CAPABILITIES:
26. REASONING: Understand context and draw logical conclusions.
27. INFERENCE: If exact answer isn't stated, infer based on related information.
28. ANALYSIS: Analyze policy language, conditions, and requirements.
29. SYNTHESIS: Combine information from multiple parts of the document.
30. INTERPRETATION: Interpret technical language and explain clearly.
31. DEDUCTION: Use deductive reasoning to answer questions.
32. INDUCTION: Use inductive reasoning to identify patterns.
33. CONTEXTUAL UNDERSTANDING: Understand broader context and implications.
34. LOGICAL REASONING: Apply logical reasoning to answer questions.
35. CRITICAL THINKING: Evaluate information critically.
36. COMPREHENSIVE ANALYSIS: Provide comprehensive analysis.

Context Information:
{context_text}

Question: {query}

Please provide a comprehensive and accurate answer based on the context above. If the context doesn't contain the answer, clearly state this. However, if you find ANY relevant information, include it in your response. Be extremely thorough in your analysis."""
        
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error constructing fast RAG prompt: {e}")
        return f"Answer the following question based on the provided context:\n\nContext: {relevant_docs}\n\nQuestion: {query}\n\nAnswer:"

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def generate_answer_fast(query: str, relevant_docs: Dict, conversation_history=None, org_info=None, tone=None) -> str:
    """Fast answer generation with speed optimizations."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized.")
    
    try:
        # Fast cache key generation
        cache_key = f"{query}:{len(relevant_docs.get('documents', [[]])[0])}"
        cached_answer = llm_response_cache.get(cache_key)
        
        if cached_answer is not None:
            return cached_answer
        
        # Fast prompt construction
        system_prompt = construct_rag_prompt_fast(query, relevant_docs, org_info, tone)
        
        # Simple message structure for speed
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            # Fast completion with reduced parameters
            response = await async_client.chat.completions.create(
                model=Config.AZURE_DEPLOYMENT_COMPLETION,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fallback with sync client
            response = sync_client.chat.completions.create(
                model=Config.AZURE_DEPLOYMENT_COMPLETION,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        
        # Cache the answer
        llm_response_cache[cache_key] = answer
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in fast answer generation: {e}")
        return f"Error generating answer: {str(e)}" 

async def process_questions_parallel(questions: List[str], collection_name: str, chroma_client=None, org_info=None, tone=None) -> List[str]:
    """Process multiple questions in parallel for speed optimization."""
    try:
        # Process questions in parallel
        async def process_single_question(question):
            try:
                # Fast vector search
                relevant_docs = await query_vector_db_fast(question, collection_name, chroma_client=chroma_client)
                
                # Fast answer generation
                answer = await generate_answer_fast(question, relevant_docs, org_info=org_info, tone=tone)
                
                return answer
            except Exception as e:
                logger.error(f"Error processing question '{question}': {e}")
                return f"Error processing question: {str(e)}"
        
        # Create tasks for all questions
        tasks = [process_single_question(question) for question in questions]
        
        # Execute all tasks in parallel
        answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_answers = []
        for i, result in enumerate(answers):
            if isinstance(result, Exception):
                logger.error(f"Error processing question {i}: {str(result)}")
                final_answers.append(f"Error processing question: {str(result)}")
            else:
                final_answers.append(result)
        
        return final_answers
        
    except Exception as e:
        logger.error(f"Error in parallel question processing: {e}")
        return [f"Error: {str(e)}"] * len(questions)

def optimize_for_speed():
    """Apply speed optimizations to the system."""
    global embedding_executor, answer_executor
    
    # Optimize thread pools
    embedding_executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_EMBEDDINGS)
    answer_executor = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS_ANSWERS)
    
    # Clear caches for fresh start
    llm_response_cache.clear()
    
    logger.info("Speed optimizations applied to OpenAI services")

# Initialize optimizations
optimize_for_speed() 