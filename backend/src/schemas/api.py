"""Request and response schemas for API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Agent Schemas
class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    system_prompt: str = Field(..., min_length=1, description="System prompt")
    model_name: str = Field(default="default", description="LLM model")
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")  # ✅ NEW
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    system_prompt: Optional[str] = Field(None, min_length=1)
    model_name: Optional[str] = None
    status: Optional[str] = None
    capabilities: Optional[list[str]] = None  # ✅ NEW
    metadata: Optional[dict] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: UUID
    name: str
    agent_type: str
    temperature: float
    system_prompt: str
    model_name: str
    status: str
    capabilities: list[str]  # ✅ NEW
    total_tasks: int
    success_rate: float
    avg_response_time: float
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# Task Schemas
class TaskCreate(BaseModel):
    """Schema for creating a task."""

    description: str = Field(..., min_length=1, description="Task description")
    priority: str = Field(default="medium", description="Task priority")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID")
    input_data: dict = Field(default_factory=dict, description="Input data")
    context: dict = Field(default_factory=dict, description="Context")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[UUID] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    context: Optional[dict] = None
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: UUID
    description: str
    status: str
    priority: str
    assigned_agent_id: Optional[UUID]
    parent_task_id: Optional[UUID]
    input_data: dict
    output_data: Optional[dict]
    error_message: Optional[str]
    context: dict
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# Memory Schemas
class MemoryCreate(BaseModel):
    """Schema for creating a memory."""

    memory_type: str = Field(..., description="Memory type")
    content: str = Field(..., min_length=1, description="Memory content")
    agent_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    session_id: Optional[str] = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class MemoryResponse(BaseModel):
    """Schema for memory response."""

    id: UUID
    memory_type: str
    content: str
    agent_id: Optional[UUID]
    task_id: Optional[UUID]
    session_id: Optional[str]
    importance_score: float
    access_count: int
    tags: list[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


# LLM Schemas
class GenerateRequest(BaseModel):
    """Schema for LLM generation request."""

    prompt: str = Field(..., min_length=1, description="User prompt")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    stream: bool = Field(default=False, description="Enable streaming")


class GenerateResponse(BaseModel):
    """Schema for LLM generation response."""

    content: str
    model: str = "default"
    usage: dict = Field(default_factory=dict)
