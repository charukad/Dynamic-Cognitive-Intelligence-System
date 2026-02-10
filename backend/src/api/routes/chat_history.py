"""
Chat History API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.infrastructure.repositories.chat_repository import chat_repository
from src.core import get_logger

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get chat history for a session.
    
    Args:
        session_id: Chat session ID
        limit: Maximum number of messages to return
        
    Returns:
        Dictionary with messages list
    """
    try:
        messages = await chat_repository.get_session_history(session_id, limit)
        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/history/{session_id}/message")
async def save_chat_message(
    session_id: str,
    message_id: str,
    sender: str,
    content: str,
    agent_id: str = None,
    agent_name: str = None
) -> Dict[str, Any]:
    """
    Save a single chat message to history.
    
    Args:
        session_id: Chat session ID
        message_id: Unique message ID
        sender: Message sender ('user' or 'agent')
        content: Message content
        agent_id: Optional agent ID
        agent_name: Optional agent name
        
    Returns:
        Success status
    """
    try:
        success = await chat_repository.save_message(
            session_id=session_id,
            message_id=message_id,
            sender=sender,
            content=content,
            agent_id=agent_id,
            agent_name=agent_name
        )
        
        if success:
            return {
                "status": "saved",
                "message_id": message_id,
                "session_id": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save message")
            
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str) -> Dict[str, str]:
    """
    Clear all messages in a chat session.
    
    Args:
        session_id: Chat session ID
        
    Returns:
        Success message
    """
    try:
        success = await chat_repository.clear_session(session_id)
        if success:
            return {"message": f"Cleared session {session_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear session")
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
