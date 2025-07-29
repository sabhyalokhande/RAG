#!/usr/bin/env python3
"""
Test the Postman fix (removed authentication)
"""
import requests
import json

def test_postman_fix():
    """Test if the authentication removal fixes the 400 error."""
    print("🧪 Testing Postman Fix (No Authentication)")
    print("=" * 50)
    
    # Test data (same as what you'd send in Postman)
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the main topic of this document?",
            "What are the key features mentioned?",
            "What are the benefits covered?"
        ]
    }
    
    try:
        print("📤 Sending request to /hackrx/run (no auth)...")
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Authentication fix worked!")
            print(f"📝 Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"  Q{i+1}: {test_data['questions'][i]}")
                print(f"  A{i+1}: {answer}")
                print()
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_postman_fix() 