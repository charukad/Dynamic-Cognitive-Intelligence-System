"""Contract tests for chat session, message, and feedback routes."""

import json
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


def test_send_chat_message_stream_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_stream_message(**kwargs):
        yield {
            "type": "message.created",
            "session_id": kwargs["session_id"],
            "message_id": "user-1",
            "sequence_number": 1,
            "timestamp": now.isoformat(),
            "payload": {
                "message": {
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
                }
            },
        }
        yield {
            "type": "response.started",
            "session_id": kwargs["session_id"],
            "message_id": "assistant-1",
            "sequence_number": 2,
            "timestamp": now.isoformat(),
            "payload": {
                "message": {
                    "id": "assistant-1",
                    "session_id": kwargs["session_id"],
                    "sequence_number": 2,
                    "role": "assistant",
                    "sender": "agent",
                    "content": "",
                    "status": "streaming",
                    "agent_id": kwargs["agent_id"],
                    "agent_name": "Designer",
                    "error_message": None,
                    "metadata": {},
                    "created_at": now,
                    "updated_at": now,
                    "feedback_id": None,
                }
            },
        }
        yield {
            "type": "response.delta",
            "session_id": kwargs["session_id"],
            "message_id": "assistant-1",
            "sequence_number": 2,
            "timestamp": now.isoformat(),
            "payload": {
                "agent_id": kwargs["agent_id"],
                "agent_name": "Designer",
                "chunk": "Generated answer",
            },
        }
        yield {
            "type": "response.completed",
            "session_id": kwargs["session_id"],
            "message_id": "assistant-1",
            "sequence_number": 2,
            "timestamp": now.isoformat(),
            "payload": {
                "message": {
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
                "routing": {
                    "source": "explicit",
                    "reason": "User explicitly selected the target agent",
                    "inferred_task_type": "creative",
                    "inferred_agent_type": "designer",
                    "mode": "balanced",
                    "start_project_mode": False,
                },
            },
        }

    monkeypatch.setattr(chat_history.chat_service, "stream_message", fake_stream_message)

    client = _build_app()
    with client.stream(
        "POST",
        "/api/v1/chat/sessions/session-1/messages/send",
        json={
            "content": "Design a cleaner navigation system",
            "agent_id": "designer",
            "stream": True,
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
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
        "response.completed",
    ]
    assert events[-1]["payload"]["routing"]["source"] == "explicit"


def test_send_chat_message_stream_emits_failed_event_on_internal_error(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_stream_message(**kwargs):
        yield {
            "type": "message.created",
            "session_id": kwargs["session_id"],
            "message_id": "user-1",
            "sequence_number": 1,
            "timestamp": now.isoformat(),
            "payload": {"message": {"id": "user-1"}},
        }
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(chat_history.chat_service, "stream_message", fake_stream_message)

    client = _build_app()
    with client.stream(
        "POST",
        "/api/v1/chat/sessions/session-1/messages/send",
        json={
            "content": "Design a cleaner navigation system",
            "agent_id": "designer",
            "stream": True,
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    data_lines = [
        line.removeprefix("data: ")
        for line in body.splitlines()
        if line.startswith("data: ")
    ]
    assert data_lines[-1] == "[DONE]"
    events = [json.loads(line) for line in data_lines[:-1]]
    assert events[0]["type"] == "message.created"
    assert events[-1]["type"] == "response.failed"
    assert events[-1]["payload"]["error"] == "Chat streaming failed"


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
            "graph_nodes": [
                {
                    "id": "strategy",
                    "label": "Strategy Center",
                    "kind": "room",
                    "status": "watching",
                    "x": 0.34,
                    "y": 0.2,
                }
            ],
            "graph_edges": [
                {
                    "id": "edge-1",
                    "from_id": "front_desk",
                    "to_id": "strategy",
                    "label": "TASK_STARTED",
                    "status": "success",
                }
            ],
            "room_timeline": [
                {
                    "id": "evt-1",
                    "room_id": "strategy",
                    "room_title": "Strategy Center",
                    "type": "TASK_STARTED",
                    "description": "User request entered the office workflow.",
                    "timestamp": now,
                    "severity": "info",
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
    assert data["graph_nodes"][0]["id"] == "strategy"
    assert data["graph_edges"][0]["to_id"] == "strategy"
    assert data["room_timeline"][0]["room_id"] == "strategy"


def test_get_chat_workspace_room_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_room_detail(session_id, room_id):
        return {
            "room": {
                "id": room_id,
                "title": "Strategy Center",
                "label": "Planning Room",
                "status": "watching",
                "detail": "Incoming requests route here first.",
                "metric": "creative",
                "description": "Task decomposition and routing view.",
            },
            "summary": "Strategy Center is preparing the latest route plan.",
            "metrics": [
                {
                    "label": "Route Source",
                    "value": "Manual Selection",
                    "hint": "Manual agent selection was provided.",
                }
            ],
            "highlights": [
                "Task type: creative",
            ],
            "recent_events": [
                {
                    "id": "evt-1",
                    "room_id": room_id,
                    "room_title": "Strategy Center",
                    "type": "TASK_STARTED",
                    "description": "User request entered the office workflow.",
                    "timestamp": now,
                    "severity": "info",
                }
            ],
            "related_messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "sender": "user",
                    "content": "Design a cleaner navigation system",
                    "status": "completed",
                    "agent_name": None,
                    "created_at": now,
                }
            ],
            "actions": [
                "Open task DAG viewer",
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_room_detail", fake_get_room_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/rooms/strategy")

    assert response.status_code == 200
    data = response.json()
    assert data["room"]["id"] == "strategy"
    assert data["summary"] == "Strategy Center is preparing the latest route plan."
    assert data["metrics"][0]["label"] == "Route Source"
    assert data["recent_events"][0]["room_id"] == "strategy"
    assert data["related_messages"][0]["id"] == "msg-1"
    assert data["actions"][0] == "Open task DAG viewer"


def test_get_chat_workspace_voting_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_voting_detail(session_id):
        return {
            "room": {
                "id": "voting",
                "title": "Voting Chamber",
                "label": "Governance",
                "status": "active",
                "detail": "Executive routing is coordinating a project-style decision path.",
                "metric": "project governance",
                "description": "Decision room for approvals, conflict resolution, and governance events.",
            },
            "status": "active",
            "decision_outcome": "Executive router triggered a project governance path for this request.",
            "participants": ["Designer"],
            "criteria": ["Task type: creative"],
            "reasoning": ["Voting events are only persisted when governance is triggered."],
            "events": [
                {
                    "id": "vote-1",
                    "room_id": "voting",
                    "room_title": "Voting Chamber",
                    "type": "VOTING_STARTED",
                    "description": "Executive router triggered a project governance path for this request.",
                    "timestamp": now,
                    "severity": "warning",
                }
            ],
            "metrics": [
                {
                    "label": "Governance Events",
                    "value": "1",
                    "hint": "Persisted Voting Chamber checkpoints",
                }
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_voting_detail", fake_get_voting_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/voting")

    assert response.status_code == 200
    data = response.json()
    assert data["room"]["id"] == "voting"
    assert data["participants"][0] == "Designer"
    assert data["events"][0]["type"] == "VOTING_STARTED"


def test_get_chat_workspace_collaboration_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_collaboration_detail(session_id):
        return {
            "room": {
                "id": "collaboration",
                "title": "Collaboration Hub",
                "label": "Shared Pod Space",
                "status": "active",
                "detail": "Designer is coordinating on the current session path.",
                "metric": "multi-step flow",
                "description": "Cross-checking and collaborative execution surface for complex requests.",
            },
            "summary": "Designer entered a collaborative project execution path.",
            "participants": ["Designer"],
            "shared_working_memory": {"selected_agent_name": "Designer"},
            "coordination_log": [
                {
                    "id": "collab-1",
                    "room_id": "collaboration",
                    "room_title": "Collaboration Hub",
                    "type": "COLLABORATION_STARTED",
                    "description": "Designer entered a collaborative project execution path.",
                    "timestamp": now,
                    "severity": "info",
                }
            ],
            "related_messages": [
                {
                    "id": "msg-1",
                    "role": "assistant",
                    "sender": "agent",
                    "content": "Acknowledged.",
                    "status": "completed",
                    "agent_name": "Designer",
                    "created_at": now,
                }
            ],
            "metrics": [
                {
                    "label": "Collaborative Turns",
                    "value": "1",
                    "hint": "Coordination events persisted for this session",
                }
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_collaboration_detail", fake_get_collaboration_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/collaboration")

    assert response.status_code == 200
    data = response.json()
    assert data["room"]["id"] == "collaboration"
    assert data["coordination_log"][0]["type"] == "COLLABORATION_STARTED"
    assert data["shared_working_memory"]["selected_agent_name"] == "Designer"


def test_get_chat_workspace_incubator_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_incubator_detail(session_id):
        return {
            "room": {
                "id": "incubator",
                "title": "Specialist Incubator",
                "label": "Capability Lab",
                "status": "watching",
                "detail": "Project mode is active without a strong specialist match.",
                "metric": "no hiring event",
                "description": "Capability expansion area for specialist discovery and onboarding workflows.",
            },
            "status": "watching",
            "summary": "Project mode is active without a strong specialist match.",
            "gap_detected": True,
            "inferred_specialist": None,
            "benchmark_signals": ["Project mode: enabled"],
            "events": [
                {
                    "id": "inc-1",
                    "room_id": "incubator",
                    "room_title": "Specialist Incubator",
                    "type": "SPECIALIST_GAP_DETECTED",
                    "description": "Project mode is active without a strong specialist match.",
                    "timestamp": now,
                    "severity": "warning",
                }
            ],
            "metrics": [
                {
                    "label": "Gap Signals",
                    "value": "1",
                    "hint": "Capability-gap or incubation triggers",
                }
            ],
            "actions": ["Review specialist-gap signals"],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_incubator_detail", fake_get_incubator_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/incubator")

    assert response.status_code == 200
    data = response.json()
    assert data["room"]["id"] == "incubator"
    assert data["gap_detected"] is True
    assert data["events"][0]["type"] == "SPECIALIST_GAP_DETECTED"


def test_get_chat_workspace_memory_vault_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_memory_vault_detail(session_id):
        return {
            "room": {
                "id": "memory",
                "title": "Memory Vault",
                "label": "Context Core",
                "status": "watching",
                "detail": "2 recent turns are available in working memory.",
                "metric": "2 turn cache",
                "description": "Persistent context surface for recent turns, route history, and session memory.",
            },
            "summary": "2 recent turns are available in working memory.",
            "working_context": {"selected_agent_name": "Designer"},
            "preference_signals": ["Preferred specialist in context: Designer"],
            "retrieval_events": [
                {
                    "id": "mem-1",
                    "room_id": "memory",
                    "room_title": "Memory Vault",
                    "type": "CONTEXT_RECALLED",
                    "description": "Session memory and retrieval context were loaded for the current turn.",
                    "timestamp": now,
                    "severity": "info",
                }
            ],
            "recent_turns": [
                {
                    "user": "Design a cleaner navigation system",
                    "assistant": "Acknowledged.",
                    "agent_id": "designer",
                    "agent_name": "Designer",
                    "mode": "balanced",
                    "updated_at": now,
                }
            ],
            "episodic_memories": [
                {
                    "id": "memory-1",
                    "content": "User asked: Design a cleaner navigation system",
                    "importance_score": 0.55,
                    "tags": ["chat", "user_turn", "creative"],
                    "created_at": now,
                }
            ],
            "metrics": [
                {
                    "label": "Recent Turns",
                    "value": "1",
                    "hint": "Turns retained in working memory",
                }
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_memory_vault_detail", fake_get_memory_vault_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/memory-vault")

    assert response.status_code == 200
    data = response.json()
    assert data["room"]["id"] == "memory"
    assert data["retrieval_events"][0]["type"] == "CONTEXT_RECALLED"
    assert data["episodic_memories"][0]["id"] == "memory-1"


def test_get_chat_workspace_dag_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_dag_detail(session_id):
        return {
            "session_id": session_id,
            "summary": "Designer completed the latest delivery path.",
            "latest_node_id": "delivery",
            "total_duration_ms": 2200,
            "nodes": [
                {
                    "id": "routing",
                    "title": "Routing and Planning",
                    "room_id": "strategy",
                    "status": "done",
                    "detail": "Manual agent selection was provided.",
                    "dependencies": ["intake"],
                    "started_at": now,
                    "completed_at": now,
                    "execution_time_ms": 120,
                    "assigned_agent": "Designer",
                    "evaluation_score": None,
                    "retry_count": 0,
                    "model_used": None,
                    "event_ids": ["evt-1"],
                },
                {
                    "id": "delivery",
                    "title": "Delivery and Validation",
                    "room_id": "execution",
                    "status": "done",
                    "detail": "Latest response delivered successfully.",
                    "dependencies": ["execution"],
                    "started_at": now,
                    "completed_at": now,
                    "execution_time_ms": 840,
                    "assigned_agent": "Designer",
                    "evaluation_score": 1.0,
                    "retry_count": 0,
                    "model_used": "demo-model",
                    "event_ids": ["evt-2"],
                },
            ],
            "edges": [
                {
                    "id": "execution:delivery",
                    "from_id": "execution",
                    "to_id": "delivery",
                    "label": "depends_on",
                    "status": "success",
                }
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_dag_detail", fake_get_dag_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/dag")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-1"
    assert data["latest_node_id"] == "delivery"
    assert data["nodes"][1]["model_used"] == "demo-model"
    assert data["edges"][0]["to_id"] == "delivery"


def test_get_chat_workspace_replay_contract(monkeypatch):
    now = datetime.now(timezone.utc)
    _allow_chat_rate_limits(monkeypatch)

    async def fake_get_replay_detail(session_id):
        return {
            "session_id": session_id,
            "summary": "Designer completed the response and returned it to the front desk.",
            "current_index": 1,
            "started_at": now,
            "ended_at": now,
            "total_duration_ms": 1800,
            "frames": [
                {
                    "id": "evt-1",
                    "index": 0,
                    "type": "TASK_STARTED",
                    "description": "User request entered the office workflow.",
                    "timestamp": now,
                    "severity": "info",
                    "room_id": "strategy",
                    "room_title": "Strategy Center",
                    "agent_name": "Designer",
                    "related_message_id": "msg-1",
                    "focus_node_ids": ["strategy", "front_desk"],
                    "focus_edge_id": "front_desk:strategy:TASK_STARTED",
                },
                {
                    "id": "evt-2",
                    "index": 1,
                    "type": "FINAL_RESPONSE_SENT",
                    "description": "Designer completed the response and returned it to the front desk.",
                    "timestamp": now,
                    "severity": "success",
                    "room_id": "execution",
                    "room_title": "Active Pods",
                    "agent_name": "Designer",
                    "related_message_id": "msg-2",
                    "focus_node_ids": ["execution", "front_desk"],
                    "focus_edge_id": "execution:front_desk:FINAL_RESPONSE_SENT",
                },
            ],
        }

    monkeypatch.setattr(chat_sessions.chat_workspace_service, "get_replay_detail", fake_get_replay_detail)

    client = _build_app()
    response = client.get("/api/v1/chat/sessions/session-1/workspace/replay")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-1"
    assert data["current_index"] == 1
    assert data["frames"][0]["focus_node_ids"][0] == "strategy"
    assert data["frames"][1]["type"] == "FINAL_RESPONSE_SENT"


def test_delete_chat_session_contract(monkeypatch):
    _allow_chat_rate_limits(monkeypatch)

    async def fake_delete_session(session_id):
        assert session_id == "session-1"
        return True

    monkeypatch.setattr(chat_sessions.chat_repository, "delete_session", fake_delete_session)

    client = _build_app()
    response = client.delete("/api/v1/chat/sessions/session-1")

    assert response.status_code == 200
    assert response.json() == {
        "deleted": True,
        "session_id": "session-1",
    }


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
