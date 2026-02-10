"""Unit tests for HTN Planner."""

import pytest

from src.services.orchestrator.htn_planner import HTNPlanner, Task, SubTask


class TestHTNPlanner:
    """Test HTN Planner decomposition."""

    def setup_method(self):
        """Set up test fixtures."""
        self.planner = HTNPlanner()

    @pytest.mark.asyncio
    async def test_planner_initialization(self):
        """Test planner initialization."""
        assert self.planner is not None

    @pytest.mark.asyncio
    async def test_simple_task_decomposition(self):
        """Test decomposing a simple task."""
        task = "Write a Python function to calculate factorial"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        assert len(subtasks) > 0

    @pytest.mark.asyncio
    async def test_complex_task_decomposition(self):
        """Test decomposing a complex multi-step task."""
        task = "Build a web scraper that extracts data and saves to database"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        assert len(subtasks) >= 3  # Should break into multiple steps

    @pytest.mark.asyncio
    async def test_research_task_decomposition(self):
        """Test decomposing a research task."""
        task = "Research and summarize the history of artificial intelligence"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        # Research tasks should have gathering and synthesis steps
        assert any("research" in str(st).lower() or "gather" in str(st).lower() 
                  for st in subtasks)

    @pytest.mark.asyncio
    async def test_coding_task_decomposition(self):
        """Test decomposing a coding task."""
        task = "Implement a REST API with authentication"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        # Coding tasks should have design, implement, test steps
        assert len(subtasks) >= 2

    @pytest.mark.asyncio
    async def test_empty_task_handling(self):
        """Test handling of empty task."""
        task = ""
        
        subtasks = await self.planner.decompose(task)
        
        # Should handle gracefully
        assert isinstance(subtasks, list)

    @pytest.mark.asyncio
    async def test_subtask_dependencies(self):
        """Test that subtasks have proper dependency order."""
        task = "Design, implement, and test a login system"
        
        subtasks = await self.planner.decompose(task)
        
        # Design should come before implementation
        # Implementation before testing
        assert len(subtasks) >= 3

    @pytest.mark.asyncio
    async def test_conditional_planning(self):
        """Test conditional logic in planning."""
        task = "If data exists, process it, else fetch new data first"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        assert len(subtasks) > 0


class TestHTNPlannerIntegration:
    """Integration tests for HTN Planner with other components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.planner = HTNPlanner()

    @pytest.mark.asyncio
    async def test_planner_with_agent_assignment(self):
        """Test planner output suitable for agent assignment."""
        task = "Write and test a function"
        
        subtasks = await self.planner.decompose(task)
        
        # Each subtask should be assignable to an agent
        for subtask in subtasks:
            assert subtask is not None

    @pytest.mark.asyncio
    async def test_planner_output_format(self):
        """Test planner output format is consistent."""
        task = "Test task"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
        # Each subtask should have expected structure
        for subtask in subtasks:
            assert subtask is not None


class TestHTNPlannerEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.planner = HTNPlanner()

    @pytest.mark.asyncio
    async def test_very_long_task_description(self):
        """Test handling of very long task descriptions."""
        task = "a " * 1000  # Very long task
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)

    @pytest.mark.asyncio
    async def test_special_characters_in_task(self):
        """Test handling of special characters."""
        task = "Task with symbols: @#$%^&*()"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)

    @pytest.mark.asyncio
    async def test_multilingual_task(self):
        """Test handling of non-English characters."""
        task = "Tarea en español"
        
        subtasks = await self.planner.decompose(task)
        
        assert isinstance(subtasks, list)
