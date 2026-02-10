"""Native FastAPI WebSocket connection manager."""

from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
import asyncio
import json

from src.core import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with room/session support.
    
    Features:
    - Per-session rooms
    - Broadcast to all or specific sessions
    - Automatic reconnection tracking
    - Heartbeat/ping support
    - Presence tracking
    """
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Session rooms: {session_id: Set[connection_id]}
        self.sessions: Dict[str, Set[str]] = {}
        
        # Connection metadata: {connection_id: dict}
        self.metadata: Dict[str, dict] = {}
        
        # Online users: {connection_id: user_info}
        self.online_users: Dict[str, Dict[str, Any]] = {}
        
        # User cursors for collaboration: {connection_id: cursor_data}
        self.user_cursors: Dict[str, Dict[str, Any]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        session_id: str = "default",
        user_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Accept and register a new connection.
        
        Args:
            websocket: WebSocket instance
            connection_id: Unique connection identifier
            session_id: Session/room identifier
            user_info: Optional user information
        """
        await websocket.accept()
        
        # Register connection
        self.active_connections[connection_id] = websocket
        self.metadata[connection_id] = {
            "session_id": session_id,
            "connected_at": asyncio.get_event_loop().time(),
            "user_info": user_info or {}
        }
        
        # Track online user
        username = (user_info or {}).get("username", f"User_{connection_id[:8]}")
        self.online_users[connection_id] = {
            "connection_id": connection_id,
            "username": username,
            "connected_at": asyncio.get_event_loop().time(),
            "metadata": (user_info or {}).get("metadata", {})
        }
        
        # Add to session room
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
        self.sessions[session_id].add(connection_id)
        
        logger.info(
            f"Client {connection_id} ({username}) connected to session {session_id}. "
            f"Total: {len(self.active_connections)}"
        )
        
        # Broadcast presence update to others in session
        await self.broadcast_to_session(
            {
                "type": "presence:update",
                "data": {
                    "event": "user_joined",
                    "user": self.online_users[connection_id],
                    "online_count": len(self.sessions.get(session_id, set()))
                },
                "timestamp": asyncio.get_event_loop().time()
            },
            session_id,
            exclude_connection=connection_id
        )
        
        # Send current presence to new user
        await self.send_personal_message(
            {
                "type": "presence:current",
                "data": {
                    "online_users": [
                        self.online_users[cid]
                        for cid in self.sessions.get(session_id, set())
                    ],
                    "count": len(self.sessions.get(session_id, set()))
                },
                "timestamp": asyncio.get_event_loop().time()
            },
            connection_id
        )
    
    def disconnect(self, connection_id: str) -> None:
        """
        Remove a connection.
        
        Args:
            connection_id: Connection to remove
        """
        if connection_id not in self.active_connections:
            return
        
        # Get session and user info before removal
        session_id = self.metadata[connection_id]["session_id"]
        user_info = self.online_users.get(connection_id)
        
        # Remove from session
        if session_id in self.sessions:
            self.sessions[session_id].discard(connection_id)
            if not self.sessions[session_id]:
                del self.sessions[session_id]
        
        # Remove connection
        del self.active_connections[connection_id]
        del self.metadata[connection_id]
        
        # Clean up user data
        if connection_id in self.online_users:
            del self.online_users[connection_id]
        if connection_id in self.user_cursors:
            del self.user_cursors[connection_id]
        
        logger.info(
            f"Client {connection_id} disconnected. "
            f"Remaining: {len(self.active_connections)}"
        )
        
        # Broadcast presence update (will be sent in disconnect handler)
        # Store for async broadcast
        self._pending_disconnect_broadcast = {
            "session_id": session_id,
            "user_info": user_info,
            "online_count": len(self.sessions.get(session_id, set()))
        }
    
    async def send_personal_message(
        self,
        message: dict,
        connection_id: str
    ) -> bool:
        """
        Send message to specific connection.
        
        Args:
            message: Message dictionary
            connection_id: Target connection
            
        Returns:
            True if sent, False if connection not found
        """
        if connection_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send to {connection_id}: {e}")
            self.disconnect(connection_id)
            return False
    
    async def broadcast_to_session(
        self,
        message: dict,
        session_id: str,
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all connections in a session.
        
        Args:
            message: Message dictionary
            session_id: Target session
            exclude_connection: Optional connection ID to exclude
            
        Returns:
            Number of successful sends
        """
        if session_id not in self.sessions:
            return 0
        
        connection_ids = list(self.sessions[session_id])
        sent_count = 0
        
        for connection_id in connection_ids:
            if exclude_connection and connection_id == exclude_connection:
                continue
            
            success = await self.send_personal_message(message, connection_id)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, message: dict) -> int:
        """
        Broadcast message to all connections.
        
        Args:
            message: Message dictionary
            
        Returns:
            Number of successful sends
        """
        connection_ids = list(self.active_connections.keys())
        sent_count = 0
        
        for connection_id in connection_ids:
            success = await self.send_personal_message(message, connection_id)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def send_heartbeat(self, connection_id: str) -> bool:
        """
        Send heartbeat/ping to connection.
        
        Args:
            connection_id: Target connection
            
        Returns:
            True if successful
        """
        return await self.send_personal_message(
            {"type": "ping", "timestamp": asyncio.get_event_loop().time()},
            connection_id
        )
    
    def get_session_participants(self, session_id: str) -> int:
        """
        Get number of participants in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of participants
        """
        return len(self.sessions.get(session_id, set()))
    
    def get_presence_info(self) -> Dict[str, Any]:
        """
        Get current presence information.
        
        Returns:
            Presence data including online users and session counts
        """
        return {
            "online_users": list(self.online_users.values()),
            "total_count": len(self.online_users),
            "sessions": {
                session_id: len(connections)
                for session_id, connections in self.sessions.items()
            }
        }
    
    def update_cursor(
        self,
        connection_id: str,
        cursor_position: Dict[str, Any]
    ) -> None:
        """
        Update cursor position for a user.
        
        Args:
            connection_id: Connection identifier
            cursor_position: Cursor position data
        """
        if connection_id not in self.online_users:
            return
        
        self.user_cursors[connection_id] = {
            "position": cursor_position,
            "user": self.online_users[connection_id]
        }


# Global instance
connection_manager = ConnectionManager()
