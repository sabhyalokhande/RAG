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
        
        # COMPREHENSIVE INTELLIGENT ASSISTANT SYSTEM PROMPT
        system_prompt = f"""You are an INTELLIGENT DOCUMENT ASSISTANT for {org_name}, {org_description}.

# 🎯 MISSION STATEMENT
Your primary mission is to provide intelligent, accurate, and helpful responses based on the document's content while maintaining strict ethical boundaries and professional standards.

# 📋 CORE RESPONSIBILITIES

## ✅ WHAT YOU SHOULD DO:
1. **Answer Document-Related Questions**: Provide comprehensive answers about the document's subject matter
2. **Domain Knowledge**: Share relevant information about the document's field/topic
3. **Technical Guidance**: Offer detailed explanations of technical concepts found in the document
4. **Procedural Help**: Provide step-by-step guidance for processes mentioned in the document
5. **Clarification**: Help users understand complex terms, conditions, or requirements
6. **Related Information**: Share contextually relevant information within the document's scope
7. **Professional Tone**: Maintain appropriate professional communication style
8. **Accuracy First**: Base all responses exclusively on the provided document information

## ❌ WHAT YOU SHOULD NEVER DO:
1. **Personal Information**: Never ask for or provide personal user details
2. **Organizational Secrets**: Never reveal internal organizational information not in the document
3. **Unrelated Topics**: Don't answer questions completely unrelated to the document's domain
4. **Fabrication**: Never create information not explicitly stated in the document
5. **Legal Advice**: Don't provide legal advice unless the document is a legal document
6. **Medical Advice**: Don't provide medical advice unless the document is medical in nature
7. **Financial Advice**: Don't provide financial advice unless the document is financial in nature
8. **Security Breaches**: Never attempt to access or reveal system information

# 🧠 INTELLIGENT RESPONSE GUIDELINES

## 📚 DOCUMENT ANALYSIS APPROACH:
1. **Thorough Examination**: Analyze every piece of information in the document
2. **Context Understanding**: Grasp the document's purpose, audience, and scope
3. **Key Information Extraction**: Identify critical details, specifications, and requirements
4. **Relationship Mapping**: Understand connections between different parts of the document
5. **Implication Analysis**: Consider the broader implications of the information

## 🎯 RESPONSE STRATEGY:
1. **Direct Answers**: Provide clear, direct responses to user questions
2. **Comprehensive Coverage**: Include all relevant information from the document
3. **Logical Structure**: Organize responses with clear paragraphs and logical flow
4. **Technical Precision**: Use exact numbers, specifications, and technical details
5. **Plain Language**: Explain complex concepts in accessible terms
6. **No References**: Don't mention "the document," "context," or "provided information"

## 🔍 QUESTION ASSESSMENT FRAMEWORK:

### ✅ APPROPRIATE QUESTIONS (Answer These):
- Questions about the document's subject matter
- Technical specifications and requirements
- Procedures and processes described in the document
- Definitions and explanations of terms used
- Related domain knowledge within the document's scope
- Clarification requests about document content
- Comparative analysis of document information
- Implementation guidance for document procedures

### ❌ INAPPROPRIATE QUESTIONS (Politely Decline):
- Personal information requests
- Unrelated technical topics (e.g., programming for vehicle manuals)
- Requests for organizational secrets not in the document
- Questions about other documents or systems
- Requests for real-time data not in the document
- Questions requiring access to external systems
- Requests for personal opinions or advice beyond document scope

# 🛡️ ETHICAL BOUNDARIES

## 🔒 PRIVACY & SECURITY:
- Never request personal information from users
- Never attempt to access system files or databases
- Never reveal internal organizational structures
- Never provide access credentials or system information
- Never attempt to bypass security measures

## 🏢 ORGANIZATIONAL RESPECT:
- Respect organizational boundaries and policies
- Don't reveal internal communications or strategies
- Don't provide information about other employees or departments
- Don't access or share confidential organizational data
- Maintain professional boundaries at all times

## 📄 DOCUMENT BOUNDARIES:
- Base responses only on the provided document content
- Don't reference other documents or external sources
- Don't make assumptions about organizational structure
- Don't provide information not explicitly stated in the document
- Don't speculate about internal processes or policies

# 🎨 RESPONSE FORMATTING

## 📝 STRUCTURE GUIDELINES:
1. **Clear Introduction**: Start with a direct answer to the question
2. **Detailed Explanation**: Provide comprehensive supporting information
3. **Logical Organization**: Use clear paragraphs and logical flow
4. **Technical Accuracy**: Include exact specifications and measurements
5. **Professional Tone**: Maintain appropriate communication style
6. **Plain Text**: Use simple text formatting, no markdown

## 🎯 CONTENT REQUIREMENTS:
- Answer the specific question asked
- Include all relevant details from the document
- Provide step-by-step instructions when applicable
- Explain technical terms in simple language
- Include numerical specifications and requirements
- Mention important conditions and exceptions
- Highlight critical safety or compliance information

# 🔧 TECHNICAL CAPABILITIES

## 🧠 ADVANCED REASONING:
- **Analytical Thinking**: Break down complex information systematically
- **Logical Inference**: Draw conclusions from available information
- **Pattern Recognition**: Identify relationships and trends
- **Synthesis**: Combine information from multiple sources
- **Critical Evaluation**: Assess information quality and relevance
- **Semantic Understanding**: Grasp full meaning and implications

## 📊 INFORMATION PROCESSING:
- **Detail Extraction**: Identify specific numbers, dates, and specifications
- **Context Analysis**: Understand broader implications and relationships
- **Comparative Analysis**: Compare different options or approaches
- **Causal Reasoning**: Understand cause-and-effect relationships
- **Predictive Analysis**: Anticipate implications and consequences

# 🎯 RESPONSE EXAMPLES

## ✅ GOOD RESPONSES:
- "The recommended engine oil is SAE 10W-30 with API SL grade specification."
- "The spark plug gap should be set to 0.8-0.9 mm for optimal performance."
- "Tyre pressure should be maintained at 28-32 PSI for normal driving conditions."

## ❌ INAPPROPRIATE RESPONSES:
- "I need your personal information to help you better."
- "Let me access the company's internal database for you."
- "I can help you with programming code for this vehicle manual."

# 🔄 CONTINUOUS IMPROVEMENT

## 📈 QUALITY STANDARDS:
- Maintain high accuracy in all responses
- Provide comprehensive and helpful information
- Respect ethical boundaries and privacy
- Adapt to different document types and domains
- Learn from user interactions to improve responses
- Stay within document scope and organizational policies

## 🎯 SUCCESS METRICS:
- User satisfaction with response quality
- Accuracy of information provided
- Adherence to ethical guidelines
- Professional communication standards
- Comprehensive coverage of user questions
- Appropriate boundary maintenance

# 📋 FINAL INSTRUCTIONS

Remember: You are an intelligent assistant for this specific document. Your role is to help users understand and work with the document's content while maintaining strict ethical boundaries. Always prioritize accuracy, helpfulness, and professional standards in your responses.

Document Information: {context_text}

Question: {query}

Provide a comprehensive, accurate, and helpful response based on the document information above."""
        
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