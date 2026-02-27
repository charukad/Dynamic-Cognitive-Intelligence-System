"""Chat feedback APIs."""

from fastapi import APIRouter, HTTPException, Request

from src.core import get_logger
from src.domain.models import ChatMessageRole, ChatMessageSender
from src.infrastructure.repositories.chat_repository import chat_repository
from src.schemas import ChatFeedbackResponse, ChatFeedbackUpsert
from src.services.chat.request_controls import (
    ChatRateLimitExceeded,
    ChatRateLimitScope,
    build_http_request_context,
    chat_rate_limiter,
    record_chat_failure,
    record_chat_success,
)

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.post("/chat/feedback", response_model=ChatFeedbackResponse)
async def upsert_chat_feedback(request: Request, payload: ChatFeedbackUpsert) -> ChatFeedbackResponse:
    """Store feedback for an agent response message."""
    context = build_http_request_context(
        request,
        route_name="chat_feedback.upsert",
        session_id=payload.session_id,
    )
    try:
        await chat_rate_limiter.enforce(
            scope=ChatRateLimitScope.FEEDBACK_WRITE,
            client_id=context.client_id,
            session_id=payload.session_id,
        )
        message = await chat_repository.get_message(payload.message_id)
        if not message:
            raise HTTPException(status_code=404, detail=f"Chat message not found: {payload.message_id}")
        if message["session_id"] != payload.session_id:
            raise HTTPException(status_code=400, detail="Feedback session_id does not match the message session")
        if message["role"] != ChatMessageRole.ASSISTANT.value or message["sender"] != ChatMessageSender.AGENT.value:
            raise HTTPException(status_code=400, detail="Feedback can only be attached to assistant messages")
        if payload.agent_id and message.get("agent_id") and payload.agent_id != message.get("agent_id"):
            raise HTTPException(status_code=400, detail="Feedback agent_id does not match the message agent")

        feedback = await chat_repository.upsert_feedback(
            session_id=payload.session_id,
            message_id=payload.message_id,
            agent_id=payload.agent_id,
            feedback_type=payload.feedback_type,
            rating=payload.rating,
            text_feedback=payload.text_feedback,
            user_id=payload.user_id,
            metadata=payload.metadata,
        )
        record_chat_success(context, status_code=200)
        return ChatFeedbackResponse(
            id=str(feedback.id),
            session_id=feedback.session_id,
            message_id=feedback.message_id,
            agent_id=feedback.agent_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            text_feedback=feedback.text_feedback,
            user_id=feedback.user_id,
            metadata=feedback.metadata,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
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
            detail="Chat feedback rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
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
        logger.error("Failed to upsert chat feedback: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
