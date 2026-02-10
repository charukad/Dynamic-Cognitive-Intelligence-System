"""
Memory Statistics API

Placeholder endpoint for memory system (not yet implemented).
"""

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(tags=["memory"])


@router.get("/memory/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """
    Get memory system statistics.
    
    Returns placeholder data until memory system is fully implemented.
    """
    return {
        "semantic_count": 0,
        "episodic_count": 0,
        "avg_importance": 0.0,
        "total_memories": 0,
        "status": "not_implemented"
    }
