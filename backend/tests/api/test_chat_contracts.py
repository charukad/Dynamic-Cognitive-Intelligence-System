"""Contract tests for chat session, message, and feedback routes."""

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import chat_feedback, chat_history, chat_sessions
from src.services.chat.request_controls import ChatRateLimitExceeded, ChatRateLimitScope


def _build_app() -> TestClient:
    app = FastAPI()
    app.include_router(chat_sessions.router, prefix="/api/v1")
    app.include_router(chat_history.router, prefix="/api/v1")
    app.include_router(chat_feedback.router, prefix="/api/v1")
    return TestClient(app)


def _allow_chat_rate_limits(monkeypatch) -> None:
    async def allow(*args, **kwargs):
        return None

    monkeypatch.setattr(chat_sessions.chat_rate_limiter, "enforce", allow)
    monkeypatch.setattr(chat_history.chat_rate_limiter, "enforce", allow)
    monkeypatch.setattr(chat_feedback.chat_rate_limiter, "enforce", allow)


def test_create_chat_session_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_create_session(*, title=None, selected_agent_id=None, metadata=None, session_id=None):
        return type(
            "Session",
            (),
            {
                "id": "session-1",
                "title": title or "New Chat",
                "status": "active",
                "selected_agent_id": selected_agent_id,
                "message_count": 0,
                "last_message_at": None,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
            },
        )()

    monkeypatch.setattr(chat_sessions.chat_repository, "create_session", fake_create_session)

    client = _build_app()
    response = client.post(
        "/api/v1/chat/sessions",
        json={"title": "Architecture Review", "selected_agent_id": "planner-1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session-1"
    assert data["title"] == "Architecture Review"
    assert data["selected_agent_id"] == "planner-1"
    assert data["message_count"] == 0


def test_list_chat_messages_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_session(session_id):
        return object()

    async def fake_list_messages(*, session_id, limit, before_sequence):
        return [
            {
                "id": "msg-1",
                "session_id": session_id,
                "sequence_number": 1,
                "role": "user",
                "sender": "user",
                "content": "Hello",
                "status": "completed",
                "agent_id": None,
                "agent_name": None,
                "error_message": None,
                "metadata": {},
                "created_at": now,
                "updated_at": now,
                "feedback_id": None,
            }
        ]

    monkeypatch.setattr(chat_history.chat_repository, "get_session", fake_get_session)
    monkeypatch.setattr(chat_history.chat_repository, "list_messages", fake_list_messages)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/messages")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-1"
    assert data["count"] == 1
    assert data["messages"][0]["id"] == "msg-1"
    assert data["messages"][0]["role"] == "user"


def test_upsert_chat_feedback_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_message(message_id):
        return {
            "id": message_id,
            "session_id": "session-1",
            "role": "assistant",
            "sender": "agent",
            "agent_id": "agent-1",
        }

    async def fake_upsert_feedback(**kwargs):
        return type(
            "Feedback",
            (),
            {
                "id": "fb-1",
                "session_id": kwargs["session_id"],
                "message_id": kwargs["message_id"],
                "agent_id": kwargs["agent_id"],
                "feedback_type": kwargs["feedback_type"],
                "rating": kwargs["rating"],
                "text_feedback": kwargs["text_feedback"],
                "user_id": kwargs["user_id"],
                "metadata": kwargs["metadata"],
                "created_at": now,
                "updated_at": now,
            },
        )()

    monkeypatch.setattr(chat_feedback.chat_repository, "get_message", fake_get_message)
    monkeypatch.setattr(chat_feedback.chat_repository, "upsert_feedback", fake_upsert_feedback)

    client = _build_app()
    response = client.post(
        "/api/v1/chat/feedback",
        json={
            "session_id": "session-1",
            "message_id": "msg-2",
            "agent_id": "agent-1",
            "feedback_type": "thumbs_up",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "fb-1"
    assert data["message_id"] == "msg-2"
    assert data["feedback_type"] == "thumbs_up"


def test_send_chat_message_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_send_message(**kwargs):
        return {
            "session": {
                "id": kwargs["session_id"],
                "title": "Architecture Review",
                "status": "active",
                "selected_agent_id": kwargs["agent_id"],
                "message_count": 2,
                "last_message": "Generated answer",
                "last_message_at": now,
                "metadata": {},
                "created_at": now,
                "updated_at": now,
            },
            "user_message": {
                "id": "user-1",
                "session_id": kwargs["session_id"],
                "sequence_number": 1,
                "role": "user",
                "sender": "user",
                "content": kwargs["content"],
                "status": "completed",
                "agent_id": kwargs["agent_id"],
                "agent_name": "Designer",
                "error_message": None,
                "metadata": {},
                "created_at": now,
                "updated_at": now,
                "feedback_id": None,
            },
            "assistant_message": {
                "id": "assistant-1",
                "session_id": kwargs["session_id"],
                "sequence_number": 2,
                "role": "assistant",
                "sender": "agent",
                "content": "Generated answer",
                "status": "completed",
                "agent_id": kwargs["agent_id"],
                "agent_name": "Designer",
                "error_message": None,
                "metadata": {},
                "created_at": now,
                "updated_at": now,
                "feedback_id": None,
            },
        }

    monkeypatch.setattr(chat_history.chat_service, "send_message", fake_send_message)

    client = _build_app()
    response = client.post(
        "/api/v1/chat/sessions/session-1/messages/send",
        json={
            "content": "Design a cleaner navigation system",
            "agent_id": "designer",
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session"]["id"] == "session-1"
    assert data["user_message"]["content"] == "Design a cleaner navigation system"
    assert data["assistant_message"]["content"] == "Generated answer"


def test_send_chat_message_rejects_blank_content():
    client = _build_app()
    response = client.post(
        "/api/v1/chat/sessions/session-1/messages/send",
        json={
            "content": "   ",
            "agent_id": "designer",
            "stream": False,
        },
    )

    assert response.status_code == 422


def test_get_chat_workspace_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_workspace(session_id):
        return {
            "session": {
                "id": session_id,
                "title": "Architecture Review",
                "status": "active",
                "selected_agent_id": "designer",
                "message_count": 2,
                "last_message": "Generated answer",
                "last_message_at": now,
                "metadata": {},
                "created_at": now,
                "updated_at": now,
            },
            "route": {
                "source": "explicit",
                "reason": "Manual agent selection was provided.",
                "inferred_task_type": "creative",
                "inferred_agent_type": "designer",
                "mode": "balanced",
                "start_project_mode": False,
            },
            "rooms": [
                {
                    "id": "strategy",
                    "title": "Strategy Center",
                    "label": "Planning Room",
                    "status": "watching",
                    "detail": "Incoming requests route here first.",
                    "metric": "creative",
                    "description": "Task decomposition and routing view.",
                }
            ],
            "activity_feed": [
                {
                    "id": "evt-1",
                    "type": "TASK_STARTED",
                    "description": "User request entered the office workflow.",
                    "timestamp": now,
                    "severity": "info",
                }
            ],
            "office_stats": [
                {
                    "label": "Persisted Messages",
                    "value": "2",
                    "hint": "Saved turns in this session",
                }
            ],
            "task_stages": [
                {
                    "id": "routing",
                    "title": "Routing and Planning",
                    "status": "done",
                    "detail": "Manual agent selection was provided.",
                }
            ],
            "replay": [
                {
                    "id": "replay-1",
                    "type": "USER_MESSAGE",
                    "description": "Design a cleaner navigation system",
                    "timestamp": now,
                }
            ],
            "working_context": {
                "selected_agent_name": "Designer",
            },
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_workspace", fake_get_workspace)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace")

    assert response.status_code == 200
    data = response.json()
    assert data["session"]["id"] == "session-1"
    assert data["route"]["source"] == "explicit"
    assert data["rooms"][0]["id"] == "strategy"
    assert data["activity_feed"][0]["type"] == "TASK_STARTED"


def test_feedback_rejects_session_mismatch(monkeypatch):
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_message(message_id):
        return {
            "id": message_id,
            "session_id": "session-2",
            "role": "assistant",
            "sender": "agent",
            "agent_id": "agent-1",
        }

    monkeypatch.setattr(chat_feedback.chat_repository, "get_message", fake_get_message)

    client = _build_app()
    response = client.post(
        "/api/v1/chat/feedback",
        json={
            "session_id": "session-1",
            "message_id": "msg-2",
            "agent_id": "agent-1",
            "feedback_type": "thumbs_up",
        },
    )

    assert response.status_code == 400
    assert "session_id does not match" in response.json()["detail"]


def test_chat_message_list_rate_limited(monkeypatch):
    async def deny(*args, **kwargs):
        raise ChatRateLimitExceeded(
            scope=ChatRateLimitScope.MESSAGE_READ,
            limit=240,
            retry_after_seconds=42,
            request_count=241,
        )

    monkeypatch.setattr(chat_history.chat_rate_limiter, "enforce", deny)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/messages")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "42"
