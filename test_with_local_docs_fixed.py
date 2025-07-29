#!/usr/bin/env python3
"""
Test RAG system with local documents using the fixed collection
"""
import requests
import json
import time
import os

def test_local_rag_fixed():
    """Test the RAG system with local documents using the new collection."""
    print("🧪 Testing RAG System with Local Documents (Fixed Collection)")
    print("=" * 60)
    
    # Test with one of your sample documents
    test_document = "temp/sample documents/Arogya Sanjeevani Policy - CIN - U10200WB1906GOI001713 1.pdf"
    
    if not os.path.exists(test_document):
        print(f"❌ Document not found: {test_document}")
        return
    
    print(f"📄 Testing with document: {test_document}")
    
    # Read the document
    with open(test_document, 'rb') as f:
        document_content = f.read()
    
    # Test questions
    questions = [
        "What is the main purpose of this policy?",
        "What are the key benefits covered?",
        "What is the sum insured amount?"
    ]
    
    # Test data
    test_data = {
        "questions": questions
    }
    
    try:
        print("📤 Sending request to /hackrx/test-process...")
        response = requests.post(
            "http://127.0.0.1:5001/hackrx/test-process",
            data={"questions": json.dumps(questions)},
            files={"document": ("test.pdf", document_content, "application/pdf")},
            timeout=120
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! RAG system working with new collection!")
            print(f"📝 Answers:")
            for i, answer in enumerate(result.get('answers', [])):
                print(f"  Q{i+1}: {questions[i]}")
                print(f"  A{i+1}: {answer}")
                print()
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_local_rag_fixed() 