"""
Mirror Protocol API Endpoints

REST API for digital twin management.
"""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.mirror import mirror_service


router = APIRouter(prefix="/v1/mirror", tags=["mirror"])


# Request/Response Models
class CreateTwinRequest(BaseModel):
    """Request to create digital twin"""
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="User message history with 'content', 'timestamp', 'role'"
    )


class UpdateTwinRequest(BaseModel):
    """Request to update digital twin"""
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="New messages to incorporate into twin"
    )


class SimulateRequest(BaseModel):
    """Request to simulate user response"""
    context: str = Field(..., description="Context for simulation")


class TwinResponse(BaseModel):
    """Digital twin response"""
    user_id: str
    persona_profile: Dict[str, Any]
    style_signature: Dict[str, Any]
    personality_ocean: Dict[str, float]
    personality_interpretation: Dict[str, str]
    knowledge_domains: List[str]
    interaction_count: int
    confidence_score: float
    created_at: str
    last_updated: str


# Endpoints
@router.post("/{user_id}", response_model=TwinResponse, status_code=status.HTTP_201_CREATED)
async def create_twin(user_id: str, request: CreateTwinRequest):
    """
    Create a digital twin from user's message history.
    
    Requires at least 10 messages for meaningful analysis.
    """
    if len(request.messages) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 10 messages required for twin creation"
        )
    
    # Check if twin already exists
    existing_twin = await mirror_service.get_twin(user_id)
    if existing_twin:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Twin for user {user_id} already exists. Use PUT to update."
        )
    
    twin = await mirror_service.create_twin(user_id, request.messages)
    return twin.to_dict()


@router.get("/{user_id}", response_model=TwinResponse)
async def get_twin(user_id: str):
    """Get existing digital twin profile"""
    twin = await mirror_service.get_twin(user_id)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No twin found for user {user_id}"
        )
    
    return twin.to_dict()


@router.put("/{user_id}", response_model=TwinResponse)
async def update_twin(user_id: str, request: UpdateTwinRequest):
    """Update digital twin with new interaction data"""
    twin = await mirror_service.update_twin(user_id, request.messages)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No twin found for user {user_id}. Use POST to create."
        )
    
    return twin.to_dict()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_twin(user_id: str):
    """Delete digital twin (privacy compliance)"""
    success = await mirror_service.delete_twin(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No twin found for user {user_id}"
        )
    
    return None


@router.post("/{user_id}/simulate")
async def simulate_response(user_id: str, request: SimulateRequest):
    """
    Simulate how user would respond (for testing twin accuracy).
    
    Returns predicted response characteristics, NOT actual text.
    """
    result = await mirror_service.simulate_response(user_id, request.context)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No twin found for user {user_id}"
        )
    
    return result


@router.get("/{user_id}/accuracy")
async def get_accuracy_metrics(user_id: str):
    """Get confidence and accuracy metrics for digital twin"""
    metrics = await mirror_service.get_twin_accuracy_metrics(user_id)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No twin found for user {user_id}"
        )
    
    return metrics


@router.get("/")
async def list_twins():
    """List all digital twins (admin endpoint)"""
    twins = await  mirror_service.list_twins()
    return {"twins": twins, "total": len(twins)}
