"""Chat domain models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

from .base import DomainEntity


class ChatSessionStatus(str, Enum):
    """Lifecycle states for a chat session."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ChatMessageRole(str, Enum):
    """Message role from the model perspective."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageSender(str, Enum):
    """Message sender used by the current frontend contract."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ChatMessageStatus(str, Enum):
    """Delivery state for an individual message."""

    QUEUED = "queued"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatFeedbackType(str, Enum):
    """Supported feedback types for agent responses."""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"
    TEXT = "text_feedback"


class ChatSession(DomainEntity):
    """Persistent chat conversation."""

    id: str | UUID = Field(default_factory=uuid4)
    title: str = Field(default="New Chat", max_length=255)
    status: ChatSessionStatus = Field(default=ChatSessionStatus.ACTIVE)
    selected_agent_id: Optional[str] = Field(default=None)
    message_count: int = Field(default=0, ge=0)
    last_message_at: Optional[datetime] = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class ChatMessage(DomainEntity):
    """Persistent chat message."""

    id: str | UUID = Field(default_factory=uuid4)
    session_id: str = Field(..., min_length=1)
    sequence_number: int = Field(default=0, ge=0)
    role: ChatMessageRole = Field(...)
    sender: ChatMessageSender = Field(...)
    content: str = Field(default="")
    status: ChatMessageStatus = Field(default=ChatMessageStatus.COMPLETED)
    agent_id: Optional[str] = Field(default=None)
    agent_name: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class ChatMessageFeedback(DomainEntity):
    """Persistent feedback tied to a single response message."""

    id: str | UUID = Field(default_factory=uuid4)
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    agent_id: Optional[str] = Field(default=None)
    feedback_type: ChatFeedbackType = Field(...)
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    text_feedback: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    metadata: dict = Field(default_factory=dict)
