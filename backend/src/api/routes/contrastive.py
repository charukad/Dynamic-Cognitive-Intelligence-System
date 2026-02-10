"""
Contrastive Learning API Endpoints

REST API for contradiction detection and consistency checking.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.contrastive import contrastive_service


router = APIRouter(prefix="/v1/contrastive", tags=["contrastive"])


# Request/Response Models
class CheckStatementRequest(BaseModel):
    """Request to check statement consistency"""
    statement: str = Field(..., description="Statement to check")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (user_id, session_id)")


class DetectContradictionRequest(BaseModel):
    """Request to detect contradiction between two statements"""
    statement1: str = Field(..., description="First statement")
    statement2: str = Field(..., description="Second statement")


class AgentConsistencyRequest(BaseModel):
    """Request to check agent consistency"""
    time_window_hours: Optional[int] = Field(24, description="Time window in hours")


# Endpoints
@router.post("/check", status_code=status.HTTP_200_OK)
async def check_statement_consistency(request: CheckStatementRequest):
    """
    Check if a new statement is consistent with existing knowledge.
    
    Returns conflicts if found.
    """
    result = await contrastive_service.check_statement_consistency(
        request.statement,
        request.context
    )
    
    return result


@router.post("/detect", status_code=status.HTTP_200_OK)
async def detect_contradiction(request: DetectContradictionRequest):
    """
    Detect contradiction between two statements.
    
    Returns detailed contradiction analysis.
    """
    result = await contrastive_service.detect_contradiction(
        request.statement1,
        request.statement2
    )
    
    return result


@router.get("/conflicts", status_code=status.HTTP_200_OK)
async def get_conflicts(
    min_severity: Optional[str] = None,
    limit: int = 50
):
    """
    Get all detected conflicts.
    
    Optional filtering by severity (low, medium, high, critical).
    """
    if min_severity and min_severity not in ['low', 'medium', 'high', 'critical']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid severity. Must be: low, medium, high, or critical"
        )
    
    conflicts = await contrastive_service.get_all_conflicts(min_severity, limit)
    
    return {"conflicts": conflicts, "total": len(conflicts)}


@router.post("/resolve/{conflict_id}", status_code=status.HTTP_200_OK)
async def resolve_conflict(conflict_id: int):
    """
    Mark a conflict as resolved.
    """
    success = await contrastive_service.resolve_conflict(conflict_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found"
        )
    
    return {"message": f"Conflict {conflict_id} resolved"}


@router.get("/agent/{agent_id}/consistency", status_code=status.HTTP_200_OK)
async def check_agent_consistency(
    agent_id: str,
    time_window_hours: int = 24
):
    """
    Check consistency of an agent's responses over time.
    """
    from datetime import timedelta
    time_window = timedelta(hours=time_window_hours)
    
    result = await contrastive_service.check_agent_consistency(agent_id, time_window)
    
    return result


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_consistency_metrics():
    """
    Get system-wide consistency metrics.
    
    Returns overall health status and conflict statistics.
    """
    metrics = await contrastive_service.get_consistency_metrics()
    
    return metrics
