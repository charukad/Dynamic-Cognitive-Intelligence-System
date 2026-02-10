#!/usr/bin/env python3
"""Test script to verify LM Studio integration."""

import asyncio
import sys

import httpx


async def test_lm_studio_connection():
    """Test connection to LM Studio server."""
    print("=" * 60)
    print("LM Studio Integration Test")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:1234/v1"
    
    # Test 1: Check server health
    print("\n1️⃣ Testing server connection...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/models")
            if response.status_code == 200:
                print("   ✅ Server is responding")
                models = response.json()
                print(f"   Found {len(models.get('data', []))} model(s):")
                for model in models.get("data", []):
                    print(f"      - {model.get('id', 'unknown')}")
            else:
                print(f"   ❌ Server error: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n💡 Make sure LM Studio is running and a model is loaded!")
        return False
    
    # Test 2: Test chat completion
    print("\n2️⃣ Testing chat completion...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'Hello from DCIS!' in one sentence."}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 50,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"   ✅ Model response: {content}")
                print(f"   Tokens used: {data.get('usage', {}).get('total_tokens', 'unknown')}")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return False
    
    # Test 3: Test specific DCIS models
    print("\n3️⃣ Testing DCIS model availability...")
    required_models = [
        "mistralai_-_mistral-7b-instruct-v0.2",
        "deepseek-ai_-_deepseek-coder-6.7b-instruct",
        "phi-3-mini-4k-instruct"
    ]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/models")
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m.get("id", "") for m in models_data.get("data", [])]
                
                for model_name in required_models:
                    if model_name in available_models:
                        print(f"   ✅ {model_name}")
                    else:
                        print(f"   ⚠️  {model_name} - Not found in LM Studio")
                        print("      Make sure this model is loaded in LM Studio")
    except Exception as e:
        print(f"   ❌ Error checking models: {e}")
    
    print("\n" + "=" * 60)
    print("✅ LM Studio integration test complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("   1. Make sure all 3 models are loaded in LM Studio")
    print("   2. Update .env file with: VLLM_API_URL=http://127.0.0.1:1234/v1")
    print("   3. Restart the DCIS backend server")
    print("   4. Test the agents via the API\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_lm_studio_connection())
    sys.exit(0 if success else 1)
