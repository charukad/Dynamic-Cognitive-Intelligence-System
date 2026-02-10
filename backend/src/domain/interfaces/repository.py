"""Repository interfaces for domain persistence."""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from ..models.agent import Agent
from ..models.memory import Memory
from ..models.task import Task

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """List entities with pagination."""
        pass


class AgentRepository(Repository[Agent]):
    """Repository interface for Agent entities."""

    @abstractmethod
    async def get_by_type(self, agent_type: str) -> List[Agent]:
        """Get agents by type."""
        pass

    @abstractmethod
    async def get_available_agents(self) -> List[Agent]:
        """Get all available (idle) agents."""
        pass


class TaskRepository(Repository[Task]):
    """Repository interface for Task entities."""

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status."""
        pass

    @abstractmethod
    async def get_by_agent(self, agent_id: UUID) -> List[Task]:
        """Get tasks assigned to an agent."""
        pass


class MemoryRepository(Repository[Memory]):
    """Repository interface for Memory entities."""

    @abstractmethod
    async def search_by_embedding(
        self, embedding: List[float], limit: int = 10
    ) -> List[Memory]:
        """Search memories by vector similarity."""
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[Memory]:
        """Get memories for a session."""
        pass

    @abstractmethod
    async def get_by_type(self, memory_type: str) -> List[Memory]:
        """Get memories by type."""
        pass
