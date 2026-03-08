"""Chat workspace projection service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from src.core import get_logger
from src.infrastructure.repositories.chat_repository import chat_repository
from src.services.memory import episodic_memory_service, working_memory_service

logger = get_logger(__name__)


class ChatWorkspaceService:
    """Build a canonical workspace view from persisted chat state."""

    _ROOM_ACTIONS = {
        "strategy": [
            "Open task DAG viewer",
            "Inspect routing decisions and dependency branches",
            "Review projected delivery path and execution mode",
        ],
        "boss": [
            "Review retry and intervention history",
            "Inspect policy and escalation conditions",
            "Audit executive oversight signals for this session",
        ],
        "voting": [
            "Inspect governance event history",
            "Review debate or approval outcomes",
            "Track project-mode decision checkpoints",
        ],
        "collaboration": [
            "Inspect collaboration log and coordination pulses",
            "Review multi-agent context hand-offs",
            "Trace shared execution dependencies",
        ],
        "memory": [
            "Inspect working-memory recall state",
            "Review session continuity and route context",
            "Audit stored context referenced by the latest turn",
        ],
        "incubator": [
            "Review specialist-gap signals",
            "Inspect candidate capability triggers",
            "Track incubation or hiring readiness",
        ],
        "execution": [
            "Inspect active delivery events",
            "Review latest assistant outputs",
            "Audit execution ownership and completion state",
        ],
    }

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
        event_rows = await chat_repository.list_events(
            session_id=session_id,
            limit=min(max(message_count * 4, 40), 250),
        )
        events = list(reversed([dict(row) for row in event_rows]))

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
                events=events,
                working_context=working_context,
                latest_route=latest_route,
                latest_user=latest_user,
                latest_assistant=latest_assistant,
            ),
            "activity_feed": self._build_activity_feed(
                summary=summary,
                messages=messages,
                events=events,
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
            "replay": self._build_replay(messages=messages, events=events, latest_route=latest_route),
            "graph_nodes": self._build_graph_nodes(summary=summary, latest_route=latest_route, latest_assistant=latest_assistant),
            "graph_edges": self._build_graph_edges(events=events, latest_route=latest_route),
            "room_timeline": self._build_room_timeline(events=events),
            "working_context": working_context,
        }

    async def get_room_detail(self, session_id: str, room_id: str) -> dict[str, Any]:
        room_context = await self._load_room_context(session_id, room_id)
        return self._build_room_detail_payload(**room_context)

    async def get_voting_detail(self, session_id: str) -> dict[str, Any]:
        room_context = await self._load_room_context(session_id, "voting")
        detail = self._build_room_detail_payload(**room_context)
        latest_route = room_context["latest_route"]
        room_events = room_context["room_events"]
        participants = self._extract_participants(
            messages=room_context["messages"],
            working_context=room_context["working_context"],
            room_events=room_events,
        )
        criteria = [
            detail["summary"],
            f"Task type: {latest_route.get('inferred_task_type') or 'general'}",
            f"Execution mode: {self._format_mode(latest_route.get('mode'))}",
        ]
        if latest_route.get("start_project_mode"):
            criteria.append("Project mode remains enabled for this request path.")

        latest_event = room_events[-1] if room_events else None
        return {
            "room": room_context["room"],
            "status": room_context["room"]["status"],
            "decision_outcome": latest_event.get("description") if latest_event else None,
            "participants": participants,
            "criteria": criteria,
            "reasoning": detail["highlights"],
            "events": detail["recent_events"],
            "metrics": [
                {
                    "label": "Governance Events",
                    "value": str(len(room_events)),
                    "hint": "Persisted Voting Chamber checkpoints",
                },
                {
                    "label": "Project Mode",
                    "value": "Enabled" if latest_route.get("start_project_mode") else "Disabled",
                    "hint": "Whether governance is being considered for a project path",
                },
                {
                    "label": "Executive Route",
                    "value": "Yes" if latest_route.get("source") == "executive_router" else "No",
                    "hint": "Whether the executive router activated this path",
                },
            ],
        }

    async def get_collaboration_detail(self, session_id: str) -> dict[str, Any]:
        room_context = await self._load_room_context(session_id, "collaboration")
        detail = self._build_room_detail_payload(**room_context)
        working_context = room_context["working_context"]
        return {
            "room": room_context["room"],
            "summary": detail["summary"],
            "participants": self._extract_participants(
                messages=room_context["messages"],
                working_context=working_context,
                room_events=room_context["room_events"],
            ),
            "shared_working_memory": {
                "selected_agent_name": working_context.get("selected_agent_name"),
                "route_source": working_context.get("route_source"),
                "route_reason": working_context.get("route_reason"),
                "inferred_task_type": working_context.get("inferred_task_type"),
                "mode": working_context.get("mode"),
                "recent_turns": list(working_context.get("recent_turns", []))[-3:],
            },
            "coordination_log": detail["recent_events"],
            "related_messages": detail["related_messages"],
            "metrics": detail["metrics"],
        }

    async def get_incubator_detail(self, session_id: str) -> dict[str, Any]:
        room_context = await self._load_room_context(session_id, "incubator")
        detail = self._build_room_detail_payload(**room_context)
        latest_route = room_context["latest_route"]
        room_events = room_context["room_events"]
        gap_detected = bool(
            room_events
            or (latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type"))
        )
        benchmark_signals = [
            detail["summary"],
            f"Inferred specialist: {latest_route.get('inferred_agent_type') or 'undetermined'}",
            f"Project mode: {'enabled' if latest_route.get('start_project_mode') else 'disabled'}",
        ]
        benchmark_signals.extend(detail["highlights"][:2])

        return {
            "room": room_context["room"],
            "status": room_context["room"]["status"],
            "summary": detail["summary"],
            "gap_detected": gap_detected,
            "inferred_specialist": latest_route.get("inferred_agent_type"),
            "benchmark_signals": benchmark_signals,
            "events": detail["recent_events"],
            "metrics": detail["metrics"],
            "actions": detail["actions"],
        }

    async def get_memory_vault_detail(self, session_id: str) -> dict[str, Any]:
        room_context = await self._load_room_context(session_id, "memory")
        detail = self._build_room_detail_payload(**room_context)
        working_context = room_context["working_context"]

        try:
            session_memories = await episodic_memory_service.get_session_memories(session_id)
        except Exception as exc:
            logger.warning("Failed to load episodic memories for session %s: %s", session_id, exc)
            session_memories = []

        ordered_memories = sorted(
            session_memories,
            key=lambda memory: memory.created_at,
            reverse=True,
        )[:8]

        return {
            "room": room_context["room"],
            "summary": detail["summary"],
            "working_context": working_context,
            "preference_signals": self._build_preference_signals(working_context),
            "retrieval_events": detail["recent_events"],
            "recent_turns": [
                {
                    "user": turn.get("user", ""),
                    "assistant": turn.get("assistant", ""),
                    "agent_id": turn.get("agent_id"),
                    "agent_name": turn.get("agent_name"),
                    "mode": turn.get("mode"),
                    "updated_at": self._parse_timestamp(turn.get("updated_at")),
                }
                for turn in reversed(list(working_context.get("recent_turns", []))[-5:])
            ],
            "episodic_memories": [
                {
                    "id": str(memory.id),
                    "content": self._truncate(memory.content, 220),
                    "importance_score": memory.importance_score,
                    "tags": memory.tags,
                    "created_at": memory.created_at,
                }
                for memory in ordered_memories
            ],
            "metrics": detail["metrics"],
        }

    async def get_dag_detail(self, session_id: str) -> dict[str, Any]:
        workspace, messages, events, working_context, latest_route = await self._load_session_context(session_id)
        latest_user = self._find_latest(messages, sender="user")
        latest_assistant = self._find_latest(messages, sender="agent")
        nodes = self._build_dag_nodes(
            messages=messages,
            events=events,
            latest_route=latest_route,
            latest_user=latest_user,
            latest_assistant=latest_assistant,
            working_context=working_context,
        )
        edges = self._build_dag_edges(nodes)
        latest_node = next(
            (
                node for node in reversed(nodes)
                if node["status"] in {"done", "active", "alert"} and (node["event_ids"] or node["status"] != "waiting")
            ),
            None,
        )
        event_times = [event["created_at"] for event in events if isinstance(event.get("created_at"), datetime)]
        total_duration_ms = None
        if len(event_times) >= 2:
            total_duration_ms = int((event_times[-1] - event_times[0]).total_seconds() * 1000)

        summary = (
            latest_node["detail"]
            if latest_node
            else "Task DAG will populate after the first persisted workspace event."
        )
        return {
            "session_id": session_id,
            "summary": summary,
            "latest_node_id": latest_node["id"] if latest_node else None,
            "total_duration_ms": total_duration_ms,
            "nodes": nodes,
            "edges": edges,
        }

    async def get_replay_detail(self, session_id: str) -> dict[str, Any]:
        workspace, messages, events, _, _ = await self._load_session_context(session_id)
        del workspace
        message_by_id = {str(message["id"]): message for message in messages}
        frames = self._build_replay_frames(events=events, message_by_id=message_by_id)
        started_at = frames[0]["timestamp"] if frames else None
        ended_at = frames[-1]["timestamp"] if frames else None
        total_duration_ms = None
        if started_at and ended_at:
            total_duration_ms = int((ended_at - started_at).total_seconds() * 1000)
        summary = (
            frames[-1]["description"]
            if frames
            else "Replay becomes available after persisted workspace events are recorded."
        )
        return {
            "session_id": session_id,
            "summary": summary,
            "current_index": len(frames) - 1 if frames else 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "total_duration_ms": total_duration_ms,
            "frames": frames,
        }

    async def _load_session_context(
        self,
        session_id: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        workspace = await self.get_workspace(session_id)
        message_count = int(workspace["session"].get("message_count", 0) or 0)
        message_rows = await chat_repository.list_messages(
            session_id=session_id,
            limit=min(max(message_count + 10, 25), 250),
        )
        event_rows = await chat_repository.list_events(
            session_id=session_id,
            limit=min(max(message_count * 4, 40), 250),
        )
        messages = [dict(row) for row in message_rows]
        events = list(reversed([dict(row) for row in event_rows]))
        working_context = workspace.get("working_context", {})
        latest_route = workspace["route"]
        return workspace, messages, events, working_context, latest_route

    async def _load_room_context(self, session_id: str, room_id: str) -> dict[str, Any]:
        workspace, messages, _, _, latest_route = await self._load_session_context(session_id)
        room = next((item for item in workspace["rooms"] if item["id"] == room_id), None)
        if not room:
            raise ValueError(f"Chat workspace room not found: {room_id}")
        room_event_rows = await chat_repository.list_events(
            session_id=session_id,
            room_id=room_id,
            limit=30,
        )
        room_events = list(reversed([dict(row) for row in room_event_rows]))
        return {
            "workspace": workspace,
            "room_id": room_id,
            "room": room,
            "messages": messages,
            "room_events": room_events,
            "latest_route": latest_route,
            "working_context": workspace.get("working_context", {}),
        }

    def _build_room_detail_payload(
        self,
        *,
        room_id: str,
        room: dict[str, Any],
        messages: list[dict[str, Any]],
        room_events: list[dict[str, Any]],
        latest_route: dict[str, Any],
        working_context: dict[str, Any],
        workspace: dict[str, Any],
    ) -> dict[str, Any]:
        del workspace
        return {
            "room": room,
            "summary": self._build_room_detail_summary(
                room_id=room_id,
                room=room,
                latest_route=latest_route,
                working_context=working_context,
                room_events=room_events,
                messages=messages,
            ),
            "metrics": self._build_room_detail_metrics(
                room_id=room_id,
                latest_route=latest_route,
                working_context=working_context,
                room_events=room_events,
                messages=messages,
            ),
            "highlights": self._build_room_detail_highlights(
                room_id=room_id,
                latest_route=latest_route,
                working_context=working_context,
                room_events=room_events,
                messages=messages,
            ),
            "recent_events": self._build_room_timeline(events=room_events),
            "related_messages": self._build_room_related_messages(
                room_id=room_id,
                room_events=room_events,
                messages=messages,
            ),
            "actions": self._ROOM_ACTIONS.get(room_id, []),
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
        events: list[dict[str, Any]],
        working_context: dict[str, Any],
        latest_route: dict[str, Any],
        latest_user: Optional[dict[str, Any]],
        latest_assistant: Optional[dict[str, Any]],
    ) -> list[dict[str, str]]:
        failure_count = sum(1 for message in messages if message.get("status") == "failed")
        memory_turns = len(working_context.get("recent_turns", []))
        latest_assistant_status = latest_assistant.get("status") if latest_assistant else None
        selected_agent_name = working_context.get("selected_agent_name") or summary.get("last_agent_name")
        latest_room_events = self._latest_room_events(events)

        return [
            {
                "id": "strategy",
                "title": "Strategy Center",
                "label": "Planning Room",
                "status": self._room_status("strategy", latest_room_events, default="watching", active_fallback=bool(latest_user and latest_assistant_status != "completed")),
                "detail": latest_room_events.get("strategy", {}).get("description") or latest_route.get("reason") or "Incoming user requests are decomposed and routed here first.",
                "metric": latest_route.get("inferred_task_type") or "general intake",
                "description": "Planning surface for orchestration, routing, and visible task decomposition.",
            },
            {
                "id": "boss",
                "title": "Boss's Office",
                "label": "Executive Oversight",
                "status": self._room_status("boss", latest_room_events, default="idle", active_fallback=bool(failure_count)),
                "detail": (
                    latest_room_events.get("boss", {}).get("description")
                    or f"{failure_count} failed turns require intervention."
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
                "status": self._room_status("voting", latest_room_events, default="idle", active_fallback=bool(latest_route.get("start_project_mode") and latest_route.get("source") == "executive_router")),
                "detail": (
                    latest_room_events.get("voting", {}).get("description")
                    or
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
                "status": self._room_status("collaboration", latest_room_events, default="idle", active_fallback=bool(latest_route.get("start_project_mode") or latest_route.get("source") == "executive_router")),
                "detail": (
                    latest_room_events.get("collaboration", {}).get("description")
                    or
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
                "status": self._room_status("memory", latest_room_events, default="idle", active_fallback=bool(working_context)),
                "detail": (
                    latest_room_events.get("memory", {}).get("description")
                    or
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
                "status": self._room_status("incubator", latest_room_events, default="idle", active_fallback=bool(latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type"))),
                "detail": (
                    latest_room_events.get("incubator", {}).get("description")
                    or
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
                "status": self._room_status("execution", latest_room_events, default="watching", active_fallback=bool(latest_assistant)),
                "detail": (
                    latest_room_events.get("execution", {}).get("description")
                    or
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
        events: list[dict[str, Any]],
        working_context: dict[str, Any],
        latest_route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if events:
            items = [
                {
                    "id": event["id"],
                    "type": event["event_type"],
                    "description": event["description"],
                    "timestamp": event["created_at"],
                    "severity": event["severity"],
                }
                for event in reversed(events[-12:])
            ]
            items.sort(key=lambda item: item["timestamp"], reverse=True)
            return items[:12]

        items: list[dict[str, Any]] = []

        if latest_route.get("source"):
            items.append({
                "id": "route-latest",
                "type": "AGENT_ASSIGNED",
                "description": (
                    f"{self._format_route_source(latest_route.get('source'))} selected"
                    f" selected for {latest_route.get('inferred_task_type')}" if latest_route.get('inferred_task_type') else " selected."
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
        events: list[dict[str, Any]],
        latest_route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if events:
            replay_items = [
                {
                    "id": event["id"],
                    "type": event["event_type"],
                    "description": event["description"],
                    "timestamp": event["created_at"],
                }
                for event in reversed(events[-16:])
            ]
            replay_items.sort(key=lambda item: item["timestamp"], reverse=True)
            return replay_items[:16]

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

    def _build_dag_nodes(
        self,
        *,
        messages: list[dict[str, Any]],
        events: list[dict[str, Any]],
        latest_route: dict[str, Any],
        latest_user: Optional[dict[str, Any]],
        latest_assistant: Optional[dict[str, Any]],
        working_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        latest_assistant_status = latest_assistant.get("status") if latest_assistant else None
        latest_assistant_feedback = latest_assistant.get("feedback_type") if latest_assistant else None
        retry_events = [event for event in events if event.get("event_type") == "RETRY_TRIGGERED"]
        latest_assistant_metadata = (latest_assistant or {}).get("metadata") or {}
        model_used = None
        if isinstance(latest_assistant_metadata, dict):
            model_used = (
                latest_assistant_metadata.get("model")
                or latest_assistant_metadata.get("model_name")
                or latest_assistant_metadata.get("provider_model")
            )

        phase_configs = [
            {
                "id": "intake",
                "title": "Front Desk Intake",
                "room_id": "strategy",
                "dependencies": [],
                "event_types": {"TASK_STARTED"},
                "applicable": bool(latest_user),
                "fallback_detail": "User request was accepted into the live conversation flow." if latest_user else "Waiting for the first request.",
            },
            {
                "id": "memory_recall",
                "title": "Context Recall",
                "room_id": "memory",
                "dependencies": ["intake"],
                "event_types": {"CONTEXT_RECALLED"},
                "applicable": bool(working_context),
                "fallback_detail": (
                    f"{len(working_context.get('recent_turns', []))} recent turns are retained in working memory."
                    if working_context
                    else "No persisted context was recalled for this session."
                ),
            },
            {
                "id": "routing",
                "title": "Routing and Planning",
                "room_id": "strategy",
                "dependencies": ["intake"],
                "event_types": {"ROUTE_DECIDED"},
                "applicable": bool(latest_route.get("source")),
                "fallback_detail": latest_route.get("reason") or "Route will resolve on the next persisted turn.",
            },
            {
                "id": "governance",
                "title": "Governance Review",
                "room_id": "voting",
                "dependencies": ["routing"],
                "event_types": {"VOTING_STARTED"},
                "applicable": bool(latest_route.get("start_project_mode") or any(event.get("room_id") == "voting" for event in events)),
                "fallback_detail": "Voting Chamber stays on standby until governance is required.",
            },
            {
                "id": "collaboration",
                "title": "Collaboration Cycle",
                "room_id": "collaboration",
                "dependencies": ["routing"],
                "event_types": {"COLLABORATION_STARTED"},
                "applicable": bool(latest_route.get("start_project_mode") or any(event.get("room_id") == "collaboration" for event in events)),
                "fallback_detail": "Cross-functional collaboration will appear here when multi-agent work starts.",
            },
            {
                "id": "incubator",
                "title": "Capability Gap Review",
                "room_id": "incubator",
                "dependencies": ["routing"],
                "event_types": {"SPECIALIST_GAP_DETECTED"},
                "applicable": bool(
                    any(event.get("room_id") == "incubator" for event in events)
                    or (latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type"))
                ),
                "fallback_detail": "Incubator review remains idle until a specialist gap is detected.",
            },
            {
                "id": "assignment",
                "title": "Specialist Assignment",
                "room_id": "execution",
                "dependencies": ["routing"],
                "event_types": {"AGENT_ASSIGNED"},
                "applicable": bool(latest_assistant or latest_route.get("source")),
                "fallback_detail": (
                    f"{latest_assistant.get('agent_name') or working_context.get('selected_agent_name') or 'Assistant'} owns the latest response path."
                    if latest_assistant or working_context.get("selected_agent_name")
                    else "No specialist has been assigned yet."
                ),
            },
            {
                "id": "execution",
                "title": "Execution Pod Run",
                "room_id": "execution",
                "dependencies": ["assignment", "collaboration"],
                "event_types": {"RESPONSE_STARTED"},
                "applicable": bool(latest_assistant or latest_assistant_status == "streaming"),
                "fallback_detail": (
                    f"{latest_assistant.get('agent_name') or 'Assistant'} is actively producing the latest response."
                    if latest_assistant_status == "streaming"
                    else "Execution pods are waiting for work."
                ),
            },
            {
                "id": "delivery",
                "title": "Delivery and Validation",
                "room_id": "execution",
                "dependencies": ["execution"],
                "event_types": {"FINAL_RESPONSE_SENT"},
                "applicable": bool(latest_assistant and latest_assistant_status == "completed"),
                "fallback_detail": (
                    "Latest response delivered successfully."
                    if latest_assistant and latest_assistant_status == "completed"
                    else "Delivery remains pending."
                ),
            },
            {
                "id": "recovery",
                "title": "Escalation and Recovery",
                "room_id": "boss",
                "dependencies": ["execution"],
                "event_types": {"RETRY_TRIGGERED"},
                "applicable": bool(retry_events),
                "fallback_detail": retry_events[-1]["description"] if retry_events else "No retries or escalations were triggered.",
            },
        ]

        nodes: list[dict[str, Any]] = []
        for config in phase_configs:
            phase_events = [
                event for event in events
                if event.get("event_type") in config["event_types"]
            ]
            if config["room_id"]:
                phase_events = [
                    event for event in phase_events
                    if event.get("room_id") == config["room_id"]
                ]

            started_at = phase_events[0]["created_at"] if phase_events else None
            completed_at = phase_events[-1]["created_at"] if phase_events else None
            execution_time_ms = None
            if started_at and completed_at:
                execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)
            assigned_agent = self._resolve_phase_agent_name(phase_events, messages)
            if not assigned_agent:
                assigned_agent = working_context.get("selected_agent_name")

            status = "waiting"
            if any(event.get("severity") == "critical" for event in phase_events):
                status = "alert"
            elif config["id"] == "execution" and (
                latest_assistant_status == "streaming"
                or self._latest_event_type(events) == "RESPONSE_STARTED"
            ):
                status = "active"
            elif config["id"] == "routing" and latest_route.get("source") and not phase_events:
                status = "active"
            elif config["id"] == "assignment" and latest_route.get("source") and not phase_events:
                status = "active"
            elif phase_events:
                status = "done"
            elif config["applicable"]:
                status = "active"

            evaluation_score = None
            if config["id"] == "delivery":
                if latest_assistant_feedback == "thumbs_up":
                    evaluation_score = 1.0
                elif latest_assistant_feedback == "thumbs_down":
                    evaluation_score = 0.0

            retry_count = len(retry_events) if config["id"] in {"delivery", "recovery", "execution"} else 0
            detail = phase_events[-1]["description"] if phase_events else config["fallback_detail"]

            nodes.append({
                "id": config["id"],
                "title": config["title"],
                "room_id": config["room_id"],
                "status": status,
                "detail": detail,
                "dependencies": config["dependencies"],
                "started_at": started_at,
                "completed_at": completed_at,
                "execution_time_ms": execution_time_ms,
                "assigned_agent": assigned_agent,
                "evaluation_score": evaluation_score,
                "retry_count": retry_count,
                "model_used": model_used if config["id"] in {"execution", "delivery"} else None,
                "event_ids": [event["id"] for event in phase_events],
            })

        return nodes

    def _build_dag_edges(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        node_map = {node["id"]: node for node in nodes}
        edges: list[dict[str, Any]] = []
        for node in nodes:
            for dependency in node.get("dependencies", []):
                if dependency not in node_map:
                    continue
                status = "info"
                if node["status"] == "alert":
                    status = "critical"
                elif node["status"] == "done":
                    status = "success"
                elif node["status"] == "active":
                    status = "warning"
                edges.append({
                    "id": f"{dependency}:{node['id']}",
                    "from_id": dependency,
                    "to_id": node["id"],
                    "label": "depends_on",
                    "status": status,
                })
        return edges

    def _build_replay_frames(
        self,
        *,
        events: list[dict[str, Any]],
        message_by_id: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        frames: list[dict[str, Any]] = []
        for index, event in enumerate(events):
            payload = event.get("payload") or {}
            related_message = None
            related_message_id = event.get("related_message_id")
            if related_message_id:
                related_message = message_by_id.get(str(related_message_id))

            graph_edge = payload.get("graph_edge") if isinstance(payload, dict) else None
            focus_node_ids: list[str] = []
            if event.get("room_id"):
                focus_node_ids.append(str(event["room_id"]))
            if isinstance(graph_edge, dict):
                for node_id in [graph_edge.get("from_id"), graph_edge.get("to_id")]:
                    if node_id and node_id not in focus_node_ids:
                        focus_node_ids.append(str(node_id))

            agent_name = None
            if isinstance(payload, dict):
                agent_name = payload.get("agent_name")
            if not agent_name and related_message:
                agent_name = related_message.get("agent_name")

            focus_edge_id = None
            if isinstance(graph_edge, dict):
                focus_edge_id = f"{graph_edge.get('from_id')}:{graph_edge.get('to_id')}:{graph_edge.get('label', event['event_type'])}"

            frames.append({
                "id": event["id"],
                "index": index,
                "type": event["event_type"],
                "description": event["description"],
                "timestamp": event["created_at"],
                "severity": event["severity"],
                "room_id": event.get("room_id"),
                "room_title": event.get("room_title"),
                "agent_name": agent_name,
                "related_message_id": str(related_message_id) if related_message_id else None,
                "focus_node_ids": focus_node_ids,
                "focus_edge_id": focus_edge_id,
            })
        return frames

    def _build_graph_nodes(
        self,
        *,
        summary: dict[str, Any],
        latest_route: dict[str, Any],
        latest_assistant: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        selected_agent_label = latest_assistant.get("agent_name") if latest_assistant else None
        if not selected_agent_label:
            selected_agent_label = summary.get("last_agent_name") or latest_route.get("inferred_agent_type") or "Assigned Agent"

        return [
            {"id": "front_desk", "label": "Front Desk", "kind": "intake", "status": "active", "x": 0.08, "y": 0.18},
            {"id": "strategy", "label": "Strategy Center", "kind": "room", "status": "active" if latest_route.get("source") else "watching", "x": 0.34, "y": 0.2},
            {"id": "boss", "label": "Boss's Office", "kind": "room", "status": "alert" if latest_route.get("source") == "executive_router" else "idle", "x": 0.74, "y": 0.12},
            {"id": "voting", "label": "Voting Chamber", "kind": "room", "status": "active" if latest_route.get("start_project_mode") else "idle", "x": 0.74, "y": 0.38},
            {"id": "collaboration", "label": "Collaboration Hub", "kind": "room", "status": "active" if latest_route.get("start_project_mode") else "watching", "x": 0.5, "y": 0.48},
            {"id": "memory", "label": "Memory Vault", "kind": "room", "status": "watching", "x": 0.26, "y": 0.68},
            {"id": "incubator", "label": "Incubator", "kind": "room", "status": "watching" if latest_route.get("start_project_mode") and not latest_route.get("inferred_agent_type") else "idle", "x": 0.74, "y": 0.7},
            {"id": "execution", "label": "Active Pods", "kind": "room", "status": "active" if latest_assistant else "watching", "x": 0.48, "y": 0.76},
            {"id": "assigned_agent", "label": str(selected_agent_label), "kind": "agent", "status": "active" if latest_assistant else "watching", "x": 0.5, "y": 0.9},
        ]

    def _build_graph_edges(
        self,
        *,
        events: list[dict[str, Any]],
        latest_route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        seen: set[str] = set()

        for event in events:
            graph_edge = (event.get("payload") or {}).get("graph_edge")
            if not isinstance(graph_edge, dict):
                continue

            edge = {
                "id": event["id"],
                "from_id": graph_edge.get("from_id", "front_desk"),
                "to_id": graph_edge.get("to_id", event.get("room_id") or "execution"),
                "label": graph_edge.get("label", event["event_type"]),
                "status": graph_edge.get("status", event.get("severity", "info")),
            }
            signature = f"{edge['from_id']}:{edge['to_id']}:{edge['label']}"
            if signature not in seen:
                seen.add(signature)
                edges.append(edge)

        if not edges:
            edges.extend([
                {"id": "edge:intake", "from_id": "front_desk", "to_id": "strategy", "label": "TASK_STARTED", "status": "success"},
                {"id": "edge:route", "from_id": "strategy", "to_id": "execution", "label": "AGENT_ASSIGNED", "status": "success"},
            ])
            if latest_route.get("start_project_mode"):
                edges.append({"id": "edge:project", "from_id": "strategy", "to_id": "collaboration", "label": "PROJECT_MODE", "status": "info"})
            if latest_route.get("source") == "executive_router":
                edges.append({"id": "edge:executive", "from_id": "strategy", "to_id": "boss", "label": "EXECUTIVE_ROUTER", "status": "warning"})

        return edges[:14]

    def _build_room_timeline(self, *, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = [
            {
                "id": event["id"],
                "room_id": event.get("room_id") or "strategy",
                "room_title": event.get("room_title"),
                "type": event["event_type"],
                "description": event["description"],
                "timestamp": event["created_at"],
                "severity": event["severity"],
            }
            for event in events
            if event.get("room_id")
        ]
        timeline.sort(key=lambda item: item["timestamp"], reverse=True)
        return timeline[:20]

    def _build_room_detail_summary(
        self,
        *,
        room_id: str,
        room: dict[str, Any],
        latest_route: dict[str, Any],
        working_context: dict[str, Any],
        room_events: list[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> str:
        latest_event = room_events[-1] if room_events else None
        latest_assistant = self._find_latest(messages, sender="agent")
        failure_count = sum(1 for message in messages if message.get("status") == "failed")

        if room_id == "strategy":
            return latest_event.get("description") if latest_event else (
                latest_route.get("reason")
                or "Strategy Center is waiting to decompose the next request and emit a delivery plan."
            )
        if room_id == "boss":
            return latest_event.get("description") if latest_event else (
                f"{failure_count} failed turns are currently flagged for executive review."
                if failure_count
                else "Boss's Office is idle until retries, risk conditions, or intervention signals appear."
            )
        if room_id == "voting":
            return latest_event.get("description") if latest_event else (
                "Voting Chamber records governance checkpoints for project-mode or executive-routed work."
                if latest_route.get("start_project_mode")
                else "No governance event has been triggered for this session yet."
            )
        if room_id == "collaboration":
            return latest_event.get("description") if latest_event else (
                "Collaboration Hub tracks multi-agent coordination and validation pulses across the office."
            )
        if room_id == "memory":
            return latest_event.get("description") if latest_event else (
                f"{len(working_context.get('recent_turns', []))} recent turns remain available for recall."
                if working_context
                else "Memory Vault will illuminate after session context or retrieval history is stored."
            )
        if room_id == "incubator":
            return latest_event.get("description") if latest_event else (
                "Incubator stays on standby until a specialist gap or hiring path is detected."
            )
        if room_id == "execution":
            return latest_event.get("description") if latest_event else (
                f"{latest_assistant.get('agent_name') or 'Assigned specialist'} owns the latest delivery path."
                if latest_assistant
                else "Execution pods will populate after the first assistant response is generated."
            )
        return room.get("detail") or room.get("description") or "No room summary available."

    def _build_room_detail_metrics(
        self,
        *,
        room_id: str,
        latest_route: dict[str, Any],
        working_context: dict[str, Any],
        room_events: list[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        latest_assistant = self._find_latest(messages, sender="agent")
        latest_user = self._find_latest(messages, sender="user")
        failure_count = sum(1 for message in messages if message.get("status") == "failed")
        metrics: list[dict[str, str]] = [
            {
                "label": "Recorded Events",
                "value": str(len(room_events)),
                "hint": "Persisted events for this room",
            }
        ]

        if room_id == "strategy":
            metrics.extend([
                {
                    "label": "Route Source",
                    "value": self._format_route_source(latest_route.get("source")),
                    "hint": latest_route.get("reason") or "Awaiting the first route",
                },
                {
                    "label": "Task Type",
                    "value": latest_route.get("inferred_task_type") or "General",
                    "hint": "Latest inferred work classification",
                },
                {
                    "label": "Execution Mode",
                    "value": self._format_mode(latest_route.get("mode")),
                    "hint": "Mode captured on the latest route",
                },
            ])
        elif room_id == "boss":
            metrics.extend([
                {
                    "label": "Failures",
                    "value": str(failure_count),
                    "hint": "Persisted failed assistant turns",
                },
                {
                    "label": "Escalations",
                    "value": str(sum(1 for event in room_events if event.get("severity") == "critical")),
                    "hint": "Critical boss-office events",
                },
                {
                    "label": "Latest Owner",
                    "value": latest_assistant.get("agent_name") or "Awaiting response",
                    "hint": "Last assistant associated with oversight",
                },
            ])
        elif room_id == "voting":
            metrics.extend([
                {
                    "label": "Governance State",
                    "value": "Active" if latest_route.get("start_project_mode") else "Standby",
                    "hint": "Project-mode governance visibility",
                },
                {
                    "label": "Vote Events",
                    "value": str(len(room_events)),
                    "hint": "Persisted governance checkpoints",
                },
                {
                    "label": "Executive Route",
                    "value": "Yes" if latest_route.get("source") == "executive_router" else "No",
                    "hint": "Whether the executive router activated this flow",
                },
            ])
        elif room_id == "collaboration":
            metrics.extend([
                {
                    "label": "Collaborative Turns",
                    "value": str(len(room_events)),
                    "hint": "Coordination events persisted for this session",
                },
                {
                    "label": "Project Mode",
                    "value": "Enabled" if latest_route.get("start_project_mode") else "Disabled",
                    "hint": "Whether collaborative orchestration is requested",
                },
                {
                    "label": "Lead Specialist",
                    "value": latest_assistant.get("agent_name") or latest_user.get("agent_name") or "Awaiting assignment",
                    "hint": "Latest visible owner in collaborative flow",
                },
            ])
        elif room_id == "memory":
            metrics.extend([
                {
                    "label": "Recent Turns",
                    "value": str(len(working_context.get("recent_turns", []))),
                    "hint": "Turns retained in working memory",
                },
                {
                    "label": "Route History",
                    "value": str(len(working_context.get("route_history", []))),
                    "hint": "Recorded route transitions in working context",
                },
                {
                    "label": "Selected Agent",
                    "value": working_context.get("selected_agent_name") or "Not captured",
                    "hint": "Latest agent stored in working context",
                },
            ])
        elif room_id == "incubator":
            metrics.extend([
                {
                    "label": "Gap Signals",
                    "value": str(len(room_events)),
                    "hint": "Capability-gap or incubation triggers",
                },
                {
                    "label": "Inferred Specialist",
                    "value": latest_route.get("inferred_agent_type") or "Undetermined",
                    "hint": "Latest inferred agent specialty",
                },
                {
                    "label": "Project Mode",
                    "value": "Enabled" if latest_route.get("start_project_mode") else "Disabled",
                    "hint": "Incubator is most relevant during project flows",
                },
            ])
        else:
            metrics.extend([
                {
                    "label": "Assistant Deliveries",
                    "value": str(sum(1 for message in messages if message.get("sender") == "agent")),
                    "hint": "Persisted assistant turns in this session",
                },
                {
                    "label": "Current Owner",
                    "value": latest_assistant.get("agent_name") or "Awaiting response",
                    "hint": "Latest assistant assigned to execution",
                },
                {
                    "label": "Latest Status",
                    "value": latest_assistant.get("status") or "Idle",
                    "hint": "Most recent assistant delivery state",
                },
            ])

        return metrics

    def _build_room_detail_highlights(
        self,
        *,
        room_id: str,
        latest_route: dict[str, Any],
        working_context: dict[str, Any],
        room_events: list[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> list[str]:
        latest_assistant = self._find_latest(messages, sender="agent")
        failure_message = next(
            (message.get("error_message") for message in reversed(messages) if message.get("status") == "failed"),
            None,
        )
        latest_event = room_events[-1] if room_events else None

        if room_id == "strategy":
            return [
                latest_route.get("reason") or "Route reason has not been captured yet.",
                f"Task type: {latest_route.get('inferred_task_type') or 'general'}",
                f"Project mode: {'enabled' if latest_route.get('start_project_mode') else 'disabled'}",
            ]
        if room_id == "boss":
            return [
                failure_message or "No failed turn is currently awaiting intervention.",
                f"Latest oversight event: {latest_event.get('event_type') if latest_event else 'none'}",
                "Boss office intensifies only when retries or risk conditions appear.",
            ]
        if room_id == "voting":
            return [
                "Voting events are only persisted when governance is triggered.",
                f"Executive router active: {'yes' if latest_route.get('source') == 'executive_router' else 'no'}",
                f"Latest chamber event: {latest_event.get('event_type') if latest_event else 'none'}",
            ]
        if room_id == "collaboration":
            return [
                "Collaboration events distinguish coordinated work from direct single-agent responses.",
                f"Latest collaboration event: {latest_event.get('event_type') if latest_event else 'none'}",
                f"Current lead: {latest_assistant.get('agent_name') or 'awaiting assignment'}",
            ]
        if room_id == "memory":
            return [
                f"Working memory retains {len(working_context.get('recent_turns', []))} recent turns.",
                f"Stored route transitions: {len(working_context.get('route_history', []))}",
                f"Latest memory event: {latest_event.get('event_type') if latest_event else 'none'}",
            ]
        if room_id == "incubator":
            return [
                "Incubator activates when project mode needs additional specialist coverage.",
                f"Latest inferred specialist: {latest_route.get('inferred_agent_type') or 'undetermined'}",
                f"Incubator event count: {len(room_events)}",
            ]
        return [
            f"Latest execution owner: {latest_assistant.get('agent_name') or 'awaiting assignment'}",
            f"Latest event: {latest_event.get('event_type') if latest_event else 'none'}",
            "Execution room reflects the final delivery path back to the front desk.",
        ]

    def _build_room_related_messages(
        self,
        *,
        room_id: str,
        room_events: list[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        message_by_id = {str(message["id"]): message for message in messages}
        related_ids = [
            str(event["related_message_id"])
            for event in room_events
            if event.get("related_message_id") and str(event["related_message_id"]) in message_by_id
        ]
        ordered_related_ids = list(dict.fromkeys(related_ids))
        selected_messages = [message_by_id[message_id] for message_id in ordered_related_ids]

        if not selected_messages:
            if room_id == "boss":
                selected_messages = [message for message in messages if message.get("status") == "failed"][-3:]
            elif room_id == "execution":
                selected_messages = [message for message in messages if message.get("sender") == "agent"][-3:]
            elif room_id == "memory":
                selected_messages = messages[-4:]
            else:
                selected_messages = messages[-3:]

        selected_messages = selected_messages[-4:]
        return [
            {
                "id": str(message["id"]),
                "role": message.get("role", ""),
                "sender": message.get("sender", ""),
                "content": self._truncate(message.get("content", "") or "", 180),
                "status": message.get("status", ""),
                "agent_name": message.get("agent_name"),
                "created_at": message.get("created_at") or self._now(),
            }
            for message in selected_messages
        ]

    def _extract_participants(
        self,
        *,
        messages: list[dict[str, Any]],
        working_context: dict[str, Any],
        room_events: list[dict[str, Any]],
    ) -> list[str]:
        participants: list[str] = []
        seen: set[str] = set()
        message_by_id = {str(message["id"]): message for message in messages}

        def add_participant(value: Optional[str]) -> None:
            if not value:
                return
            normalized = value.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                participants.append(normalized)

        add_participant(working_context.get("selected_agent_name"))

        for event in room_events:
            payload = event.get("payload") or {}
            if isinstance(payload, dict):
                add_participant(payload.get("agent_name"))
            related_message_id = event.get("related_message_id")
            if related_message_id:
                message = message_by_id.get(str(related_message_id))
                if message:
                    add_participant(message.get("agent_name"))

        for message in messages:
            if message.get("sender") == "agent":
                add_participant(message.get("agent_name"))

        return participants[:6]

    def _build_preference_signals(self, working_context: dict[str, Any]) -> list[str]:
        signals: list[str] = []
        if working_context.get("selected_agent_name"):
            signals.append(f"Preferred specialist in context: {working_context['selected_agent_name']}")
        if working_context.get("mode"):
            signals.append(f"Latest execution mode: {self._format_mode(working_context.get('mode'))}")
        if working_context.get("inferred_task_type"):
            signals.append(f"Inferred task type: {working_context['inferred_task_type']}")
        if working_context.get("route_source"):
            signals.append(f"Route source retained: {self._format_route_source(working_context['route_source'])}")
        if working_context.get("start_project_mode"):
            signals.append("Project mode was enabled in the stored session context.")
        return signals

    @staticmethod
    def _latest_event_type(events: list[dict[str, Any]]) -> Optional[str]:
        if not events:
            return None
        return events[-1].get("event_type")

    @staticmethod
    def _resolve_phase_agent_name(
        phase_events: list[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> Optional[str]:
        message_by_id = {str(message["id"]): message for message in messages}
        for event in reversed(phase_events):
            payload = event.get("payload") or {}
            if isinstance(payload, dict) and payload.get("agent_name"):
                return str(payload["agent_name"])
            related_message_id = event.get("related_message_id")
            if related_message_id:
                message = message_by_id.get(str(related_message_id))
                if message and message.get("agent_name"):
                    return str(message["agent_name"])
        return None

    @staticmethod
    def _latest_room_events(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for event in events:
            room_id = event.get("room_id")
            if room_id:
                latest[room_id] = event
        return latest

    @staticmethod
    def _room_status(
        room_id: str,
        latest_room_events: dict[str, dict[str, Any]],
        *,
        default: str,
        active_fallback: bool,
    ) -> str:
        event = latest_room_events.get(room_id)
        if event:
            if event.get("severity") == "critical":
                return "alert"
            if event.get("severity") == "warning":
                return "watching"
            return "active"
        return "active" if active_fallback else default

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
