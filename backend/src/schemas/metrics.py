"""Metrics schemas."""

from typing import List
from pydantic import BaseModel, Field

class AgentMetrics(BaseModel):
    """Metrics for a single agent."""
    agent_id: str
    name: str
    total_tasks: int
    success_rate: float
    avg_response_time: float
    elo_rating: int
    dream_cycles: int
    insights_generated: int
    matches_won: int
    matches_lost: int

class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    agents: List[AgentMetrics]
