"""LLM client interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class LLMClient(ABC):
    """Abstract interface for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate completion from prompt."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Generate streaming completion."""
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding."""
        pass
