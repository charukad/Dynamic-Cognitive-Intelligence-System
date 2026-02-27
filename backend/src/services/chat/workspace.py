"""Chat workspace projection service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from src.core import get_logger
from src.infrastructure.repositories.chat_repository import chat_repository
from src.services.memory import working_memory_service

logger = get_logger(__name__)


class ChatWorkspaceService:
    """Build a canonical workspace view from persisted chat state."""

    async def get_workspace(self, session_id: str) -> dict[str, Any]:
        summary = await chat_repository.get_session_summary(session_id)
        if not summary:
            raise ValueError(f"Chat session not found: {session_id}")

        message_count = int(summary.get("message_count", 0) or 0)
        rows = await chat_repository.list_messages(
            session_id=session_id,
            limit=min(max(message_count + 10, 25), 250),
        )
        messages = [dict(row) for row in rows]

        try:
            working_context = await working_memory_service.get_context(session_id) or {}
        except Exception as exc:
            logger.warning("Failed to load working context for workspace %s: %s", session_id, exc)
            working_context = {}

        latest_user = self._find_latest(messages, sender="user")
        latest_assistant = self._find_latest(messages, sender="agent")
        latest_route = self._extract_route(
            latest_assistant.get("metadata") if latest_assistant else None
        ) or self._extract_route(latest_user.get("metadata") if latest_user else None)

        return {
            "session": self._build_session(summary),
            "route": latest_route,
            "rooms": self._build_rooms(
                summary=summary,
                messages=messages,
                working_context=working_context,
                latest_route=latest_route,
                latest_user=latest_user,
                latest_assistant=latest_assistant,
            ),
            "activity_feed": self._build_activity_feed(
                summary=summary,
                messages=messages,
                working_context=working_context,
                latest_route=latest_route,
            ),
            "office_stats": self._build_office_stats(
                summary=summary,
                messages=messages,
                working_context=working_context,
                latest_route=latest_route,
            ),
            "task_stages": self._build_task_stages(
                messages=messages,
                latest_route=latest_route,
                latest_user=latest_user,
                latest_assistant=latest_assistant,
                working_context=working_context,
            ),
            "replay": self._build_replay(messages=messages, latest_route=latest_route),
            "working_context": working_context,
        }

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _build_session(summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": summary["id"],
            "title": summary["title"],
            "status": summary["status"],
            "selected_agent_id": summary.get("selected_agent_id"),
            "message_count": int(summary.get("message_count", 0) or 0),
            "last_message": summary.get("last_message", "") or "",
            "last_message_at": summary.get("last_message_at"),
            "metadata": summary.get("metadata", {}),
            "created_at": summary["created_at"],
            "updated_at": summary["updated_at"],
        }

    @staticmethod
    def _find_latest(messages: list[dict[str, Any]], *, sender: str) -> Optional[dict[str, Any]]:
        for message in reversed(messages):
            if message.get("sender") == sender:
                return message
        return None

    @staticmethod
    def _extract_route(metadata: Optional[dict[str, Any]]) -> dict[str, Any]:
        routing = (metadata or {}).get("routing")
        if not isinstance(routing, dict):
            return {
                "source": None,
                "reason": None,
                "inferred_task_type": None,
                "inferred_agent_type": None,
                "mode": None,
                "start_project_mode": False,
            }

        return {
            "source": routing.get("source"),
            "reason": routing.get("reason"),
            "inferred_task_type": routing.get("inferred_task_type"),
            "inferred_agent_type": routing.get("inferred_agent_type"),
            "mode": routing.get("mode"),
            "start_project_mode": bool(routing.get("start_project_mode")),
        }

    def _build_rooms(
        self,
        *,
        summary: dict[str, Any],
        messages: list[dict[str, Any]],
        working_context: dict[str, Any],
        latest_route: dict[str, Any],
        latest_user: Optional[dict[str, Any]],
        latest_assistant: Optional[dict[str, Any]],
    ) -> list[dict[str, str]]:
        failure_count = sum(1 for message in messages if message.get("status") == "failed")
        memory_turns = len(working_context.get("recent_turns", []))
        latest_assistant_status = latest_assistant.get("status") if latest_assistant else None
        selected_agent_name = working_context.get("selected_agent_name") or summary.get("last_agent_name")

        return [
            {
                "id": "strategy",
                "title": "Strategy Center",
                "label": "Planning Room",
                "status": "active" if latest_user and latest_assistant_status != "completed" else "watching",
                "detail": latest_route.get("reason") or "Incoming user requests are decomposed and routed here first.",
                "metric": latest_route.get("inferred_task_type") or "general intake",
                "description": "Planning surface for orchestration, routing, and visible task decomposition.",
            },
            {
                "id": "boss",
                "title": "Boss's Office",
                "label": "Executive Oversight",
                "status": "alert" if failure_count else "idle",
                "detail": (
                    f"{failure_count} failed turns require intervention."
                    if failure_count
                    else "Escalation and retry controls remain on standby."
                ),
                "metric": "attention required" if failure_count else "nominal",
                "description": "Executive oversight room for retries, risk review, and intervention traces.",
            },
            {
                "id": "voting",
                "title": "Voting Chamber",
                "label": "Governance",
                "status": "active" if latest_route.get("start_project_mode") and latest_route.get("source") == "executive_router" else "idle",
                "detail": (
                    "Executive routing is coordinating a project-style decision path."
                    if latest_route.get("start_project_mode")
                    else "No governance event has been triggered for this session."
                ),
                "metric": "project governance" if latest_route.get("start_project_mode") else "standby",
                "description": "Decision room for approvals, conflict resolution, and governance events.",
            },
            {
                "id": "collaboration",
                "title": "Collaboration Hub",
                "label": "Shared Pod Space",
                "status": "active" if latest_route.get("start_project_mode") or latest_route.get("source") == "executive_router" else "idle",
                "detail": (
                    f"{selected_agent_name or 'Assigned specialists'} are coordinating on the current session path."
                    if latest_user
                    else "Specialists gather here when a request requires visible collaboration."
                ),
                "metric": "multi-step flow" if latest_route.get("start_project_mode") else "single path",
                "description": "Cross-checking and collaborative execution surface for complex requests.",
            },
            {
                "id": "memory",
                "title": "Memory Vault",
                "label": "Context Core",
                "status": "watching" if working_context else "idle",
                "detail": (
                    f"{memory_turns} recent turns are available in working memory."
                    if working_context
                    else "No working-memory context has been stored yet."
                ),
                "metric": f"{memory_turns} turn cache" if memory_turns else "no recall yet",
                "description": "Persistent context surface for recent turns, route history, and session memory.",
            },
            {
                "id": "incubator",
                "title": "Specialist Incubator",
                "label": "Capability Lab",
                "status": "watching" if latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type") else "idle",
                "detail": (
                    "Project mode is active without a strong specialist match."
                    if latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type")
                    else "No hiring or specialist incubation event has been detected."
                ),
                "metric": latest_route.get("inferred_agent_type") or "no hiring event",
                "description": "Capability expansion area for specialist discovery and onboarding workflows.",
            },
            {
                "id": "execution",
                "title": "Active Pods",
                "label": "Execution Floor",
                "status": "active" if latest_assistant else "watching",
                "detail": (
                    f"{latest_assistant.get('agent_name') or selected_agent_name or 'Assistant'} owns the latest response."
                    if latest_assistant
                    else "Execution pods will populate after the first response is generated."
                ),
                "metric": latest_assistant.get("agent_name") if latest_assistant else (selected_agent_name or "standby"),
                "description": "Specialist execution surface for active work, validation, and delivery preparation.",
            },
        ]

    def _build_activity_feed(
        self,
        *,
        summary: dict[str, Any],
        messages: list[dict[str, Any]],
        working_context: dict[str, Any],
        latest_route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        if latest_route.get("source"):
            items.append({
                "id": "route-latest",
                "type": "AGENT_ASSIGNED",
                "description": (
                    f"{self._format_route_source(latest_route.get('source'))} selected"
                    f"{f' for {latest_route.get('inferred_task_type')}' if latest_route.get('inferred_task_type') else ''}."
                ),
                "timestamp": summary["updated_at"],
                "severity": "info",
            })

        if working_context.get("recent_turns"):
            items.append({
                "id": "memory-context",
                "type": "CONTEXT_RECALLED",
                "description": f"{len(working_context['recent_turns'])} recent turns are cached for session continuity.",
                "timestamp": self._parse_timestamp(working_context.get("updated_at")) or summary["updated_at"],
                "severity": "info",
            })

        for message in messages[-10:]:
            created_at = message.get("created_at") or summary["updated_at"]
            if message.get("sender") == "user":
                items.append({
                    "id": f"{message['id']}:task",
                    "type": "TASK_STARTED",
                    "description": "User request entered the office workflow.",
                    "timestamp": created_at,
                    "severity": "info",
                })
            elif message.get("status") == "failed":
                items.append({
                    "id": f"{message['id']}:retry",
                    "type": "RETRY_TRIGGERED",
                    "description": message.get("error_message") or "Assistant response failed and requires recovery.",
                    "timestamp": created_at,
                    "severity": "critical",
                })
            else:
                items.append({
                    "id": f"{message['id']}:response",
                    "type": "FINAL_RESPONSE_SENT",
                    "description": f"{message.get('agent_name') or 'Assistant'} produced a completed response.",
                    "timestamp": created_at,
                    "severity": "success",
                })

            if message.get("feedback_type"):
                items.append({
                    "id": f"{message['id']}:feedback",
                    "type": "FEEDBACK_RECORDED",
                    "description": f"User submitted {message['feedback_type']} feedback for the latest assistant turn.",
                    "timestamp": message.get("feedback_updated_at") or created_at,
                    "severity": "info",
                })

        items.sort(key=lambda item: item["timestamp"], reverse=True)
        return items[:12]

    def _build_office_stats(
        self,
        *,
        summary: dict[str, Any],
        messages: list[dict[str, Any]],
        working_context: dict[str, Any],
        latest_route: dict[str, Any],
    ) -> list[dict[str, str]]:
        user_turns = sum(1 for message in messages if message.get("sender") == "user")
        assistant_turns = sum(1 for message in messages if message.get("sender") == "agent")
        failure_count = sum(1 for message in messages if message.get("status") == "failed")
        feedback_total = sum(1 for message in messages if message.get("feedback_type"))
        positive_feedback = sum(1 for message in messages if message.get("feedback_type") == "thumbs_up")
        route_reason = latest_route.get("reason")
        feedback_ratio = (
            f"{round((positive_feedback / feedback_total) * 100)}%"
            if feedback_total
            else "No data"
        )

        return [
            {
                "label": "Persisted Messages",
                "value": str(int(summary.get("message_count", 0) or 0)),
                "hint": "Saved turns in this session",
            },
            {
                "label": "User Requests",
                "value": str(user_turns),
                "hint": "Intake messages received",
            },
            {
                "label": "Assistant Deliveries",
                "value": str(assistant_turns),
                "hint": "Completed or streaming assistant turns",
            },
            {
                "label": "Failure Count",
                "value": str(failure_count),
                "hint": "Persisted failed response attempts",
            },
            {
                "label": "Feedback Score",
                "value": feedback_ratio,
                "hint": "Positive feedback ratio on stored responses",
            },
            {
                "label": "Execution Mode",
                "value": self._format_mode(latest_route.get("mode")),
                "hint": route_reason or "No routed mode captured yet",
            },
            {
                "label": "Route Source",
                "value": self._format_route_source(latest_route.get("source")),
                "hint": latest_route.get("inferred_task_type") or "Awaiting task type",
            },
            {
                "label": "Memory Turns",
                "value": str(len(working_context.get("recent_turns", []))),
                "hint": "Working-memory turns available to the session",
            },
        ]

    def _build_task_stages(
        self,
        *,
        messages: list[dict[str, Any]],
        latest_route: dict[str, Any],
        latest_user: Optional[dict[str, Any]],
        latest_assistant: Optional[dict[str, Any]],
        working_context: dict[str, Any],
    ) -> list[dict[str, str]]:
        latest_assistant_status = latest_assistant.get("status") if latest_assistant else None
        failure_message = latest_assistant.get("error_message") if latest_assistant and latest_assistant_status == "failed" else None

        return [
            {
                "id": "intake",
                "title": "Front Desk Intake",
                "status": "done" if latest_user else "waiting",
                "detail": "User request was accepted into the live conversation flow." if latest_user else "Waiting for the first request.",
            },
            {
                "id": "routing",
                "title": "Routing and Planning",
                "status": "done" if latest_route.get("source") else "waiting",
                "detail": latest_route.get("reason") or "Route and task type will appear after the first sent message.",
            },
            {
                "id": "execution",
                "title": "Specialist Execution",
                "status": "active" if latest_assistant_status == "streaming" else ("done" if latest_assistant else "waiting"),
                "detail": (
                    f"{latest_assistant.get('agent_name') or 'Assistant'} is streaming a response."
                    if latest_assistant_status == "streaming"
                    else (f"{latest_assistant.get('agent_name') or 'Assistant'} completed the latest execution." if latest_assistant else "Execution pods are idle.")
                ),
            },
            {
                "id": "memory",
                "title": "Context and Recall",
                "status": "done" if working_context else "waiting",
                "detail": (
                    f"{len(working_context.get('recent_turns', []))} recent turns are retained in working memory."
                    if working_context
                    else "No working-memory context recorded yet."
                ),
            },
            {
                "id": "delivery",
                "title": "Delivery and Validation",
                "status": "alert" if failure_message else ("done" if latest_assistant_status == "completed" else "waiting"),
                "detail": failure_message or (
                    "Latest response delivered successfully."
                    if latest_assistant_status == "completed"
                    else "Delivery remains pending."
                ),
            },
        ]

    def _build_replay(
        self,
        *,
        messages: list[dict[str, Any]],
        latest_route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        replay_items: list[dict[str, Any]] = []
        if latest_route.get("source"):
            replay_items.append({
                "id": "replay:route",
                "type": "ROUTE_DECIDED",
                "description": latest_route.get("reason") or "Route resolved for the latest conversation turn.",
                "timestamp": self._now(),
            })

        for message in messages[-12:]:
            replay_items.append({
                "id": f"replay:{message['id']}",
                "type": "USER_MESSAGE" if message.get("sender") == "user" else "ASSISTANT_MESSAGE",
                "description": self._truncate(message.get("content", "")),
                "timestamp": message.get("created_at") or self._now(),
            })

        replay_items.sort(key=lambda item: item["timestamp"], reverse=True)
        return replay_items[:12]

    @staticmethod
    def _format_route_source(source: Optional[str]) -> str:
        if source == "executive_router":
            return "Executive Router"
        if source == "explicit":
            return "Manual Selection"
        if source == "session":
            return "Session Preference"
        if source == "auto":
            return "Auto Router"
        return "Awaiting route"

    @staticmethod
    def _format_mode(mode: Optional[str]) -> str:
        if mode == "high_accuracy":
            return "High Accuracy"
        if mode == "budget":
            return "Budget Mode"
        if mode == "balanced":
            return "Balanced"
        return "Not captured"

    @staticmethod
    def _truncate(value: str, limit: int = 160) -> str:
        compact = " ".join(value.strip().split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3] + "..."

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None


chat_workspace_service = ChatWorkspaceService()
