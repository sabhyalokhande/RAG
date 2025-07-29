#!/usr/bin/env python3
"""
Comprehensive Azure OpenAI Status Checker
"""
import requests
import json
import os

def check_azure_openai_status():
    """Check the status of Azure OpenAI resources."""
    print("🔍 Azure OpenAI Status Check")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    
    print(f"API Key: {'✅ Set' if api_key else '❌ Not Set'}")
    print(f"Endpoint: {'✅ Set' if endpoint else '❌ Not Set'}")
    
    if not api_key or not endpoint:
        print("\n❌ Environment variables not set!")
        print("Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        return
    
    # Test different endpoints
    endpoints_to_test = [
        "https://botwot-opanai.openai.azure.com",
        "https://wacha-mc7zfgir-eastus2.openai.azure.com",
        endpoint  # Use the one from environment
    ]
    
    api_version = "2023-06-01-preview"
    
    for test_endpoint in endpoints_to_test:
        print(f"\n🔍 Testing endpoint: {test_endpoint}")
        
        # Test 1: Check deployments
        try:
            url = f"{test_endpoint}/openai/deployments?api-version={api_version}"
            headers = {"api-key": api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Deployments Status: {response.status_code}")
            
            if response.status_code == 200:
                deployments = response.json()
                print(f"  ✅ Found {len(deployments.get('data', []))} deployments")
                for deployment in deployments.get('data', []):
                    print(f"    - {deployment.get('id', 'Unknown')}")
            else:
                print(f"  ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Test 2: Check embeddings endpoint
        try:
            url = f"{test_endpoint}/openai/deployments/text-embedding-ada-002/embeddings?api-version={api_version}"
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            data = {"input": ["test"]}
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"  Embeddings Status: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ Embeddings endpoint working")
            else:
                print(f"  ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    check_azure_openai_status() 