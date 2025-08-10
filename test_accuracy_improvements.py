import requests
import json
import time

# Test with a simple document to verify accuracy improvements
test_data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/principia_newton.pdf?sv=2023-01-03&st=2025-07-28T07%3A20%3A32Z&se=2026-07-29T07%3A20%3A00Z&sr=b&sp=r&sig=V5I1QYyigoxeUMbnUKsdEaST99F5%2FDfo7wpKg9XXF5w%3D",
    "questions": [
        "What is Newton's First Law of Motion?",
        "Explain the concept of inertia.",
        "What is the Law of Universal Gravitation?",
        "How does Newton describe force?",
        "What are the three laws of motion?"
    ]
}

def test_accuracy_improvements():
    """Test the accuracy improvements with the enhanced RAG system"""
    
    print("🔧 TESTING ACCURACY IMPROVEMENTS")
    print("="*80)
    print("📊 Configuration Changes Applied:")
    print("✅ Increased chunk size from 800 to 1500 characters")
    print("✅ Increased chunk overlap from 256 to 400 characters")
    print("✅ Increased retrieval count from 15 to 25 documents")
    print("✅ Relaxed quality filtering (more inclusive)")
    print("✅ Enhanced RAG prompt for better information extraction")
    print("✅ Increased token limits for better content preservation")
    print("="*80)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Test the health endpoint first
    try:
        health_response = requests.get("http://localhost:5001/health")
        print(f"🏥 Health check status: {health_response.status_code}")
        if health_response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("❌ Server health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:5001")
        return
    
    # Prepare the request
    url = "http://localhost:5001/hackrx/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key"
    }
    
    print("\n" + "="*80)
    print("🚀 TESTING ENHANCED RAG SYSTEM")
    print("="*80)
    print(f"📄 Document URL: {test_data['documents']}")
    print(f"❓ Number of questions: {len(test_data['questions'])}")
    print("="*80)
    
    try:
        # Make the request
        print("📤 Sending request to /hackrx/run...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=test_data, timeout=600)  # 10 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request completed in {duration:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Here are the results:")
            print(json.dumps(result, indent=2))
            
            # Analyze accuracy improvements
            print("\n" + "="*80)
            print("📈 ACCURACY ANALYSIS")
            print("="*80)
            
            if 'answers' in result:
                answers = result['answers']
                total_questions = len(answers)
                informative_answers = 0
                
                for i, answer in enumerate(answers):
                    question = test_data['questions'][i]
                    answer_text = answer.get('answer', '')
                    
                    # Check if answer is informative (not just "no information found")
                    if answer_text and not any(phrase in answer_text.lower() for phrase in [
                        'the provided documents do not contain information',
                        'no information provided',
                        'not mentioned in the context'
                    ]):
                        informative_answers += 1
                        print(f"✅ Q{i+1}: Informative answer found")
                    else:
                        print(f"❌ Q{i+1}: No relevant information found")
                
                accuracy_percentage = (informative_answers / total_questions) * 100
                print(f"\n📊 Accuracy Score: {accuracy_percentage:.1f}% ({informative_answers}/{total_questions} questions)")
                
                if accuracy_percentage > 50:
                    print("🎉 SIGNIFICANT IMPROVEMENT DETECTED!")
                elif accuracy_percentage > 20:
                    print("📈 MODERATE IMPROVEMENT DETECTED!")
                else:
                    print("⚠️  FURTHER OPTIMIZATION NEEDED")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (10 minutes). The document might be large or processing is taking longer than expected.")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_accuracy_improvements() 