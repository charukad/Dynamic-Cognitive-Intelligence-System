"""Lightweight multi-agent debating service for legacy tests."""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

from src.infrastructure.repositories.memory import InMemoryAgentRepository


class DebaterService:
    """Minimal debate orchestrator with in-memory state."""

    def __init__(self) -> None:
        self.llm_client: Any = None
        self.agent_repo = InMemoryAgentRepository()
        self._debates: Dict[str, Dict[str, Any]] = {}

    async def create_debate(self, topic: str, agent_ids: List[str]) -> str:
        debate_id = str(uuid4())
        self._debates[debate_id] = {
            "topic": topic,
            "agent_ids": [str(agent_id) for agent_id in agent_ids],
            "rounds": [],
        }
        return debate_id

    async def execute_round(self, debate_id: str, round_number: int) -> Dict[str, Any]:
        debate = self._debates.get(debate_id)
        if debate is None:
            return {"error": "debate_not_found", "arguments": []}

        arguments = []
        for agent_id in debate["agent_ids"]:
            content = f"Agent {agent_id} argument for round {round_number}"
            if self.llm_client is not None and hasattr(self.llm_client, "generate"):
                generated = await self.llm_client.generate(
                    f"Debate topic: {debate['topic']}. Round: {round_number}.",
                )
                content = generated if isinstance(generated, str) else str(generated)

            arguments.append({
                "agent_id": agent_id,
                "round": round_number,
                "argument": content,
            })

        round_payload = {"round": round_number, "arguments": arguments}
        debate["rounds"].append(round_payload)
        return round_payload

    async def get_debate_summary(self, debate_id: str) -> Dict[str, Any]:
        debate = self._debates.get(debate_id)
        if debate is None:
            return {"error": "debate_not_found"}

        return {
            "debate_id": debate_id,
            "topic": debate["topic"],
            "agent_ids": debate["agent_ids"],
            "round_count": len(debate["rounds"]),
            "rounds": debate["rounds"],
        }


debater_service = DebaterService()

