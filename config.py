# RAG System Configuration - OPTIMIZED FOR SPEED (<60s) WITH ACCURACY
import os
from typing import Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

class Config:
    # ============================================================================
    # CORE SETTINGS - OPTIMIZED FOR SPEED
    # ============================================================================
    
    # Document Processing - Optimized for speed
    CHUNK_SIZE = 2000  # Reduced from 3000 for faster processing
    CHUNK_OVERLAP = 200  # Reduced from 300
    MAX_CHUNKS_PER_DOCUMENT = 100  # Limit chunks for speed
    
    # Vector Search - Optimized for speed
    SIMILARITY_TOP_K = 25  # Reduced from 50 for faster retrieval
    SIMILARITY_THRESHOLD = 0.7  # Increased threshold for better precision
    
    # AI Model Settings - Optimized for speed
    TEMPERATURE = 0.1  # Low temperature for consistent answers
    MAX_TOKENS = 2000  # Reduced from 4000 for faster generation
    MAX_PROCESSING_TIME = 60  # Target: 60 seconds total
    
    # ============================================================================
    # PARALLEL PROCESSING OPTIMIZATION
    # ============================================================================
    
    # Parallel Processing Settings
    ENABLE_PARALLEL_PROCESSING = True
    PARALLEL_CHUNK_PROCESSING = True
    PARALLEL_EMBEDDING_PROCESSING = True
    PARALLEL_ANSWER_GENERATION = True
    
    # Thread Pool Settings
    MAX_WORKERS_CHUNKING = 8  # Parallel chunk processing
    MAX_WORKERS_EMBEDDINGS = 6  # Parallel embedding generation
    MAX_WORKERS_ANSWERS = 4  # Parallel answer generation
    
    # Batch Processing
    BATCH_SIZE_EMBEDDINGS = 50  # Increased for faster processing
    BATCH_SIZE_CHUNKS = 100  # Process chunks in larger batches
    
    # ============================================================================
    # SPEED OPTIMIZATION SETTINGS
    # ============================================================================
    
    # Document Processing Speed
    ENABLE_FAST_PDF_EXTRACTION = True
    ENABLE_FAST_TEXT_PROCESSING = True
    ENABLE_FAST_CHUNKING = True
    
    # Vector Database Speed
    ENABLE_FAST_VECTOR_SEARCH = True
    ENABLE_FAST_SIMILARITY_CALC = True
    
    # AI Generation Speed
    ENABLE_FAST_ANSWER_GENERATION = True
    ENABLE_FAST_PROMPT_PROCESSING = True
    
    # ============================================================================
    # ACCURACY PRESERVATION SETTINGS
    # ============================================================================
    
    # Quality Thresholds - Kept lenient for accuracy
    MIN_CHUNK_QUALITY_SCORE = 0.1  # Very lenient for maximum information
    ANSWER_CONFIDENCE_THRESHOLD = 0.3  # Very lenient for accuracy
    MIN_CHUNK_LENGTH = 3  # Very short chunks allowed
    MIN_MEANINGFUL_CHARS = 1  # Very lenient
    
    # Context Enhancement - Preserved for accuracy
    ENABLE_CONTEXT_ENHANCEMENT = True
    CONTEXT_WINDOW_SIZE = 300  # Reduced from 400 for speed
    ENABLE_SEMANTIC_BOUNDARIES = True
    ENABLE_KEYWORD_PRIORITIZATION = True
    
    # ============================================================================
    # DYNAMIC CONFIGURATION
    # ============================================================================
    
    # Document Size Based Configuration
    SMALL_DOC_THRESHOLD = 50000  # characters
    LARGE_DOC_THRESHOLD = 200000  # characters
    
    # Processing Modes
    SMALL_DOC_TOP_K = 15  # Reduced for speed
    MEDIUM_DOC_TOP_K = 25  # Reduced for speed
    LARGE_DOC_TOP_K = 35  # Reduced for speed
    
    # Time Targets
    TARGET_PROCESSING_TIME = 60  # 60 seconds target
    DOCUMENT_PROCESSING_TARGET = 20  # 20 seconds for document
    QUESTIONS_PROCESSING_TARGET = 40  # 40 seconds for questions
    
    # ============================================================================
    # CACHING AND OPTIMIZATION
    # ============================================================================
    
    # Cache Settings
    ENABLE_CACHING = True
    CACHE_TTL = 3600  # 1 hour
    MAX_CACHE_SIZE = 1000
    
    # Memory Optimization
    ENABLE_MEMORY_OPTIMIZATION = True
    MAX_MEMORY_USAGE = 0.8  # 80% of available memory
    
    # ============================================================================
    # FALLBACK SETTINGS
    # ============================================================================
    
    # Timeout Settings
    REQUEST_TIMEOUT = 30  # Reduced from 60
    EMBEDDING_TIMEOUT = 15  # Reduced from 30
    COMPLETION_TIMEOUT = 20  # Reduced from 45
    
    # Retry Settings
    MAX_RETRIES = 2  # Reduced from 3
    RETRY_DELAY = 1  # Reduced from 2
    
    # ============================================================================
    # ENVIRONMENT VARIABLES - PROPERLY LOADED FROM .ENV
    # ============================================================================
    
    # Azure OpenAI - Read from environment with proper defaults
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    
    # Use environment variables with proper defaults
    AZURE_DEPLOYMENT_EMBEDDING = os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
    AZURE_DEPLOYMENT_COMPLETION = os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4")
    
    # Vector Database
    CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")
    
    # ============================================================================
    # PERFORMANCE MONITORING
    # ============================================================================
    
    # Performance Tracking
    ENABLE_PERFORMANCE_MONITORING = True
    LOG_PERFORMANCE_METRICS = True
    
    # Debug Settings
    DEBUG_MODE = False
    VERBOSE_LOGGING = False
    
    # ============================================================================
    # VALIDATION AND DEBUGGING
    # ============================================================================
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and print debug info."""
        print("🔧 CONFIGURATION VALIDATION:")
        print(f"   AZURE_OPENAI_API_KEY: {'✅ Set' if cls.AZURE_OPENAI_API_KEY else '❌ Missing'}")
        print(f"   AZURE_OPENAI_ENDPOINT: {'✅ Set' if cls.AZURE_OPENAI_ENDPOINT else '❌ Missing'}")
        print(f"   AZURE_DEPLOYMENT_EMBEDDING: {cls.AZURE_DEPLOYMENT_EMBEDDING}")
        print(f"   AZURE_DEPLOYMENT_COMPLETION: {cls.AZURE_DEPLOYMENT_COMPLETION}")
        print(f"   CHROMA_DB_PATH: {cls.CHROMA_DB_PATH}")
        print(f"   PINECONE_API_KEY: {'✅ Set' if cls.PINECONE_API_KEY else '❌ Missing'}")
        print("="*80)

# Validate configuration on import
Config.validate_config()