"""Base agent class for all specialized agents."""

import time
from typing import Any, Optional

from src.core import get_logger
from src.domain.models import Agent, AgentType, Task
from src.infrastructure.llm import vllm_client

logger = get_logger(__name__)


class BaseAgent:
    """
    Base class for all specialized agents.

    Provides common functionality for task execution, prompt building,
    and LLM interaction. Also maintains backward compatibility with
    legacy unit tests that instantiate BaseAgent directly.
    """

    def __init__(
        self,
        agent: Optional[Agent] = None,
        llm_client: Optional[Any] = None,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        """
        Initialize base agent.

        Args:
            agent: Agent domain model
            llm_client: Optional injected LLM client (for tests/overrides)
            agent_id: Legacy constructor path
            agent_type: Legacy constructor path
            system_prompt: Optional override prompt for legacy constructor path
            temperature: Optional override temperature for legacy constructor path
        """
        if agent is None:
            resolved_type = (agent_type or self.__class__.__name__.replace("Agent", "")).lower()
            resolved_enum = self._resolve_agent_type(resolved_type)
            resolved_temperature = (
                temperature
                if temperature is not None
                else self._default_temperature(resolved_type)
            )
            agent = Agent(
                id=agent_id or f"{resolved_type}_agent",
                name=f"{resolved_type.title()} Agent",
                agent_type=resolved_enum,
                system_prompt=system_prompt or f"You are a {resolved_type} specialist.",
                temperature=resolved_temperature,
            )

        self.agent = agent
        self.agent_model = agent  # Legacy alias expected by tests
        self.llm_client = llm_client or vllm_client
        self.execution_count = 0
        self.agent_id = str(agent.id)  # Legacy alias expected by tests
        self.agent_type = getattr(agent.agent_type, "value", str(agent.agent_type))
        self.temperature = agent.temperature
        self.logger = get_logger(f"{__name__}.{agent.name}")

    @staticmethod
    def _resolve_agent_type(agent_type: str) -> AgentType:
        """Resolve string values to AgentType with a safe fallback."""
        for value in AgentType:
            if value.value == agent_type:
                return value
        return AgentType.CUSTOM

    @staticmethod
    def _default_temperature(agent_type: str) -> float:
        """Provide sensible default temperatures by agent type."""
        defaults = {
            "coder": 0.2,
            "logician": 0.1,
            "critic": 0.2,
            "scholar": 0.3,
            "creative": 0.8,
            "executive": 0.4,
        }
        return defaults.get(agent_type, 0.5)

    async def process(self, task_input: Any) -> dict:
        """
        Default processing for generic agents.

        Specialized agents can override this method.
        """
        prompt = self._build_prompt(task_input)
        response = await self.generate_response(prompt)
        return {
            "agent": self.agent.name,
            "response": response,
        }

    async def execute(
        self,
        task_input: dict | Task,
        context: Optional[dict] = None,
    ) -> dict:
        """
        Execute task with performance tracking and error handling.

        Args:
            task_input: Task model or dict payload
            context: Optional execution context

        Returns:
            Task output/result
        """
        start_time = time.time()
        success = False

        try:
            self.agent.mark_busy()
            self.logger.info("Agent %s starting task execution", self.agent.name)

            normalized_input = self._normalize_task_input(task_input, context)
            result = await self.process(normalized_input)

            self.execution_count += 1
            success = True
            self.logger.info("Agent %s completed task successfully", self.agent.name)
            return result

        except Exception as e:
            self.agent.mark_error()
            self.logger.error("Agent %s failed: %s", self.agent.name, str(e))
            return {"error": str(e)}

        finally:
            response_time = time.time() - start_time
            self.agent.update_performance(success, response_time)

            if success:
                self.agent.mark_idle()

            self.logger.info(
                "Agent %s performance: success_rate=%.2f%%, avg_response_time=%.2fs",
                self.agent.name,
                self.agent.success_rate * 100.0,
                self.agent.avg_response_time,
            )

    def _normalize_task_input(
        self,
        task_input: dict | Task,
        context: Optional[dict] = None,
    ) -> dict:
        """Normalize Task/domain inputs into a dict payload."""
        if isinstance(task_input, Task):
            payload = {
                "task_id": str(task_input.id),
                "title": task_input.title,
                "description": task_input.description,
                "task_type": task_input.task_type,
                "problem": task_input.description,
                "query": task_input.description,
                "task": task_input.description,
                "subject": task_input.description,
                "situation": task_input.description,
            }
            if task_input.input_data:
                payload.update(task_input.input_data)
        elif isinstance(task_input, dict):
            payload = dict(task_input)
        else:
            payload = {"problem": str(task_input)}

        if context:
            payload["context"] = context
        return payload

    def _build_prompt(
        self,
        task_input: dict | Task,
        context: Optional[dict] = None,
    ) -> str:
        """Build a prompt string from task/context."""
        if isinstance(task_input, Task):
            task_text = task_input.description
        elif isinstance(task_input, dict):
            task_text = (
                task_input.get("description")
                or task_input.get("problem")
                or task_input.get("query")
                or str(task_input)
            )
        else:
            task_text = str(task_input)

        prompt = f"{self.agent.system_prompt}\n\nTask:\n{task_text}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        return prompt

    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate LLM response using agent configuration.
        """
        try:
            try:
                response = await self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=self.agent.system_prompt,
                    temperature=self.agent.temperature,
                    max_tokens=max_tokens,
                )
            except TypeError:
                # Backward compatibility with simpler mock clients.
                response = await self.llm_client.generate(prompt)

            if isinstance(response, dict):
                return str(response.get("response") or response.get("content") or response)
            return str(response)

        except Exception as e:
            self.logger.error("LLM generation failed: %s", str(e))
            raise

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.agent.name}, type={self.agent.agent_type.value})"

    def __repr__(self) -> str:
        """String representation."""
        return self.__str__()
