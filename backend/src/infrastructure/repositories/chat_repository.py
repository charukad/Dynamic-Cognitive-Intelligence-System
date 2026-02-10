"""
Chat History Repository

Handles persistence of chat messages and conversations using file-based storage.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from src.core import get_logger

logger = get_logger(__name__)


class ChatRepository:
    """Repository for chat message persistence using JSON files (no Redis required)."""
    
    def __init__(self):
        # Use file-based storage in backend data directory
        self.storage_dir = Path(__file__).parent.parent.parent.parent / "data" / "chat_sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Chat storage initialized at: {self.storage_dir}")
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session file."""
        # Sanitize session_id for filename
        safe_session_id = "".join(c for c in session_id if c.isalnum() or c in ('-', '_'))
        return self.storage_dir / f"{safe_session_id}.json"
    
    async def save_message(
        self,
        session_id: str,
        message_id: str,
        sender: str,  # 'user' | 'agent'
        content: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> bool:
        """
        Save a chat message to JSON file.
        
        Args:
            session_id: Chat session ID
            message_id: Unique message ID
            sender: Message sender ('user' or 'agent')
            content: Message content
            agent_id: Agent ID if sender is agent
            agent_name: Agent name if sender is agent
            
        Returns:
            True if successful
        """
        try:
            # Create message object
            message = {
                "id": message_id,
                "sender": sender,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "agent_name": agent_name,
            }
            
            # Load existing messages
            session_file = self._get_session_file(session_id)
            messages = []
            
            if session_file.exists():
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    messages = data.get('messages', [])
            
            # Add new message
            messages.append(message)
            
            # Save back to file
            with open(session_file, 'w') as f:
                json.dump({
                    'session_id': session_id,
                    'created_at': messages[0]['timestamp'] if messages else datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'messages': messages
                }, f, indent=2)
            
            logger.info(f"Saved message {message_id} to session {session_id} (total: {len(messages)} messages)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}", exc_info=True)
            return False
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a session.
        
        Args:
            session_id: Chat session ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        try:
            session_file = self._get_session_file(session_id)
            
            if not session_file.exists():
                logger.info(f"No history found for session {session_id}")
                return []
            
            with open(session_file, 'r') as f:
                data = json.load(f)
                messages = data.get('messages', [])
            
            # Return last 'limit' messages
            result = messages[-limit:] if len(messages) > limit else messages
            
            logger.info(f"Retrieved {len(result)} messages for session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}", exc_info=True)
            return []
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear all messages in a session."""
        try:
            session_file = self._get_session_file(session_id)
            
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Cleared session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}", exc_info=True)
            return False


# Singleton instance
chat_repository = ChatRepository()
