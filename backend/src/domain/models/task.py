"""Task domain model."""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import DomainEntity


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(DomainEntity):
    """Task entity representing a unit of work."""

    description: str = Field(..., description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    
    # Assignment
    assigned_agent_id: Optional[UUID] = Field(None, description="ID of assigned agent")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task for hierarchical planning")
    
    # Execution details
    input_data: dict = Field(default_factory=dict, description="Task input data")
    output_data: Optional[dict] = Field(None, description="Task output/result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Metadata
    context: dict = Field(default_factory=dict, description="Execution context")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def __str__(self) -> str:
        """String representation."""
        return f"Task({self.id}, status={self.status.value}, priority={self.priority.value})"

    def assign_to(self, agent_id: UUID) -> None:
        """Assign task to an agent."""
        self.assigned_agent_id = agent_id
        self.status = TaskStatus.IN_PROGRESS

    def complete(self, output: dict) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.output_data = output

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error

    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
