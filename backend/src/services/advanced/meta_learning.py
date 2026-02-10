"""Meta-learning and self-improvement system."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric for an agentor task."""
    
    task_id: str
    agent_id: str
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningUpdate:
    """A learning update based on performance feedback."""
    
    update_id: str
    component: str  # "agent", "planner", "router"
    parameter_name: str
    old_value: Any
    new_value: Any
    reason: str
    improvement: float
    timestamp: float = field(default_factory=time.time)


class MetaLearner:
    """
    Meta-learning system for self-improvement.
    
    Analyzes performance metrics and adjusts agent parameters
    to improve system performance over time.
    """
    
    def __init__(self, learning_rate: float = 0.1):
        """
        Initialize meta-learner.
        
        Args:
            learning_rate: Rate of parameter updates
        """
        self.learning_rate = learning_rate
        
        # Performance history
        self.metrics: List[PerformanceMetric] = []
        self.updates: List[LearningUpdate] = []
        
        # Agent performance tracking
        self.agent_success_rate: Dict[str, float] = defaultdict(float)
        self.agent_avg_latency: Dict[str, float] = defaultdict(float)
        self.agent_task_count: Dict[str, int] = defaultdict(int)
        
        # Temperature adaptation
        self.agent_temperatures: Dict[str, float] = {
            "logician": 0.1,
            "creative": 0.8,
            "scholar": 0.3,
            "critic": 0.2,
            "coder": 0.2,
            "executive": 0.4,
        }
        
        # Router weights (Thompson Sampling)
        self.router_weights: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"alpha": 1.0, "beta": 1.0}
        )
    
    async def record_performance(
        self,
        task_id: str,
        agent_id: str,
        success: bool,
        latency: float,
        quality_score: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Record performance metric for a task.
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            success: Whether task succeeded
            latency: Task completion time
            quality_score: Optional quality rating (0-1)
            metadata: Additional metadata
        """
        # Record success metric
        metric = PerformanceMetric(
            task_id=task_id,
            agent_id=agent_id,
            metric_name="success",
            value=1.0 if success else 0.0,
            metadata=metadata or {},
        )
        self.metrics.append(metric)
        
        # Record latency
        latency_metric = PerformanceMetric(
            task_id=task_id,
            agent_id=agent_id,
            metric_name="latency",
            value=latency,
            metadata=metadata or {},
        )
        self.metrics.append(latency_metric)
        
        # Record quality if provided
        if quality_score is not None:
            quality_metric = PerformanceMetric(
                task_id=task_id,
                agent_id=agent_id,
                metric_name="quality",
                value=quality_score,
                metadata=metadata or {},
            )
            self.metrics.append(quality_metric)
        
        # Update running statistics
        self.agent_task_count[agent_id] += 1
        
        # Update success rate (exponential moving average)
        current_success = self.agent_success_rate.get(agent_id, 0.5)
        new_success = (1 - self.learning_rate) * current_success + self.learning_rate * (
            1.0 if success else 0.0
        )
        self.agent_success_rate[agent_id] = new_success
        
        # Update latency (exponential moving average)
        current_latency = self.agent_avg_latency.get(agent_id, latency)
        new_latency = (1 - self.learning_rate) * current_latency + self.learning_rate * latency
        self.agent_avg_latency[agent_id] = new_latency
        
        logger.info(
            f"Recorded performance - Agent: {agent_id}, Success: {success}, "
            f"Latency: {latency:.2f}s, Quality: {quality_score}"
        )
    
    async def adapt_temperature(self, agent_id: str) -> Optional[float]:
        """
        Adapt agent temperature based on performance.
        
        Lower temperature for consistently successful agents,
        higher for struggling agents (encourages exploration).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            New temperature value, or None if no adaptation needed
        """
        if agent_id not in self.agent_success_rate:
            return None
        
        success_rate = self.agent_success_rate[agent_id]
        current_temp = self.agent_temperatures.get(agent_id, 0.7)
        
        # If very successful, reduce temperature (exploit)
        if success_rate > 0.9:
            new_temp = max(0.1, current_temp * 0.95)
            
        # If struggling, increase temperature (explore)
        elif success_rate < 0.5:
            new_temp = min(1.0, current_temp * 1.05)
            
        # Moderate performance, small adjustment
        else:
            new_temp = current_temp
        
        # Only update if significant change
        if abs(new_temp - current_temp) > 0.01:
            update = LearningUpdate(
                update_id=f"temp_{agent_id}_{int(time.time())}",
                component="agent",
                parameter_name="temperature",
                old_value=current_temp,
                new_value=new_temp,
                reason=f"Success rate: {success_rate:.2%}",
                improvement=success_rate - 0.5,  # Relative to baseline
            )
            self.updates.append(update)
            self.agent_temperatures[agent_id] = new_temp
            
            logger.info(
                f"Adapted temperature for {agent_id}: {current_temp:.2f} → {new_temp:.2f} "
                f"(Success rate: {success_rate:.2%})"
            )
            
            return new_temp
        
        return None
    
    async def update_router_weights(
        self,
        task_type: str,
        agent_id: str,
        success: bool,
    ) -> Dict[str, float]:
        """
        Update Thompson Sampling weights based on outcome.
        
        Args:
            task_type: Type of task
            agent_id: Agent that handled it
            success: Whether it succeeded
            
        Returns:
            Updated weights (alpha, beta)
        """
        key = f"{task_type}:{agent_id}"
        weights = self.router_weights[key]
        
        # Update Beta distribution parameters
        if success:
            weights["alpha"] += 1
        else:
            weights["beta"] += 1
        
        logger.debug(
            f"Updated router weights for {key}: "
            f"α={weights['alpha']:.1f}, β={weights['beta']:.1f}"
        )
        
        return weights
    
    def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get performance statistics for an agent."""
        return {
            "agent_id": agent_id,
            "success_rate": self.agent_success_rate.get(agent_id, 0.0),
            "avg_latency": self.agent_avg_latency.get(agent_id, 0.0),
            "task_count": self.agent_task_count.get(agent_id, 0),
            "temperature": self.agent_temperatures.get(agent_id, 0.7),
        }
    
    def get_learning_report(self, limit: int = 10) -> Dict[str, Any]:
        """
        Generate learning progress report.
        
        Args:
            limit: Number of recent updates to include
            
        Returns:
            Report dictionary
        """
        recent_updates = sorted(
            self.updates,
            key=lambda u: u.timestamp,
            reverse=True,
        )[:limit]
        
        return {
            "total_metrics": len(self.metrics),
            "total_updates": len(self.updates),
            "agent_statistics": {
                agent_id: self.get_agent_statistics(agent_id)
                for agent_id in self.agent_success_rate.keys()
            },
            "recent_updates": [
                {
                    "component": u.component,
                    "parameter": u.parameter_name,
                    "old_value": u.old_value,
                    "new_value": u.new_value,
                    "reason": u.reason,
                    "improvement": u.improvement,
                }
                for u in recent_updates
            ],
        }
    
    async def periodic_optimization(self) -> None:
        """
        Periodic background task to optimize parameters.
        
        Run this every N minutes to analyze trends and adapt.
        """
        logger.info("Running periodic meta-learning optimization...")
        
        # Adapt temperatures for all agents
        for agent_id in list(self.agent_success_rate.keys()):
            await self.adapt_temperature(agent_id)
        
        # Log summary
        report = self.get_learning_report(limit=5)
        logger.info(
            f"Meta-learning summary: {len(self.metrics)} metrics, "
            f"{len(self.updates)} updates"
        )


# Global meta-learner instance
meta_learner = MetaLearner()
