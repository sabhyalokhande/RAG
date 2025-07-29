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

def chunk_text(text, chunk_size=512, chunk_overlap=50):
    """Split text into overlapping chunks of specified size."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Determine the end position for this chunk
        end = min(start + chunk_size, text_length)
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < text_length:
            # Look for a space or newline to break at
            while end > start + chunk_size - chunk_overlap and not text[end].isspace():
                end -= 1
        
        # Extract the chunk and add it to our list
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move the start pointer, accounting for overlap
        start = end
        if start < text_length and text[start].isspace():
            start += 1  # Skip the space we broke at
        
        # Apply overlap (but not if we're already at the end)
        if start < text_length:
            start = max(start - chunk_overlap, 0)
    
    return chunks 