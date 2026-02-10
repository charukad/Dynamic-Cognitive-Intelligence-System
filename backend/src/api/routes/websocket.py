"""WebSocket routes for real-time communication."""

from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from src.api.websocket.ai_services_ws import ai_services_websocket_endpoint

router = APIRouter()


@router.websocket("/ws/ai-services")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(default="default"),
    user_id: Optional[str] = Query(default=None)
):
    """
    WebSocket endpoint for AI services real-time updates.
    
    Query Parameters:
        session_id: Session/room identifier (default: "default")
        user_id: Optional user identifier for presence tracking
    
    Provides:
        - Real-time AI service progress updates
        - Presence tracking and collaboration
        - Dream cycle, GAIA match, processing notifications
        - Service status broadcasts
    """
    await ai_services_websocket_endpoint(
        websocket=websocket,
        session_id=session_id,
        user_id=user_id
    )
