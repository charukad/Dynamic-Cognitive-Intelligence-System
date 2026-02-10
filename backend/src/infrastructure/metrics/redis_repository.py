"""
Redis Cache Repository Implementation

Provides fast, in-memory caching for real-time metrics using Redis.
"""

from typing import List, Optional, Dict
import json
import logging

from src.domain.interfaces.metrics_repository import IMetricsCacheRepository
from src.infrastructure.database.redis_client import redis_client

logger = logging.getLogger(__name__)


class RedisCacheRepository(IMetricsCacheRepository):
    """
    Redis implementation of metrics cache repository.
    
    Stores real-time counters, moving averages, and current ratings
    for immediate dashboard access.
    
    NOTE: Using in-memory fallback until Redis is fully configured.
    """
    
    def __init__(self):
        self.redis = redis_client
        # In-memory fallback for demo purposes
        self._memory_cache: Dict[str, any] = {}
        self._active_agents = {"data-analyst", "designer", "financial", "translator"}
    
    # ========================================================================
    # Task Counters
    # ========================================================================
    
    async def increment_task_counter(self, agent_id: str, success: bool) -> None:
        """Increment task counters for an agent"""
        try:
            key = f"agent:{agent_id}:metrics"
            if key not in self._memory_cache:
                self._memory_cache[key] = {"total_tasks": 0, "successful_tasks": 0, "failed_tasks": 0}
            
            self._memory_cache[key]["total_tasks"] += 1
            if success:
                self._memory_cache[key]["successful_tasks"] += 1
            else:
                self._memory_cache[key]["failed_tasks"] += 1
                
        except Exception as e:
            logger.error(f"Failed to increment task counter: {e}")
    
    async def get_task_counts(self, agent_id: str) -> dict:
        """Get current task counts from cache"""
        try:
            key = f"agent:{agent_id}:metrics"
            return self._memory_cache.get(key, {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0
            })
        except Exception as e:
            logger.error(f"Failed to get task counts: {e}")
            return {"total_tasks": 0, "successful_tasks": 0, "failed_tasks": 0}
    
    # ========================================================================
    # Response Time Tracking
    # ========================================================================
    
    async def add_response_time(
        self,
        agent_id: str,
        response_time_ms: int,
        max_samples: int = 100
    ) -> None:
        """Add response time to moving average"""
        try:
            key = f"agent:{agent_id}:response_times"
            if key not in self._memory_cache:
                self._memory_cache[key] = []
            
            self._memory_cache[key].insert(0, response_time_ms)
            self._memory_cache[key] = self._memory_cache[key][:max_samples]
            
        except Exception as e:
            logger.error(f"Failed to add response time: {e}")
    
    async def get_avg_response_time(self, agent_id: str) -> Optional[int]:
        """Get average response time from cached samples"""
        try:
            key = f"agent:{agent_id}:response_times"
            response_times = self._memory_cache.get(key, [])
            
            if not response_times:
                return None
            
            return sum(response_times) // len(response_times)
            
        except Exception as e:
            logger.error(f"Failed to get avg response time: {e}")
            return None
    
    # ========================================================================
    # ELO Rating
    # ========================================================================
    
    async def get_elo_rating(self, agent_id: str) -> int:
        """Get current ELO rating"""
        try:
            key = f"agent:{agent_id}:elo"
            return self._memory_cache.get(key, 1500)
        except Exception as e:
            logger.error(f"Failed to get ELO rating: {e}")
            return 1500
    
    async def set_elo_rating(self, agent_id: str, elo: int) -> None:
        """Update ELO rating"""
        try:
            key = f"agent:{agent_id}:elo"
            self._memory_cache[key] = elo
        except Exception as e:
            logger.error(f"Failed to set ELO rating: {e}")
    
    # ========================================================================
    # Dream and Insight Counters
    # ========================================================================
    
    async def increment_dream_counter(self, agent_id: str) -> None:
        """Increment dream cycle counter"""
        try:
            key = f"agent:{agent_id}:metrics"
            if key not in self._memory_cache:
                self._memory_cache[key] = {}
            if "dream_cycles" not in self._memory_cache[key]:
                self._memory_cache[key]["dream_cycles"] = 0
            self._memory_cache[key]["dream_cycles"] += 1
        except Exception as e:
            logger.error(f"Failed to increment dream counter: {e}")
    
    async def increment_insight_counter(self, agent_id: str, count: int = 1) -> None:
        """Increment insights generated counter"""
        try:
            key = f"agent:{agent_id}:metrics"
            if key not in self._memory_cache:
                self._memory_cache[key] = {}
            if "insights" not in self._memory_cache[key]:
                self._memory_cache[key]["insights"] = 0
            self._memory_cache[key]["insights"] += count
        except Exception as e:
            logger.error(f"Failed to increment insight counter: {e}")
    
    # ========================================================================
    # Agent Management
    # ========================================================================
    
    async def get_active_agents(self) -> List[str]:
        """Get list of all active agent IDs"""
        try:
            return list(self._active_agents)
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            return []
    
    async def mark_agent_active(self, agent_id: str) -> None:
        """Add agent to active set"""
        try:
            self._active_agents.add(agent_id)
        except Exception as e:
            logger.error(f"Failed to mark agent active: {e}")


# Global singleton instance
_redis_cache_instance: Optional[RedisCacheRepository] = None


async def get_cache_repository() -> RedisCacheRepository:
    """Get Redis cache repository instance (Singleton)"""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCacheRepository()
    return _redis_cache_instance

