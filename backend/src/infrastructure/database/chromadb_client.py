"""ChromaDB client for vector storage."""

from typing import Any, Optional

import httpx

from src.core import get_logger, settings

logger = get_logger(__name__)


class ChromaDBClient:
    """ChromaDB HTTP client for vector storage."""

    def __init__(self) -> None:
        """Initialize ChromaDB client."""
        self.base_url = settings.chroma_url
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Connect to ChromaDB."""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        logger.info(f"Connected to ChromaDB at {self.base_url}")

    async def disconnect(self) -> None:
        """Disconnect from ChromaDB."""
        if self.client:
            await self.client.aclose()
            logger.info("Disconnected from ChromaDB")
    
    async def health_check(self) -> bool:
        """
        Verify ChromaDB connection is healthy.
        
        Returns:
            True if healthy
            
        Raises:
            RuntimeError: If health check fails
        """
        if not self.client:
            raise RuntimeError("ChromaDB client not initialized")
        
        try:
        # Try to pulse/heartbeat as health check
            response = await self.client.get("/api/v2/heartbeat")
            response.raise_for_status()
            logger.debug("ChromaDB health check passed")
            return True
        except Exception as e:
            raise RuntimeError(f"ChromaDB health check failed: {e}") from e


    async def create_collection(self, name: str) -> dict[str, Any]:
        """Create a collection."""
        if not self.client:
            raise RuntimeError("Client not connected")
        
        response = await self.client.post(
            "/api/v2/collections",
            json={"name": name, "metadata": {}},
        )
        response.raise_for_status()
        return response.json()

    async def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        embeddings: list[list[float]],
        ids: list[str],
        metadatas: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Add documents to collection."""
        if not self.client:
            raise RuntimeError("Client not connected")

        payload: dict[str, Any] = {
            "documents": documents,
            "embeddings": embeddings,
            "ids": ids,
        }
        if metadatas:
            payload["metadatas"] = metadatas

        response = await self.client.post(
            f"/api/v2/collections/{collection_name}/add",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]],
        n_results: int = 10,
    ) -> dict[str, Any]:
        """Query collection by embedding."""
        if not self.client:
            raise RuntimeError("Client not connected")

        response = await self.client.post(
            f"/api/v2/collections/{collection_name}/query",
            json={"query_embeddings": query_embeddings, "n_results": n_results},
        )
        response.raise_for_status()
        return response.json()


# Global instance
chroma_client = ChromaDBClient()
