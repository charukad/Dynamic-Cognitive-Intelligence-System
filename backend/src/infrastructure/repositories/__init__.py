"""Repositories package."""

# PostgreSQL-based repositories  
from .agent_repository import get_agent_repository

# In-memory repositories (for development)
from .memory import task_repository, memory_repository

# Create global instance
agent_repository = get_agent_repository()

__all__ = ["agent_repository", "task_repository", "memory_repository"]
