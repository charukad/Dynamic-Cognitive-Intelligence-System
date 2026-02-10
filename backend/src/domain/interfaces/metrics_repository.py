"""
Metrics Repository Interface

Defines the contract for metrics data persistence following
the Repository pattern for clean architecture separation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from src.domain.models.metrics import (
    AgentExecution,
    AgentMetricsSnapshot,
    TournamentMatch,
    DreamCycle,
    TaskStatus
)


class IMetricsRepository(ABC):
    """
    Repository interface for metrics persistence.
    
    Abstracts data access layer to allow switching between
    PostgreSQL, Redis, or other storage backends.
    """
    
    # ========================================================================
    # Agent Execution Methods
    # ========================================================================
    
    @abstractmethod
    async def create_execution(self, execution: AgentExecution) -> AgentExecution:
        """
        Create a new execution record.
        
        Args:
            execution: AgentExecution domain model
            
        Returns:
            Created execution with generated ID
        """
        pass
    
    @abstractmethod
    async def update_execution(self, execution: AgentExecution) -> AgentExecution:
        """
        Update an existing execution record.
        
        Args:
            execution: AgentExecution with updated fields
            
        Returns:
            Updated execution
        """
        pass
    
    @abstractmethod
    async def get_execution_by_id(self, execution_id: str) -> Optional[AgentExecution]:
        """Get execution by ID"""
        pass
    
    @abstractmethod
    async def get_executions_by_agent(
        self,
        agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[AgentExecution]:
        """
        Get executions for a specific agent with optional filters.
        
        Args:
            agent_id: Agent identifier
            start_time: Filter for executions after this time
            end_time: Filter for executions before this time
            status: Filter by execution status
            limit: Maximum number of results
            
        Returns:
            List of matching executions
        """
        pass
    
    @abstractmethod
    async def get_running_executions(self, agent_id: str) -> List[AgentExecution]:
        """Get all currently running executions for an agent"""
        pass
    
    # ========================================================================
    # Metrics Snapshot Methods
    # ========================================================================
    
    @abstractmethod
    async def create_snapshot(self, snapshot: AgentMetricsSnapshot) -> AgentMetricsSnapshot:
        """Create a metrics snapshot"""
        pass
    
    @abstractmethod
    async def get_latest_snapshot(self, agent_id: str) -> Optional[AgentMetricsSnapshot]:
        """Get the most recent snapshot for an agent"""
        pass
    
    @abstractmethod
    async def get_snapshots_in_range(
        self,
        agent_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[AgentMetricsSnapshot]:
        """Get all snapshots within a time range"""
        pass
    
    @abstractmethod
    async def get_all_latest_snapshots(self) -> List[AgentMetricsSnapshot]:
        """Get the latest snapshot for each agent"""
        pass
    
    # ========================================================================
    # Tournament Match Methods
    # ========================================================================
    
    @abstractmethod
    async def create_match(self, match: TournamentMatch) -> TournamentMatch:
        """Record a tournament match"""
        pass
    
    @abstractmethod
    async def get_matches_by_agent(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[TournamentMatch]:
        """Get match history for an agent"""
        pass
    
    @abstractmethod
    async def get_match_by_id(self, match_id: str) -> Optional[TournamentMatch]:
        """Get a specific match by ID"""
        pass
    
    @abstractmethod
    async def get_tournament_matches(
        self,
        tournament_id: str
    ) -> List[TournamentMatch]:
        """Get all matches in a tournament"""
        pass
    
    # ========================================================================
    # Dream Cycle Methods
    # ========================================================================
    
    @abstractmethod
    async def create_dream_cycle(self, dream: DreamCycle) -> DreamCycle:
        """Record a dream cycle"""
        pass
    
    @abstractmethod
    async def get_dream_cycles_by_agent(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[DreamCycle]:
        """Get dream cycles for an agent"""
        pass
    
    @abstractmethod
    async def get_dream_cycle_by_id(self, dream_id: str) -> Optional[DreamCycle]:
        """Get a specific dream cycle by ID"""
        pass


class IMetricsCacheRepository(ABC):
    """
    Cache repository for real-time metrics using Redis.
    
    Provides fast access to current metrics and moving averages.
    """
    
    @abstractmethod
    async def increment_task_counter(
        self,
        agent_id: str,
        success: bool
    ) -> None:
        """Increment task counters for an agent"""
        pass
    
    @abstractmethod
    async def add_response_time(
        self,
        agent_id: str,
        response_time_ms: int,
        max_samples: int = 100
    ) -> None:
        """Add response time to moving average"""
        pass
    
    @abstractmethod
    async def get_task_counts(self, agent_id: str) -> dict:
        """Get current task counts from cache"""
        pass
    
    @abstractmethod
    async def get_avg_response_time(self, agent_id: str) -> Optional[int]:
        """Get average response time from cached samples"""
        pass
    
    @abstractmethod
    async def get_elo_rating(self, agent_id: str) -> int:
        """Get current ELO rating"""
        pass
    
    @abstractmethod
    async def set_elo_rating(self, agent_id: str, elo: int) -> None:
        """Update ELO rating"""
        pass
    
    @abstractmethod
    async def increment_dream_counter(self, agent_id: str) -> None:
        """Increment dream cycle counter"""
        pass
    
    @abstractmethod
    async def increment_insight_counter(self, agent_id: str, count: int = 1) -> None:
        """Increment insights generated counter"""
        pass
    
    @abstractmethod
    async def get_active_agents(self) -> List[str]:
        """Get list of all active agent IDs"""
        pass
    
    @abstractmethod
    async def mark_agent_active(self, agent_id: str) -> None:
        """Add agent to active set"""
        pass
