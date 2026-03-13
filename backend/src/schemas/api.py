"""Request and response schemas for API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# Agent Schemas
class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    agent_type: Optional[str] = Field(None, description="Agent type")
    type: Optional[str] = Field(None, description="Legacy alias for agent_type")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    system_prompt: Optional[str] = Field(None, min_length=1, description="System prompt")
    model_name: str = Field(default="default", description="LLM model")
    config: dict = Field(default_factory=dict, description="Legacy config envelope")
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")  # ✅ NEW
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_agent_fields(cls, values: dict) -> dict:
        """Accept legacy payloads that use `type` and `config` fields."""
        if not isinstance(values, dict):
            return values

        if not values.get("agent_type") and values.get("type"):
            values["agent_type"] = values["type"]

        config = values.get("config")
        if isinstance(config, dict):
            if "temperature" in config and "temperature" not in values:
                values["temperature"] = config["temperature"]
            if "model_name" in config and "model_name" not in values:
                values["model_name"] = config["model_name"]
            if "system_prompt" in config and not values.get("system_prompt"):
                values["system_prompt"] = config["system_prompt"]

        return values

    @model_validator(mode="after")
    def ensure_required_agent_fields(self) -> "AgentCreate":
        """Ensure compatibility defaults for required fields."""
        if not self.agent_type:
            raise ValueError("agent_type or type is required")
        if not self.system_prompt:
            self.system_prompt = f"You are {self.name}, a {self.agent_type} specialist agent."
        return self


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

    title: Optional[str] = Field(None, min_length=1, description="Optional task title")
    description: Optional[str] = Field(None, min_length=1, description="Task description")
    task_type: Optional[str] = Field(None, description="Optional task type")
    priority: str | int = Field(default="medium", description="Task priority")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID")
    input_data: dict = Field(default_factory=dict, description="Input data")
    context: dict = Field(default_factory=dict, description="Context")
    metadata: dict = Field(default_factory=dict, description="Metadata")

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: str | int) -> str:
        """Accept both string and numeric priorities from legacy clients."""
        if isinstance(value, int):
            if value >= 8:
                return "critical"
            if value >= 6:
                return "high"
            if value >= 3:
                return "medium"
            return "low"
        return str(value).lower()

    @model_validator(mode="after")
    def ensure_description(self) -> "TaskCreate":
        """Ensure at least one textual descriptor is available."""
        if not self.description and self.title:
            self.description = self.title
        if not self.description:
            raise ValueError("description or title is required")
        return self


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
    title: Optional[str]
    description: str
    task_type: Optional[str]
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
