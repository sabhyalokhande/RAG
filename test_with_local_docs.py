#!/usr/bin/env python3
"""
Test RAG system with local documents
"""
import requests
import json
import time

def test_with_local_documents():
    """Test the RAG system with local documents."""
    base_url = "http://127.0.0.1:5001"
    
    # Test questions for different document types
    test_cases = [
        {
            "documents": "temp/sample documents/indian_constitution.pdf",
            "questions": [
                "When was the Indian Constitution adopted?",
                "What are fundamental rights?",
                "What is the structure of the Indian government?"
            ]
        },
        {
            "documents": "temp/sample documents/Arogya Sanjeevani Policy - CIN - U10200WB1906GOI001713 1.pdf",
            "questions": [
                "What is the grace period for premium payment?",
                "What is the waiting period for pre-existing diseases?",
                "Does the policy cover maternity expenses?"
            ]
        }
    ]
    
    print("Testing RAG System with Local Documents")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['documents']}")
        print("-" * 50)
        
        # Test the /hackrx/run endpoint
        payload = {
            "documents": test_case["documents"],
            "questions": test_case["questions"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/hackrx/run", json=payload)
            end_time = time.time()
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                print("Answers:")
                for j, answer in enumerate(result.get('answers', []), 1):
                    print(f"  {j}. {answer}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_with_local_documents() 