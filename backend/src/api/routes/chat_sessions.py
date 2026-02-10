"""
Chat Sessions List API

Returns list of all chat sessions with metadata
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pathlib import Path
import json
from datetime import datetime

from src.core import get_logger

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.get("/chat/sessions")
async def list_chat_sessions(limit: int = 50) -> Dict[str, Any]:
    """
    List all chat sessions with metadata.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        Dictionary with sessions list
    """
    try:
        # Get chat sessions directory
        sessions_dir = Path(__file__).parent.parent.parent.parent / "data" / "chat_sessions"
        
        if not sessions_dir.exists():
            return {"sessions": [], "count": 0}
        
        sessions = []
        
        # Iterate through all session files
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                messages = data.get('messages', [])
                
                # Generate title from first user message
                title = "New Chat"
                if messages:
                    for msg in messages:
                        if msg.get('sender') == 'user':
                            title = msg.get('content', 'New Chat')[:50]
                            if len(msg.get('content', '')) > 50:
                                title += '...'
                            break
                
                session_info = {
                    "session_id": data.get('session_id', session_file.stem),
                    "title": title,
                    "created_at": data.get('created_at'),
                    "updated_at": data.get('updated_at'),
                    "message_count": len(messages),
                    "last_message": messages[-1].get('content', '')[:100] if messages else ""
                }
                
                sessions.append(session_info)
                
            except Exception as e:
                logger.warning(f"Failed to read session {session_file}: {e}")
                continue
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        # Limit results
        sessions = sessions[:limit]
        
        logger.info(f"Retrieved {len(sessions)} chat sessions")
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
