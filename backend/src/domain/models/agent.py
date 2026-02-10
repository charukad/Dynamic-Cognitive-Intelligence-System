"""Agent domain model."""

from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from .base import DomainEntity


class AgentType(str, Enum):
    """Types of agents in the system."""

    LOGICIAN = "logician"
    CREATIVE = "creative"
    SCHOLAR = "scholar"
    CRITIC = "critic"
    CODER = "coder"
    EXECUTIVE = "executive"
    CUSTOM = "custom"
    
    # Specialized Agents
    DATA_ANALYST = "data_analyst"
    DESIGNER = "designer"
    TRANSLATOR = "translator"
    FINANCIAL = "financial"


class AgentStatus(str, Enum):
    """Agent operational status."""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class Agent(DomainEntity):
    """Agent entity representing an AI agent in the system."""
    
    # Allow string IDs for agents (e.g. "data_analyst")
    id: str | UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Agent name")
    agent_type: AgentType = Field(..., description="Type of agent")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    system_prompt: str = Field(..., description="Agent's system prompt")
    model_name: str = Field(default="default", description="LLM model to use")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    
    # ✅ NEW: Agent capabilities
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of agent capabilities (e.g., 'data_analysis', 'code_generation', 'design')"
    )
    
    # Performance metrics
    total_tasks: int = Field(default=0, description="Total tasks completed")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate")
    avg_response_time: float = Field(default=0.0, ge=0.0, description="Average response time in seconds")
    
    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """
        Validate and normalize capabilities.
        
        Args:
            v: List of capability strings
            
        Returns:
            Normalized capabilities (lowercase, trimmed, no duplicates)
        """
        # Clean and normalize
        normalized = [cap.strip().lower() for cap in v if cap.strip()]
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for cap in normalized:
            if cap not in seen:
                seen.add(cap)
                unique.append(cap)
        return unique


    def __str__(self) -> str:
        """String representation."""
        return f"Agent({self.name}, type={self.agent_type.value}, status={self.status.value})"

    def mark_busy(self) -> None:
        """Mark agent as busy."""
        self.status = AgentStatus.BUSY

    def mark_idle(self) -> None:
        """Mark agent as idle."""
        self.status = AgentStatus.IDLE

    def mark_error(self) -> None:
        """Mark agent as error."""
        self.status = AgentStatus.ERROR

    def update_performance(self, success: bool, response_time: float) -> None:
        """Update agent performance metrics."""
        self.total_tasks += 1
        # Moving average for success rate
        self.success_rate = (
            (self.success_rate * (self.total_tasks - 1) + (1.0 if success else 0.0))
            / self.total_tasks
        )
        # Moving average for response time
        self.avg_response_time = (
            (self.avg_response_time * (self.total_tasks - 1) + response_time)
            / self.total_tasks
        )
