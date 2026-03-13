"""Test configuration and fixtures."""

import inspect
import pytest
import httpx
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import src.infrastructure.repositories as repository_registry
from src.api.routes import agents as agents_routes
from src.api.routes import tasks as tasks_routes
from src.domain.models import Agent, AgentType, Memory, MemoryType, Task
from src.infrastructure.repositories.memory import (
    agent_repository as in_memory_agent_repository,
    memory_repository as in_memory_memory_repository,
    task_repository as in_memory_task_repository,
)
from src.services.orchestrator.meta_orchestrator import meta_orchestrator


if "app" not in inspect.signature(httpx.AsyncClient.__init__).parameters:
    _OriginalAsyncClient = httpx.AsyncClient

    class _CompatAsyncClient(_OriginalAsyncClient):
        """Back-compat wrapper for test suites still using AsyncClient(app=...)."""

        def __init__(self, *args, app=None, **kwargs):
            if app is not None and "transport" not in kwargs:
                kwargs["transport"] = httpx.ASGITransport(app=app)
            kwargs.setdefault("follow_redirects", True)
            super().__init__(*args, **kwargs)

    httpx.AsyncClient = _CompatAsyncClient


@pytest.fixture
def sample_agent() -> Agent:
    """Create a sample agent for testing."""
    return Agent(
        name="TestAgent",
        agent_type=AgentType.LOGICIAN,
        system_prompt="You are a test agent",
        temperature=0.5,
        capabilities=["testing", "analysis"],
    )


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        title="Test Task",
        description="This is a test task",
        task_type="testing",
    )


@pytest.fixture
def sample_memory() -> Memory:
    """Create a sample memory for testing."""
    return Memory(
        content="This is a test memory",
        memory_type=MemoryType.EPISODIC,
        session_id="test-session",
        importance_score=0.5,
    )


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Create a mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="Test response")
    client.generate_stream = AsyncMock()
    client.get_embedding = AsyncMock(return_value=[0.1] * 768)
    return client


@pytest.fixture
def mock_chroma_client() -> AsyncMock:
    """Create a mock ChromaDB client."""
    client = AsyncMock()
    client.add_documents = AsyncMock()
    client.query_documents = AsyncMock(return_value=[])
    client.delete_documents = AsyncMock()
    return client


@pytest.fixture
def mock_neo4j_client() -> AsyncMock:
    """Create a mock Neo4j client."""
    client = AsyncMock()
    client.execute_query = AsyncMock(return_value=[])
    client.create_node = AsyncMock(return_value={"id": "test-node"})
    client.create_relationship = AsyncMock(return_value={"id": "test-rel"})
    return client


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Create a mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    return client


@pytest.fixture(autouse=True)
def clear_repositories():
    """Clear in-memory repositories before each test."""
    # Force in-memory repositories for integration tests to avoid DB auth dependencies.
    repository_registry.agent_repository = in_memory_agent_repository
    repository_registry.task_repository = in_memory_task_repository
    repository_registry.memory_repository = in_memory_memory_repository
    agents_routes.agent_repository = in_memory_agent_repository
    tasks_routes.agent_repository = in_memory_agent_repository
    tasks_routes.task_repository = in_memory_task_repository
    meta_orchestrator.agent_repo = in_memory_agent_repository
    meta_orchestrator.task_repo = in_memory_task_repository
    meta_orchestrator.router.performance.clear()
    meta_orchestrator.router.type_to_agents.clear()

    in_memory_agent_repository.agents.clear()
    in_memory_task_repository.tasks.clear()
    in_memory_memory_repository.memories.clear()
    
    # Reset RLHF feedback manager
    try:
        from src.services.rlhf.feedback_manager import feedback_manager
        feedback_manager.feedback_history.clear()
        feedback_manager.reward_models.clear()
    except ImportError:
        pass
    
    # Reset metrics collector
    try:
        from src.services.monitoring.metrics import metrics_collector
        metrics_collector.metrics.clear()
        metrics_collector.counters.clear()
        metrics_collector.gauges.clear()
        metrics_collector.histograms.clear()
    except ImportError:
        pass
    
    yield
    
    in_memory_agent_repository.agents.clear()
    in_memory_task_repository.tasks.clear()
    in_memory_memory_repository.memories.clear()


@pytest.fixture
def multiple_agents() -> list[Agent]:
    """Create multiple agents for testing."""
    return [
        Agent(
            name=f"Agent{i}",
            agent_type=AgentType.LOGICIAN,
            system_prompt=f"Agent {i} prompt",
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_agents() -> list[Agent]:
    """Create a representative set of agents used by legacy integration tests."""
    return [
        Agent(
            name="LogicAgent",
            agent_type=AgentType.LOGICIAN,
            system_prompt="You reason through structured problems.",
            capabilities=["analysis"],
        ),
        Agent(
            name="CodeAgent",
            agent_type=AgentType.CODER,
            system_prompt="You implement robust production code.",
            capabilities=["coding"],
        ),
        Agent(
            name="CriticAgent",
            agent_type=AgentType.CRITIC,
            system_prompt="You review and improve outputs.",
            capabilities=["review"],
        ),
    ]


@pytest.fixture
def multiple_tasks() -> list[Task]:
    """Create multiple tasks for testing."""
    return [
        Task(
            title=f"Task {i}",
            description=f"Description {i}",
            task_type="testing",
        )
        for i in range(5)
    ]


@pytest.fixture
def multiple_memories() -> list[Memory]:
    """Create multiple memories for testing."""
    return [
        Memory(
            content=f"Memory content {i}",
            memory_type=MemoryType.EPISODIC,
            session_id="test-session",
        )
        for i in range(5)
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as benchmark/performance"
    )


def pytest_collection_modifyitems(config, items):
    """
    Skip performance benchmark tests when pytest-benchmark plugin is unavailable.
    """
    if config.pluginmanager.hasplugin("benchmark"):
        return

    skip_perf = pytest.mark.skip(reason="pytest-benchmark plugin not installed")
    for item in items:
        path = str(item.fspath)
        if "/tests/performance/" in path:
            item.add_marker(skip_perf)
