#!/usr/bin/env python3
"""
Test script to check environment variable loading
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔧 ENVIRONMENT VARIABLE CHECK:")
print("="*80)

# Check Azure OpenAI variables
azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_embedding = os.environ.get("AZURE_DEPLOYMENT_EMBEDDING")
azure_completion = os.environ.get("AZURE_DEPLOYMENT_COMPLETION")

print(f"AZURE_OPENAI_API_KEY: {'✅ Set' if azure_api_key else '❌ Missing'}")
print(f"AZURE_OPENAI_ENDPOINT: {'✅ Set' if azure_endpoint else '❌ Missing'}")
print(f"AZURE_DEPLOYMENT_EMBEDDING: {azure_embedding}")
print(f"AZURE_DEPLOYMENT_COMPLETION: {azure_completion}")

# Check Pinecone variables
pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pinecone_environment = os.environ.get("PINECONE_ENVIRONMENT")
pinecone_index = os.environ.get("PINECONE_INDEX_NAME")

print(f"PINECONE_API_KEY: {'✅ Set' if pinecone_api_key else '❌ Missing'}")
print(f"PINECONE_ENVIRONMENT: {'✅ Set' if pinecone_environment else '❌ Missing'}")
print(f"PINECONE_INDEX_NAME: {pinecone_index}")

print("="*80)

# Test config import
try:
    from config import Config
    print("✅ Config imported successfully")
    print(f"Config.AZURE_DEPLOYMENT_EMBEDDING: {Config.AZURE_DEPLOYMENT_EMBEDDING}")
    print(f"Config.AZURE_DEPLOYMENT_COMPLETION: {Config.AZURE_DEPLOYMENT_COMPLETION}")
except Exception as e:
    print(f"❌ Error importing config: {e}")

print("="*80) 