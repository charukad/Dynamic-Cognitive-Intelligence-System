"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import UUID

from src.api.main import app
from src.domain.models import AgentType, TaskPriority, TaskStatus


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentEndpoints:
    """Integration tests for agent API endpoints."""

    async def test_create_agent(self):
        """Test creating an agent via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/v1/agents/",
                json={
                    "name": "TestAgent",
                    "agent_type": "logician",
                    "system_prompt": "You are a test agent",
                    "temperature": 0.5,
                    "capabilities": ["testing"],
                },
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "TestAgent"
            assert data["agent_type"] == "logician"
            assert UUID(data["id"])  # Valid UUID

    async def test_get_agent(self):
        """Test retrieving an agent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agent
            create_response = await client.post(
                "/v1/agents/",
                json={
                    "name": "GetTestAgent",
                    "agent_type": "creative",
                    "system_prompt": "Creative agent",
                },
            )
            agent_id = create_response.json()["id"]
            
            # Get agent
            get_response = await client.get(f"/v1/agents/{agent_id}")
            
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["id"] == agent_id
            assert data["name"] == "GetTestAgent"

    async def test_list_agents(self):
        """Test listing agents."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create multiple agents
            for i in range(3):
                await client.post(
                    "/v1/agents/",
                    json={
                        "name": f"Agent{i}",
                        "agent_type": "logician",
                        "system_prompt": f"Agent {i}",
                    },
                )
            
            # List agents
            response = await client.get("/v1/agents/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 3

    async def test_update_agent(self):
        """Test updating an agent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agent
            create_response = await client.post(
                "/v1/agents/",
                json={
                    "name": "OriginalName",
                    "agent_type": "scholar",
                    "system_prompt": "Original",
                },
            )
            agent_id = create_response.json()["id"]
            
            # Update agent
            update_response = await client.put(
                f"/v1/agents/{agent_id}",
                json={
                    "name": "UpdatedName",
                    "system_prompt": "Updated prompt",
                },
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["name"] == "UpdatedName"

    async def test_delete_agent(self):
        """Test deleting an agent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agent
            create_response = await client.post(
                "/v1/agents/",
                json={
                    "name": "ToDelete",
                    "agent_type": "critic",
                    "system_prompt": "Will be deleted",
                },
            )
            agent_id = create_response.json()["id"]
            
            # Delete agent
            delete_response = await client.delete(f"/v1/agents/{agent_id}")
            assert delete_response.status_code == 204
            
            # Verify deleted
            get_response = await client.get(f"/v1/agents/{agent_id}")
            assert get_response.status_code == 404

    async def test_filter_agents_by_type(self):
        """Test filtering agents by type."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agents of different types
            await client.post(
                "/v1/agents/",
                json={
                    "name": "Coder1",
                    "agent_type": "coder",
                    "system_prompt": "Coding expert",
                },
            )
            
            # Filter by type
            response = await client.get("/v1/agents/?agent_type=coder")
            
            assert response.status_code == 200
            data = response.json()
            assert all(agent["agent_type"] == "coder" for agent in data)


@pytest.mark.integration
@pytest.mark.asyncio
class TestTaskEndpoints:
    """Integration tests for task API endpoints."""

    async def test_create_task(self):
        """Test creating a task via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/v1/tasks/",
                json={
                    "title": "Test Task",
                    "description": "This is a test task",
                    "task_type": "testing",
                    "priority": "high",
                },
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Task"
            assert data["priority"] == "high"

    async def test_get_task(self):
        """Test retrieving a task."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create task
            create_response = await client.post(
                "/v1/tasks/",
                json={
                    "title": "Get Test Task",
                    "description": "Task to retrieve",
                    "task_type": "testing",
                },
            )
            task_id = create_response.json()["id"]
            
            # Get task
            get_response = await client.get(f"/v1/tasks/{task_id}")
            
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["id"] == task_id
            assert data["title"] == "Get Test Task"

    async def test_update_task_status(self):
        """Test updating task status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create task
            create_response = await client.post(
                "/v1/tasks/",
                json={
                    "title": "Status Test",
                    "description": "Test status update",
                    "task_type": "testing",
                },
            )
            task_id = create_response.json()["id"]
            
            # Update status
            update_response = await client.put(
                f"/v1/tasks/{task_id}",
                json={
                    "status": "completed",
                    "result": {"success": True},
                },
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["status"] == "completed"

    async def test_assign_task_to_agent(self):
        """Test assigning a task to an agent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create agent
            agent_response = await client.post(
                "/v1/agents/",
                json={
                    "name": "TaskAgent",
                    "agent_type": "executive",
                    "system_prompt": "Executive agent",
                },
            )
            agent_id = agent_response.json()["id"]
            
            # Create task
            task_response = await client.post(
                "/v1/tasks/",
                json={
                    "title": "Assigned Task",
                    "description": "Task to assign",
                    "task_type": "general",
                },
            )
            task_id = task_response.json()["id"]
            
            # Assign task
            assign_response = await client.post(
                f"/v1/tasks/{task_id}/assign",
                json={"agent_id": agent_id},
            )
            
            assert assign_response.status_code == 200
            data = assign_response.json()
            assert data["assigned_agent_id"] == agent_id

    async def test_filter_tasks_by_status(self):
        """Test filtering tasks by status."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create tasks with different statuses
            await client.post(
                "/v1/tasks/",
                json={
                    "title": "Pending Task",
                    "description": "Pending",
                    "task_type": "test",
                },
            )
            
            response = await client.get("/v1/tasks/?status=pending")
            
            assert response.status_code == 200
            data = response.json()
            assert all(task["status"] == "pending" for task in data)


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueryEndpoints:
    """Integration tests for query API endpoints."""

    async def test_query_endpoint(self):
        """Test query processing endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/v1/query",
                json={
                    "query": "What is Python?",
                    "session_id": "test-session",
                },
                timeout=30.0,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert "response" in data

    async def test_query_status(self):
        """Test query status endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Submit query
            query_response = await client.post(
                "/v1/query",
                json={
                    "query": "Test query",
                    "session_id": "status-test",
                },
                timeout=30.0,
            )
            task_id = query_response.json()["task_id"]
            
            # Check status
            status_response = await client.get(f"/v1/query/status/{task_id}")
            
            assert status_response.status_code == 200
            data = status_response.json()
            assert "status" in data
            assert "task_id" in data


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthEndpoint:
    """Integration tests for health check endpoint."""

    async def test_health_check(self):
        """Test health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

    async def test_root_endpoint(self):
        """Test root endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
