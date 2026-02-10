"""Semantic memory service for storing general knowledge."""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Memory, MemoryType
from src.infrastructure.database import chroma_client
from src.infrastructure.llm import vllm_client
from src.infrastructure.repositories import memory_repository

logger = get_logger(__name__)


class SemanticMemoryService:
    """
    Service for managing semantic memories (facts, knowledge, concepts).
    
    Semantic memories represent learned knowledge independent of context.
    """

    def __init__(self) -> None:
        """Initialize semantic memory service."""
        self.collection_name = "semantic_memories"

    async def store_knowledge(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance_score: float = 0.7,
    ) -> Memory:
        """
        Store semantic knowledge.
        
        Args:
            content: Knowledge content
            tags: Optional categorization tags
            importance_score: Knowledge importance
            
        Returns:
            Created memory
        """
        # Generate embedding
        try:
            embedding = await vllm_client.get_embedding(content)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            embedding = None

        # Create memory
        memory = Memory(
            memory_type=MemoryType.SEMANTIC,
            content=content,
            embedding=embedding,
            importance_score=importance_score,
            tags=tags or [],
        )

        # Store in repository
        stored_memory = await memory_repository.create(memory)
        
        # Store in ChromaDB
        if embedding:
            try:
                await chroma_client.add_documents(
                    collection_name=self.collection_name,
                    documents=[content],
                    embeddings=[embedding],
                    ids=[str(stored_memory.id)],
                    metadatas=[{
                        "importance": importance_score,
                        "tags": ",".join(tags) if tags else "",
                    }],
                )
            except Exception as e:
                logger.warning(f"Failed to store in ChromaDB: {e}")

        logger.info(f"Stored semantic memory: {stored_memory.id}")
        return stored_memory

    def _calculate_forgetting_score(self, memory: Memory) -> float:
        """
        Calculate memory retention score based on Ebbinghaus forgetting curve.
        
        The forgetting curve models memory decay over time with the formula:
        R = e^(-t/S)
        
        Where:
        - R = retention probability (0-1)
        - t = time since last access in days
        - S = memory strength (determined by access_count and importance)
        
        Args:
            memory: Memory object to score
            
        Returns:
            Retention score (0-1), higher means better retained
        """
        now = datetime.now()
        
        # Calculate time since last access (in days)
        if memory.last_accessed:
            time_delta = now - memory.last_accessed
            days_since_access = time_delta.total_seconds() / 86400  # Convert to days
        else:
            # If never accessed, use creation time
            time_delta = now - memory.created_at
            days_since_access = time_delta.total_seconds() / 86400
        
        # Calculate memory strength S based on:
        # 1. Importance score (0-1)
        # 2. Access count (more accesses = stronger memory)
        # 3. Base strength
        base_strength = 1.0  # Base decay rate (days)
        importance_factor = 1.0 + (memory.importance_score * 2.0)  # 1-3x multiplier
        access_factor = 1.0 + math.log(1 + memory.access_count)  # Logarithmic scaling
        
        strength = base_strength * importance_factor * access_factor
        
        # Apply forgetting curve: R = e^(-t/S)
        retention = math.exp(-days_since_access / strength)
        
        return retention

    async def retrieve_knowledge(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None,
        use_forgetting_curve: bool = True,
    ) -> List[Memory]:
        """
        Retrieve relevant semantic knowledge with forgetting curve ranking.
        
        Args:
            query: Knowledge query
            limit: Maximum results
            tags: Optional tag filters
            use_forgetting_curve: Apply forgetting curve re-ranking
            
        Returns:
            List of relevant knowledge memories, ranked by semantic similarity
            and retention score
        """
        try:
            # Generate query embedding
            query_embedding = await vllm_client.get_embedding(query)
            
            # Search in ChromaDB (get more results for re-ranking)
            search_limit = limit * 3 if use_forgetting_curve else limit
            results = await chroma_client.query(
                collection_name=self.collection_name,
                query_embeddings=[query_embedding],
                n_results=search_limit,
            )
            
            # Retrieve full memory objects
            if results.get("ids"):
                memory_ids = [UUID(id) for id in results["ids"][0]]
                distances = results.get("distances", [[]])[0]  # Similarity distances
                
                memories_with_scores = []
                for idx, memory_id in enumerate(memory_ids):
                    memory = await memory_repository.get_by_id(memory_id)
                    if memory:
                        # Filter by tags if specified
                        if tags and not any(tag in memory.tags for tag in tags):
                            continue
                        
                        # Calculate combined score
                        similarity_score = 1.0 - (distances[idx] if idx < len(distances) else 0.5)
                        
                        if use_forgetting_curve:
                            # Apply forgetting curve
                            retention_score = self._calculate_forgetting_score(memory)
                            
                            # Combined score: 70% similarity, 30% retention
                            final_score = (0.7 * similarity_score) + (0.3 * retention_score)
                        else:
                            final_score = similarity_score
                        
                        memories_with_scores.append((memory, final_score))
                
                # Sort by combined score and take top results
                memories_with_scores.sort(key=lambda x: x[1], reverse=True)
                top_memories = [mem for mem, _ in memories_with_scores[:limit]]
                
                # Mark as accessed and update
                for memory in top_memories:
                    memory.mark_accessed()
                    await memory_repository.update(memory)
                
                return top_memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge: {e}")
        
        return []

    async def get_all_knowledge(self, tags: Optional[List[str]] = None) -> List[Memory]:
        """
        Get all semantic memories, optionally filtered by tags.
        
        Args:
            tags: Optional tag filters
            
        Returns:
            List of semantic memories
        """
        all_memories = await memory_repository.get_by_type(MemoryType.SEMANTIC.value)
        
        if tags:
            return [m for m in all_memories if any(tag in m.tags for tag in tags)]
        
        return all_memories

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get semantic memory statistics.
        
        Returns:
            Dictionary containing memory stats
        """
        memories = await memory_repository.get_by_type(MemoryType.SEMANTIC.value)
        total_count = len(memories)
        
        return {
            "total_count": total_count,
            "avg_importance": sum(m.importance_score for m in memories) / total_count if total_count > 0 else 0.0,
        }



# Singleton instance
semantic_memory_service = SemanticMemoryService()
