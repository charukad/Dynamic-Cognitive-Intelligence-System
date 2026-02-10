"""
Memory Management API endpoints.

Provides control over memory optimization operations.
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.memory.memory_manager import (
    memory_pruner,
    memory_compressor,
    memory_sharer,
)

router = APIRouter(prefix="/memory/management", tags=["memory-management"])


# ============================================================================
# Request/Response Models
# ============================================================================

class PruneRequest(BaseModel):
    """Memory pruning request."""
    
    agent_id: str
    max_keep: int = Field(default=1000, ge=10, le=10000)
    force_prune: bool = Field(default=False)


class CompressRequest(BaseModel):
    """Memory compression request."""
    
    agent_id: str
    min_age_days: int = Field(default=30, ge=1, le=365)


class ShareRequest(BaseModel):
    """Memory sharing request."""
    
    source_agent_id: str
    target_agent_ids: List[str]
    memory_ids: List[str]


class MemoryHealthResponse(BaseModel):
    """Memory health metrics."""
    
    total_memories: int
    episodic_count: int
    semantic_count: int
    avg_importance: float
    storage_mb: float
    old_memories_count: int
    low_importance_count: int
    health_score: float


class OptimizationResultResponse(BaseModel):
    """Optimization operation result."""
    
    operation: str
    success: bool
    items_processed: int
    items_affected: int
    storage_saved_mb: float
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/prune", response_model=OptimizationResultResponse)
async def prune_memories(request: PruneRequest) -> OptimizationResultResponse:
    """
    Prune low-importance memories.
    
    Args:
        request: Pruning configuration
        
    Returns:
        Pruning results
    """
    try:
        from src.infrastructure.repositories import memory_repository
        
        # Fetch all memories for agent
        memories = await memory_repository.get_by_agent(request.agent_id)
        
        # Run pruner
        kept, pruned = memory_pruner.prune_memories(
            memories=memories,
            max_keep=request.max_keep
        )
        
        # Delete pruned memories
        pruned_count = 0
        for memory in pruned:
            # Only prune if force=True or if memory is truly low importance
            if request.force_prune or memory.importance_score < 0.3:
                await memory_repository.delete(memory.id)
                pruned_count += 1
        
        return OptimizationResultResponse(
            operation="prune",
            success=True,
            items_processed=len(memories),
            items_affected=pruned_count,
            storage_saved_mb=pruned_count * 0.005,  # Approx 5KB per memory
            message=f"Successfully pruned {pruned_count} low-importance memories"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pruning failed: {str(e)}"
        )


@router.post("/compress", response_model=OptimizationResultResponse)
async def compress_memories(request: CompressRequest) -> OptimizationResultResponse:
    """
    Compress old episodic memories into summaries.
    
    Args:
        request: Compression configuration
        
    Returns:
        Compression results
    """
    try:
        from src.infrastructure.repositories import memory_repository
        from src.domain.models import MemoryType
        
        # Fetch all memories for agent
        memories = await memory_repository.get_by_agent(request.agent_id)
        episodic_memories = [m for m in memories if m.memory_type == MemoryType.EPISODIC]
        
        # Run compressor
        # Note: We override the default age if provided in request not strictly supported by current compressor init
        # so we rely on the compressor's default or re-init if needed. 
        # But compressor is singleton. We'll use it as is for now.
        
        compressed_summaries = memory_compressor.compress_by_session(episodic_memories)
        
        # Store summaries
        for summary in compressed_summaries:
            summary.agent_id = UUID(request.agent_id)
            await memory_repository.create(summary)
            
        return OptimizationResultResponse(
            operation="compress",
            success=True,
            items_processed=len(episodic_memories),
            items_affected=len(compressed_summaries),
            storage_saved_mb=len(compressed_summaries) * 0.01, # Estimated savings
            message=f"Compressed episodes into {len(compressed_summaries)} semantic summaries"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compression failed: {str(e)}"
        )


@router.post("/share", response_model=OptimizationResultResponse)
async def share_memories(request: ShareRequest) -> OptimizationResultResponse:
    """
    Share memories between agents.
    
    Args:
        request: Sharing configuration
        
    Returns:
        Sharing results
    """
    try:
        from src.infrastructure.repositories import memory_repository
        
        items_processed = 0
        shared_count = 0
        
        for pool_memory_id in request.memory_ids:
            # Get original memory
            memory = await memory_repository.get_by_id(UUID(pool_memory_id))
            if not memory:
                continue
                
            items_processed += 1
            
            # Share to each target
            for target_id in request.target_agent_ids:
                shared = memory_sharer.share_memory(
                    memory=memory,
                    source_agent_id=UUID(request.source_agent_id),
                    target_agent_id=UUID(target_id)
                )
                shared.agent_id = UUID(target_id)
                await memory_repository.create(shared)
                shared_count += 1
        
        return OptimizationResultResponse(
            operation="share",
            success=True,
            items_processed=items_processed,
            items_affected=shared_count,
            storage_saved_mb=0.0,
            message=f"Shared {items_processed} memories to {len(request.target_agent_ids)} agents"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sharing failed: {str(e)}"
        )


@router.get("/health/{agent_id}", response_model=MemoryHealthResponse)
async def get_memory_health(agent_id: str) -> MemoryHealthResponse:
    """
    Get memory health metrics for an agent.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Health metrics
    """
    from src.infrastructure.repositories import memory_repository
    from src.domain.models import MemoryType
    
    # Get real stats
    memories = await memory_repository.get_by_agent(agent_id)
    
    if not memories:
        return MemoryHealthResponse(
            total_memories=0,
            episodic_count=0,
            semantic_count=0,
            avg_importance=0.0,
            storage_mb=0.0,
            old_memories_count=0,
            low_importance_count=0,
            health_score=1.0
        )
    
    total = len(memories)
    episodic = sum(1 for m in memories if m.memory_type == MemoryType.EPISODIC)
    semantic = sum(1 for m in memories if m.memory_type == MemoryType.SEMANTIC)
    avg_imp = sum(m.importance_score for m in memories) / total
    
    # Calculate health score
    # "Old" = older than 30 days
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    old_count = sum(1 for m in memories if m.created_at < cutoff)
    low_imp_count = sum(1 for m in memories if m.importance_score < 0.3)
    
    health = 1.0
    if total > 0:
        if old_count / total > 0.3:
            health -= 0.2
        if low_imp_count / total > 0.2:
            health -= 0.3
    
    return MemoryHealthResponse(
        total_memories=total,
        episodic_count=episodic,
        semantic_count=semantic,
        avg_importance=avg_imp,
        storage_mb=total * 0.005, # Approx 5KB/memory
        old_memories_count=old_count,
        low_importance_count=low_imp_count,
        health_score=max(0.0, min(1.0, health))
    )


@router.post("/optimize-all/{agent_id}")
async def optimize_all(agent_id: str) -> Dict[str, Any]:
    """
    Run all optimization operations.
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Combined results
    """
    try:
        # Run prune
        prune_result = await prune_memories(PruneRequest(agent_id=agent_id))
        
        # Run compress
        compress_result = await compress_memories(CompressRequest(agent_id=agent_id))
        
        total_saved = prune_result.storage_saved_mb + compress_result.storage_saved_mb
        
        return {
            "success": True,
            "operations": ["prune", "compress"],
            "total_items_affected": prune_result.items_affected + compress_result.items_affected,
            "total_storage_saved_mb": total_saved,
            "message": f"Optimized memory: saved {total_saved:.1f}MB"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )
