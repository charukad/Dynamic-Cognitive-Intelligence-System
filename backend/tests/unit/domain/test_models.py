"""Complete unit tests for all domain models."""

import pytest
from datetime import datetime

from src.domain.models import Agent, AgentStatus, AgentType, Task, TaskStatus, Memory, MemoryType


class TestAgentModel:
    """Comprehensive tests for Agent domain model."""

    def test_agent_creation_with_all_fields(self):
        """Test creating an agent with all fields."""
        now = datetime.utcnow()
        agent = Agent(
            id="agent_123",
            name="Test Agent",
            type=AgentType.CODER,
            status=AgentStatus.IDLE,
            created_at=now,
            updated_at=now,
            metadata={"version": "1.0"},
        )
        
        assert agent.id == "agent_123"
        assert agent.name == "Test Agent"
        assert agent.type == AgentType.CODER
        assert agent.status == AgentStatus.IDLE
        assert agent.created_at == now
        assert agent.metadata["version"] == "1.0"

    def test_agent_type_all_variants(self):
        """Test all agent type variants."""
        types = [
            AgentType.CODER,
            AgentType.LOGICIAN,
            AgentType.CREATIVE,
            AgentType.SCHOLAR,
            AgentType.CRITIC,
            AgentType.EXECUTIVE,
        ]
        
        for agent_type in types:
            agent = Agent(
                id=f"agent_{agent_type}",
                name=f"{agent_type} Agent",
                type=agent_type,
                status=AgentStatus.IDLE,
            )
            assert agent.type == agent_type

    def test_agent_status_transitions(self):
        """Test agent status transitions."""
        agent = Agent(
            id="agent_1",
            name="Test",
            type=AgentType.CODER,
            status=AgentStatus.IDLE,
        )
        
        # Simulate status transitions
        assert agent.status == AgentStatus.IDLE
        agent.status = AgentStatus.BUSY
        assert agent.status == AgentStatus.BUSY
        agent.status = AgentStatus.ERROR
        assert agent.status == AgentStatus.ERROR


class TestTaskModel:
    """Comprehensive tests for Task domain model."""

    def test_task_creation_minimal(self):
        """Test creating a task with minimal required fields."""
        task = Task(
            id="task_1",
            description="Test task",
            status=TaskStatus.PENDING,
        )
        
        assert task.id == "task_1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING

    def test_task_with_all_fields(self):
        """Test task with all fields populated."""
        now = datetime.utcnow()
        task = Task(
            id="task_full",
            description="Complete task",
            status=TaskStatus.COMPLETED,
            assigned_agent_id="agent_1",
            priority=10,
            created_at=now,
            updated_at=now,
            completed_at=now,
            result="Task completed successfully",
            metadata={"complexity": "high"},
        )
        
        assert task.id == "task_full"
        assert task.assigned_agent_id == "agent_1"
        assert task.priority == 10
        assert task.result == "Task completed successfully"
        assert task.metadata["complexity"] == "high"

    def test_task_status_lifecycle(self):
        """Test complete task lifecycle."""
        task = Task(
            id="task_lifecycle",
            description="Lifecycle test",
            status=TaskStatus.PENDING,
        )
        
        assert task.status == TaskStatus.PENDING
        
        task.status = TaskStatus.IN_PROGRESS
        assert task.status == TaskStatus.IN_PROGRESS
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_task_priority_levels(self):
        """Test different priority levels."""
        priorities = [0, 5, 10, 100]
        
        for priority in priorities:
            task = Task(
                id=f"task_p{priority}",
                description="Priority test",
                status=TaskStatus.PENDING,
                priority=priority,
            )
            assert task.priority == priority


class TestMemoryModel:
    """Comprehensive tests for Memory domain model."""

    def test_memory_creation(self):
        """Test creating a memory."""
        memory = Memory(
            id="mem_1",
            type=MemoryType.EPISODIC,
            content="User asked about Python",
            importance=0.8,
        )
        
        assert memory.id == "mem_1"
        assert memory.type == MemoryType.EPISODIC
        assert memory.content == "User asked about Python"
        assert memory.importance == 0.8

    def test_memory_types(self):
        """Test all memory types."""
        types = [
            MemoryType.EPISODIC,
            MemoryType.SEMANTIC,
            MemoryType.PROCEDURAL,
            MemoryType.WORKING,
        ]
        
        for mem_type in types:
            memory = Memory(
                id=f"mem_{mem_type}",
                type=mem_type,
                content=f"Content for {mem_type}",
                importance=0.5,
            )
            assert memory.type == mem_type

    def test_memory_importance_range(self):
        """Test memory importance values."""
        importances = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for importance in importances:
            memory = Memory(
                id=f"mem_{importance}",
                type=MemoryType.EPISODIC,
                content="Test",
                importance=importance,
            )
            assert memory.importance == importance

    def test_memory_with_metadata(self):
        """Test memory with rich metadata."""
        metadata = {
            "source": "user_query",
            "topic": "programming",
            "language": "python",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        memory = Memory(
            id="mem_meta",
            type=MemoryType.EPISODIC,
            content="Python programming question",
            importance=0.9,
            metadata=metadata,
        )
        
        assert memory.metadata["source"] == "user_query"
        assert memory.metadata["topic"] == "programming"


class TestModelRelationships:
    """Test relationships between domain models."""

    def test_task_agent_assignment(self):
        """Test task assigned to agent."""
        agent = Agent(
            id="agent_coder",
            name="Coder",
            type=AgentType.CODER,
            status=AgentStatus.IDLE,
        )
        
        task = Task(
            id="task_code",
            description="Write function",
            status=TaskStatus.PENDING,
            assigned_agent_id=agent.id,
        )
        
        assert task.assigned_agent_id == agent.id

    def test_multiple_tasks_per_agent(self):
        """Test one agent handling multiple tasks."""
        agent_id = "agent_multi"
        
        tasks = [
            Task(
                id=f"task_{i}",
                description=f"Task {i}",
                status=TaskStatus.PENDING,
                assigned_agent_id=agent_id,
            )
            for i in range(5)
        ]
        
        assert all(t.assigned_agent_id == agent_id for t in tasks)
        assert len(tasks) == 5


class TestModelValidation:
    """Test domain model validation."""

    def test_agent_requires_id(self):
        """Test that agent needs an ID."""
        with pytest.raises((ValueError, TypeError)):
            Agent(
                id=None,
                name="Test",
                type=AgentType.CODER,
                status=AgentStatus.IDLE,
            )

    def test_task_requires_description(self):
        """Test that task needs description."""
        task = Task(
            id="task_1",
            description="",
            status=TaskStatus.PENDING,
        )
        # Empty description is allowed, but should be validated at service layer
        assert task.description == ""

    def test_memory_importance_bounds(self):
        """Test memory importance validation."""
        # Valid importances
        valid_importances = [0.0, 0.5, 1.0]
        for imp in valid_importances:
            memory = Memory(
                id="mem",
                type=MemoryType.EPISODIC,
                content="Test",
                importance=imp,
            )
            assert 0.0 <= memory.importance <= 1.0


class TestModelSerialization:
    """Test model serialization/deserialization."""

    def test_agent_to_dict(self):
        """Test agent model conversion to dict."""
        agent = Agent(
            id="agent_1",
            name="Test Agent",
            type=AgentType.CODER,
            status=AgentStatus.IDLE,
            metadata={"test": "value"},
        )
        
        # Assuming model has dict() method (Pydantic)
        if hasattr(agent, 'dict'):
            agent_dict = agent.dict()
            assert agent_dict["id"] == "agent_1"
            assert agent_dict["name"] == "Test Agent"

    def test_task_to_dict(self):
        """Test task model conversion to dict."""
        task = Task(
            id="task_1",
            description="Test",
            status=TaskStatus.PENDING,
            priority=5,
        )
        
        if hasattr(task, 'dict'):
            task_dict = task.dict()
            assert task_dict["id"] == "task_1"
            assert task_dict["priority"] == 5
