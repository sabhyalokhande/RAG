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
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    MAX_TOKENS = 4000
    SIMILARITY_TOP_K = 5
    TEMPERATURE = 0.1
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")
    
    # Organization Configuration
    ORG_NAME = os.environ.get("ORG_NAME", "Your Organization")
    ORG_DESCRIPTION = os.environ.get("ORG_DESCRIPTION", "A leading provider of innovative solutions")
    DEFAULT_TONE = os.environ.get("DEFAULT_TONE", "professional")