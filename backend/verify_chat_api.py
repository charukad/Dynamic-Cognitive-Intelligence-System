"""
Verify Chat API

Tests the new Chat API endpoint with a real LLM request.
"""
import requests
import json
import time

def test_chat():
    print("💬 Testing Chat API with Real LLM...")
    
    url = "http://localhost:8008/api/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "user", "content": "What is the capital of France? Answer in one word."}
        ],
        "stream": False
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload)
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Success ({duration:.2f}s)")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_chat()
