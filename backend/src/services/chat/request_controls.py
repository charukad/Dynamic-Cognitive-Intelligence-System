"""Request controls for chat HTTP and WebSocket entry points."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import Request
from starlette.websockets import WebSocket

from src.core import get_logger, settings
from src.infrastructure.database import postgres_client
from src.services.monitoring.metrics import tracer, metrics_collector

logger = get_logger(__name__)


class ChatRateLimitScope(str, Enum):
    """Named rate-limit scopes for chat APIs."""

    SESSION_READ = "session_read"
    SESSION_WRITE = "session_write"
    MESSAGE_READ = "message_read"
    MESSAGE_WRITE = "message_write"
    MESSAGE_SEND = "message_send"
    FEEDBACK_WRITE = "feedback_write"
    WEBSOCKET_SEND = "websocket_send"


@dataclass(frozen=True)
class RateLimitPolicy:
    """Rate-limit configuration for one scope."""

    scope: ChatRateLimitScope
    limit: int
    window_seconds: int


@dataclass(frozen=True)
class RateLimitDecision:
    """Decision returned from the rate limiter."""

    allowed: bool
    limit: int
    request_count: int
    retry_after_seconds: int


@dataclass
class ChatRequestContext:
    """Per-request state used for tracing and metrics."""

    route_name: str
    method: str
    transport: str
    client_id: str
    request_id: str
    session_id: str | None
    stream: bool
    started_at: float
    trace_span_id: UUID
    trace_metadata: dict[str, Any]


class ChatRateLimitExceeded(RuntimeError):
    """Raised when a chat request exceeds its configured quota."""

    def __init__(
        self,
        *,
        scope: ChatRateLimitScope,
        limit: int,
        retry_after_seconds: int,
        request_count: int,
    ) -> None:
        self.scope = scope
        self.limit = limit
        self.retry_after_seconds = retry_after_seconds
        self.request_count = request_count
        super().__init__(
            f"Rate limit exceeded for {scope.value}: {request_count}/{limit} requests in "
            f"{retry_after_seconds}s window"
        )


class ChatRateLimiter:
    """PostgreSQL-backed rate limiter for chat request entry points."""

    def get_policy(self, scope: ChatRateLimitScope) -> RateLimitPolicy:
        """Resolve the configured rate-limit policy for a given scope."""
        window_seconds = settings.chat_rate_limit_window_seconds
        limit_by_scope = {
            ChatRateLimitScope.SESSION_READ: settings.chat_session_read_rate_limit_per_window,
            ChatRateLimitScope.SESSION_WRITE: settings.chat_session_write_rate_limit_per_window,
            ChatRateLimitScope.MESSAGE_READ: settings.chat_message_read_rate_limit_per_window,
            ChatRateLimitScope.MESSAGE_WRITE: settings.chat_message_write_rate_limit_per_window,
            ChatRateLimitScope.MESSAGE_SEND: settings.chat_message_send_rate_limit_per_window,
            ChatRateLimitScope.FEEDBACK_WRITE: settings.chat_feedback_rate_limit_per_window,
            ChatRateLimitScope.WEBSOCKET_SEND: settings.chat_websocket_send_rate_limit_per_window,
        }
        return RateLimitPolicy(scope=scope, limit=limit_by_scope[scope], window_seconds=window_seconds)

    async def enforce(
        self,
        *,
        scope: ChatRateLimitScope,
        client_id: str,
        session_id: str | None = None,
    ) -> RateLimitDecision:
        """Consume one request from the matching rate-limit bucket."""
        policy = self.get_policy(scope)
        bucket_input = f"{scope.value}:{client_id}:{session_id or '-'}"
        bucket_key = hashlib.sha256(bucket_input.encode("utf-8")).hexdigest()

        row = await postgres_client.fetchrow(
            """
            INSERT INTO chat_request_rate_limits (
                bucket_key,
                scope,
                subject,
                session_id,
                request_count,
                limit_value,
                window_seconds,
                window_started_at,
                window_expires_at,
                updated_at
            ) VALUES (
                $1,
                $2,
                $3,
                $4,
                1,
                $5,
                $6,
                NOW(),
                NOW() + ($6 * INTERVAL '1 second'),
                NOW()
            )
            ON CONFLICT (bucket_key)
            DO UPDATE
            SET
                request_count = CASE
                    WHEN chat_request_rate_limits.window_expires_at <= NOW() THEN 1
                    ELSE chat_request_rate_limits.request_count + 1
                END,
                limit_value = EXCLUDED.limit_value,
                window_seconds = EXCLUDED.window_seconds,
                window_started_at = CASE
                    WHEN chat_request_rate_limits.window_expires_at <= NOW() THEN NOW()
                    ELSE chat_request_rate_limits.window_started_at
                END,
                window_expires_at = CASE
                    WHEN chat_request_rate_limits.window_expires_at <= NOW()
                    THEN NOW() + (EXCLUDED.window_seconds * INTERVAL '1 second')
                    ELSE chat_request_rate_limits.window_expires_at
                END,
                updated_at = NOW()
            RETURNING
                request_count,
                limit_value,
                GREATEST(
                    CEIL(EXTRACT(EPOCH FROM (window_expires_at - NOW()))),
                    0
                )::integer AS retry_after_seconds
            """,
            bucket_key,
            policy.scope.value,
            client_id,
            session_id,
            policy.limit,
            policy.window_seconds,
        )
        if not row:
            raise RuntimeError("Failed to evaluate chat rate limit")

        decision = RateLimitDecision(
            allowed=int(row["request_count"]) <= int(row["limit_value"]),
            limit=int(row["limit_value"]),
            request_count=int(row["request_count"]),
            retry_after_seconds=max(int(row["retry_after_seconds"]), 1),
        )
        if not decision.allowed:
            raise ChatRateLimitExceeded(
                scope=scope,
                limit=decision.limit,
                retry_after_seconds=decision.retry_after_seconds,
                request_count=decision.request_count,
            )
        return decision


def build_http_request_context(
    request: Request,
    *,
    route_name: str,
    session_id: str | None = None,
    stream: bool = False,
) -> ChatRequestContext:
    """Create request context for an HTTP chat route."""
    client_id = extract_client_identifier(request)
    request_id = extract_request_id_from_scope(request)
    return _build_request_context(
        route_name=route_name,
        method=request.method,
        transport="http",
        client_id=client_id,
        request_id=request_id,
        session_id=session_id,
        stream=stream,
    )


def build_websocket_request_context(
    websocket: WebSocket,
    *,
    route_name: str,
    client_id: str,
    session_id: str | None = None,
) -> ChatRequestContext:
    """Create request context for chat messages delivered over WebSocket."""
    request_id = websocket.headers.get("x-request-id", client_id)
    return _build_request_context(
        route_name=route_name,
        method="WEBSOCKET",
        transport="websocket",
        client_id=client_id,
        request_id=request_id,
        session_id=session_id,
        stream=True,
    )


def extract_client_identifier(request: Request) -> str:
    """Resolve the best available client identifier from an HTTP request."""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def record_chat_success(
    context: ChatRequestContext,
    *,
    status_code: int,
    extra_tags: dict[str, str] | None = None,
) -> None:
    """Record a successful chat request."""
    _record_chat_result(
        context,
        status_code=status_code,
        error_code=None,
        detail=None,
        level="info",
        extra_tags=extra_tags,
    )


def record_chat_failure(
    context: ChatRequestContext,
    *,
    status_code: int,
    error_code: str,
    detail: str,
    exc_info: bool = False,
    extra_tags: dict[str, str] | None = None,
) -> None:
    """Record a failed chat request."""
    log_level = "warning" if status_code < 500 else "error"
    _record_chat_result(
        context,
        status_code=status_code,
        error_code=error_code,
        detail=detail,
        level=log_level,
        exc_info=exc_info,
        extra_tags=extra_tags,
    )


def record_stream_event(context: ChatRequestContext, event_type: str) -> None:
    """Track chat stream event counts."""
    metrics_collector.increment_counter(
        "chat_stream_events_total",
        tags={
            "route": context.route_name,
            "transport": context.transport,
            "event_type": event_type,
        },
    )


chat_rate_limiter = ChatRateLimiter()


def _build_request_context(
    *,
    route_name: str,
    method: str,
    transport: str,
    client_id: str,
    request_id: str,
    session_id: str | None,
    stream: bool,
) -> ChatRequestContext:
    metadata = {
        "route": route_name,
        "method": method,
        "transport": transport,
        "client_id": client_id,
        "request_id": request_id,
        "session_id": session_id or "-",
        "stream": stream,
    }
    trace = tracer.start_trace(operation=f"chat.{route_name}", metadata=metadata.copy())
    return ChatRequestContext(
        route_name=route_name,
        method=method,
        transport=transport,
        client_id=client_id,
        request_id=request_id,
        session_id=session_id,
        stream=stream,
        started_at=time.perf_counter(),
        trace_span_id=trace.span_id,
        trace_metadata=metadata,
    )


def _record_chat_result(
    context: ChatRequestContext,
    *,
    status_code: int,
    error_code: str | None,
    detail: str | None,
    level: str,
    exc_info: bool = False,
    extra_tags: dict[str, str] | None = None,
) -> None:
    duration_ms = (time.perf_counter() - context.started_at) * 1000
    tags = {
        "route": context.route_name,
        "method": context.method,
        "transport": context.transport,
        "status": str(status_code),
        "stream": str(context.stream).lower(),
    }
    if extra_tags:
        tags.update(extra_tags)

    metrics_collector.increment_counter("chat_requests_total", tags=tags)
    metrics_collector.record_histogram("chat_request_latency_ms", duration_ms, tags=tags)

    if status_code >= 400:
        metrics_collector.increment_counter(
            "chat_request_errors_total",
            tags={
                **tags,
                "error_code": error_code or "unknown",
            },
        )
    if error_code == "validation_failed":
        metrics_collector.increment_counter(
            "chat_validation_failures_total",
            tags={
                "route": context.route_name,
                "transport": context.transport,
                "method": context.method,
            },
        )
    if status_code == 429:
        metrics_collector.increment_counter(
            "chat_rate_limit_rejections_total",
            tags={
                "route": context.route_name,
                "transport": context.transport,
                "method": context.method,
            },
        )

    trace = tracer.active_traces.get(context.trace_span_id)
    if trace:
        if error_code:
            trace.metadata["error_code"] = error_code
            trace.metadata["detail"] = detail or ""
            trace.status = "error"
        trace.metadata["status_code"] = status_code
        trace.metadata["duration_ms"] = round(duration_ms, 2)
    tracer.finish_trace(context.trace_span_id)

    log_message = (
        f"chat_request route={context.route_name} transport={context.transport} "
        f"method={context.method} status={status_code} duration_ms={duration_ms:.2f} "
        f"client_id={context.client_id} session_id={context.session_id or '-'} "
        f"request_id={context.request_id}"
    )
    if error_code:
        log_message = f"{log_message} error_code={error_code} detail={detail or ''}"

    if level == "error":
        logger.error(log_message, exc_info=exc_info)
    elif level == "warning":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def extract_request_id_from_scope(request: Request) -> str:
    """Resolve the request ID from middleware state or request headers."""
    state_request_id = getattr(request.state, "request_id", None)
    if state_request_id:
        return str(state_request_id)
    return request.headers.get("x-request-id", "missing-request-id")
