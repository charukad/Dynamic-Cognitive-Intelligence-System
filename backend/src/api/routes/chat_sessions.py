"""Chat session APIs."""

from fastapi import APIRouter, HTTPException, Query, Request

from src.core import get_logger
from src.infrastructure.repositories.chat_repository import chat_repository
from src.schemas import (
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
    ChatSessionUpdate,
    ChatWorkspaceResponse,
)
from src.services.chat.request_controls import (
    ChatRateLimitExceeded,
    ChatRateLimitScope,
    build_http_request_context,
    chat_rate_limiter,
    record_chat_failure,
    record_chat_success,
)
from src.services.chat.workspace import chat_workspace_service
from src.services.chat.validation import validate_identifier

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


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


@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(request: Request, payload: ChatSessionCreate) -> ChatSessionResponse:
    """Create a new chat session."""
    context = build_http_request_context(request, route_name="chat_sessions.create")
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_WRITE,
            client_id=context.client_id,
        )
        session = await chat_repository.create_session(
            title=payload.title,
            selected_agent_id=payload.selected_agent_id,
            metadata=payload.metadata,
        )
        record_chat_success(context, status_code=200)
        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            status=session.status,
            selected_agent_id=session.selected_agent_id,
            message_count=session.message_count,
            last_message="",
            last_message_at=session.last_message_at,
            metadata=session.metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat session creation rate limit exceeded",
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
        logger.error("Failed to create chat session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10000),
) -> ChatSessionListResponse:
    """List chat sessions ordered by most recent activity."""
    context = build_http_request_context(request, route_name="chat_sessions.list")
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_READ,
            client_id=context.client_id,
        )
        sessions = await chat_repository.list_sessions(limit=limit, offset=offset)
        record_chat_success(context, status_code=200)
        return ChatSessionListResponse(
            sessions=[_to_session_response(session) for session in sessions],
            count=len(sessions),
        )
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat session listing rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except Exception as exc:
        record_chat_failure(
            context,
            status_code=500,
            error_code=type(exc).__name__,
            detail=str(exc),
            exc_info=True,
        )
        logger.error("Failed to list chat sessions: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(request: Request, session_id: str) -> ChatSessionResponse:
    """Get a single chat session."""
    context = build_http_request_context(
        request,
        route_name="chat_sessions.get",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_READ,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        summary = await chat_repository.get_session_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Chat session not found: {session_id}")
        record_chat_success(context, status_code=200)
        return _to_session_response(summary)
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat session lookup rate limit exceeded",
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
        logger.error("Failed to get chat session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/chat/sessions/{session_id}/workspace", response_model=ChatWorkspaceResponse)
async def get_chat_workspace(request: Request, session_id: str) -> ChatWorkspaceResponse:
    """Return the canonical office/workspace projection for a chat session."""
    context = build_http_request_context(
        request,
        route_name="chat_sessions.workspace",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_READ,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        payload = await chat_workspace_service.get_workspace(session_id)
        record_chat_success(context, status_code=200)
        return ChatWorkspaceResponse(**payload)
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat workspace lookup rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        record_chat_failure(
            context,
            status_code=status_code,
            error_code="not_found" if status_code == 404 else "validation_failed",
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
        logger.error("Failed to get chat workspace: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    request: Request,
    session_id: str,
    payload: ChatSessionUpdate,
) -> ChatSessionResponse:
    """Update chat session metadata."""
    context = build_http_request_context(
        request,
        route_name="chat_sessions.update",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_WRITE,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        session = await chat_repository.update_session(
            session_id,
            title=payload.title,
            status=payload.status,
            selected_agent_id=payload.selected_agent_id,
            metadata=payload.metadata,
        )
        if not session:
            raise HTTPException(status_code=404, detail=f"Chat session not found: {session_id}")

        summary = await chat_repository.get_session_summary(session_id)
        if summary:
            record_chat_success(context, status_code=200)
            return _to_session_response(summary)

        record_chat_success(context, status_code=200)
        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            status=session.status,
            selected_agent_id=session.selected_agent_id,
            message_count=session.message_count,
            last_message="",
            last_message_at=session.last_message_at,
            metadata=session.metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    except ChatRateLimitExceeded as exc:
        record_chat_failure(
            context,
            status_code=429,
            error_code="rate_limit_exceeded",
            detail=str(exc),
        )
        raise HTTPException(
            status_code=429,
            detail="Chat session update rate limit exceeded",
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
        logger.error("Failed to update chat session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(request: Request, session_id: str) -> dict[str, object]:
    """Delete a chat session and all related records."""
    context = build_http_request_context(
        request,
        route_name="chat_sessions.delete",
        session_id=session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.SESSION_WRITE,
            client_id=context.client_id,
            session_id=session_id,
        )
        session_id = validate_identifier(session_id, "session_id") or session_id
        deleted = await chat_repository.delete_session(session_id)
        if not deleted:
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
            detail="Chat session deletion rate limit exceeded",
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
        logger.error("Failed to delete chat session: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
