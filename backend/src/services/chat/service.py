"""
Chat Service

Handles chat interactions with the LLM via VLLMClient.
"""

from typing import List, AsyncIterator
import json
from src.core import get_logger
from src.infrastructure.llm.vllm_client import vllm_client
from src.domain.models.agent import Agent

logger = get_logger(__name__)

class ChatService:
    """Service for handling chat completions and history."""
    
    def __init__(self):
        self.client = vllm_client
        
    async def chat_completion(
        self, 
        messages: List[dict], 
        system_prompt: str = "You are a helpful AI assistant in the DCIS system.",
        temperature: float = 0.7
    ) -> str:
        """
        Generate a unified chat completion.
        
        Args:
            messages: List of message dicts (role, content)
            system_prompt: System instruction
            temperature: Creativity parameter
            
        Returns:
            The complete response text
        """
        # Convert history to prompt format if needed, or pass as is
        # VLLMClient currently expects a single prompt string for 'generate'
        # We need to construct a prompt from the history for raw completion
        # OR use a specific chat endpoint if VLLMClient supports it.
        
        # Checking VLLMClient, it has 'generate' and 'generate_stream'.
        # We will construct a simple prompt for now.
        
        # Simple prompt construction for Llama/Mistral (Instruction format)
        # standardized for compatibility
        
        prompt = f"System: {system_prompt}\n\n"
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
            
        prompt += "Assistant: "
        
        response = await self.client.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=1000
        )
        return response

    async def chat_stream(
        self,
        messages: List[dict],
        system_prompt: str = "You are a helpful AI assistant."
    ) -> AsyncIterator[str]:
        """Stream chat response."""
        prompt = f"System: {system_prompt}\n\n"
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
            
        prompt += "Assistant: "
        
        async for chunk in self.client.generate_stream(prompt=prompt):
            yield chunk

# Singleton
chat_service = ChatService()
