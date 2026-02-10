"""Agent repository implementation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.models import Agent, AgentType, AgentStatus
from src.infrastructure.repositories.base_repository import BaseRepository
from src.infrastructure.database import postgres_client
from src.core import get_logger

logger = get_logger(__name__)


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent entities with PostgreSQL backend."""
    
    @property
    def table_name(self) -> str:
        """Return table name."""
        return "agents"
    
    @property
    def model_class(self) -> type[Agent]:
        """Return model class."""
        return Agent
    
    def _row_to_entity(self, row: Dict[str, Any]) -> Agent:
        """
        Convert database row to Agent entity.
        
        Args:
            row: Database row dictionary
            
        Returns:
            Agent entity
        """
        # Convert PostgreSQL array to Python list
        capabilities = row.get('capabilities', []) or []
        if isinstance(capabilities, str):
            # Handle string representation
            capabilities = capabilities.strip('{}').split(',') if capabilities else []
            capabilities = [c.strip() for c in capabilities if c.strip()]
        
        return Agent(
            id=UUID(row['id']) if isinstance(row['id'], str) else row['id'],
            name=row['name'],
            agent_type=AgentType(row['type']),
            temperature=float(row.get('temperature', 0.7)),
            system_prompt=row.get('system_prompt', ''),
            model_name=row.get('model_name', 'default'),
            status=AgentStatus(row['status']),
            capabilities=capabilities,
            total_tasks=int(row.get('total_tasks', 0)),
            success_rate=float(row.get('success_rate', 0.0)),
            avg_response_time=float(row.get('avg_response_time', 0.0)),
            metadata=row.get('metadata', {}),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
    
    def _entity_to_row(self, entity: Agent) -> Dict[str, Any]:
        """
        Convert Agent entity to database row.
        
        Args:
            entity: Agent entity
            
        Returns:
            Row dictionary
        """
        return {
            'id': str(entity.id),
            'name': entity.name,
            'type': entity.agent_type.value,
            'temperature': entity.temperature,
            'system_prompt': entity.system_prompt,
            'model_name': entity.model_name,
            'status': entity.status.value,
            'capabilities': entity.capabilities,  # PostgreSQL will handle array conversion
            'total_tasks': entity.total_tasks,
            'success_rate': entity.success_rate,
            'avg_response_time': entity.avg_response_time,
            'metadata': entity.metadata,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
        }
    
    # ✅ Agent-specific methods
    
    async def get_by_type(self, agent_type: AgentType) -> List[Agent]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: Agent type to filter by
            
        Returns:
            List of agents
        """
        return await self.list(filters={"type": agent_type.value})
    
    async def get_available_agents(self) -> List[Agent]:
        """
        Get all idle agents.
        
        Returns:
            List of idle agents
        """
        return await self.list(filters={"status": AgentStatus.IDLE.value})
    
    async def get_by_capability(self, capability: str) -> List[Agent]:
        """
        Find agents with specific capability.
        
        Args:
            capability: Capability to search for (case-insensitive)
            
        Returns:
            List of agents with that capability
        """
        # Normalize capability
        capability_normalized = capability.strip().lower()
        
        # PostgreSQL array contains query
        query = """
            SELECT * FROM agents
            WHERE $1 = ANY(capabilities)
            ORDER BY created_at DESC
        """
        
        try:
            results = await postgres_client.fetch(query, capability_normalized)
            return [self._row_to_entity(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error fetching agents by capability: {e}")
            raise
    
    async def get_by_capabilities_all(self, capabilities: List[str]) -> List[Agent]:
        """
        Find agents that have ALL of the specified capabilities.
        
        Args:
            capabilities: List of required capabilities
            
        Returns:
            List of agents with all capabilities
        """
        # Normalize capabilities
        capabilities_normalized = [c.strip().lower() for c in capabilities]
        
        # PostgreSQL array contains all query
        query = """
            SELECT * FROM agents
            WHERE capabilities @> $1
            ORDER BY created_at DESC
        """
        
        try:
            results = await postgres_client.fetch(query, capabilities_normalized)
            return [self._row_to_entity(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error fetching agents by capabilities: {e}")
            raise
    
    async def get_by_capabilities_any(self, capabilities: List[str]) -> List[Agent]:
        """
        Find agents that have ANY of the specified capabilities.
        
        Args:
            capabilities: List of desired capabilities
            
        Returns:
            List of agents with at least one capability
        """
        # Normalize capabilities
        capabilities_normalized = [c.strip().lower() for c in capabilities]
        
        # PostgreSQL array overlap query
        query = """
            SELECT * FROM agents
            WHERE capabilities && $1
            ORDER BY created_at DESC
        """
        
        try:
            results = await postgres_client.fetch(query, capabilities_normalized)
            return [self._row_to_entity(dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Error fetching agents by capabilities: {e}")
            raise
    
    async def update_status(self, agent_id: UUID, status: AgentStatus) -> Agent:
        """
        Update agent status.
        
        Args:
            agent_id: Agent ID
            status: New status
            
        Returns:
            Updated agent
        """
        query = """
            UPDATE agents
            SET status = $1, updated_at = $2
            WHERE id = $3
            RETURNING *
        """
        
        try:
            result = await postgres_client.fetchrow(
                query,
                status.value,
                datetime.utcnow(),
                str(agent_id)
            )
            
            if not result:
                raise RuntimeError(f"Agent not found: {agent_id}")
            
            return self._row_to_entity(dict(result))
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            raise
    
    async def update_performance(
        self,
        agent_id: UUID,
        total_tasks: int,
        success_rate: float,
        avg_response_time: float
    ) -> Agent:
        """
        Update agent performance metrics.
        
        Args:
            agent_id: Agent ID
            total_tasks: Total tasks completed
            success_rate: Success rate (0.0-1.0)
            avg_response_time: Average response time in seconds
            
        Returns:
            Updated agent
        """
        query = """
            UPDATE agents
            SET total_tasks = $1,
                success_rate = $2,
                avg_response_time = $3,
                updated_at = $4
            WHERE id = $5
            RETURNING *
        """
        
        try:
            result = await postgres_client.fetchrow(
                query,
                total_tasks,
                success_rate,
                avg_response_time,
                datetime.utcnow(),
                str(agent_id)
            )
            
            if not result:
                raise RuntimeError(f"Agent not found: {agent_id}")
            
            return self._row_to_entity(dict(result))
        except Exception as e:
            logger.error(f"Error updating agent performance: {e}")
            raise


# Global instance - will be replaced with dependency injection
_agent_repository_instance: Optional[AgentRepository] = None


def get_agent_repository() -> AgentRepository:
    """
    Get agent repository instance.
    
    This is a simple factory function for dependency injection.
    In production, this would be managed by a DI container.
    
    Returns:
        AgentRepository instance
    """
    global _agent_repository_instance
    if _agent_repository_instance is None:
        _agent_repository_instance = AgentRepository()
    return _agent_repository_instance
