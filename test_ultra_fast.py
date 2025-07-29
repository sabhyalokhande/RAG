#!/usr/bin/env python3
"""
Test ultra-fast optimizations for hackathon performance
"""
import requests
import json
import time

def test_ultra_fast():
    """Test the ultra-optimized RAG system for maximum speed."""
    print("🚀 Testing Ultra-Fast Optimizations")
    print("=" * 50)
    
    # Test data
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D",
        "questions": [
            "What is the main topic of this document?",
            "What are the key benefits mentioned?",
            "What are the eligibility criteria?"
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
            timeout=60  # Increased timeout for large documents
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"⏱️ Total Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Ultra-fast optimization working!")
            print(f"📝 Final Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"\n  Q{i+1}: {test_data['questions'][i]}")
                print(f"  A{i+1}: {answer}")
                print("-" * 50)
            
            # Performance analysis
            if response_time < 10:
                print(f"\n🎉 EXCELLENT: Response time {response_time:.2f}s under 10 seconds!")
            elif response_time < 20:
                print(f"\n✅ GOOD: Response time {response_time:.2f}s under 20 seconds!")
            elif response_time < 30:
                print(f"\n⚠️ ACCEPTABLE: Response time {response_time:.2f}s under 30 seconds!")
            else:
                print(f"\n❌ SLOW: Response time {response_time:.2f}s over 30 seconds!")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_ultra_fast() 