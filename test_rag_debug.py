#!/usr/bin/env python3
"""
Test script to debug RAG system with image processing
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_with_image():
    """Test the RAG system with the image containing mathematical expressions."""
    
    url = "http://localhost:5001/hackrx/run"
    
    payload = {
        "documents": "https://hackrx.blob.core.windows.net/assets/Test%20/image.jpeg?sv=2023-01-03&spr=https&st=2025-08-04T19%3A29%3A01Z&se=2026-08-05T19%3A29%3A00Z&sr=b&sp=r&sig=YnJJThygjCT6%2FpNtY1aHJEZ%2F%2BqHoEB59TRGPSxJJBwo%3D",
        "questions": [
            "What is 100+23?",  # This is in the image as "100+23=10023"
            "What is 9+5?",     # This is in the image as "Q9+5= 22" (OCR error)
        ]    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key"
    }
    
    print("="*80)
    print("TESTING RAG SYSTEM WITH IMAGE")
    print("="*80)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "="*80)
            print("SUCCESS - RAG RESPONSE")
            print("="*80)
            print(json.dumps(result, indent=2))
            
            # Analyze answers
            print("\n" + "="*80)
            print("ANSWER ANALYSIS")
            print("="*80)
            
            answers = result.get('answers', [])
            questions = payload['questions']
            
            for i, (question, answer) in enumerate(zip(questions, answers)):
                print(f"\nQ{i+1}: {question}")
                print(f"A{i+1}: {answer}")
                
                # Check if answer references document content
                if "document" in answer.lower():
                    if "does not" in answer.lower() or "cannot" in answer.lower():
                        print(f"   ❌ ISSUE: Claims document doesn't contain info")
                    else:
                        print(f"   ✅ GOOD: References document content")
                else:
                    print(f"   ⚠️  WARNING: Doesn't mention document")
                    
        else:
            print(f"\n❌ ERROR - Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_rag_with_image()
