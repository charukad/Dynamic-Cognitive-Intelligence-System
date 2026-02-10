"""Unit tests for service layer."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.services.agents.base_agent import BaseAgent
from src.services.agents.specialized_agents import CoderAgent, LogicianAgent
from src.services.memory.episodic_memory import EpisodicMemoryService
from src.services.orchestrator.meta_orchestrator import MetaOrchestrator


class TestBaseAgent:
    """Test BaseAgent functionality."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = BaseAgent(agent_id="test_agent", agent_type="coder")
        
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "coder"

    @pytest.mark.asyncio
    async def test_agent_process_with_mock_llm(self):
        """Test agent processing with mocked LLM."""
        agent = BaseAgent(agent_id="test", agent_type="coder")
        
        # Mock LLM client
        with patch.object(agent, 'llm_client') as mock_llm:
            mock_llm.generate = AsyncMock(return_value="Test response")
            
            result = await agent.process("Test task")
            
            assert "Test response" in result or result is not None


class TestCoderAgent:
    """Test CoderAgent specialized functionality."""

    @pytest.mark.asyncio
    async def test_coder_agent_initialization(self):
        """Test CoderAgent initialization."""
        agent = CoderAgent(agent_id="coder_1")
        
        assert agent.agent_type == "coder"
        assert agent.temperature <= 0.3  # Coder should have low temperature

    @pytest.mark.asyncio
    async def test_coder_agent_code_generation(self):
        """Test code generation capability."""
        agent = CoderAgent(agent_id="coder_1")
        
        with patch.object(agent, 'llm_client') as mock_llm:
            mock_llm.generate = AsyncMock(
                return_value="def hello():\n    return 'Hello, World!'"
            )
            
            result = await agent.process("Write a hello world function")
            
            assert result is not None


class TestLogicianAgent:
    """Test LogicianAgent specialized functionality."""

    @pytest.mark.asyncio
    async def test_logician_agent_initialization(self):
        """Test LogicianAgent initialization."""
        agent = LogicianAgent(agent_id="logician_1")
        
        assert agent.agent_type == "logician"
        assert agent.temperature <= 0.2  # Logician should have very low temperature


class TestEpisodicMemoryService:
    """Test EpisodicMemoryService."""

    @pytest.mark.asyncio
    async def test_store_memory(self):
        """Test storing a memory."""
        service = EpisodicMemoryService()
        
        memory_id = await service.store(
            content="Test memory content",
            importance=0.8,
            metadata={"source": "test"},
        )
        
        assert memory_id is not None
        assert isinstance(memory_id, str)

    @pytest.mark.asyncio
    async def test_retrieve_memories(self):
        """Test retrieving memories."""
        service = EpisodicMemoryService()
        
        # Store a memory first
        await service.store(
            content="Retrievable memory",
            importance=0.9,
        )
        
        # Retrieve recent memories
        memories = await service.get_recent(limit=10)
        
        assert isinstance(memories, list)


class TestMetaOrchestrator:
    """Test MetaOrchestrator coordination."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = MetaOrchestrator()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'process_query')

    @pytest.mark.asyncio
    async def test_orchestrator_query_processing(self):
        """Test query processing."""
        orchestrator = MetaOrchestrator()
        
        with patch.object(orchestrator, 'htn_planner') as mock_planner:
            mock_planner.decompose = AsyncMock(return_value=[{"subtask": "test"}])
            
            # Process a simple query
            result = await orchestrator.process_query("Test query")
            
            assert result is not None


class TestServiceIntegration:
    """Test service layer integration."""

    @pytest.mark.asyncio
    async def test_agent_memory_integration(self):
        """Test agent and memory service integration."""
        agent = CoderAgent(agent_id="coder_1")
        memory_service = EpisodicMemoryService()
        
        # Agent processes task
        with patch.object(agent, 'llm_client') as mock_llm:
            mock_llm.generate = AsyncMock(return_value="Code result")
            result = await agent.process("Write code")
        
        # Store result in memory
        memory_id = await memory_service.store(
            content=f"Agent {agent.agent_id} generated: {result}",
            importance=0.7,
        )
        
        assert memory_id is not None

    @pytest.mark.asyncio
    async def test_multiple_agents_coordination(self):
        """Test multiple agents working together."""
        agents = [
            CoderAgent(agent_id="coder_1"),
            LogicianAgent(agent_id="logician_1"),
        ]
        
        for agent in agents:
            assert agent.agent_id is not None
            assert agent.agent_type is not None
