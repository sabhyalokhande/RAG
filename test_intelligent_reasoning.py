import requests
import json
import time

# Test with complex questions that require reasoning and understanding
test_data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the waiting period for cataract surgery?",
        "Are the medical expenses for an organ donor covered under this policy?",
        "What is the No Claim Discount (NCD) offered in this policy?",
        "Is there a benefit for preventive health check-ups?",
        "How does the policy define a 'Hospital'?",
        "What is the extent of coverage for AYUSH treatments?",
        "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
}

def test_intelligent_reasoning():
    """Test the intelligent reasoning capabilities with complex questions"""
    
    print("🧠 TESTING INTELLIGENT REASONING")
    print("="*80)
    print("📊 INTELLIGENT REASONING CAPABILITIES:")
    print("✅ Context understanding and logical reasoning")
    print("✅ Inference from related information")
    print("✅ Analysis of policy language and conditions")
    print("✅ Synthesis of information from multiple parts")
    print("✅ Interpretation of technical language")
    print("✅ Deductive and inductive reasoning")
    print("✅ Critical thinking and evaluation")
    print("✅ Comprehensive analysis and understanding")
    print("="*80)
    print("📊 REASONING FOCUS AREAS:")
    print("✅ Understanding document context")
    print("✅ Drawing logical conclusions")
    print("✅ Inferring answers from related information")
    print("✅ Analyzing policy implications")
    print("✅ Synthesizing complex information")
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
    print("🚀 TESTING INTELLIGENT REASONING RAG SYSTEM")
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
            
            # Intelligent reasoning analysis
            print("\n" + "="*80)
            print("🧠 INTELLIGENT REASONING ANALYSIS")
            print("="*80)
            
            if 'answers' in result:
                answers = result['answers']
                total_questions = len(answers)
                informative_answers = 0
                reasoned_answers = 0
                inferred_answers = 0
                analyzed_answers = 0
                comprehensive_answers = 0
                
                print(f"\n📊 Analyzing {total_questions} answers for intelligent reasoning...")
                
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
                    
                    # Check if answer shows reasoning (contains analysis words)
                    shows_reasoning = any(indicator in answer_text.lower() for indicator in [
                        'based on', 'according to', 'this means', 'therefore', 'thus',
                        'implies', 'indicates', 'suggests', 'shows', 'demonstrates',
                        'analysis', 'interpretation', 'understanding', 'reasoning'
                    ])
                    
                    # Check if answer shows inference (drawing conclusions)
                    shows_inference = any(indicator in answer_text.lower() for indicator in [
                        'can be inferred', 'this suggests', 'it follows', 'consequently',
                        'as a result', 'therefore', 'thus', 'hence', 'so',
                        'based on this', 'from this', 'we can conclude'
                    ])
                    
                    # Check if answer shows analysis (detailed examination)
                    shows_analysis = any(indicator in answer_text.lower() for indicator in [
                        'analysis', 'examination', 'review', 'assessment', 'evaluation',
                        'detailed', 'comprehensive', 'thorough', 'in-depth', 'extensive'
                    ])
                    
                    # Check if answer is comprehensive (shows deep understanding)
                    is_comprehensive = (is_informative and shows_reasoning and 
                                     (shows_inference or shows_analysis))
                    
                    if is_informative:
                        informative_answers += 1
                        print(f"✅ Q{i+1}: Informative answer found")
                    else:
                        print(f"❌ Q{i+1}: No relevant information found")
                    
                    if shows_reasoning:
                        reasoned_answers += 1
                        print(f"🧠 Q{i+1}: Shows reasoning")
                    
                    if shows_inference:
                        inferred_answers += 1
                        print(f"🔍 Q{i+1}: Shows inference")
                    
                    if shows_analysis:
                        analyzed_answers += 1
                        print(f"📊 Q{i+1}: Shows analysis")
                    
                    if is_comprehensive:
                        comprehensive_answers += 1
                        print(f"🏆 Q{i+1}: COMPREHENSIVE UNDERSTANDING")
                    
                    # Show sample of answer
                    if answer_text:
                        sample = answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                        print(f"   Sample: {sample}")
                
                # Calculate reasoning metrics
                accuracy_percentage = (informative_answers / total_questions) * 100
                reasoning_percentage = (reasoned_answers / total_questions) * 100
                inference_percentage = (inferred_answers / total_questions) * 100
                analysis_percentage = (analyzed_answers / total_questions) * 100
                comprehensive_percentage = (comprehensive_answers / total_questions) * 100
                
                print(f"\n📊 INTELLIGENT REASONING METRICS:")
                print(f"   Informative Answers: {accuracy_percentage:.1f}% ({informative_answers}/{total_questions})")
                print(f"   Reasoning Answers: {reasoning_percentage:.1f}% ({reasoned_answers}/{total_questions})")
                print(f"   Inference Answers: {inference_percentage:.1f}% ({inferred_answers}/{total_questions})")
                print(f"   Analysis Answers: {analysis_percentage:.1f}% ({analyzed_answers}/{total_questions})")
                print(f"   Comprehensive Understanding: {comprehensive_percentage:.1f}% ({comprehensive_answers}/{total_questions})")
                
                # Performance metrics
                print(f"\n📊 PERFORMANCE METRICS:")
                print(f"   Total Time: {duration:.2f} seconds")
                print(f"   Target Time: 120 seconds")
                print(f"   Performance: {'✅ FAST' if duration < 120 else '⚠️ SLOW'}")
                
                # Overall reasoning assessment
                if comprehensive_percentage > 80:
                    print("🎉 EXCELLENT INTELLIGENT REASONING!")
                elif comprehensive_percentage > 60:
                    print("📈 GOOD INTELLIGENT REASONING!")
                elif comprehensive_percentage > 40:
                    print("📊 MODERATE INTELLIGENT REASONING!")
                else:
                    print("⚠️  NEEDS IMPROVEMENT FOR REASONING")
                    
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
    test_intelligent_reasoning() 