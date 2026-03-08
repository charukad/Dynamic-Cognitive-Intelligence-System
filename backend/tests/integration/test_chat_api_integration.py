"""Stateful integration tests for canonical chat session/message/feedback APIs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import chat_feedback, chat_history, chat_sessions


class InMemoryChatRepository:
    """Minimal in-memory repository used for API integration coverage."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._messages: dict[str, list[dict[str, Any]]] = {}
        self._feedback: dict[str, dict[str, Any]] = {}
        self._session_counter = 0
        self._message_counter = 0
        self._feedback_counter = 0

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def create_session(self, *, title=None, selected_agent_id=None, metadata=None, session_id=None):
        self._session_counter += 1
        now = self._now()
        resolved_id = session_id or f"session-{self._session_counter}"
        session = {
            "id": resolved_id,
            "title": title or "New Chat",
            "status": "active",
            "selected_agent_id": selected_agent_id,
            "message_count": 0,
            "last_message": "",
            "last_message_at": None,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        self._sessions[resolved_id] = session
        self._messages[resolved_id] = []
        return SimpleNamespace(
            id=resolved_id,
            title=session["title"],
            status=session["status"],
            selected_agent_id=session["selected_agent_id"],
            message_count=0,
            metadata=session["metadata"],
            created_at=now,
            updated_at=now,
            last_message_at=None,
        )

    async def list_sessions(self, *, limit: int, offset: int):
        sessions = sorted(
            self._sessions.values(),
            key=lambda item: item["updated_at"],
            reverse=True,
        )
        return sessions[offset : offset + limit]

    async def get_session_summary(self, session_id: str):
        return self._sessions.get(session_id)

    async def get_session(self, session_id: str):
        session = self._sessions.get(session_id)
        if not session:
            return None
        return SimpleNamespace(
            id=session["id"],
            selected_agent_id=session.get("selected_agent_id"),
        )

    async def update_session(self, session_id: str, *, title=None, status=None, selected_agent_id=None, metadata=None):
        session = self._sessions.get(session_id)
        if not session:
            return None
        if title is not None:
            session["title"] = title
        if status is not None:
            session["status"] = status
        if selected_agent_id is not None:
            session["selected_agent_id"] = selected_agent_id
        if metadata is not None:
            session["metadata"] = metadata
        session["updated_at"] = self._now()
        return SimpleNamespace(
            id=session["id"],
            title=session["title"],
            status=session["status"],
            selected_agent_id=session["selected_agent_id"],
            message_count=session["message_count"],
            metadata=session["metadata"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            last_message_at=session["last_message_at"],
        )

    async def delete_session(self, session_id: str):
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        self._messages.pop(session_id, None)
        self._feedback = {
            key: value
            for key, value in self._feedback.items()
            if value["session_id"] != session_id
        }
        return True

    def _attach_feedback(self, row: dict[str, Any]) -> dict[str, Any]:
        feedback_id = row.get("feedback_id")
        if not feedback_id:
            return row
        feedback = self._feedback.get(feedback_id)
        if not feedback:
            return row
        return {
            **row,
            "feedback_agent_id": feedback.get("agent_id"),
            "feedback_type": feedback["feedback_type"],
            "rating": feedback.get("rating"),
            "text_feedback": feedback.get("text_feedback"),
            "user_id": feedback.get("user_id"),
            "feedback_metadata": feedback.get("metadata", {}),
            "feedback_created_at": feedback["created_at"],
            "feedback_updated_at": feedback["updated_at"],
        }

    async def create_message(
        self,
        *,
        session_id: str,
        message_id: str | None,
        role: Any,
        sender: Any,
        content: str,
        status: Any,
        agent_id: str | None,
        agent_name: str | None,
        metadata: dict[str, Any] | None,
        error_message: str | None = None,
    ):
        if session_id not in self._sessions:
            raise ValueError(f"Chat session not found: {session_id}")
        self._message_counter += 1
        now = self._now()
        sequence_number = len(self._messages[session_id]) + 1
        resolved_id = message_id or f"message-{self._message_counter}"
        row = {
            "id": resolved_id,
            "session_id": session_id,
            "sequence_number": sequence_number,
            "role": getattr(role, "value", role),
            "sender": getattr(sender, "value", sender),
            "content": content,
            "status": getattr(status, "value", status),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "error_message": error_message,
            "metadata": metadata or {},
            "feedback_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self._messages[session_id].append(row)
        session = self._sessions[session_id]
        session["selected_agent_id"] = agent_id or session.get("selected_agent_id")
        session["message_count"] = len(self._messages[session_id])
        session["last_message"] = content
        session["last_message_at"] = now
        session["updated_at"] = now
        return SimpleNamespace(id=resolved_id, sequence_number=sequence_number)

    async def list_messages(self, *, session_id: str, limit: int, before_sequence: int | None = None):
        rows = list(self._messages.get(session_id, []))
        if before_sequence is not None:
            rows = [row for row in rows if row["sequence_number"] < before_sequence]
        return [self._attach_feedback(row) for row in rows[-limit:]]

    async def get_message(self, message_id: str):
        for rows in self._messages.values():
            for row in rows:
                if row["id"] == message_id:
                    return self._attach_feedback(row)
        return None

    async def update_message(self, message_id: str, **changes):
        for session_id, rows in self._messages.items():
            for row in rows:
                if row["id"] != message_id:
                    continue
                for key, value in changes.items():
                    row[key] = getattr(value, "value", value)
                row["updated_at"] = self._now()
                if "content" in changes:
                    session = self._sessions[session_id]
                    session["last_message"] = row["content"]
                    session["last_message_at"] = row["updated_at"]
                    session["updated_at"] = row["updated_at"]
                return row
        raise ValueError(f"Chat message not found: {message_id}")

    async def upsert_feedback(
        self,
        *,
        session_id: str,
        message_id: str,
        agent_id: str | None,
        feedback_type: str,
        rating: int | None,
        text_feedback: str | None,
        user_id: str | None,
        metadata: dict[str, Any] | None,
    ):
        now = self._now()
        existing = None
        for feedback in self._feedback.values():
            if feedback["session_id"] == session_id and feedback["message_id"] == message_id:
                existing = feedback
                break

        if existing:
            existing.update(
                {
                    "agent_id": agent_id,
                    "feedback_type": feedback_type,
                    "rating": rating,
                    "text_feedback": text_feedback,
                    "user_id": user_id,
                    "metadata": metadata or {},
                    "updated_at": now,
                }
            )
            selected = existing
        else:
            self._feedback_counter += 1
            feedback_id = f"feedback-{self._feedback_counter}"
            selected = {
                "id": feedback_id,
                "session_id": session_id,
                "message_id": message_id,
                "agent_id": agent_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "text_feedback": text_feedback,
                "user_id": user_id,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
            }
            self._feedback[feedback_id] = selected

        for rows in self._messages.values():
            for row in rows:
                if row["id"] == message_id:
                    row["feedback_id"] = selected["id"]
                    row["updated_at"] = now
                    break

        return SimpleNamespace(**selected)


class InMemoryChatService:
    """Chat service stub that persists via the in-memory repository."""

    def __init__(self, repository: InMemoryChatRepository) -> None:
        self.repository = repository

    async def send_message(self, *, session_id: str, content: str, agent_id=None, user_message_id=None, metadata=None):
        now = datetime.now(timezone.utc)
        user = await self.repository.create_message(
            session_id=session_id,
            message_id=user_message_id,
            role="user",
            sender="user",
            content=content,
            status="completed",
            agent_id=agent_id,
            agent_name="Designer" if agent_id == "designer" else "Assistant",
            metadata=metadata or {},
        )
        assistant = await self.repository.create_message(
            session_id=session_id,
            message_id=None,
            role="assistant",
            sender="agent",
            content=f"Assistant response for: {content}",
            status="completed",
            agent_id=agent_id,
            agent_name="Designer" if agent_id == "designer" else "Assistant",
            metadata={"routing": {"source": "explicit" if agent_id else "auto"}},
        )
        return {
            "session": await self.repository.get_session_summary(session_id),
            "user_message": await self.repository.get_message(str(user.id)),
            "assistant_message": await self.repository.get_message(str(assistant.id)),
            "timestamp": now,
        }

    async def stream_message(self, *, session_id: str, content: str, agent_id=None, user_message_id=None, metadata=None):
        user = await self.repository.create_message(
            session_id=session_id,
            message_id=user_message_id,
            role="user",
            sender="user",
            content=content,
            status="completed",
            agent_id=agent_id,
            agent_name="Designer" if agent_id == "designer" else "Assistant",
            metadata=metadata or {},
        )
        assistant = await self.repository.create_message(
            session_id=session_id,
            message_id=None,
            role="assistant",
            sender="agent",
            content="",
            status="streaming",
            agent_id=agent_id,
            agent_name="Designer" if agent_id == "designer" else "Assistant",
            metadata={"routing": {"source": "explicit" if agent_id else "auto"}},
        )
        user_row = await self.repository.get_message(str(user.id))
        assistant_row = await self.repository.get_message(str(assistant.id))
        yield {
            "type": "message.created",
            "session_id": session_id,
            "message_id": str(user.id),
            "sequence_number": user_row["sequence_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": user_row},
        }
        yield {
            "type": "response.started",
            "session_id": session_id,
            "message_id": str(assistant.id),
            "sequence_number": assistant_row["sequence_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": assistant_row},
        }
        for chunk in ("Assistant ", "stream"):
            yield {
                "type": "response.delta",
                "session_id": session_id,
                "message_id": str(assistant.id),
                "sequence_number": assistant_row["sequence_number"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "agent_id": agent_id,
                    "agent_name": "Designer" if agent_id == "designer" else "Assistant",
                    "chunk": chunk,
                },
            }
        await self.repository.update_message(str(assistant.id), content="Assistant stream", status="completed")
        yield {
            "type": "response.completed",
            "session_id": session_id,
            "message_id": str(assistant.id),
            "sequence_number": assistant_row["sequence_number"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "message": await self.repository.get_message(str(assistant.id)),
                "session": await self.repository.get_session_summary(session_id),
                "routing": {"source": "explicit" if agent_id else "auto"},
            },
        }


@pytest.fixture
def integration_client(monkeypatch):
    repository = InMemoryChatRepository()
    service = InMemoryChatService(repository)

    async def allow(*args, **kwargs):
        return None

    monkeypatch.setattr(chat_sessions, "chat_repository", repository)
    monkeypatch.setattr(chat_history, "chat_repository", repository)
    monkeypatch.setattr(chat_feedback, "chat_repository", repository)
    monkeypatch.setattr(chat_history, "chat_service", service)

    monkeypatch.setattr(chat_sessions.chat_rate_limiter, "enforce", allow)
    monkeypatch.setattr(chat_history.chat_rate_limiter, "enforce", allow)
    monkeypatch.setattr(chat_feedback.chat_rate_limiter, "enforce", allow)

    app = FastAPI()
    app.include_router(chat_sessions.router, prefix="/api/v1")
    app.include_router(chat_history.router, prefix="/api/v1")
    app.include_router(chat_feedback.router, prefix="/api/v1")
    return TestClient(app)


def test_chat_session_message_feedback_lifecycle(integration_client: TestClient):
    create = integration_client.post(
        "/api/v1/chat/sessions",
        json={"title": "Integration Session", "selected_agent_id": "designer"},
    )
    assert create.status_code == 200
    session_id = create.json()["id"]

    send = integration_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages/send",
        json={
            "content": "Prepare a refined dashboard design",
            "agent_id": "designer",
            "stream": False,
            "metadata": {"mode": "balanced"},
        },
    )
    assert send.status_code == 200
    payload = send.json()
    assert payload["assistant_message"]["content"] == "Assistant response for: Prepare a refined dashboard design"

    list_messages = integration_client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert list_messages.status_code == 200
    listed = list_messages.json()["messages"]
    assert len(listed) == 2
    assistant_id = listed[1]["id"]

    feedback = integration_client.post(
        "/api/v1/chat/feedback",
        json={
            "session_id": session_id,
            "message_id": assistant_id,
            "agent_id": "designer",
            "feedback_type": "thumbs_up",
            "rating": 5,
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["feedback_type"] == "thumbs_up"

    list_after_feedback = integration_client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert list_after_feedback.status_code == 200
    with_feedback = list_after_feedback.json()["messages"][1]
    assert with_feedback["feedback"]["feedback_type"] == "thumbs_up"
    assert with_feedback["feedback"]["rating"] == 5


def test_chat_streaming_and_delete_lifecycle(integration_client: TestClient):
    create = integration_client.post(
        "/api/v1/chat/sessions",
        json={"title": "Streaming Session", "selected_agent_id": "designer"},
    )
    assert create.status_code == 200
    session_id = create.json()["id"]

    with integration_client.stream(
        "POST",
        f"/api/v1/chat/sessions/{session_id}/messages/send",
        json={
            "content": "Stream this reply",
            "agent_id": "designer",
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    data_lines = [
        line.removeprefix("data: ")
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    assert data_lines[-1] == "[DONE]"
    events = [json.loads(line) for line in data_lines[:-1]]
    assert [event["type"] for event in events] == [
        "message.created",
        "response.started",
        "response.delta",
        "response.delta",
        "response.completed",
    ]

    messages = integration_client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert messages.status_code == 200
    rows = messages.json()["messages"]
    assert len(rows) == 2
    assert rows[1]["content"] == "Assistant stream"
    assert rows[1]["status"] == "completed"

    deleted = integration_client.delete(f"/api/v1/chat/sessions/{session_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "session_id": session_id}

    missing = integration_client.get(f"/api/v1/chat/sessions/{session_id}")
    assert missing.status_code == 404
