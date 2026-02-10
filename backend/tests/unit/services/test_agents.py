"""Unit tests for agent services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.domain.models import Agent, AgentType, Task, TaskStatus
from src.services.agents import (
    BaseAgent,
    CoderAgent,
    CreativeAgent,
    CriticAgent,
    ExecutiveAgent,
    LogicianAgent,
    ScholarAgent,
    agent_factory,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestBaseAgent:
    """Test suite for BaseAgent."""

    async def test_agent_initialization(self, sample_agent, mock_llm_client):
        """Test agent initialization."""
        agent = BaseAgent(sample_agent, mock_llm_client)
        
        assert agent.agent_model == sample_agent
        assert agent.llm_client == mock_llm_client
        assert agent.execution_count == 0

    async def test_execute_task(self, sample_agent, sample_task, mock_llm_client):
        """Test task execution."""
        agent = BaseAgent(sample_agent, mock_llm_client)
        
        result = await agent.execute(sample_task)
        
        assert result is not None
        assert "response" in result
        assert agent.execution_count == 1
        mock_llm_client.generate.assert_called_once()

    async def test_execute_with_context(self, sample_agent, sample_task, mock_llm_client):
        """Test task execution with context."""
        agent = BaseAgent(sample_agent, mock_llm_client)
        context = {"previous_result": "Some context"}
        
        result = await agent.execute(sample_task, context=context)
        
        assert result is not None
        assert agent.execution_count == 1

    async def test_build_prompt(self, sample_agent, sample_task, mock_llm_client):
        """Test prompt building."""
        agent = BaseAgent(sample_agent, mock_llm_client)
        
        prompt = agent._build_prompt(sample_task)
        
        assert sample_agent.system_prompt in prompt
        assert sample_task.description in prompt

    async def test_build_prompt_with_context(self, sample_agent, sample_task, mock_llm_client):
        """Test prompt building with context."""
        agent = BaseAgent(sample_agent, mock_llm_client)
        context = {"info": "Additional context"}
        
        prompt = agent._build_prompt(sample_task, context)
        
        assert "Additional context" in prompt

    async def test_error_handling(self, sample_agent, sample_task, mock_llm_client):
        """Test error handling during execution."""
        mock_llm_client.generate.side_effect = Exception("LLM Error")
        agent = BaseAgent(sample_agent, mock_llm_client)
        
        result = await agent.execute(sample_task)
        
        assert "error" in result
        assert "LLM Error" in result["error"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestSpecializedAgents:
    """Test suite for specialized agents."""

    async def test_logician_agent(self, mock_llm_client):
        """Test LogicianAgent execution."""
        agent_model = Agent(
            name="Logician",
            agent_type=AgentType.LOGICIAN,
            system_prompt="You are a logical thinker",
        )
        
        agent = LogicianAgent(agent_model, mock_llm_client)
        task = Task(
            title="Solve Logic Puzzle",
            description="Find the logical answer",
            task_type="reasoning",
        )
        
        result = await agent.execute(task)
        
        assert result is not None
        assert "response" in result

    async def test_creative_agent(self, mock_llm_client):
        """Test CreativeAgent execution."""
        agent_model = Agent(
            name="Creative",
            agent_type=AgentType.CREATIVE,
            system_prompt="You are creative",
        )
        
        agent = CreativeAgent(agent_model, mock_llm_client)
        task = Task(
            title="Write Story",
            description="Create a creative story",
            task_type="creative",
        )
        
        result = await agent.execute(task)
        
        assert result is not None

    async def test_coder_agent(self, mock_llm_client):
        """Test CoderAgent execution."""
        agent_model = Agent(
            name="Coder",
            agent_type=AgentType.CODER,
            system_prompt="You are a coding expert",
        )
        
        agent = CoderAgent(agent_model, mock_llm_client)
        task = Task(
            title="Write Code",
            description="Implement a function",
            task_type="coding",
        )
        
        result = await agent.execute(task)
        
        assert result is not None

    async def test_scholar_agent(self, mock_llm_client):
        """Test ScholarAgent execution."""
        agent_model = Agent(
            name="Scholar",
            agent_type=AgentType.SCHOLAR,
            system_prompt="You are knowledgeable",
        )
        
        agent = ScholarAgent(agent_model, mock_llm_client)
        task = Task(
            title="Research Topic",
            description="Research quantum physics",
            task_type="research",
        )
        
        result = await agent.execute(task)
        
        assert result is not None

    async def test_critic_agent(self, mock_llm_client):
        """Test CriticAgent execution."""
        agent_model = Agent(
            name="Critic",
            agent_type=AgentType.CRITIC,
            system_prompt="You analyze critically",
        )
        
        agent = CriticAgent(agent_model, mock_llm_client)
        task = Task(
            title="Review Work",
            description="Analyze the solution",
            task_type="review",
        )
        
        result = await agent.execute(task)
        
        assert result is not None

    async def test_executive_agent(self, mock_llm_client):
        """Test ExecutiveAgent execution."""
        agent_model = Agent(
            name="Executive",
            agent_type=AgentType.EXECUTIVE,
            system_prompt="You coordinate tasks",
        )
        
        agent = ExecutiveAgent(agent_model, mock_llm_client)
        task = Task(
            title="Coordinate Project",
            description="Manage the project",
            task_type="management",
        )
        
        result = await agent.execute(task)
        
        assert result is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestAgentFactory:
    """Test suite for AgentFactory."""

    async def test_create_logician(self, mock_llm_client):
        """Test creating logician agent."""
        agent_model = Agent(
            name="Logic",
            agent_type=AgentType.LOGICIAN,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, LogicianAgent)

    async def test_create_creative(self, mock_llm_client):
        """Test creating creative agent."""
        agent_model = Agent(
            name="Creative",
            agent_type=AgentType.CREATIVE,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, CreativeAgent)

    async def test_create_coder(self, mock_llm_client):
        """Test creating coder agent."""
        agent_model = Agent(
            name="Coder",
            agent_type=AgentType.CODER,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, CoderAgent)

    async def test_create_scholar(self, mock_llm_client):
        """Test creating scholar agent."""
        agent_model = Agent(
            name="Scholar",
            agent_type=AgentType.SCHOLAR,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, ScholarAgent)

    async def test_create_critic(self, mock_llm_client):
        """Test creating critic agent."""
        agent_model = Agent(
            name="Critic",
            agent_type=AgentType.CRITIC,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, CriticAgent)

    async def test_create_executive(self, mock_llm_client):
        """Test creating executive agent."""
        agent_model = Agent(
            name="Executive",
            agent_type=AgentType.EXECUTIVE,
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, ExecutiveAgent)

    async def test_factory_fallback(self, mock_llm_client):
        """Test factory fallback to BaseAgent."""
        agent_model = Agent(
            name="Unknown",
            agent_type=AgentType.LOGICIAN,  # Type exists but no special handling
            system_prompt="Test",
        )
        
        # Modify agent_type to something custom
        agent_model.agent_type = "custom_type"  # type: ignore
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        # Should fall back to BaseAgent for unknown types
        assert isinstance(agent, BaseAgent)

    async def test_register_custom_agent(self, mock_llm_client):
        """Test registering custom agent type."""
        
        class CustomAgent(BaseAgent):
            async def execute(self, task, context=None):
                return {"custom": True}
        
        # Register custom agent
        agent_factory.register_agent_type("custom", CustomAgent)
        
        agent_model = Agent(
            name="Custom",
            agent_type="custom",  # type: ignore
            system_prompt="Test",
        )
        
        agent = agent_factory.create_agent(agent_model, mock_llm_client)
        
        assert isinstance(agent, CustomAgent)
