"""
Metrics Domain Models

Core domain models for the metrics system following DDD principles.
These models represent the business concepts of agent execution tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from uuid import uuid4


class TaskStatus(str, Enum):
    """Status of a task execution"""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DreamType(str, Enum):
    """Type of dream cycle"""
    EXPLORATION = "exploration"
    CONSOLIDATION = "consolidation"
    INNOVATION = "innovation"
    REFLECTION = "reflection"


@dataclass
class AgentExecution:
    """
    Domain model for agent task execution.
    
    Represents a single task executed by an agent with complete
    lifecycle tracking from start to completion.
    """
    agent_id: str
    agent_name: str
    task_id: str
    started_at: datetime
    task_type: Optional[str] = None
    completed_at: Optional[datetime] = None
    response_time_ms: Optional[int] = None
    status: TaskStatus = TaskStatus.RUNNING
    success: Optional[bool] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def mark_completed(
        self,
        success: bool,
        response_time_ms: int,
        output_data: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Mark the execution as completed with outcome"""
        self.completed_at = datetime.now()
        self.success = success
        self.response_time_ms = response_time_ms
        self.status = TaskStatus.SUCCESS if success else TaskStatus.FAILED
        self.output_data = output_data
        self.error_type = error_type
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def mark_timeout(self) -> None:
        """Mark the execution as timed out"""
        self.completed_at = datetime.now()
        self.success = False
        self.status = TaskStatus.TIMEOUT
        self.error_type = "timeout"
        self.updated_at = datetime.now()
    
    @property
    def is_completed(self) -> bool:
        """Check if execution has completed"""
        return self.completed_at is not None
    
    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate duration in milliseconds"""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None


@dataclass
class AgentMetricsSnapshot:
    """
    Pre-aggregated metrics snapshot for an agent.
    
    Contains compiled statistics for a specific point in time,
    optimized for fast dashboard queries.
    """
    agent_id: str
    snapshot_time: datetime
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: int = 0
    p50_response_time_ms: int = 0
    p95_response_time_ms: int = 0
    p99_response_time_ms: int = 0
    elo_rating: int = 1500
    dream_cycles_completed: int = 0
    insights_generated: int = 0
    knowledge_nodes_created: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    matches_drawn: int = 0
    id: Optional[int] = None
    
    @property
    def total_matches(self) -> int:
        """Total tournament matches played"""
        return self.matches_won + self.matches_lost + self.matches_drawn
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        total = self.total_matches
        return (self.matches_won / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "agent_id": self.agent_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": round(self.success_rate, 2),
            "avg_response_time_ms": self.avg_response_time_ms,
            "p50_response_time_ms": self.p50_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "p99_response_time_ms": self.p99_response_time_ms,
            "elo_rating": self.elo_rating,
            "dream_cycles_completed": self.dream_cycles_completed,
            "insights_generated": self.insights_generated,
            "knowledge_nodes_created": self.knowledge_nodes_created,
            "matches_won": self.matches_won,
            "matches_lost": self.matches_lost,
            "matches_drawn": self.matches_drawn,
            "win_rate": round(self.win_rate, 2),
        }


@dataclass
class TournamentMatch:
    """
    Tournament match record for ELO tracking.
    
    Records a competitive match between two agents including
    ELO rating changes and outcomes.
    """
    agent1_id: str
    agent2_id: str
    started_at: datetime
    agent1_elo_before: int
    agent2_elo_before: int
    tournament_id: Optional[str] = None
    round_number: Optional[int] = None
    winner_id: Optional[str] = None
    loser_id: Optional[str] = None
    is_draw: bool = False
    score_agent1: Optional[float] = None
    score_agent2: Optional[float] = None
    agent1_elo_after: Optional[int] = None
    agent2_elo_after: Optional[int] = None
    elo_change: Optional[int] = None
    completed_at: Optional[datetime] = None
    match_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def record_outcome(
        self,
        winner_id: Optional[str],
        loser_id: Optional[str],
        score_agent1: float,
        score_agent2: float,
        agent1_elo_after: int,
        agent2_elo_after: int,
        is_draw: bool = False
    ) -> None:
        """Record the match outcome and ELO changes"""
        self.completed_at = datetime.now()
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.is_draw = is_draw
        self.score_agent1 = score_agent1
        self.score_agent2 = score_agent2
        self.agent1_elo_after = agent1_elo_after
        self.agent2_elo_after = agent2_elo_after
        
        # Calculate ELO change (positive for winner)
        if winner_id == self.agent1_id:
            self.elo_change = agent1_elo_after - self.agent1_elo_before
        elif winner_id == self.agent2_id:
            self.elo_change = agent2_elo_after - self.agent2_elo_before
        else:
            self.elo_change = 0
    
    @property
    def is_completed(self) -> bool:
        """Check if match is completed"""
        return self.completed_at is not None


@dataclass
class DreamCycle:
    """
    Oneiroi dream cycle record.
    
    Tracks a complete dream cycle including insights generated
    and quality metrics.
    """
    agent_id: str
    dream_type: DreamType
    cycle_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    insights_generated: int = 0
    patterns_discovered: int = 0
    knowledge_consolidated: bool = False
    coherence_score: Optional[float] = None
    novelty_score: Optional[float] = None
    utility_score: Optional[float] = None
    dream_narrative: Optional[str] = None
    insights: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def complete_cycle(
        self,
        insights_generated: int,
        patterns_discovered: int,
        knowledge_consolidated: bool,
        coherence_score: float,
        novelty_score: float,
        utility_score: float,
        dream_narrative: Optional[str] = None,
        insights: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark the dream cycle as completed"""
        self.completed_at = datetime.now()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        self.insights_generated = insights_generated
        self.patterns_discovered = patterns_discovered
        self.knowledge_consolidated = knowledge_consolidated
        self.coherence_score = coherence_score
        self.novelty_score = novelty_score
        self.utility_score = utility_score
        self.dream_narrative = dream_narrative
        self.insights = insights
    
    @property
    def is_completed(self) -> bool:
        """Check if dream cycle is completed"""
        return self.completed_at is not None
    
    @property
    def avg_quality_score(self) -> Optional[float]:
        """Calculate average quality score across all metrics"""
        if all(score is not None for score in [self.coherence_score, self.novelty_score, self.utility_score]):
            return (self.coherence_score + self.novelty_score + self.utility_score) / 3
        return None
