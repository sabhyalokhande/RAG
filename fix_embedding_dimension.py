#!/usr/bin/env python3
"""
Fix embedding dimension mismatch in ChromaDB
"""
import os
import shutil
import chromadb
from chromadb.config import Settings

def fix_embedding_dimension():
    """Fix the embedding dimension mismatch by recreating the collection."""
    print("🔧 Fixing Embedding Dimension Mismatch")
    print("=" * 50)
    
    # ChromaDB path
    chroma_path = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    
    print(f"ChromaDB path: {chroma_path}")
    
    # Check if ChromaDB directory exists
    if os.path.exists(chroma_path):
        print(f"✅ Found existing ChromaDB at: {chroma_path}")
        
        # Backup the existing database
        backup_path = f"{chroma_path}_backup"
        if not os.path.exists(backup_path):
            print(f"📦 Creating backup at: {backup_path}")
            shutil.copytree(chroma_path, backup_path)
            print("✅ Backup created successfully")
        else:
            print(f"📦 Backup already exists at: {backup_path}")
        
        # Remove the existing ChromaDB
        print(f"🗑️ Removing existing ChromaDB: {chroma_path}")
        shutil.rmtree(chroma_path)
        print("✅ Existing ChromaDB removed")
    else:
        print(f"ℹ️ No existing ChromaDB found at: {chroma_path}")
    
    # Create new ChromaDB client
    print("🔄 Creating new ChromaDB client...")
    client = chromadb.PersistentClient(
        path=chroma_path,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=chroma_path
        )
    )
    
    # Create a new collection
    collection_name = "hackrx_documents"
    print(f"📝 Creating new collection: {collection_name}")
    
    try:
        collection = client.create_collection(name=collection_name)
        print("✅ New collection created successfully")
        print("✅ Embedding dimension issue fixed!")
        print("\n🎉 Your RAG system is now ready with Azure OpenAI!")
        
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        print("🔄 Trying to get existing collection...")
        try:
            collection = client.get_collection(name=collection_name)
            print("✅ Collection retrieved successfully")
        except Exception as e2:
            print(f"❌ Error retrieving collection: {e2}")

if __name__ == "__main__":
    fix_embedding_dimension() 