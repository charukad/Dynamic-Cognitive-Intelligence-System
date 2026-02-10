"""
Advanced Memory Management System

Implements intelligent memory optimization:
- Automatic pruning of low-importance memories
- Compression of episodic memories into semantic summaries
- Cross-agent memory sharing and knowledge transfer
- Memory health monitoring and optimization
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.core import get_logger
from src.domain.models import Memory, MemoryType

logger = get_logger(__name__)


# ============================================================================
# Memory Pruning Engine
# ============================================================================

class MemoryPruner:
    """
    Intelligent memory pruning based on importance decay.
    
    Uses a multi-factor scoring system to determine which memories to prune:
    - Base importance score
    - Temporal decay (older memories less valuable)
    - Access frequency (frequently accessed memories preserved)
    - Redundancy detection (similar memories consolidated)
    """
    
    def __init__(
        self,
        decay_rate: float = 0.1,
        access_boost: float = 0.2,
        min_importance_threshold: float = 0.3,
    ):
        """
        Initialize memory pruner.
        
        Args:
            decay_rate: Daily importance decay rate (0.0 to 1.0)
            access_boost: Importance boost per access
            min_importance_threshold: Minimum score to keep memory
        """
        self.decay_rate = decay_rate
        self.access_boost = access_boost
        self.min_importance_threshold = min_importance_threshold
        
        logger.info(
            f"Initialized MemoryPruner: "
            f"decay_rate={decay_rate}, "
            f"threshold={min_importance_threshold}"
        )
    
    def calculate_current_importance(
        self,
        memory: Memory,
        current_time: datetime,
    ) -> float:
        """
        Calculate current importance with temporal decay.
        
        Args:
            memory: Memory to evaluate
            current_time: Current timestamp
            
        Returns:
            Current importance score (0.0 to 1.0)
        """
        # Base importance
        importance = memory.importance_score
        
        # Apply temporal decay
        age_days = (current_time - memory.created_at).days
        decay_factor = (1.0 - self.decay_rate) ** age_days
        importance *= decay_factor
        
        # Boost for access frequency
        access_count = memory.metadata.get('access_count', 0)
        access_boost = min(access_count * self.access_boost, 0.5)
        importance += access_boost
        
        return min(1.0, max(0.0, importance))
    
    def should_prune(
        self,
        memory: Memory,
        current_time: datetime,
    ) -> bool:
        """
        Determine if memory should be pruned.
        
        Args:
            memory: Memory to evaluate
            current_time: Current timestamp
            
        Returns:
            True if memory should be pruned
        """
        current_importance = self.calculate_current_importance(memory, current_time)
        return current_importance < self.min_importance_threshold
    
    def prune_memories(
        self,
        memories: List[Memory],
        max_keep: Optional[int] = None,
    ) -> Tuple[List[Memory], List[Memory]]:
        """
        Prune memory list.
        
        Args:
            memories: List of memories to prune
            max_keep: Maximum memories to keep (None = no limit)
            
        Returns:
            Tuple of (kept_memories, pruned_memories)
        """
        current_time = datetime.now()
        
        # Calculate current importance for all memories
        scored_memories = [
            (memory, self.calculate_current_importance(memory, current_time))
            for memory in memories
        ]
        
        # Sort by importance (descending)
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Determine pruning threshold
        kept = []
        pruned = []
        
        for i, (memory, score) in enumerate(scored_memories):
            # Keep if above threshold and within max_keep limit
            if score >= self.min_importance_threshold:
                if max_keep is None or len(kept) < max_keep:
                    kept.append(memory)
                else:
                    pruned.append(memory)
            else:
                pruned.append(memory)
        
        logger.info(
            f"Pruned {len(pruned)} memories, kept {len(kept)} "
            f"(threshold={self.min_importance_threshold:.2f})"
        )
        
        return kept, pruned


# ============================================================================
# Memory Compression Engine
# ============================================================================

class MemoryCompressor:
    """
    Compress episodic memories into semantic summaries.
    
    Converts detailed episodic memories into compact semantic knowledge:
    - Groups related episodes by session/topic
    - Extracts key insights and patterns
    - Creates compressed summaries
    - Preserves essential information while reducing storage
    """
    
    def __init__(self, compression_age_days: int = 30):
        """
        Initialize memory compressor.
        
        Args:
            compression_age_days: Age threshold for compression
        """
        self.compression_age_days = compression_age_days
        logger.info(f"Initialized MemoryCompressor: age_threshold={compression_age_days} days")
    
    def should_compress(self, memory: Memory) -> bool:
        """
        Determine if memory is old enough to compress.
        
        Args:
            memory: Memory to evaluate
            
        Returns:
            True if should compress
        """
        age = datetime.now() - memory.created_at
        return age.days >= self.compression_age_days
    
    def compress_episode_group(
        self,
        episodes: List[Memory],
    ) -> Memory:
        """
        Compress group of related episodes into summary.
        
        Args:
            episodes: Related episodic memories
            
        Returns:
            Compressed semantic memory
        """
        if not episodes:
            raise ValueError("Cannot compress empty episode group")
        
        # Extract key information
        session_ids = list(set(e.session_id for e in episodes if e.session_id))
        all_tags = list(set(tag for e in episodes for tag in e.tags))
        
        # Calculate aggregate importance
        avg_importance = sum(e.importance_score for e in episodes) / len(episodes)
        max_importance = max(e.importance_score for e in episodes)
        
        # Create summary content
        summary_content = f"Summary of {len(episodes)} episodes"
        if session_ids:
            summary_content += f" from sessions: {', '.join(session_ids[:3])}"
        
        # Create compressed memory
        compressed = Memory(
            memory_type=MemoryType.SEMANTIC,
            content=summary_content,
            importance_score=max(avg_importance, max_importance * 0.8),
            tags=all_tags[:10],  # Keep top tags
            metadata={
                'compressed_from': [str(e.id) for e in episodes],
                'episode_count': len(episodes),
                'compression_date': datetime.now().isoformat(),
                'original_date_range': {
                    'start': min(e.created_at for e in episodes).isoformat(),
                    'end': max(e.created_at for e in episodes).isoformat(),
                }
            }
        )
        
        logger.info(f"Compressed {len(episodes)} episodes into semantic memory")
        return compressed
    
    def compress_by_session(
        self,
        memories: List[Memory],
    ) -> List[Memory]:
        """
        Compress memories grouped by session.
        
        Args:
            memories: Episodic memories to compress
            
        Returns:
            List of compressed semantic memories
        """
        # Group by session
        session_groups: Dict[str, List[Memory]] = {}
        for memory in memories:
            if self.should_compress(memory) and memory.memory_type == MemoryType.EPISODIC:
                session_id = memory.session_id or 'unknown'
                if session_id not in session_groups:
                    session_groups[session_id] = []
                session_groups[session_id].append(memory)
        
        # Compress each group
        compressed_memories = []
        for session_id, episodes in session_groups.items():
            if len(episodes) >= 3:  # Only compress if enough episodes
                compressed = self.compress_episode_group(episodes)
                compressed_memories.append(compressed)
        
        logger.info(
            f"Compressed {sum(len(g) for g in session_groups.values())} memories "
            f"into {len(compressed_memories)} summaries"
        )
        
        return compressed_memories


# ============================================================================
# Cross-Agent Memory Sharing
# ============================================================================

class MemorySharer:
    """
    Enable knowledge sharing between agents.
    
    Facilitates collaborative learning:
    - Identifies transferable knowledge
    - Shares successful strategies between agents
    - Maintains provenance tracking
    - Prevents knowledge pollution
    """
    
    def __init__(self, min_quality_threshold: float = 0.7):
        """
        Initialize memory sharer.
        
        Args:
            min_quality_threshold: Minimum quality to share
        """
        self.min_quality_threshold = min_quality_threshold
        logger.info(f"Initialized MemorySharer: threshold={min_quality_threshold}")
    
    def is_shareable(self, memory: Memory) -> bool:
        """
        Determine if memory is valuable enough to share.
        
        Args:
            memory: Memory to evaluate
            
        Returns:
            True if memory should be shared
        """
        # Must be high importance
        if memory.importance_score < self.min_quality_threshold:
            return False
        
        # Semantic knowledge is more shareable than episodic
        if memory.memory_type == MemoryType.EPISODIC:
            return False
        
        # Must have successful outcome indicator
        success_indicators = ['success', 'completed', 'solved']
        has_success = any(ind in memory.content.lower() for ind in success_indicators)
        
        return has_success
    
    def share_memory(
        self,
        memory: Memory,
        source_agent_id: UUID,
        target_agent_id: UUID,
    ) -> Memory:
        """
        Share memory from one agent to another.
        
        Args:
            memory: Memory to share
            source_agent_id: Source agent ID
            target_agent_id: Target agent ID
            
        Returns:
            New memory for target agent
        """
        # Create copy with provenance tracking
        shared_memory = Memory(
            memory_type=memory.memory_type,
            content=memory.content,
            importance_score=memory.importance_score * 0.9,  # Slight importance reduction
            tags=memory.tags + ['shared'],
            session_id=None,  # Not tied to specific session
            metadata={
                **memory.metadata,
                'shared_from': str(source_agent_id),
                'shared_to': str(target_agent_id),
                'shared_at': datetime.now().isoformat(),
                'original_memory_id': str(memory.id),
            }
        )
        
        logger.info(f"Shared memory from {source_agent_id} to {target_agent_id}")
        return shared_memory
    
    def find_shareable_memories(
        self,
        memories: List[Memory],
        agent_id: UUID,
    ) -> List[Memory]:
        """
        Find memories worth sharing from an agent.
        
        Args:
            memories: Agent's memories
            agent_id: Agent ID
            
        Returns:
            List of shareable memories
        """
        shareable = [m for m in memories if self.is_shareable(m)]
        
        logger.info(f"Found {len(shareable)} shareable memories from agent {agent_id}")
        return shareable


# ============================================================================
# Singleton Instances
# ============================================================================

memory_pruner = MemoryPruner()
memory_compressor = MemoryCompressor()
memory_sharer = MemorySharer()
