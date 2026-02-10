"""
GAIA API - General Endpoints
"""

from typing import Any, Dict

from fastapi import APIRouter

from src.services.advanced.gaia.evolution_engine import evolution_engine

router = APIRouter(prefix="/gaia", tags=["gaia"])


@router.get("/stats")
async def get_gaia_stats() -> Dict[str, Any]:
    """Get general GAIA statistics."""
    return evolution_engine.get_stats()
