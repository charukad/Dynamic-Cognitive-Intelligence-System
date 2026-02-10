"""vLLM client for LLM inference."""

import random
from typing import AsyncIterator, Dict, List, Optional, Union, Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.interfaces.llm_client import LLMClient

# Optional generic imports to avoid hard dependency failure if not used
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = get_logger(__name__)


class VLLMClient(LLMClient):
    """vLLM HTTP client implementation."""

    def __init__(self) -> None:
        """Initialize vLLM client."""
        
        # Model configuration per agent type
        # Updated for LM Studio integration
        self.model_routing = {
            "coder": "deepseek-ai_-_deepseek-coder-6.7b-instruct",
            "logician": "deepseek-ai_-_deepseek-coder-6.7b-instruct",
            "creative": "mistralai_-_mistral-7b-instruct-v0.2",
            "scholar": "mistralai_-_mistral-7b-instruct-v0.2",
            "critic": "phi-3-mini-4k-instruct",
            "executive": "mistralai_-_mistral-7b-instruct-v0.2",
        }
        self.model_map = {
            "default": settings.vllm_model_name,
            "mistral": "mistralai_-_mistral-7b-instruct-v0.2",
            "llama2": "llama-2-7b-chat",
            "codellama": "codellama-7b-instruct",
        }
        
        # Local embedding model cache
        self._embedding_model = None
        self._embedding_tokenizer = None
        self._local_embedding_model_name = "prajjwal1/bert-tiny"
        
        # Temperature settings per agent
        self.temperature_config = {
            "coder": 0.2,
            "logician": 0.1,
            "creative": 0.8,
            "scholar": 0.3,
            "critic": 0.2,
            "executive": 0.4,
        }
        
        # Token budget (max tokens per request)
        self.token_budget = {
            "default": 2048,
            "coder": 4096,
            "creative": 2048,
        }
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

        self.base_url = settings.vllm_api_url
        self.api_key = settings.vllm_api_key
        self.client: Optional[httpx.AsyncClient] = None

    def get_model_for_agent(self, agent_type: str) -> str:
        """Get the appropriate model for an agent type."""
        # Assuming a default model name exists, e.g., settings.vllm_model_name
        # Or, if not, ensure self.model_name is defined or handle the default differently.
        # For now, I'll assume a placeholder `self.model_name` or a default from settings.
        # If `self.model_name` is not defined, this line will cause an AttributeError.
        # A safer approach might be to use a default from settings directly or define a default here.
        # For the purpose of this edit, I'll keep it as provided, assuming `self.model_name` will be set elsewhere or is intended to be a default.
        return self.model_routing.get(agent_type.lower(), settings.vllm_model_name) # Changed self.model_name to settings.vllm_model_name for correctness
    
    def get_temperature_for_agent(self, agent_type: str) -> float:
        """Get the appropriate temperature for an agent type."""
        return self.temperature_config.get(agent_type.lower(), 0.7)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Simple approximation: ~4 chars per token for English.
        For production, use tiktoken or model-specific tokenizer.
        """
        return len(text) // 4
    
    def check_token_budget(self, prompt: str, agent_type: str = "default") -> bool:
        """Check if prompt is within token budget."""
        token_count = self.count_tokens(prompt)
        budget = self.token_budget.get(agent_type, self.token_budget["default"])
        return token_count <= budget

    async def connect(self) -> None:
        """Connect to vLLM server or initialize mock mode."""
        if settings.use_mock_llm:
            logger.warning("🔸 DCIS is running in MOCK LLM MODE - No real AI inference will occur")
            logger.info("Mock LLM ready to generate deterministic responses")
            return

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=120.0,
        )
        logger.info(f"Connected to vLLM at {self.base_url}")

    async def disconnect(self) -> None:
        """Disconnect from vLLM server."""
        if self.client:
            await self.client.aclose()
            logger.info("Disconnected from vLLM")
    
    async def health_check(self) -> bool:
        """Verify vLLM server is healthy."""
        if settings.use_mock_llm:
            return True

        if not self.client:
            raise RuntimeError("vLLM client not initialized")
        
        try:
            # Try to access models endpoint as health check
            response = await self.client.get("/models")
            response.raise_for_status()
            logger.debug("vLLM health check passed")
            return True
        except Exception as e:
            raise RuntimeError(f"vLLM health check failed: {e}") from e

    def _get_mock_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a context-aware mock response."""
        import time
        import random
        
        # Simulate thinking time for realism (500ms - 2s)
        time.sleep(random.uniform(0.5, 2.0))
        
        # Detect agent type/intent from system prompt or prompt content
        prompt_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()
        
        if "data analyst" in sys_lower or "pandas" in prompt_lower:
            return """
I have analyzed the provided dataset. Here are the key insights:
1. **Trend Analysis**: Strong positive correlation (r=0.85) between time and variable X.
2. **Outliers**: 3 significant outliers detected in Q3.
3. **Recommendation**: Optimize for segment A to maximize ROI.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({'x': [1, 2, 3], 'y': [10, 20, 30]})
plt.plot(df['x'], df['y'])
plt.title("Growth Trend")
```
"""
        elif "designer" in sys_lower or "ui" in prompt_lower:
            return """
Based on the requirements, I propose a 'Glassmorphism' aesthetic:
- **Primary Color**: #6C5CE7 (Soft Purple)
- **Background**: Frosted glass blur (backdrop-filter: blur(10px))
- **Typography**: Inter for body, Montserrat for headers.

Component Structure:
1. **Hero Section**: Large gradient heading with floating 3D elements.
2. **Dashboard**: Card-based layout with soft shadows.
"""
        elif "translator" in sys_lower:
            return f"Translated text: [Simulated translation of input] - Content preserved with high fidelity."
        
        elif "financial" in sys_lower:
            return """
Financial Assessment:
- **Risk Profile**: Moderate
- **Market Sentiment**: Bullish
- **Projected Growth**: +12% YoY

Recommendation: Diversify portfolio allocation with a focus on emerging tech sectors.
"""
        
        # Default generic response
        return f"I have processed your request: '{prompt[:50]}...'. \n\nThis is a simulated response working in Mock Mode. The system logic, routing, and metrics are real, but I am not using a GPU."

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate completion from prompt."""
        if settings.use_mock_llm:
            return self._get_mock_response(prompt, system_prompt)

        if not self.client:
            raise RuntimeError("Client not connected")

        messages = []
        # Merge system prompt into user message to support models that don't allow 'system' role
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {prompt}"
            
        messages.append({"role": "user", "content": full_prompt})

        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": settings.vllm_model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            
            # Log raw response for debugging 400 errors
            if response.status_code >= 400:
                error_content = response.text
                logger.error(f"LLM Error {response.status_code}: {error_content}")
                raise RuntimeError(f"LLM Error {response.status_code}: {error_content}")
            
            # response.raise_for_status() # Removed in favor of explicit check above
            data = response.json()
            logger.info(f"LLM Response: {data}")
            
            if "error" in data:
                error_obj = data["error"]
                if isinstance(error_obj, dict):
                    error_msg = error_obj.get("message", str(error_obj))
                else:
                    error_msg = str(error_obj)
                
                logger.error(f"LLM API Error: {error_msg}")
                raise RuntimeError(f"LLM API Error: {error_msg}")
                
            if "choices" not in data:
                logger.error(f"Invalid LLM response format: {data}")
                raise KeyError(f"'choices' not found in response: {data.keys()}")
                
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"vLLM generation failed: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        if settings.use_mock_llm:
            # Simulate streaming mock response
            import asyncio
            response = self._get_mock_response(prompt, system_prompt)
            for word in response.split(" "):
                yield word + " "
                await asyncio.sleep(0.05)  # Simulate token generation speed
            return

        if not self.client:
            raise RuntimeError("Client not connected")

        messages = []
        # Merge system prompt into user message to support models that don't allow 'system' role
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System Instruction: {system_prompt}\n\nUser Request: {prompt}"
            
        messages.append({"role": "user", "content": full_prompt})

        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": settings.vllm_model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as response:
                if response.status_code >= 400:
                    content = await response.aread()
                    error_msg = content.decode()
                    logger.error(f"LLM Stream Error {response.status_code}: {error_msg}")
                    raise RuntimeError(f"LLM Stream Error {response.status_code}: {error_msg}")
                
                # response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            logger.error(f"vLLM streaming failed: {e}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get vector embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Vector embedding (list of floats)
        """
        if settings.use_mock_llm:
            # Return random embedding vector of size 384 (common size)
            import random
            return [random.uniform(-1.0, 1.0) for _ in range(384)]

        if not self.client:
            await self.connect()
            
        try:
            # Try API first
            response = await self.client.post(
                "/embeddings",
                json={
                    "model": settings.vllm_model_name,
                    "input": text,
                },
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
            
        except Exception as e:
            logger.warning(f"API embedding failed ({e}), attempting local fallback...")
            return await self._get_local_embedding(text)

    async def _get_local_embedding(self, text: str) -> List[float]:
        """Generate embedding locally using transformers."""
        if not TRANSFORMERS_AVAILABLE:
             raise RuntimeError("Transformers library not available for local embedding fallback")
             
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        if not self._embedding_model:
            logger.info(f"Loading local embedding model: {self._local_embedding_model_name}")
            def load_model():
                tokenizer = AutoTokenizer.from_pretrained(self._local_embedding_model_name)
                model = AutoModel.from_pretrained(self._local_embedding_model_name)
                return tokenizer, model
            
            with ThreadPoolExecutor() as executor:
                self._embedding_tokenizer, self._embedding_model = await asyncio.get_event_loop().run_in_executor(
                    executor, load_model
                )

        def generate():
            inputs = self._embedding_tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                outputs = self._embedding_model(**inputs)
            # Mean pooling
            return outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, generate)


# Global instance
vllm_client = VLLMClient()
