"""Debate orchestration API endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.debater import debater_service

router = APIRouter(prefix="/debate", tags=["debate"])


class DebateStartRequest(BaseModel):
    """Request schema to create and start a debate session."""

    topic: str = Field(..., min_length=1, description="Debate topic")
    participants: List[str] = Field(..., min_length=1, description="Participant agent IDs/types")
    rounds: int = Field(default=1, ge=1, le=10, description="Number of initial rounds to run")


class DebateRoundRequest(BaseModel):
    """Request schema to execute a specific round."""

    round: int = Field(..., ge=1, description="Round number")


@router.post("/start")
async def start_debate(request: DebateStartRequest) -> Dict[str, Any]:
    """
    Create a debate and execute initial rounds.
    """
    try:
        debate_id = await debater_service.create_debate(
            topic=request.topic,
            agent_ids=request.participants,
        )

        executed_rounds = []
        for round_number in range(1, request.rounds + 1):
            executed_rounds.append(await debater_service.execute_round(debate_id, round_number))

        return {
            "debate_id": debate_id,
            "status": "started",
            "topic": request.topic,
            "participants": request.participants,
            "rounds_executed": len(executed_rounds),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start debate: {str(e)}",
        )


@router.post("/{debate_id}/round")
async def run_debate_round(debate_id: str, request: DebateRoundRequest) -> Dict[str, Any]:
    """
    Execute one additional round for an existing debate.
    """
    round_result = await debater_service.execute_round(debate_id, request.round)
    if round_result.get("error") == "debate_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debate {debate_id} not found",
        )
    return round_result


@router.get("/{debate_id}")
async def get_debate_summary(debate_id: str) -> Dict[str, Any]:
    """
    Get summary for an existing debate.
    """
    summary = await debater_service.get_debate_summary(debate_id)
    if summary.get("error") == "debate_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debate {debate_id} not found",
        )
    return summary
