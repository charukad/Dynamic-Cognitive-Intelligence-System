"""
Metrics Aggregator Service

Aggregates and computes metrics from raw execution data.
Provides real-time and historical metrics for dashboards.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from statistics import median, mean
import math
import logging

from src.domain.models.metrics import AgentMetricsSnapshot
from src.domain.interfaces.metrics_repository import (
    IMetricsRepository,
    IMetricsCacheRepository
)

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """
    Aggregates metrics from execution data.
    
    Computes real-time metrics from Redis cache and historical
    aggregations from PostgreSQL.
    """
    
    AGENT_NAMES = {
        "data-analyst": "Data Analyst",
        "designer": "Designer",
        "financial": "Financial Advisor",
        "translator": "Translator"
    }
    
    def __init__(
        self,
        repository: IMetricsRepository,
        cache: IMetricsCacheRepository
    ):
        self.repository = repository
        self.cache = cache
    
    async def get_agent_metrics(self, agent_id: str) -> AgentMetricsSnapshot:
        """
        Get current metrics for a specific agent.
        
        Combines real-time data from Redis with latest snapshot from PostgreSQL.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current metrics snapshot
        """
        try:
            # Get task counts from cache
            counts = await self.cache.get_task_counts(agent_id)
            total_tasks = counts.get("total_tasks", 0)
            successful_tasks = counts.get("successful_tasks", 0)
            failed_tasks = counts.get("failed_tasks", 0)
            
            # Calculate success rate
            success_rate = (
                (successful_tasks / total_tasks * 100)
                if total_tasks > 0 else 0.0
            )
            
            # Get response time metrics
            avg_response_time = await self.cache.get_avg_response_time(agent_id) or 0
            
            # Get percentiles from recent executions
            recent_executions = await self.repository.get_executions_by_agent(
                agent_id=agent_id,
                start_time=datetime.now() - timedelta(hours=1),
                limit=100
            )
            
            response_times = [
                e.response_time_ms for e in recent_executions
                if e.response_time_ms is not None
            ]
            
            p50 = int(self._calculate_percentile(response_times, 50)) if response_times else 0
            p95 = int(self._calculate_percentile(response_times, 95)) if response_times else 0
            p99 = int(self._calculate_percentile(response_times, 99)) if response_times else 0
            
            # Get ELO rating
            elo_rating = await self.cache.get_elo_rating(agent_id)
            
            # Get latest snapshot for advanced metrics
            latest_snapshot = await self.repository.get_latest_snapshot(agent_id)
            
            # Create combined snapshot
            snapshot = AgentMetricsSnapshot(
                agent_id=agent_id,
                snapshot_time=datetime.now(),
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                success_rate=success_rate,
                avg_response_time_ms=avg_response_time,
                p50_response_time_ms=p50,
                p95_response_time_ms=p95,
                p99_response_time_ms=p99,
                elo_rating=elo_rating,
                dream_cycles_completed=(
                    latest_snapshot.dream_cycles_completed if latest_snapshot else 0
                ),
                insights_generated=(
                    latest_snapshot.insights_generated if latest_snapshot else 0
                ),
                knowledge_nodes_created=(
                    latest_snapshot.knowledge_nodes_created if latest_snapshot else 0
                ),
                matches_won=latest_snapshot.matches_won if latest_snapshot else 0,
                matches_lost=latest_snapshot.matches_lost if latest_snapshot else 0,
                matches_drawn=latest_snapshot.matches_drawn if latest_snapshot else 0,
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics for {agent_id}: {e}", exc_info=True)
            # Return default snapshot on error
            return AgentMetricsSnapshot(
                agent_id=agent_id,
                snapshot_time=datetime.now()
            )
    
    async def get_all_agents_metrics(self) -> List[Dict[str, Any]]:
        """
        Get current metrics for all active agents.
        
        Returns:
            List of metrics dictionaries for API response
        """
        try:
            active_agents = await self.cache.get_active_agents()
            
            # If no active agents in cache, use default list
            if not active_agents:
                active_agents = list(self.AGENT_NAMES.keys())
            
            metrics_list = []
            for agent_id in active_agents:
                snapshot = await self.get_agent_metrics(agent_id)
                
                # Convert to API-friendly dictionary
                metrics_dict = {
                    "agent_id": agent_id,
                    "name": self.AGENT_NAMES.get(agent_id, agent_id.title()),
                    "total_tasks": snapshot.total_tasks,
                    "success_rate": round(snapshot.success_rate, 2),
                    "avg_response_time": snapshot.avg_response_time_ms,
                    "elo_rating": snapshot.elo_rating,
                    "dream_cycles": snapshot.dream_cycles_completed,
                    "insights_generated": snapshot.insights_generated,
                    "matches_won": snapshot.matches_won,
                    "matches_lost": snapshot.matches_lost,
                }
                
                metrics_list.append(metrics_dict)
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Failed to get all agents metrics: {e}", exc_info=True)
            return []
    
    async def create_snapshot(self, agent_id: str) -> AgentMetricsSnapshot:
        """
        Create and persist a metrics snapshot.
        
        Used for periodic snapshot creation (e.g., every hour).
        
        Args:
            agent_id: Agent to snapshot
            
        Returns:
            Created snapshot
        """
        snapshot = await self.get_agent_metrics(agent_id)
        
        try:
            snapshot = await self.repository.create_snapshot(snapshot)
            logger.info(f"Created snapshot for agent {agent_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}", exc_info=True)
            raise
    
    async def get_performance_history(
        self,
        agent_id: str,
        time_range: str = "24h"
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance data for an agent.
        
        Args:
            agent_id: Agent identifier
            time_range: Time range (e.g., "1h", "24h", "7d")
            
        Returns:
            List of historical data points
        """
        # Parse time range
        hours = self._parse_time_range(time_range)
        start_time = datetime.now() - timedelta(hours=hours)
        
        try:
            snapshots = await self.repository.get_snapshots_in_range(
                agent_id=agent_id,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            history = [
                {
                    "timestamp": snap.snapshot_time.isoformat(),
                    "success_rate": snap.success_rate,
                    "avg_response_time": snap.avg_response_time_ms,
                    "elo_rating": snap.elo_rating,
                    "total_tasks": snap.total_tasks,
                }
                for snap in snapshots
            ]
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get performance history: {e}", exc_info=True)
            return []
    
    def _calculate_percentile(self, values: List[int], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_values[int(k)]
        
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to hours"""
        mapping = {
            "1h": 1,
            "6h": 6,
            "24h": 24,
            "7d": 168,
            "30d": 720,
        }
        return mapping.get(time_range, 24)


# Global singleton
_metrics_aggregator: Optional[MetricsAggregator] = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get the global metrics aggregator instance"""
    if _metrics_aggregator is None:
        raise RuntimeError("MetricsAggregator not initialized")
    return _metrics_aggregator


def initialize_metrics_aggregator(
    repository: IMetricsRepository,
    cache: IMetricsCacheRepository
) -> MetricsAggregator:
    """Initialize the global metrics aggregator"""
    global _metrics_aggregator
    _metrics_aggregator = MetricsAggregator(repository, cache)
    return _metrics_aggregator
