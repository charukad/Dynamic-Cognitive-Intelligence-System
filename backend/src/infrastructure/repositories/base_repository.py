"""Base repository with generic CRUD operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from src.domain.models.base import DomainEntity
from src.infrastructure.database import postgres_client
from src.core import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=DomainEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository implementing common patterns.
    
    Provides:
    - CRUD operations
    - Pagination
    - Filtering
    - Exists checks
    
    Subclasses must implement:
    - table_name property
    - model_class property
    - _row_to_entity method
    - _entity_to_row method
    """
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the database table name."""
        pass
    
    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        """Return the model class this repository manages."""
        pass
    
    @abstractmethod
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """
        Convert database row to domain entity.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            Domain entity instance
        """
        pass
    
    @abstractmethod
    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        """
        Convert domain entity to database row.
        
        Args:
            entity: Domain entity
            
        Returns:
            Row dictionary for database
        """
        pass
    
    async def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with all fields
        """
        row = self._entity_to_row(entity)
        
        # Build INSERT query
        columns = ', '.join(row.keys())
        placeholders = ', '.join(f'${i+1}' for i in range(len(row)))
        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        
        try:
            result = await postgres_client.fetchrow(query, *row.values())
            if not result:
                raise RuntimeError(f"Failed to create {self.model_class.__name__}")
            
            created_entity = self._row_to_entity(dict(result))
            logger.info(f"Created {self.model_class.__name__} with ID {created_entity.id}")
            return created_entity
            
        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity if found, None otherwise
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        
        try:
            result = await postgres_client.fetchrow(query, str(entity_id))
            if not result:
                return None
            
            return self._row_to_entity(dict(result))
            
        except Exception as e:
            logger.error(f"Error fetching {self.model_class.__name__} by ID: {e}")
            raise
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at DESC"
    ) -> List[T]:
        """
        List entities with pagination and filters.
        
        Args:
            skip: Number of items to skip
            limit: Maximum items to return
            filters: Optional filter criteria (column: value)
            order_by: ORDER BY clause (default: created_at DESC)
            
        Returns:
            List of entities
        """
        # Build WHERE clause
        where_conditions = []
        params = []
        param_index = 1
        
        if filters:
            for key, value in filters.items():
                where_conditions.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Add pagination params
        params.extend([limit, skip])
        
        query = f"""
            SELECT * FROM {self.table_name}
            {where_clause}
            ORDER BY {order_by}
            LIMIT ${param_index} OFFSET ${param_index + 1}
        """
        
        try:
            results = await postgres_client.fetch(query, *params)
            return [self._row_to_entity(dict(row)) for row in results]
            
        except Exception as e:
            logger.error(f"Error listing {self.model_class.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: Entity with updated fields
            
        Returns:
            Updated entity
        """
        row = self._entity_to_row(entity)
        
        # Remove id and created_at from update
        entity_id = row.pop('id')
        row.pop('created_at', None)
        
        # Update updated_at
        from datetime import datetime, timezone
        row['updated_at'] = datetime.now(timezone.utc)
        
        # Build UPDATE query
        set_clauses = [f"{key} = ${i+1}" for i, key in enumerate(row.keys())]
        params = list(row.values()) + [entity_id]
        
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE id = ${len(params)}
            RETURNING *
        """
        
        try:
            result = await postgres_client.fetchrow(query, *params)
            if not result:
                raise RuntimeError(f"{self.model_class.__name__} not found for update")
            
            updated_entity = self._row_to_entity(dict(result))
            logger.info(f"Updated {self.model_class.__name__} with ID {updated_entity.id}")
            return updated_entity
            
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if deleted, False if not found
        """
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        
        try:
            result = await postgres_client.execute(query, str(entity_id))
            deleted = "DELETE 1" in result
            
            if deleted:
                logger.info(f"Deleted {self.model_class.__name__} with ID {entity_id}")
            else:
                logger.warning(f"{self.model_class.__name__} not found for deletion: {entity_id}")
                
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise
    
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if exists, False otherwise
        """
        query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = $1)"
        
        try:
            result = await postgres_client.fetchval(query, str(entity_id))
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error checking existence of {self.model_class.__name__}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.
        
        Args:
            filters: Optional filter criteria
            
        Returns:
            Count of matching entities
        """
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if filters:
            for i, (key, value) in enumerate(filters.items(), 1):
                where_conditions.append(f"{key} = ${i}")
                params.append(value)
        
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        query = f"SELECT COUNT(*) FROM {self.table_name} {where_clause}"
        
        try:
            result = await postgres_client.fetchval(query, *params)
            return int(result) if result else 0
            
        except Exception as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise
