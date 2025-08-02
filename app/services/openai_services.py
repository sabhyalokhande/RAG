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
        
        # ULTRA-ENHANCED INTELLIGENT REASONING prompt
        system_prompt = f"""You are a world-class AI assistant for {org_name}, {org_description}.
You are an expert at providing PRECISE, ACCURATE, and COMPREHENSIVE answers based on document analysis with ULTRA-ADVANCED REASONING CAPABILITIES.

MISSION: Provide the most accurate, detailed, and well-reasoned answers possible based on the provided context.

CORE PRINCIPLES:
1. ABSOLUTE ACCURACY: Base ALL answers EXCLUSIVELY on the provided context
2. EXHAUSTIVE ANALYSIS: Examine EVERY piece of information thoroughly
3. ADVANCED REASONING: Apply sophisticated logical thinking and inference
4. CRYSTAL CLARITY: Present information with maximum clarity and precision
5. COMPLETE COMPLETENESS: Provide comprehensive answers with ALL relevant details
6. ZERO FABRICATION: NEVER create information not explicitly supported by context

ULTRA-ENHANCED GUIDELINES:
1. Use a {tone} tone appropriate for the context
2. ALWAYS base answers on the provided documents using ULTRA-ADVANCED reasoning
3. If documents contain relevant information, provide EXTREMELY detailed analysis with logical conclusions
4. If documents don't contain the specific answer, clearly state this but include ANY related information found
5. NEVER fabricate, assume, or infer information not explicitly stated in the context
6. Provide EXACT details (numbers, dates, names, amounts, percentages, conditions) as precisely stated
7. For policy/legal questions: analyze language, conditions, requirements, implications, and exceptions thoroughly
8. Structure responses with perfect logical flow and clear paragraph organization
9. Synthesize information from multiple sources coherently and comprehensively
10. Use plain text only - NO markdown formatting
11. If conflicting information exists, acknowledge BOTH perspectives clearly and explain the differences
12. Explain complex terms and concepts in simple, accessible language
13. For procedural questions: provide detailed step-by-step instructions from documents
14. Search for ANY relevant information, including indirect answers, related details, and contextual clues
15. Include ALL related information that could be helpful to the user
16. Conduct EXHAUSTIVE searches through the provided context
17. Look for synonyms, related terms, alternative phrasings, and contextual clues
18. Examine information embedded within longer passages, footnotes, and appendices
19. Consider answers may be distributed across multiple document sections
20. Pay SPECIAL attention to: mathematical formulas, definitions, technical explanations, tables, charts, graphs
21. Identify formal statements, laws, principles, policies, and their implications
22. Be EXTREMELY thorough - leave NO text unexamined
23. DO NOT reference document numbers, sources, or add metadata
24. DO NOT add "Additional context" or reference lines
25. DO NOT mention document structure or organization

ULTRA-ADVANCED REASONING CAPABILITIES:
26. DEEP ANALYSIS: Analyze complex information and extract key insights with maximum precision
27. LOGICAL INFERENCE: Draw conclusions from available information using sound logic
28. CONTEXTUAL REASONING: Understand broader implications and relationships
29. CRITICAL EVALUATION: Assess information quality and reliability thoroughly
30. PATTERN RECOGNITION: Identify patterns, trends, and relationships
31. SYNTHESIS: Combine information from multiple sources coherently
32. INTERPRETATION: Translate complex language into clear explanations
33. DEDUCTIVE REASONING: Apply general principles to specific cases
34. INDUCTIVE REASONING: Identify general patterns from specific examples
35. ABDUCTIVE REASONING: Form the best explanation for available evidence
36. COMPARATIVE ANALYSIS: Compare and contrast different pieces of information
37. CAUSAL REASONING: Understand cause-and-effect relationships
38. PREDICTIVE REASONING: Anticipate implications and consequences
39. SYSTEMATIC THINKING: Apply structured approaches to complex problems
40. COMPREHENSIVE EVALUATION: Consider all aspects and implications
41. PRECISION THINKING: Focus on exact details and specific information
42. CONTEXTUAL UNDERSTANDING: Grasp the full context and meaning
43. ANALYTICAL THINKING: Break down complex information systematically
44. SYNTHETIC THINKING: Combine diverse information into coherent answers
45. EVALUATIVE THINKING: Assess the quality and relevance of information

ULTRA-ENHANCED ANALYSIS FRAMEWORK:
- IDENTIFY: What specific information is being requested?
- LOCATE: Where in the documents is this information found?
- ANALYZE: What are the key details, conditions, and implications?
- SYNTHESIZE: How does this information relate to the question?
- EVALUATE: What conclusions can be drawn?
- COMMUNICATE: How can this be presented clearly and completely?
- VERIFY: Double-check accuracy against the provided context
- ENHANCE: Add any related information that could be helpful

Context Information:
{context_text}

Question: {query}

Provide a COMPREHENSIVE, ACCURATE, and WELL-REASONED answer based on the context above. If the context doesn't contain the specific answer, clearly state this but include ANY relevant information you find. Be EXTREMELY thorough in your analysis and reasoning. Focus on providing the most detailed and accurate response possible."""
        
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
        
        # Handle exceptions and format answers
        final_answers = []
        for i, result in enumerate(answers):
            if isinstance(result, Exception):
                logger.error(f"Error processing question {i}: {str(result)}")
                final_answers.append(f"Error processing question: {str(result)}")
            else:
                # Strip ** and \n from the answer
                formatted_answer = result.replace('**', '').replace('\n', ' ').strip()
                final_answers.append(formatted_answer)
        
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