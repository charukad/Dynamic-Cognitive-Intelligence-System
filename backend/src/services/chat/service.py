"""Chat application service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Iterable, List, Optional
from uuid import UUID, uuid4

from src.core import get_logger
from src.domain.models import (
    Agent,
    AgentStatus,
    AgentType,
    ChatMessageRole,
    ChatMessageSender,
    ChatMessageStatus,
)
from src.infrastructure.llm.vllm_client import vllm_client
from src.infrastructure.repositories import agent_repository
from src.infrastructure.repositories.chat_repository import chat_repository
from src.services.memory import (
    embedding_pipeline,
    episodic_memory_service,
    working_memory_service,
)
from src.services.agents.data_analyst_agent import create_data_analyst_agent
from src.services.agents.designer_agent import create_designer_agent
from src.services.agents.financial_agent import create_financial_advisor_agent
from src.services.agents.specialized_agents import ExecutiveAgent
from src.services.agents.translator_agent import create_translator_agent
from src.services.orchestrator.thompson_router import thompson_router

logger = get_logger(__name__)


@dataclass
class RouteDecision:
    """Resolved routing decision for a chat turn."""

    agent: Agent
    route_source: str
    route_reason: str
    requested_agent_id: Optional[str]
    inferred_task_type: str
    inferred_agent_type: Optional[str]
    mode: str
    start_project_mode: bool
    effective_system_prompt: str


@dataclass
class MemoryContext:
    """Resolved memory context for a chat turn."""

    working_context: dict
    recent_session_memories: list[str]
    retrieved_memories: list[str]
    rag_context: str

    @property
    def has_context(self) -> bool:
        return bool(
            self.working_context
            or self.recent_session_memories
            or self.retrieved_memories
            or self.rag_context
        )


class ChatService:
    """Service for chat completions, streaming, and persistence."""

    def __init__(self):
        self.client = vllm_client
        self._builtin_agents = {
            "data-analyst": create_data_analyst_agent().agent,
            "data_analyst": create_data_analyst_agent("data_analyst").agent,
            "designer": create_designer_agent().agent,
            "translator": create_translator_agent().agent,
            "financial": create_financial_advisor_agent("financial").agent,
            "financial_advisor": create_financial_advisor_agent().agent,
            "executive": Agent(
                id="executive",
                name="Executive Orchestrator",
                agent_type=AgentType.EXECUTIVE,
                status=AgentStatus.IDLE,
                capabilities=["routing", "planning", "prioritization", "coordination"],
                system_prompt=(
                    "You are the Executive Orchestrator for DCIS. "
                    "Route work to the best specialist, maintain clarity, and synthesize outcomes."
                ),
                temperature=0.4,
            ),
            "logician": Agent(
                id="logician",
                name="Logician",
                agent_type=AgentType.LOGICIAN,
                status=AgentStatus.IDLE,
                capabilities=["reasoning", "analysis", "decomposition"],
                system_prompt=(
                    "You are a rigorous reasoning specialist. "
                    "Break down problems systematically and surface assumptions."
                ),
                temperature=0.1,
            ),
            "scholar": Agent(
                id="scholar",
                name="Scholar",
                agent_type=AgentType.SCHOLAR,
                status=AgentStatus.IDLE,
                capabilities=["research", "fact_checking", "synthesis"],
                system_prompt=(
                    "You are a research specialist. "
                    "Provide careful, accurate, context-rich answers."
                ),
                temperature=0.3,
            ),
            "coder": Agent(
                id="coder",
                name="Coder",
                agent_type=AgentType.CODER,
                status=AgentStatus.IDLE,
                capabilities=["coding", "debugging", "implementation"],
                system_prompt=(
                    "You are a software implementation specialist. "
                    "Provide correct, maintainable, well-explained technical solutions."
                ),
                temperature=0.2,
            ),
            "creative": Agent(
                id="creative",
                name="Creative Strategist",
                agent_type=AgentType.CREATIVE,
                status=AgentStatus.IDLE,
                capabilities=["ideation", "concept_generation", "creative_strategy"],
                system_prompt=(
                    "You are a creative strategist. "
                    "Generate novel, useful options while staying aligned to the user's goals."
                ),
                temperature=0.8,
            ),
        }

    async def resolve_agent(self, agent_id: Optional[str]) -> Agent:
        """Resolve an agent from the database or built-in specialized registry."""
        if not agent_id:
            raise ValueError("No agent selected for chat session")

        if agent_id in self._builtin_agents:
            return self._builtin_agents[agent_id]

        try:
            agent_uuid = UUID(agent_id)
        except ValueError:
            raise ValueError(f"Unknown agent ID: {agent_id}") from None

        agent = await agent_repository.get_by_id(agent_uuid)
        if not agent:
            raise ValueError(f"Agent with ID '{agent_id}' not found")
        return agent

    async def _get_routable_agents(self) -> list[Agent]:
        """Load routable agents from the repository and built-in registry."""
        candidates: dict[str, Agent] = {}

        try:
            for agent in await agent_repository.get_available_agents():
                candidates[str(agent.id)] = agent
        except Exception as exc:
            logger.warning("Failed to load repository agents for chat routing: %s", exc)

        for agent in self._builtin_agents.values():
            candidates.setdefault(str(agent.id), agent)

        return list(candidates.values())

    @staticmethod
    def _normalize_mode(metadata: Optional[dict]) -> str:
        raw_mode = str((metadata or {}).get("mode", "balanced")).strip().lower()
        return raw_mode if raw_mode in {"balanced", "high_accuracy", "budget"} else "balanced"

    @staticmethod
    def _infer_task_type(content: str, metadata: Optional[dict]) -> str:
        explicit_type = str((metadata or {}).get("task_type", "")).strip().lower()
        if explicit_type:
            return explicit_type

        text = content.lower()
        if any(word in text for word in ["code", "bug", "debug", "function", "api", "typescript", "python"]):
            return "coding"
        if any(word in text for word in ["design", "ui", "ux", "layout", "visual", "color", "brand"]):
            return "creative"
        if any(word in text for word in ["translate", "translation", "localize", "language"]):
            return "translation"
        if any(word in text for word in ["finance", "financial", "portfolio", "market", "investment", "revenue"]):
            return "financial"
        if any(word in text for word in ["data", "dataset", "sql", "statistics", "analyze csv", "anomaly"]):
            return "analysis"
        if any(word in text for word in ["research", "compare", "explain", "find", "summarize"]):
            return "research"
        return "general"

    @staticmethod
    def _infer_agent_type(task_type: str, content: str) -> Optional[AgentType]:
        text = content.lower()
        if task_type == "coding":
            return AgentType.CODER
        if task_type == "creative":
            return AgentType.DESIGNER if any(word in text for word in ["design", "ui", "ux"]) else AgentType.CREATIVE
        if task_type == "translation":
            return AgentType.TRANSLATOR
        if task_type == "financial":
            return AgentType.FINANCIAL
        if task_type == "analysis":
            return AgentType.DATA_ANALYST
        if task_type == "research":
            return AgentType.SCHOLAR
        if any(word in text for word in ["plan", "coordinate", "orchestrate"]):
            return AgentType.EXECUTIVE
        if any(word in text for word in ["reason", "logic", "tradeoff"]):
            return AgentType.LOGICIAN
        return None

    @staticmethod
    def _matches_agent_type(agent: Agent, target_type: Optional[AgentType]) -> bool:
        if not target_type:
            return True
        return agent.agent_type == target_type

    async def _llm_route_agent(
        self,
        *,
        content: str,
        candidates: list[Agent],
        inferred_agent_type: Optional[AgentType],
    ) -> Optional[tuple[Agent, str]]:
        """Use the executive agent to refine routing when the task is ambiguous or large."""
        executive = self._builtin_agents.get("executive")
        if not executive or not candidates:
            return None

        candidate_lines = "\n".join(
            f"- {agent.id}: {agent.name} ({agent.agent_type.value})"
            for agent in candidates
        )

        try:
            result = await ExecutiveAgent(executive).process(
                {
                    "routing_request": True,
                    "situation": (
                        f"User message: {content}\n"
                        f"Preferred type hint: {inferred_agent_type.value if inferred_agent_type else 'none'}\n"
                        f"Available candidates:\n{candidate_lines}"
                    ),
                }
            )
        except Exception as exc:
            logger.warning("Executive LLM routing failed: %s", exc)
            return None

        target_id = str(result.get("target", "")).strip()
        for agent in candidates:
            if str(agent.id) == target_id:
                return agent, result.get("reasoning", "Executive orchestrator selected the best fit")
        return None

    def _resolve_system_prompt(
        self,
        *,
        agent: Agent,
        route: RouteDecision | None = None,
        memory_context: MemoryContext | None = None,
    ) -> str:
        """Build the effective system prompt for a routed conversation turn."""
        mode = route.mode if route else "balanced"
        directives = [
            agent.system_prompt.strip(),
            "You are responding inside DCIS Neural Link.",
            "Provide a direct, high-signal answer with professional tone.",
        ]

        if route and route.route_source == "auto":
            directives.append(
                f"You were auto-routed to this request because: {route.route_reason}"
            )

        if mode == "high_accuracy":
            directives.extend(
                [
                    "Optimize for correctness over speed.",
                    "State uncertainty explicitly when evidence is incomplete.",
                    "Prefer careful stepwise reasoning and verifiable claims.",
                ]
            )
        elif mode == "budget":
            directives.extend(
                [
                    "Optimize for cost-efficiency and brevity.",
                    "Keep the answer concise while still useful.",
                    "Avoid unnecessary elaboration unless the user explicitly asks for detail.",
                ]
            )
        else:
            directives.append(
                "Balance speed, clarity, and correctness."
            )

        if route and route.start_project_mode:
            directives.append(
                "Treat this as project-oriented work: surface plan, risks, and recommended next steps."
            )

        if memory_context and memory_context.has_context:
            directives.append(self._format_memory_context(memory_context))

        return "\n\n".join(part for part in directives if part)

    @staticmethod
    def _safe_agent_uuid(agent: Agent) -> Optional[UUID]:
        """Return a UUID agent identifier when available."""
        if isinstance(agent.id, UUID):
            return agent.id
        try:
            return UUID(str(agent.id))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _truncate(value: str, limit: int = 240) -> str:
        compact = " ".join(value.strip().split())
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3] + "..."

    def _format_memory_context(self, memory_context: MemoryContext) -> str:
        """Render supplemental memory context for the system prompt."""
        sections: list[str] = [
            "Supplemental context is provided below. Use it when relevant, but prioritize the current user request if there is any conflict."
        ]

        if memory_context.working_context:
            sections.append(
                "Working context:\n"
                + "\n".join(
                    f"- {key}: {self._truncate(str(value), 180)}"
                    for key, value in memory_context.working_context.items()
                    if value not in (None, "", [], {})
                )
            )

        if memory_context.recent_session_memories:
            sections.append(
                "Recent session memories:\n"
                + "\n".join(f"- {item}" for item in memory_context.recent_session_memories)
            )

        if memory_context.retrieved_memories:
            sections.append(
                "Relevant recalled memories:\n"
                + "\n".join(f"- {item}" for item in memory_context.retrieved_memories)
            )

        if memory_context.rag_context:
            sections.append(f"RAG context:\n{memory_context.rag_context}")

        return "\n\n".join(sections)

    async def _load_memory_context(self, session_id: str, content: str) -> MemoryContext:
        """Load working memory, episodic recalls, and retrieval context for a chat turn."""
        working_context: dict = {}
        recent_session_memories: list[str] = []
        retrieved_memories: list[str] = []
        rag_context = ""

        try:
            working_context = await working_memory_service.get_context(session_id) or {}
        except Exception as exc:
            logger.warning("Failed to load working memory for session %s: %s", session_id, exc)

        try:
            session_memories = await episodic_memory_service.get_session_memories(session_id)
            ordered = sorted(session_memories, key=lambda memory: memory.created_at, reverse=True)
            recent_session_memories = [
                self._truncate(memory.content, 220)
                for memory in ordered[:4]
            ]
        except Exception as exc:
            logger.warning("Failed to load session episodic memories for %s: %s", session_id, exc)

        try:
            memories = await episodic_memory_service.retrieve_memories(query=content, limit=3)
            seen = set()
            for memory in memories:
                text = self._truncate(memory.content, 220)
                if text not in seen:
                    seen.add(text)
                    retrieved_memories.append(text)
        except Exception as exc:
            logger.warning("Failed to retrieve relevant episodic memories: %s", exc)

        try:
            rag_context = await embedding_pipeline.build_rag_context(
                collection_name="knowledge_base",
                query=content,
                max_chunks=3,
            )
            rag_context = self._truncate(rag_context, 900)
        except Exception as exc:
            logger.warning("Failed to build RAG context for chat: %s", exc)

        return MemoryContext(
            working_context=working_context,
            recent_session_memories=recent_session_memories,
            retrieved_memories=retrieved_memories,
            rag_context=rag_context,
        )

    async def _update_memory_state(
        self,
        *,
        session_id: str,
        agent: Agent,
        route: RouteDecision,
        user_content: str,
        assistant_content: str,
    ) -> None:
        """Persist chat turn context into working memory and episodic memory."""
        try:
            current_context = await working_memory_service.get_context(session_id) or {}
        except Exception as exc:
            logger.warning("Failed to read existing working context for %s: %s", session_id, exc)
            current_context = {}

        recent_turns = list(current_context.get("recent_turns", []))
        recent_turns.append(
            {
                "user": self._truncate(user_content, 220),
                "assistant": self._truncate(assistant_content, 220),
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "mode": route.mode,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        recent_turns = recent_turns[-5:]

        updated_context = {
            **current_context,
            "selected_agent_id": str(agent.id),
            "selected_agent_name": agent.name,
            "route_source": route.route_source,
            "route_reason": route.route_reason,
            "inferred_task_type": route.inferred_task_type,
            "mode": route.mode,
            "start_project_mode": route.start_project_mode,
            "last_user_message": self._truncate(user_content, 220),
            "last_assistant_message": self._truncate(assistant_content, 220),
            "recent_turns": recent_turns,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await working_memory_service.store_context(session_id, updated_context)
        except Exception as exc:
            logger.warning("Failed to persist working context for %s: %s", session_id, exc)

        agent_uuid = self._safe_agent_uuid(agent)

        try:
            await episodic_memory_service.store_memory(
                content=f"User asked: {self._truncate(user_content, 400)}",
                agent_id=agent_uuid,
                session_id=session_id,
                importance_score=0.55,
                tags=["chat", "user_turn", route.inferred_task_type],
            )
        except Exception as exc:
            logger.warning("Failed to persist user episodic memory: %s", exc)

        try:
            await episodic_memory_service.store_memory(
                content=(
                    f"Agent {agent.name} responded via {route.route_source}: "
                    f"{self._truncate(assistant_content, 500)}"
                ),
                agent_id=agent_uuid,
                session_id=session_id,
                importance_score=0.7,
                tags=["chat", "assistant_turn", route.inferred_task_type],
            )
        except Exception as exc:
            logger.warning("Failed to persist assistant episodic memory: %s", exc)

        try:
            await embedding_pipeline.store_document(
                collection_name="knowledge_base",
                document=(
                    f"Session {session_id}\n"
                    f"User: {user_content}\n"
                    f"Assistant ({agent.name}): {assistant_content}"
                ),
                metadata={
                    "type": "chat_turn",
                    "session_id": session_id,
                    "agent_id": str(agent.id),
                    "route_source": route.route_source,
                    "task_type": route.inferred_task_type,
                },
                document_id=f"chat_turn:{session_id}:{uuid4()}",
            )
        except Exception as exc:
            logger.warning("Failed to store chat turn in knowledge base: %s", exc)

    async def route_message(
        self,
        *,
        content: str,
        requested_agent_id: Optional[str],
        session_agent_id: Optional[str],
        metadata: Optional[dict],
    ) -> RouteDecision:
        """Resolve the best agent and prompt for the next chat turn."""
        mode = self._normalize_mode(metadata)
        start_project_mode = bool((metadata or {}).get("start_project_mode"))
        task_type = self._infer_task_type(content, metadata)
        inferred_agent_type = self._infer_agent_type(task_type, content)

        if requested_agent_id:
            agent = await self.resolve_agent(requested_agent_id)
            route = RouteDecision(
                agent=agent,
                route_source="explicit",
                route_reason="User explicitly selected the target agent",
                requested_agent_id=requested_agent_id,
                inferred_task_type=task_type,
                inferred_agent_type=inferred_agent_type.value if inferred_agent_type else None,
                mode=mode,
                start_project_mode=start_project_mode,
                effective_system_prompt="",
            )
            route.effective_system_prompt = self._resolve_system_prompt(agent=agent, route=route)
            return route

        if session_agent_id:
            agent = await self.resolve_agent(session_agent_id)
            route = RouteDecision(
                agent=agent,
                route_source="session",
                route_reason="Continuing the session with the existing selected agent",
                requested_agent_id=None,
                inferred_task_type=task_type,
                inferred_agent_type=inferred_agent_type.value if inferred_agent_type else None,
                mode=mode,
                start_project_mode=start_project_mode,
                effective_system_prompt="",
            )
            route.effective_system_prompt = self._resolve_system_prompt(agent=agent, route=route)
            return route

        candidates = await self._get_routable_agents()
        filtered_candidates = [
            agent for agent in candidates if self._matches_agent_type(agent, inferred_agent_type)
        ] or candidates

        if start_project_mode or inferred_agent_type is None:
            llm_route = await self._llm_route_agent(
                content=content,
                candidates=filtered_candidates,
                inferred_agent_type=inferred_agent_type,
            )
            if llm_route:
                agent, reason = llm_route
                route = RouteDecision(
                    agent=agent,
                    route_source="executive_router",
                    route_reason=reason,
                    requested_agent_id=None,
                    inferred_task_type=task_type,
                    inferred_agent_type=inferred_agent_type.value if inferred_agent_type else None,
                    mode=mode,
                    start_project_mode=start_project_mode,
                    effective_system_prompt="",
                )
                route.effective_system_prompt = self._resolve_system_prompt(agent=agent, route=route)
                return route

        if not filtered_candidates:
            raise ValueError("No routable agents available")

        try:
            selected_agent = thompson_router.select_agent(
                filtered_candidates,
                agent_type_hint=inferred_agent_type.value if inferred_agent_type else None,
            )
            reason = (
                f"Auto-routed using Thompson sampling"
                + (f" with preferred type {inferred_agent_type.value}" if inferred_agent_type else "")
            )
        except Exception:
            selected_agent = filtered_candidates[0]
            reason = "Auto-routed using deterministic fallback"

        route = RouteDecision(
            agent=selected_agent,
            route_source="auto",
            route_reason=reason,
            requested_agent_id=None,
            inferred_task_type=task_type,
            inferred_agent_type=inferred_agent_type.value if inferred_agent_type else None,
            mode=mode,
            start_project_mode=start_project_mode,
            effective_system_prompt="",
        )
        route.effective_system_prompt = self._resolve_system_prompt(agent=selected_agent, route=route)
        return route

    @staticmethod
    def _history_to_prompt_messages(history: Iterable[dict]) -> List[dict]:
        prompt_messages: List[dict] = []
        for message in history:
            role = message.get("role") or (
                ChatMessageRole.ASSISTANT.value
                if message.get("sender") == ChatMessageSender.AGENT.value
                else ChatMessageRole.USER.value
            )
            prompt_messages.append(
                {
                    "role": role,
                    "content": message.get("content", ""),
                }
            )
        return prompt_messages

    def _build_prompt(self, messages: List[dict], system_prompt: str) -> str:
        prompt = f"System: {system_prompt}\n\n"
        for msg in messages:
            role = msg.get("role", ChatMessageRole.USER.value).capitalize()
            content = msg.get("content", "")
            prompt += f"{role}: {content}\n"
        prompt += "Assistant: "
        return prompt

    async def chat_completion(
        self,
        messages: List[dict],
        system_prompt: str = "You are a helpful AI assistant in the DCIS system.",
        temperature: float = 0.7,
    ) -> str:
        """Generate a complete assistant response from structured history."""
        prompt = self._build_prompt(messages, system_prompt)
        return await self.client.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=1000,
        )

    async def chat_stream(
        self,
        messages: List[dict],
        system_prompt: str = "You are a helpful AI assistant.",
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream assistant output from structured history."""
        prompt = self._build_prompt(messages, system_prompt)
        async for chunk in self.client.generate_stream(
            prompt=prompt,
            temperature=temperature,
            max_tokens=1000,
        ):
            yield chunk

    async def send_message(
        self,
        *,
        session_id: str,
        content: str,
        agent_id: Optional[str] = None,
        user_message_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Persist a user message, generate a response, and persist the assistant turn."""
        session = await chat_repository.get_session(session_id)
        if not session:
            raise ValueError(f"Chat session not found: {session_id}")

        route = await self.route_message(
            content=content,
            requested_agent_id=agent_id,
            session_agent_id=session.selected_agent_id,
            metadata=metadata,
        )
        agent = route.agent
        memory_context = await self._load_memory_context(session_id, content)
        effective_system_prompt = self._resolve_system_prompt(
            agent=agent,
            route=route,
            memory_context=memory_context,
        )

        user_message = await chat_repository.create_message(
            session_id=session_id,
            message_id=user_message_id,
            role=ChatMessageRole.USER,
            sender=ChatMessageSender.USER,
            content=content,
            status=ChatMessageStatus.COMPLETED,
            agent_id=str(agent.id),
            agent_name=agent.name,
            metadata={**(metadata or {}), "routing": {
                "source": route.route_source,
                "reason": route.route_reason,
                "inferred_task_type": route.inferred_task_type,
                "inferred_agent_type": route.inferred_agent_type,
                "mode": route.mode,
                "start_project_mode": route.start_project_mode,
            }},
        )

        history_rows = await chat_repository.list_messages(session_id=session_id, limit=50)
        prompt_messages = self._history_to_prompt_messages(history_rows)
        try:
            assistant_content = await self.chat_completion(
                messages=prompt_messages,
                system_prompt=effective_system_prompt,
                temperature=agent.temperature,
            )
        except Exception:
            try:
                thompson_router.update_performance(agent.id, success=False)
            except Exception:
                logger.debug("Unable to update router performance for %s", agent.id)
            raise

        assistant_message = await chat_repository.create_message(
            session_id=session_id,
            role=ChatMessageRole.ASSISTANT,
            sender=ChatMessageSender.AGENT,
            content=assistant_content,
            status=ChatMessageStatus.COMPLETED,
            agent_id=str(agent.id),
            agent_name=agent.name,
            metadata={
                "routing": {
                    "source": route.route_source,
                    "reason": route.route_reason,
                    "inferred_task_type": route.inferred_task_type,
                    "inferred_agent_type": route.inferred_agent_type,
                    "mode": route.mode,
                    "start_project_mode": route.start_project_mode,
                }
            },
        )

        try:
            thompson_router.update_performance(agent.id, success=True)
        except Exception:
            logger.debug("Unable to update router performance for %s", agent.id)

        await self._update_memory_state(
            session_id=session_id,
            agent=agent,
            route=route,
            user_content=content,
            assistant_content=assistant_content,
        )

        session_summary = await chat_repository.get_session_summary(session_id)
        if not session_summary:
            raise RuntimeError("Chat session persisted but summary could not be loaded")

        assistant_row = await chat_repository.get_message(str(assistant_message.id))
        user_row = await chat_repository.get_message(str(user_message.id))
        if not assistant_row or not user_row:
            raise RuntimeError("Persisted chat messages could not be reloaded")

        return {
            "session": session_summary,
            "user_message": user_row,
            "assistant_message": assistant_row,
        }

    async def stream_message(
        self,
        *,
        session_id: str,
        content: str,
        agent_id: Optional[str] = None,
        user_message_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AsyncIterator[dict]:
        """Persist a user turn and stream the assistant response as canonical events."""
        session = await chat_repository.get_session(session_id)
        if not session:
            raise ValueError(f"Chat session not found: {session_id}")

        route = await self.route_message(
            content=content,
            requested_agent_id=agent_id,
            session_agent_id=session.selected_agent_id,
            metadata=metadata,
        )
        agent = route.agent
        memory_context = await self._load_memory_context(session_id, content)
        effective_system_prompt = self._resolve_system_prompt(
            agent=agent,
            route=route,
            memory_context=memory_context,
        )
        now = datetime.now(timezone.utc)

        user_message = await chat_repository.create_message(
            session_id=session_id,
            message_id=user_message_id,
            role=ChatMessageRole.USER,
            sender=ChatMessageSender.USER,
            content=content,
            status=ChatMessageStatus.COMPLETED,
            agent_id=str(agent.id),
            agent_name=agent.name,
            metadata={**(metadata or {}), "routing": {
                "source": route.route_source,
                "reason": route.route_reason,
                "inferred_task_type": route.inferred_task_type,
                "inferred_agent_type": route.inferred_agent_type,
                "mode": route.mode,
                "start_project_mode": route.start_project_mode,
            }},
        )

        assistant_message = await chat_repository.create_message(
            session_id=session_id,
            message_id=str(uuid4()),
            role=ChatMessageRole.ASSISTANT,
            sender=ChatMessageSender.AGENT,
            content="",
            status=ChatMessageStatus.STREAMING,
            agent_id=str(agent.id),
            agent_name=agent.name,
            metadata={
                "routing": {
                    "source": route.route_source,
                    "reason": route.route_reason,
                    "inferred_task_type": route.inferred_task_type,
                    "inferred_agent_type": route.inferred_agent_type,
                    "mode": route.mode,
                    "start_project_mode": route.start_project_mode,
                }
            },
        )

        user_row = await chat_repository.get_message(str(user_message.id))
        assistant_row = await chat_repository.get_message(str(assistant_message.id))
        if not user_row or not assistant_row:
            raise RuntimeError("Persisted streaming messages could not be reloaded")

        yield {
            "type": "message.created",
            "session_id": session_id,
            "message_id": str(user_message.id),
            "sequence_number": user_message.sequence_number,
            "timestamp": now.isoformat(),
            "payload": {"message": user_row},
        }
        yield {
            "type": "response.started",
            "session_id": session_id,
            "message_id": str(assistant_message.id),
            "sequence_number": assistant_message.sequence_number,
            "timestamp": now.isoformat(),
            "payload": {"message": assistant_row},
        }

        history_rows = await chat_repository.list_messages(session_id=session_id, limit=50)
        prompt_messages = self._history_to_prompt_messages(history_rows[:-1])
        prompt_messages.append({"role": ChatMessageRole.USER.value, "content": content})

        assembled_content = ""
        try:
            async for chunk in self.chat_stream(
                messages=prompt_messages,
                system_prompt=effective_system_prompt,
                temperature=agent.temperature,
            ):
                assembled_content += chunk
                yield {
                    "type": "response.delta",
                    "session_id": session_id,
                    "message_id": str(assistant_message.id),
                    "sequence_number": assistant_message.sequence_number,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "agent_id": str(agent.id),
                        "agent_name": agent.name,
                        "chunk": chunk,
                    },
                }

            await chat_repository.update_message(
                str(assistant_message.id),
                content=assembled_content,
                status=ChatMessageStatus.COMPLETED,
            )
            final_assistant = await chat_repository.get_message(str(assistant_message.id))
            session_summary = await chat_repository.get_session_summary(session_id)

            yield {
                "type": "response.completed",
                "session_id": session_id,
                "message_id": str(assistant_message.id),
                "sequence_number": assistant_message.sequence_number,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "message": final_assistant,
                    "session": session_summary,
                    "routing": {
                        "source": route.route_source,
                        "reason": route.route_reason,
                        "inferred_task_type": route.inferred_task_type,
                        "inferred_agent_type": route.inferred_agent_type,
                        "mode": route.mode,
                        "start_project_mode": route.start_project_mode,
                    },
                },
            }
            try:
                thompson_router.update_performance(agent.id, success=True)
            except Exception:
                logger.debug("Unable to update router performance for %s", agent.id)
            await self._update_memory_state(
                session_id=session_id,
                agent=agent,
                route=route,
                user_content=content,
                assistant_content=assembled_content,
            )
        except Exception as exc:
            await chat_repository.update_message(
                str(assistant_message.id),
                content=assembled_content,
                status=ChatMessageStatus.FAILED,
                error_message=str(exc),
            )
            try:
                thompson_router.update_performance(agent.id, success=False)
            except Exception:
                logger.debug("Unable to update router performance for %s", agent.id)
            yield {
                "type": "response.failed",
                "session_id": session_id,
                "message_id": str(assistant_message.id),
                "sequence_number": assistant_message.sequence_number,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "error": str(exc),
                },
            }
            raise


chat_service = ChatService()
