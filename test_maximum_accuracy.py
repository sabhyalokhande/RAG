import requests
import json
import time

# Test with Newton's Principia to verify maximum accuracy improvements
test_data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/principia_newton.pdf?sv=2023-01-03&st=2025-07-28T07%3A20%3A32Z&se=2026-07-29T07%3A20%3A00Z&sr=b&sp=r&sig=V5I1QYyigoxeUMbnUKsdEaST99F5%2FDfo7wpKg9XXF5w%3D",
    "questions": [
        "What is Newton's First Law of Motion?",
        "Explain the concept of inertia.",
        "What is the Law of Universal Gravitation?",
        "How does Newton describe force?",
        "What are the three laws of motion?",
        "What is Newton's Second Law?",
        "What is Newton's Third Law?",
        "How does Newton define mass?",
        "What is the relationship between force and acceleration?",
        "How does Newton describe the motion of bodies?"
    ]
}

def test_maximum_accuracy():
    """Test the maximum accuracy improvements with the enhanced RAG system"""
    
    print("🎯 TESTING MAXIMUM ACCURACY IMPROVEMENTS")
    print("="*80)
    print("📊 MAXIMUM ACCURACY Configuration Changes:")
    print("✅ Chunk size: 2500 characters (increased from 1500)")
    print("✅ Chunk overlap: 600 characters (increased from 400)")
    print("✅ Retrieval count: 40 documents (increased from 25)")
    print("✅ Temperature: 0.05 (reduced from 0.1 for consistency)")
    print("✅ Quality filtering: Extremely lenient (5 char minimum)")
    print("✅ Token limits: 256,000 tokens (increased from 128,000)")
    print("✅ Processing time: 180 seconds maximum (increased from 120)")
    print("✅ Context limit: 4000 characters (increased from 2000)")
    print("✅ Enhanced RAG prompt with 24 accuracy guidelines")
    print("="*80)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(8)
    
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
    print("🚀 TESTING MAXIMUM ACCURACY RAG SYSTEM")
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
            
            # Comprehensive accuracy analysis
            print("\n" + "="*80)
            print("📈 COMPREHENSIVE ACCURACY ANALYSIS")
            print("="*80)
            
            if 'answers' in result:
                answers = result['answers']
                total_questions = len(answers)
                informative_answers = 0
                detailed_answers = 0
                specific_answers = 0
                
                print(f"\n📊 Analyzing {total_questions} answers...")
                
                for i, answer in enumerate(answers):
                    question = test_data['questions'][i]
                    answer_text = answer.get('answer', '')
                    
                    # Check if answer is informative (not just "no information found")
                    is_informative = answer_text and not any(phrase in answer_text.lower() for phrase in [
                        'the provided documents do not contain information',
                        'no information provided',
                        'not mentioned in the context',
                        'does not contain information'
                    ])
                    
                    # Check if answer is detailed (more than 100 characters)
                    is_detailed = len(answer_text) > 100
                    
                    # Check if answer contains specific details (numbers, formulas, etc.)
                    has_specifics = any(indicator in answer_text.lower() for indicator in [
                        'according to', 'the law states', 'specifically', 'exactly', 'precisely',
                        'force equals', 'mass times', 'acceleration', 'inertia', 'gravitation'
                    ])
                    
                    if is_informative:
                        informative_answers += 1
                        print(f"✅ Q{i+1}: Informative answer found")
                    else:
                        print(f"❌ Q{i+1}: No relevant information found")
                    
                    if is_detailed:
                        detailed_answers += 1
                        print(f"📝 Q{i+1}: Detailed answer ({len(answer_text)} chars)")
                    
                    if has_specifics:
                        specific_answers += 1
                        print(f"🎯 Q{i+1}: Contains specific details")
                    
                    # Show sample of answer
                    if answer_text:
                        sample = answer_text[:150] + "..." if len(answer_text) > 150 else answer_text
                        print(f"   Sample: {sample}")
                
                # Calculate accuracy metrics
                accuracy_percentage = (informative_answers / total_questions) * 100
                detail_percentage = (detailed_answers / total_questions) * 100
                specificity_percentage = (specific_answers / total_questions) * 100
                
                print(f"\n📊 ACCURACY METRICS:")
                print(f"   Informative Answers: {accuracy_percentage:.1f}% ({informative_answers}/{total_questions})")
                print(f"   Detailed Answers: {detail_percentage:.1f}% ({detailed_answers}/{total_questions})")
                print(f"   Specific Answers: {specificity_percentage:.1f}% ({specific_answers}/{total_questions})")
                
                # Overall assessment
                if accuracy_percentage > 70:
                    print("🎉 EXCELLENT ACCURACY ACHIEVED!")
                elif accuracy_percentage > 50:
                    print("📈 SIGNIFICANT IMPROVEMENT DETECTED!")
                elif accuracy_percentage > 30:
                    print("📊 MODERATE IMPROVEMENT DETECTED!")
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
    test_maximum_accuracy() 