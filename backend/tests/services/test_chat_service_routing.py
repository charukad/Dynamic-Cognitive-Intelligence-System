"""Unit tests for chat routing and prompt resolution."""

import pytest

from src.domain.models import Agent, AgentStatus, AgentType
from src.services.chat.service import ChatService


def _agent(agent_id: str, name: str, agent_type: AgentType) -> Agent:
    return Agent(
        id=agent_id,
        name=name,
        agent_type=agent_type,
        status=AgentStatus.IDLE,
        capabilities=[agent_type.value],
        system_prompt=f"You are {name}.",
    )


@pytest.mark.asyncio
async def test_route_message_respects_explicit_agent(monkeypatch):
    service = ChatService()
    explicit_agent = _agent("designer", "Designer", AgentType.DESIGNER)

    async def fake_resolve_agent(agent_id):
        assert agent_id == "designer"
        return explicit_agent

    monkeypatch.setattr(service, "resolve_agent", fake_resolve_agent)

    route = await service.route_message(
        content="Create a cleaner dashboard layout",
        requested_agent_id="designer",
        session_agent_id=None,
        metadata={"mode": "balanced"},
    )

    assert route.route_source == "explicit"
    assert route.agent.id == "designer"
    assert route.mode == "balanced"


@pytest.mark.asyncio
async def test_route_message_infers_coding_agent(monkeypatch):
    service = ChatService()
    coder = _agent("coder", "Coder", AgentType.CODER)
    designer = _agent("designer", "Designer", AgentType.DESIGNER)

    async def fake_routable_agents():
        return [designer, coder]

    async def fake_llm_route_agent(**kwargs):
        return None

    monkeypatch.setattr(service, "_get_routable_agents", fake_routable_agents)
    monkeypatch.setattr(service, "_llm_route_agent", fake_llm_route_agent)

    route = await service.route_message(
        content="Debug this Python API handler and fix the failing code path",
        requested_agent_id=None,
        session_agent_id=None,
        metadata={"mode": "high_accuracy"},
    )

    assert route.agent.agent_type == AgentType.CODER
    assert route.inferred_task_type == "coding"
    assert route.inferred_agent_type == AgentType.CODER.value
    assert "correctness" in route.effective_system_prompt.lower()


@pytest.mark.asyncio
async def test_route_message_uses_executive_router_for_project_mode(monkeypatch):
    service = ChatService()
    scholar = _agent("scholar", "Scholar", AgentType.SCHOLAR)
    designer = _agent("designer", "Designer", AgentType.DESIGNER)

    async def fake_routable_agents():
        return [scholar, designer]

    async def fake_llm_route_agent(**kwargs):
        return designer, "Executive orchestrator selected the designer for the request"

    monkeypatch.setattr(service, "_get_routable_agents", fake_routable_agents)
    monkeypatch.setattr(service, "_llm_route_agent", fake_llm_route_agent)

    route = await service.route_message(
        content="Plan a new visual concept for the product launch",
        requested_agent_id=None,
        session_agent_id=None,
        metadata={"start_project_mode": True, "mode": "budget"},
    )

    assert route.route_source == "executive_router"
    assert route.agent.id == "designer"
    assert route.start_project_mode is True
    assert route.mode == "budget"
    assert "cost-efficiency" in route.effective_system_prompt.lower()


def test_resolve_system_prompt_includes_memory_context():
    service = ChatService()
    agent = _agent("scholar", "Scholar", AgentType.SCHOLAR)
    route = type(
        "Route",
        (),
        {
            "mode": "high_accuracy",
            "route_source": "auto",
            "route_reason": "Thompson sampling preferred the scholar",
            "start_project_mode": False,
        },
    )()
    memory_context = type(
        "MemoryContext",
        (),
        {
            "working_context": {"customer_persona": "Prefers concise technical explanations"},
            "recent_session_memories": ["User previously asked about orchestration latency"],
            "retrieved_memories": ["Past answer covered agent routing tradeoffs"],
            "rag_context": "DCIS stores sessions and feedback in persistent systems.",
            "has_context": True,
        },
    )()

    prompt = service._resolve_system_prompt(
        agent=agent,
        route=route,
        memory_context=memory_context,
    )

    assert "Supplemental context" in prompt
    assert "customer_persona" in prompt
    assert "orchestration latency" in prompt
    assert "correctness" in prompt
