"""PostgreSQL database client."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg

from src.core import get_logger, settings

logger = get_logger(__name__)


class PostgresClient:
    """
    PostgreSQL client for persistent data storage.
    
    Handles connection pooling and query execution.
    """

    def __init__(self):
        """Initialize PostgreSQL client."""
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = settings.database_url

    async def connect(self) -> None:
        """Create connection pool."""
        if self.pool is not None:
            logger.warning("PostgreSQL pool already connected")
            return

        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )
            logger.info("PostgreSQL connection pool created")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool is None:
            return

        try:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")
            
        except Exception as e:
            logger.error(f"Error closing PostgreSQL pool: {e}")
    
    async def health_check(self) -> bool:
        """
        Verify PostgreSQL connection is healthy.
        
        Returns:
            True if healthy
            
        Raises:
            RuntimeError: If health check fails
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        try:
            async with self.pool.acquire() as conn:
                # Test query
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise RuntimeError("Health check query returned unexpected result")
            
            logger.debug("PostgreSQL health check passed")
            return True
            
        except Exception as e:
            raise RuntimeError(f"PostgreSQL health check failed: {e}") from e


    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Status message
        """
        async with self.acquire() as conn:
            result = await conn.execute(query, *args, timeout=timeout)
            return result

    async def fetch(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows.
        
        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout
            
        Returns:
            List of row dictionaries
        """
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args, timeout=timeout)
            return [dict(row) for row in rows]

    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.
        
        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout
            
        Returns:
            Row dictionary or None
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None

    async def fetchval(
        self,
        query: str,
        *args,
        column: int = 0,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Fetch a single value.
        
        Args:
            query: SQL query
            *args: Query parameters
            column: Column index
            timeout: Query timeout
            
        Returns:
            Single value
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def init_schema(self) -> None:
        """Initialize database schema."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS agents (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            temperature FLOAT DEFAULT 0.7,
            system_prompt TEXT NOT NULL,
            model_name VARCHAR(100) DEFAULT 'default',
            status VARCHAR(50) NOT NULL,
            capabilities TEXT[] DEFAULT '{}',
            total_tasks INTEGER DEFAULT 0,
            success_rate FLOAT DEFAULT 0.0,
            avg_response_time FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(255) PRIMARY KEY,
            description TEXT NOT NULL,
            status VARCHAR(50) NOT NULL,
            assigned_agent_id VARCHAR(255) REFERENCES agents(id),
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE TABLE IF NOT EXISTS memories (
            id VARCHAR(255) PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            importance FLOAT DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
        CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
        CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents USING GIN(capabilities);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent_id);
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
        CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
        """

        await self.execute(schema_sql)
        logger.info("PostgreSQL schema initialized")



# Global instance
postgres_client = PostgresClient()
