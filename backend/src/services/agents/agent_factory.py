"""Agent factory for creating specialized agents."""

from typing import Any, Optional

from src.core import get_logger
from src.domain.models import Agent, AgentType
from src.services.agents.base_agent import BaseAgent
from src.services.agents.specialized_agents import (
    CoderAgent,
    CreativeAgent,
    CriticAgent,
    ExecutiveAgent,
    LogicianAgent,
    ScholarAgent,
)

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating specialized agent instances.
    
    Provides centralized agent creation with proper type mapping.
    """

    # Mapping of agent types to agent classes
    _agent_classes = {
        AgentType.LOGICIAN: LogicianAgent,
        AgentType.CREATIVE: CreativeAgent,
        AgentType.SCHOLAR: ScholarAgent,
        AgentType.CRITIC: CriticAgent,
        AgentType.CODER: CoderAgent,
        AgentType.EXECUTIVE: ExecutiveAgent,
    }

    @classmethod
    def create_agent(cls, agent: Agent, llm_client: Optional[Any] = None) -> BaseAgent:
        """
        Create a specialized agent instance.
        
        Args:
            agent: Agent domain model
            
        Returns:
            Specialized agent instance
            
        Raises:
            ValueError: If agent type is not supported
        """
        agent_type = getattr(agent, "agent_type", None)
        agent_class = cls._agent_classes.get(agent_type)

        # Backward-compatible lookup by raw string type.
        if agent_class is None:
            agent_class = cls._agent_classes.get(str(agent_type))

        if agent_class is None:
            logger.warning(
                "Unsupported agent type %s, falling back to BaseAgent",
                agent_type,
            )
            return BaseAgent(agent, llm_client=llm_client)

        type_label = getattr(agent_type, "value", agent_type)
        logger.info("Creating agent: %s (type=%s)", agent.name, type_label)
        return agent_class(agent, llm_client=llm_client)

    @classmethod
    def get_supported_types(cls) -> list[AgentType]:
        """
        Get list of supported agent types.
        
        Returns:
            List of supported agent types
        """
        return list(cls._agent_classes.keys())

    @classmethod
    def register_agent_type(cls, agent_type: AgentType | str, agent_class: type[BaseAgent]) -> None:
        """
        Register a new agent type (for custom agents).
        
        Args:
            agent_type: Agent type enum
            agent_class: Agent class implementation
        """
        key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
        cls._agent_classes[key] = agent_class
        logger.info("Registered new agent type: %s", key)


# Singleton instance
agent_factory = AgentFactory()
