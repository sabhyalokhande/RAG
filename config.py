import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = "2023-06-01-preview"
    
    # Updated to use better models for accuracy
    AZURE_DEPLOYMENT_COMPLETION = os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4")
    AZURE_DEPLOYMENT_EMBEDDING = os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
    
    # Pinecone Configuration (Updated for v7.x with text-embedding-3-large)
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-index")
    PINECONE_DIMENSION = 3072  # text-embedding-3-large dimension (increased from 1536)
    PINECONE_METRIC = "cosine"
    PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")
    
    # Pinecone Performance Settings
    PINECONE_POOL_THREADS = int(os.environ.get("PINECONE_POOL_THREADS", "50"))
    PINECONE_BATCH_SIZE = int(os.environ.get("PINECONE_BATCH_SIZE", "100"))
    PINECONE_QUERY_TIMEOUT = float(os.environ.get("PINECONE_QUERY_TIMEOUT", "10.0"))
    
    # ChromaDB Configuration (fallback)
    CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    
    # RAG Configuration - OPTIMIZED FOR PERFORMANCE + ACCURACY
    CHUNK_SIZE = 2000  # OPTIMIZED from 2500 for better performance
    CHUNK_OVERLAP = 500  # OPTIMIZED from 600 for better performance
    MAX_TOKENS = 12000  # OPTIMIZED from 16000 for better performance
    SIMILARITY_TOP_K = 30  # OPTIMIZED from 40 for better performance
    TEMPERATURE = 0.05  # REDUCED from 0.1 for maximum consistency
    
    # Performance Optimizations - OPTIMIZED FOR SPEED + ACCURACY
    BATCH_SIZE_EMBEDDINGS = 25  # INCREASED from 15 for better performance
    TOP_K_REDUCED = 12  # OPTIMIZED from 15 for better performance
    MAX_TOKENS_REDUCED = 6000  # OPTIMIZED from 8000 for better performance
    TIMEOUT_VECTOR_SEARCH = 30.0  # REDUCED from 45.0 for better performance
    TIMEOUT_ANSWER_GENERATION = 45.0  # REDUCED from 60.0 for better performance
    TIMEOUT_EMBEDDING_GENERATION = 10.0  # REDUCED from 15.0 for better performance
    CONTEXT_LIMIT = 3000  # OPTIMIZED from 4000 for better performance
    MAX_PARALLEL_QUESTS = 6  # REDUCED from 8 for better quality
    MAX_CHUNKS_PER_DOCUMENT = 200  # REDUCED from 300 for better performance
    
    # NEW: Performance Enhancement Settings
    ENABLE_PARALLEL_PROCESSING = True  # Enable parallel document processing
    ENABLE_SMART_CHUNKING = True  # Enable intelligent chunking
    ENABLE_PRIORITY_QUEUE = True  # Enable priority-based processing
    ENABLE_CACHE_OPTIMIZATION = True  # Enable cache optimization
    ENABLE_PROGRESSIVE_LOADING = True  # Enable progressive document loading
    
    # NEW: Large Document Optimization
    LARGE_DOC_THRESHOLD = 500000  # 500KB - documents larger than this get special treatment
    HUGE_DOC_THRESHOLD = 1000000  # 1MB - documents larger than this get aggressive optimization
    PARALLEL_CHUNK_PROCESSING = True  # Process chunks in parallel
    SMART_CHUNK_SELECTION = True  # Select most relevant chunks first
    PROGRESSIVE_EMBEDDING = True  # Generate embeddings progressively
    
    # Accuracy Enhancement Settings - OPTIMIZED
    MIN_CHUNK_QUALITY_SCORE = 0.1  # REDUCED from 0.3 to be extremely inclusive
    ANSWER_CONFIDENCE_THRESHOLD = 0.2  # REDUCED from 0.4 to accept more answers
    ENABLE_CONTEXT_ENHANCEMENT = True  # Enable context enhancement
    ENABLE_ANSWER_VALIDATION = True  # Enable answer validation
    ENABLE_CHUNK_PRIORITIZATION = True  # Enable chunk prioritization
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")
    
    # Organization Configuration
    ORG_NAME = os.environ.get("ORG_NAME", "Your Organization")
    ORG_DESCRIPTION = os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions")
    DEFAULT_TONE = os.environ.get("DEFAULT_TONE", "professional")
    
    # Dynamic Processing Configuration - OPTIMIZED FOR PERFORMANCE + ACCURACY
    # Small documents (< 100KB, < 50 pages): High accuracy, detailed processing
    # Medium documents (100KB-1MB, 50-200 pages): Balanced processing
    # Large documents (> 1MB, > 200 pages): Fast processing, essential content only
    
    # Document size thresholds (in characters)
    SMALL_DOCUMENT_THRESHOLD = 100000  # 100KB
    LARGE_DOCUMENT_THRESHOLD = 1000000  # 1MB
    
    # Page count thresholds
    SMALL_PAGE_THRESHOLD = 50
    LARGE_PAGE_THRESHOLD = 200
    
    # Processing time targets - OPTIMIZED
    TARGET_PROCESSING_TIME = 60  # REDUCED from 90 to 60 seconds target
    MAX_PROCESSING_TIME = 120  # REDUCED from 180 to 120 seconds maximum
    
    # Dynamic chunking based on document size - OPTIMIZED
    SMALL_DOC_CHUNK_SIZE = 2500  # OPTIMIZED from 3000 for better performance
    MEDIUM_DOC_CHUNK_SIZE = 2000  # OPTIMIZED from 2500 for better performance
    LARGE_DOC_CHUNK_SIZE = 1000   # OPTIMIZED from 1200 for better performance
    
    # Dynamic retrieval based on document size - OPTIMIZED
    SMALL_DOC_TOP_K = 35  # OPTIMIZED from 50 for better performance
    MEDIUM_DOC_TOP_K = 30  # OPTIMIZED from 40 for better performance
    LARGE_DOC_TOP_K = 20    # OPTIMIZED from 25 for better performance
    
    # Dynamic token limits based on document size - OPTIMIZED
    SMALL_DOC_MAX_TOKENS = 128000  # OPTIMIZED from 256000 for better performance
    MEDIUM_DOC_MAX_TOKENS = 64000  # OPTIMIZED from 128000 for better performance
    LARGE_DOC_MAX_TOKENS = 32000  # OPTIMIZED from 64000 for better performance