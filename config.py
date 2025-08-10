"""
Configuration file for RAG System
- Environment-based configuration
- Dynamic model selection
- Configurable API endpoints
- No hardcoded values
"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the RAG system."""
    
    def __init__(self):
        # API Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
        self.OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION', '2024-02-15-preview')
        self.OPENAI_API_TYPE = os.getenv('OPENAI_API_TYPE', 'azure')
        
        # Azure OpenAI Configuration
        self.AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
        self.AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        # Google AI Configuration
        self.GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')
        
        # Model Configuration - Dynamic based on environment
        self.DEFAULT_COMPLETION_MODEL = os.getenv('DEFAULT_COMPLETION_MODEL', 'gpt-4o')
        self.DEFAULT_EMBEDDING_MODEL = os.getenv('DEFAULT_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.DEFAULT_VISION_MODEL = os.getenv('DEFAULT_VISION_MODEL', 'gpt-4o')
        
        # Fallback models for different providers
        self.FALLBACK_MODELS = {
            'openai': {
                'completion': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                'embedding': ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002']
            },
            'azure': {
                'completion': ['gpt-4o', 'gpt-4o-mini', 'gpt-4', 'gpt-35-turbo'],
                'embedding': ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002']
            },
            'google': {
                'completion': ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
                'embedding': ['text-embedding-004', 'text-embedding-gecko-001']
            }
        }
        
        # Vector Database Configuration
        self.CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')
        self.EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
        
        # Document Processing Configuration
        self.CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
        self.CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
        self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '50'))  # MB
        
        # Supported file types
        self.SUPPORTED_FILE_TYPES = [
            '.pdf', '.txt', '.docx', '.doc', '.md', '.html', '.json', '.csv', '.xlsx', '.xls'
        ]
        
        # RAG Configuration
        self.TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '5'))
        self.SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
        self.MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', '8000'))
        
        # API Rate Limiting
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
        self.RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
        
        # Security Configuration
        self.ENABLE_AUTHENTICATION = os.getenv('ENABLE_AUTHENTICATION', 'false').lower() == 'true'
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
        self.JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'rag_system.log')
        
        # Performance Configuration
        self.ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        self.CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # seconds
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
        
        # Thread Pool Configuration
        self.MAX_WORKERS_CHUNKING = int(os.getenv('MAX_WORKERS_CHUNKING', '4'))
        self.MAX_WORKERS_EMBEDDINGS = int(os.getenv('MAX_WORKERS_EMBEDDINGS', '8'))
        self.MAX_WORKERS_ANSWERS = int(os.getenv('MAX_WORKERS_ANSWERS', '4'))
        
        # Timeout Configuration
        self.EMBEDDING_TIMEOUT = int(os.getenv('EMBEDDING_TIMEOUT', '60'))
        self.COMPLETION_TIMEOUT = int(os.getenv('COMPLETION_TIMEOUT', '120'))
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        
        # Retry Configuration
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', '1'))
        
        # Azure Deployment Configuration
        self.AZURE_DEPLOYMENT_EMBEDDING = os.getenv('AZURE_DEPLOYMENT_EMBEDDING', 'text-embedding-3-small')
        self.AZURE_DEPLOYMENT_COMPLETION = os.getenv('AZURE_DEPLOYMENT_COMPLETION', 'gpt-4o')
        
        # Model Parameters
        self.TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
        self.MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4000'))
        
        # Batch Processing Configuration
        self.BATCH_SIZE_EMBEDDINGS = int(os.getenv('BATCH_SIZE_EMBEDDINGS', '100'))
        self.BATCH_SIZE_CHUNKS = int(os.getenv('BATCH_SIZE_CHUNKS', '50'))
        
        # Performance Targets
        self.TARGET_PROCESSING_TIME = int(os.getenv('TARGET_PROCESSING_TIME', '60'))
        
        # Document Processing Limits
        self.MIN_CHUNK_LENGTH = int(os.getenv('MIN_CHUNK_LENGTH', '100'))
        self.MAX_CHUNKS_PER_DOCUMENT = int(os.getenv('MAX_CHUNKS_PER_DOCUMENT', '1000'))
        self.MIN_MEANINGFUL_CHARS = int(os.getenv('MIN_MEANINGFUL_CHARS', '50'))
        self.CONTEXT_WINDOW_SIZE = int(os.getenv('CONTEXT_WINDOW_SIZE', '4000'))
        self.SIMILARITY_TOP_K = int(os.getenv('SIMILARITY_TOP_K', '5'))
        
        # Feature Flags
        self.ENABLE_FAST_CHUNKING = os.getenv('ENABLE_FAST_CHUNKING', 'true').lower() == 'true'
        self.PPT_EXTRACT_NOTES = os.getenv('PPT_EXTRACT_NOTES', 'true').lower() == 'true'
        
        # Excel Processing Limits
        self.MAX_EXCEL_ROWS = int(os.getenv('MAX_EXCEL_ROWS', '1000'))
        self.MAX_EXCEL_COLUMNS = int(os.getenv('MAX_EXCEL_COLUMNS', '100'))
        
        # ZIP Processing Limits
        self.MAX_ZIP_FILES = int(os.getenv('MAX_ZIP_FILES', '100'))
        
        # Gemini Configuration
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
        
        # External API Configuration
        self.EXTERNAL_APIS = {
            'hackrx': {
                'base_url': os.getenv('HACKRX_BASE_URL', 'https://register.hackrx.in'),
                'timeout': int(os.getenv('HACKRX_TIMEOUT', '30')),
                'retries': int(os.getenv('HACKRX_RETRIES', '3'))
            }
        }
        
        # Document Analysis Configuration
        self.ENABLE_DOCUMENT_ANALYSIS = os.getenv('ENABLE_DOCUMENT_ANALYSIS', 'true').lower() == 'true'
        self.ENABLE_ACTION_DETECTION = os.getenv('ENABLE_ACTION_DETECTION', 'true').lower() == 'true'
        self.ENABLE_ROLE_DETECTION = os.getenv('ENABLE_ROLE_DETECTION', 'true').lower() == 'true'
        
        # Role Detection Configuration
        self.DOCUMENT_ROLES = [
            'medical', 'legal', 'financial', 'technical', 'educational', 
            'news', 'travel', 'policy', 'general'
        ]
        
        # Action Detection Configuration
        self.ACTION_TYPES = [
            'api_call', 'form_submission', 'calculation', 'mission_execution'
        ]
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        required_vars = []
        
        # Check if at least one AI provider is configured
        if not any([self.OPENAI_API_KEY, self.AZURE_OPENAI_API_KEY, self.GOOGLE_AI_API_KEY]):
            required_vars.append("At least one AI provider API key (OPENAI_API_KEY, AZURE_OPENAI_API_KEY, or GOOGLE_AI_API_KEY)")
        
        # Check Azure-specific requirements
        if self.OPENAI_API_TYPE == 'azure' and not self.AZURE_OPENAI_ENDPOINT:
            required_vars.append("AZURE_OPENAI_ENDPOINT when using Azure OpenAI")
        
        if required_vars:
            raise ValueError(f"Missing required configuration: {', '.join(required_vars)}")
    
    def get_model_config(self, provider: str = None, model_type: str = 'completion') -> Dict[str, Any]:
        """
        Get model configuration for a specific provider and type.
        
        Args:
            provider: AI provider ('openai', 'azure', 'google')
            model_type: Model type ('completion', 'embedding')
            
        Returns:
            Model configuration dictionary
        """
        if not provider:
            # Auto-detect provider based on available API keys
            if self.AZURE_OPENAI_API_KEY:
                provider = 'azure'
            elif self.OPENAI_API_KEY:
                provider = 'openai'
            elif self.GOOGLE_AI_API_KEY:
                provider = 'google'
            else:
                raise ValueError("No AI provider configured")
        
        if provider not in self.FALLBACK_MODELS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        if model_type not in self.FALLBACK_MODELS[provider]:
            raise ValueError(f"Unsupported model type: {model_type} for provider {provider}")
        
        models = self.FALLBACK_MODELS[provider][model_type]
        
        return {
            'provider': provider,
            'type': model_type,
            'models': models,
            'default': models[0] if models else None
        }
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """
        Get configuration for external APIs.
        
        Args:
            api_name: Name of the API
            
        Returns:
            API configuration dictionary
        """
        return self.EXTERNAL_APIS.get(api_name, {})
    
    def is_provider_available(self, provider: str) -> bool:
        """
        Check if a specific AI provider is available.
        
        Args:
            provider: AI provider name
            
        Returns:
            True if provider is available, False otherwise
        """
        if provider == 'azure':
            return bool(self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_ENDPOINT)
        elif provider == 'openai':
            return bool(self.OPENAI_API_KEY)
        elif provider == 'google':
            return bool(self.GOOGLE_AI_API_KEY)
        return False
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available AI providers.
        
        Returns:
            List of available provider names
        """
        providers = []
        if self.is_provider_available('azure'):
            providers.append('azure')
        if self.is_provider_available('openai'):
            providers.append('openai')
        if self.is_provider_available('google'):
            providers.append('google')
        return providers
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'openai_api_type': self.OPENAI_API_TYPE,
            'azure_openai_endpoint': self.AZURE_OPENAI_ENDPOINT,
            'default_completion_model': self.DEFAULT_COMPLETION_MODEL,
            'default_embedding_model': self.DEFAULT_EMBEDDING_MODEL,
            'chunk_size': self.CHUNK_SIZE,
            'chunk_overlap': self.CHUNK_OVERLAP,
            'top_k_results': self.TOP_K_RESULTS,
            'similarity_threshold': self.SIMILARITY_THRESHOLD,
            'available_providers': self.get_available_providers(),
            'enable_document_analysis': self.ENABLE_DOCUMENT_ANALYSIS,
            'enable_action_detection': self.ENABLE_ACTION_DETECTION,
            'enable_role_detection': self.ENABLE_ROLE_DETECTION
        }

# Global configuration instance
config = Config()

# Export commonly used values for backward compatibility
OPENAI_API_KEY = config.OPENAI_API_KEY
OPENAI_API_BASE = config.OPENAI_API_BASE
OPENAI_API_VERSION = config.OPENAI_API_VERSION
OPENAI_API_TYPE = config.OPENAI_API_TYPE

AZURE_OPENAI_API_KEY = config.AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT = config.AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_VERSION = config.AZURE_OPENAI_API_VERSION

GOOGLE_AI_API_KEY = config.GOOGLE_AI_API_KEY

# Dynamic model selection - no hardcoded values
def get_completion_model(provider: str = None) -> str:
    """Get completion model for specified provider."""
    model_config = config.get_model_config(provider, 'completion')
    return model_config['default']

def get_embedding_model(provider: str = None) -> str:
    """Get embedding model for specified provider."""
    model_config = config.get_model_config(provider, 'embedding')
    return model_config['default']

def get_vision_model(provider: str = None) -> str:
    """Get vision model for specified provider."""
    if provider == 'google':
        return 'gemini-2.0-flash-exp'
    else:
        return config.DEFAULT_VISION_MODEL

# Configuration validation on import
try:
    config._validate_config()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your environment variables and configuration.")