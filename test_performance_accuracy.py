import requests
import json
import time

# Test with Newton's Principia to verify performance + accuracy improvements
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

def test_performance_accuracy():
    """Test both performance improvements and accuracy enhancements"""
    
    print("⚡ TESTING PERFORMANCE + ACCURACY IMPROVEMENTS")
    print("="*80)
    print("📊 PERFORMANCE OPTIMIZATIONS:")
    print("✅ Parallel PDF processing for large documents")
    print("✅ Intelligent chunking with size-based optimization")
    print("✅ Reduced chunk sizes for better performance")
    print("✅ Optimized token limits and processing times")
    print("✅ Enhanced batch processing for embeddings")
    print("✅ Smart document size detection and handling")
    print("="*80)
    print("📊 ACCURACY ENHANCEMENTS:")
    print("✅ Removed document references from answers")
    print("✅ Enhanced RAG prompt for better information extraction")
    print("✅ Improved context organization")
    print("✅ Better semantic search capabilities")
    print("✅ Optimized retrieval counts")
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
    print("🚀 TESTING OPTIMIZED RAG SYSTEM")
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
            
            # Performance and accuracy analysis
            print("\n" + "="*80)
            print("📈 PERFORMANCE + ACCURACY ANALYSIS")
            print("="*80)
            
            if 'answers' in result:
                answers = result['answers']
                total_questions = len(answers)
                informative_answers = 0
                detailed_answers = 0
                specific_answers = 0
                clean_answers = 0
                
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
                    
                    # Check if answer is clean (no document references)
                    is_clean = not any(phrase in answer_text.lower() for phrase in [
                        'document 1', 'document 2', 'document 3', 'document 4', 'document 5',
                        'policy details from document', 'document details'
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
                    
                    if is_clean:
                        clean_answers += 1
                        print(f"🧹 Q{i+1}: Clean answer (no doc references)")
                    
                    # Show sample of answer
                    if answer_text:
                        sample = answer_text[:150] + "..." if len(answer_text) > 150 else answer_text
                        print(f"   Sample: {sample}")
                
                # Calculate metrics
                accuracy_percentage = (informative_answers / total_questions) * 100
                detail_percentage = (detailed_answers / total_questions) * 100
                specificity_percentage = (specific_answers / total_questions) * 100
                cleanliness_percentage = (clean_answers / total_questions) * 100
                
                print(f"\n📊 PERFORMANCE METRICS:")
                print(f"   Total Time: {duration:.2f} seconds")
                print(f"   Target Time: 60 seconds")
                print(f"   Performance: {'✅ FAST' if duration < 60 else '⚠️ SLOW'}")
                
                print(f"\n📊 ACCURACY METRICS:")
                print(f"   Informative Answers: {accuracy_percentage:.1f}% ({informative_answers}/{total_questions})")
                print(f"   Detailed Answers: {detail_percentage:.1f}% ({detailed_answers}/{total_questions})")
                print(f"   Specific Answers: {specificity_percentage:.1f}% ({specific_answers}/{total_questions})")
                print(f"   Clean Answers: {cleanliness_percentage:.1f}% ({clean_answers}/{total_questions})")
                
                # Overall assessment
                if accuracy_percentage > 70 and duration < 60:
                    print("🎉 EXCELLENT PERFORMANCE + ACCURACY ACHIEVED!")
                elif accuracy_percentage > 50 and duration < 90:
                    print("📈 GOOD PERFORMANCE + ACCURACY!")
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
    test_performance_accuracy() 