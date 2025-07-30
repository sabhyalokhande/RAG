import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = "2023-06-01-preview"
    
    AZURE_DEPLOYMENT_COMPLETION = os.environ.get("AZURE_DEPLOYMENT_COMPLETION", "gpt-4o-mini")
    AZURE_DEPLOYMENT_EMBEDDING = os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
    
    # ChromaDB Configuration
    CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    
    # RAG Configuration
    CHUNK_SIZE = 2048  # Much larger chunks for fewer API calls
    CHUNK_OVERLAP = 200  # Increased overlap for larger chunks
    MAX_TOKENS = 4000
    SIMILARITY_TOP_K = 5
    TEMPERATURE = 0.1
    
    # Performance Optimizations
    BATCH_SIZE_EMBEDDINGS = 20  # Reduced to avoid rate limits
    TOP_K_REDUCED = 3  # Reduced from 5
    MAX_TOKENS_REDUCED = 1000  # Reduced from 4000
    TIMEOUT_VECTOR_SEARCH = 10.0  # Reduced from 15.0
    TIMEOUT_ANSWER_GENERATION = 15.0  # Reduced from 25.0
    TIMEOUT_EMBEDDING_GENERATION = 5.0  # Reduced timeout for embeddings
    CONTEXT_LIMIT = 500  # Limit context length per document
    MAX_PARALLEL_QUESTS = 10  # Limit parallel processing
    MAX_CHUNKS_PER_DOCUMENT = 50  # Limit chunks to avoid rate limits
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")
    
    # Organization Configuration
    ORG_NAME = os.environ.get("ORG_NAME", "Your Organization")
    ORG_DESCRIPTION = os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions")
    DEFAULT_TONE = os.environ.get("DEFAULT_TONE", "professional")