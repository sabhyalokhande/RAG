"""
Advanced Production-Ready Utils
- Document processing functions
- Text extraction and cleaning
- Chunking algorithms with semantic boundaries
- File format support
"""

import os
import re
import logging
import asyncio
from typing import List, Dict, Optional
import PyPDF2
import docx
from io import BytesIO
import requests
from urllib.parse import urlparse
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_token_count(text: str, model: str = "text-embedding-3-large") -> int:
    """Get the token count for a text using a simple approximation."""
    try:
        # Simple approximation: 1 token ≈ 4 characters for English text
        # This is a reasonable approximation for text-embedding-3-large
        return len(text) // 4
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        return len(text) // 4

def truncate_text_for_embeddings(text: str, max_tokens: int = 128000) -> str:
    """Truncate text to stay within the embedding model's token limit - OPTIMIZED for performance."""
    if get_token_count(text) <= max_tokens:
        return text
    
    # OPTIMIZED token limit for better performance
    # 128000 tokens ≈ 512000 characters (optimized from 256000 tokens)
    max_chars = max_tokens * 4
    return text[:max_chars]

def clean_text(text: str) -> str:
    """Clean and normalize text for better processing."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']', '', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Remove multiple periods
    text = re.sub(r'\.{2,}', '.', text)
    
    return text.strip()

def extract_text_from_file(file) -> str:
    """Extract text from various file formats with enhanced error handling."""
    try:
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            return extract_text_from_pdf(file)
        elif filename.endswith('.docx'):
            return extract_text_from_docx(file)
        elif filename.endswith('.txt'):
            return extract_text_from_txt(file)
        else:
            logger.warning(f"Unsupported file format: {filename}")
            return ""
            
    except Exception as e:
        logger.error(f"Error extracting text from file: {e}")
        return ""

def extract_text_from_pdf(file) -> str:
    """Extract text from PDF with enhanced error handling."""
    try:
        # Check if file has content
        if hasattr(file, 'content'):
            logger.info(f"PDF file has {len(file.content)} bytes")
        else:
            logger.warning("PDF file object doesn't have content attribute")
        
        # Try to read the file first
        try:
            file.seek(0)
            content = file.read()
            logger.info(f"Successfully read {len(content)} bytes from PDF file")
        except Exception as read_error:
            logger.error(f"Error reading PDF file: {read_error}")
            return ""
        
        # Use PyPDF2 for text extraction
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ""
            
            # OPTIMIZED: Process pages in parallel for large documents
            if len(pdf_reader.pages) > 50:  # Large document
                logger.info(f"Large PDF detected ({len(pdf_reader.pages)} pages), using parallel processing")
                text = extract_text_parallel(pdf_reader)
            else:
                # Sequential processing for smaller documents
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        logger.debug(f"Processed page {page_num + 1}")
                    except Exception as page_error:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {page_error}")
                        continue
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return clean_text(text)
            
        except Exception as pdf_error:
            logger.error(f"Error processing PDF: {pdf_error}")
            return ""
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_parallel(pdf_reader) -> str:
    """Extract text from PDF pages in parallel for better performance."""
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all page extraction tasks
            future_to_page = {
                executor.submit(extract_page_text, page, i): i 
                for i, page in enumerate(pdf_reader.pages)
            }
            
            # Collect results in order
            page_texts = [""] * len(pdf_reader.pages)
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_text = future.result()
                    page_texts[page_num] = page_text
                except Exception as e:
                    logger.warning(f"Error processing page {page_num + 1}: {e}")
            
            # Combine all page texts
            text = "\n".join(page_texts)
            logger.info(f"Parallel extraction completed: {len(text)} characters")
            return text
            
    except Exception as e:
        logger.error(f"Error in parallel text extraction: {e}")
        return ""

def extract_page_text(page, page_num: int) -> str:
    """Extract text from a single PDF page."""
    try:
        text = page.extract_text()
        if text:
            logger.debug(f"Extracted {len(text)} characters from page {page_num + 1}")
            return text
        return ""
    except Exception as e:
        logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
        return ""

def extract_text_from_docx(file) -> str:
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        logger.info(f"Successfully extracted {len(text)} characters from DOCX")
        return clean_text(text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_txt(file) -> str:
    """Extract text from TXT file."""
    try:
        content = file.read()
        text = content.decode('utf-8')
        logger.info(f"Successfully extracted {len(text)} characters from TXT")
        return clean_text(text)
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {e}")
        return ""

def extract_text_from_url(url: str) -> str:
    """Extract text from URL with enhanced error handling."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Try to determine file type and extract accordingly
        content_type = response.headers.get('content-type', '').lower()
        
        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            # Handle PDF from URL
            pdf_reader = PyPDF2.PdfReader(BytesIO(response.content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Assume it's text
            text = response.text
        
        logger.info(f"Successfully extracted {len(text)} characters from URL")
        return clean_text(text)
        
    except Exception as e:
        logger.error(f"Error extracting text from URL: {e}")
        return ""

def find_semantic_boundaries(text, start, end, max_lookback=100):
    """Find semantic boundaries for chunking."""
    # Look for sentence endings, paragraph breaks, or natural breaks
    for i in range(end, max(start, end - max_lookback), -1):
        if text[i-1] in '.!?':
            return i
        elif text[i-1] == '\n':
            return i
    return end

def is_high_quality_chunk(chunk: str) -> bool:
    """Check if a chunk is high quality for better accuracy - INTELLIGENT REASONING."""
    if not chunk or len(chunk.strip()) < 3:  # EXTREMELY LENIENT for maximum coverage
        return False
    
    # Check for meaningful content (not just whitespace or special characters)
    meaningful_chars = len(re.sub(r'[^\w]', '', chunk))
    if meaningful_chars < 1:  # EXTREMELY LENIENT for maximum coverage
        return False
    
    # Only reject extremely long chunks without any sentence structure
    sentence_endings = chunk.count('.') + chunk.count('!') + chunk.count('?')
    if sentence_endings == 0 and len(chunk) > 10000:  # EXTREMELY LENIENT
        return False
    
    # Accept all other chunks - no keyword requirements
    return True

def chunk_text(text, chunk_size=1024, chunk_overlap=256):
    """Split text into overlapping chunks with semantic boundaries for better accuracy."""
    if not text:
        return []
    
    # Truncate text to stay within embedding model limits
    text = truncate_text_for_embeddings(text, max_tokens=8000)
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        if end >= len(text):
            chunk = text[start:]
        else:
            # Find semantic boundary
            boundary = find_semantic_boundaries(text, start, end)
            chunk = text[start:boundary]
        
        # Only add high-quality chunks
        if chunk and is_high_quality_chunk(chunk):
            chunks.append(chunk.strip())
        
        # Move start position with overlap
        start = start + chunk_size - chunk_overlap
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks

def chunk_text_advanced(text, chunk_size=None, chunk_overlap=None, max_tokens=None, page_count=None):
    """Advanced chunking with dynamic configuration - INTELLIGENT REASONING OPTIMIZATION."""
    if not text:
        return []
    
    # Get dynamic configuration based on document characteristics
    if chunk_size is None or max_tokens is None:
        dynamic_config = get_dynamic_processing_config(len(text), page_count or 0)
        chunk_size = chunk_size or dynamic_config['chunk_size']
        chunk_overlap = chunk_overlap or dynamic_config['chunk_overlap']
        max_tokens = max_tokens or dynamic_config['max_tokens']
    
    logger.info(f"Starting chunking with {len(text)} characters")
    logger.info(f"Dynamic config: chunk_size={chunk_size}, max_tokens={max_tokens}")
    
    # INTELLIGENT REASONING: Enhanced optimization for better understanding
    if len(text) > Config.LARGE_DOC_THRESHOLD:
        logger.info("Large document detected, applying intelligent reasoning optimization")
        max_tokens = min(max_tokens, Config.LARGE_DOC_MAX_TOKENS)
        chunk_size = min(chunk_size, Config.LARGE_DOC_CHUNK_SIZE)
    
    # Truncate text to stay within embedding model limits
    text = truncate_text_for_embeddings(text, max_tokens=max_tokens)
    logger.info(f"After truncation: {len(text)} characters")
    
    # INTELLIGENT REASONING: Use parallel processing for large documents
    if len(text) > Config.LARGE_DOC_THRESHOLD and Config.PARALLEL_CHUNK_PROCESSING:
        logger.info("Using parallel chunking for large document")
        return chunk_text_parallel(text, chunk_size, chunk_overlap)
    
    # Standard chunking for smaller documents
    return chunk_text_standard(text, chunk_size, chunk_overlap)

def chunk_text_parallel(text, chunk_size, chunk_overlap):
    """Chunk text using parallel processing for large documents."""
    try:
        # Split text into sections for parallel processing
        section_size = len(text) // 4  # Split into 4 sections
        sections = [text[i:i+section_size] for i in range(0, len(text), section_size)]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Process each section in parallel
            future_to_section = {
                executor.submit(chunk_text_standard, section, chunk_size, chunk_overlap): i 
                for i, section in enumerate(sections)
            }
            
            # Collect results
            all_chunks = []
            for future in as_completed(future_to_section):
                try:
                    chunks = future.result()
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.warning(f"Error in parallel chunking: {e}")
        
        # Final filtering and deduplication
        final_chunks = []
        seen_chunks = set()
        for chunk in all_chunks:
            if chunk and len(chunk) > 10 and chunk not in seen_chunks:
                final_chunks.append(chunk)
                seen_chunks.add(chunk)
        
        logger.info(f"Parallel chunking completed: {len(final_chunks)} chunks")
        return final_chunks
        
    except Exception as e:
        logger.error(f"Error in parallel chunking: {e}")
        return chunk_text_standard(text, chunk_size, chunk_overlap)

def chunk_text_standard(text, chunk_size, chunk_overlap):
    """Standard chunking algorithm - INTELLIGENT REASONING."""
    # Split into paragraphs first (works for most document types)
    paragraphs = text.split('\n\n')
    logger.info(f"Found {len(paragraphs)} paragraphs")
    
    chunks = []
    
    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If paragraph is small enough, add it as a single chunk
        if len(paragraph) <= chunk_size:
            if is_high_quality_chunk(paragraph):
                chunks.append(paragraph)
        else:
            # For large paragraphs, split into sentences
            sentences = re.split(r'[.!?]+', paragraph)
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # If adding this sentence would exceed chunk size
                if len(current_chunk) + len(sentence) > chunk_size:
                    if current_chunk and is_high_quality_chunk(current_chunk.strip()):
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            # Add the last chunk if high quality
            if current_chunk.strip() and is_high_quality_chunk(current_chunk.strip()):
                chunks.append(current_chunk.strip())
    
    # INTELLIGENT REASONING: Enhanced character-based chunking for better understanding
    if len(chunks) < 25:  # INCREASED threshold for better reasoning
        logger.info("Not enough chunks from paragraph splitting, trying character-based chunking")
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunk = text[start:]
            else:
                boundary = find_semantic_boundaries(text, start, end)
                chunk = text[start:boundary]
            
            if chunk and is_high_quality_chunk(chunk.strip()):
                chunks.append(chunk.strip())
            
            start = start + chunk_size - chunk_overlap
            if start >= len(text):
                break
    
    # Final filtering - EXTREMELY LENIENT for maximum coverage
    final_chunks = [chunk for chunk in chunks if len(chunk) > 5]  # REDUCED to 5 for maximum coverage
    logger.info(f"Final result: {len(final_chunks)} chunks from {len(chunks)} initial chunks")
    
    return final_chunks

def enhance_context_for_accuracy(chunks: List[str]) -> List[str]:
    """Enhance chunks with additional context for better accuracy - INTELLIGENT REASONING."""
    enhanced_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Add context from surrounding chunks
        context_before = chunks[i-1] if i > 0 else ""
        context_after = chunks[i+1] if i < len(chunks)-1 else ""
        
        # INTELLIGENT REASONING: Enhanced context combination for better understanding
        enhanced_chunk = chunk
        if context_before:
            enhanced_chunk = context_before[-400:] + " " + enhanced_chunk  # INCREASED context for reasoning
        if context_after:
            enhanced_chunk = enhanced_chunk + " " + context_after[:400]  # INCREASED context for reasoning
        
        enhanced_chunks.append(enhanced_chunk)
    
    return enhanced_chunks

def prioritize_chunks_by_relevance(chunks: List[str], query_keywords: Optional[List[str]] = None) -> List[str]:
    """Prioritize chunks based on relevance to query - INTELLIGENT REASONING."""
    if not query_keywords:
        return chunks
    
    # Enhanced keyword-based prioritization for reasoning
    scored_chunks = []
    for chunk in chunks:
        score = 0
        chunk_lower = chunk.lower()
        
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            # Exact match gets higher score
            if keyword_lower in chunk_lower:
                score += 5  # INCREASED score for exact matches
            # Partial match gets lower score
            elif any(word in chunk_lower for word in keyword_lower.split()):
                score += 2
            # Related terms get medium score
            elif any(related in chunk_lower for related in get_related_terms(keyword_lower)):
                score += 3
        
        scored_chunks.append((score, chunk))
    
    # Sort by score (highest first)
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks]

def get_related_terms(keyword: str) -> List[str]:
    """Get related terms for better semantic matching - INTELLIGENT REASONING."""
    related_terms = {
        'policy': ['coverage', 'terms', 'conditions', 'clause', 'section', 'provision'],
        'coverage': ['policy', 'benefit', 'protection', 'inclusion', 'scope'],
        'premium': ['payment', 'cost', 'fee', 'amount', 'rate'],
        'claim': ['benefit', 'coverage', 'payment', 'reimbursement'],
        'hospital': ['medical', 'treatment', 'facility', 'care', 'institution'],
        'waiting': ['period', 'time', 'delay', 'exclusion', 'restriction'],
        'grace': ['period', 'extension', 'time', 'payment', 'delay'],
        'maternity': ['pregnancy', 'childbirth', 'delivery', 'birth', 'prenatal'],
        'surgery': ['operation', 'procedure', 'treatment', 'medical', 'surgical'],
        'organ': ['donor', 'transplant', 'medical', 'surgery', 'procedure'],
        'discount': ['reduction', 'saving', 'benefit', 'claim', 'bonus'],
        'health': ['medical', 'wellness', 'preventive', 'checkup', 'examination'],
        'ayush': ['alternative', 'medicine', 'treatment', 'therapy', 'natural'],
        'room': ['accommodation', 'stay', 'lodging', 'charge', 'rent'],
        'icu': ['intensive', 'care', 'unit', 'critical', 'emergency']
    }
    
    return related_terms.get(keyword.lower(), [])

def get_dynamic_processing_config(text_length: int, page_count: int) -> dict:
    """Get dynamic processing configuration based on document characteristics - INTELLIGENT REASONING."""
    if text_length < Config.SMALL_DOCUMENT_THRESHOLD:
        return {
            'chunk_size': Config.SMALL_DOC_CHUNK_SIZE,
            'chunk_overlap': Config.CHUNK_OVERLAP,
            'max_tokens': Config.SMALL_DOC_MAX_TOKENS,
            'processing_mode': 'SMALL'
        }
    elif text_length > Config.LARGE_DOCUMENT_THRESHOLD:
        return {
            'chunk_size': Config.LARGE_DOC_CHUNK_SIZE,
            'chunk_overlap': Config.CHUNK_OVERLAP,
            'max_tokens': Config.LARGE_DOC_MAX_TOKENS,
            'processing_mode': 'LARGE'
        }
    else:
        return {
            'chunk_size': Config.MEDIUM_DOC_CHUNK_SIZE,
            'chunk_overlap': Config.CHUNK_OVERLAP,
            'max_tokens': Config.MEDIUM_DOC_MAX_TOKENS,
            'processing_mode': 'MEDIUM'
        } 