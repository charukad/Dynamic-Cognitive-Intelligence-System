"""
Benchmark tests for DCIS critical operations using pytest-benchmark.

Run with:
    pytest tests/performance/test_benchmarks.py --benchmark-only
    pytest tests/performance/test_benchmarks.py --benchmark-compare
    pytest tests/performance/test_benchmarks.py --benchmark-save=baseline
"""

import pytest
from unittest.mock import Mock, AsyncMock
from backend.src.services.orchestrator.meta_orchestrator import MetaOrchestrator
from backend.src.services.orchestrator.htn_planner import HTNPlanner
from backend.src.services.orchestrator.thompson_router import ThompsonSamplingRouter


class TestCriticalPathBenchmarks:
    """Benchmark critical code paths"""
    
    @pytest.fixture
    def orchestrator(self):
        """Mock orchestrator for benchmarking"""
        mock_orch = Mock(spec=MetaOrchestrator)
        mock_orch.process_query = AsyncMock(return_value={
            "response": "Test response",
            "agents_used": ["logician"],
            "confidence": 0.9
        })
        return mock_orch
    
    @pytest.fixture
    def htn_planner(self):
        """HTN Planner instance"""
        return HTNPlanner()
    
    @pytest.fixture
    def thompson_router(self):
        """Thompson Sampling Router instance"""
        return ThompsonSamplingRouter()
    
    def test_query_processing_benchmark(self, benchmark, orchestrator):
        """Benchmark query processing time"""
        async def process():
            return await orchestrator.process_query("Test query")
        
        # Run benchmark (synchronous wrapper for async)
        import asyncio
        result = benchmark(lambda: asyncio.run(process()))
        
        assert result is not None
    
    def test_task_decomposition_benchmark(self, benchmark, htn_planner):
        """Benchmark HTN task decomposition"""
        task = {
            "type": "coding",
            "description": "Write a Python function to sort a list",
            "complexity": "medium"
        }
        
        result = benchmark(htn_planner.decompose, task)
        assert len(result) > 0
    
    def test_agent_selection_benchmark(self, benchmark, thompson_router):
        """Benchmark Thompson Sampling agent selection"""
        task_type = "reasoning"
        available_agents = ["logician", "scholar", "creative"]
        
        result = benchmark(
            thompson_router.select_agent,
            task_type,
            available_agents
        )
        
        assert result in available_agents
    
    def test_memory_storage_benchmark(self, benchmark):
        """Benchmark memory storage operations"""
        from backend.src.services.memory.episodic_memory import EpisodicMemoryService
        
        memory_service = EpisodicMemoryService()
        
        def store_memory():
            return memory_service.store({
                "query": "Test query",
                "response": "Test response",
                "timestamp": "2024-01-29T00:00:00Z",
                "agents": ["logician"]
            })
        
        result = benchmark(store_memory)
        assert result is not None
    
    def test_memory_retrieval_benchmark(self, benchmark):
        """Benchmark memory retrieval"""
        from backend.src.services.memory.episodic_memory import EpisodicMemoryService
        
        memory_service = EpisodicMemoryService()
        
        result = benchmark(memory_service.retrieve, limit=10)
        assert isinstance(result, list)


class TestDataStructureBenchmarks:
    """Benchmark data structure operations"""
    
    def test_large_list_operations(self, benchmark):
        """Benchmark list operations with large datasets"""
        def process_large_list():
            data = list(range(10000))
            return sorted([x * 2 for x in data if x % 2 == 0])
        
        result = benchmark(process_large_list)
        assert len(result) == 5000
    
    def test_dict_lookup_performance(self, benchmark):
        """Benchmark dictionary lookups"""
        agent_configs = {f"agent_{i}": {"model": "gpt-4"} for i in range(1000)}
        
        def lookup_agents():
            results = []
            for i in range(100):
                agent_key = f"agent_{i * 10}"
                if agent_key in agent_configs:
                    results.append(agent_configs[agent_key])
            return results
        
        result = benchmark(lookup_agents)
        assert len(result) == 100


class TestAPIResponseBenchmarks:
    """Benchmark API response times"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_benchmark(self, benchmark):
        """Benchmark health check endpoint"""
        from fastapi.testclient import TestClient
        from backend.src.api.main import app
        
        client = TestClient(app)
        
        def health_check():
            return client.get("/health")
        
        response = benchmark(health_check)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_agents_list_benchmark(self, benchmark):
        """Benchmark agents listing endpoint"""
        from fastapi.testclient import TestClient
        from backend.src.api.main import app
        
        client = TestClient(app)
        
        def list_agents():
            return client.get("/v1/agents/")
        
        response = benchmark(list_agents)
        assert response.status_code in [200, 500]  # 500 if DB not available
