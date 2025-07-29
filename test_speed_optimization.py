#!/usr/bin/env python3
"""
Test speed optimizations for hackathon performance
"""
import requests
import json
import time

def test_speed_optimization():
    """Test the aggressively optimized RAG system for speed."""
    print("🚀 Testing Aggressive Speed Optimizations")
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
        start_time = time.time()
        
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-api-key"
            },
            timeout=60  # Increased timeout for large documents
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"⏱️ Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Speed optimization working!")
            print(f"📝 Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"  Q{i+1}: {test_data['questions'][i]}")
                print(f"  A{i+1}: {answer[:200]}...")  # Show first 200 chars
                print()
            
            # Performance analysis
            if response_time < 15:
                print("🎉 EXCELLENT: Response time under 15 seconds!")
            elif response_time < 25:
                print("✅ GOOD: Response time under 25 seconds!")
            elif response_time < 30:
                print("⚠️ ACCEPTABLE: Response time under 30 seconds!")
            else:
                print("❌ SLOW: Response time over 30 seconds - needs more optimization")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_speed_optimization() 