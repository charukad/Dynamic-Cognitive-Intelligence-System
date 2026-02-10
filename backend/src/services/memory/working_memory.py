"""Working memory service using Redis for short-term caching."""

from typing import Any, Dict, List, Optional

from src.core import get_logger
from src.infrastructure.database import redis_client

logger = get_logger(__name__)


class WorkingMemoryService:
    """
    Service for managing working memory (short-term cache).
    
    Uses Redis for fast access to conversation context and temporary data.
    """

    def __init__(self) -> None:
        """Initialize working memory service."""
        self.client = redis_client
        self.default_ttl = 3600  # 1 hour

    async def store_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store conversation context.
        
        Args:
            session_id: Session identifier
            context: Context data
            ttl: Time to live in seconds
            
        Returns:
            True if stored successfully
        """
        import json
        
        key = f"context:{session_id}"
        value = json.dumps(context)
        
        success = await self.client.set(
            key=key,
            value=value,
            expire=ttl or self.default_ttl,
        )
        
        logger.info(f"Stored context for session: {session_id}")
        return success

    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context data or None
        """
        import json
        
        key = f"context:{session_id}"
        value = await self.client.get(key)
        
        if value:
            try:
                context = json.loads(value)
                logger.debug(f"Retrieved context for session: {session_id}")
                return context
            except json.JSONDecodeError:
                logger.error(f"Failed to decode context for session: {session_id}")
        
        return None

    async def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update conversation context.
        
        Args:
            session_id: Session identifier
            updates: Context updates to apply
            
        Returns:
            True if updated successfully
        """
        context = await self.get_context(session_id) or {}
        context.update(updates)
        
        return await self.store_context(session_id, context)

    async def clear_context(self, session_id: str) -> bool:
        """
        Clear conversation context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared
        """
        key = f"context:{session_id}"
        success = await self.client.delete(key)
        
        logger.info(f"Cleared context for session: {session_id}")
        return success

    async def cache_value(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "cache",
    ) -> bool:
        """
        Cache a value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Cache namespace
            
        Returns:
            True if cached successfully
        """
        import json
        
        full_key = f"{namespace}:{key}"
        
        # Serialize value
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value)
        else:
            serialized = str(value)
        
        success = await self.client.set(
            key=full_key,
            value=serialized,
            expire=ttl or self.default_ttl,
        )
        
        logger.debug(f"Cached value: {full_key}")
        return success

    async def get_cached_value(
        self,
        key: str,
        namespace: str = "cache",
    ) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            Cached value or None
        """
        import json
        
        full_key = f"{namespace}:{key}"
        value = await self.client.get(full_key)
        
        if value:
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        return None

    async def invalidate_cache(
        self,
        key: str,
        namespace: str = "cache",
    ) -> bool:
        """
        Invalidate cached value.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if invalidated
        """
        full_key = f"{namespace}:{key}"
        success = await self.client.delete(full_key)
        
        logger.debug(f"Invalidated cache: {full_key}")
        return success


# Singleton instance
working_memory_service = WorkingMemoryService()
