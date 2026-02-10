"""
AI Enhancement Layer for Meta-Orchestrator

Enterprise-grade integration of Phase 13 advanced AI features:
- Mirror Protocol (User Personalization)
- Contrastive Learning (Response Validation)
- Causal Reasoning (Explanations)
- Graph Neural Networks (Knowledge Discovery)

Design Patterns:
- Strategy Pattern for enhancement selection
- Dependency Injection for testability
- Factory Pattern for enhancement instantiation
- Circuit Breaker for fault tolerance

Architecture:
- SOLID principles compliance
- Type safety with Pydantic
- Comprehensive error handling
- Graceful degradation
- Performance monitoring
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.core import get_logger
from src.services.advanced.causal import (
    CausalGraphBuilder,
    DoCalculus,
    CounterfactualEngine,
)
from src.services.advanced.contrastive import (
    ContradictionDetector,
    ConsistencyChecker,
)
from src.services.advanced.gnn import (
    GNNService,
    NodeEmbedder as KnowledgeGraphEmbedder,  # Alias
    MultiHopReasoner,
)
from src.services.advanced.mirror import (
    PersonaExtractor,
    StyleTransfer,
    PersonalityModel,
)

logger = get_logger(__name__)

T = TypeVar('T')


# ============================================================================
# Domain Models (Type-Safe)
# ============================================================================

class EnhancementType(str, Enum):
    """Types of AI enhancements."""
    PERSONALIZATION = "personalization"
    VALIDATION = "validation"
    CAUSAL_REASONING = "causal_reasoning"
    KNOWLEDGE_DISCOVERY = "knowledge_discovery"


class EnhancementPriority(int, Enum):
    """Enhancement execution priority."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class EnhancementContext:
    """Context for AI enhancement processing."""
    query: str
    response: str
    session_id: Optional[str]
    user_id: Optional[UUID]
    task_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "response": self.response,
            "session_id": self.session_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "task_type": self.task_type,
            "metadata": self.metadata,
        }


@dataclass
class EnhancementResult(Generic[T]):
    """Result from an AI enhancement."""
    enhancement_type: EnhancementType
    success: bool
    data: Optional[T]
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if enhancement succeeded."""
        return self.success and self.data is not None


class EnhancedResponse(BaseModel):
    """Enhanced response with all AI improvements."""
    
    original_response: str = Field(..., description="Original agent response")
    enhanced_response: str = Field(..., description="AI-enhanced response")
    
    # Mirror Protocol results
    persona_profile: Optional[Dict[str, Any]] = Field(None, description="User persona")
    style_applied: bool = Field(False, description="Whether style transfer applied")
    
    # Contrastive Learning results
    contradictions_found: List[str] = Field(default_factory=list)
    consistency_score: float = Field(1.0, ge=0.0, le=1.0)
    validation_passed: bool = Field(True)
    
    # Causal Reasoning results
    causal_explanation: Optional[str] = Field(None)
    counterfactual_scenarios: List[str] = Field(default_factory=list)
    
    # GNN results
    related_concepts: List[str] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)
    
    # Performance metrics
    total_enhancement_time_ms: float = Field(0.0)
    enhancements_applied: List[str] = Field(default_factory=list)
    
    @validator('consistency_score')
    def validate_consistency_score(cls, v: float) -> float:
        """Validate consistency score is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Consistency score must be between 0.0 and 1.0")
        return v


# ✅ NEW: Circuit Breaker States
class CircuitBreakerState(str, Enum):
    """Circuit breaker states for fault tolerance."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing fast, not executing
    HALF_OPEN = "half_open"  # Testing if system recovered


# ============================================================================
# Strategy Pattern: Enhancement Strategies
# ============================================================================

class AIEnhancementStrategy(ABC):
    """
    Abstract base class for AI enhancement strategies.
    
    Implements Strategy Pattern for pluggable enhancements.
    ✅ Updated: Added auto-reset circuit breaker with HALF_OPEN state.
    """
    
    def __init__(
        self,
        priority: EnhancementPriority = EnhancementPriority.MEDIUM,
        reset_timeout_seconds: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.priority = priority
        
        # Circuit breaker configuration
        self._cb_failures = 0
        self._cb_threshold = 5
        self._cb_state = CircuitBreakerState.CLOSED
        self._cb_opened_at: Optional[float] = None
        self._cb_reset_timeout = reset_timeout_seconds
        self._cb_half_open_successes = 0
        self._cb_half_open_max_calls = half_open_max_calls
    
    @property
    @abstractmethod
    def enhancement_type(self) -> EnhancementType:
        """Get enhancement type."""
        pass
    
    @abstractmethod
    async def enhance(self, context: EnhancementContext) -> EnhancementResult:
        """
        Apply AI enhancement to the context.
        
        Args:
            context: Enhancement context
            
        Returns:
            Enhancement result
        """
        pass
    
    async def execute_with_circuit_breaker(
        self,
        context: EnhancementContext,
    ) -> EnhancementResult:
        """
        Execute enhancement with circuit breaker pattern.
        
        Implements fault tolerance with auto-reset:
        - CLOSED: Normal operation
        - OPEN: Fail fast after threshold failures
        - HALF_OPEN: Test recovery after timeout
        """
        # Check if we should attempt reset
        self._check_auto_reset()
        
        if self._cb_state == CircuitBreakerState.OPEN:
            logger.warning(
                f"Circuit breaker OPEN for {self.enhancement_type.value}, "
                f"skipping enhancement"
            )
            return EnhancementResult(
                enhancement_type=self.enhancement_type,
                success=False,
                data=None,
                error="Circuit breaker open",
            )
        
        try:
            start_time = time.perf_counter()
            result = await self.enhance(context)
            execution_time = (time.perf_counter() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            # Handle success based on state
            if result.success:
                self._handle_success()
            else:
                self._handle_failure()
            
            return result
            
        except Exception as e:
            logger.error(
                f"Enhancement {self.enhancement_type.value} failed: {str(e)}",
                exc_info=True,
            )
            self._handle_failure()
            
            return EnhancementResult(
                enhancement_type=self.enhancement_type,
                success=False,
                data=None,
                error=str(e),
            )
    
    def _check_auto_reset(self) -> None:
        """
        Check if circuit breaker should automatically reset.
        
        ✅ NEW: Implements auto-reset after timeout.
        """
        if self._cb_state != CircuitBreakerState.OPEN:
            return
        
        if self._cb_opened_at is None:
            return
        
        # Check if timeout has elapsed
        time_since_open = time.time() - self._cb_opened_at
        if time_since_open >= self._cb_reset_timeout:
            self._cb_state = CircuitBreakerState.HALF_OPEN
            self._cb_half_open_successes = 0
            logger.info(
                f"Circuit breaker transitioned to HALF_OPEN for "
                f"{self.enhancement_type.value} after {time_since_open:.2f}s"
            )
    
    def _handle_success(self) -> None:
        """
        Handle successful enhancement execution.
        
        ✅ UPDATED: Tracks consecutive successes in HALF_OPEN state.
        """
        if self._cb_state == CircuitBreakerState.HALF_OPEN:
            self._cb_half_open_successes += 1
            
            if self._cb_half_open_successes >= self._cb_half_open_max_calls:
                # Enough successes - close circuit breaker
                self._cb_state = CircuitBreakerState.CLOSED
                self._cb_failures = 0
                self._cb_opened_at = None
                logger.info(
                    f"Circuit breaker CLOSED for {self.enhancement_type.value} "
                    f"after {self._cb_half_open_successes} successful calls"
                )
        else:
            # Normal CLOSED state - reset failure counter
            self._cb_failures = 0
    
    def _handle_failure(self) -> None:
        """
        Handle enhancement failure for circuit breaker.
        
        ✅ UPDATED: Handles HALF_OPEN state failures.
        """
        if self._cb_state == CircuitBreakerState.HALF_OPEN:
            # Failure in HALF_OPEN - go back to OPEN
            self._cb_state = CircuitBreakerState.OPEN
            self._cb_opened_at = time.time()
            logger.warning(
                f"Circuit breaker returned to OPEN for {self.enhancement_type.value} "
                f"after failure in HALF_OPEN state"
            )
            return
        
        self._cb_failures += 1
        
        if self._cb_failures >= self._cb_threshold:
            self._cb_state = CircuitBreakerState.OPEN
            self._cb_opened_at = time.time()
            logger.error(
                f"Circuit breaker OPENED for {self.enhancement_type.value} "
                f"after {self._cb_failures} failures. Will auto-reset in "
                f"{self._cb_reset_timeout}s"
            )
    
    def reset_circuit_breaker(self) -> None:
        """
        Manually reset circuit breaker.
        
        ✅ UPDATED: Resets all state including auto-reset timer.
        """
        self._cb_state = CircuitBreakerState.CLOSED
        self._cb_failures = 0
        self._cb_opened_at = None
        self._cb_half_open_successes = 0
        logger.info(f"Circuit breaker manually RESET for {self.enhancement_type.value}")
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status.
        
        ✅ NEW: Returns detailed status for monitoring.
        """
        return {
            "state": self._cb_state.value,
            "failures": self._cb_failures,
            "threshold": self._cb_threshold,
            "opened_at": self._cb_opened_at,
            "reset_timeout": self._cb_reset_timeout,
            "half_open_successes": self._cb_half_open_successes,
        }



# ============================================================================
# Concrete Enhancement Strategies
# ============================================================================

class PersonalizationStrategy(AIEnhancementStrategy):
    """Mirror Protocol personalization enhancement."""
    
    def __init__(
        self,
        persona_extractor: PersonaExtractor,
        style_transfer: StyleTransfer,
        personality_model: PersonalityModel,
    ):
        super().__init__(priority=EnhancementPriority.HIGH)
        self._persona_extractor = persona_extractor
        self._style_transfer = style_transfer
        self._personality_model = personality_model
    
    @property
    def enhancement_type(self) -> EnhancementType:
        return EnhancementType.PERSONALIZATION
    
    async def enhance(
        self,
        context: EnhancementContext,
    ) -> EnhancementResult[Dict[str, Any]]:
        """Apply personalization to response."""
        
        if not context.user_id:
            logger.debug("No user_id provided, skipping personalization")
            return EnhancementResult(
                enhancement_type=self.enhancement_type,
                success=True,
                data={"style_applied": False},
            )
        
        # Extract user persona
        persona = await self._persona_extractor.extract_persona(
            user_id=context.user_id,
            session_id=context.session_id,
        )
        
        # Get personality traits
        personality = await self._personality_model.get_personality_profile(
            user_id=context.user_id,
        )
        
        # Apply style transfer
        enhanced_response = await self._style_transfer.apply_style(
            text=context.response,
            target_style=personality.get("communication_style", "professional"),
        )
        
        return EnhancementResult(
            enhancement_type=self.enhancement_type,
            success=True,
            data={
                "persona": persona,
                "personality": personality,
                "enhanced_response": enhanced_response,
                "style_applied": enhanced_response != context.response,
            },
        )


class ValidationStrategy(AIEnhancementStrategy):
    """Contrastive learning validation enhancement."""
    
    def __init__(
        self,
        contradiction_detector: ContradictionDetector,
        consistency_checker: ConsistencyChecker,
    ):
        super().__init__(priority=EnhancementPriority.CRITICAL)
        self._contradiction_detector = contradiction_detector
        self._consistency_checker = consistency_checker
    
    @property
    def enhancement_type(self) -> EnhancementType:
        return EnhancementType.VALIDATION
    
    async def enhance(
        self,
        context: EnhancementContext,
    ) -> EnhancementResult[Dict[str, Any]]:
        """Validate response for contradictions and consistency."""
        
        # Check for contradictions
        contradictions = await self._contradiction_detector.detect_contradictions(
            text=context.response,
            context=context.query,
        )
        
        # Check consistency
        consistency_result = await self._consistency_checker.check_consistency(
            response=context.response,
            query=context.query,
            session_id=context.session_id,
        )
        
        validation_passed = (
            len(contradictions) == 0 and
            consistency_result.get("score", 1.0) >= 0.7
        )
        
        if not validation_passed:
            logger.warning(
                f"Response validation failed: "
                f"{len(contradictions)} contradictions, "
                f"consistency score: {consistency_result.get('score', 0.0)}"
            )
        
        return EnhancementResult(
            enhancement_type=self.enhancement_type,
            success=True,
            data={
                "contradictions": contradictions,
                "consistency_score": consistency_result.get("score", 1.0),
                "validation_passed": validation_passed,
                "suggestions": consistency_result.get("suggestions", []),
            },
        )


class CausalReasoningStrategy(AIEnhancementStrategy):
    """Causal reasoning enhancement for explanations."""
    
    def __init__(
        self,
        causal_graph_builder: CausalGraphBuilder,
        do_calculus: DoCalculus,
        counterfactual_engine: CounterfactualEngine,
    ):
        super().__init__(priority=EnhancementPriority.MEDIUM)
        self._graph_builder = causal_graph_builder
        self._do_calculus = do_calculus
        self._counterfactual_engine = counterfactual_engine
    
    @property
    def enhancement_type(self) -> EnhancementType:
        return EnhancementType.CAUSAL_REASONING
    
    async def enhance(
        self,
        context: EnhancementContext,
    ) -> EnhancementResult[Dict[str, Any]]:
        """Add causal explanations to response."""
        
        # Only apply for "why" questions or causal queries
        if not self._is_causal_query(context.query):
            return EnhancementResult(
                enhancement_type=self.enhancement_type,
                success=True,
                data={"causal_reasoning_applied": False},
            )
        
        # Build causal graph
        causal_graph = await self._graph_builder.build_from_text(
            text=f"{context.query} {context.response}",
        )
        
        # Generate explanation
        explanation = await self._do_calculus.generate_explanation(
            graph=causal_graph,
            query=context.query,
        )
        
        # Generate counterfactuals
        counterfactuals = await self._counterfactual_engine.generate_scenarios(
            graph=causal_graph,
            observed_outcome=context.response,
            max_scenarios=3,
        )
        
        return EnhancementResult(
            enhancement_type=self.enhancement_type,
            success=True,
            data={
                "causal_explanation": explanation,
                "counterfactual_scenarios": counterfactuals,
                "causal_graph_nodes": len(causal_graph.nodes),
            },
        )
    
    @staticmethod
    def _is_causal_query(query: str) -> bool:
        """Check if query requires causal reasoning."""
        causal_keywords = ["why", "because", "cause", "reason", "explain"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in causal_keywords)


class KnowledgeDiscoveryStrategy(AIEnhancementStrategy):
    """GNN-based knowledge discovery enhancement."""
    
    def __init__(
        self,
        kg_embedder: KnowledgeGraphEmbedder,
        multi_hop_reasoner: MultiHopReasoner,
    ):
        super().__init__(priority=EnhancementPriority.LOW)
        self._kg_embedder = kg_embedder
        self._multi_hop_reasoner = multi_hop_reasoner
    
    @property
    def enhancement_type(self) -> EnhancementType:
        return EnhancementType.KNOWLEDGE_DISCOVERY
    
    async def enhance(
        self,
        context: EnhancementContext,
    ) -> EnhancementResult[Dict[str, Any]]:
        """Discover related knowledge using GNN."""
        
        # Extract entities from query
        entities = self._extract_entities(context.query)
        
        if not entities:
            return EnhancementResult(
                enhancement_type=self.enhancement_type,
                success=True,
                data={"related_concepts": []},
            )
        
        # Find related concepts using multi-hop reasoning
        related_concepts = await self._multi_hop_reasoner.find_related_entities(
            seed_entities=entities,
            max_hops=2,
            top_k=5,
        )
        
        # Identify knowledge gaps
        knowledge_gaps = await self._multi_hop_reasoner.identify_gaps(
            query=context.query,
            current_knowledge=entities,
        )
        
        return EnhancementResult(
            enhancement_type=self.enhancement_type,
            success=True,
            data={
                "related_concepts": related_concepts,
                "knowledge_gaps": knowledge_gaps,
                "seed_entities": entities,
            },
        )
    
    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """Simple entity extraction (replace with NER in production)."""
        import re
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        stopwords = {'The', 'This', 'That', 'What', 'How', 'Why'}
        return [w for w in set(words) if w not in stopwords and len(w) > 3]


# ============================================================================
# Factory Pattern: Enhancement Factory
# ============================================================================

class AIEnhancementFactory:
    """
    Factory for creating AI enhancement strategies.
    
    Implements Factory Pattern for centralized instantiation.
    """
    
    @staticmethod
    def create_personalization_strategy() -> PersonalizationStrategy:
        """Create personalization strategy with dependencies."""
        from src.services.advanced.mirror import (
            PersonaExtractor,
            StyleTransfer,
            PersonalityModel,
        )
        
        return PersonalizationStrategy(
            persona_extractor=PersonaExtractor(),
            style_transfer=StyleTransfer(),
            personality_model=PersonalityModel(),
        )
    
    @staticmethod
    def create_validation_strategy() -> ValidationStrategy:
        """Create validation strategy with dependencies."""
        from src.services.advanced.contrastive import (
            ContradictionDetector,
            ConsistencyChecker,
        )
        
        return ValidationStrategy(
            contradiction_detector=ContradictionDetector(),
            consistency_checker=ConsistencyChecker(),
        )
    
    @staticmethod
    def create_causal_reasoning_strategy() -> CausalReasoningStrategy:
        """Create causal reasoning strategy with dependencies."""
        from src.services.advanced.causal import (
            CausalGraphBuilder,
            DoCalculus,
            CounterfactualEngine,
        )
        
        return CausalReasoningStrategy(
            causal_graph_builder=CausalGraphBuilder(),
            do_calculus=DoCalculus(),
            counterfactual_engine=CounterfactualEngine(),
        )
    
    @staticmethod
    def create_knowledge_discovery_strategy() -> KnowledgeDiscoveryStrategy:
        """Create knowledge discovery strategy with dependencies."""
        from src.services.advanced.gnn import MultiHopReasoner
        from src.services.advanced.gnn import NodeEmbedder as KnowledgeGraphEmbedder
        
        return KnowledgeDiscoveryStrategy(
            kg_embedder=KnowledgeGraphEmbedder(),
            multi_hop_reasoner=MultiHopReasoner(),
        )


# ============================================================================
# Main Enhancement Orchestrator
# ============================================================================

class AIEnhancementOrchestrator:
    """
    Orchestrates all AI enhancements with proper error handling and monitoring.
    
    Features:
    - Strategy pattern for pluggable enhancements
    - Circuit breaker for fault tolerance
    - Parallel execution for performance
    - Comprehensive logging and monitoring
    - Graceful degradation
    """
    
    def __init__(
        self,
        strategies: Optional[List[AIEnhancementStrategy]] = None,
        enable_parallel: bool = True,
    ):
        """
        Initialize AI enhancement orchestrator.
        
        Args:
            strategies: List of enhancement strategies to apply
            enable_parallel: Whether to execute enhancements in parallel
        """
        self.strategies = strategies or self._create_default_strategies()
        self.enable_parallel = enable_parallel
        
        # Sort strategies by priority
        self.strategies.sort(key=lambda s: s.priority.value)
        
        logger.info(
            f"AI Enhancement Orchestrator initialized with "
            f"{len(self.strategies)} strategies"
        )
    
    @staticmethod
    def _create_default_strategies() -> List[AIEnhancementStrategy]:
        """Create default enhancement strategies."""
        factory = AIEnhancementFactory()
        
        return [
            factory.create_validation_strategy(),       # CRITICAL priority
            factory.create_personalization_strategy(),  # HIGH priority
            factory.create_causal_reasoning_strategy(), # MEDIUM priority
            factory.create_knowledge_discovery_strategy(), # LOW priority
        ]
    
    async def enhance_response(
        self,
        query: str,
        response: str,
        session_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        task_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnhancedResponse:
        """
        Apply all AI enhancements to a response.
        
        Args:
            query: User query
            response: Original agent response
            session_id: Optional session ID
            user_id: Optional user ID
            task_type: Type of task
            metadata: Additional metadata
            
        Returns:
            Enhanced response with all improvements
        """
        start_time = time.perf_counter()
        
        context = EnhancementContext(
            query=query,
            response=response,
            session_id=session_id,
            user_id=user_id,
            task_type=task_type,
            metadata=metadata or {},
        )
        
        # Execute enhancements
        if self.enable_parallel:
            results = await self._execute_parallel(context)
        else:
            results = await self._execute_sequential(context)
        
        # Build enhanced response
        enhanced_response = self._build_enhanced_response(
            original_response=response,
            results=results,
            total_time=time.perf_counter() - start_time,
        )
        
        logger.info(
            f"Response enhancement complete: "
            f"{len(enhanced_response.enhancements_applied)} applied, "
            f"{enhanced_response.total_enhancement_time_ms:.2f}ms"
        )
        
        return enhanced_response
    
    async def _execute_parallel(
        self,
        context: EnhancementContext,
    ) -> List[EnhancementResult]:
        """Execute all enhancements in parallel."""
        tasks = [
            strategy.execute_with_circuit_breaker(context)
            for strategy in self.strategies
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def _execute_sequential(
        self,
        context: EnhancementContext,
    ) -> List[EnhancementResult]:
        """Execute enhancements sequentially by priority."""
        results = []
        
        for strategy in self.strategies:
            result = await strategy.execute_with_circuit_breaker(context)
            results.append(result)
        
        return results
    
    def _build_enhanced_response(
        self,
        original_response: str,
        results: List[EnhancementResult],
        total_time: float,
    ) -> EnhancedResponse:
        """Build final enhanced response from all results."""
        
        enhanced_resp = original_response
        enhancements_applied = []
        
        # Aggregate results by type
        for result in results:
            if not result.is_success:
                continue
            
            enhancement_type = result.enhancement_type.value
            enhancements_applied.append(enhancement_type)
            
            # Apply enhancements
            if result.enhancement_type == EnhancementType.PERSONALIZATION:
                data = result.data or {}
                if data.get("style_applied"):
                    enhanced_resp = data.get("enhanced_response", enhanced_resp)
        
        # Extract specific enhancement data
        persona_data = self._extract_enhancement_data(
            results, EnhancementType.PERSONALIZATION
        )
        validation_data = self._extract_enhancement_data(
            results, EnhancementType.VALIDATION
        )
        causal_data = self._extract_enhancement_data(
            results, EnhancementType.CAUSAL_REASONING
        )
        gnn_data = self._extract_enhancement_data(
            results, EnhancementType.KNOWLEDGE_DISCOVERY
        )
        
        return EnhancedResponse(
            original_response=original_response,
            enhanced_response=enhanced_resp,
            persona_profile=persona_data.get("persona") if persona_data else None,
            style_applied=persona_data.get("style_applied", False) if persona_data else False,
            contradictions_found=validation_data.get("contradictions", []) if validation_data else [],
            consistency_score=validation_data.get("consistency_score", 1.0) if validation_data else 1.0,
            validation_passed=validation_data.get("validation_passed", True) if validation_data else True,
            causal_explanation=causal_data.get("causal_explanation") if causal_data else None,
            counterfactual_scenarios=causal_data.get("counterfactual_scenarios", []) if causal_data else [],
            related_concepts=gnn_data.get("related_concepts", []) if gnn_data else [],
            knowledge_gaps=gnn_data.get("knowledge_gaps", []) if gnn_data else [],
            total_enhancement_time_ms=total_time * 1000,
            enhancements_applied=enhancements_applied,
        )
    
    @staticmethod
    def _extract_enhancement_data(
        results: List[EnhancementResult],
        enhancement_type: EnhancementType,
    ) -> Optional[Dict[str, Any]]:
        """Extract data for specific enhancement type."""
        for result in results:
            if result.enhancement_type == enhancement_type and result.is_success:
                return result.data
        return None


# ============================================================================
# Singleton Instance
# ============================================================================

# Create global orchestrator instance
ai_enhancement_orchestrator = AIEnhancementOrchestrator()
