"""
RLHF API - Human Feedback and Reward Modeling

Endpoints for collecting user feedback and training reward models.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.rlhf.feedback_manager import (
    feedback_manager,
    FeedbackType,
    FeedbackCategory,
)

router = APIRouter(prefix="/rlhf", tags=["rlhf"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SubmitFeedbackRequest(BaseModel):
    """Submit user feedback."""
    session_id: str
    message_id: str
    agent_id: str
    feedback_type: str  # "thumbs_up", "thumbs_down", "rating"
    user_query: str = ""
    agent_response: str = ""
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    text_feedback: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None
    model_version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Feedback Collection Endpoints
# ============================================================================

@router.post("/feedback")
async def submit_feedback(request: SubmitFeedbackRequest) -> Dict[str, Any]:
    """Submit user feedback on agent response."""
    try:
        # Parse feedback type
        feedback_type = FeedbackType(request.feedback_type)
        
        # Parse categories
        categories = [
            FeedbackCategory(cat) for cat in request.categories
            if cat in [c.value for c in FeedbackCategory]
        ]
        
        # Collect feedback
        feedback = feedback_manager.collect_feedback(
            session_id=request.session_id,
            message_id=request.message_id,
            agent_id=request.agent_id,
            feedback_type=feedback_type,
            user_query=request.user_query,
            agent_response=request.agent_response,
            rating=request.rating,
            text_feedback=request.text_feedback,
            categories=categories,
            user_id=request.user_id,
            model_version=request.model_version,
            metadata=request.metadata,
        )
        
        return {
            'success': True,
            'feedback_id': str(feedback.id),
            'message': 'Feedback recorded successfully',
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feedback data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/agent/{agent_id}")
async def get_agent_feedback(agent_id: str) -> Dict[str, Any]:
    """Get feedback summary for specific agent."""
    summary = feedback_manager.get_agent_feedback_summary(agent_id)
    return summary


@router.get("/feedback/top-agents")
async def get_top_rated_agents(limit: int = 5) -> Dict[str, Any]:
    """Get top-rated agents based on user feedback."""
    top_agents = feedback_manager.get_top_rated_agents(limit)
    
    return {
        'top_agents': top_agents,
        'count': len(top_agents),
    }


@router.get("/feedback/trends")
async def get_feedback_trends(days: int = 7) -> Dict[str, Any]:
    """Get feedback trends over time."""
    trends = feedback_manager.get_feedback_trends(days)
    return trends


# ============================================================================
# Reward Model Endpoints
# ============================================================================

@router.get("/reward-score")
async def get_reward_score(
    agent_id: str,
    response: str,
    query: str = "",
) -> Dict[str, Any]:
    """Get predicted reward score for a response."""
    score = feedback_manager.get_reward_score(agent_id, response, query)
    
    return {
        'agent_id': agent_id,
        'predicted_score': score,
        'confidence': 'high' if score > 0.7 or score < 0.3 else 'medium',
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_rlhf_stats() -> Dict[str, Any]:
    """Get overall RLHF statistics."""
    stats = feedback_manager.get_statistics()
    return stats


@router.get("/health")
async def check_rlhf_health() -> Dict[str, Any]:
    """Check RLHF system health."""
    stats = feedback_manager.get_statistics()
    
    # System is healthy if we have some feedback
    healthy = stats['total_feedback'] > 0
    
    return {
        'status': 'healthy' if healthy else 'no_data',
        'total_feedback': stats['total_feedback'],
        'agents_trained': stats['total_agents_with_models'],
    }
