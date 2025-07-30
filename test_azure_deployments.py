#!/usr/bin/env python3
"""
Test Azure OpenAI deployments
"""
import os
import openai
from openai import AzureOpenAI

def test_azure_deployments():
    """Test which Azure OpenAI deployments are available."""
    print("🔍 Testing Azure OpenAI Deployments")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    
    print(f"API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"Endpoint: {'✅ Set' if endpoint else '❌ Not set'}")
    
    if not api_key or not endpoint:
        print("\n❌ Missing environment variables!")
        print("Please set:")
        print("  AZURE_OPENAI_API_KEY")
        print("  AZURE_OPENAI_ENDPOINT")
        return
    
    try:
        # Initialize client
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-12-01-preview"
        )
        
        print("\n🔍 Testing Embedding Deployments:")
        
        # Test common embedding models
        embedding_models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large"
        ]
        
        for model in embedding_models:
            try:
                print(f"\nTesting {model}...")
                response = client.embeddings.create(
                    input=["test"],
                    model=model
                )
                print(f"✅ {model} - WORKING")
                print(f"   Dimensions: {len(response.data[0].embedding)}")
            except Exception as e:
                print(f"❌ {model} - FAILED: {str(e)}")
        
        print("\n🔍 Testing Completion Deployments:")
        
        # Test common completion models
        completion_models = [
            "gpt-4o-mini",
            "gpt-35-turbo",
            "gpt-4",
            "gpt-35-turbo-instruct"
        ]
        
        for model in completion_models:
            try:
                print(f"\nTesting {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                print(f"✅ {model} - WORKING")
            except Exception as e:
                print(f"❌ {model} - FAILED: {str(e)}")
                
    except Exception as e:
        print(f"\n❌ Error connecting to Azure OpenAI: {str(e)}")

if __name__ == "__main__":
    test_azure_deployments() 