"""Execution-contract tests for the chat service."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.domain.models import Agent, AgentStatus, AgentType
from src.services.chat import service as chat_service_module
from src.services.chat.service import ChatService, MemoryContext, RouteDecision


def _agent(agent_id: str = "designer") -> Agent:
    return Agent(
        id=agent_id,
        name="Designer",
        agent_type=AgentType.DESIGNER,
        status=AgentStatus.IDLE,
        capabilities=["ui", "ux"],
        system_prompt="You are the design specialist.",
        temperature=0.2,
    )


def _route(agent: Agent) -> RouteDecision:
    return RouteDecision(
        agent=agent,
        route_source="explicit",
        route_reason="User explicitly selected the target agent",
        requested_agent_id=str(agent.id),
        inferred_task_type="creative",
        inferred_agent_type=AgentType.DESIGNER.value,
        mode="balanced",
        start_project_mode=False,
        effective_system_prompt="Resolved prompt",
    )


def _normalize(value):
    return value.value if hasattr(value, "value") else value


def _install_repository_fakes(monkeypatch) -> dict:
    now = datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc)
    state = {
        "messages": {},
        "updates": [],
    }
    counters = {"sequence": 0}

    async def fake_get_session(session_id):
        if session_id != "session-1":
            return None
        return SimpleNamespace(id=session_id, selected_agent_id=None)

    async def fake_create_message(
        *,
        session_id,
        message_id,
        role,
        sender,
        content,
        status,
        agent_id,
        agent_name,
        metadata,
        error_message=None,
    ):
        counters["sequence"] += 1
        sequence_number = counters["sequence"]
        stored_id = message_id or f"message-{sequence_number}"
        row = {
            "id": stored_id,
            "session_id": session_id,
            "sequence_number": sequence_number,
            "role": _normalize(role),
            "sender": _normalize(sender),
            "content": content,
            "status": _normalize(status),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "error_message": error_message,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "feedback_id": None,
        }
        state["messages"][stored_id] = row
        return SimpleNamespace(id=stored_id, sequence_number=sequence_number)

    async def fake_list_messages(*, session_id, limit, before_sequence=None):
        rows = [
            row
            for row in state["messages"].values()
            if row["session_id"] == session_id
        ]
        rows.sort(key=lambda row: row["sequence_number"])
        if before_sequence is not None:
            rows = [row for row in rows if row["sequence_number"] < before_sequence]
        return rows[-limit:]

    async def fake_get_message(message_id):
        return state["messages"].get(message_id)

    async def fake_update_message(message_id, **changes):
        row = state["messages"][message_id]
        for key, value in changes.items():
            row[key] = _normalize(value)
        row["updated_at"] = now
        state["updates"].append((message_id, changes))
        return row

    async def fake_get_session_summary(session_id):
        rows = [
            row
            for row in state["messages"].values()
            if row["session_id"] == session_id
        ]
        rows.sort(key=lambda row: row["sequence_number"])
        last_row = rows[-1] if rows else None
        return {
            "id": session_id,
            "title": "New Conversation",
            "status": "active",
            "selected_agent_id": None,
            "message_count": len(rows),
            "last_message": last_row["content"] if last_row else "",
            "last_message_at": last_row["created_at"] if last_row else None,
            "metadata": {},
            "created_at": now,
            "updated_at": now,
        }

    monkeypatch.setattr(chat_service_module.chat_repository, "get_session", fake_get_session)
    monkeypatch.setattr(chat_service_module.chat_repository, "create_message", fake_create_message)
    monkeypatch.setattr(chat_service_module.chat_repository, "list_messages", fake_list_messages)
    monkeypatch.setattr(chat_service_module.chat_repository, "get_message", fake_get_message)
    monkeypatch.setattr(chat_service_module.chat_repository, "update_message", fake_update_message)
    monkeypatch.setattr(chat_service_module.chat_repository, "get_session_summary", fake_get_session_summary)

    return state


@pytest.mark.asyncio
async def test_send_message_persists_completed_turn_and_updates_memory(monkeypatch):
    service = ChatService()
    agent = _agent()
    route = _route(agent)
    repo_state = _install_repository_fakes(monkeypatch)
    completion_calls: list[dict] = []
    memory_updates: list[dict] = []
    performance_updates: list[tuple[str, bool]] = []

    async def fake_route_message(**kwargs):
        return route

    async def fake_load_memory_context(session_id, content):
        return MemoryContext({}, [], [], "")

    def fake_resolve_system_prompt(**kwargs):
        return "System prompt"

    async def fake_record_pre_response_events(**kwargs):
        return None

    async def fake_record_response_started_event(**kwargs):
        return None

    async def fake_record_response_completed_event(**kwargs):
        return None

    async def fake_update_memory_state(**kwargs):
        memory_updates.append(kwargs)

    async def fake_chat_completion(**kwargs):
        completion_calls.append(kwargs)
        return "Approved design direction."

    monkeypatch.setattr(service, "route_message", fake_route_message)
    monkeypatch.setattr(service, "_load_memory_context", fake_load_memory_context)
    monkeypatch.setattr(service, "_resolve_system_prompt", fake_resolve_system_prompt)
    monkeypatch.setattr(service, "_record_pre_response_events", fake_record_pre_response_events)
    monkeypatch.setattr(service, "_record_response_started_event", fake_record_response_started_event)
    monkeypatch.setattr(service, "_record_response_completed_event", fake_record_response_completed_event)
    monkeypatch.setattr(service, "_update_memory_state", fake_update_memory_state)
    monkeypatch.setattr(service, "chat_completion", fake_chat_completion)
    monkeypatch.setattr(
        chat_service_module.thompson_router,
        "update_performance",
        lambda agent_id, success: performance_updates.append((str(agent_id), success)),
    )

    result = await service.send_message(
        session_id="session-1",
        content="Create a cleaner launch screen",
        agent_id="designer",
        user_message_id="user-1",
        metadata={"mode": "balanced"},
    )

    assert result["session"]["message_count"] == 2
    assert result["user_message"]["metadata"]["routing"]["source"] == "explicit"
    assert result["assistant_message"]["content"] == "Approved design direction."
    assert completion_calls[0]["system_prompt"] == "System prompt"
    assert completion_calls[0]["messages"] == [
        {"role": "user", "content": "Create a cleaner launch screen"},
    ]
    assert memory_updates[0]["assistant_content"] == "Approved design direction."
    assert performance_updates == [("designer", True)]
    assert len(repo_state["messages"]) == 2


@pytest.mark.asyncio
async def test_send_message_persists_failed_assistant_turn(monkeypatch):
    service = ChatService()
    agent = _agent()
    route = _route(agent)
    repo_state = _install_repository_fakes(monkeypatch)
    failed_events: list[dict] = []
    performance_updates: list[tuple[str, bool]] = []
    memory_updates: list[dict] = []

    async def fake_route_message(**kwargs):
        return route

    async def fake_load_memory_context(session_id, content):
        return MemoryContext({}, [], [], "")

    def fake_resolve_system_prompt(**kwargs):
        return "System prompt"

    async def fake_record_pre_response_events(**kwargs):
        return None

    async def fake_record_response_started_event(**kwargs):
        return None

    async def fake_record_response_failed_event(**kwargs):
        failed_events.append(kwargs)

    async def fake_update_memory_state(**kwargs):
        memory_updates.append(kwargs)

    async def fake_chat_completion(**kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(service, "route_message", fake_route_message)
    monkeypatch.setattr(service, "_load_memory_context", fake_load_memory_context)
    monkeypatch.setattr(service, "_resolve_system_prompt", fake_resolve_system_prompt)
    monkeypatch.setattr(service, "_record_pre_response_events", fake_record_pre_response_events)
    monkeypatch.setattr(service, "_record_response_started_event", fake_record_response_started_event)
    monkeypatch.setattr(service, "_record_response_failed_event", fake_record_response_failed_event)
    monkeypatch.setattr(service, "_update_memory_state", fake_update_memory_state)
    monkeypatch.setattr(service, "chat_completion", fake_chat_completion)
    monkeypatch.setattr(
        chat_service_module.thompson_router,
        "update_performance",
        lambda agent_id, success: performance_updates.append((str(agent_id), success)),
    )

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        await service.send_message(
            session_id="session-1",
            content="Create a cleaner launch screen",
            agent_id="designer",
            user_message_id="user-1",
        )

    assistant_rows = [
        row
        for row in repo_state["messages"].values()
        if row["sender"] == "agent"
    ]
    assert len(assistant_rows) == 1
    assert assistant_rows[0]["status"] == "failed"
    assert assistant_rows[0]["error_message"] == "LLM unavailable"
    assert failed_events[0]["error"] == "LLM unavailable"
    assert performance_updates == [("designer", False)]
    assert memory_updates == []


@pytest.mark.asyncio
async def test_stream_message_emits_canonical_events_and_finalizes_content(monkeypatch):
    service = ChatService()
    agent = _agent()
    route = _route(agent)
    repo_state = _install_repository_fakes(monkeypatch)
    stream_calls: list[dict] = []
    memory_updates: list[dict] = []
    performance_updates: list[tuple[str, bool]] = []

    async def fake_route_message(**kwargs):
        return route

    async def fake_load_memory_context(session_id, content):
        return MemoryContext({}, [], [], "")

    def fake_resolve_system_prompt(**kwargs):
        return "System prompt"

    async def fake_record_pre_response_events(**kwargs):
        return None

    async def fake_record_response_started_event(**kwargs):
        return None

    async def fake_record_response_completed_event(**kwargs):
        return None

    async def fake_update_memory_state(**kwargs):
        memory_updates.append(kwargs)

    async def fake_chat_stream(**kwargs):
        stream_calls.append(kwargs)
        yield "Approved"
        yield " design"

    monkeypatch.setattr(service, "route_message", fake_route_message)
    monkeypatch.setattr(service, "_load_memory_context", fake_load_memory_context)
    monkeypatch.setattr(service, "_resolve_system_prompt", fake_resolve_system_prompt)
    monkeypatch.setattr(service, "_record_pre_response_events", fake_record_pre_response_events)
    monkeypatch.setattr(service, "_record_response_started_event", fake_record_response_started_event)
    monkeypatch.setattr(service, "_record_response_completed_event", fake_record_response_completed_event)
    monkeypatch.setattr(service, "_update_memory_state", fake_update_memory_state)
    monkeypatch.setattr(service, "chat_stream", fake_chat_stream)
    monkeypatch.setattr(
        chat_service_module.thompson_router,
        "update_performance",
        lambda agent_id, success: performance_updates.append((str(agent_id), success)),
    )

    events = [
        event
        async for event in service.stream_message(
            session_id="session-1",
            content="Create a cleaner launch screen",
            agent_id="designer",
            user_message_id="user-1",
        )
    ]

    assert [event["type"] for event in events] == [
        "message.created",
        "response.started",
        "response.delta",
        "response.delta",
        "response.completed",
    ]
    assert stream_calls[0]["system_prompt"] == "System prompt"
    assert stream_calls[0]["messages"] == [
        {"role": "user", "content": "Create a cleaner launch screen"},
    ]
    assert events[-1]["payload"]["message"]["content"] == "Approved design"
    assert events[-1]["payload"]["routing"]["source"] == "explicit"
    assert memory_updates[0]["assistant_content"] == "Approved design"
    assert performance_updates == [("designer", True)]
    assistant_rows = [
        row
        for row in repo_state["messages"].values()
        if row["sender"] == "agent"
    ]
    assert assistant_rows[0]["status"] == "completed"
    assert assistant_rows[0]["content"] == "Approved design"
