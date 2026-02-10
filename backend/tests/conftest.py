"""Test configuration and fixtures."""

import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from src.domain.models import Agent, AgentType, Memory, MemoryType, Task
from src.infrastructure.repositories import (
    agent_repository,
    memory_repository,
    task_repository,
)


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
    agent_repository._storage.clear()
    task_repository._storage.clear()
    memory_repository._storage.clear()
    
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
    
    agent_repository._storage.clear()
    task_repository._storage.clear()
    memory_repository._storage.clear()


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
