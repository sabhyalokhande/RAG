#!/usr/bin/env python3
"""
Debug the 400 error in Postman
"""
import requests
import json

def debug_postman_400():
    """Debug what's causing the 400 error in Postman."""
    print("🔍 Debugging Postman 400 Error")
    print("=" * 40)
    
    # Test different scenarios
    
    # Test 1: No Authorization header
    print("\n📋 Test 1: No Authorization header")
    test_data_1 = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": ["What is this document about?"]
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data_1,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With Authorization header
    print("\n📋 Test 2: With Authorization header")
    test_data_2 = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": ["What is this document about?"]
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data_2,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-api-key"
            },
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Invalid JSON
    print("\n📋 Test 3: Invalid JSON")
    try:
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Missing documents field
    print("\n📋 Test 4: Missing documents field")
    test_data_4 = {
        "questions": ["What is this document about?"]
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data_4,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Missing questions field
    print("\n📋 Test 5: Missing questions field")
    test_data_5 = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/run",
            json=test_data_5,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_postman_400() 