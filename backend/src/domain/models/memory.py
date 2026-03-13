"""Memory domain model."""

from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from .base import DomainEntity


class MemoryType(str, Enum):
    """Types of memory in the system."""

    EPISODIC = "episodic"  # Specific events/interactions
    SEMANTIC = "semantic"  # General knowledge/facts
    PROCEDURAL = "procedural"  # How-to knowledge/patterns
    WORKING = "working"  # Short-term context


class Memory(DomainEntity):
    """Memory entity for storing agent memories."""

    # Backward compatibility: allow both UUID and string IDs.
    id: str | UUID = Field(default_factory=uuid4)
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content")
    embedding: Optional[list[float]] = Field(None, description="Vector embedding")
    
    # Context
    agent_id: Optional[str | UUID] = Field(None, description="Associated agent ID")
    task_id: Optional[str | UUID] = Field(None, description="Associated task ID")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Importance and relevance
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    access_count: int = Field(default=0, description="Number of times accessed")
    
    # Metadata
    tags: list[str] = Field(default_factory=list, description="Memory tags")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, values):
        """Backwards compatibility for `type` and `importance` fields."""
        if not isinstance(values, dict):
            return values

        if "memory_type" not in values and "type" in values:
            values["memory_type"] = values["type"]
        if "importance_score" not in values and "importance" in values:
            values["importance_score"] = values["importance"]
        return values

    def __str__(self) -> str:
        """String representation."""
        return f"Memory({self.memory_type.value}, importance={self.importance_score:.2f})"

    @property
    def type(self) -> MemoryType:
        """Legacy alias for memory_type."""
        return self.memory_type

    @type.setter
    def type(self, value: MemoryType) -> None:
        """Legacy alias setter for memory_type."""
        self.memory_type = MemoryType(value)

    @property
    def importance(self) -> float:
        """Legacy alias for importance_score."""
        return self.importance_score

    @importance.setter
    def importance(self, value: float) -> None:
        """Legacy alias setter for importance_score."""
        self.importance_score = max(0.0, min(1.0, value))

    def mark_accessed(self) -> None:
        """Increment access count."""
        self.access_count += 1

    def update_importance(self, score: float) -> None:
        """Update importance score."""
        self.importance_score = max(0.0, min(1.0, score))
