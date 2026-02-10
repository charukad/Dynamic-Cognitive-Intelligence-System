"""
Oneiroi - The Dreaming System.

Implements offline learning through experience replay and model fine-tuning.
Named after the Greek gods of dreams.
"""

import asyncio
import json
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core import get_logger

logger = get_logger(__name__)


@dataclass
class Experience:
    """A single experience from agent interactions."""
    
    task_id: str
    agent_type: str
    input_prompt: str
    output_response: str
    reward: float  # Quality score, success rating, etc.
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DreamingConfig:
    """Configuration for the dreaming system."""
    
    replay_buffer_size: int = 10000
    batch_size: int = 32
    min_reward_threshold: float = 0.7  # Only learn from good experiences
    dream_frequency_hours: int = 24  # How often to trigger dreaming
    lora_rank: int = 8  # LoRA adaptation rank
    learning_rate: float = 3e-4


class ReplayBuffer:
    """
    Experience replay buffer for storing agent interactions.
    
    Stores high-quality experiences for offline learning.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize replay buffer.
        
        Args:
            max_size: Maximum number of experiences to store
        """
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.high_reward_buffer = deque(maxlen=max_size // 2)

    def add(self, experience: Experience) -> None:
        """
        Add experience to buffer.
        
        Args:
            experience: Experience to add
        """
        self.buffer.append(experience)
        
        # Track high-reward experiences separately
        if experience.reward > 0.8:
            self.high_reward_buffer.append(experience)
        
        logger.debug(
            f"Added experience with reward {experience.reward:.2f}. "
            f"Buffer size: {len(self.buffer)}"
        )

    def sample(self, batch_size: int, min_reward: float = 0.0) -> List[Experience]:
        """
        Sample random batch of experiences.
        
        Args:
            batch_size: Number of experiences to sample
            min_reward: Minimum reward threshold
            
        Returns:
            List of sampled experiences
        """
        # Filter by reward threshold
        eligible = [exp for exp in self.buffer if exp.reward >= min_reward]
        
        if len(eligible) < batch_size:
            return list(eligible)
        
        return random.sample(eligible, batch_size)

    def get_top_experiences(self, n: int = 100) -> List[Experience]:
        """Get top N experiences by reward."""
        sorted_exp = sorted(self.buffer, key=lambda x: x.reward, reverse=True)
        return sorted_exp[:n]

    def get_statistics(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        if not self.buffer:
            return {"size": 0, "avg_reward": 0.0}
        
        rewards = [exp.reward for exp in self.buffer]
        
        return {
            "size": len(self.buffer),
            "high_reward_size": len(self.high_reward_buffer),
            "avg_reward": sum(rewards) / len(rewards),
            "max_reward": max(rewards),
            "min_reward": min(rewards),
        }


class OneiroiDreamer:
    """
    The Dreaming System - Offline learning from experiences.
    
    Implements:
    - Experience replay
    - LoRA fine-tuning
    - Knowledge consolidation
    - Scheduled "twilight" mode for optimization
    """

    def __init__(self, config: Optional[DreamingConfig] = None):
        """
        Initialize Oneiroi dreaming system.
        
        Args:
            config: Dreaming configuration
        """
        self.config = config or DreamingConfig()
        self.replay_buffer = ReplayBuffer(self.config.replay_buffer_size)
        
        self.last_dream_time: Optional[datetime] = None
        self.total_dreams: int = 0
        self.training_history: List[Dict[str, Any]] = []

    async def record_experience(
        self,
        task_id: str,
        agent_type: str,
        input_prompt: str,
        output_response: str,
        reward: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Record an agent experience.
        
        Args:
            task_id: Task identifier
            agent_type: Type of agent
            input_prompt: Input prompt
            output_response: Generated response
            reward: Quality/success reward
            metadata: Additional metadata
        """
        experience = Experience(
            task_id=task_id,
            agent_type=agent_type,
            input_prompt=input_prompt,
            output_response=output_response,
            reward=reward,
            metadata=metadata or {},
        )
        
        self.replay_buffer.add(experience)

    async def dream(self) -> Dict[str, Any]:
        """
        Enter dreaming mode - replay experiences and fine-tune models.
        
        Returns:
            Dreaming session statistics
        """
        logger.info("🌙 Entering Oneiroi Dreaming Mode...")
        
        # Get high-quality experiences
        training_data = self.replay_buffer.sample(
            batch_size=self.config.batch_size * 10,
            min_reward=self.config.min_reward_threshold,
        )
        
        if len(training_data) < 10:
            logger.warning("Not enough high-quality experiences for dreaming")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        logger.info(f"Dreaming with {len(training_data)} experiences")
        
        # Organize by agent type
        agent_experiences: Dict[str, List[Experience]] = {}
        for exp in training_data:
            if exp.agent_type not in agent_experiences:
                agent_experiences[exp.agent_type] = []
            agent_experiences[exp.agent_type].append(exp)
        
        # Train each agent type
        training_results = {}
        for agent_type, experiences in agent_experiences.items():
            result = await self._train_agent_lora(agent_type, experiences)
            training_results[agent_type] = result
        
        # Update statistics
        self.last_dream_time = datetime.utcnow()
        self.total_dreams += 1
        
        dream_stats = {
            "status": "completed",
            "total_experiences": len(training_data),
            "agents_trained": list(training_results.keys()),
            "training_results": training_results,
            "timestamp": self.last_dream_time.isoformat(),
        }
        
        self.training_history.append(dream_stats)
        
        logger.info(f"✨ Dreaming complete! Trained {len(training_results)} agent types")
        
        return dream_stats

    async def _train_agent_lora(
        self,
        agent_type: str,
        experiences: List[Experience],
    ) -> Dict[str, Any]:
        """
        Fine-tune agent using LoRA.
        
        Args:
            agent_type: Agent type to train
            experiences: Training experiences
            
        Returns:
            Training statistics
        """
        logger.info(f"Training {agent_type} agent with {len(experiences)} examples")
        
        # Prepare training data in instruction format
        training_examples = []
        for exp in experiences:
            training_examples.append({
                "instruction": exp.input_prompt,
                "output": exp.output_response,
                "weight": exp.reward,  # Weight by quality
            })
        
        # In production, this would:
        # 1. Format data for LoRA training
        # 2. Call HuggingFace PEFT library
        # 3. Train LoRA adapters
        # 4. Save adapters to disk
        # 5. Optionally merge with base model
        
        # Simulate training
        await asyncio.sleep(0.5)  # Simulate training time
        
        avg_reward = sum(exp.reward for exp in experiences) / len(experiences)
        
        return {
            "agent_type": agent_type,
            "examples_trained": len(experiences),
            "avg_reward": avg_reward,
            "lora_rank": self.config.lora_rank,
            "status": "success",
        }

    async def should_dream(self) -> bool:
        """Check if it's time to dream."""
        if self.last_dream_time is None:
            return len(self.replay_buffer.buffer) > 100
        
        hours_since_last = (
            datetime.utcnow() - self.last_dream_time
        ).total_seconds() / 3600
        
        return hours_since_last >= self.config.dream_frequency_hours

    async def twilight_mode(self) -> None:
        """
        Background task that periodically triggers dreaming.
        
        Run this as a scheduled job (e.g., cron, celery beat).
        """
        while True:
            if await self.should_dream():
                await self.dream()
            
            # Sleep for 1 hour
            await asyncio.sleep(3600)

    def export_training_data(self, filepath: str) -> None:
        """
        Export replay buffer to training dataset file.
        
        Args:
            filepath: Output JSON file path
        """
        top_experiences = self.replay_buffer.get_top_experiences(n=1000)
        
        data = [
            {
                "input": exp.input_prompt,
                "output": exp.output_response,
                "reward": exp.reward,
                "agent_type": exp.agent_type,
                "metadata": exp.metadata,
            }
            for exp in top_experiences
        ]
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(data)} training examples to {filepath}")

    def get_dreaming_stats(self) -> Dict[str, Any]:
        """Get dreaming system statistics."""
        buffer_stats = self.replay_buffer.get_statistics()
        
        return {
            "total_dreams": self.total_dreams,
            "last_dream": self.last_dream_time.isoformat() if self.last_dream_time else None,
            "buffer_stats": buffer_stats,
            "config": {
                "buffer_size": self.config.replay_buffer_size,
                "batch_size": self.config.batch_size,
                "min_reward_threshold": self.config.min_reward_threshold,
                "dream_frequency_hours": self.config.dream_frequency_hours,
            },
        }


# Global instance
oneiroi = OneiroiDreamer()
