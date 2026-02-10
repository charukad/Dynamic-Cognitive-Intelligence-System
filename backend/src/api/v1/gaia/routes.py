"""
GAIA API Routes

REST API for the GAIA self-play system.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core import get_logger
from src.services.advanced.gaia.match_engine import (
    gaia_engine,
    OpponentType,
    MatchConfig,
    GAIAMatch
)
from src.services.advanced.gaia.tournament_system import (
    tournament_system,
    TournamentFormat,
    TournamentConfig
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/gaia", tags=["gaia"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateMatchRequest(BaseModel):
    """Request to create a match"""
    agent_id: str
    opponent_type: OpponentType = OpponentType.SYNTHETIC
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    domain: str = "general"
    rounds: int = Field(5, ge=1, le=20)
    opponent_id: Optional[str] = None


class CreateMatchResponse(BaseModel):
    """Match creation response"""
    match_id: UUID
    agent_id: str
    opponent_name: str
    opponent_type: str
    estimated_duration_seconds: float


class MatchStatusResponse(BaseModel):
    """Match status response"""
    match_id: UUID
    status: str
    current_round: int
    total_rounds: int
    agent_score: float
    opponent_score: float
    duration_seconds: Optional[float] = None


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    agent_id: str
    elo: float
    matches_played: int = 0


class CreateTournamentRequest(BaseModel):
    """Request to create tournament"""
    name: str
    agent_ids: List[str]
    format: TournamentFormat = TournamentFormat.SINGLE_ELIMINATION
    rounds_per_match: int = 5
    domain: str = "general"


class CreateTournamentResponse(BaseModel):
    """Tournament creation response"""
    tournament_id: UUID
    name: str
    format: str
    participants: int
    total_matches: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/match/create", response_model=CreateMatchResponse)
async def create_match(request: CreateMatchRequest):
    """
    Create a new self-play match.
    
    Match types:
    - SELF: Agent vs itself (discover strategies)
    - SYNTHETIC: Agent vs AI opponent (curriculum learning)
    - HISTORICAL: Agent vs past version (measure improvement)
    - PEER: Agent vs another agent (competitive learning)
    """
    try:
        match_id = await gaia_engine.create_match(
            agent_id=request.agent_id,
            opponent_type=request.opponent_type,
            config=MatchConfig(
                rounds=request.rounds,
                domain=request.domain,
                difficulty=request.difficulty
            ),
            opponent_id=request.opponent_id
        )
        
        # Get match details
        match = gaia_engine.get_match_status(match_id)
        if not match:
            raise HTTPException(status_code=500, detail="Failed to create match")
        
        # Estimate duration (0.2s per round)
        estimated_duration = request.rounds * 0.2
        
        return CreateMatchResponse(
            match_id=match_id,
            agent_id=request.agent_id,
            opponent_name=match.opponent.name,
            opponent_type=request.opponent_type.value,
            estimated_duration_seconds=estimated_duration
        )
        
    except Exception as e:
        logger.error(f"Failed to create match: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/{match_id}", response_model=MatchStatusResponse)
async def get_match_status(match_id: UUID):
    """
    Get current status of a match.
    """
    match = gaia_engine.get_match_status(match_id)
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    duration = None
    if match.start_time:
        if match.end_time:
            duration = (match.end_time - match.start_time).total_seconds()
        else:
            from datetime import datetime
            duration = (datetime.utcnow() - match.start_time).total_seconds()
    
    return MatchStatusResponse(
        match_id=match.id,
        status=match.status.value,
        current_round=match.current_round,
        total_rounds=match.config.rounds,
        agent_score=match.agent_score,
        opponent_score=match.opponent_score,
        duration_seconds=duration
    )


@router.get("/leaderboard/{domain}", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    domain: str = "general",
    limit: int = 20
):
    """
    Get ELO leaderboard for agents.
    """
    rankings = gaia_engine.get_leaderboard(domain, limit)
    
    return [
        LeaderboardEntry(
            rank=entry["rank"],
            agent_id=entry["agent_id"],
            elo=entry["elo"]
        )
        for entry in rankings
    ]


@router.post("/tournament/create", response_model=CreateTournamentResponse)
async def create_tournament(request: CreateTournamentRequest):
    """
    Create a new tournament.
    
    Formats:
    - SINGLE_ELIMINATION: Bracket-style, single loss elimination
    - ROUND_ROBIN: Everyone plays everyone
    - SWISS: Pair agents by performance each round
    """
    try:
        if len(request.agent_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 participants"
            )
        
        tournament_id = await tournament_system.create_tournament(
            name=request.name,
            agent_ids=request.agent_ids,
            format=request.format,
            config=TournamentConfig(
                format=request.format,
                rounds_per_match=request.rounds_per_match,
                domain=request.domain
            )
        )
        
        # Calculate total matches
        n = len(request.agent_ids)
        if request.format == TournamentFormat.ROUND_ROBIN:
            total_matches = n * (n - 1) // 2
        else:  # SINGLE_ELIMINATION
            total_matches = n - 1
        
        return CreateTournamentResponse(
            tournament_id=tournament_id,
            name=request.name,
            format=request.format.value,
            participants=len(request.agent_ids),
            total_matches=total_matches
        )
        
    except Exception as e:
        logger.error(f"Failed to create tournament: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tournament/{tournament_id}/start")
async def start_tournament(tournament_id: UUID):
    """
    Start a tournament.
    """
    try:
        await tournament_system.start_tournament(tournament_id)
        return {"status": "started", "tournament_id": str(tournament_id)}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start tournament: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tournament/{tournament_id}")
async def get_tournament_status(tournament_id: UUID):
    """
    Get tournament status and rankings.
    """
    tournament = tournament_system.get_tournament_status(tournament_id)
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    return {
        "tournament_id": str(tournament.id),
        "name": tournament.name,
        "format": tournament.format.value,
        "status": tournament.status.value,
        "current_round": tournament.current_round,
        "participants": len(tournament.participant_ids),
        "rankings": tournament.rankings
    }


@router.get("/stats")
async def get_gaia_stats():
    """
    Get overall GAIA system statistics.
    """
    stats = {
        "active_matches": len(gaia_engine.active_matches),
        "completed_matches": len(gaia_engine.completed_matches),
        "active_tournaments": len(tournament_system.active_tournaments),
        "completed_tournaments": len(tournament_system.completed_tournaments),
        "total_agents_ranked": len(gaia_engine.agent_ratings),
        "avg_elo": (
            sum(gaia_engine.agent_ratings.values()) / len(gaia_engine.agent_ratings)
            if gaia_engine.agent_ratings else 1500.0
        )
    }
    
    return stats
