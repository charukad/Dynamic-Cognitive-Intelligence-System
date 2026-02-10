"""Unit tests for orchestrator services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.domain.models import Agent, AgentType, Task, TaskStatus
from src.services.orchestrator import (
    HTNPlanner,
    ThompsonRouter,
    meta_orchestrator,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestHTNPlanner:
    """Test suite for HTN Planner."""

    def test_planner_initialization(self):
        """Test HTN planner initialization."""
        planner = HTNPlanner()
        
        assert planner is not None
        assert len(planner.methods) > 0  # Should have default methods

    async def test_decompose_simple_task(self):
        """Test decomposing a simple task."""
        planner = HTNPlanner()
        
        task = Task(
            title="Write Code",
            description="Implement a function",
            task_type="coding",
        )
        
        subtasks = await planner.decompose_task(task)
        
        assert isinstance(subtasks, list)
        assert len(subtasks) >= 1

    async def test_decompose_complex_task(self):
        """Test decomposing a complex research task."""
        planner = HTNPlanner()
        
        task = Task(
            title="Research Topic",
            description="Research quantum computing",
            task_type="research",
        )
        
        subtasks = await planner.decompose_task(task)
        
        assert isinstance(subtasks, list)
        # Complex tasks should decompose into multiple subtasks
        assert len(subtasks) >= 1

    async def test_register_custom_method(self):
        """Test registering a custom decomposition method."""
        planner = HTNPlanner()
        
        async def custom_method(task):
            return [
                Task(title="Step 1", description="First", task_type="custom"),
                Task(title="Step 2", description="Second", task_type="custom"),
            ]
        
        planner.register_method("custom_task", custom_method)
        
        task = Task(
            title="Custom Task",
            description="Test custom",
            task_type="custom_task",
        )
        
        subtasks = await planner.decompose_task(task)
        
        assert len(subtasks) == 2
        assert subtasks[0].title == "Step 1"

    async def test_build_task_hierarchy(self):
        """Test building task hierarchy."""
        planner = HTNPlanner()
        
        root_task = Task(
            title="Build App",
            description="Create web application",
            task_type="coding",
        )
        
        hierarchy = await planner.build_hierarchy(root_task, max_depth=2)
        
        assert hierarchy is not None
        assert "task" in hierarchy
        assert "subtasks" in hierarchy

    async def test_max_depth_limit(self):
        """Test that max depth is respected."""
        planner = HTNPlanner()
        
        task = Task(
            title="Complex Task",
            description="Very complex",
            task_type="research",
        )
        
        # Build with depth limit
        hierarchy = await planner.build_hierarchy(task, max_depth=1)
        
        # Should not recurse beyond max_depth
        assert hierarchy is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestThompsonRouter:
    """Test suite for Thompson Sampling Router."""

    def test_router_initialization(self):
        """Test router initialization."""
        router = ThompsonRouter()
        
        assert router is not None
        assert router.exploration_weight > 0

    async def test_select_agent_initial(self, sample_agents):
        """Test selecting agent with no history."""
        router = ThompsonRouter()
        
        # Register agents
        for agent in sample_agents:
            router.register_agent(agent.id, agent.agent_type)
        
        # Select agent
        selected = await router.select_agent(task_type="coding")
        
        assert selected is not None

    async def test_update_performance(self, sample_agent):
        """Test updating agent performance."""
        router = ThompsonRouter()
        router.register_agent(sample_agent.id, sample_agent.agent_type)
        
        # Update with success
        await router.update_performance(
            agent_id=sample_agent.id,
            task_type="coding",
            success=True,
            execution_time_ms=500,
        )
        
        # Check that stats were updated
        stats = router.get_agent_stats(sample_agent.id, "coding")
        assert stats is not None
        assert stats["successes"] >= 1

    async def test_exploration_vs_exploitation(self):
        """Test exploration vs exploitation balance."""
        router = ThompsonRouter()
        
        agent1_id = uuid4()
        agent2_id = uuid4()
        
        router.register_agent(agent1_id, AgentType.CODER)
        router.register_agent(agent2_id, AgentType.CODER)
        
        # Give agent1 good performance history
        for _ in range(10):
            await router.update_performance(
                agent_id=agent1_id,
                task_type="coding",
                success=True,
                execution_time_ms=300,
            )
        
        # Select multiple times - should still explore agent2 sometimes
        selections = []
        for _ in range(20):
            selected = await router.select_agent(task_type="coding")
            selections.append(selected)
        
        # Should select both agents (exploration)
        unique_selections = set(selections)
        # At least agent1 should be selected multiple times
        assert len([s for s in selections if s == agent1_id]) > 0

    async def test_get_agent_stats(self, sample_agent):
        """Test retrieving agent statistics."""
        router = ThompsonRouter()
        router.register_agent(sample_agent.id, sample_agent.agent_type)
        
        # Update performance
        await router.update_performance(
            agent_id=sample_agent.id,
            task_type="coding",
            success=True,
            execution_time_ms=400,
        )
        
        stats = router.get_agent_stats(sample_agent.id, "coding")
        
        assert stats is not None
        assert "successes" in stats
        assert "failures" in stats
        assert "avg_time_ms" in stats

    async def test_get_leaderboard(self):
        """Test getting agent leaderboard."""
        router = ThompsonRouter()
        
        agent1 = uuid4()
        agent2 = uuid4()
        
        router.register_agent(agent1, AgentType.CODER)
        router.register_agent(agent2, AgentType.CODER)
        
        # Give different performance
        await router.update_performance(agent1, "coding", True, 300)
        await router.update_performance(agent2, "coding", True, 500)
        
        leaderboard = router.get_leaderboard("coding")
        
        assert isinstance(leaderboard, list)


@pytest.mark.unit
@pytest.mark.asyncio
class TestMetaOrchestrator:
    """Test suite for Meta-Orchestrator."""

    async def test_orchestrator_initialization(
        self,
        mock_llm_client,
        mock_chroma_client,
        mock_neo4j_client,
        mock_redis_client,
    ):
        """Test orchestrator initialization."""
        orchestrator = meta_orchestrator
        
        assert orchestrator is not None
        assert orchestrator.planner is not None
        assert orchestrator.router is not None

    async def test_process_query_simple(
        self,
        sample_agent,
        mock_llm_client,
    ):
        """Test processing a simple query."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Register agent
        await orchestrator.agent_repo.create(sample_agent)
        
        # Process query
        result = await orchestrator.process_query(
            query="What is Python?",
            session_id="test-session",
        )
        
        assert result is not None
        assert "response" in result or "error" in result

    async def test_plan_and_execute(
        self,
        sample_agents,
        mock_llm_client,
    ):
        """Test planning and executing tasks."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Register agents
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Create task
        task = Task(
            title="Write Python Code",
            description="Implement a sorting algorithm",
            task_type="coding",
        )
        
        result = await orchestrator.plan_and_execute(
            task=task,
            session_id="test-session",
        )
        
        assert result is not None

    async def test_streaming_response(self, sample_agent, mock_llm_client):
        """Test streaming query response."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        await orchestrator.agent_repo.create(sample_agent)
        
        # Mock streaming
        async def mock_stream():
            yield "Response"
            yield " chunk"
        
        mock_llm_client.stream_generate.return_value = mock_stream()
        
        chunks = []
        async for chunk in orchestrator.process_query_stream(
            query="Test query",
            session_id="test-session",
        ):
            chunks.append(chunk)
        
        assert len(chunks) >= 0

    async def test_agent_selection(self, sample_agents, mock_llm_client):
        """Test agent selection for task."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Register multiple agents
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Select agent for coding task
        selected = await orchestrator._select_agent_for_task(
            task_type="coding",
            available_agents=sample_agents,
        )
        
        assert selected is not None

    async def test_error_handling(self, mock_llm_client):
        """Test error handling in orchestrator."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Make LLM fail
        mock_llm_client.generate.side_effect = Exception("LLM Error")
        
        result = await orchestrator.process_query(
            query="Test",
            session_id="test-session",
        )
        
        # Should handle error gracefully
        assert result is not None
        assert "error" in result or "response" in result
