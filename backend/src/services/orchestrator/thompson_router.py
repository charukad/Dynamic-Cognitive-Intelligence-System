"""Thompson Sampling router for intelligent agent selection."""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Agent, AgentType

logger = get_logger(__name__)


@dataclass
class AgentPerformance:
    """
    Agent performance statistics for Thompson Sampling.
    
    Uses Beta distribution to model agent success probability.
    """
    
    agent_id: UUID
    agent_type: AgentType
    successes: int = 0  # Alpha parameter
    failures: int = 0   # Beta parameter
    total_tasks: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate empirical success rate."""
        if self.total_tasks == 0:
            return 0.5  # Prior belief
        return self.successes / self.total_tasks
    
    def sample(self) -> float:
        """
        Sample from Beta distribution.
        
        Returns:
            Sampled success probability
        """
        # Use Beta(successes + 1, failures + 1) as posterior
        # +1 for uniform prior
        alpha = self.successes + 1
        beta = self.failures + 1
        
        # Sample from Beta distribution
        return random.betavariate(alpha, beta)
    
    def update(self, success: bool) -> None:
        """
        Update performance statistics.
        
        Args:
            success: Whether task was successful
        """
        self.total_tasks += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1


class ThompsonSamplingRouter:
    """
    Thompson Sampling router for multi-armed bandit agent selection.
    
    Balances exploration (trying different agents) and exploitation
    (using best-performing agents) using Bayesian optimization.
    """

    def __init__(self, exploration_bonus: float = 0.1) -> None:
        """
        Initialize Thompson Sampling router.
        
        Args:
            exploration_bonus: Bonus for exploration (0.0-1.0)
        """
        self.exploration_bonus = exploration_bonus
        self.performance: Dict[UUID, AgentPerformance] = {}
        self.type_to_agents: Dict[AgentType, List[UUID]] = {}

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the router.
        
        Args:
            agent: Agent to register
        """
        if agent.id not in self.performance:
            self.performance[agent.id] = AgentPerformance(
                agent_id=agent.id,
                agent_type=agent.agent_type,
            )
            
            # Add to type mapping
            if agent.agent_type not in self.type_to_agents:
                self.type_to_agents[agent.agent_type] = []
            self.type_to_agents[agent.agent_type].append(agent.id)
            
            logger.info(f"Registered agent {agent.name} (id={agent.id}) with router")

    def select_agent(
        self,
        available_agents: List[Agent],
        agent_type_hint: Optional[str] = None,
    ) -> Agent:
        """
        Select best agent using Thompson Sampling.
        
        Args:
            available_agents: List of available agents
            agent_type_hint: Optional hint for preferred agent type
            
        Returns:
            Selected agent
            
        Raises:
            ValueError: If no agents available
        """
        if not available_agents:
            raise ValueError("No available agents")

        # Register any new agents
        for agent in available_agents:
            if agent.id not in self.performance:
                self.register_agent(agent)

        # Filter by type hint if provided
        candidates = available_agents
        if agent_type_hint:
            try:
                preferred_type = AgentType(agent_type_hint)
                type_candidates = [
                    a for a in available_agents 
                    if a.agent_type == preferred_type
                ]
                if type_candidates:
                    candidates = type_candidates
                    logger.debug(f"Filtered to {len(candidates)} agents of type {agent_type_hint}")
            except ValueError:
                logger.warning(f"Invalid agent type hint: {agent_type_hint}")

        # Sample from each agent's performance distribution
        samples = {}
        for agent in candidates:
            perf = self.performance[agent.id]
            sample = perf.sample()
            
            # Add exploration bonus for under-explored agents
            if perf.total_tasks < 5:
                sample += self.exploration_bonus
            
            samples[agent.id] = sample
            logger.debug(
                f"Agent {agent.name}: sample={sample:.3f}, "
                f"success_rate={perf.success_rate:.2%}, "
                f"tasks={perf.total_tasks}"
            )

        # Select agent with highest sample
        selected_id = max(samples, key=samples.get)
        selected_agent = next(a for a in candidates if a.id == selected_id)
        
        logger.info(
            f"Selected agent {selected_agent.name} "
            f"(sample={samples[selected_id]:.3f})"
        )
        
        return selected_agent

    def update_performance(
        self,
        agent_id: UUID,
        success: bool,
    ) -> None:
        """
        Update agent performance after task completion.
        
        Args:
            agent_id: Agent ID
            success: Whether task was successful
        """
        if agent_id not in self.performance:
            logger.warning(f"Unknown agent ID: {agent_id}")
            return

        self.performance[agent_id].update(success)
        
        perf = self.performance[agent_id]
        logger.info(
            f"Updated agent {agent_id} performance: "
            f"success_rate={perf.success_rate:.2%}, "
            f"tasks={perf.total_tasks}"
        )

    def get_performance_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Get performance statistics for all agents.
        
        Returns:
            Performance statistics by agent ID
        """
        return {
            str(agent_id): {
                "agent_type": perf.agent_type.value,
                "success_rate": perf.success_rate,
                "total_tasks": perf.total_tasks,
                "successes": perf.successes,
                "failures": perf.failures,
            }
            for agent_id, perf in self.performance.items()
        }

    def get_best_agent_for_type(self, agent_type: AgentType) -> Optional[UUID]:
        """
        Get best-performing agent for a given type.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Best agent ID, or None if no agents of that type
        """
        agent_ids = self.type_to_agents.get(agent_type, [])
        if not agent_ids:
            return None

        # Find agent with highest success rate
        best_id = max(
            agent_ids,
            key=lambda aid: self.performance[aid].success_rate,
        )
        
        return best_id


# Singleton instance
thompson_router = ThompsonSamplingRouter()
