"""
Pinecone Vector Database Services (v7.x)
- High-performance vector storage and retrieval with gRPC support
- Optimized for RAG applications with text-embedding-3-large
- Automatic index management with ServerlessSpec
- Batch operations for efficiency
- Query across namespaces support
"""

import os
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Pinecone v7.x (with gRPC support)
try:
    from pinecone import Pinecone, ServerlessSpec
    from pinecone.grpc import PineconeGRPC
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone not available. Using ChromaDB fallback.")

# Azure OpenAI for embeddings
import openai
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeService:
    """High-performance Pinecone vector database service for RAG applications (v7.x) with text-embedding-3-large."""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "rag-index")
        self.dimension = int(os.environ.get("PINECONE_DIMENSION", "3072"))  # Updated for text-embedding-3-large
        self.metric = os.environ.get("PINECONE_METRIC", "cosine")
        self.cloud = os.environ.get("PINECONE_CLOUD", "aws")
        self.region = os.environ.get("PINECONE_REGION", "us-east-1")
        self.pool_threads = int(os.environ.get("PINECONE_POOL_THREADS", "50"))
        self.batch_size = int(os.environ.get("PINECONE_BATCH_SIZE", "100"))
        self.initialize_pinecone()
        
    def initialize_pinecone(self):
        """Initialize Pinecone client and index with gRPC support."""
        global PINECONE_AVAILABLE
        
        if not PINECONE_AVAILABLE:
            logger.warning("Pinecone not available. Using ChromaDB fallback.")
            return
            
        try:
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                logger.warning("PINECONE_API_KEY not set. Using ChromaDB fallback.")
                return
            
            # Initialize Pinecone with gRPC support
            self.pc = PineconeGRPC(api_key=api_key)
            
            # Test the connection first
            try:
                indexes = self.pc.list_indexes()
                logger.info(f"Successfully connected to Pinecone. Available indexes: {indexes.names()}")
            except Exception as e:
                logger.error(f"Failed to connect to Pinecone: {e}")
                logger.warning("Using ChromaDB fallback")
                return
            
            # Check if index exists, create if not
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region
                    ),
                    deletion_protection="disabled"
                )
                # Wait for index to be ready
                time.sleep(10)
            
            # Connect to index with performance optimizations
            self.index = self.pc.Index(
                name=self.index_name,
                pool_threads=self.pool_threads
            )
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            logger.warning("Falling back to ChromaDB")
            # Force ChromaDB fallback
            PINECONE_AVAILABLE = False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Azure OpenAI with text-embedding-3-large."""
        try:
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            
            if not api_key or not endpoint:
                raise ValueError("Azure OpenAI API key or endpoint not configured")
            
            client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version="2023-06-01-preview",
                azure_endpoint=endpoint
            )
            
            deployment = os.environ.get("AZURE_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")
            
            # Process in batches to avoid rate limits
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Truncate each text to stay within token limits
                truncated_batch = []
                for text in batch:
                    # Import the truncation function
                    from app.services.utils import truncate_text_for_embeddings
                    truncated_text = truncate_text_for_embeddings(text, max_tokens=8000)
                    truncated_batch.append(truncated_text)
                
                try:
                    response = await client.embeddings.create(
                        input=truncated_batch,
                        model=deployment
                    )
                    batch_embeddings = [embedding.embedding for embedding in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch: {e}")
                    # Return zero vectors for failed embeddings to continue processing
                    batch_embeddings = [[0.0] * self.dimension] * len(truncated_batch)
                    all_embeddings.extend(batch_embeddings)
                
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def upsert_documents(self, collection_name: str, documents: List[Dict]) -> Dict:
        """Upsert documents to Pinecone index with metadata using optimized batching."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            vectors = []
            metadata_list = []
            ids = []
            
            for doc in documents:
                # Generate embedding for the text
                embeddings = await self.get_embeddings([doc['text']])
                vector = embeddings[0]
                
                # Create unique ID
                doc_id = f"{collection_name}_{doc.get('file_id', str(uuid.uuid4()))}_{doc.get('chunk_id', 0)}"
                
                # Prepare metadata
                metadata = {
                    'collection_name': collection_name,
                    'file_id': doc.get('file_id', ''),
                    'filename': doc.get('filename', ''),
                    'chunk_id': doc.get('chunk_id', 0),
                    'text': doc['text'][:1000],  # Truncate for metadata
                    'created_at': time.time()
                }
                
                vectors.append(vector)
                metadata_list.append(metadata)
                ids.append(doc_id)
            
            # Upsert to Pinecone in optimized batches
            for i in range(0, len(vectors), self.batch_size):
                batch_vectors = vectors[i:i + self.batch_size]
                batch_metadata = metadata_list[i:i + self.batch_size]
                batch_ids = ids[i:i + self.batch_size]
                
                # Create vectors in the correct format for Pinecone v7.x
                upsert_vectors = []
                for j, (doc_id, vector, metadata) in enumerate(zip(batch_ids, batch_vectors, batch_metadata)):
                    upsert_vectors.append({
                        'id': doc_id,
                        'values': vector,
                        'metadata': metadata
                    })
                
                self.index.upsert(vectors=upsert_vectors)
            
            logger.info(f"Successfully upserted {len(documents)} documents to Pinecone")
            return {
                'status': 'success',
                'documents_processed': len(documents),
                'collection_name': collection_name
            }
            
        except Exception as e:
            logger.error(f"Error upserting documents to Pinecone: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
    async def query_similar(self, query: str, collection_name: str, top_k: int = 5) -> List[Dict]:
        """Query similar documents from Pinecone with optimized performance."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            # Generate embedding for query
            query_embeddings = await self.get_embeddings([query])
            query_vector = query_embeddings[0]
            
            # Query Pinecone with optimized settings
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                include_values=False,  # Don't include vectors in response for performance
                filter={"collection_name": {"$eq": collection_name}}
            )
            
            # Format results
            similar_docs = []
            if hasattr(results, 'matches'):
                for match in results.matches:
                    similar_docs.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata,
                        'text': match.metadata.get('text', '')
                    })
            
            logger.info(f"Found {len(similar_docs)} similar documents for query")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            raise
    
    async def query_across_namespaces(self, query: str, namespaces: List[str], top_k: int = 10) -> List[Dict]:
        """Query across multiple namespaces and merge results (v7.x feature)."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            # Generate embedding for query
            query_embeddings = await self.get_embeddings([query])
            query_vector = query_embeddings[0]
            
            # Use query_namespaces utility for cross-namespace search
            combined_results = self.index.query_namespaces(
                vector=query_vector,
                namespaces=namespaces,
                top_k=top_k,
                include_metadata=True,
                include_values=False,
                show_progress=False
            )
            
            # Format results
            similar_docs = []
            if hasattr(combined_results, 'matches'):
                for match in combined_results.matches:
                    similar_docs.append({
                        'id': match.id,
                        'score': match.score,
                        'metadata': match.metadata,
                        'text': match.metadata.get('text', ''),
                        'namespace': match.metadata.get('collection_name', '')
                    })
            
            logger.info(f"Found {len(similar_docs)} similar documents across {len(namespaces)} namespaces")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error querying across namespaces: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> Dict:
        """Delete all documents from a collection using optimized queries."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            # Query to get all documents in collection with optimized settings
            dummy_vector = [0.0] * self.dimension  # Use float values
            results = self.index.query(
                vector=dummy_vector,
                top_k=10000,  # Large number to get all
                include_metadata=True,
                include_values=False,
                filter={"collection_name": {"$eq": collection_name}}
            )
            
            # Delete documents
            if hasattr(results, 'matches') and results.matches:
                ids_to_delete = [match.id for match in results.matches]
                self.index.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents from collection: {collection_name}")
            
            return {
                'status': 'success',
                'deleted_count': len(results.matches) if hasattr(results, 'matches') and results.matches else 0,
                'collection_name': collection_name
            }
            
        except Exception as e:
            logger.error(f"Error deleting collection from Pinecone: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: str) -> Dict:
        """Get statistics for a collection with optimized queries."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            dummy_vector = [0.0] * self.dimension  # Use float values
            results = self.index.query(
                vector=dummy_vector,
                top_k=10000,  # Large number to get all
                include_metadata=True,
                include_values=False,
                filter={"collection_name": {"$eq": collection_name}}
            )
            
            file_counts = {}
            if hasattr(results, 'matches'):
                for match in results.matches:
                    filename = match.metadata.get('filename', 'unknown')
                    file_counts[filename] = file_counts.get(filename, 0) + 1
            
            return {
                'total_documents': len(results.matches) if hasattr(results, 'matches') else 0,
                'files': file_counts,
                'collection_name': collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats from Pinecone: {e}")
            raise
    
    async def list_collections(self) -> List[str]:
        """List all collections in the index with optimized queries."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            # Get all unique collection names
            dummy_vector = [0.0] * self.dimension  # Use float values
            results = self.index.query(
                vector=dummy_vector,
                top_k=10000,  # Large number to get all
                include_metadata=True,
                include_values=False
            )
            
            collections = set()
            if hasattr(results, 'matches'):
                for match in results.matches:
                    collection_name = match.metadata.get('collection_name', '')
                    if collection_name:
                        collections.add(collection_name)
            
            return list(collections)
            
        except Exception as e:
            logger.error(f"Error listing collections from Pinecone: {e}")
            raise
    
    def get_index_stats(self) -> Dict:
        """Get index statistics with detailed information."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces,
                'index_name': self.index_name
            }
        except Exception as e:
            logger.error(f"Error getting index stats from Pinecone: {e}")
            raise
    
    async def upsert_from_dataframe(self, dataframe, collection_name: str) -> Dict:
        """Upsert data from a dataframe using Pinecone's optimized method."""
        try:
            if not self.index:
                raise RuntimeError("Pinecone index not initialized")
                
            # Add collection_name to dataframe metadata
            dataframe['collection_name'] = collection_name
            
            # Use Pinecone's optimized upsert_from_dataframe method
            self.index.upsert_from_dataframe(dataframe)
            
            logger.info(f"Successfully upserted dataframe to Pinecone collection: {collection_name}")
            return {
                'status': 'success',
                'collection_name': collection_name,
                'method': 'dataframe_upsert'
            }
            
        except Exception as e:
            logger.error(f"Error upserting dataframe to Pinecone: {e}")
            raise

# Global Pinecone service instance
pinecone_service = PineconeService() 