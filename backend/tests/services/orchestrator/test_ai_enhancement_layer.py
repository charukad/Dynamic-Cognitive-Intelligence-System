"""
Comprehensive tests for AI Enhancement Layer

Tests cover:
- Strategy pattern implementations
- Circuit breaker functionality
- Error handling and graceful degradation
- Type safety and validation
- Performance benchmarks
"""

import asyncio
import time
from typing import Dict, Any
from uuid import UUID, uuid4

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.orchestrator.ai_enhancement_layer import (
    AIEnhancementStrategy,
    AIEnhancementOrchestrator,
    PersonalizationStrategy,
    ValidationStrategy,
    CausalReasoningStrategy,
    KnowledgeDiscoveryStrategy,
    EnhancementType,
    EnhancementPriority,
    EnhancementContext,
    EnhancementResult,
    EnhancedResponse,
    AIEnhancementFactory,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def enhancement_context() -> EnhancementContext:
    """Create a sample enhancement context."""
    return EnhancementContext(
        query="What is Python?",
        response="Python is a high-level programming language known for its simplicity.",
        session_id="test-session-123",
        user_id=uuid4(),
        task_type="general",
        metadata={"test": True},
    )


@pytest.fixture
def mock_persona_extractor():
    """Mock PersonaExtractor for testing."""
    mock = AsyncMock()
    mock.extract_persona.return_value = {
        "communication_style": "professional",
        "expertise_level": "intermediate",
    }
    return mock


@pytest.fixture
def mock_style_transfer():
    """Mock StyleTransfer for testing."""
    mock = AsyncMock()
    mock.apply_style.return_value = "Python is a high-level programming language."
    return mock


@pytest.fixture
def mock_personality_model():
    """Mock PersonalityModel for testing."""
    mock = AsyncMock()
    mock.get_personality_profile.return_value = {
        "communication_style": "professional",
        "openness": 0.8,
        "conscientiousness": 0.9,
    }
    return mock


@pytest.fixture
def mock_contradiction_detector():
    """Mock ContradictionDetector for testing."""
    mock = AsyncMock()
    mock.detect_contradictions.return_value = []
    return mock


@pytest.fixture
def mock_consistency_checker():
    """Mock ConsistencyChecker for testing."""
    mock = AsyncMock()
    mock.check_consistency.return_value = {
        "score": 0.95,
        "suggestions": [],
    }
    return mock


# ============================================================================
# Unit Tests: Enhancement Strategies
# ============================================================================

class TestPersonalizationStrategy:
    """Test PersonalizationStrategy implementation."""
    
    @pytest.mark.asyncio
    async def test_successful_personalization(
        self,
        enhancement_context: EnhancementContext,
        mock_persona_extractor,
        mock_style_transfer,
        mock_personality_model,
    ):
        """Test successful personalization enhancement."""
        strategy = PersonalizationStrategy(
            persona_extractor=mock_persona_extractor,
            style_transfer=mock_style_transfer,
            personality_model=mock_personality_model,
        )
        
        result = await strategy.enhance(enhancement_context)
        
        assert result.success is True
        assert result.enhancement_type == EnhancementType.PERSONALIZATION
        assert result.data is not None
        assert "persona" in result.data
        assert "enhanced_response" in result.data
        
        # Verify service calls
        mock_persona_extractor.extract_persona.assert_called_once()
        mock_personality_model.get_personality_profile.assert_called_once()
        mock_style_transfer.apply_style.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_no_user_id_skips_personalization(
        self,
        mock_persona_extractor,
        mock_style_transfer,
        mock_personality_model,
    ):
        """Test personalization is skipped when no user_id."""
        context = EnhancementContext(
            query="Test query",
            response="Test response",
            session_id="test",
            user_id=None,  # No user ID
            task_type="general",
        )
        
        strategy = PersonalizationStrategy(
            persona_extractor=mock_persona_extractor,
            style_transfer=mock_style_transfer,
            personality_model=mock_personality_model,
        )
        
        result = await strategy.enhance(context)
        
        assert result.success is True
        assert result.data["style_applied"] is False
        
        # Should not call services
        mock_persona_extractor.extract_persona.assert_not_called()
        mock_style_transfer.apply_style.assert_not_called()


class TestValidationStrategy:
    """Test ValidationStrategy implementation."""
    
    @pytest.mark.asyncio
    async def test_successful_validation(
        self,
        enhancement_context: EnhancementContext,
        mock_contradiction_detector,
        mock_consistency_checker,
    ):
        """Test successful validation enhancement."""
        strategy = ValidationStrategy(
            contradiction_detector=mock_contradiction_detector,
            consistency_checker=mock_consistency_checker,
        )
        
        result = await strategy.enhance(enhancement_context)
        
        assert result.success is True
        assert result.enhancement_type == EnhancementType.VALIDATION
        assert result.data["validation_passed"] is True
        assert result.data["consistency_score"] == 0.95
        assert len(result.data["contradictions"]) == 0
    
    @pytest.mark.asyncio
    async def test_validation_fails_with_contradictions(
        self,
        enhancement_context: EnhancementContext,
        mock_contradiction_detector,
        mock_consistency_checker,
    ):
        """Test validation fails when contradictions detected."""
        # Mock contradictions detected
        mock_contradiction_detector.detect_contradictions.return_value = [
            "Statement A contradicts statement B"
        ]
        mock_consistency_checker.check_consistency.return_value = {
            "score": 0.5,
            "suggestions": ["Fix contradiction"],
        }
        
        strategy = ValidationStrategy(
            contradiction_detector=mock_contradiction_detector,
            consistency_checker=mock_consistency_checker,
        )
        
        result = await strategy.enhance(enhancement_context)
        
        assert result.success is True  # Enhancement itself succeeds
        assert result.data["validation_passed"] is False  # But validation fails
        assert len(result.data["contradictions"]) == 1
        assert result.data["consistency_score"] == 0.5


class TestCausalReasoningStrategy:
    """Test CausalReasoningStrategy implementation."""
    
    @pytest.mark.asyncio
    async def test_causal_reasoning_for_why_question(self):
        """Test causal reasoning applies to 'why' questions."""
        context = EnhancementContext(
            query="Why is the sky blue?",  # Causal query
            response="The sky appears blue due to Rayleigh scattering.",
            session_id="test",
            user_id=None,
            task_type="general",
        )
        
        # Mock causal services
        mock_graph_builder = AsyncMock()
        mock_graph_builder.build_from_text.return_value = Mock(nodes=["sky", "blue", "scattering"])
        
        mock_do_calculus = AsyncMock()
        mock_do_calculus.generate_explanation.return_value = "Causal explanation: ..."
        
        mock_counterfactual = AsyncMock()
        mock_counterfactual.generate_scenarios.return_value = [
            "If no atmosphere, sky would be black"
        ]
        
        strategy = CausalReasoningStrategy(
            causal_graph_builder=mock_graph_builder,
            do_calculus=mock_do_calculus,
            counterfactual_engine=mock_counterfactual,
        )
        
        result = await strategy.enhance(context)
        
        assert result.success is True
        assert result.data["causal_explanation"] is not None
        assert len(result.data["counterfactual_scenarios"]) > 0
    
    @pytest.mark.asyncio
    async def test_skips_non_causal_queries(self):
        """Test causal reasoning skips non-causal queries."""
        context = EnhancementContext(
            query="List Python frameworks",  # Not causal
            response="Django, Flask, FastAPI",
            session_id="test",
            user_id=None,
            task_type="general",
        )
        
        mock_graph_builder = AsyncMock()
        
        strategy = CausalReasoningStrategy(
            causal_graph_builder=mock_graph_builder,
            do_calculus=AsyncMock(),
            counterfactual_engine=AsyncMock(),
        )
        
        result = await strategy.enhance(context)
        
        assert result.success is True
        assert result.data["causal_reasoning_applied"] is False
        
        # Should not build causal graph
        mock_graph_builder.build_from_text.assert_not_called()


# ============================================================================
# Unit Tests: Circuit Breaker Pattern
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(
        self,
        enhancement_context: EnhancementContext,
    ):
        """Test circuit breaker opens after threshold failures."""
        # Create strategy that will fail
        mock_service = AsyncMock()
        mock_service.extract_persona.side_effect = RuntimeError("Service down")
        
        strategy = PersonalizationStrategy(
            persona_extractor=mock_service,
            style_transfer=AsyncMock(),
            personality_model=AsyncMock(),
        )
        
        # Trigger failures
        for _ in range(5):  # Threshold is 5
            result = await strategy.execute_with_circuit_breaker(enhancement_context)
            assert result.success is False
        
        # Circuit breaker should now be open
        assert strategy._circuit_breaker_open is True
        
        # Next call should fail fast without calling service
        call_count_before = mock_service.extract_persona.call_count
        result = await strategy.execute_with_circuit_breaker(enhancement_context)
        call_count_after = mock_service.extract_persona.call_count
        
        assert result.success is False
        assert result.error == "Circuit breaker open"
        assert call_count_before == call_count_after  # No new calls
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(
        self,
        enhancement_context: EnhancementContext,
        mock_persona_extractor,
        mock_style_transfer,
        mock_personality_model,
    ):
        """Test circuit breaker resets failure count on success."""
        strategy = PersonalizationStrategy(
            persona_extractor=mock_persona_extractor,
            style_transfer=mock_style_transfer,
            personality_model=mock_personality_model,
        )
        
        # Simulate some failures
        strategy._circuit_breaker_failures = 3
        
        # Successful call should reset
        result = await strategy.execute_with_circuit_breaker(enhancement_context)
        
        assert result.success is True
        assert strategy._circuit_breaker_failures == 0
    
    def test_manual_circuit_breaker_reset(self):
        """Test manual circuit breaker reset."""
        strategy = PersonalizationStrategy(
            persona_extractor=AsyncMock(),
            style_transfer=AsyncMock(),
            personality_model=AsyncMock(),
        )
        
        # Open circuit breaker
        strategy._circuit_breaker_open = True
        strategy._circuit_breaker_failures = 5
        
        # Reset
        strategy.reset_circuit_breaker()
        
        assert strategy._circuit_breaker_open is False
        assert strategy._circuit_breaker_failures == 0


# ============================================================================
# Integration Tests: AI Enhancement Orchestrator
# ============================================================================

class TestAIEnhancementOrchestrator:
    """Test AIEnhancementOrchestrator integration."""
    
    @pytest.mark.asyncio
    async def test_parallel_enhancement_execution(
        self,
        enhancement_context: EnhancementContext,
    ):
        """Test all enhancements execute in parallel."""
        # Create mock strategies
        strategies = []
        for i in range(4):
            strategy = Mock(spec=AIEnhancementStrategy)
            strategy.priority = EnhancementPriority(i + 1)
            strategy.execute_with_circuit_breaker = AsyncMock(
                return_value=EnhancementResult(
                    enhancement_type=EnhancementType.VALIDATION,
                    success=True,
                    data={"test": True},
                )
            )
            strategies.append(strategy)
        
        orchestrator = AIEnhancementOrchestrator(
            strategies=strategies,
            enable_parallel=True,
        )
        
        start_time = time.perf_counter()
        
        result = await orchestrator.enhance_response(
            query=enhancement_context.query,
            response=enhancement_context.response,
            session_id=enhancement_context.session_id,
            user_id=enhancement_context.user_id,
        )
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        # All strategies should have been called
        for strategy in strategies:
            strategy.execute_with_circuit_breaker.assert_called_once()
        
        # Parallel execution should be fast
        assert execution_time < 100  # Should complete quickly with mocks
        
        assert isinstance(result, EnhancedResponse)
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_enhancement_failure(
        self,
        enhancement_context: EnhancementContext,
    ):
        """Test orchestrator continues even if enhancements fail."""
        # Create failing strategy
        failing_strategy = Mock(spec=AIEnhancementStrategy)
        failing_strategy.priority = EnhancementPriority.HIGH
        failing_strategy.execute_with_circuit_breaker = AsyncMock(
            return_value=EnhancementResult(
                enhancement_type=EnhancementType.PERSONALIZATION,
                success=False,
                data=None,
                error="Service unavailable",
            )
        )
        
        # Create successful strategy
        success_strategy = Mock(spec=AIEnhancementStrategy)
        success_strategy.priority = EnhancementPriority.MEDIUM
        success_strategy.execute_with_circuit_breaker = AsyncMock(
            return_value=EnhancementResult(
                enhancement_type=EnhancementType.VALIDATION,
                success=True,
                data={"validation_passed": True, "consistency_score": 1.0},
            )
        )
        
        orchestrator = AIEnhancementOrchestrator(
            strategies=[failing_strategy, success_strategy],
        )
        
        # Should not raise exception
        result = await orchestrator.enhance_response(
            query=enhancement_context.query,
            response=enhancement_context.response,
        )
        
        assert isinstance(result, EnhancedResponse)
        # Should still have validation data from successful strategy
        assert result.consistency_score == 1.0


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance benchmarks for enhancement layer."""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_enhancement_latency_under_500ms(self):
        """Test enhancement completes in <500ms (P95)."""
        # Create lightweight mock strategies
        strategies = [
            Mock(
                spec=AIEnhancementStrategy,
                priority=EnhancementPriority(i + 1),
                execute_with_circuit_breaker=AsyncMock(
                    return_value=EnhancementResult(
                        enhancement_type=EnhancementType.VALIDATION,
                        success=True,
                        data={},
                    )
                ),
            )
            for i in range(4)
        ]
        
        orchestrator = AIEnhancementOrchestrator(strategies=strategies)
        
        # Run 100 iterations
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            
            await orchestrator.enhance_response(
                query="Test query",
                response="Test response",
            )
            
            latencies.append((time.perf_counter() - start) * 1000)
        
        # Calculate P95
        latencies.sort()
        p95 = latencies[94]  # 95th percentile
        
        assert p95 < 500, f"P95 latency {p95:.2f}ms exceeds 500ms threshold"


# ============================================================================
# Type Safety Tests
# ============================================================================

class TestTypeSafety:
    """Test type safety and validation."""
    
    def test_enhanced_response_validation(self):
        """Test EnhancedResponse validates consistency_score."""
        # Valid score
        response = EnhancedResponse(
            original_response="Test",
            enhanced_response="Test",
            consistency_score=0.85,
        )
        assert response.consistency_score == 0.85
        
        # Invalid score should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            EnhancedResponse(
                original_response="Test",
                enhanced_response="Test",
                consistency_score=1.5,  # Invalid: > 1.0
            )
    
    def test_enhancement_context_to_dict(self):
        """Test EnhancementContext serialization."""
        context = EnhancementContext(
            query="Test",
            response="Test",
            session_id="123",
            user_id=uuid4(),
            task_type="general",
            metadata={"key": "value"},
        )
        
        context_dict = context.to_dict()
        
        assert isinstance(context_dict, dict)
        assert "query" in context_dict
        assert "user_id" in context_dict
        assert isinstance(context_dict["user_id"], str)  # UUID converted to string


# ============================================================================
# Factory Pattern Tests
# ============================================================================

class TestAIEnhancementFactory:
    """Test AIEnhancementFactory."""
    
    @patch('src.services.orchestrator.ai_enhancement_layer.persona_extractor')
    @patch('src.services.orchestrator.ai_enhancement_layer.style_transfer')
    @patch('src.services.orchestrator.ai_enhancement_layer.personality_model')
    def test_create_personalization_strategy(
        self,
        mock_personality,
        mock_style,
        mock_persona,
    ):
        """Test factory creates PersonalizationStrategy."""
        strategy = AIEnhancementFactory.create_personalization_strategy()
        
        assert isinstance(strategy, PersonalizationStrategy)
        assert strategy.priority == EnhancementPriority.HIGH
    
    @patch('src.services.orchestrator.ai_enhancement_layer.contradiction_detector')
    @patch('src.services.orchestrator.ai_enhancement_layer.consistency_checker')
    def test_create_validation_strategy(
        self,
        mock_consistency,
        mock_contradiction,
    ):
        """Test factory creates ValidationStrategy."""
        strategy = AIEnhancementFactory.create_validation_strategy()
        
        assert isinstance(strategy, ValidationStrategy)
        assert strategy.priority == EnhancementPriority.CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
