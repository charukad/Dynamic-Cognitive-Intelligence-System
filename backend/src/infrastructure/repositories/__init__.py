"""Repositories package."""

# PostgreSQL-based repositories  
from .agent_repository import get_agent_repository
from .chat_repository import chat_repository

# In-memory repositories (for development)
from .memory import (
    InMemoryAgentRepository,
    InMemoryMemoryRepository,
    InMemoryTaskRepository,
    agent_repository as in_memory_agent_repository,
    memory_repository,
    task_repository,
)

# Create global instance
agent_repository = get_agent_repository()

__all__ = [
    "agent_repository",
    "in_memory_agent_repository",
    "chat_repository",
    "task_repository",
    "memory_repository",
    "InMemoryAgentRepository",
    "InMemoryTaskRepository",
    "InMemoryMemoryRepository",
]
