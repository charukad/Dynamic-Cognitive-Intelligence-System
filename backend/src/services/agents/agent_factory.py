"""Agent factory for creating specialized agents."""

from typing import Optional

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
    def create_agent(cls, agent: Agent) -> BaseAgent:
        """
        Create a specialized agent instance.
        
        Args:
            agent: Agent domain model
            
        Returns:
            Specialized agent instance
            
        Raises:
            ValueError: If agent type is not supported
        """
        agent_class = cls._agent_classes.get(agent.agent_type)
        
        if agent_class is None:
            raise ValueError(
                f"Unsupported agent type: {agent.agent_type}. "
                f"Supported types: {list(cls._agent_classes.keys())}"
            )
        
        logger.info(f"Creating agent: {agent.name} (type={agent.agent_type.value})")
        return agent_class(agent)

    @classmethod
    def get_supported_types(cls) -> list[AgentType]:
        """
        Get list of supported agent types.
        
        Returns:
            List of supported agent types
        """
        return list(cls._agent_classes.keys())

    @classmethod
    def register_agent_type(cls, agent_type: AgentType, agent_class: type[BaseAgent]) -> None:
        """
        Register a new agent type (for custom agents).
        
        Args:
            agent_type: Agent type enum
            agent_class: Agent class implementation
        """
        cls._agent_classes[agent_type] = agent_class
        logger.info(f"Registered new agent type: {agent_type.value}")


# Singleton instance
agent_factory = AgentFactory()
