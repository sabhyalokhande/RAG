import requests
import json
import time

# Test with insurance policy document to verify scoring optimization
test_data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2026-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=example",
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

def test_scoring_optimization():
    """Test the scoring optimization improvements with insurance policy questions"""
    
    print("🎯 TESTING SCORING OPTIMIZATION")
    print("="*80)
    print("📊 SCORING OPTIMIZATIONS:")
    print("✅ Maximum chunk sizes (3000 chars) for comprehensive coverage")
    print("✅ Increased retrieval counts (50 documents) for thorough search")
    print("✅ Extremely lenient quality filtering (3 char minimum)")
    print("✅ Enhanced RAG prompt with 30 scoring guidelines")
    print("✅ Aggressive chunking for maximum information extraction")
    print("✅ Optimized context enhancement (300 chars)")
    print("✅ Enhanced keyword prioritization for better relevance")
    print("="*80)
    print("📊 SCORING FOCUS AREAS:")
    print("✅ Detailed policy information extraction")
    print("✅ Specific numbers, dates, and exact terms")
    print("✅ Complete condition listings")
    print("✅ Comprehensive coverage explanations")
    print("✅ Exact policy language inclusion")
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
    print("🚀 TESTING SCORING-OPTIMIZED RAG SYSTEM")
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
            
            # Scoring analysis
            print("\n" + "="*80)
            print("📈 SCORING ANALYSIS")
            print("="*80)
            
            if 'answers' in result:
                answers = result['answers']
                total_questions = len(answers)
                informative_answers = 0
                detailed_answers = 0
                specific_answers = 0
                policy_specific_answers = 0
                scoring_ready_answers = 0
                
                print(f"\n📊 Analyzing {total_questions} answers for scoring...")
                
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
                    
                    # Check if answer is detailed (more than 150 characters)
                    is_detailed = len(answer_text) > 150
                    
                    # Check if answer contains specific details (numbers, dates, etc.)
                    has_specifics = any(indicator in answer_text.lower() for indicator in [
                        'according to', 'the policy states', 'specifically', 'exactly', 'precisely',
                        'grace period', 'waiting period', 'coverage', 'conditions', 'policy'
                    ])
                    
                    # Check if answer contains policy-specific information
                    has_policy_info = any(indicator in answer_text.lower() for indicator in [
                        'policy', 'coverage', 'conditions', 'terms', 'clause', 'section',
                        'premium', 'claim', 'benefit', 'exclusion', 'limit'
                    ])
                    
                    # Check if answer is scoring-ready (comprehensive and detailed)
                    is_scoring_ready = (is_informative and is_detailed and has_specifics and has_policy_info)
                    
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
                    
                    if has_policy_info:
                        policy_specific_answers += 1
                        print(f"📋 Q{i+1}: Contains policy information")
                    
                    if is_scoring_ready:
                        scoring_ready_answers += 1
                        print(f"🏆 Q{i+1}: SCORING READY")
                    
                    # Show sample of answer
                    if answer_text:
                        sample = answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                        print(f"   Sample: {sample}")
                
                # Calculate scoring metrics
                accuracy_percentage = (informative_answers / total_questions) * 100
                detail_percentage = (detailed_answers / total_questions) * 100
                specificity_percentage = (specific_answers / total_questions) * 100
                policy_percentage = (policy_specific_answers / total_questions) * 100
                scoring_percentage = (scoring_ready_answers / total_questions) * 100
                
                print(f"\n📊 SCORING METRICS:")
                print(f"   Informative Answers: {accuracy_percentage:.1f}% ({informative_answers}/{total_questions})")
                print(f"   Detailed Answers: {detail_percentage:.1f}% ({detailed_answers}/{total_questions})")
                print(f"   Specific Answers: {specificity_percentage:.1f}% ({specific_answers}/{total_questions})")
                print(f"   Policy-Specific: {policy_percentage:.1f}% ({policy_specific_answers}/{total_questions})")
                print(f"   Scoring Ready: {scoring_percentage:.1f}% ({scoring_ready_answers}/{total_questions})")
                
                # Performance metrics
                print(f"\n📊 PERFORMANCE METRICS:")
                print(f"   Total Time: {duration:.2f} seconds")
                print(f"   Target Time: 120 seconds")
                print(f"   Performance: {'✅ FAST' if duration < 120 else '⚠️ SLOW'}")
                
                # Overall scoring assessment
                if scoring_percentage > 80:
                    print("🎉 EXCELLENT SCORING POTENTIAL!")
                elif scoring_percentage > 60:
                    print("📈 GOOD SCORING POTENTIAL!")
                elif scoring_percentage > 40:
                    print("📊 MODERATE SCORING POTENTIAL!")
                else:
                    print("⚠️  NEEDS IMPROVEMENT FOR SCORING")
                    
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
    test_scoring_optimization() 