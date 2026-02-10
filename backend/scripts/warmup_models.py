#!/usr/bin/env python3
"""Model warm-up script for vLLM inference server."""

import asyncio
import time
from typing import List

import httpx

# Model endpoints
VLLM_BASE_URL = "http://localhost:8001"

# Warm-up prompts for each model type
WARMUP_PROMPTS = {
    "deepseek-coder": [
        "def fibonacci(n):",
        "# Write a Python function to",
        "class DataStructure:",
    ],
    "mistral": [
        "Explain the concept of",
        "What are the benefits of",
        "How does one implement",
    ],
    "phi-3": [
        "Question: What is AI?\nAnswer:",
        "Summarize the following:",
        "Translate to French:",
    ],
}


async def warmup_model(model_name: str, prompts: List[str]):
    """
    Warm up a specific model with test prompts.
    
    Args:
        model_name: Name of the model
        prompts: List of warm-up prompts
    """
    print(f"\n🔥 Warming up {model_name}...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, prompt in enumerate(prompts, 1):
            print(f"  [{i}/{len(prompts)}] Sending prompt: {prompt[:50]}...")
            
            start_time = time.time()
            
            try:
                response = await client.post(
                    f"{VLLM_BASE_URL}/v1/completions",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "max_tokens": 50,
                        "temperature": 0.1,
                    },
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    tokens = data.get("usage", {}).get("completion_tokens", 0)
                    print(f"    ✓ Success ({elapsed:.0f}ms, {tokens} tokens)")
                else:
                    print(f"    ✗ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ✗ Exception: {e}")
    
    print(f"✓ {model_name} warm-up complete")


async def check_health():
    """Check if vLLM server is healthy."""
    print("🏥 Checking vLLM server health...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{VLLM_BASE_URL}/health")
            
            if response.status_code == 200:
                print("  ✓ Server is healthy")
                return True
            else:
                print(f"  ✗ Server unhealthy: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ✗ Cannot reach server: {e}")
        return False


async def get_models():
    """Get list of loaded models."""
    print("\n📋 Fetching loaded models...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{VLLM_BASE_URL}/v1/models")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                
                print(f"  Found {len(models)} model(s):")
                for model in models:
                    print(f"    - {model.get('id', 'unknown')}")
                
                return [m.get("id") for m in models]
            else:
                print(f"  ✗ Error fetching models: {response.status_code}")
                return []
                
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return []


async def main():
    """Main warm-up routine."""
    print("=" * 60)
    print("vLLM Model Warm-Up Script")
    print("=" * 60)
    
    # Check server health
    if not await check_health():
        print("\n❌ vLLM server is not available. Exiting.")
        return
    
    # Get loaded models
    loaded_models = await get_models()
    
    if not loaded_models:
        print("\n❌ No models loaded. Exiting.")
        return
    
    # Warm up each model
    print("\n🚀 Starting warm-up sequence...")
    
    for model_id in loaded_models:
        # Determine prompt set
        prompts = WARMUP_PROMPTS.get("mistral", WARMUP_PROMPTS["mistral"])  # Default
        
        if "deepseek" in model_id.lower() or "coder" in model_id.lower():
            prompts = WARMUP_PROMPTS["deepseek-coder"]
        elif "phi" in model_id.lower():
            prompts = WARMUP_PROMPTS["phi-3"]
        
        # Warm up
        await warmup_model(model_id, prompts)
        
        # Small delay between models
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ All models warmed up successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
