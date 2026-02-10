"""Application lifecycle management."""

from typing import Dict, Any
import asyncio

from src.core import get_logger
from src.infrastructure.database import (
    neo4j_client,
    chroma_client,
    redis_client,
    postgres_client,  # ✅ RESTORED
)
from src.infrastructure.llm import vllm_client

logger = get_logger(__name__)


class LifecycleManager:
    """
    Manages startup/shutdown of external dependencies.
    
    Features:
    - Dependency-ordered initialization
    - Health checks for all services
    - Graceful degradation for non-critical services
    - Proper cleanup on shutdown
    """
    
    def __init__(self):
        self._initialized = False
        self._clients: Dict[str, Any] = {
            "postgres": postgres_client,  # ✅ RESTORED
            "neo4j": neo4j_client,
            "redis": redis_client,
            "chromadb": chroma_client,
            "vllm": vllm_client,
        }
        
        # Critical services that must be available
        # ✅ UPDATED: All services optional for development/degraded mode
        # In production, you may want to make neo4j or vllm critical
        self._critical_services = set()  # Empty = all services optional
    
    async def startup(self) -> None:
        """
        Initialize all clients with health checks.
        
        Raises:
            RuntimeError: If critical service unavailable
        """
        if self._initialized:
            logger.warning("Lifecycle already initialized")
            return
        
        logger.info("🚀 Starting DCIS application...")
        
        # Initialize in dependency order
        # ✅ UPDATED: Added postgres
        initialization_order = [
            "postgres",   # Relational DB first
            "neo4j",      # Knowledge graph
            "redis",      # Cache
            "chromadb",   # Vector store
            "vllm",       # LLM inference last
        ]
        
        for client_name in initialization_order:
            client = self._clients[client_name]
            try:
                logger.info(f"Connecting to {client_name}...")
                await client.connect()
                
                # Initialize schema for Postgres
                if client_name == "postgres":
                    await client.init_schema()
                
                # Health check if available
                if hasattr(client, 'health_check'):
                    await client.health_check()
                
                logger.info(f"✅ {client_name} connected")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to {client_name}: {e}")
                
                # Fail fast on critical services
                if client_name in self._critical_services:
                    raise RuntimeError(
                        f"Critical service {client_name} unavailable"
                    ) from e
                
                # Non-critical services degraded mode
                logger.warning(
                    f"⚠️  {client_name} unavailable - running in degraded mode"
                )
                
                # Cleanup client to reflect disconnected state
                try:
                    await client.disconnect()
                except Exception:
                    pass
                 
                if hasattr(client, 'client'):
                    client.client = None
                if hasattr(client, 'driver'):
                    client.driver = None        
        self._initialized = True
        logger.info("✅ DCIS application ready!")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all clients."""
        if not self._initialized:
            return
        
        logger.info("👋 Shutting down DCIS application...")
        
        # Shutdown in reverse order
        # ✅ UPDATED: Removed postgres
        shutdown_order = [
            "vllm",
            "chromadb",
            "redis",
            "neo4j",
            "postgres",
        ]
        
        for client_name in shutdown_order:
            client = self._clients[client_name]
            try:
                logger.info(f"Disconnecting from {client_name}...")
                await client.disconnect()
                logger.info(f"✅ {client_name} disconnected")
            except Exception as e:
                logger.error(f"❌ Error disconnecting {client_name}: {e}")
        
        self._initialized = False
        logger.info("✅ DCIS application stopped")
    
    def is_initialized(self) -> bool:
        """Check if lifecycle is initialized."""
        return self._initialized
    
    def get_client_status(self) -> Dict[str, str]:
        """
        Get connection status of all clients.
        
        Returns:
            Dictionary with client names and their status
        """
        status = {}
        for client_name, client in self._clients.items():
            if hasattr(client, 'client') and client.client:
                status[client_name] = "connected"
            elif hasattr(client, 'driver') and client.driver:
                status[client_name] = "connected"
            else:
                status[client_name] = "disconnected"
        return status


# Global instance
lifecycle_manager = LifecycleManager()
