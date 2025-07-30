#!/usr/bin/env python3
"""
Test fallback mechanism debug
"""
import requests
import json
import time

def test_fallback_debug():
    """Test the fallback mechanism to see what's happening."""
    print("🔍 Testing Fallback Debug")
    print("=" * 50)
    
    # Test data with specific questions
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?",
            "What is the waiting period for pre-existing diseases?"
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
            print("\n✅ Success! Fallback working!")
            print(f"📝 Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"\n  Q{i+1}: {test_data['questions'][i]}")
                print(f"  A{i+1}: {answer}")
                print("-" * 50)
            
            # Check if answers are meaningful
            meaningful_answers = 0
            for answer in result.get('answers', []):
                if len(answer) > 50 and not answer.startswith("Premises No.") and not answer.startswith("National Insurance Co."):
                    meaningful_answers += 1
            
            print(f"\n📊 Analysis:")
            print(f"  Total Answers: {len(result.get('answers', []))}")
            print(f"  Meaningful Answers: {meaningful_answers}")
            print(f"  Success Rate: {(meaningful_answers/len(result.get('answers', [])))*100:.1f}%")
            
            if meaningful_answers == len(result.get('answers', [])):
                print("🎉 EXCELLENT: All answers are meaningful!")
            elif meaningful_answers > 0:
                print("⚠️ PARTIAL: Some answers are meaningful")
            else:
                print("❌ POOR: No meaningful answers")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_fallback_debug() 