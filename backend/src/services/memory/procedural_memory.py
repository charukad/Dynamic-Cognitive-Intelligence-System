"""Procedural memory for storing successful patterns and playbooks."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Memory, MemoryType
from src.infrastructure.repositories import memory_repository

logger = get_logger(__name__)


class ProceduralMemoryService:
    """
    Service for managing procedural memory (how-to knowledge).
    
    Stores successful patterns, playbooks, and procedures that can be
    retrieved and applied to similar situations.
    """

    def __init__(self) -> None:
        """Initialize procedural memory service."""
        self.repository = memory_repository
        self.playbooks: Dict[str, Dict[str, Any]] = {}

    async def store_playbook(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        success_rate: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        Store a successful playbook.
        
        Args:
            name: Playbook name
            steps: List of steps in the playbook
            success_rate: Historical success rate
            tags: Optional tags for categorization
            metadata: Additional metadata
            
        Returns:
            Created memory
        """
        logger.info(f"Storing playbook: {name}")

        # Create playbook content
        content = self._format_playbook(name, steps)
        
        # Store as procedural memory
        memory = Memory(
            content=content,
            memory_type=MemoryType.PROCEDURAL,
            importance_score=success_rate,
            tags=tags or [],
            metadata={
                "playbook_name": name,
                "steps_count": len(steps),
                "success_rate": success_rate,
                **(metadata or {}),
            },
        )
        
        created = await self.repository.create(memory)
        
        # Cache playbook
        self.playbooks[name] = {
            "id": str(created.id),
            "steps": steps,
            "success_rate": success_rate,
            "tags": tags or [],
        }
        
        logger.info(f"Playbook '{name}' stored with {len(steps)} steps")
        
        return created

    async def retrieve_playbook(
        self,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a playbook by name.
        
        Args:
            name: Playbook name
            
        Returns:
            Playbook data or None
        """
        # Check cache first
        if name in self.playbooks:
            return self.playbooks[name]
        
        # Search in repository
        all_memories = await self.repository.list(limit=1000)
        
        for memory in all_memories:
            if (
                memory.memory_type == MemoryType.PROCEDURAL
                and memory.metadata.get("playbook_name") == name
            ):
                playbook = {
                    "id": str(memory.id),
                    "steps": self._extract_steps(memory.content),
                    "success_rate": memory.metadata.get("success_rate", 0.0),
                    "tags": memory.tags,
                }
                
                # Update cache
                self.playbooks[name] = playbook
                
                return playbook
        
        logger.warning(f"Playbook not found: {name}")
        return None

    async def find_similar_playbooks(
        self,
        query: str,
        min_success_rate: float = 0.5,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find playbooks similar to query.
        
        Args:
            query: Query string
            min_success_rate: Minimum success rate filter
            limit: Maximum results
            
        Returns:
            List of matching playbooks
        """
        logger.info(f"Finding playbooks for: {query}")

        # Get all procedural memories
        all_memories = await self.repository.list(limit=1000)
        
        matching_playbooks = []
        
        for memory in all_memories:
            if memory.memory_type != MemoryType.PROCEDURAL:
                continue
            
            success_rate = memory.metadata.get("success_rate", 0.0)
            
            if success_rate < min_success_rate:
                continue
            
            # Simple text matching (can be enhanced with embeddings)
            query_lower = query.lower()
            content_lower = memory.content.lower()
            
            if any(word in content_lower for word in query_lower.split()):
                matching_playbooks.append({
                    "id": str(memory.id),
                    "name": memory.metadata.get("playbook_name", "Unknown"),
                    "steps": self._extract_steps(memory.content),
                    "success_rate": success_rate,
                    "tags": memory.tags,
                    "relevance": self._calculate_relevance(query, memory.content),
                })
        
        # Sort by relevance and success rate
        matching_playbooks.sort(
            key=lambda x: (x["relevance"], x["success_rate"]),
            reverse=True,
        )
        
        return matching_playbooks[:limit]

    async def update_success_rate(
        self,
        playbook_name: str,
        success: bool,
    ) -> bool:
        """
        Update playbook success rate based on outcome.
        
        Args:
            playbook_name: Name of playbook
            success: Whether execution was successful
            
        Returns:
            True if updated
        """
        playbook = await self.retrieve_playbook(playbook_name)
        
        if not playbook:
            return False
        
        # Get memory
        memory_id = UUID(playbook["id"])
        memory = await self.repository.get_by_id(memory_id)
        
        if not memory:
            return False
        
        # Update success rate (simple moving average)
        current_rate = memory.metadata.get("success_rate", 0.5)
        executions = memory.metadata.get("executions", 0)
        
        new_rate = (current_rate * executions + (1.0 if success else 0.0)) / (executions + 1)
        
        memory.metadata["success_rate"] = new_rate
        memory.metadata["executions"] = executions + 1
        memory.importance_score = new_rate
        
        await self.repository.update(memory)
        
        # Update cache
        if playbook_name in self.playbooks:
            self.playbooks[playbook_name]["success_rate"] = new_rate
        
        logger.info(
            f"Updated playbook '{playbook_name}' success rate: {new_rate:.2f}"
        )
        
        return True

    async def cache_successful_pattern(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any],
        context: Optional[str] = None,
    ) -> Memory:
        """
        Cache a successful pattern for future use.
        
        Args:
            pattern_name: Name of the pattern
            pattern_data: Pattern data
            context: Optional context description
            
        Returns:
            Created memory
        """
        logger.info(f"Caching pattern: {pattern_name}")

        content = f"Pattern: {pattern_name}\n"
        if context:
            content += f"Context: {context}\n"
        content += f"Data: {pattern_data}"
        
        memory = Memory(
            content=content,
            memory_type=MemoryType.PROCEDURAL,
            importance_score=0.7,
            tags=["pattern", pattern_name],
            metadata={
                "pattern_name": pattern_name,
                "pattern_type": "cached",
                "pattern_data": pattern_data,
            },
        )
        
        return await self.repository.create(memory)

    def _format_playbook(
        self,
        name: str,
        steps: List[Dict[str, Any]],
    ) -> str:
        """
        Format playbook as text.
        
        Args:
            name: Playbook name
            steps: Steps list
            
        Returns:
            Formatted text
        """
        content = f"Playbook: {name}\n\nSteps:\n"
        
        for i, step in enumerate(steps, 1):
            content += f"{i}. {step.get('action', 'Unknown action')}\n"
            if step.get('description'):
                content += f"   Description: {step['description']}\n"
        
        return content

    def _extract_steps(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract steps from playbook content.
        
        Args:
            content: Playbook content
            
        Returns:
            List of steps
        """
        # Simple extraction - can be enhanced
        steps = []
        
        in_steps = False
        for line in content.split('\n'):
            if line.strip().startswith("Steps:"):
                in_steps = True
                continue
            
            if in_steps and line.strip():
                if line.strip()[0].isdigit():
                    step_text = line.split('.', 1)[1].strip() if '.' in line else line
                    steps.append({"action": step_text})
        
        return steps

    def _calculate_relevance(self, query: str, content: str) -> float:
        """
        Calculate relevance score.
        
        Args:
            query: Query string
            content: Content to match
            
        Returns:
            Relevance score 0-1
        """
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        
        return len(intersection) / len(query_words)


# Singleton instance
procedural_memory_service = ProceduralMemoryService()
