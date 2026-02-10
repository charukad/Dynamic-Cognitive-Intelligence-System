"""Memory domain model."""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import DomainEntity


class MemoryType(str, Enum):
    """Types of memory in the system."""

    EPISODIC = "episodic"  # Specific events/interactions
    SEMANTIC = "semantic"  # General knowledge/facts
    PROCEDURAL = "procedural"  # How-to knowledge/patterns
    WORKING = "working"  # Short-term context


class Memory(DomainEntity):
    """Memory entity for storing agent memories."""

    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content")
    embedding: Optional[list[float]] = Field(None, description="Vector embedding")
    
    # Context
    agent_id: Optional[UUID] = Field(None, description="Associated agent ID")
    task_id: Optional[UUID] = Field(None, description="Associated task ID")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Importance and relevance
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    access_count: int = Field(default=0, description="Number of times accessed")
    
    # Metadata
    tags: list[str] = Field(default_factory=list, description="Memory tags")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def __str__(self) -> str:
        """String representation."""
        return f"Memory({self.memory_type.value}, importance={self.importance_score:.2f})"

    def mark_accessed(self) -> None:
        """Increment access count."""
        self.access_count += 1

    def update_importance(self, score: float) -> None:
        """Update importance score."""
        self.importance_score = max(0.0, min(1.0, score))
