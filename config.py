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
    
    # Document Processing - Optimized for 30-second target
    CHUNK_SIZE = 800  # Reduced for faster processing
    CHUNK_OVERLAP = 200  # Reduced for speed
    MAX_CHUNKS_PER_DOCUMENT = 80  # Reduced for speed
    
    # Vector Search - Optimized for speed
    SIMILARITY_TOP_K = 25  # Reduced for faster retrieval
    SIMILARITY_THRESHOLD = 0.5  # Reduced for more inclusive retrieval
    
    # AI Model Settings - Optimized for speed
    TEMPERATURE = 0.1  # Low temperature for consistent answers
    MAX_TOKENS = 1500  # Reduced for faster generation
    MAX_PROCESSING_TIME = 30  # Target: 30 seconds total
    
    # ============================================================================
    # NEW FILE TYPE PROCESSING SETTINGS
    # ============================================================================
    
    # PowerPoint Processing
    ENABLE_PPT_PROCESSING = True
    PPT_EXTRACT_NOTES = True
    PPT_EXTRACT_SHAPES = True
    PPT_EXTRACT_TABLES = True
    
    # Image Processing - Gemini API
    ENABLE_IMAGE_PROCESSING = True
    GEMINI_API_ENABLED = True
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    GEMINI_TIMEOUT = 10  # 10 seconds timeout for Gemini API
    GEMINI_MAX_RETRIES = 2
    
    # Excel Processing
    ENABLE_EXCEL_PROCESSING = True
    MAX_EXCEL_ROWS = 10000
    MAX_EXCEL_COLUMNS = 100
    EXCEL_EXTRACT_FORMULAS = False  # Set to True if you want to extract formulas
    
    # CSV Processing
    ENABLE_CSV_PROCESSING = True
    CSV_ENCODING_DETECTION = True
    CSV_DEFAULT_ENCODING = "utf-8"
    CSV_MAX_ROWS = 10000
    CSV_MAX_COLUMNS = 100
    
    # ZIP Processing
    ENABLE_ZIP_PROCESSING = True
    MAX_ZIP_FILES = 20  # Limit number of files to process from ZIP
    ZIP_EXTRACT_RECURSIVE = True  # Enable recursive extraction for nested ZIPs
    
    # ============================================================================
    # PARALLEL PROCESSING OPTIMIZATION
    # ============================================================================
    
    # Parallel Processing Settings
    ENABLE_PARALLEL_PROCESSING = True
    PARALLEL_CHUNK_PROCESSING = True
    PARALLEL_EMBEDDING_PROCESSING = True
    PARALLEL_ANSWER_GENERATION = True
    
    # Thread Pool Settings - Optimized for speed
    MAX_WORKERS_CHUNKING = 12  # Increased for faster chunk processing
    MAX_WORKERS_EMBEDDINGS = 8  # Increased for faster embedding generation
    MAX_WORKERS_ANSWERS = 6  # Increased for faster answer generation
    
    # Batch Processing - Optimized for speed
    BATCH_SIZE_EMBEDDINGS = 100  # Increased for faster processing
    BATCH_SIZE_CHUNKS = 200  # Process chunks in larger batches
    
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
    
    # Processing Modes - Enhanced for better recall
    SMALL_DOC_TOP_K = 20  # Increased for better coverage
    MEDIUM_DOC_TOP_K = 35  # Increased for better coverage
    LARGE_DOC_TOP_K = 50  # Increased for better coverage
    
    # Time Targets - Optimized for 30-second total
    TARGET_PROCESSING_TIME = 30  # 30 seconds target
    DOCUMENT_PROCESSING_TARGET = 15  # 15 seconds for document
    QUESTIONS_PROCESSING_TARGET = 15  # 15 seconds for questions
    
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
        print(f"   ENABLE_PPT_PROCESSING: {cls.ENABLE_PPT_PROCESSING}")
        print(f"   ENABLE_IMAGE_PROCESSING: {cls.ENABLE_IMAGE_PROCESSING}")
        print(f"   GEMINI_API_ENABLED: {cls.GEMINI_API_ENABLED}")
        print(f"   GEMINI_API_KEY: {'✅ Set' if cls.GEMINI_API_KEY else '❌ Missing'}")
        print(f"   GEMINI_MODEL: {cls.GEMINI_MODEL}")
        print(f"   ENABLE_EXCEL_PROCESSING: {cls.ENABLE_EXCEL_PROCESSING}")
        print(f"   ENABLE_CSV_PROCESSING: {cls.ENABLE_CSV_PROCESSING}")
        print("="*80)

# Validate configuration on import
Config.validate_config()