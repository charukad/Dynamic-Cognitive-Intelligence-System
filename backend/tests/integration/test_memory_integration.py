"""Integration tests for memory systems."""

import pytest
from unittest.mock import AsyncMock

from src.domain.models import Memory, MemoryType
from src.services.memory import (
    episodic_memory_service,
    semantic_memory_service,
    knowledge_graph_service,
    working_memory_service,
    procedural_memory_service,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestMemoryIntegration:
    """Integration tests for memory system interactions."""

    async def test_episodic_to_semantic_flow(
        self,
        mock_chroma_client,
        mock_llm_client,
    ):
        """Test flow from episodic to semantic memory."""
        # Store episodic memory
        episodic = episodic_memory_service
        episodic.chroma_client = mock_chroma_client
        episodic.llm_client = mock_llm_client
        
        memory = await episodic.store_memory(
            content="Python is a programming language used for AI",
            session_id="integration-test",
            importance_score=0.9,
        )
        
        assert memory is not None
        
        # Promote to semantic memory
        semantic = semantic_memory_service
        semantic.chroma_client = mock_chroma_client
        semantic.llm_client = mock_llm_client
        
        semantic_memory = await semantic.store_knowledge(
            content=memory.content,
            tags=["python", "programming", "ai"],
        )
        
        assert semantic_memory is not None
        assert semantic_memory.memory_type == MemoryType.SEMANTIC

    async def test_working_memory_to_episodic(
        self,
        mock_redis_client,
        mock_chroma_client,
        mock_llm_client,
    ):
        """Test converting working memory context to episodic."""
        # Store in working memory
        working = working_memory_service
        working.redis_client = mock_redis_client
        
        session_id = "wm-test-session"
        context = {
            "messages": [
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a language"},
            ]
        }
        
        await working.store_context(session_id, context)
        
        # Retrieve and store as episodic
        retrieved_context = await working.get_context(session_id)
        
        episodic = episodic_memory_service
        episodic.chroma_client = mock_chroma_client
        episodic.llm_client = mock_llm_client
        
        memory = await episodic.store_memory(
            content=str(retrieved_context),
            session_id=session_id,
            importance_score=0.7,
        )
        
        assert memory is not None

    async def test_knowledge_graph_integration(
        self,
        mock_neo4j_client,
        mock_chroma_client,
        mock_llm_client,
    ):
        """Test integrating semantic memory with knowledge graph."""
        # Store semantic knowledge
        semantic = semantic_memory_service
        semantic.chroma_client = mock_chroma_client
        semantic.llm_client = mock_llm_client
        
        memory = await semantic.store_knowledge(
            content="Python is used for machine learning",
            tags=["python", "ml"],
        )
        
        # Create knowledge graph nodes
        kg = knowledge_graph_service
        kg.neo4j_client = mock_neo4j_client
        
        mock_neo4j_client.create_node.return_value = {"id": "node1"}
        mock_neo4j_client.create_relationship.return_value = {"id": "rel1"}
        
        python_node = await kg.create_concept("Python", "Language")
        ml_node = await kg.create_concept("Machine Learning", "Field")
        
        relationship = await kg.create_relationship(
            from_concept="Python",
            to_concept="Machine Learning",
            relationship_type="USED_FOR",
        )
        
        assert python_node is not None
        assert ml_node is not None
        assert relationship is not None

    async def test_procedural_memory_caching(
        self,
        mock_redis_client,
    ):
        """Test procedural memory with caching."""
        procedural = procedural_memory_service
        
        # Store playbook
        steps = [
            {"action": "analyze", "description": "Analyze requirements"},
            {"action": "design", "description": "Design solution"},
            {"action": "implement", "description": "Write code"},
        ]
        
        memory = await procedural.store_playbook(
            name="Software Development",
            steps=steps,
            success_rate=0.95,
        )
        
        assert memory is not None
        
        # Cache successful pattern
        cached = await procedural.cache_successful_pattern(
            pattern_name="TDD Pattern",
            pattern_data={"approach": "test-driven"},
            context="software development",
        )
        
        assert cached is not None

    async def test_multi_memory_search(
        self,
        mock_chroma_client,
        mock_llm_client,
        mock_neo4j_client,
    ):
        """Test searching across multiple memory types."""
        query = "Python programming"
        
        # Search episodic
        episodic = episodic_memory_service
        episodic.chroma_client = mock_chroma_client
        episodic.llm_client = mock_llm_client
        
        mock_chroma_client.query_documents.return_value = []
        
        episodic_results = await episodic.search_memories(
            query=query,
            session_id="test",
            limit=5,
        )
        
        # Search semantic
        semantic = semantic_memory_service
        semantic.chroma_client = mock_chroma_client
        semantic.llm_client = mock_llm_client
        
        semantic_results = await semantic.search_knowledge(
            query=query,
            limit=5,
        )
        
        # Search knowledge graph
        kg = knowledge_graph_service
        kg.neo4j_client = mock_neo4j_client
        
        mock_neo4j_client.execute_query.return_value = []
        
        kg_results = await kg.find_related_concepts(
            concept_name="Python",
            max_depth=2,
        )
        
        # Should have results from all systems
        assert isinstance(episodic_results, list)
        assert isinstance(semantic_results, list)
        assert isinstance(kg_results, list)

    async def test_memory_consolidation(
        self,
        mock_chroma_client,
        mock_llm_client,
    ):
        """Test consolidating episodic to semantic memory."""
        episodic = episodic_memory_service
        episodic.chroma_client = mock_chroma_client
        episodic.llm_client = mock_llm_client
        
        # Store multiple episodic memories
        memories = []
        for i in range(5):
            mem = await episodic.store_memory(
                content=f"Python fact {i}",
                session_id="consolidation-test",
                importance_score=0.8,
            )
            memories.append(mem)
        
        # Consolidate to semantic
        semantic = semantic_memory_service
        semantic.chroma_client = mock_chroma_client
        semantic.llm_client = mock_llm_client
        
        consolidated = await semantic.store_knowledge(
            content="Consolidated Python knowledge",
            tags=["python", "consolidated"],
        )
        
        assert consolidated is not None

    async def test_session_memory_lifecycle(
        self,
        mock_redis_client,
        mock_chroma_client,
        mock_llm_client,
    ):
        """Test complete session memory lifecycle."""
        session_id = "lifecycle-test"
        
        # 1. Start with working memory
        working = working_memory_service
        working.redis_client = mock_redis_client
        
        await working.store_context(
            session_id=session_id,
            context={"user_query": "Tell me about Python"},
        )
        
        # 2. Store interaction as episodic
        episodic = episodic_memory_service
        episodic.chroma_client = mock_chroma_client
        episodic.llm_client = mock_llm_client
        
        episodic_mem = await episodic.store_memory(
            content="User asked about Python",
            session_id=session_id,
            importance_score=0.6,
        )
        
        # 3. Extract and store as semantic
        semantic = semantic_memory_service
        semantic.chroma_client = mock_chroma_client
        semantic.llm_client = mock_llm_client
        
        semantic_mem = await semantic.store_knowledge(
            content="Python is a popular language",
            tags=["python"],
        )
        
        # 4. Clear working memory
        await working.clear_context(session_id)
        
        # Verify lifecycle
        assert episodic_mem is not None
        assert semantic_mem is not None
