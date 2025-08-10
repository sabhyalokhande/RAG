"""
Pinecone v7.x Example Implementation
This file demonstrates the correct usage of Pinecone v7.x SDK with text-embedding-3-large
"""

import os
import asyncio
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pinecone v7.x imports
try:
    from pinecone import Pinecone, ServerlessSpec
    from pinecone.grpc import PineconeGRPC
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone not available. Install with: pip install 'pinecone[grpc]>=7.0.0'")

# Azure OpenAI for embeddings
from openai import AsyncAzureOpenAI

class PineconeExample:
    """Example Pinecone v7.x implementation with proper API usage and text-embedding-3-large."""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = "example-index"
        self.dimension = 3072  # Updated for text-embedding-3-large
        self.metric = "cosine"
        
    def initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        if not PINECONE_AVAILABLE:
            print("Pinecone not available")
            return False
            
        try:
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                print("PINECONE_API_KEY not set")
                return False
            
            # Initialize Pinecone with gRPC support
            self.pc = PineconeGRPC(api_key=api_key)
            
            # Check if index exists, create if not
            if self.index_name not in self.pc.list_indexes().names():
                print(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    ),
                    deletion_protection="disabled"
                )
                print("Waiting for index to be ready...")
                import time
                time.sleep(10)
            
            # Connect to index
            self.index = self.pc.Index(
                name=self.index_name,
                pool_threads=50
            )
            print(f"Successfully connected to Pinecone index: {self.index_name}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
            return False
    
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
            
            # Process in batches
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await client.embeddings.create(
                    input=batch,
                    model=deployment
                )
                batch_embeddings = [embedding.embedding for embedding in response.data]
                all_embeddings.extend(batch_embeddings)
                
            return all_embeddings
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise
    
    async def upsert_example(self):
        """Example of upserting documents to Pinecone."""
        if not self.index:
            print("Index not initialized")
            return
        
        try:
            # Sample documents
            documents = [
                {"text": "This is a sample document about artificial intelligence.", "id": "doc1"},
                {"text": "Machine learning is a subset of AI.", "id": "doc2"},
                {"text": "Deep learning uses neural networks.", "id": "doc3"}
            ]
            
            # Generate embeddings
            texts = [doc["text"] for doc in documents]
            embeddings = await self.get_embeddings(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, doc in enumerate(documents):
                vectors.append({
                    'id': doc['id'],
                    'values': embeddings[i],
                    'metadata': {
                        'text': doc['text'],
                        'source': 'example'
                    }
                })
            
            # Upsert to Pinecone
            self.index.upsert(vectors=vectors)
            print(f"Successfully upserted {len(documents)} documents")
            
        except Exception as e:
            print(f"Error upserting documents: {e}")
    
    async def query_example(self):
        """Example of querying documents from Pinecone."""
        if not self.index:
            print("Index not initialized")
            return
        
        try:
            # Query text
            query_text = "What is artificial intelligence?"
            
            # Generate embedding for query
            query_embeddings = await self.get_embeddings([query_text])
            query_vector = query_embeddings[0]
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=3,
                include_metadata=True,
                include_values=False
            )
            
            # Process results
            print(f"Query: {query_text}")
            print("Results:")
            if hasattr(results, 'matches'):
                for i, match in enumerate(results.matches):
                    print(f"{i+1}. Score: {match.score:.4f}")
                    print(f"   Text: {match.metadata.get('text', 'N/A')}")
                    print()
            
        except Exception as e:
            print(f"Error querying documents: {e}")
    
    def get_stats(self):
        """Get index statistics."""
        if not self.index:
            print("Index not initialized")
            return
        
        try:
            stats = self.index.describe_index_stats()
            print(f"Index: {self.index_name}")
            print(f"Total vectors: {stats.total_vector_count}")
            print(f"Dimension: {stats.dimension}")
            print(f"Index fullness: {stats.index_fullness}")
            
        except Exception as e:
            print(f"Error getting stats: {e}")

async def main():
    """Main function to demonstrate Pinecone v7.x usage with text-embedding-3-large."""
    example = PineconeExample()
    
    # Initialize Pinecone
    if example.initialize_pinecone():
        print("Pinecone initialized successfully")
        
        # Get initial stats
        example.get_stats()
        
        # Upsert example documents
        await example.upsert_example()
        
        # Query example
        await example.query_example()
        
        # Get final stats
        example.get_stats()
    else:
        print("Failed to initialize Pinecone")

if __name__ == "__main__":
    asyncio.run(main()) 