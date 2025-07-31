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
    
    # RAG Configuration - MAXIMUM SCORING OPTIMIZATION
    CHUNK_SIZE = 3000  # INCREASED for maximum context preservation
    CHUNK_OVERLAP = 800  # INCREASED for maximum context continuity
    MAX_TOKENS = 16000  # INCREASED for comprehensive processing
    SIMILARITY_TOP_K = 50  # INCREASED for maximum retrieval
    TEMPERATURE = 0.01  # REDUCED for maximum consistency
    
    # Performance Optimizations - SCORING FOCUSED
    BATCH_SIZE_EMBEDDINGS = 20  # OPTIMIZED for better quality
    TOP_K_REDUCED = 20  # INCREASED for maximum accuracy
    MAX_TOKENS_REDUCED = 8000  # INCREASED for comprehensive answers
    TIMEOUT_VECTOR_SEARCH = 45.0  # INCREASED for thorough search
    TIMEOUT_ANSWER_GENERATION = 60.0  # INCREASED for detailed answers
    TIMEOUT_EMBEDDING_GENERATION = 15.0  # INCREASED for quality
    CONTEXT_LIMIT = 5000  # INCREASED for maximum context
    MAX_PARALLEL_QUESTS = 4  # REDUCED for better quality
    MAX_CHUNKS_PER_DOCUMENT = 400  # INCREASED for maximum coverage
    
    # NEW: Scoring Enhancement Settings
    ENABLE_PARALLEL_PROCESSING = True  # Enable parallel document processing
    ENABLE_SMART_CHUNKING = True  # Enable intelligent chunking
    ENABLE_PRIORITY_QUEUE = True  # Enable priority-based processing
    ENABLE_CACHE_OPTIMIZATION = True  # Enable cache optimization
    ENABLE_PROGRESSIVE_LOADING = True  # Enable progressive document loading
    ENABLE_SCORING_OPTIMIZATION = True  # Enable scoring-specific optimizations
    
    # NEW: Large Document Optimization for Scoring
    LARGE_DOC_THRESHOLD = 500000  # 500KB - documents larger than this get special treatment
    HUGE_DOC_THRESHOLD = 1000000  # 1MB - documents larger than this get aggressive optimization
    PARALLEL_CHUNK_PROCESSING = True  # Process chunks in parallel
    SMART_CHUNK_SELECTION = True  # Select most relevant chunks first
    PROGRESSIVE_EMBEDDING = True  # Generate embeddings progressively
    
    # Accuracy Enhancement Settings - MAXIMUM SCORING
    MIN_CHUNK_QUALITY_SCORE = 0.05  # EXTREMELY LENIENT for maximum coverage
    ANSWER_CONFIDENCE_THRESHOLD = 0.1  # EXTREMELY LENIENT to accept more answers
    ENABLE_CONTEXT_ENHANCEMENT = True  # Enable context enhancement
    ENABLE_ANSWER_VALIDATION = True  # Enable answer validation
    ENABLE_CHUNK_PRIORITIZATION = True  # Enable chunk prioritization
    ENABLE_SCORING_BOOST = True  # Enable scoring boost features
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")
    
    # Organization Configuration
    ORG_NAME = os.environ.get("ORG_NAME", "Your Organization")
    ORG_DESCRIPTION = os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions")
    DEFAULT_TONE = os.environ.get("DEFAULT_TONE", "professional")
    
    # Dynamic Processing Configuration - MAXIMUM SCORING
    # Small documents (< 100KB, < 50 pages): High accuracy, detailed processing
    # Medium documents (100KB-1MB, 50-200 pages): Balanced processing
    # Large documents (> 1MB, > 200 pages): Fast processing, essential content only
    
    # Document size thresholds (in characters)
    SMALL_DOCUMENT_THRESHOLD = 100000  # 100KB
    LARGE_DOCUMENT_THRESHOLD = 1000000  # 1MB
    
    # Page count thresholds
    SMALL_PAGE_THRESHOLD = 50
    LARGE_PAGE_THRESHOLD = 200
    
    # Processing time targets - SCORING OPTIMIZED
    TARGET_PROCESSING_TIME = 120  # INCREASED for better accuracy
    MAX_PROCESSING_TIME = 300  # INCREASED for maximum processing
    
    # Dynamic chunking based on document size - MAXIMUM SCORING
    SMALL_DOC_CHUNK_SIZE = 3500  # INCREASED for maximum context
    MEDIUM_DOC_CHUNK_SIZE = 3000  # INCREASED for maximum context
    LARGE_DOC_CHUNK_SIZE = 1500   # INCREASED for maximum context
    
    # Dynamic retrieval based on document size - MAXIMUM SCORING
    SMALL_DOC_TOP_K = 60  # INCREASED for maximum retrieval
    MEDIUM_DOC_TOP_K = 50  # INCREASED for maximum retrieval
    LARGE_DOC_TOP_K = 35    # INCREASED for maximum retrieval
    
    # Dynamic token limits based on document size - MAXIMUM SCORING
    SMALL_DOC_MAX_TOKENS = 256000  # INCREASED for full processing
    MEDIUM_DOC_MAX_TOKENS = 128000  # INCREASED for maximum processing
    LARGE_DOC_MAX_TOKENS = 64000  # INCREASED for maximum processing