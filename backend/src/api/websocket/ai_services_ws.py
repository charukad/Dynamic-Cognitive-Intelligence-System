"""
WebSocket Handler for Advanced AI Services

Provides real-time updates for:
- Dream cycle progress
- GAIA match events
- Multi-modal processing progress
- Service status changes
- Presence tracking
- Collaborative features
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import asyncio
import json
from datetime import datetime
from uuid import uuid4

from src.core import get_logger
from src.api.websocket.connection_manager import connection_manager
from src.services.chat.request_controls import (
    ChatRateLimitExceeded,
    ChatRateLimitScope,
    build_websocket_request_context,
    chat_rate_limiter,
    record_chat_failure,
    record_chat_success,
    record_stream_event,
)
from src.services.chat.validation import validate_chat_text, validate_identifier
from src.services.chat.validation import validate_metadata_dict

logger = get_logger(__name__)


# ============================================================================
# WebSocket Endpoint Handler
# ============================================================================

async def ai_services_websocket_endpoint(
    websocket: WebSocket,
    session_id: str = "default",
    user_id: Optional[str] = None
):
    """
    WebSocket endpoint for AI services real-time updates.
    
    Clients can:
    - Subscribe to specific update types
    - Receive real-time progress updates
    - Get notified of completions
    - Track presence and collaborate
    
    Args:
        websocket: WebSocket connection
        session_id: Session/room identifier (default: "default")
        user_id: Optional user identifier
    """
    # Generate unique connection ID
    connection_id = user_id or str(uuid4())
    
    # User info for presence tracking
    user_info = {
        "user_id": user_id or connection_id,
        "username": user_id or f"User_{connection_id[:8]}",
        "metadata": {}
    }
    
    # Connect using unified connection manager
    await connection_manager.connect(
        websocket=websocket,
        connection_id=connection_id,
        session_id=session_id,
        user_info=user_info
    )
    
    # Track subscriptions for this connection
    subscriptions = {
        'dream_progress', 'dream_complete',
        'match_progress', 'match_complete',
        'processing_progress', 'processing_complete',
        'service_status'
    }
    
    try:
        # Send welcome message
        await connection_manager.send_personal_message(
            {
                'type': 'connected',
                'data': {
                    'connection_id': connection_id,
                    'session_id': session_id,
                    'available_subscriptions': list(subscriptions)
                },
                'timestamp': datetime.now().isoformat()
            },
            connection_id
        )
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type')
                message_data = message.get('data', {})
                
                # Handle different message types
                if message_type == 'ping':
                    # Heartbeat response
                    await connection_manager.send_personal_message(
                        {
                            'type': 'pong',
                            'data': {'timestamp': datetime.now().isoformat()},
                            'timestamp': datetime.now().isoformat()
                        },
                        connection_id
                    )
                
                elif message_type == 'subscribe':
                    # Client wants to subscribe to specific events
                    requested_types = message_data.get('types', [])
                    valid_types = [t for t in requested_types if t in subscriptions]
                    
                    await connection_manager.send_personal_message(
                        {
                            'type': 'subscription_confirmed',
                            'data': {'types': valid_types},
                            'timestamp': datetime.now().isoformat()
                        },
                        connection_id
                    )
                
                elif message_type == 'get_presence':
                    # Client requests presence information
                    presence = connection_manager.get_presence_info()
                    await connection_manager.send_personal_message(
                        {
                            'type': 'presence_info',
                            'data': presence,
                            'timestamp': datetime.now().isoformat()
                        },
                        connection_id
                    )
                
                elif message_type == 'cursor_update':
                    # Collaborative cursor update
                    cursor_position = message_data.get('position')
                    if cursor_position:
                        connection_manager.update_cursor(connection_id, cursor_position)
                        
                        # Broadcast to session
                        await connection_manager.broadcast_to_session(
                            {
                                'type': 'cursor_update',
                                'data': {
                                    'connection_id': connection_id,
                                    'user': connection_manager.online_users.get(connection_id, {}),
                                    'position': cursor_position
                                },
                                'timestamp': datetime.now().isoformat()
                            },
                            session_id,
                            exclude_connection=connection_id
                        )
                
                elif message_type == 'broadcast':
                    # Client wants to broadcast a message to session
                    event_type = message_data.get('event_type')
                    payload = message_data.get('payload', {})
                    
                    if event_type:
                        await connection_manager.broadcast_to_session(
                            {
                                'type': event_type,
                                'data': {
                                    'from_connection': connection_id,
                                    'from_user': connection_manager.online_users.get(connection_id, {}),
                                    **payload
                                },
                                'timestamp': datetime.now().isoformat()
                            },
                            session_id,
                            exclude_connection=connection_id
                        )
                
                elif message_type == 'chat':
                    # Handle chat message - route to agent and generate response
                    agent_id = message_data.get('agent_id')
                    user_message = message_data.get('message')
                    message_id = message_data.get('message_id')
                    metadata = message_data.get('metadata')
                    # Use session_id from message if provided, otherwise use connection session_id
                    chat_session_id = message_data.get('session_id', session_id)
                    
                    if not user_message or not agent_id:
                        await connection_manager.send_personal_message({
                            'type': 'error',
                            'data': {'message': 'Missing agent_id or message'},
                            'timestamp': datetime.now().isoformat()
                        }, connection_id)
                    else:
                        # Process chat message (async task)
                        await handle_chat_message(
                            websocket=websocket,
                            connection_id=connection_id,
                            session_id=chat_session_id,  # Use extracted session_id
                            agent_id=agent_id,
                            user_message=user_message,
                            message_id=message_id,
                            metadata=metadata,
                        )
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {connection_id}")
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
    
    except WebSocketDisconnect:
        logger.info(f"Client {connection_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        # Clean up connection
        connection_manager.disconnect(connection_id)
        
        # Broadcast disconnection to session if needed
        if hasattr(connection_manager, '_pending_disconnect_broadcast'):
            pending = connection_manager._pending_disconnect_broadcast
            await connection_manager.broadcast_to_session(
                {
                    'type': 'presence:update',
                    'data': {
                        'event': 'user_left',
                        'user': pending.get('user_info'),
                        'online_count': pending.get('online_count', 0)
                    },
                    'timestamp': datetime.now().isoformat()
                },
                pending.get('session_id', session_id)
            )



# ============================================================================
# Chat Message Handler
# ============================================================================

async def handle_chat_message(
    websocket: WebSocket,
    connection_id: str,
    session_id: str,
    agent_id: str,
    user_message: str,
    message_id: str | None,
    metadata: dict | None,
):
    """
    Process chat message and generate agent response.
    
    Args:
        connection_id: WebSocket connection ID
        session_id: Chat session ID
        agent_id: Target agent ID
        user_message: User's message content
    message_id: Original message ID from client
    """
    context = build_websocket_request_context(
        websocket,
        route_name="chat_messages.websocket_send",
        client_id=connection_id,
        session_id=session_id,
    )
    typing_started = False
    failure_event_emitted = False
    try:
        session_id = validate_identifier(session_id, "session_id") or session_id
        agent_id = validate_identifier(agent_id, "agent_id") or agent_id
        user_message = validate_chat_text(user_message, field_name="message")
        message_id = validate_identifier(message_id, "message_id")
        metadata = validate_metadata_dict(metadata, "metadata")
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.WEBSOCKET_SEND,
            client_id=context.client_id,
            session_id=session_id,
        )

        await connection_manager.send_personal_message({
            'type': 'typing',
            'data': {'is_typing': True},
            'timestamp': datetime.now().isoformat()
        }, connection_id)
        typing_started = True
        from src.services.chat.service import chat_service

        async for event in chat_service.stream_message(
            session_id=session_id,
            content=user_message,
            agent_id=agent_id,
            user_message_id=message_id,
            metadata=metadata,
        ):
            event_type = event["type"]
            record_stream_event(context, event_type)
            if event_type == "response.started":
                message = event["payload"]["message"]
                await connection_manager.send_personal_message(
                    {
                        "type": "message",
                        "id": message["id"],
                        "agent_id": message.get("agent_id"),
                        "agent_name": message.get("agent_name"),
                        "content": message["content"],
                        "metadata": message.get("metadata", {}),
                        "timestamp": message["created_at"].isoformat()
                        if hasattr(message["created_at"], "isoformat")
                        else str(message["created_at"]),
                    },
                    connection_id,
                )
            elif event_type == "response.delta":
                await connection_manager.send_personal_message(
                    {
                        "type": "stream_chunk",
                        "message_id": event["message_id"],
                        "chunk": event["payload"]["chunk"],
                        "agent_id": event["payload"]["agent_id"],
                        "agent_name": event["payload"]["agent_name"],
                        "timestamp": event["timestamp"],
                    },
                    connection_id,
                )
            elif event_type == "response.completed":
                await connection_manager.send_personal_message(
                    {
                        "type": "message_completed",
                        "message_id": event["message_id"],
                        "timestamp": event["timestamp"],
                    },
                    connection_id,
                )
            elif event_type == "response.failed":
                failure_event_emitted = True
                await connection_manager.send_personal_message(
                    {
                        "type": "error",
                        "data": {"message": event["payload"]["error"]},
                        "timestamp": event["timestamp"],
                    },
                    connection_id,
                )
        record_chat_success(context, status_code=200, extra_tags={"stream": "true"})
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
            extra_tags={"stream": "true"},
        )
        await connection_manager.send_personal_message({
            'type': 'error',
            'data': {
                'message': 'Chat rate limit exceeded',
                'retry_after_seconds': exc.retry_after_seconds,
            },
            'timestamp': datetime.now().isoformat()
        }, connection_id)
    except ValueError as exc:
        record_chat_failure(
            context,
            status_code=400,
            error_code="validation_failed",
            detail=str(exc),
            extra_tags={"stream": "true"},
        )
        await connection_manager.send_personal_message({
            'type': 'error',
            'data': {'message': str(exc)},
            'timestamp': datetime.now().isoformat()
        }, connection_id)
    except Exception as e:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(e).__name__,
            detail=str(e),
            exc_info=True,
            extra_tags={"stream": "true"},
        )
        logger.error(f"Error handling chat message: {e}", exc_info=True)
        if not failure_event_emitted:
            await connection_manager.send_personal_message({
                'type': 'error',
                'data': {'message': f'Failed to process message: {str(e)}'},
                'timestamp': datetime.now().isoformat()
            }, connection_id)
    finally:
        # Stop typing indicator
        if typing_started:
            await connection_manager.send_personal_message({
                'type': 'typing',
                'data': {'is_typing': False},
                'timestamp': datetime.now().isoformat()
            }, connection_id)


# ============================================================================
# Progress Update Functions (for use in AI services)
# ============================================================================

# ============================================================================
# Progress Update Functions (for use in AI services)
# ============================================================================

async def send_dream_progress(agent_id: str, progress: float, status: str, session_id: str = "default"):
    """Send dream cycle progress update"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'dream_progress',
            'data': {
                'agent_id': agent_id,
                'progress': progress,
                'status': status
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_dream_complete(agent_id: str, result: dict, session_id: str = "default"):
    """Send dream cycle completion notification"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'dream_complete',
            'data': {
                'agent_id': agent_id,
                'result': result
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_match_progress(match_id: str, round_num: int, score: dict, session_id: str = "default"):
    """Send match progress update"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'match_progress',
            'data': {
                'match_id': match_id,
                'round': round_num,
                'score': score
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_match_complete(match_id: str, result: dict, session_id: str = "default"):
    """Send match completion notification"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'match_complete',
            'data': {
                'match_id': match_id,
                'result': result
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_processing_progress(task_id: str, progress: float, operation: str, session_id: str = "default"):
    """Send multi-modal processing progress"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'processing_progress',
            'data': {
                'task_id': task_id,
                'progress': progress,
                'operation': operation
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_processing_complete(task_id: str, result: dict, session_id: str = "default"):
    """Send processing completion notification"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'processing_complete',
            'data': {
                'task_id': task_id,
                'result': result
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


async def send_service_status(services: dict, session_id: str = "default"):
    """Send service status update"""
    await connection_manager.broadcast_to_session(
        {
            'type': 'service_status',
            'data': {
                'services': services
            },
            'timestamp': datetime.now().isoformat()
        },
        session_id
    )


# ============================================================================
# Background Status Broadcasting
# ============================================================================

async def start_status_broadcaster():
    """Background task to broadcast service status periodically"""
    from src.services.advanced.ai_services_manager import get_ai_services_manager
    
    while True:
        try:
            manager = get_ai_services_manager()
            status = manager.get_service_status()
            
            # Convert to dict
            status_dict = {
                name: {
                    'service_name': s.service_name,
                    'status': s.status,
                    'last_activity': s.last_activity.isoformat(),
                    'total_requests': s.total_requests,
                    'success_rate': s.success_rate
                }
                for name, s in status.items()
            }
            
            # Broadcast to all sessions
            for session_id in list(connection_manager.sessions.keys()):
                await send_service_status(status_dict, session_id)
            
        except Exception as e:
            logger.error(f"Error broadcasting status: {e}")
        
        # Broadcast every 10 seconds
        await asyncio.sleep(10)
