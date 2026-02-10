"""Unit tests for in-memory repositories."""

import pytest
from uuid import uuid4

from src.domain.models import Agent, AgentStatus, AgentType, Memory, MemoryType, Task, TaskStatus
from src.infrastructure.repositories import (
    InMemoryAgentRepository,
    InMemoryMemoryRepository,
    InMemoryTaskRepository,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestInMemoryAgentRepository:
    """Test suite for InMemoryAgentRepository."""

    async def test_create_agent(self, sample_agent):
        """Test creating an agent."""
        repo = InMemoryAgentRepository()
        created = await repo.create(sample_agent)
        
        assert created.id == sample_agent.id
        assert created.name == sample_agent.name
        assert created.agent_type == sample_agent.agent_type

    async def test_get_agent_by_id(self, sample_agent):
        """Test retrieving agent by ID."""
        repo = InMemoryAgentRepository()
        await repo.create(sample_agent)
        
        retrieved = await repo.get_by_id(sample_agent.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_agent.id
        assert retrieved.name == sample_agent.name

    async def test_get_nonexistent_agent(self):
        """Test retrieving non-existent agent returns None."""
        repo = InMemoryAgentRepository()
        retrieved = await repo.get_by_id(uuid4())
        
        assert retrieved is None

    async def test_update_agent(self, sample_agent):
        """Test updating an agent."""
        repo = InMemoryAgentRepository()
        await repo.create(sample_agent)
        
        sample_agent.name = "UpdatedAgent"
        sample_agent.status = AgentStatus.BUSY
        
        updated = await repo.update(sample_agent)
        
        assert updated.name == "UpdatedAgent"
        assert updated.status == AgentStatus.BUSY

    async def test_delete_agent(self, sample_agent):
        """Test deleting an agent."""
        repo = InMemoryAgentRepository()
        await repo.create(sample_agent)
        
        result = await repo.delete(sample_agent.id)
        assert result is True
        
        retrieved = await repo.get_by_id(sample_agent.id)
        assert retrieved is None

    async def test_list_agents(self, multiple_agents):
        """Test listing multiple agents."""
        repo = InMemoryAgentRepository()
        
        for agent in multiple_agents:
            await repo.create(agent)
        
        agents = await repo.list(limit=10)
        
        assert len(agents) == 5
        assert all(isinstance(a, Agent) for a in agents)

    async def test_list_agents_with_limit(self, multiple_agents):
        """Test listing agents with limit."""
        repo = InMemoryAgentRepository()
        
        for agent in multiple_agents:
            await repo.create(agent)
        
        agents = await repo.list(limit=3)
        
        assert len(agents) == 3

    async def test_find_by_type(self, multiple_agents):
        """Test finding agents by type."""
        repo = InMemoryAgentRepository()
        
        # Create agents of different types
        multiple_agents[0].agent_type = AgentType.CREATIVE
        multiple_agents[1].agent_type = AgentType.CREATIVE
        
        for agent in multiple_agents:
            await repo.create(agent)
        
        creative_agents = await repo.find_by_type(AgentType.CREATIVE)
        
        assert len(creative_agents) == 2
        assert all(a.agent_type == AgentType.CREATIVE for a in creative_agents)

    async def test_find_by_status(self, multiple_agents):
        """Test finding agents by status."""
        repo = InMemoryAgentRepository()
        
        # Create agents with different statuses
        multiple_agents[0].status = AgentStatus.BUSY
        multiple_agents[1].status = AgentStatus.BUSY
        
        for agent in multiple_agents:
            await repo.create(agent)
        
        busy_agents = await repo.find_by_status(AgentStatus.BUSY)
        
        assert len(busy_agents) == 2
        assert all(a.status == AgentStatus.BUSY for a in busy_agents)


@pytest.mark.unit
@pytest.mark.asyncio
class TestInMemoryTaskRepository:
    """Test suite for InMemoryTaskRepository."""

    async def test_create_task(self, sample_task):
        """Test creating a task."""
        repo = InMemoryTaskRepository()
        created = await repo.create(sample_task)
        
        assert created.id == sample_task.id
        assert created.title == sample_task.title

    async def test_get_task_by_id(self, sample_task):
        """Test retrieving task by ID."""
        repo = InMemoryTaskRepository()
        await repo.create(sample_task)
        
        retrieved = await repo.get_by_id(sample_task.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_task.id

    async def test_update_task(self, sample_task):
        """Test updating a task."""
        repo = InMemoryTaskRepository()
        await repo.create(sample_task)
        
        sample_task.status = TaskStatus.COMPLETED
        sample_task.result = {"success": True}
        
        updated = await repo.update(sample_task)
        
        assert updated.status == TaskStatus.COMPLETED
        assert updated.result["success"] is True

    async def test_find_by_status(self, multiple_tasks):
        """Test finding tasks by status."""
        repo = InMemoryTaskRepository()
        
        multiple_tasks[0].status = TaskStatus.COMPLETED
        multiple_tasks[1].status = TaskStatus.COMPLETED
        
        for task in multiple_tasks:
            await repo.create(task)
        
        completed_tasks = await repo.find_by_status(TaskStatus.COMPLETED)
        
        assert len(completed_tasks) == 2
        assert all(t.status == TaskStatus.COMPLETED for t in completed_tasks)

    async def test_find_by_agent(self, multiple_tasks):
        """Test finding tasks by assigned agent."""
        repo = InMemoryTaskRepository()
        agent_id = uuid4()
        
        multiple_tasks[0].assigned_agent_id = agent_id
        multiple_tasks[1].assigned_agent_id = agent_id
        
        for task in multiple_tasks:
            await repo.create(task)
        
        agent_tasks = await repo.find_by_agent(agent_id)
        
        assert len(agent_tasks) == 2
        assert all(t.assigned_agent_id == agent_id for t in agent_tasks)

    async def test_find_by_parent(self, sample_task):
        """Test finding child tasks."""
        repo = InMemoryTaskRepository()
        parent_task = sample_task
        await repo.create(parent_task)
        
        # Create child tasks
        child1 = Task(
            title="Child 1",
            description="First child",
            task_type="subtask",
            parent_task_id=parent_task.id,
        )
        child2 = Task(
            title="Child 2",
            description="Second child",
            task_type="subtask",
            parent_task_id=parent_task.id,
        )
        
        await repo.create(child1)
        await repo.create(child2)
        
        children = await repo.find_by_parent(parent_task.id)
        
        assert len(children) == 2
        assert all(t.parent_task_id == parent_task.id for t in children)


@pytest.mark.unit
@pytest.mark.asyncio
class TestInMemoryMemoryRepository:
    """Test suite for InMemoryMemoryRepository."""

    async def test_create_memory(self, sample_memory):
        """Test creating a memory."""
        repo = InMemoryMemoryRepository()
        created = await repo.create(sample_memory)
        
        assert created.id == sample_memory.id
        assert created.content == sample_memory.content

    async def test_get_memory_by_id(self, sample_memory):
        """Test retrieving memory by ID."""
        repo = InMemoryMemoryRepository()
        await repo.create(sample_memory)
        
        retrieved = await repo.get_by_id(sample_memory.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_memory.id

    async def test_find_by_session(self, multiple_memories):
        """Test finding memories by session ID."""
        repo = InMemoryMemoryRepository()
        
        session_id = "session-123"
        for memory in multiple_memories:
            memory.session_id = session_id
            await repo.create(memory)
        
        session_memories = await repo.find_by_session(session_id)
        
        assert len(session_memories) == 5
        assert all(m.session_id == session_id for m in session_memories)

    async def test_find_by_type(self, multiple_memories):
        """Test finding memories by type."""
        repo = InMemoryMemoryRepository()
        
        multiple_memories[0].memory_type = MemoryType.SEMANTIC
        multiple_memories[1].memory_type = MemoryType.SEMANTIC
        
        for memory in multiple_memories:
            await repo.create(memory)
        
        semantic_memories = await repo.find_by_type(MemoryType.SEMANTIC)
        
        assert len(semantic_memories) == 2
        assert all(m.memory_type == MemoryType.SEMANTIC for m in semantic_memories)

    async def test_delete_memory(self, sample_memory):
        """Test deleting a memory."""
        repo = InMemoryMemoryRepository()
        await repo.create(sample_memory)
        
        result = await repo.delete(sample_memory.id)
        assert result is True
        
        retrieved = await repo.get_by_id(sample_memory.id)
        assert retrieved is None

    async def test_list_memories_with_limit(self, multiple_memories):
        """Test listing memories with pagination."""
        repo = InMemoryMemoryRepository()
        
        for memory in multiple_memories:
            await repo.create(memory)
        
        memories = await repo.list(limit=3)
        
        assert len(memories) == 3

    async def test_search_by_content(self, multiple_memories):
        """Test searching memories by content."""
        repo = InMemoryMemoryRepository()
        
        multiple_memories[0].content = "Python is a programming language"
        multiple_memories[1].content = "Python has great libraries"
        multiple_memories[2].content = "JavaScript is also popular"
        
        for memory in multiple_memories:
            await repo.create(memory)
        
        # Simple text search
        results = await repo.search("Python")
        
        assert len(results) >= 2
        assert all("Python" in m.content for m in results)
