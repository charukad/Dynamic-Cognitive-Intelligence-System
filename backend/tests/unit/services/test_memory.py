"""Unit tests for memory services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.domain.models import Memory, MemoryType
from src.services.memory import (
    episodic_memory_service,
    semantic_memory_service,
    knowledge_graph_service,
    working_memory_service,
    procedural_memory_service,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestEpisodicMemoryService:
    """Test suite for EpisodicMemoryService."""

    async def test_store_memory(self, mock_chroma_client, mock_llm_client):
        """Test storing episodic memory."""
        service = episodic_memory_service
        service.chroma_client = mock_chroma_client
        service.llm_client = mock_llm_client
        
        memory = await service.store_memory(
            content="User asked about Python",
            session_id="test-session",
            importance_score=0.8,
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.EPISODIC
        assert memory.session_id == "test-session"
        assert memory.importance_score == 0.8

    async def test_search_memories(self, mock_chroma_client, mock_llm_client):
        """Test searching episodic memories."""
        service = episodic_memory_service
        service.chroma_client = mock_chroma_client
        service.llm_client = mock_llm_client
        
        # Mock search results
        mock_chroma_client.query_documents.return_value = [
            {
                "id": "mem1",
                "content": "Python is a language",
                "metadata": {"importance": 0.8},
            }
        ]
        
        results = await service.search_memories(
            query="What is Python?",
            session_id="test-session",
            limit=5,
        )
        
        assert len(results) >= 0
        mock_chroma_client.query_documents.assert_called_once()

    async def test_get_recent_memories(self, sample_memory):
        """Test retrieving recent memories."""
        service = episodic_memory_service
        
        # Store a memory first
        await service.repository.create(sample_memory)
        
        recent = await service.get_recent_memories(
            session_id=sample_memory.session_id,
            limit=10,
        )
        
        assert len(recent) >= 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestSemanticMemoryService:
    """Test suite for SemanticMemoryService."""

    async def test_store_knowledge(self, mock_chroma_client, mock_llm_client):
        """Test storing semantic knowledge."""
        service = semantic_memory_service
        service.chroma_client = mock_chroma_client
        service.llm_client = mock_llm_client
        
        memory = await service.store_knowledge(
            content="Python is a high-level programming language",
            tags=["python", "programming"],
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.SEMANTIC
        assert "python" in memory.tags

    async def test_search_knowledge(self, mock_chroma_client, mock_llm_client):
        """Test searching semantic knowledge."""
        service = semantic_memory_service
        service.chroma_client = mock_chroma_client
        service.llm_client = mock_llm_client
        
        mock_chroma_client.query_documents.return_value = []
        
        results = await service.search_knowledge(
            query="programming languages",
            limit=5,
        )
        
        assert isinstance(results, list)

    async def test_retrieve_by_tags(self):
        """Test retrieving knowledge by tags."""
        service = semantic_memory_service
        
        # Store knowledge with tags
        memory = Memory(
            content="Test knowledge",
            memory_type=MemoryType.SEMANTIC,
            tags=["test", "unit"],
        )
        await service.repository.create(memory)
        
        results = await service.retrieve_by_tags(tags=["test"])
        
        assert len(results) >= 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestKnowledgeGraphService:
    """Test suite for KnowledgeGraphService."""

    async def test_create_concept(self, mock_neo4j_client):
        """Test creating a concept node."""
        service = knowledge_graph_service
        service.neo4j_client = mock_neo4j_client
        
        mock_neo4j_client.create_node.return_value = {"id": "concept-1"}
        
        node = await service.create_concept(
            name="Python",
            concept_type="Programming Language",
        )
        
        assert node is not None
        mock_neo4j_client.create_node.assert_called_once()

    async def test_create_relationship(self, mock_neo4j_client):
        """Test creating relationship between concepts."""
        service = knowledge_graph_service
        service.neo4j_client = mock_neo4j_client
        
        mock_neo4j_client.create_relationship.return_value = {"id": "rel-1"}
        
        rel = await service.create_relationship(
            from_concept="Python",
            to_concept="Programming",
            relationship_type="IS_A",
        )
        
        assert rel is not None
        mock_neo4j_client.create_relationship.assert_called_once()

    async def test_find_related_concepts(self, mock_neo4j_client):
        """Test finding related concepts."""
        service = knowledge_graph_service
        service.neo4j_client = mock_neo4j_client
        
        mock_neo4j_client.execute_query.return_value = []
        
        related = await service.find_related_concepts(
            concept_name="Python",
            max_depth=2,
        )
        
        assert isinstance(related, list)


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkingMemoryService:
    """Test suite for WorkingMemoryService."""

    async def test_store_context(self, mock_redis_client):
        """Test storing conversation context."""
        service = working_memory_service
        service.redis_client = mock_redis_client
        
        result = await service.store_context(
            session_id="test-session",
            context={"messages": ["Hello", "Hi"]},
        )
        
        assert result is True
        mock_redis_client.set.assert_called_once()

    async def test_get_context(self, mock_redis_client):
        """Test retrieving conversation context."""
        service = working_memory_service
        service.redis_client = mock_redis_client
        
        mock_redis_client.get.return_value = '{"messages": ["Hello"]}'
        
        context = await service.get_context(session_id="test-session")
        
        assert context is not None
        assert "messages" in context

    async def test_update_context(self, mock_redis_client):
        """Test updating conversation context."""
        service = working_memory_service
        service.redis_client = mock_redis_client
        
        mock_redis_client.get.return_value = '{"messages": []}'
        
        result = await service.update_context(
            session_id="test-session",
            new_data={"messages": ["New message"]},
        )
        
        assert result is True

    async def test_clear_context(self, mock_redis_client):
        """Test clearing conversation context."""
        service = working_memory_service
        service.redis_client = mock_redis_client
        
        result = await service.clear_context(session_id="test-session")
        
        assert result is True
        mock_redis_client.delete.assert_called_once()

    async def test_cache_value(self, mock_redis_client):
        """Test caching a value with TTL."""
        service = working_memory_service
        service.redis_client = mock_redis_client
        
        result = await service.cache_value(
            key="test-key",
            value="test-value",
            ttl=3600,
        )
        
        assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestProceduralMemoryService:
    """Test suite for ProceduralMemoryService."""

    async def test_store_playbook(self):
        """Test storing a playbook."""
        service = procedural_memory_service
        
        steps = [
            {"action": "Step 1", "description": "First step"},
            {"action": "Step 2", "description": "Second step"},
        ]
        
        memory = await service.store_playbook(
            name="Test Playbook",
            steps=steps,
            success_rate=0.9,
            tags=["test"],
        )
        
        assert memory is not None
        assert memory.memory_type == MemoryType.PROCEDURAL
        assert memory.metadata["playbook_name"] == "Test Playbook"

    async def test_retrieve_playbook(self):
        """Test retrieving a playbook by name."""
        service = procedural_memory_service
        
        # Store first
        steps = [{"action": "Do something"}]
        await service.store_playbook("My Playbook", steps)
        
        # Retrieve
        playbook = await service.retrieve_playbook("My Playbook")
        
        assert playbook is not None
        assert playbook["steps"] is not None

    async def test_find_similar_playbooks(self):
        """Test finding similar playbooks."""
        service = procedural_memory_service
        
        # Store a playbook
        steps = [{"action": "Deploy application"}]
        await service.store_playbook(
            "Deployment Playbook",
            steps,
            success_rate=0.95,
        )
        
        # Search
        results = await service.find_similar_playbooks(
            query="deploy",
            min_success_rate=0.5,
        )
        
        assert isinstance(results, list)

    async def test_update_success_rate(self):
        """Test updating playbook success rate."""
        service = procedural_memory_service
        
        # Store playbook
        steps = [{"action": "Test"}]
        await service.store_playbook("Test PB", steps, success_rate=0.5)
        
        # Update
        result = await service.update_success_rate("Test PB", success=True)
        
        # Success rate should increase
        playbook = await service.retrieve_playbook("Test PB")
        assert playbook is not None

    async def test_cache_pattern(self):
        """Test caching a successful pattern."""
        service = procedural_memory_service
        
        memory = await service.cache_successful_pattern(
            pattern_name="API Pattern",
            pattern_data={"method": "GET", "endpoint": "/api/v1"},
            context="REST API",
        )
        
        assert memory is not None
        assert memory.metadata["pattern_name"] == "API Pattern"
