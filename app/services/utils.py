"""
Advanced Production-Ready Utils
- Document processing functions
- Text extraction and cleaning
- Chunking algorithms
- File format support
"""

import os
import re
import logging
from io import BytesIO
from typing import List

# Document processing
import docx2txt
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(raw_text):
    """Clean raw text by normalizing whitespace and paragraph spacing."""
    cleaned = re.sub(r'\s+', ' ', raw_text)  # collapse whitespace
    cleaned = re.sub(r'\n{2,}', '\n\n', cleaned)  # normalize paragraph spacing
    return cleaned.strip()

def get_raw_data_from_docx(file):
    """Extract text from a .docx file."""
    # Create /tmp directory if it doesn't exist
    temp_dir = '/tmp'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create a secure temporary file path
    temp_file_path = os.path.join(temp_dir, file.filename.replace('/', '_'))
    
    # Save the file
    file.save(temp_file_path)
    
    try:
        text = docx2txt.process(temp_file_path)
    finally:
        # Ensure the temp file is removed even if processing fails
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    
    return text

def get_raw_data_txt(file):
    """Extract text from a .txt file."""
    return file.read().decode('utf-8')

def get_raw_data_pdf(file):
    """Extract text from a .pdf file."""
    pdf_bytes = file.read()
    pdf_stream = BytesIO(pdf_bytes)

    text = ""
    pdf_reader = PdfReader(pdf_stream)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_file(file):
    """Extract text from a file based on its extension."""
    file_name = file.filename.lower()
    
    try:
        if file_name.endswith(".txt"):
            raw_text = get_raw_data_txt(file)
        elif file_name.endswith(".pdf"):
            raw_text = get_raw_data_pdf(file)
        elif file_name.endswith(".docx"):
            raw_text = get_raw_data_from_docx(file)
        else:
            raise ValueError(f"Unsupported file format: {file_name}")
        
        return clean_text(raw_text)
    except Exception as e:
        logger.error(f"Error extracting text from {file_name}: {str(e)}")
        raise

def chunk_text(text, chunk_size=1200, chunk_overlap=150):
    """Split text into ultra-optimized chunks for maximum speed."""
    if not text:
        return []
    
    # Clean the text first
    text = clean_text(text)
    
    # Use very large chunks for minimal API calls (1200 chars ≈ 300 tokens)
    # Still well under 8192 token limit but much fewer chunks = fastest
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If adding this paragraph would exceed chunk size
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            # Save current chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Start new chunk
            current_chunk = paragraph
        else:
            current_chunk += " " + paragraph if current_chunk else paragraph
    
    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk) > 150]
    
    # Limit to maximum 15 chunks for fastest processing
    if len(chunks) > 15:
        chunks = chunks[:15]
    
    return chunks 