"""Agent Forge for dynamic agent creation and management."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Agent, AgentStatus, AgentType
from src.infrastructure.llm import vllm_client
from src.infrastructure.repositories import agent_repository
from src.services.agents import agent_factory

logger = get_logger(__name__)


class AgentForge:
    """
    Agent Forge for dynamically creating specialized agents.
    
    Creates custom agents with synthesized prompts based on requirements.
    """

    def __init__(self) -> None:
        """Initialize Agent Forge."""
        self.agent_templates = self._load_agent_templates()

    def _load_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load agent templates.
        
        Returns:
            Agent templates by type
        """
        return {
            "specialist": {
                "temperature": 0.3,
                "description": "Expert in a specific domain with deep knowledge",
            },
            "creative": {
                "temperature": 0.8,
                "description": "Creative problem solver with innovative approaches",
            },
            "analyst": {
                "temperature": 0.2,
                "description": "Analytical thinker with systematic methodology",
            },
            "generalist": {
                "temperature": 0.5,
                "description": "Versatile agent with broad knowledge",
            },
        }

    async def forge_agent(
        self,
        name: str,
        role: str,
        capabilities: List[str],
        agent_template: str = "specialist",
        temperature: Optional[float] = None,
    ) -> Agent:
        """
        Forge a new custom agent.
        
        Args:
            name: Agent name
            role: Agent role description
            capabilities: List of required capabilities
            agent_template: Template type
            temperature: Optional custom temperature
            
        Returns:
            Created agent
        """
        logger.info(f"Forging new agent: {name} ({role})")

        # Generate system prompt
        system_prompt = await self._synthesize_system_prompt(
            role=role,
            capabilities=capabilities,
            template=agent_template,
        )

        # Get template configuration
        template_config = self.agent_templates.get(
            agent_template,
            self.agent_templates["generalist"],
        )

        # Create agent
        agent = Agent(
            name=name,
            agent_type=AgentType.EXECUTIVE,  # Custom agents use executive type
            system_prompt=system_prompt,
            temperature=temperature or template_config["temperature"],
            capabilities=capabilities,
            metadata={
                "forged": True,
                "template": agent_template,
                "role": role,
            },
        )

        # Store agent
        created_agent = await agent_repository.create(agent)
        
        # Register with factory
        agent_factory.register_agent_type(
            agent_type=AgentType.EXECUTIVE,
            agent_class=agent_factory._agent_classes[AgentType.EXECUTIVE],
        )

        logger.info(f"Forged agent {name} (id={created_agent.id})")
        
        return created_agent

    async def _synthesize_system_prompt(
        self,
        role: str,
        capabilities: List[str],
        template: str,
    ) -> str:
        """
        Synthesize system prompt for custom agent.
        
        Args:
            role: Agent role
            capabilities: Required capabilities
            template: Template type
            
        Returns:
            Synthesized system prompt
        """
        capabilities_text = "\n".join([f"- {cap}" for cap in capabilities])
        template_desc = self.agent_templates[template]["description"]
        
        prompt = f"""Create a detailed system prompt for an AI agent with the following specifications:

Role: {role}
Type: {template_desc}

Required Capabilities:
{capabilities_text}

The system prompt should:
1. Clearly define the agent's role and expertise
2. Specify the agent's approach and methodology
3. Include guidelines for response quality
4. Be concise but comprehensive (2-3 paragraphs)

System Prompt:"""

        try:
            system_prompt = await vllm_client.generate(
                prompt=prompt,
                temperature=0.4,
                max_tokens=500,
            )
            
            return system_prompt.strip()
            
        except Exception as e:
            logger.error(f"Failed to synthesize system prompt: {e}")
            # Fallback to basic prompt
            return f"You are {role}. Your capabilities include: {', '.join(capabilities)}. Provide expert assistance in your domain."

    async def evolve_agent(
        self,
        agent_id: UUID,
        performance_feedback: Dict[str, Any],
    ) -> Agent:
        """
        Evolve an agent based on performance feedback.
        
        Args:
            agent_id: Agent to evolve
            performance_feedback: Performance metrics and feedback
            
        Returns:
            Evolved agent
        """
        agent = await agent_repository.get_by_id(agent_id)
        
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        logger.info(f"Evolving agent: {agent.name}")

        # Generate improved prompt based on feedback
        feedback_text = "\n".join([
            f"- {key}: {value}"
            for key, value in performance_feedback.items()
        ])
        
        prompt = f"""Improve this agent's system prompt based on performance feedback.

Current System Prompt:
{agent.system_prompt}

Performance Feedback:
{feedback_text}

Generate an improved system prompt that addresses the feedback while maintaining the agent's core role:"""

        try:
            improved_prompt = await vllm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
            )
            
            # Update agent
            agent.system_prompt = improved_prompt.strip()
            
            # Increment version in metadata
            current_version = agent.metadata.get("version", 1)
            agent.metadata["version"] = current_version + 1
            agent.metadata["last_evolution"] = performance_feedback
            
            updated_agent = await agent_repository.update(agent)
            
            logger.info(f"Agent {agent.name} evolved to version {agent.metadata['version']}")
            
            return updated_agent
            
        except Exception as e:
            logger.error(f"Failed to evolve agent: {e}")
            return agent

    async def clone_agent(
        self,
        agent_id: UUID,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Clone an existing agent with optional modifications.
        
        Args:
            agent_id: Agent to clone
            new_name: Name for cloned agent
            modifications: Optional modifications
            
        Returns:
            Cloned agent
        """
        original = await agent_repository.get_by_id(agent_id)
        
        if not original:
            raise ValueError(f"Agent not found: {agent_id}")

        logger.info(f"Cloning agent: {original.name} -> {new_name}")

        # Create clone
        cloned = Agent(
            name=new_name,
            agent_type=original.agent_type,
            system_prompt=original.system_prompt,
            temperature=original.temperature,
            capabilities=original.capabilities.copy(),
            metadata={
                **original.metadata,
                "cloned_from": str(agent_id),
                "original_name": original.name,
            },
        )

        # Apply modifications
        if modifications:
            if "system_prompt" in modifications:
                cloned.system_prompt = modifications["system_prompt"]
            if "temperature" in modifications:
                cloned.temperature = modifications["temperature"]
            if "capabilities" in modifications:
                cloned.capabilities = modifications["capabilities"]

        # Store clone
        created_clone = await agent_repository.create(cloned)
        
        logger.info(f"Cloned agent {new_name} (id={created_clone.id})")
        
        return created_clone

    async def list_forged_agents(self) -> List[Agent]:
        """
        List all forged (custom) agents.
        
        Returns:
            List of forged agents
        """
        all_agents = await agent_repository.list(limit=1000)
        
        forged = [
            agent for agent in all_agents
            if agent.metadata.get("forged", False)
        ]
        
        return forged


# Singleton instance
agent_forge = AgentForge()
