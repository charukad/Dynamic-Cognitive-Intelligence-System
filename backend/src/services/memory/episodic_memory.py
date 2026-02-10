"""Episodic memory service for storing agent experiences."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Memory, MemoryType
from src.infrastructure.database import chroma_client
from src.infrastructure.llm import vllm_client
from src.infrastructure.repositories import memory_repository

logger = get_logger(__name__)


class EpisodicMemoryService:
    """
    Service for managing episodic memories (specific events/interactions).
    
    Episodic memories are stored with embeddings for semantic search.
    """

    def __init__(self) -> None:
        """Initialize episodic memory service."""
        self.collection_name = "episodic_memories"

    async def store_memory(
        self,
        content: str,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store an episodic memory.
        
        Args:
            content: Memory content
            agent_id: Associated agent ID
            task_id: Associated task ID
            session_id: Session identifier
            importance_score: Memory importance (0.0-1.0)
            tags: Optional tags
            
        Returns:
            Created memory
        """
        # Generate embedding
        try:
            embedding = await vllm_client.get_embedding(content)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}. Using None.")
            embedding = None

        # Create memory
        memory = Memory(
            memory_type=MemoryType.EPISODIC,
            content=content,
            embedding=embedding,
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id,
            importance_score=importance_score,
            tags=tags or [],
        )

        # Store in repository
        stored_memory = await memory_repository.create(memory)
        
        # Store in ChromaDB for semantic search (if embedding available)
        if embedding:
            try:
                await chroma_client.add_documents(
                    collection_name=self.collection_name,
                    documents=[content],
                    embeddings=[embedding],
                    ids=[str(stored_memory.id)],
                    metadatas=[{
                        "agent_id": str(agent_id) if agent_id else None,
                        "task_id": str(task_id) if task_id else None,
                        "session_id": session_id,
                        "importance": importance_score,
                    }],
                )
            except Exception as e:
                logger.warning(f"Failed to store in ChromaDB: {e}")

        logger.info(f"Stored episodic memory: {stored_memory.id}")
        return stored_memory

    async def retrieve_memories(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        Retrieve relevant episodic memories using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of memories to return
            min_importance: Minimum importance score filter
            
        Returns:
            List of relevant memories
        """
        try:
            # Generate query embedding
            query_embedding = await vllm_client.get_embedding(query)
            
            # Search in ChromaDB
            results = await chroma_client.query(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=limit,
            )
            
            # Retrieve full memory objects from repository
            if results.get("ids"):
                memory_ids = [UUID(id) for id in results["ids"][0]]
                memories = []
                for memory_id in memory_ids:
                    memory = await memory_repository.get_by_id(memory_id)
                    if memory and memory.importance_score >= min_importance:
                        memory.mark_accessed()
                        await memory_repository.update(memory)
                        memories.append(memory)
                return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
        
        return []

    async def get_session_memories(self, session_id: str) -> List[Memory]:
        """
        Get all memories for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of session memories
        """
        return await memory_repository.get_by_session(session_id)

    async def get_recent_sessions(self, limit: int = 10) -> List[str]:
        """
        Get recent session IDs.
        
        Args:
            limit: Maximum number of sessions
            
        Returns:
            List of session IDs
        """
        return await memory_repository.get_recent_sessions(limit)

    async def prune_memories(
        self,
        agent_id: str,
        max_keep: int = 1000,
        force_prune: bool = False
    ) -> int:
        """
        Prune low-importance memories for an agent.
        
        Args:
            agent_id: Agent ID to prune
            max_keep: Maximum number of memories to keep
            force_prune: Force pruning even if high importance
            
        Returns:
            Number of memories pruned
        """
        # Get all episodic memories for agent
        # Note: In production, use a more efficient query with ordering
        all_memories = await memory_repository.get_by_agent(agent_id)
        episodic_memories = [
            m for m in all_memories 
            if m.memory_type == MemoryType.EPISODIC
        ]
        
        if len(episodic_memories) <= max_keep:
            return 0
            
        # Sort by importance (ascending) and then age (oldest first)
        # to identify candidates for pruning
        episodic_memories.sort(key=lambda m: (m.importance_score, m.created_at))
        
        to_prune_count = len(episodic_memories) - max_keep
        pruned_count = 0
        
        for i in range(to_prune_count):
            memory = episodic_memories[i]
            
            # Skip high importance unless forced
            if not force_prune and memory.importance_score > 0.8:
                continue
                
            await memory_repository.delete(memory.id)
            
            # Also remove from ChromaDB if it has an embedding
            if memory.embedding:
                try:
                    await chroma_client.delete_document(
                        collection_name=self.collection_name,
                        document_id=str(memory.id)
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete from ChromaDB: {e}")
            
            pruned_count += 1
            
        logger.info(f"Pruned {pruned_count} memories for agent {agent_id}")
        return pruned_count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics.
        
        Returns:
            Dictionary containing memory stats
        """
        memories = await memory_repository.get_by_type(MemoryType.EPISODIC.value)
        total_count = len(memories)
        
        return {
            "total_count": total_count,
            "recent_count": 0, # Placeholder until we have filtering
            "avg_importance": sum(m.importance_score for m in memories) / total_count if total_count > 0 else 0.0,
        }



# Singleton instance
episodic_memory_service = EpisodicMemoryService()
