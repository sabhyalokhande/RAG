#!/usr/bin/env python3
"""
Test the collection fix
"""
import requests
import json

def test_collection_fix():
    """Test if the new collection name fixes the dimension issue."""
    print("🧪 Testing Collection Fix")
    print("=" * 40)
    
    # Test data
    test_data = {
        "documents_url": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the main topic of this document?",
            "What are the key features mentioned?"
        ]
    }
    
    try:
        print("📤 Sending request to /hackrx/run...")
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data,
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Collection fix worked!")
            print(f"📝 Answers: {result.get('answers', [])}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_collection_fix() 