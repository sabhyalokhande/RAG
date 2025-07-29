#!/usr/bin/env python3
"""
Test script for HackRx RAG system
"""

import requests
import json
import time

def test_hackrx_endpoint():
    """Test the HackRx endpoint with sample data."""
    
    # Test URL (replace with your actual endpoint)
    base_url = "http://localhost:5001"
    
    # Sample test data
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?",
            "What is the waiting period for pre-existing diseases?",
            "Does the policy cover maternity expenses?",
            "What is the waiting period for cataract surgery?"
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key"
    }
    
    print("Testing HackRx endpoint...")
    print(f"URL: {base_url}/hackrx/run")
    print(f"Questions: {test_data['questions']}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/hackrx/run",
            json=test_data,
            headers=headers,
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("Answers:")
            for i, answer in enumerate(result.get('answers', []), 1):
                print(f"{i}. {answer}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def test_health_endpoint():
    """Test the health endpoint."""
    
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("System is healthy!")
        else:
            print(f"Health check failed: {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    print("HackRx RAG System Test")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_endpoint()
    print()
    
    # Test main endpoint
    test_hackrx_endpoint() 