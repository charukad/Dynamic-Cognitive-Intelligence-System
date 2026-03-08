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


class ChatWorkspaceGraphNodeResponse(BaseModel):
    """Node in the live office graph overlay."""

    id: str
    label: str
    kind: str
    status: str
    x: float
    y: float


class ChatWorkspaceGraphEdgeResponse(BaseModel):
    """Edge in the live office graph overlay."""

    id: str
    from_id: str
    to_id: str
    label: str
    status: str


class ChatWorkspaceRoomTimelineItemResponse(BaseModel):
    """Timeline item scoped to a single office room."""

    id: str
    room_id: str
    room_title: Optional[str] = None
    type: str
    description: str
    timestamp: datetime
    severity: str


class ChatWorkspaceRoomDetailMessageResponse(BaseModel):
    """Message excerpt relevant to a room-level drill-down panel."""

    id: str
    role: str
    sender: str
    content: str
    status: str
    agent_name: Optional[str] = None
    created_at: datetime


class ChatWorkspaceRoomDetailResponse(BaseModel):
    """Detailed drill-down payload for a single office room."""

    room: ChatWorkspaceRoomResponse
    summary: str
    metrics: list[ChatWorkspaceStatResponse]
    highlights: list[str] = Field(default_factory=list)
    recent_events: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    related_messages: list[ChatWorkspaceRoomDetailMessageResponse] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class ChatWorkspaceVotingResponse(BaseModel):
    """Governance/voting room projection."""

    room: ChatWorkspaceRoomResponse
    status: str
    decision_outcome: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    events: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    metrics: list[ChatWorkspaceStatResponse] = Field(default_factory=list)


class ChatWorkspaceCollaborationResponse(BaseModel):
    """Collaboration room log and working-state projection."""

    room: ChatWorkspaceRoomResponse
    summary: str
    participants: list[str] = Field(default_factory=list)
    shared_working_memory: dict[str, Any] = Field(default_factory=dict)
    coordination_log: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    related_messages: list[ChatWorkspaceRoomDetailMessageResponse] = Field(default_factory=list)
    metrics: list[ChatWorkspaceStatResponse] = Field(default_factory=list)


class ChatWorkspaceIncubatorResponse(BaseModel):
    """Specialist incubator and hiring-readiness projection."""

    room: ChatWorkspaceRoomResponse
    status: str
    summary: str
    gap_detected: bool
    inferred_specialist: Optional[str] = None
    benchmark_signals: list[str] = Field(default_factory=list)
    events: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    metrics: list[ChatWorkspaceStatResponse] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class ChatWorkspaceMemoryTurnResponse(BaseModel):
    """Working-memory turn retained for memory-vault inspection."""

    user: str
    assistant: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    mode: Optional[str] = None
    updated_at: Optional[datetime] = None


class ChatWorkspaceMemoryItemResponse(BaseModel):
    """Episodic memory item surfaced in the memory vault."""

    id: str
    content: str
    importance_score: float
    tags: list[str] = Field(default_factory=list)
    created_at: datetime


class ChatWorkspaceMemoryVaultResponse(BaseModel):
    """Memory-vault inspection payload."""

    room: ChatWorkspaceRoomResponse
    summary: str
    working_context: dict[str, Any] = Field(default_factory=dict)
    preference_signals: list[str] = Field(default_factory=list)
    retrieval_events: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    recent_turns: list[ChatWorkspaceMemoryTurnResponse] = Field(default_factory=list)
    episodic_memories: list[ChatWorkspaceMemoryItemResponse] = Field(default_factory=list)
    metrics: list[ChatWorkspaceStatResponse] = Field(default_factory=list)


class ChatWorkspaceDagNodeResponse(BaseModel):
    """Node in the task DAG projection."""

    id: str
    title: str
    room_id: Optional[str] = None
    status: str
    detail: str
    dependencies: list[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    assigned_agent: Optional[str] = None
    evaluation_score: Optional[float] = None
    retry_count: int = 0
    model_used: Optional[str] = None
    event_ids: list[str] = Field(default_factory=list)


class ChatWorkspaceDagEdgeResponse(BaseModel):
    """Dependency edge in the task DAG projection."""

    id: str
    from_id: str
    to_id: str
    label: str
    status: str


class ChatWorkspaceDagResponse(BaseModel):
    """Task DAG view derived from persisted workspace events."""

    session_id: str
    summary: str
    latest_node_id: Optional[str] = None
    total_duration_ms: Optional[int] = None
    nodes: list[ChatWorkspaceDagNodeResponse] = Field(default_factory=list)
    edges: list[ChatWorkspaceDagEdgeResponse] = Field(default_factory=list)


class ChatWorkspaceReplayFrameResponse(BaseModel):
    """Single replay frame derived from a persisted workspace event."""

    id: str
    index: int
    type: str
    description: str
    timestamp: datetime
    severity: str
    room_id: Optional[str] = None
    room_title: Optional[str] = None
    agent_name: Optional[str] = None
    related_message_id: Optional[str] = None
    focus_node_ids: list[str] = Field(default_factory=list)
    focus_edge_id: Optional[str] = None


class ChatWorkspaceReplayResponse(BaseModel):
    """Replay controls payload derived from persisted workspace events."""

    session_id: str
    summary: str
    current_index: int = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    frames: list[ChatWorkspaceReplayFrameResponse] = Field(default_factory=list)


class ChatWorkspaceResponse(BaseModel):
    """Workspace projection derived from persisted chat state."""

    session: ChatSessionResponse
    route: ChatWorkspaceRouteResponse
    rooms: list[ChatWorkspaceRoomResponse]
    activity_feed: list[ChatWorkspaceActivityResponse]
    office_stats: list[ChatWorkspaceStatResponse]
    task_stages: list[ChatWorkspaceTaskStageResponse]
    replay: list[ChatWorkspaceReplayItemResponse]
    graph_nodes: list[ChatWorkspaceGraphNodeResponse] = Field(default_factory=list)
    graph_edges: list[ChatWorkspaceGraphEdgeResponse] = Field(default_factory=list)
    room_timeline: list[ChatWorkspaceRoomTimelineItemResponse] = Field(default_factory=list)
    working_context: dict[str, Any] = Field(default_factory=dict)
