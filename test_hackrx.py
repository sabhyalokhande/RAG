import requests
import json
import time

# Test data for Newton's Principia
test_data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/principia_newton.pdf?sv=2023-01-03&st=2025-07-28T07%3A20%3A32Z&se=2026-07-29T07%3A20%3A00Z&sr=b&sp=r&sig=V5I1QYyigoxeUMbnUKsdEaST99F5%2FDfo7wpKg9XXF5w%3D",
    "questions": [
        "State Newton's First Law of Motion from the Principia.",
        "Explain Newton's concept of absolute space and time.",
        "What is the Law of Universal Gravitation as stated in the Principia?",
        "How does Newton describe centripetal force mathematically?",
        "What is the significance of the three laws of motion according to Newton?",
        "Describe Newton's treatment of planetary motion.",
        "How did Newton derive Kepler's laws from his own principles?",
        "What is inertia according to Newton's description?",
        "What are the definitions of mass and quantity of motion in Book I?",
        "How does Newton distinguish between empirical observation and mathematical proof in his method?"
    ]
}

def test_hackrx_endpoint():
    """Test the /hackrx/run endpoint"""
    
    # Wait a moment for the server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Test the health endpoint first
    try:
        health_response = requests.get("http://localhost:5001/health")
        print(f"Health check status: {health_response.status_code}")
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
        "Authorization": "Bearer test-api-key"  # You'll need to replace this with a real API key
    }
    
    print("\n" + "="*80)
    print("🚀 TESTING HACKRX ENDPOINT")
    print("="*80)
    print(f"📄 Document URL: {test_data['documents']}")
    print(f"❓ Number of questions: {len(test_data['questions'])}")
    print("="*80)
    
    try:
        # Make the request
        print("📤 Sending request to /hackrx/run...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=test_data, timeout=300)  # 5 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request completed in {duration:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Here are the results:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes). The document might be large or processing is taking longer than expected.")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_hackrx_endpoint() 