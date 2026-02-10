"""Base agent class for all specialized agents."""

import time
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Agent, AgentStatus
from src.infrastructure.llm import vllm_client

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialized agents.
    
    Provides common functionality for agent execution, performance tracking,
    and LLM interaction.
    """

    def __init__(self, agent: Agent) -> None:
        """
        Initialize base agent.
        
        Args:
            agent: Agent domain model
        """
        self.agent = agent
        self.logger = get_logger(f"{__name__}.{agent.name}")

    @abstractmethod
    async def process(self, task_input: dict) -> dict:
        """
        Process a task with agent-specific logic.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Task output/result
            
        Raises:
            Exception: If processing fails
        """
        pass

    async def execute(self, task_input: dict) -> dict:
        """
        Execute task with performance tracking and error handling.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Task output/result
        """
        start_time = time.time()
        success = False
        
        try:
            self.agent.mark_busy()
            self.logger.info(f"Agent {self.agent.name} starting task execution")
            
            result = await self.process(task_input)
            
            success = True
            self.logger.info(f"Agent {self.agent.name} completed task successfully")
            return result
            
        except Exception as e:
            self.agent.mark_error()
            self.logger.error(f"Agent {self.agent.name} failed: {str(e)}")
            raise
            
        finally:
            # Update performance metrics
            response_time = time.time() - start_time
            self.agent.update_performance(success, response_time)
            
            if success:
                self.agent.mark_idle()
            
            self.logger.info(
                f"Agent {self.agent.name} performance: "
                f"success_rate={self.agent.success_rate:.2%}, "
                f"avg_response_time={self.agent.avg_response_time:.2f}s"
            )

    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate LLM response using agent's configuration.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        try:
            response = await vllm_client.generate(
                prompt=prompt,
                system_prompt=self.agent.system_prompt,
                temperature=self.agent.temperature,
                max_tokens=max_tokens,
            )
            return response
            
        except Exception as e:
            self.logger.error(f"LLM generation failed: {str(e)}")
            raise

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.agent.name}, type={self.agent.agent_type.value})"

    def __repr__(self) -> str:
        """String representation."""
        return self.__str__()
