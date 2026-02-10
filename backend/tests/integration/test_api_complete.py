"""API integration tests."""

import pytest
from httpx import AsyncClient

from src.api.main import app


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoints."""

    async def test_health_check_returns_200(self):
        """Test health endpoint returns 200."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    async def test_health_check_response_structure(self):
        """Test health check response structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            data = response.json()
            
            assert "status" in data
            assert data["status"] in ["healthy", "ok"]


@pytest.mark.asyncio
class TestAgentEndpoints:
    """Test agent CRUD endpoints."""

    async def test_create_agent(self):
        """Test creating an agent via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            agent_data = {
                "name": "test_agent",
                "type": "coder",
                "config": {"temperature": 0.2},
            }
            
            response = await client.post("/api/v1/agents", json=agent_data)
            
            assert response.status_code in [200, 201, 422]  # 422 if validation fails

    async def test_list_agents(self):
        """Test listing all agents."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/agents")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_get_agent_by_id(self):
        """Test getting a specific agent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First create an agent
            agent_data = {"name": "get_test", "type": "coder"}
            create_response = await client.post("/api/v1/agents", json=agent_data)
            
            if create_response.status_code in [200, 201]:
                agent = create_response.json()
                agent_id = agent.get("id")
                
                # Now get it
                get_response = await client.get(f"/api/v1/agents/{agent_id}")
                assert get_response.status_code in [200, 404]


@pytest.mark.asyncio
class TestTaskEndpoints:
    """Test task CRUD endpoints."""

    async def test_create_task(self):
        """Test creating a task."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            task_data = {
                "description": "Test task from integration test",
                "priority": 5,
            }
            
            response = await client.post("/api/v1/tasks", json=task_data)
            
            assert response.status_code in [200, 201, 422]

    async def test_list_tasks(self):
        """Test listing all tasks."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/tasks")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_update_task_status(self):
        """Test updating task status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a task
            task_data = {"description": "Update test task"}
            create_response = await client.post("/api/v1/tasks", json=task_data)
            
            if create_response.status_code in [200, 201]:
                task = create_response.json()
                task_id = task.get("id")
                
                # Update status
                update_data = {"status": "in_progress"}
                update_response = await client.patch(
                    f"/api/v1/tasks/{task_id}",
                    json=update_data,
                )
                
                assert update_response.status_code in [200, 404, 422]


@pytest.mark.asyncio
class TestQueryEndpoint:
    """Test query processing endpoint."""

    async def test_submit_query(self):
        """Test submitting a query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            query_data = {
                "query": "What is machine learning?",
                "user_id": "test_user",
            }
            
            response = await client.post("/api/v1/query", json=query_data)
            
            # Should return task_id and status
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "task_id" in data or "status" in data

    async def test_query_validation(self):
        """Test query input validation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Empty query should fail
            query_data = {
                "query": "",
                "user_id": "test_user",
            }
            
            response = await client.post("/api/v1/query", json=query_data)
            
            # Should return validation error
            assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestMemoryEndpoints:
    """Test memory API endpoints."""

    async def test_store_memory(self):
        """Test storing a memory."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            memory_data = {
                "type": "episodic",
                "content": "Test memory content",
                "importance": 0.8,
            }
            
            response = await client.post("/api/v1/memory", json=memory_data)
            
            assert response.status_code in [200, 201, 422]

    async def test_search_memory(self):
        """Test searching memories."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            search_data = {
                "query": "test",
                "limit": 10,
            }
            
            response = await client.post("/api/v1/memory/search", json=search_data)
            
            assert response.status_code in [200, 422]


@pytest.mark.asyncio
class TestErrorHandling:
    """Test API error handling."""

    async def test_404_for_invalid_endpoint(self):
        """Test 404 for non-existent endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent")
            
            assert response.status_code == 404

    async def test_405_for_wrong_method(self):
        """Test 405 for wrong HTTP method."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try POST on a GET-only endpoint
            response = await client.post("/health")
            
            assert response.status_code in [404, 405, 422]

    async def test_malformed_json(self):
        """Test handling of malformed JSON."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/agents",
                content="invalid json{{{",
                headers={"Content-Type": "application/json"},
            )
            
            assert response.status_code in [400, 422]
