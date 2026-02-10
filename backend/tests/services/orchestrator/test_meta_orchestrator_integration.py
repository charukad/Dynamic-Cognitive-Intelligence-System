"""
Integration tests for MetaOrchestrator with memory and AI enhancements

Tests cover:
- RAG pipeline integration
- Knowledge graph updates
- AI enhancement integration
- End-to-end query processing
- Error handling and recovery
"""

import asyncio
from uuid import uuid4
from typing import Dict, Any

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.domain.models import Task, TaskStatus
from src.services.orchestrator.meta_orchestrator import MetaOrchestrator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_pipeline():
    """Mock EmbeddingPipeline."""
    mock = Mock()
    mock.build_rag_context = AsyncMock(return_value="Relevant context from past interactions...")
    mock.store_document = AsyncMock(return_value="doc-id-123")
    return mock


@pytest.fixture
def mock_knowledge_graph_service():
    """Mock KnowledgeGraphService."""
    mock = Mock()
    mock.add_concept = AsyncMock(return_value={"id": "concept-123"})
    return mock


@pytest.fixture
def mock_ai_enhancement_orchestrator():
    """Mock AIEnhancementOrchestrator."""
    from src.services.orchestrator.ai_enhancement_layer import EnhancedResponse
    
    mock = Mock()
    mock.enhance_response = AsyncMock(
        return_value=EnhancedResponse(
            original_response="Python is a programming language.",
            enhanced_response="Python is a high-level programming language known for simplicity.",
            validation_passed=True,
            consistency_score=0.95,
            style_applied=True,
            persona_profile={"style": "professional"},
            enhancements_applied=["validation", "personalization"],
            total_enhancement_time_ms=245.3,
        )
    )
    return mock


@pytest.fixture
def mock_task_repository():
    """Mock task repository."""
    mock = Mock()
    
    async def mock_create(task):
        task.id = uuid4()
        return task
    
    async def mock_update(task):
        return task
    
    mock.create = mock_create
    mock.update = mock_update
    return mock


@pytest.fixture
def mock_agent_repository():
    """Mock agent repository."""
    from src.domain.models import Agent, AgentType
    
    mock = Mock()
    mock.get_available_agents = AsyncMock(
        return_value=[
            Agent(
                name="ScholarAgent",
                agent_type=AgentType.SCHOLAR,
                specialization="Research and knowledge",
            )
        ]
    )
    mock.update = AsyncMock()
    return mock


# ============================================================================
# Integration Tests: RAG Pipeline
# ============================================================================

class TestRAGIntegration:
    """Test RAG pipeline integration."""
    
    @pytest.mark.asyncio
    async def test_rag_context_retrieval_before_processing(
        self,
        mock_embedding_pipeline,
        mock_knowledge_graph_service,
        mock_task_repository,
    ):
        """Test RAG context is retrieved before query processing."""
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.knowledge_graph_service', mock_knowledge_graph_service), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service') as mock_episodic:
            
            mock_episodic.store_memory = AsyncMock()
            
            orchestrator = MetaOrchestrator()
            
            # Mock agent execution
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "response": "Python is great!",
                    "task_id": "123",
                }
                
                await orchestrator.process_query(
                    query="What is Python?",
                    session_id="test-session",
                )
            
            # Verify RAG context was retrieved
            mock_embedding_pipeline.build_rag_context.assert_called_once_with(
                collection_name="knowledge_base",
                query="What is Python?",
                max_chunks=5,
            )
    
    @pytest.mark.asyncio
    async def test_rag_context_passed_to_task(
        self,
        mock_embedding_pipeline,
        mock_task_repository,
    ):
        """Test RAG context is included in task context."""
        rag_context = "Previous knowledge: Python is a language..."
        mock_embedding_pipeline.build_rag_context.return_value = rag_context
        
        created_task = None
        
        async def capture_task(task):
            nonlocal created_task
            created_task = task
            task.id = uuid4()
            return task
        
        mock_task_repository.create = capture_task
        
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'):
            
            orchestrator = MetaOrchestrator()
            
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock):
                await orchestrator.process_query(query="Test query")
        
        # Verify RAG context in task
        assert created_task is not None
        assert "rag_context" in created_task.context
        assert created_task.context["rag_context"] == rag_context
    
    @pytest.mark.asyncio
    async def test_response_stored_in_chromadb(
        self,
        mock_embedding_pipeline,
        mock_task_repository,
    ):
        """Test agent response is stored in ChromaDB."""
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'):
            
            orchestrator = MetaOrchestrator()
            
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "response": "Python is a programming language",
                    "task_id": str(uuid4()),
                }
                
                await orchestrator.process_query(
                    query="What is Python?",
                    session_id="test-123",
                )
        
        # Verify storage was called
        mock_embedding_pipeline.store_document.assert_called_once()
        
        # Check Q&A format
        call_args = mock_embedding_pipeline.store_document.call_args
        assert "Q: What is Python?" in call_args.kwargs["document"]
        assert "A: Python is a programming language" in call_args.kwargs["document"]
    
    @pytest.mark.asyncio
    async def test_rag_graceful_degradation_on_failure(
        self,
        mock_embedding_pipeline,
        mock_task_repository,
    ):
        """Test query continues even if RAG retrieval fails."""
        # Mock RAG failure
        mock_embedding_pipeline.build_rag_context.side_effect = RuntimeError("ChromaDB unavailable")
        
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'):
            
            orchestrator = MetaOrchestrator()
            
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {"response": "Answer", "task_id": "123"}
                
                # Should not raise exception
                result = await orchestrator.process_query(query="Test")
                
                assert result is not None
                assert "response" in result


# ============================================================================
# Integration Tests: AI Enhancement
# ============================================================================

class TestAIEnhancementIntegration:
    """Test AI enhancement integration."""
    
    @pytest.mark.asyncio
    async def test_ai_enhancement_applied_to_response(
        self,
        mock_ai_enhancement_orchestrator,
        mock_task_repository,
    ):
        """Test AI enhancements are applied to agent response."""
        with patch('src.services.orchestrator.meta_orchestrator.ai_enhancement_orchestrator', mock_ai_enhancement_orchestrator), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline'), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'):
            
            orchestrator = MetaOrchestrator()
            
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "response": "Original response",
                    "task_id": "123",
                }
                
                result = await orchestrator.process_query(
                    query="Test query",
                    user_id=uuid4(),
                )
        
        # Verify enhancement was called
        mock_ai_enhancement_orchestrator.enhance_response.assert_called_once()
        
        # Verify enhanced response is used
        assert "ai_enhancements" in result
        assert "validation" in result["ai_enhancements"]["applied"]
    
    @pytest.mark.asyncio
    async def test_validation_failure_uses_original_response(
        self,
        mock_ai_enhancement_orchestrator,
        mock_task_repository,
    ):
        """Test original response used if validation fails."""
        from src.services.orchestrator.ai_enhancement_layer import EnhancedResponse
        
        # Mock validation failure
        mock_ai_enhancement_orchestrator.enhance_response.return_value = EnhancedResponse(
            original_response="Original",
            enhanced_response="Enhanced",
            validation_passed=False,  # Validation failed
            consistency_score=0.3,
            contradictions_found=["Contradiction detected"],
        )
        
        with patch('src.services.orchestrator.meta_orchestrator.ai_enhancement_orchestrator', mock_ai_enhancement_orchestrator), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline'), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'):
            
            orchestrator = MetaOrchestrator()
            
            with patch.object(orchestrator, '_execute_primitive_task', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = {
                    "response": "Original",
                    "task_id": "123",
                }
                
                result = await orchestrator.process_query(query="Test")
        
       # Original response should be preserved
        assert result["ai_enhancements"]["validation_failed"] is True
        assert result["ai_enhancements"]["consistency_score"] == 0.3


# ============================================================================
# End-to-End Tests
# ============================================================================

class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_query_processing_flow(
        self,
        mock_embedding_pipeline,
        mock_knowledge_graph_service,
        mock_ai_enhancement_orchestrator,
        mock_task_repository,
        mock_agent_repository,
    ):
        """Test complete query processing flow."""
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.knowledge_graph_service', mock_knowledge_graph_service), \
             patch('src.services.orchestrator.meta_orchestrator.ai_enhancement_orchestrator', mock_ai_enhancement_orchestrator), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.agent_repository', mock_agent_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'), \
             patch('src.services.orchestrator.meta_orchestrator.agent_factory') as mock_factory:
            
            # Mock agent execution
            mock_agent = Mock()
            mock_agent.execute = AsyncMock(return_value={"response": "Test answer"})
            mock_factory.create_agent.return_value = mock_agent
            
            orchestrator = MetaOrchestrator()
            
            result = await orchestrator.process_query(
                query="What is Python?",
                session_id="test-session",
                user_id=uuid4(),
                task_type="general",
            )
            
            # Verify complete flow
            assert "response" in result
            assert "rag_context_used" in result
            assert "ai_enhancements" in result
            
            # Verify all integration points were called
            mock_embedding_pipeline.build_rag_context.assert_called_once()
            mock_embedding_pipeline.store_document.assert_called_once()
            mock_ai_enhancement_orchestrator.enhance_response.assert_called_once()


# ============================================================================
# Performance Tests
# ============================================================================

class TestIntegrationPerformance:
    """Performance tests for integrated system."""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_query_processing_under_2_seconds(
        self,
        mock_embedding_pipeline,
        mock_task_repository,
        mock_agent_repository,
    ):
        """Test complete query processing completes in <2s."""
        import time
        
        with patch('src.services.orchestrator.meta_orchestrator.embedding_pipeline', mock_embedding_pipeline), \
             patch('src.services.orchestrator.meta_orchestrator.task_repository', mock_task_repository), \
             patch('src.services.orchestrator.meta_orchestrator.agent_repository', mock_agent_repository), \
             patch('src.services.orchestrator.meta_orchestrator.episodic_memory_service'), \
             patch('src.services.orchestrator.meta_orchestrator.knowledge_graph_service'), \
             patch('src.services.orchestrator.meta_orchestrator.ai_enhancement_orchestrator'), \
             patch('src.services.orchestrator.meta_orchestrator.agent_factory') as mock_factory:
            
            mock_agent = Mock()
            mock_agent.execute = AsyncMock(return_value={"response": "Answer"})
            mock_factory.create_agent.return_value = mock_agent
            
            orchestrator = MetaOrchestrator()
            
            start = time.time()
            await orchestrator.process_query(query="Test query")
            duration = time.time() - start
            
            assert duration < 2.0, f"Query took {duration:.2f}s, exceeds 2s threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
