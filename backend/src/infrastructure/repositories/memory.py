"""In-memory repository implementations (for development)."""

from typing import List, Optional
from uuid import UUID

from src.domain.interfaces.repository import (
    AgentRepository,
    MemoryRepository,
    TaskRepository,
)
from src.domain.models import Agent, Memory, Task


class InMemoryAgentRepository(AgentRepository):
    """In-memory implementation of AgentRepository."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._agents: dict[UUID, Agent] = {}

    async def create(self, entity: Agent) -> Agent:
        """Create a new agent."""
        self._agents[entity.id] = entity
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(entity_id)

    async def update(self, entity: Agent) -> Agent:
        """Update an agent."""
        self._agents[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an agent."""
        if entity_id in self._agents:
            del self._agents[entity_id]
            return True
        return False

    async def list(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """List agents with pagination."""
        agents = list(self._agents.values())
        return agents[skip : skip + limit]

    async def get_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type."""
        return [a for a in self._agents.values() if a.agent_type.value == agent_type]

    async def get_available_agents(self) -> List[Agent]:
        """Get all available (idle) agents."""
        return [a for a in self._agents.values() if a.status.value == "idle"]


class InMemoryTaskRepository(TaskRepository):
    """In-memory implementation of TaskRepository."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._tasks: dict[UUID, Task] = {}

    async def create(self, entity: Task) -> Task:
        """Create a new task."""
        self._tasks[entity.id] = entity
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(entity_id)

    async def update(self, entity: Task) -> Task:
        """Update a task."""
        self._tasks[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a task."""
        if entity_id in self._tasks:
            del self._tasks[entity_id]
            return True
        return False

    async def list(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """List tasks with pagination."""
        tasks = list(self._tasks.values())
        return tasks[skip : skip + limit]

    async def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status."""
        return [t for t in self._tasks.values() if t.status.value == status]

    async def get_by_agent(self, agent_id: UUID) -> List[Task]:
        """Get tasks assigned to an agent."""
        return [t for t in self._tasks.values() if t.assigned_agent_id == agent_id]


class InMemoryMemoryRepository(MemoryRepository):
    """In-memory implementation of MemoryRepository."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._memories: dict[UUID, Memory] = {}

    async def create(self, entity: Memory) -> Memory:
        """Create a new memory."""
        self._memories[entity.id] = entity
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[Memory]:
        """Get memory by ID."""
        return self._memories.get(entity_id)

    async def update(self, entity: Memory) -> Memory:
        """Update a memory."""
        self._memories[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a memory."""
        if entity_id in self._memories:
            del self._memories[entity_id]
            return True
        return False

    async def list(self, skip: int = 0, limit: int = 100) -> List[Memory]:
        """List memories with pagination."""
        memories = list(self._memories.values())
        return memories[skip : skip + limit]

    async def search_by_embedding(
        self, embedding: List[float], limit: int = 10
    ) -> List[Memory]:
        """Search memories by vector similarity (simplified for in-memory)."""
        # TODO: Implement proper vector similarity when using ChromaDB
        return list(self._memories.values())[:limit]

    async def get_by_session(self, session_id: str) -> List[Memory]:
        """Get memories for a session."""
        return [m for m in self._memories.values() if m.session_id == session_id]

    async def get_by_agent(self, agent_id: str) -> List[Memory]:
        """Get memories by agent ID."""
        try:
            agent_uuid = UUID(agent_id) if isinstance(agent_id, str) else agent_id
            return [m for m in self._memories.values() if m.agent_id == agent_uuid]
        except ValueError:
            return []


    async def get_by_type(self, memory_type: str) -> List[Memory]:
        """Get memories by type."""
        return [m for m in self._memories.values() if m.memory_type.value == memory_type]

    async def get_recent_sessions(self, limit: int = 10) -> List[str]:
        """Get list of recent unique session IDs."""
        sessions = {}
        for m in self._memories.values():
            if m.session_id:
                # Keep the latest timestamp for each session
                if m.session_id not in sessions or m.created_at > sessions[m.session_id]:
                    sessions[m.session_id] = m.created_at
        
        # Sort by timestamp descending
        sorted_sessions = sorted(sessions.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_sessions[:limit]]


# Global instances
agent_repository = InMemoryAgentRepository()
task_repository = InMemoryTaskRepository()
memory_repository = InMemoryMemoryRepository()
