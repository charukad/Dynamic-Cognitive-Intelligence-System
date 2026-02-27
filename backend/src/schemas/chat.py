"""Schemas for chat APIs and realtime contracts."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from src.domain.models import (
    ChatFeedbackType,
    ChatMessageRole,
    ChatMessageSender,
    ChatMessageStatus,
    ChatSessionStatus,
)
from src.services.chat.validation import (
    normalize_optional_text,
    validate_chat_text,
    validate_feedback_text,
    validate_identifier,
    validate_metadata_dict,
)


class ChatSessionCreate(BaseModel):
    """Create a new chat session."""

    title: Optional[str] = Field(default=None, max_length=255)
    selected_agent_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("selected_agent_id")
    @classmethod
    def validate_selected_agent_id(cls, value: str | None) -> str | None:
        return validate_identifier(value, "selected_agent_id")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_metadata_dict(value, "metadata")


class ChatSessionUpdate(BaseModel):
    """Update chat session metadata."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[ChatSessionStatus] = None
    selected_agent_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("selected_agent_id")
    @classmethod
    def validate_selected_agent_id(cls, value: str | None) -> str | None:
        return validate_identifier(value, "selected_agent_id")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        return validate_metadata_dict(value, "metadata")


class ChatFeedbackResponse(BaseModel):
    """Stored feedback state for a single message."""

    id: str
    session_id: str
    message_id: str
    agent_id: Optional[str]
    feedback_type: ChatFeedbackType
    rating: Optional[float]
    text_feedback: Optional[str]
    user_id: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    """Create a message record within a session."""

    id: Optional[str] = None
    role: ChatMessageRole
    content: str = Field(default="")
    sender: Optional[ChatMessageSender] = None
    status: ChatMessageStatus = Field(default=ChatMessageStatus.COMPLETED)
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "agent_id")
    @classmethod
    def validate_identifiers(cls, value: str | None, info) -> str | None:
        return validate_identifier(value, info.field_name)

    @field_validator("agent_name", "error_message")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return validate_chat_text(value, field_name="content", allow_empty=True)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_metadata_dict(value, "metadata")


class ChatMessageResponse(BaseModel):
    """API shape for a persisted chat message."""

    id: str
    session_id: str
    sequence_number: int
    role: ChatMessageRole
    sender: ChatMessageSender
    content: str
    status: ChatMessageStatus
    agent_id: Optional[str]
    agent_name: Optional[str]
    error_message: Optional[str]
    metadata: dict[str, Any]
    feedback: Optional[ChatFeedbackResponse] = None
    created_at: datetime
    updated_at: datetime


class ChatMessageListResponse(BaseModel):
    """Paginated message list for one session."""

    session_id: str
    messages: list[ChatMessageResponse]
    count: int
    limit: int
    before_sequence: Optional[int] = None


class ChatSessionResponse(BaseModel):
    """API shape for a chat session."""

    id: str
    title: str
    status: ChatSessionStatus
    selected_agent_id: Optional[str]
    message_count: int
    last_message: str = ""
    last_message_at: Optional[datetime]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    """Paginated session list."""

    sessions: list[ChatSessionResponse]
    count: int


class ChatFeedbackUpsert(BaseModel):
    """Create or update feedback for a response message."""

    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    agent_id: Optional[str] = None
    feedback_type: ChatFeedbackType
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    text_feedback: Optional[str] = None
    user_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("session_id", "message_id", "agent_id", "user_id")
    @classmethod
    def validate_identifiers(cls, value: str | None, info) -> str | None:
        return validate_identifier(value, info.field_name)

    @field_validator("text_feedback")
    @classmethod
    def validate_feedback_text_value(cls, value: str | None) -> str | None:
        return validate_feedback_text(value)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_metadata_dict(value, "metadata")


class ChatRealtimeEventType(str):
    """Compatibility marker for documented realtime event names."""


class ChatRealtimeEvent(BaseModel):
    """Canonical realtime envelope for future chat streaming and office updates."""

    type: str
    session_id: str
    message_id: Optional[str] = None
    sequence_number: Optional[int] = None
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatMessageSendRequest(BaseModel):
    """Submit a user prompt and generate the next assistant turn."""

    id: Optional[str] = None
    content: str = Field(..., min_length=1)
    agent_id: Optional[str] = None
    stream: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "agent_id")
    @classmethod
    def validate_identifiers(cls, value: str | None, info) -> str | None:
        return validate_identifier(value, info.field_name)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return validate_chat_text(value, field_name="content")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_metadata_dict(value, "metadata")


class ChatMessageSendResponse(BaseModel):
    """Completed chat turn including both persisted messages."""

    session: ChatSessionResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatWorkspaceRouteResponse(BaseModel):
    """Latest routing context for a session workspace."""

    source: Optional[str] = None
    reason: Optional[str] = None
    inferred_task_type: Optional[str] = None
    inferred_agent_type: Optional[str] = None
    mode: Optional[str] = None
    start_project_mode: bool = False


class ChatWorkspaceRoomResponse(BaseModel):
    """Office room state shown in the workspace projection."""

    id: str
    title: str
    label: str
    status: str
    detail: str
    metric: str
    description: str


class ChatWorkspaceActivityResponse(BaseModel):
    """Activity feed item for the workspace."""

    id: str
    type: str
    description: str
    timestamp: datetime
    severity: str


class ChatWorkspaceStatResponse(BaseModel):
    """Key stat shown in the lower analytics panel."""

    label: str
    value: str
    hint: str


class ChatWorkspaceTaskStageResponse(BaseModel):
    """High-level task stage in the workspace DAG summary."""

    id: str
    title: str
    status: str
    detail: str


class ChatWorkspaceReplayItemResponse(BaseModel):
    """Replay timeline entry for the workspace."""

    id: str
    type: str
    description: str
    timestamp: datetime


class ChatWorkspaceResponse(BaseModel):
    """Workspace projection derived from persisted chat state."""

    session: ChatSessionResponse
    route: ChatWorkspaceRouteResponse
    rooms: list[ChatWorkspaceRoomResponse]
    activity_feed: list[ChatWorkspaceActivityResponse]
    office_stats: list[ChatWorkspaceStatResponse]
    task_stages: list[ChatWorkspaceTaskStageResponse]
    replay: list[ChatWorkspaceReplayItemResponse]
    working_context: dict[str, Any] = Field(default_factory=dict)
