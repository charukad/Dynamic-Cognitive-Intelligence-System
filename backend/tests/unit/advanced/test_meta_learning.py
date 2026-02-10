"""Tests for meta-learning system."""

import pytest

from src.services.advanced.meta_learning import MetaLearner, PerformanceMetric


@pytest.mark.asyncio
class TestMetaLearner:
    """Test suite for meta-learning system."""

    async def test_initialization(self):
        """Test meta-learner initialization."""
        learner = MetaLearner(learning_rate=0.1)
        
        assert learner.learning_rate == 0.1
        assert len(learner.metrics) == 0
        assert len(learner.updates) == 0

    async def test_record_performance_success(self):
        """Test recording successful performance."""
        learner = MetaLearner()
        
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_coder",
            success=True,
            latency=1.5,
            quality_score=0.9,
        )
        
        assert len(learner.metrics) >= 2  # success + latency
        assert learner.agent_task_count["agent_coder"] == 1
        assert learner.agent_success_rate["agent_coder"] > 0

    async def test_record_performance_failure(self):
        """Test recording failed performance."""
        learner = MetaLearner()
        
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_coder",
            success=False,
            latency=2.0,
        )
        
        assert learner.agent_success_rate["agent_coder"] < 0.5

    async def test_exponential_moving_average(self):
        """Test EMA calculation for success rate."""
        learner = MetaLearner(learning_rate=0.5)
        
        # Record multiple successes
        for i in range(5):
            await learner.record_performance(
                task_id=f"task_{i}",
                agent_id="agent_test",
                success=True,
                latency=1.0,
            )
        
        assert learner.agent_success_rate["agent_test"] > 0.9

    async def test_temperature_adaptation_high_success(self):
        """Test temperature reduction for high success rate."""
        learner = MetaLearner()
        learner.agent_success_rate["agent_test"] = 0.95
        learner.agent_temperatures["agent_test"] = 0.7
        
        new_temp = await learner.adapt_temperature("agent_test")
        
        assert new_temp is not None
        assert new_temp < 0.7  # Should decrease

    async def test_temperature_adaptation_low_success(self):
        """Test temperature increase for low success rate."""
        learner = MetaLearner()
        learner.agent_success_rate["agent_test"] = 0.3
        learner.agent_temperatures["agent_test"] = 0.5
        
        new_temp = await learner.adapt_temperature("agent_test")
        
        assert new_temp is not None
        assert new_temp > 0.5  # Should increase

    async def test_temperature_bounds(self):
        """Test temperature stays within bounds."""
        learner = MetaLearner()
        
        # Test upper bound
        learner.agent_success_rate["agent_test"] = 0.1
        learner.agent_temperatures["agent_test"] = 0.99
        
        for _ in range(10):
            await learner.adapt_temperature("agent_test")
        
        assert learner.agent_temperatures["agent_test"] <= 1.0
        
        # Test lower bound
        learner.agent_success_rate["agent_test2"] = 0.99
        learner.agent_temperatures["agent_test2"] = 0.11
        
        for _ in range(10):
            await learner.adapt_temperature("agent_test2")
        
        assert learner.agent_temperatures["agent_test2"] >= 0.1

    async def test_router_weight_update_success(self):
        """Test router weight update on success."""
        learner = MetaLearner()
        
        weights = await learner.update_router_weights(
            task_type="coding",
            agent_id="agent_coder",
            success=True,
        )
        
        assert weights["alpha"] == 2.0  # Initial 1.0 + 1
        assert weights["beta"] == 1.0

    async def test_router_weight_update_failure(self):
        """Test router weight update on failure."""
        learner = MetaLearner()
        
        weights = await learner.update_router_weights(
            task_type="coding",
            agent_id="agent_coder",
            success=False,
        )
        
        assert weights["alpha"] == 1.0
        assert weights["beta"] == 2.0  # Initial 1.0 + 1

    async def test_get_agent_statistics(self):
        """Test getting agent statistics."""
        learner = MetaLearner()
        
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_test",
            success=True,
            latency=1.5,
        )
        
        stats = learner.get_agent_statistics("agent_test")
        
        assert "agent_id" in stats
        assert "success_rate" in stats
        assert "avg_latency" in stats
        assert "task_count" in stats
        assert stats["task_count"] == 1

    async def test_learning_report_generation(self):
        """Test learning report generation."""
        learner = MetaLearner()
        
        # Generate some data
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_test",
            success=True,
            latency=1.0,
        )
        
        learner.agent_success_rate["agent_test"] = 0.95
        await learner.adapt_temperature("agent_test")
        
        report = learner.get_learning_report(limit=5)
        
        assert "total_metrics" in report
        assert "total_updates" in report
        assert "agent_statistics" in report
        assert "recent_updates" in report

    async def test_multiple_agents(self):
        """Test tracking multiple agents."""
        learner = MetaLearner()
        
        agents = ["agent_1", "agent_2", "agent_3"]
        
        for agent in agents:
            await learner.record_performance(
                task_id=f"task_{agent}",
                agent_id=agent,
                success=True,
                latency=1.0,
            )
        
        assert len(learner.agent_task_count) == 3
        
        for agent in agents:
            assert learner.agent_task_count[agent] == 1

    async def test_quality_score_recording(self):
        """Test quality score recording."""
        learner = MetaLearner()
        
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_test",
            success=True,
            latency=1.0,
            quality_score=0.85,
        )
        
        # Check quality metric was recorded
        quality_metrics = [
            m for m in learner.metrics
            if m.metric_name == "quality"
        ]
        
        assert len(quality_metrics) == 1
        assert quality_metrics[0].value == 0.85

    async def test_metadata_storage(self):
        """Test metadata storage in metrics."""
        learner = MetaLearner()
        
        metadata = {"task_type": "coding", "complexity": "high"}
        
        await learner.record_performance(
            task_id="task_1",
            agent_id="agent_test",
            success=True,
            latency=1.0,
            metadata=metadata,
        )
        
        # Check metadata was stored
        assert learner.metrics[0].metadata == metadata
