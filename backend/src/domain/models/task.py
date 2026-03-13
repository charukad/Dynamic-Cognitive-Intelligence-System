"""Task domain model."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import Field, model_validator

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

    # Backward compatibility: allow both UUID and string IDs.
    id: str | UUID = Field(default_factory=uuid4)
    title: Optional[str] = Field(None, description="Task title")
    description: str = Field(..., description="Task description")
    task_type: Optional[str] = Field(None, description="Task classification/type")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    priority: TaskPriority | int = Field(default=TaskPriority.MEDIUM, description="Task priority")
    
    # Assignment
    assigned_agent_id: Optional[str | UUID] = Field(None, description="ID of assigned agent")
    parent_task_id: Optional[str | UUID] = Field(None, description="Parent task for hierarchical planning")
    
    # Execution details
    input_data: dict = Field(default_factory=dict, description="Task input data")
    output_data: Optional[Any] = Field(None, description="Task output/result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    
    # Metadata
    context: dict = Field(default_factory=dict, description="Execution context")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="before")
    @classmethod
    def normalize_priority(cls, values):
        """Accept legacy integer/string priority values and aliases."""
        if not isinstance(values, dict):
            return values

        priority = values.get("priority")
        if isinstance(priority, str):
            if priority.isdigit():
                values["priority"] = int(priority)
            else:
                normalized = priority.lower()
                enum_values = {item.value for item in TaskPriority}
                if normalized in enum_values:
                    values["priority"] = TaskPriority(normalized)

        if "output_data" not in values and "result" in values:
            values["output_data"] = values["result"]
        return values

    def __str__(self) -> str:
        """String representation."""
        priority = self.priority.value if isinstance(self.priority, TaskPriority) else self.priority
        return f"Task({self.id}, status={self.status.value}, priority={priority})"

    def assign_to(self, agent_id: str | UUID) -> None:
        """Assign task to an agent."""
        self.assigned_agent_id = agent_id
        self.status = TaskStatus.IN_PROGRESS

    def complete(self, output: Any) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.utcnow()

    def mark_completed(self, output: Any) -> None:
        """Backward-compatible alias for complete()."""
        self.complete(output)

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error

    def mark_failed(self, error: str) -> None:
        """Backward-compatible alias for fail()."""
        self.fail(error)

    @property
    def result(self) -> Optional[Any]:
        """Backward-compatible alias for output_data."""
        return self.output_data

    @result.setter
    def result(self, value: Optional[Any]) -> None:
        """Backward-compatible alias setter for output_data."""
        self.output_data = value

    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
