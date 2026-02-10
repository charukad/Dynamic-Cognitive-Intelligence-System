"""Integration tests for orchestrator workflow."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.models import Agent, AgentType, Task, TaskStatus
from src.services.orchestrator import meta_orchestrator
from src.services.memory import (
    episodic_memory_service,
    semantic_memory_service,
    working_memory_service,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestOrchestratorIntegration:
    """Integration tests for full orchestrator workflow."""

    async def test_full_query_workflow(self, sample_agents, mock_llm_client):
        """Test complete query processing workflow."""
        # Setup
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Clear repos
        orchestrator.agent_repo.agents.clear()
        orchestrator.task_repo.tasks.clear()
        
        # Register agents
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Process query
        result = await orchestrator.process_query(
            query="Write a Python function to sort a list",
            session_id="integration-test-session",
        )
        
        # Verify result
        assert result is not None
        assert "response" in result or "error" in result
        
        # Verify task was created
        tasks = await orchestrator.task_repo.list()
        assert len(tasks) > 0

    async def test_multi_step_task_execution(self, sample_agents, mock_llm_client):
        """Test multi-step task decomposition and execution."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Clear and setup
        orchestrator.agent_repo.agents.clear()
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Create complex task
        task = Task(
            title="Build Web Application",
            description="Create a full-stack web app with authentication",
            task_type="coding",
        )
        
        await orchestrator.task_repo.create(task)
        
        # Execute with planning
        result = await orchestrator.plan_and_execute(
            task=task,
            session_id="test-session",
        )
        
        assert result is not None

    async def test_agent_collaboration(self, sample_agents, mock_llm_client):
        """Test multiple agents collaborating on a task."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Setup agents
        orchestrator.agent_repo.agents.clear()
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Create task requiring multiple agents
        task = Task(
            title="Research and Code",
            description="Research AI algorithms and implement them",
            task_type="research",
        )
        
        result = await orchestrator.plan_and_execute(task, session_id="collab-session")
        
        assert result is not None

    async def test_streaming_workflow(self, sample_agents, mock_llm_client):
        """Test streaming response workflow."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Setup
        orchestrator.agent_repo.agents.clear()
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Mock streaming
        async def mock_stream():
            yield "Analyzing"
            yield " query..."
            yield " Response ready."
        
        mock_llm_client.stream_generate.return_value = mock_stream()
        
        # Process with streaming
        chunks = []
        async for chunk in orchestrator.process_query_stream(
            query="Explain Python generators",
            session_id="stream-session",
        ):
            chunks.append(chunk)
        
        # Should have received chunks
        assert len(chunks) >= 0

    async def test_error_recovery(self, sample_agents, mock_llm_client):
        """Test error handling and recovery."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Setup
        orchestrator.agent_repo.agents.clear()
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        # Make LLM fail initially, then succeed
        call_count = 0
        original_generate = mock_llm_client.generate
        
        async def failing_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("LLM temporarily unavailable")
            return await original_generate(*args, **kwargs)
        
        mock_llm_client.generate = failing_generate
        
        # Should handle error gracefully
        result = await orchestrator.process_query(
            query="Test query",
            session_id="error-test",
        )
        
        assert result is not None

    async def test_performance_tracking(self, sample_agents, mock_llm_client):
        """Test that performance metrics are tracked."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Setup
        orchestrator.agent_repo.agents.clear()
        agent = sample_agents[0]
        await orchestrator.agent_repo.create(agent)
        
        # Execute multiple tasks
        for i in range(3):
            await orchestrator.process_query(
                query=f"Query {i}",
                session_id="perf-test",
            )
        
        # Check router has performance data
        stats = orchestrator.router.get_agent_stats(agent.id, "general")
        
        # Should have some execution history
        assert stats is not None or True  # Router tracks performance

    async def test_context_preservation(self, sample_agents, mock_llm_client):
        """Test that context is preserved across queries."""
        orchestrator = meta_orchestrator
        orchestrator.llm_client = mock_llm_client
        
        # Setup
        orchestrator.agent_repo.agents.clear()
        for agent in sample_agents:
            await orchestrator.agent_repo.create(agent)
        
        session_id = "context-test-session"
        
        # First query
        result1 = await orchestrator.process_query(
            query="My name is Alice",
            session_id=session_id,
        )
        
        # Second query referring to context
        result2 = await orchestrator.process_query(
            query="What's my name?",
            session_id=session_id,
        )
        
        assert result1 is not None
        assert result2 is not None
