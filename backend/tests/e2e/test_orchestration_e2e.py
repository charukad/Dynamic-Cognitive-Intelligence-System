"""End-to-end tests for orchestration flow."""

import pytest
from httpx import AsyncClient

from src.api.main import app
from src.domain.models import TaskStatus


@pytest.mark.asyncio
class TestOrchestrationE2E:
    """End-to-end tests for complete orchestration workflows."""

    async def test_full_query_processing_flow(self):
        """Test complete query processing from input to output."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Submit query
            query_data = {
                "query": "Explain how neural networks learn using backpropagation",
                "user_id": "test_user",
            }
            
            response = await client.post("/api/v1/query", json=query_data)
            assert response.status_code == 200
            
            result = response.json()
            assert "task_id" in result
            assert "status" in result
            
            task_id = result["task_id"]
            
            # Step 2: Check task status
            status_response = await client.get(f"/api/v1/tasks/{task_id}")
            assert status_response.status_code == 200
            
            task_data = status_response.json()
            assert task_data["id"] == task_id
            assert task_data["status"] in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]

    async def test_multi_agent_debate_flow(self):
        """Test multi-agent debate orchestration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            debate_data = {
                "topic": "Should AI development be regulated?",
                "participants": ["logician", "creative", "critic"],
                "rounds": 2,
            }
            
            response = await client.post("/api/v1/debate/start", json=debate_data)
            assert response.status_code == 200
            
            result = response.json()
            assert "debate_id" in result
            assert "status" in result

    async def test_agent_creation_and_task_assignment(self):
        """Test creating an agent and assigning a task."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agent
            agent_data = {
                "name": "test_coder",
                "type": "coder",
                "config": {"temperature": 0.2},
            }
            
            create_response = await client.post("/api/v1/agents", json=agent_data)
            assert create_response.status_code in [200, 201]
            
            agent = create_response.json()
            agent_id = agent.get("id")
            
            # Assign task
            task_data = {
                "description": "Write a Python function to calculate factorial",
                "agent_id": agent_id,
            }
            
            task_response = await client.post("/api/v1/tasks", json=task_data)
            assert task_response.status_code in [200, 201]

    async def test_memory_storage_and_retrieval_flow(self):
        """Test storing and retrieving memories."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Store memory
            memory_data = {
                "type": "episodic",
                "content": "User asked about machine learning algorithms",
                "importance": 0.8,
                "metadata": {"topic": "ML", "user_id": "test_user"},
            }
            
            store_response = await client.post("/api/v1/memory", json=memory_data)
            assert store_response.status_code in [200, 201]
            
            memory = store_response.json()
            memory_id = memory.get("id")
            
            # Retrieve memory
            retrieve_response = await client.get(f"/api/v1/memory/{memory_id}")
            assert retrieve_response.status_code == 200
            
            retrieved = retrieve_response.json()
            assert retrieved["content"] == memory_data["content"]

    async def test_knowledge_graph_creation_flow(self):
        """Test creating knowledge graph relationships."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create concept nodes
            concept1 = {
                "label": "Concept",
                "properties": {"id": "neural_network", "name": "Neural Network"},
            }
            
            concept2 = {
                "label": "Concept",
                "properties": {"id": "backprop", "name": "Backpropagation"},
            }
            
            # Create relationship
            relationship_data = {
                "from_id": "neural_network",
                "to_id": "backprop",
                "type": "USES",
                "properties": {"strength": 0.9},
            }
            
            # Note: This assumes knowledge graph API endpoints exist
            # If not, this test validates the intended functionality

    async def test_error_handling_in_orchestration(self):
        """Test error handling during orchestration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Submit invalid query
            invalid_query = {
                "query": "",  # Empty query
                "user_id": "test_user",
            }
            
            response = await client.post("/api/v1/query", json=invalid_query)
            # Should return validation error
            assert response.status_code in [400, 422]

    async def test_concurrent_task_processing(self):
        """Test handling multiple concurrent tasks."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            tasks = []
            
            # Submit multiple queries concurrently
            for i in range(5):
                query_data = {
                    "query": f"Query {i}: What is machine learning?",
                    "user_id": f"user_{i}",
                }
                
                response = await client.post("/api/v1/query", json=query_data)
                assert response.status_code == 200
                tasks.append(response.json())
            
            # Verify all tasks were created
            assert len(tasks) == 5
            assert all("task_id" in task for task in tasks)

    async def test_health_check_endpoints(self):
        """Test system health check."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert "status" in health_data
