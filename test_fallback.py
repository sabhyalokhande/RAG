#!/usr/bin/env python3
"""
Test script to verify fallback mechanisms work without Azure OpenAI
"""
import sys
import os
sys.path.append('.')

from app.services.openai_services import simple_similarity_search, generate_simple_answer

def test_fallback_mechanisms():
    """Test the fallback mechanisms without Azure OpenAI."""
    print("Testing Fallback Mechanisms")
    print("=" * 50)
    
    # Test documents
    test_documents = [
        "The Indian Constitution was adopted on 26 November 1949 and came into effect on 26 January 1950.",
        "The Constitution of India is the supreme law of India. It lays down the framework defining fundamental political principles.",
        "The Constitution establishes the structure, procedures, powers and duties of government institutions.",
        "Fundamental Rights are guaranteed by the Constitution to all citizens of India.",
        "The Constitution provides for a federal system of government with a strong central government."
    ]
    
    # Test queries
    test_queries = [
        "When was the Indian Constitution adopted?",
        "What are fundamental rights?",
        "What type of government does India have?",
        "What is the supreme law of India?"
    ]
    
    print("Test Documents:")
    for i, doc in enumerate(test_documents, 1):
        print(f"{i}. {doc}")
    
    print("\nTest Results:")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Test simple similarity search
        relevant_docs = simple_similarity_search(query, test_documents, top_k=3)
        print(f"Relevant documents found: {len(relevant_docs)}")
        
        # Test simple answer generation
        mock_relevant_docs = {
            'documents': [relevant_docs] if relevant_docs else [[]]
        }
        
        answer = generate_simple_answer(query, mock_relevant_docs)
        print(f"Generated answer: {answer}")

if __name__ == "__main__":
    test_fallback_mechanisms() 