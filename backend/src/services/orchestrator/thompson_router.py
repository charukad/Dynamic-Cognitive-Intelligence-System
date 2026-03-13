"""Thompson Sampling router for intelligent agent selection."""

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
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


@dataclass
class LegacyAgentPerformance:
    """Legacy performance structure keyed by (task_type, agent_type)."""

    successes: float = 0.0
    failures: float = 0.0
    total_reward: float = 0.0
    total_time_ms: float = 0.0
    trials: int = 0

    def sample(self) -> float:
        alpha = self.successes + 1.0
        beta = self.failures + 1.0
        return random.betavariate(alpha, beta)


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

    def get_agent_stats(self, agent_id: UUID, task_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Backward-compatible accessor used by legacy orchestration tests.

        Args:
            agent_id: Agent identifier
            task_type: Optional task-type hint (currently informational)

        Returns:
            Agent performance stats, or None if the agent is unknown
        """
        perf = self.performance.get(agent_id)
        if not perf:
            return None

        return {
            "agent_id": str(agent_id),
            "agent_type": perf.agent_type.value,
            "task_type": task_type,
            "success_rate": perf.success_rate,
            "total_tasks": perf.total_tasks,
            "successes": perf.successes,
            "failures": perf.failures,
        }


class ThompsonRouter:
    """
    Backward-compatible async Thompson router used by legacy unit tests.

    This router operates on string `agent_type` identifiers and keeps
    per-task-type Beta distributions.
    """

    def __init__(self, exploration_weight: float = 0.05) -> None:
        self.exploration_weight = exploration_weight
        self.exploration_bonus = exploration_weight
        self._performance: Dict[str, Dict[str, LegacyAgentPerformance]] = {}
        self._agent_values: Dict[str, Any] = {}
        self._agent_types: Dict[str, str] = {}

    @staticmethod
    def _to_key(agent_identifier: Any) -> str:
        return str(agent_identifier)

    def register_agent(self, agent_id: Any, agent_type: Any) -> None:
        """Register an agent for selection when `available_agents` is omitted."""
        key = self._to_key(agent_id)
        self._agent_values[key] = agent_id
        self._agent_types[key] = str(getattr(agent_type, "value", agent_type))

    async def select_agent(
        self,
        task_type: str,
        available_agents: Optional[List[Any]] = None,
    ) -> Optional[Any]:
        if available_agents is None:
            available_agents = list(self._agent_values.values())
        if not available_agents:
            return None
        if len(available_agents) == 1:
            return available_agents[0]

        task_stats = self._performance.setdefault(task_type, {})
        best_agent_key: Optional[str] = None
        best_score = float("-inf")
        agent_lookup: Dict[str, Any] = {}

        for agent_identifier in available_agents:
            agent_key = self._to_key(agent_identifier)
            agent_lookup[agent_key] = agent_identifier
            stats = task_stats.setdefault(agent_key, LegacyAgentPerformance())
            sample = stats.sample()
            if stats.trials < 3:
                sample += self.exploration_bonus
            if sample > best_score:
                best_score = sample
                best_agent_key = agent_key

        if best_agent_key is None:
            return None
        return agent_lookup.get(best_agent_key)

    async def update_performance(
        self,
        agent_id: Any = None,
        task_type: str = "general",
        success: bool = False,
        execution_time_ms: Optional[float] = None,
        reward: Optional[float] = None,
        agent_type: Optional[str] = None,
    ) -> None:
        if agent_id is None and agent_type is None:
            return

        if agent_type is not None and agent_id is None:
            agent_id = agent_type

        agent_key = self._to_key(agent_id)
        task_stats = self._performance.setdefault(task_type, {})
        stats = task_stats.setdefault(agent_key, LegacyAgentPerformance())

        stats.trials += 1
        if reward is None:
            if execution_time_ms is not None:
                reward = max(0.0, 1.0 - (float(execution_time_ms) / 5000.0))
            else:
                reward = 1.0 if success else 0.0
        stats.total_reward += float(reward)
        if execution_time_ms is not None:
            stats.total_time_ms += float(execution_time_ms)

        if success:
            stats.successes += 1.0
        else:
            stats.failures += 1.0

    def get_agent_stats(self, agent_id: Any, task_type: str) -> Optional[Dict[str, float]]:
        task_stats = self._performance.get(task_type, {})
        stats = task_stats.get(self._to_key(agent_id))
        if stats is None:
            return None

        return {
            "successes": stats.successes,
            "failures": stats.failures,
            "trials": float(stats.trials),
            "avg_time_ms": (stats.total_time_ms / stats.trials) if stats.trials else 0.0,
            "avg_reward": (stats.total_reward / stats.trials) if stats.trials else 0.0,
        }

    def get_leaderboard(self, task_type: str) -> List[Dict[str, Any]]:
        task_stats = self._performance.get(task_type, {})
        rows: List[Dict[str, Any]] = []
        for agent_key, stats in task_stats.items():
            total = stats.successes + stats.failures
            success_rate = (stats.successes / total) if total > 0 else 0.0
            rows.append(
                {
                    "agent_id": self._agent_values.get(agent_key, agent_key),
                    "success_rate": success_rate,
                    "avg_time_ms": (stats.total_time_ms / stats.trials) if stats.trials else 0.0,
                    "trials": stats.trials,
                }
            )
        rows.sort(key=lambda row: (-row["success_rate"], row["avg_time_ms"]))
        return rows

    def get_statistics(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        snapshot: Dict[str, Dict[str, Dict[str, float]]] = {}
        for task_type, agents in self._performance.items():
            snapshot[task_type] = {}
            for agent_key, stats in agents.items():
                total = stats.successes + stats.failures
                success_rate = (stats.successes / total) if total > 0 else 0.0
                snapshot[task_type][agent_key] = {
                    "successes": stats.successes,
                    "failures": stats.failures,
                    "trials": float(stats.trials),
                    "success_rate": success_rate,
                    "total_reward": stats.total_reward,
                    "total_time_ms": stats.total_time_ms,
                    "avg_reward": (stats.total_reward / stats.trials) if stats.trials else 0.0,
                }
        return snapshot


# Singleton instance
thompson_router = ThompsonSamplingRouter()
