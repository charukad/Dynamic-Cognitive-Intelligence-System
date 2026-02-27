"""Chat message APIs and backwards-compatible history routes."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from src.core import get_logger
from src.domain.models import ChatMessageSender
from src.infrastructure.repositories.chat_repository import chat_repository
from src.schemas import (
    ChatMessageCreate,
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatMessageSendRequest,
    ChatMessageSendResponse,
    ChatSessionResponse,
)
from src.services.chat.request_controls import (
    ChatRateLimitExceeded,
    ChatRateLimitScope,
    build_http_request_context,
    chat_rate_limiter,
    record_chat_failure,
    record_chat_success,
    record_stream_event,
)
from src.services.chat.service import chat_service
from src.services.chat.validation import (
    normalize_optional_text,
    validate_chat_text,
    validate_identifier,
)

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


def _to_message_response(row: dict) -> ChatMessageResponse:
    feedback = None
    if row.get("feedback_id"):
        feedback = {
            "id": row["feedback_id"],
            "session_id": row["session_id"],
            "message_id": row["id"],
            "agent_id": row.get("feedback_agent_id"),
            "feedback_type": row["feedback_type"],
            "rating": row.get("rating"),
            "text_feedback": row.get("text_feedback"),
            "user_id": row.get("user_id"),
            "metadata": row.get("feedback_metadata", {}),
            "created_at": row["feedback_created_at"],
            "updated_at": row["feedback_updated_at"],
        }

    return ChatMessageResponse(
        id=row["id"],
        session_id=row["session_id"],
        sequence_number=int(row["sequence_number"]),
        role=row["role"],
        sender=row["sender"],
        content=row["content"],
        status=row["status"],
        agent_id=row.get("agent_id"),
        agent_name=row.get("agent_name"),
        error_message=row.get("error_message"),
        metadata=row.get("metadata", {}),
        feedback=feedback,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_session_response(row: dict) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=row["id"],
        title=row["title"],
        status=row["status"],
        selected_agent_id=row.get("selected_agent_id"),
        message_count=int(row.get("message_count", 0) or 0),
        last_message=row.get("last_message", "") or "",
        last_message_at=row.get("last_message_at"),
        metadata=row.get("metadata", {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/chat/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def list_chat_messages(
    request: Request,
    session_id: str,
    limit: int = Query(default=100, ge=1, le=200),
    before_sequence: int | None = Query(default=None, ge=1),
) -> ChatMessageListResponse:
    """List persisted messages for a session."""
    context = build_http_request_context(
        request,
        route_name="chat_messages.list",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.MESSAGE_READ,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        session = await chat_repository.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Chat session not found: {session_id}")

        rows = await chat_repository.list_messages(
            session_id=session_id,
            limit=limit,
            before_sequence=before_sequence,
        )
        response = ChatMessageListResponse(
            session_id=session_id,
            messages=[_to_message_response(row) for row in rows],
            count=len(rows),
            limit=limit,
            before_sequence=before_sequence,
        )
        record_chat_success(context, status_code=200)
        return response
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat message listing rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        record_chat_failure(
            context,
            status_code=400,
            error_code="validation_failed",
            detail=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException as exc:
        record_chat_failure(
            context,
            status_code=exc.status_code,
            error_code="not_found" if exc.status_code == 404 else "invalid_request",
            detail=str(exc.detail),
        )
        raise
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to list chat messages: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def create_chat_message(
    request: Request,
    session_id: str,
    payload: ChatMessageCreate,
) -> ChatMessageResponse:
    """Persist a single chat message."""
    context = build_http_request_context(
        request,
        route_name="chat_messages.create",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.MESSAGE_WRITE,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        message = await chat_repository.create_message(
            session_id=session_id,
            message_id=payload.id,
            role=payload.role,
            sender=payload.sender,
            content=payload.content,
            status=payload.status,
            agent_id=payload.agent_id,
            agent_name=payload.agent_name,
            error_message=payload.error_message,
            metadata=payload.metadata,
        )
        stored = await chat_repository.get_message(str(message.id))
        if not stored:
            raise RuntimeError("Message persisted but could not be reloaded")
        record_chat_success(context, status_code=200)
        return _to_message_response(stored)
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat message persistence rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        record_chat_failure(
            context,
            status_code=status_code,
            error_code="validation_failed" if status_code == 400 else "not_found",
            detail=str(exc),
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to create chat message: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/sessions/{session_id}/messages/send")
async def send_chat_message(
    request: Request,
    session_id: str,
    payload: ChatMessageSendRequest,
):
    """Create a user turn and generate the next assistant response."""
    context = build_http_request_context(
        request,
        route_name="chat_messages.send",
        session_id=session_id,
        stream=payload.stream,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.MESSAGE_SEND,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id

        if payload.stream:
            def _json_default(value):
                if hasattr(value, "isoformat"):
                    return value.isoformat()
                return str(value)

            async def event_stream():
                failure_event_emitted = False
                try:
                    async for event in chat_service.stream_message(
                        session_id=session_id,
                        content=payload.content,
                        agent_id=payload.agent_id,
                        user_message_id=payload.id,
                        metadata=payload.metadata,
                    ):
                        record_stream_event(context, event["type"])
                        if event["type"] == "response.failed":
                            failure_event_emitted = True
                        yield f"data: {json.dumps(event, default=_json_default)}\n\n"
                    yield "data: [DONE]\n\n"
                    record_chat_success(context, status_code=200, extra_tags={"stream": "true"})
                except Exception as exc:
                    record_chat_failure(
                        context,
                        status_code=500,
                        error_code=type(exc).__name__,
                        detail=str(exc),
                        exc_info=True,
                        extra_tags={"stream": "true"},
                    )
                    if not failure_event_emitted:
                        error_event = {
                            "type": "response.failed",
                            "session_id": session_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {"error": "Chat streaming failed"},
                        }
                        yield f"data: {json.dumps(error_event, default=_json_default)}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        result = await chat_service.send_message(
            session_id=session_id,
            content=payload.content,
            agent_id=payload.agent_id,
            user_message_id=payload.id,
            metadata=payload.metadata,
        )
        record_chat_success(context, status_code=200, extra_tags={"stream": "false"})
        return ChatMessageSendResponse(
            session=_to_session_response(result["session"]),
            user_message=_to_message_response(result["user_message"]),
            assistant_message=_to_message_response(result["assistant_message"]),
        )
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
            extra_tags={"stream": str(payload.stream).lower()},
        )
        raise HTTPException(
            status_code=429,
            detail="Chat send rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        record_chat_failure(
            context,
            status_code=status_code,
            error_code="not_found" if status_code == 404 else "validation_failed",
            detail=detail,
            extra_tags={"stream": str(payload.stream).lower()},
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
            extra_tags={"stream": str(payload.stream).lower()},
        )
        logger.error("Failed to send chat message: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    request: Request,
    session_id: str,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, object]:
    """Backward-compatible session history endpoint."""
    context = build_http_request_context(
        request,
        route_name="chat_history.get",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.MESSAGE_READ,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        messages = await chat_repository.get_session_history(session_id, limit)
        response = {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages),
        }
        record_chat_success(context, status_code=200)
        return response
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat history rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        record_chat_failure(
            context,
            status_code=400,
            error_code="validation_failed",
            detail=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to get chat history: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/history/{session_id}/message")
async def save_chat_message(
    request: Request,
    session_id: str,
    message_id: str = Query(..., min_length=1, max_length=255),
    sender: str = Query(..., min_length=1, max_length=32),
    content: str = Query(..., min_length=1, max_length=20000),
    agent_id: str | None = Query(default=None, min_length=1, max_length=255),
    agent_name: str | None = Query(default=None, min_length=1, max_length=255),
) -> dict[str, object]:
    """Backward-compatible single-message persistence endpoint."""
    context = build_http_request_context(
        request,
        route_name="chat_history.save_message",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.MESSAGE_WRITE,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        message_id = validate_identifier(message_id, "message_id") or message_id
        agent_id = validate_identifier(agent_id, "agent_id")
        content = validate_chat_text(content, field_name="content")
        agent_name = normalize_optional_text(agent_name)
        if sender not in {member.value for member in ChatMessageSender}:
            raise HTTPException(status_code=400, detail=f"Invalid sender: {sender}")

        success = await chat_repository.save_message(
            session_id=session_id,
            message_id=message_id,
            sender=sender,
            content=content,
            agent_id=agent_id,
            agent_name=agent_name,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save message")

        response = {
            "status": "saved",
            "message_id": message_id,
            "session_id": session_id,
        }
        record_chat_success(context, status_code=200)
        return response
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Legacy chat persistence rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        record_chat_failure(
            context,
            status_code=400,
            error_code="validation_failed",
            detail=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException as exc:
        record_chat_failure(
            context,
            status_code=exc.status_code,
            error_code="invalid_request" if exc.status_code < 500 else "storage_failed",
            detail=str(exc.detail),
        )
        raise
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to save chat message: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(request: Request, session_id: str) -> dict[str, object]:
    """Backward-compatible delete endpoint."""
    context = build_http_request_context(
        request,
        route_name="chat_history.clear",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_WRITE,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        cleared = await chat_repository.clear_session(session_id)
        if not cleared:
            raise HTTPException(status_code=404, detail=f"Chat session not found: {session_id}")
        record_chat_success(context, status_code=200)
        return {"deleted": True, "session_id": session_id}
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat history deletion rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        record_chat_failure(
            context,
            status_code=400,
            error_code="validation_failed",
            detail=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException as exc:
        record_chat_failure(
            context,
            status_code=exc.status_code,
            error_code="not_found" if exc.status_code == 404 else "invalid_request",
            detail=str(exc.detail),
        )
        raise
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to clear chat history: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
