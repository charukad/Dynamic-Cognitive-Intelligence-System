"""
Tournament API endpoints for agent competitions.
"""

from typing import Any, Dict, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/gaia/tournament", tags=["tournaments"])


class TournamentResponse(BaseModel):
    """Tournament data."""
    
    id: str
    format: str  # "round_robin", "elimination", "ranked"
    status: str  # "active", "completed", "pending"
    participants: int
    rounds_completed: int
    total_rounds: int
    start_time: str
    leaderboard: List[Dict[str, Any]]


@router.get("/latest")
async def get_latest_tournament() -> TournamentResponse:
    """Get the latest tournament data."""
    
    return TournamentResponse(
        id="tournament-demo-1",
        format="round_robin",
        status="active",
        participants=4,
        rounds_completed=2,
        total_rounds=6,
        start_time=datetime.now().isoformat(),
        leaderboard=[
            {"rank": 1, "agent_id": "data-analyst", "score": 950, "wins": 5, "losses": 1},
            {"rank": 2, "agent_id": "financial", "score": 920, "wins": 4, "losses": 2},
            {"rank": 3, "agent_id": "designer", "score": 880, "wins": 3, "losses": 3},
            {"rank": 4, "agent_id": "translator", "score": 850, "wins": 2, "losses": 4},
        ]
    )


@router.get("/active")
async def get_active_tournaments() -> List[TournamentResponse]:
    """Get all active tournaments."""
    latest = await get_latest_tournament()
    return [latest]
