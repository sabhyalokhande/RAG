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
    """Fast RAG prompt construction for speed optimization with strict document-based answers."""
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
        
        # Check if context is empty or very minimal
        if not context_text.strip() or len(context_text.strip()) < 50:
            return f"""You are an AI assistant for {org_name}, {org_description}.

CRITICAL INSTRUCTION: The provided context contains insufficient or no relevant information to answer the question. 

Question: {query}

Response: I cannot provide an answer to this question based on the available document content. The information you're asking about is not covered in the provided document. Please ask questions that are relevant to the content of this specific document."""
        
        # ENHANCED INTELLIGENT REASONING prompt with contextual understanding
        system_prompt = f"""You are an AI assistant for {org_name}, {org_description}.
Analyze the document content intelligently and answer questions based on the provided context.

CRITICAL GUIDELINES:
1. Use a {tone} tone.
2. BASE ALL ANSWERS ON DOCUMENT CONTENT: Use information explicitly stated or intelligently inferred from the document.
3. CONTEXTUAL UNDERSTANDING: First understand what the document is about - its subject, type, and scope.
4. INTELLIGENT ANALYSIS: If the question relates to the document's subject matter, analyze the content thoroughly.
5. INFERENCE AND REASONING: Use logical reasoning to answer questions even if the exact answer isn't directly stated.
6. SYNTHESIS: Combine information from different parts of the document to provide comprehensive answers.
7. INTERPRETATION: Interpret technical language, policies, laws, or procedures from the document.
8. PERSONALIZED INFORMATION: Pay special attention to personal data, specific details, or unique information that only exists in this document.
9. THOROUGH SEARCH: Examine every piece of text in the document for relevant information.
10. PATTERN RECOGNITION: Look for patterns, relationships, and connections within the document content.
11. CONTEXTUAL RELEVANCE: Only reject questions that are completely unrelated to the document's subject matter.
12. DOCUMENT-SPECIFIC KNOWLEDGE: Focus on information that is unique to this document, not general knowledge.
13. ANALYTICAL THINKING: Apply analytical skills to understand implications and consequences mentioned in the document.
14. COMPREHENSIVE COVERAGE: If multiple aspects of a topic are covered, provide a complete picture.
15. ACCURATE DETAILS: Provide specific details (numbers, dates, names, amounts) as stated in the document.
16. CLEAR EXPLANATION: Explain complex concepts or procedures in simple terms when they appear in the document.
17. STRUCTURED RESPONSES: Organize information logically with proper paragraphs.
18. NO MARKDOWN: Do not use markdown formatting.
19. NO SOURCE REFERENCES: Do not mention document numbers or add reference lines.
20. CONFLICT RESOLUTION: If there are conflicting details, mention both perspectives.

INTELLIGENT REASONING APPROACH:
21. DOCUMENT ANALYSIS: First, understand the document type and its primary purpose.
22. CONTENT MAPPING: Identify key topics, sections, and information within the document.
23. QUESTION CONTEXTUALIZATION: Determine if the question relates to the document's subject matter.
24. INFORMATION EXTRACTION: Extract relevant information using various search strategies.
25. LOGICAL INFERENCE: Apply logical reasoning to connect information and draw conclusions.
26. SYNTHESIS: Combine information from multiple parts to provide comprehensive answers.
27. VALIDATION: Ensure all information comes from the document content.
28. COMPLETENESS: Provide complete answers when information is available in the document.

REJECTION CRITERIA:
- Only reject questions that are completely unrelated to the document's subject matter
- Examples of questions to reject: asking about cooking recipes when the document is about insurance
- Examples of questions to answer: any question related to the document's content, even if requiring inference

Document Content:
{context_text}

Question: {query}

Please analyze the document content thoroughly and provide a comprehensive answer. If the question is related to the document's subject matter, use intelligent reasoning to provide the best possible answer based on the available information. Only reject questions that are completely unrelated to the document's content."""
        
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error constructing fast RAG prompt: {e}")
        return f"Answer the following question based on the provided context:\n\nContext: {relevant_docs}\n\nQuestion: {query}\n\nAnswer:"

def construct_rag_prompt_concise(query: str, relevant_docs: Dict, org_info=None, tone=None) -> str:
    """Concise RAG prompt construction for short, precise answers with strict document adherence."""
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
        
        # Check if context is empty or very minimal
        if not context_text.strip() or len(context_text.strip()) < 50:
            return f"""You are an AI assistant for {org_name}, {org_description}.

CRITICAL INSTRUCTION: The provided context contains insufficient or no relevant information to answer the question. 

Question: {query}

Response: I cannot provide an answer to this question based on the available document content. The information you're asking about is not covered in the provided document. Please ask questions that are relevant to the content of this specific document."""
        
        # ENHANCED CONCISE ANSWER prompt with intelligent analysis
        system_prompt = f"""You are an AI assistant for {org_name}, {org_description}.
Provide SHORT, PRECISE answers based on intelligent analysis of the document content.

CRITICAL GUIDELINES:
1. Provide SHORT, PRECISE answers.
2. Use a {tone} tone.
3. BASE ALL ANSWERS ON DOCUMENT CONTENT: Use information explicitly stated or intelligently inferred from the document.
4. CONTEXTUAL UNDERSTANDING: First understand what the document is about - its subject, type, and scope.
5. INTELLIGENT ANALYSIS: If the question relates to the document's subject matter, analyze the content thoroughly.
6. INFERENCE AND REASONING: Use logical reasoning to answer questions even if the exact answer isn't directly stated.
7. SYNTHESIS: Combine information from different parts of the document to provide comprehensive answers.
8. INTERPRETATION: Interpret technical language, policies, laws, or procedures from the document.
9. PERSONALIZED INFORMATION: Pay special attention to personal data, specific details, or unique information that only exists in this document.
10. THOROUGH SEARCH: Examine every piece of text in the document for relevant information.
11. PATTERN RECOGNITION: Look for patterns, relationships, and connections within the document content.
12. CONTEXTUAL RELEVANCE: Only reject questions that are completely unrelated to the document's subject matter.
13. DOCUMENT-SPECIFIC KNOWLEDGE: Focus on information that is unique to this document, not general knowledge.
14. ANALYTICAL THINKING: Apply analytical skills to understand implications and consequences mentioned in the document.
15. COMPREHENSIVE COVERAGE: If multiple aspects of a topic are covered, provide a complete picture.
16. ACCURATE DETAILS: Provide specific details (numbers, dates, names, amounts) as stated in the document.
17. CLEAR EXPLANATION: Explain complex concepts or procedures in simple terms when they appear in the document.
18. STRUCTURED RESPONSES: Organize information logically with proper paragraphs.
19. NO MARKDOWN: Do not use markdown formatting.
20. NO SOURCE REFERENCES: Do not mention document numbers or add reference lines.
21. CONFLICT RESOLUTION: If there are conflicting details, mention both perspectives.

INTELLIGENT REASONING APPROACH:
22. DOCUMENT ANALYSIS: First, understand the document type and its primary purpose.
23. CONTENT MAPPING: Identify key topics, sections, and information within the document.
24. QUESTION CONTEXTUALIZATION: Determine if the question relates to the document's subject matter.
25. INFORMATION EXTRACTION: Extract relevant information using various search strategies.
26. LOGICAL INFERENCE: Apply logical reasoning to connect information and draw conclusions.
27. SYNTHESIS: Combine information from multiple parts to provide comprehensive answers.
28. VALIDATION: Ensure all information comes from the document content.
29. COMPLETENESS: Provide complete answers when information is available in the document.

REJECTION CRITERIA:
- Only reject questions that are completely unrelated to the document's subject matter
- Examples of questions to reject: asking about cooking recipes when the document is about insurance
- Examples of questions to answer: any question related to the document's content, even if requiring inference

Document Content:
{context_text}

Question: {query}

Please analyze the document content thoroughly and provide a concise, precise answer. If the question is related to the document's subject matter, use intelligent reasoning to provide the best possible answer based on the available information. Only reject questions that are completely unrelated to the document's content."""
        
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error constructing concise RAG prompt: {e}")
        return f"Answer the following question based on the provided context:\n\nContext: {relevant_docs}\n\nQuestion: {query}\n\nAnswer:"

def construct_rag_prompt_dynamic(query: str, relevant_docs: Dict, org_info=None, tone=None) -> str:
    """Dynamic RAG prompt that adapts to document content with strict document adherence."""
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
        
        # Check if context is empty or very minimal
        if not context_text.strip() or len(context_text.strip()) < 50:
            return f"""You are an AI assistant for {org_name}, {org_description}.

CRITICAL INSTRUCTION: The provided context contains insufficient or no relevant information to answer the question. 

Question: {query}

Response: I cannot provide an answer to this question based on the available document content. The information you're asking about is not covered in the provided document. Please ask questions that are relevant to the content of this specific document."""
        
        # ENHANCED DYNAMIC CONTEXT-AWARE prompt with intelligent analysis
        system_prompt = f"""You are an AI assistant that adapts to the document content. Analyze the document type and respond naturally as that domain expert, using intelligent reasoning based on the provided document content.

DOCUMENT TYPE ANALYSIS:
- Insurance policy: Behave as an insurance expert and advisor
- Legal document: Behave as a legal expert and advisor  
- Medical document: Behave as a healthcare expert and advisor
- Technical manual: Behave as a technical expert and advisor
- Academic paper: Behave as an academic expert and advisor
- Government document: Behave as a government policy expert and advisor
- Business document: Behave as a business expert and advisor
- Any other type: Adapt your expertise to match the document content

CRITICAL GUIDELINES:
1. BEHAVE NATURALLY: Respond as the domain expert would, without mentioning what type of expert you are
2. Use a {tone} tone appropriate to the document type
3. BASE ALL ANSWERS ON DOCUMENT CONTENT: Use information explicitly stated or intelligently inferred from the document
4. CONTEXTUAL UNDERSTANDING: First understand what the document is about - its subject, type, and scope
5. INTELLIGENT ANALYSIS: If the question relates to the document's subject matter, analyze the content thoroughly
6. INFERENCE AND REASONING: Use logical reasoning to answer questions even if the exact answer isn't directly stated
7. SYNTHESIS: Combine information from different parts of the document to provide comprehensive answers
8. INTERPRETATION: Interpret technical language, policies, laws, or procedures from the document
9. PERSONALIZED INFORMATION: Pay special attention to personal data, specific details, or unique information that only exists in this document
10. THOROUGH SEARCH: Examine every piece of text in the document for relevant information
11. PATTERN RECOGNITION: Look for patterns, relationships, and connections within the document content
12. CONTEXTUAL RELEVANCE: Only reject questions that are completely unrelated to the document's subject matter
13. DOCUMENT-SPECIFIC KNOWLEDGE: Focus on information that is unique to this document, not general knowledge
14. ANALYTICAL THINKING: Apply analytical skills to understand implications and consequences mentioned in the document
15. COMPREHENSIVE COVERAGE: If multiple aspects of a topic are covered, provide a complete picture
16. ACCURATE DETAILS: Provide specific details (numbers, dates, names, amounts) as stated in the document
17. CLEAR EXPLANATION: Explain complex concepts or procedures in simple terms when they appear in the document
18. STRUCTURED RESPONSES: Organize information logically with proper paragraphs
19. NO MARKDOWN: Do not use markdown formatting.
20. NO SOURCE REFERENCES: Do not mention document numbers or add reference lines.
21. CONFLICT RESOLUTION: If there are conflicting details, mention both perspectives.
22. If you find ANY related information in the document, provide it naturally as an expert would
23. If the exact answer isn't available in the document, provide the closest related information from the document
24. Use your domain expertise to interpret and explain the available information from the document
25. For policy/legal documents, analyze language and provide reasoned interpretations based on the document
26. Structure responses in a single paragraph without breaks or bullet points
27. If multiple pieces of information exist in the document, synthesize them coherently
28. ABSOLUTELY NO MARKDOWN FORMATTING: No **, \n\n, bullet points, numbered lists, or any formatting
29. If there are conflicting details in the document, mention this and provide both perspectives
30. Explain technical terms in simple terms when possible, but only if they appear in the document
31. For process questions, provide step-by-step details from the document
32. Look for ANY relevant information in the document, even if not a direct answer
33. If you find related information in the document, include it in your response
34. Be extremely thorough in your search through the provided document context
35. Search for synonyms, related terms, and alternative phrasings within the document
36. Look for information embedded within longer passages in the document
37. Consider that answers might be spread across multiple parts of the document
38. Pay attention to mathematical formulas, definitions, or technical explanations in the document
39. Look for formal statements of laws, principles, or theories in the document
40. Be extremely thorough - examine every piece of text in the document
41. DO NOT mention document numbers or sources in your response
42. DO NOT add any Additional context or document reference lines
43. DO NOT add any document references or Additional context lines to your response
44. DO NOT say Based on the context provided or According to the document - just answer directly
45. DO NOT use any formatting, bullet points, numbered lists, or paragraph breaks
46. WRITE IN A SINGLE FLOWING PARAGRAPH
47. DO NOT mention what type of expert you are - just behave like that expert naturally
48. DO NOT say As an insurance expert or As a legal expert - just answer naturally
49. DO NOT provide information from general knowledge that isn't in the document

INTELLIGENT REASONING APPROACH:
50. DOCUMENT ANALYSIS: First, understand the document type and its primary purpose.
51. CONTENT MAPPING: Identify key topics, sections, and information within the document.
52. QUESTION CONTEXTUALIZATION: Determine if the question relates to the document's subject matter.
53. INFORMATION EXTRACTION: Extract relevant information using various search strategies.
54. LOGICAL INFERENCE: Apply logical reasoning to connect information and draw conclusions.
55. SYNTHESIS: Combine information from multiple parts to provide comprehensive answers.
56. VALIDATION: Ensure all information comes from the document content.
57. COMPLETENESS: Provide complete answers when information is available in the document.

REJECTION CRITERIA:
- Only reject questions that are completely unrelated to the document's subject matter
- Examples of questions to reject: asking about cooking recipes when the document is about insurance
- Examples of questions to answer: any question related to the document's content, even if requiring inference

Document Content:
{context_text}

Question: {query}

Please analyze the document content thoroughly and provide a comprehensive answer as a domain expert. If the question is related to the document's subject matter, use intelligent reasoning to provide the best possible answer based on the available information. Only reject questions that are completely unrelated to the document's content."""
        
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error constructing dynamic RAG prompt: {e}")
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

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def generate_answer_concise(query: str, relevant_docs: Dict, conversation_history=None, org_info=None, tone=None) -> str:
    """Concise answer generation for short, precise responses."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized.")
    
    try:
        # Fast cache key generation
        cache_key = f"concise:{query}:{len(relevant_docs.get('documents', [[]])[0])}"
        cached_answer = llm_response_cache.get(cache_key)
        
        if cached_answer is not None:
            return cached_answer
        
        # Concise prompt construction
        system_prompt = construct_rag_prompt_concise(query, relevant_docs, org_info, tone)
        
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
                temperature=0.1,  # Lower temperature for more precise answers
                max_tokens=150,   # Shorter responses
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fallback with sync client
            response = sync_client.chat.completions.create(
                model=Config.AZURE_DEPLOYMENT_COMPLETION,
                messages=messages,
                temperature=0.1,  # Lower temperature for more precise answers
                max_tokens=150,   # Shorter responses
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        
        # Cache the answer
        llm_response_cache[cache_key] = answer
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in concise answer generation: {e}")
        return f"Error generating answer: {str(e)}"

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=Config.RETRY_DELAY, max=6))
async def generate_answer_dynamic(query: str, relevant_docs: Dict, conversation_history=None, org_info=None, tone=None) -> str:
    """Dynamic answer generation that adapts to document content."""
    if not async_client:
        raise Exception("Azure OpenAI client not initialized.")
    
    try:
        # Fast cache key generation
        cache_key = f"dynamic:{query}:{len(relevant_docs.get('documents', [[]])[0])}"
        cached_answer = llm_response_cache.get(cache_key)
        
        if cached_answer is not None:
            return cached_answer
        
        # Dynamic prompt construction
        system_prompt = construct_rag_prompt_dynamic(query, relevant_docs, org_info, tone)
        
        # Simple message structure for speed
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            # Dynamic completion with optimized parameters
            response = await async_client.chat.completions.create(
                model=Config.AZURE_DEPLOYMENT_COMPLETION,
                messages=messages,
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=800,   # Increased for better explanations
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        except asyncio.TimeoutError:
            # Fallback with sync client
            response = sync_client.chat.completions.create(
                model=Config.AZURE_DEPLOYMENT_COMPLETION,
                messages=messages,
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=800,   # Increased for better explanations
                timeout=Config.COMPLETION_TIMEOUT
            )
            answer = response.choices[0].message.content
        
        # Cache the answer
        llm_response_cache[cache_key] = answer
        
        return answer
        
    except Exception as e:
        logger.error(f"Error in dynamic answer generation: {e}")
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

async def process_questions_parallel_concise(questions: List[str], collection_name: str, chroma_client=None, org_info=None, tone=None) -> List[str]:
    """Process multiple questions in parallel using concise answer generation."""
    
    try:
        # Process questions in parallel
        async def process_single_question(question):
            try:
                # Fast vector search
                relevant_docs = await query_vector_db_fast(question, collection_name, chroma_client=chroma_client)
                
                # Concise answer generation
                answer = await generate_answer_concise(question, relevant_docs, org_info=org_info, tone=tone)
                
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
        logger.error(f"Error in parallel concise question processing: {e}")
        return [f"Error: {str(e)}"] * len(questions)

async def process_questions_parallel_dynamic(questions: List[str], collection_name: str, chroma_client=None, org_info=None, tone=None) -> List[str]:
    """Process multiple questions in parallel using dynamic answer generation."""
    
    try:
        # Process questions in parallel
        async def process_single_question(question):
            try:
                # Fast vector search
                relevant_docs = await query_vector_db_fast(question, collection_name, chroma_client=chroma_client)
                
                # Dynamic answer generation
                answer = await generate_answer_dynamic(question, relevant_docs, org_info=org_info, tone=tone)
                
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
        logger.error(f"Error in parallel dynamic question processing: {e}")
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