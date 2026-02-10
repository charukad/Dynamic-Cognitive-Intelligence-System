"""
Metrics Collector Service

Core service for collecting agent execution metrics in real-time.
Records task lifecycle events and updates both PostgreSQL and Redis.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from src.domain.models.metrics import (
    AgentExecution,
    TournamentMatch,
    DreamCycle,
    TaskStatus,
    DreamType
)
from src.domain.interfaces.metrics_repository import (
    IMetricsRepository,
    IMetricsCacheRepository
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and persists agent execution metrics.
    
    Implements dual-write pattern: writes to both PostgreSQL (durable)
    and Redis (fast real-time access).
    """
    
    def __init__(
        self,
        repository: IMetricsRepository,
        cache: IMetricsCacheRepository
    ):
        self.repository = repository
        self.cache = cache
    
    # ========================================================================
    # Task Execution Tracking
    # ========================================================================
    
    async def record_task_start(
        self,
        agent_id: str,
        agent_name: str,
        task_id: str,
        task_type: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentExecution:
        """
        Record when an agent starts executing a task.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable agent name
            task_id: Unique identifier for the task
            task_type: Type/category of task
            input_data: Task input parameters
            metadata: Additional context
            
        Returns:
            Created AgentExecution instance
        """
        execution = AgentExecution(
            agent_id=agent_id,
            agent_name=agent_name,
            task_id=task_id,
            task_type=task_type,
            started_at=datetime.now(),
            input_data=input_data,
            metadata=metadata,
            status=TaskStatus.RUNNING
        )
        
        try:
            # Persist to database
            execution = await self.repository.create_execution(execution)
            
            # Mark agent as active in cache
            await self.cache.mark_agent_active(agent_id)
            
            logger.info(
                f"Task started: agent={agent_id}, task={task_id}, "
                f"execution_id={execution.id}"
            )
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to record task start: {e}", exc_info=True)
            raise
    
    async def record_task_completion(
        self,
        execution: AgentExecution,
        success: bool,
        output_data: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AgentExecution:
        """
        Record when an agent completes a task.
        
        Args:
            execution: The execution instance to complete
            success: Whether the task succeeded
            output_data: Task output/results
            error_type: Category of error if failed
            error_message: Detailed error message if failed
            
        Returns:
            Updated AgentExecution instance
        """
        # Calculate response time
        response_time_ms = execution.duration_ms or 0
        
        # Update execution model
        execution.mark_completed(
            success=success,
            response_time_ms=response_time_ms,
            output_data=output_data,
            error_type=error_type,
            error_message=error_message
        )
        
        try:
            # Update database
            execution = await self.repository.update_execution(execution)
            
            # Update Redis counters
            await self.cache.increment_task_counter(execution.agent_id, success)
            await self.cache.add_response_time(execution.agent_id, response_time_ms)
            
            logger.info(
                f"Task completed: agent={execution.agent_id}, "
                f"task={execution.task_id}, success={success}, "
                f"time={response_time_ms}ms"
            )
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to record task completion: {e}", exc_info=True)
            raise
    
    async def record_task_timeout(self, execution: AgentExecution) -> AgentExecution:
        """
        Record when a task times out.
        
        Args:
            execution: The execution instance that timed out
            
        Returns:
            Updated AgentExecution instance
        """
        execution.mark_timeout()
        
        try:
            execution = await self.repository.update_execution(execution)
            await self.cache.increment_task_counter(execution.agent_id, success=False)
            
            logger.warning(
                f"Task timeout: agent={execution.agent_id}, "
                f"task={execution.task_id}"
            )
            
            return execution
            
        except Exception as e:
            logger.error(f"Failed to record task timeout: {e}", exc_info=True)
            raise
    
    # ========================================================================
    # Tournament Match Recording
    # ========================================================================
    
    async def record_match_start(
        self,
        tournament_id: str,
        round_number: int,
        agent1_id: str,
        agent2_id: str,
        match_type: str = "standard"
    ) -> TournamentMatch:
        """
        Record the start of a tournament match.
        
        Args:
            tournament_id: Tournament identifier
            round_number: Round number in tournament
            agent1_id: First participant
            agent2_id: Second participant
            match_type: Type of match
            
        Returns:
            Created TournamentMatch instance
        """
        # Get current ELO ratings from cache
        agent1_elo = await self.cache.get_elo_rating(agent1_id)
        agent2_elo = await self.cache.get_elo_rating(agent2_id)
        
        match = TournamentMatch(
            tournament_id=tournament_id,
            round_number=round_number,
            agent1_id=agent1_id,
            agent2_id=agent2_id,
            agent1_elo_before=agent1_elo,
            agent2_elo_before=agent2_elo,
            started_at=datetime.now(),
            match_type=match_type
        )
        
        try:
            match = await self.repository.create_match(match)
            logger.info(
                f"Match started: {agent1_id} vs {agent2_id}, "
                f"tournament={tournament_id}"
            )
            return match
            
        except Exception as e:
            logger.error(f"Failed to record match start: {e}", exc_info=True)
            raise
    
    async def record_match_outcome(
        self,
        match: TournamentMatch,
        winner_id: Optional[str],
        loser_id: Optional[str],
        score_agent1: float,
        score_agent2: float,
        agent1_elo_after: int,
        agent2_elo_after: int,
        is_draw: bool = False
    ) -> TournamentMatch:
        """
        Record the outcome of a tournament match with ELO updates.
        
        Args:
            match: The match instance
            winner_id: ID of winning agent (None if draw)
            loser_id: ID of losing agent (None if draw)
            score_agent1: Score for agent 1
            score_agent2: Score for agent 2
            agent1_elo_after: New ELO for agent 1
            agent2_elo_after: New ELO for agent 2
            is_draw: Whether the match was a draw
            
        Returns:
            Updated TournamentMatch instance
        """
        match.record_outcome(
            winner_id=winner_id,
            loser_id=loser_id,
            score_agent1=score_agent1,
            score_agent2=score_agent2,
            agent1_elo_after=agent1_elo_after,
            agent2_elo_after=agent2_elo_after,
            is_draw=is_draw
        )
        
        try:
            # Update database
            match = await self.repository.create_match(match)
            
            # Update ELO ratings in cache
            await self.cache.set_elo_rating(match.agent1_id, agent1_elo_after)
            await self.cache.set_elo_rating(match.agent2_id, agent2_elo_after)
            
            logger.info(
                f"Match completed: winner={winner_id}, "
                f"elo_change={match.elo_change}"
            )
            
            return match
            
        except Exception as e:
            logger.error(f"Failed to record match outcome: {e}", exc_info=True)
            raise
    
    #========================================================================
    # Dream Cycle Recording
    # ========================================================================
    
    async def record_dream_start(
        self,
        agent_id: str,
        dream_type: DreamType,
        cycle_number: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DreamCycle:
        """
        Record the start of a dream cycle.
        
        Args:
            agent_id: Agent performing the dream
            dream_type: Type of dream cycle
            cycle_number: Sequential cycle number
            metadata: Additional context
            
        Returns:
            Created DreamCycle instance
        """
        dream = DreamCycle(
            agent_id=agent_id,
            dream_type=dream_type,
            cycle_number=cycle_number,
            started_at=datetime.now(),
            metadata=metadata
        )
        
        try:
            dream = await self.repository.create_dream_cycle(dream)
            logger.info(
                f"Dream started: agent={agent_id}, type={dream_type}, "
                f"cycle={cycle_number}"
            )
            return dream
            
        except Exception as e:
            logger.error(f"Failed to record dream start: {e}", exc_info=True)
            raise
    
    async def record_dream_completion(
        self,
        dream: DreamCycle,
        insights_generated: int,
        patterns_discovered: int,
        knowledge_consolidated: bool,
        coherence_score: float,
        novelty_score: float,
        utility_score: float,
        dream_narrative: Optional[str] = None,
        insights: Optional[Dict[str, Any]] = None
    ) -> DreamCycle:
        """
        Record the completion of a dream cycle.
        
        Args:
            dream: The dream cycle instance
            insights_generated: Number of insights produced
            patterns_discovered: Number of patterns found
            knowledge_consolidated: Whether knowledge was consolidated
            coherence_score: Coherence quality score (0-1)
            novelty_score: Novelty quality score (0-1)
            utility_score: Utility quality score (0-1)
            dream_narrative: Optional narrative description
            insights: Dictionary of insights data
            
        Returns:
            Updated DreamCycle instance
        """
        dream.complete_cycle(
            insights_generated=insights_generated,
            patterns_discovered=patterns_discovered,
            knowledge_consolidated=knowledge_consolidated,
            coherence_score=coherence_score,
            novelty_score=novelty_score,
            utility_score=utility_score,
            dream_narrative=dream_narrative,
            insights=insights
        )
        
        try:
            # Update database
            dream = await self.repository.create_dream_cycle(dream)
            
            # Update cache counters
            await self.cache.increment_dream_counter(dream.agent_id)
            await self.cache.increment_insight_counter(
                dream.agent_id,
                insights_generated
            )
            
            logger.info(
                f"Dream completed: agent={dream.agent_id}, "
                f"insights={insights_generated}, "
                f"avg_quality={dream.avg_quality_score:.2f}"
            )
            
            return dream
            
        except Exception as e:
            logger.error(f"Failed to record dream completion: {e}", exc_info=True)
            raise


# Global singleton instance (will be initialized by dependency injection)
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    if _metrics_collector is None:
        raise RuntimeError("MetricsCollector not initialized")
    return _metrics_collector


def initialize_metrics_collector(
    repository: IMetricsRepository,
    cache: IMetricsCacheRepository
) -> MetricsCollector:
    """Initialize the global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(repository, cache)
    return _metrics_collector
