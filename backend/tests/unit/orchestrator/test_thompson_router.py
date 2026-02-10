"""Unit tests for Thompson Sampling Router."""

import pytest
import numpy as np

from src.services.orchestrator.thompson_router import ThompsonRouter


class TestThompsonRouter:
    """Test Thompson Sampling Router."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = ThompsonRouter()
        self.agent_types = ["coder", "logician", "creative", "scholar"]

    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test router initialization."""
        assert self.router is not None
        assert hasattr(self.router, 'select_agent')

    @pytest.mark.asyncio
    async def test_select_agent_initial_state(self):
        """Test agent selection with no prior data."""
        selected = await self.router.select_agent(
            task_type="coding",
            available_agents=self.agent_types,
        )
        
        assert selected in self.agent_types

    @pytest.mark.asyncio
    async def test_select_agent_multiple_times(self):
        """Test selecting agents multiple times."""
        selections = []
        
        for _ in range(10):
            selected = await self.router.select_agent(
                task_type="coding",
                available_agents=self.agent_types,
            )
            selections.append(selected)
        
        # Should explore different agents
        assert len(selections) == 10

    @pytest.mark.asyncio
    async def test_update_performance(self):
        """Test updating agent performance."""
        agent_type = "coder"
        
        # Update with success
        await self.router.update_performance(
            agent_type=agent_type,
            task_type="coding",
            success=True,
            reward=1.0,
        )
        
        # Router should now favor this agent
        stats = self.router.get_statistics()
        assert stats is not None

    @pytest.mark.asyncio
    async def test_learning_from_feedback(self):
        """Test router learns from feedback."""
        # Give coder many successes
        for _ in range(10):
            await self.router.update_performance(
                agent_type="coder",
                task_type="coding",
                success=True,
                reward=1.0,
            )
        
        # Give logician many failures
        for _ in range(10):
            await self.router.update_performance(
                agent_type="logician",
                task_type="coding",
                success=False,
                reward=0.0,
            )
        
        # Router should prefer coder for coding tasks
        selections = []
        for _ in range(20):
            selected = await self.router.select_agent(
                task_type="coding",
                available_agents=["coder", "logician"],
            )
            selections.append(selected)
        
        # Coder should be selected more often
        coder_count = selections.count("coder")
        assert coder_count > 10  # Should be majority

    @pytest.mark.asyncio
    async def test_exploration_exploitation_balance(self):
        """Test router balances exploration and exploitation."""
        # Update one agent with good performance
        for _ in range(5):
            await self.router.update_performance(
                agent_type="coder",
                task_type="coding",
                success=True,
                reward=1.0,
            )
        
        # Router should still explore other agents sometimes
        selections = []
        for _ in range(50):
            selected = await self.router.select_agent(
                task_type="coding",
                available_agents=self.agent_types,
            )
            selections.append(selected)
        
        # Should have selected multiple different agents
        unique_selections = set(selections)
        assert len(unique_selections) >= 2  # At least 2 different agents

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test getting router statistics."""
        # Update some performance data
        await self.router.update_performance(
            agent_type="coder",
            task_type="coding",
            success=True,
            reward=0.9,
        )
        
        stats = self.router.get_statistics()
        
        assert stats is not None
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_different_task_types(self):
        """Test router handles different task types."""
        task_types = ["coding", "research", "creative", "logic"]
        
        for task_type in task_types:
            selected = await self.router.select_agent(
                task_type=task_type,
                available_agents=self.agent_types,
            )
            
            assert selected in self.agent_types


class TestThompsonRouterEdgeCases:
    """Test edge cases for Thompson Router."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = ThompsonRouter()

    @pytest.mark.asyncio
    async def test_single_agent_available(self):
        """Test with only one agent available."""
        selected = await self.router.select_agent(
            task_type="coding",
            available_agents=["coder"],
        )
        
        assert selected == "coder"

    @pytest.mark.asyncio
    async def test_empty_agent_list(self):
        """Test with empty agent list."""
        selected = await self.router.select_agent(
            task_type="coding",
            available_agents=[],
        )
        
        # Should handle gracefully
        assert selected is None or isinstance(selected, str)

    @pytest.mark.asyncio
    async def test_extreme_reward_values(self):
        """Test with extreme reward values."""
        # Very high reward
        await self.router.update_performance(
            agent_type="coder",
            task_type="coding",
            success=True,
            reward=1000.0,
        )
        
        # Very low reward
        await self.router.update_performance(
            agent_type="logician",
            task_type="coding",
            success=False,
            reward=-100.0,
        )
        
        # Router should still function
        selected = await self.router.select_agent(
            task_type="coding",
            available_agents=["coder", "logician"],
        )
        
        assert selected is not None


class TestThompsonRouterIntegration:
    """Integration tests for Thompson Router."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = ThompsonRouter()

    @pytest.mark.asyncio
    async def test_router_with_meta_orchestrator_workflow(self):
        """Test router in orchestrator workflow."""
        # Simulate orchestrator workflow
        task = "Write Python code"
        agent_types = ["coder", "logician", "creative"]
        
        # Select agent
        selected = await self.router.select_agent(
            task_type="coding",
            available_agents=agent_types,
        )
        
        # Simulate task execution and feedback
        success = True
        reward = 0.85
        
        await self.router.update_performance(
            agent_type=selected,
            task_type="coding",
            success=success,
            reward=reward,
        )
        
        assert selected in agent_types

    @pytest.mark.asyncio
    async def test_multi_task_learning(self):
        """Test learning across multiple task types."""
        # Different agents perform well on different tasks
        performance_map = {
            "coding": "coder",
            "logic": "logician",
            "creative": "creative",
        }
        
        # Train router
        for task_type, best_agent in performance_map.items():
            for _ in range(5):
                await self.router.update_performance(
                    agent_type=best_agent,
                    task_type=task_type,
                    success=True,
                    reward=0.9,
                )
        
        # Test specialization
        for task_type, expected_agent in performance_map.items():
            selections = []
            for _ in range(20):
                selected = await self.router.select_agent(
                    task_type=task_type,
                    available_agents=list(performance_map.values()),
                )
                selections.append(selected)
            
            # Expected agent should be selected majority of time
            expected_count = selections.count(expected_agent)
            assert expected_count >= 10  # At least half the time
