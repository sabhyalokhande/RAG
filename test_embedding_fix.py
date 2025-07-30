#!/usr/bin/env python3
"""
Test embedding dimension fix for text-embedding-3-small
"""
import requests
import json
import time

def test_embedding_fix():
    """Test the embedding dimension fix for text-embedding-3-small."""
    print("🔧 Testing Embedding Dimension Fix")
    print("=" * 50)
    
    # Test data
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the main topic?",
            "What are the key benefits?"
        ]
    }
    
    try:
        print("📤 Sending request to /hackrx/run...")
        print("⏱️ Starting timer...")
        start_time = time.time()
        
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-api-key"
            },
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"⏱️ Total Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Embedding dimension fix working!")
            print(f"📝 Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"  Q{i+1}: {test_data['questions'][i]}")
                print(f"  A{i+1}: {answer[:200]}...")
                print()
            
            # Performance analysis
            if response_time < 15:
                print("🎉 EXCELLENT: Response time under 15 seconds!")
            elif response_time < 25:
                print("✅ GOOD: Response time under 25 seconds!")
            elif response_time < 30:
                print("⚠️ ACCEPTABLE: Response time under 30 seconds!")
            else:
                print("❌ SLOW: Response time over 30 seconds!")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_embedding_fix() 