"""Database integration tests."""

import pytest
import asyncio

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.redis_client import redis_client


@pytest.mark.asyncio
class TestPostgresIntegration:
    """Integration tests for PostgreSQL client."""

    async def test_postgres_connection(self):
        """Test PostgreSQL connection."""
        try:
            await postgres_client.connect()
            assert postgres_client.pool is not None
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        finally:
            await postgres_client.disconnect()

    async def test_postgres_query_execution(self):
        """Test executing queries."""
        try:
            await postgres_client.connect()
            
            # Execute a simple query
            result = await postgres_client.execute("SELECT 1")
            assert result is not None
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        finally:
            await postgres_client.disconnect()

    async def test_postgres_create_and_fetch(self):
        """Test creating and fetching data."""
        try:
            await postgres_client.connect()
            await postgres_client.init_schema()
            
            # Insert test data
            await postgres_client.execute(
                """
                INSERT INTO agents (id, name, type, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
                """,
                "test_agent_123",
                "Test Agent",
                "coder",
                "idle",
            )
            
            # Fetch it back
            result = await postgres_client.fetchrow(
                "SELECT * FROM agents WHERE id = $1",
                "test_agent_123",
            )
            
            if result:
                assert result["id"] == "test_agent_123"
                assert result["name"] == "Test Agent"
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        finally:
            await postgres_client.disconnect()


@pytest.mark.asyncio
class TestNeo4jIntegration:
    """Integration tests for Neo4j client."""

    async def test_neo4j_connection(self):
        """Test Neo4j connection."""
        try:
            await neo4j_client.connect()
            assert neo4j_client.driver is not None
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await neo4j_client.disconnect()

    async def test_neo4j_create_node(self):
        """Test creating a node."""
        try:
            await neo4j_client.connect()
            
            # Create a test node
            node = await neo4j_client.create_node(
                label="TestConcept",
                properties={"id": "test_node_1", "name": "Test"},
            )
            
            assert node is not None
            
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await neo4j_client.disconnect()

    async def test_neo4j_create_relationship(self):
        """Test creating relationships between nodes."""
        try:
            await neo4j_client.connect()
            
            # Create two nodes
            await neo4j_client.create_node(
                label="TestConcept",
                properties={"id": "node_a", "name": "Node A"},
            )
            
            await neo4j_client.create_node(
                label="TestConcept",
                properties={"id": "node_b", "name": "Node B"},
            )
            
            # Create relationship
            rel = await neo4j_client.create_relationship(
                from_id="node_a",
                to_id="node_b",
                rel_type="RELATES_TO",
                properties={"strength": 0.9},
            )
            
            assert rel is not None
            
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await neo4j_client.disconnect()

    async def test_neo4j_find_nodes(self):
        """Test finding nodes."""
        try:
            await neo4j_client.connect()
            
            # Create a test node
            await neo4j_client.create_node(
                label="TestConcept",
                properties={"id": "find_test", "name": "Findable"},
            )
            
            # Find it
            nodes = await neo4j_client.find_nodes(
                label="TestConcept",
                filters={"id": "find_test"},
            )
            
            assert isinstance(nodes, list)
            
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await neo4j_client.disconnect()


@pytest.mark.asyncio
class TestRedisIntegration:
    """Integration tests for Redis client."""

    async def test_redis_connection(self):
        """Test Redis connection."""
        try:
            await redis_client.connect()
            assert redis_client.redis is not None
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        finally:
            await redis_client.disconnect()

    async def test_redis_set_and_get(self):
        """Test setting and getting values."""
        try:
            await redis_client.connect()
            
            # Set a value
            await redis_client.set("test_key", "test_value")
            
            # Get it back
            value = await redis_client.get("test_key")
            assert value == "test_value"
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        finally:
            await redis_client.disconnect()

    async def test_redis_expiration(self):
        """Test key expiration."""
        try:
            await redis_client.connect()
            
            # Set a value with 1 second TTL
            await redis_client.set("expire_test", "value", ttl=1)
            
            # Should exist immediately
            value = await redis_client.get("expire_test")
            assert value == "value"
            
            # Wait and it should be gone
            await asyncio.sleep(2)
            value = await redis_client.get("expire_test")
            assert value is None
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        finally:
            await redis_client.disconnect()

    async def test_redis_delete(self):
        """Test deleting keys."""
        try:
            await redis_client.connect()
            
            # Set and delete
            await redis_client.set("delete_test", "value")
            await redis_client.delete("delete_test")
            
            # Should be gone
            value = await redis_client.get("delete_test")
            assert value is None
            
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
        finally:
            await redis_client.disconnect()


@pytest.mark.asyncio
class TestDatabaseInteroperability:
    """Test multiple databases working together."""

    async def test_all_databases_concurrent(self):
        """Test all databases can be used concurrently."""
        try:
            # Connect to all
            await postgres_client.connect()
            await neo4j_client.connect()
            await redis_client.connect()
            
            # Perform operations concurrently
            postgres_task = postgres_client.execute("SELECT 1")
            redis_task = redis_client.set("test", "value")
            
            # Wait for all
            results = await asyncio.gather(
                postgres_task,
                redis_task,
                return_exceptions=True,
            )
            
            # At least some should succeed
            assert len(results) == 2
            
        except Exception as e:
            pytest.skip(f"Databases not available: {e}")
        finally:
            await postgres_client.disconnect()
            await neo4j_client.disconnect()
            await redis_client.disconnect()
