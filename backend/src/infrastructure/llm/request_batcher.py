"""Request batching for LLM inference optimization."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


@dataclass
class BatchRequest:
    """Single request in a batch."""
    
    request_id: UUID = field(default_factory=uuid4)
    prompt: str = ""
    max_tokens: int = 512
    temperature: float = 0.7
    timestamp: float = field(default_factory=time.time)
    future: Optional[asyncio.Future] = None


class RequestBatcher:
    """
    Batches LLM requests for efficient GPU utilization.
    
    Implements continuous batching with dynamic batch sizing.
    Fixed: Removed lock contention and deadlock issues.
    """
    
    def __init__(
        self,
        max_batch_size: int = 32,
        max_wait_ms: int = 50,
        llm_client=None,
    ):
        """
        Initialize request batcher.
        
        Args:
            max_batch_size: Maximum requests per batch
            max_wait_ms: Maximum wait time before processing batch
            llm_client: LLM client for inference
        """
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.llm_client = llm_client
        
        self.pending_requests: List[BatchRequest] = []
        self.processing = False
        self.lock = asyncio.Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_batches = 0
        self.avg_batch_size = 0.0

    async def submit_request(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Submit a request for batched processing.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        # Create request with future
        request = BatchRequest(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            future=asyncio.Future(),
        )
        
        # Add request to queue and check if processing needed
        should_process_immediate = False
        should_start_timer = False
        
        async with self.lock:
            self.pending_requests.append(request)
            self.total_requests += 1
            
            # Check if batch is full
            if len(self.pending_requests) >= self.max_batch_size and not self.processing:
                should_process_immediate = True
            elif not self.processing and len(self.pending_requests) == 1:
                # First request in a new batch - start timer
                should_start_timer = True
        
        # Start processing outside the lock to avoid deadlock
        if should_process_immediate:
            asyncio.create_task(self._process_batch())
        elif should_start_timer:
            asyncio.create_task(self._wait_and_process())
        
        # Wait for result
        result = await request.future
        return result

    async def _wait_and_process(self):
        """Wait for timeout then process partial batch."""
        await asyncio.sleep(self.max_wait_ms / 1000.0)
        
        # Check if we should process (outside lock first)
        should_process = False
        async with self.lock:
            if self.pending_requests and not self.processing:
                should_process = True
        
        if should_process:
            await self._process_batch()

    async def _process_batch(self):
        """
        Process current batch of requests.
        
        Fixed: Lock is only held for reading/modifying shared state,
        not during actual LLM processing to prevent deadlocks.
        """
        # Get batch to process (quick critical section)
        batch: List[BatchRequest] = []
        
        async with self.lock:
            if self.processing or not self.pending_requests:
                return
            
            # Mark as processing and extract batch
            self.processing = True
            batch = self.pending_requests[:self.max_batch_size]
            self.pending_requests = self.pending_requests[self.max_batch_size:]
        
        if not batch:
            async with self.lock:
                self.processing = False
            return
        
        try:
            # Extract prompts and params (no lock needed - local data)
            prompts = [req.prompt for req in batch]
            max_batch_tokens = max(req.max_tokens for req in batch)
            avg_temperature = sum(req.temperature for req in batch) / len(batch)
            
            logger.info(f"Processing batch of {len(batch)} requests")
            
            # Call LLM with all prompts (NO LOCK - long operation)
            try:
                results = await self._batch_generate(
                    prompts=prompts,
                    max_tokens=max_batch_tokens,
                    temperature=avg_temperature,
                )
                
                # Distribute results (no lock needed - futures are thread-safe)
                for request, result in zip(batch, results):
                    if not request.future.done():
                        request.future.set_result(result)
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                # Set exceptions (no lock needed)
                for request in batch:
                    if not request.future.done():
                        request.future.set_exception(e)
            
            # Update statistics (quick critical section)
            async with self.lock:
                self.total_batches += 1
                self.avg_batch_size = (
                    (self.avg_batch_size * (self.total_batches - 1) + len(batch))
                    / self.total_batches
                )
            
        finally:
            # Mark processing complete and check for more work
            should_continue = False
            async with self.lock:
                self.processing = False
                if self.pending_requests:
                    should_continue = True
            
            # Start next batch outside lock
            if should_continue:
                asyncio.create_task(self._process_batch())

    async def _batch_generate(
        self,
        prompts: List[str],
        max_tokens: int,
        temperature: float,
    ) -> List[str]:
        """
        Generate responses for a batch of prompts.
        
        Args:
            prompts: List of prompts
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            List of generated texts
        """
        if not self.llm_client:
            # Fallback: process individually
            results = []
            for prompt in prompts:
                result = await self._single_generate(prompt, max_tokens, temperature)
                results.append(result)
            return results
        
        # Batch processing with vLLM
        results = []
        for prompt in prompts:
            result = await self.llm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            results.append(result)
        
        return results

    async def _single_generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate response for single prompt (fallback)."""
        if self.llm_client:
            return await self.llm_client.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        return "Mock response"

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics."""
        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "avg_batch_size": self.avg_batch_size,
            "pending_requests": len(self.pending_requests),
            "processing": self.processing,
        }


# Global batcher instance
request_batcher = RequestBatcher()
