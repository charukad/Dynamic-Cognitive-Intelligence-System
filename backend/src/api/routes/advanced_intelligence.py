"""
Advanced Intelligence API - Mirror Protocol, Neurosymbolic, Temporal

Unified endpoints for cutting-edge AI capabilities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.mirror.mirror_agent import (
    default_mirror_agent,
    ReasoningTrace,
    ReflectionType,
)
from src.services.advanced.neurosymbolic.reasoner import (
    neurosymbolic_reasoner,
    SymbolicRule,
    LogicalOperator,
)
from src.services.advanced.temporal.temporal_kg import temporal_kg

router = APIRouter(prefix="/intelligence", tags=["advanced-intelligence"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ReasoningTraceRequest(BaseModel):
    """Reasoning trace for analysis."""
    task_description: str
    steps: List[Dict[str, Any]]
    final_conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)


class InferenceRequest(BaseModel):
    """Hybrid inference request."""
    query: str
    facts: List[str] = Field(default_factory=list)
    neural_context: Optional[Dict[str, float]] = None


class TemporalFactRequest(BaseModel):
    """Add temporal fact."""
    subject: str
    predicate: str
    object: str
    start_time: str  # ISO format
    end_time: Optional[str] = None  # ISO format
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TimelineRequest(BaseModel):
    """Timeline query."""
    start_time: str
    end_time: str
    entity: Optional[str] = None


# ============================================================================
# Mirror Protocol Endpoints
# ============================================================================

@router.post("/mirror/analyze")
async def analyze_reasoning(request: ReasoningTraceRequest) -> Dict[str, Any]:
    """
    Analyze reasoning trace with Mirror Protocol.
    
    Returns self-critique and improvement suggestions.
    """
    try:
        from uuid import uuid4
        
        trace = ReasoningTrace(
            id=uuid4(),
            task_description=request.task_description,
            steps=request.steps,
            final_conclusion=request.final_conclusion,
            confidence=request.confidence,
            timestamp=datetime.now(),
        )
        
        critique = default_mirror_agent.analyze_reasoning(trace)
        
        return {
            'success': True,
            'critique': critique.to_dict(),
            'original_confidence': request.confidence,
            'adjusted_confidence': max(0.0, min(1.0, request.confidence + critique.confidence_adjustment)),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reasoning analysis failed: {str(e)}"
        )


@router.get("/mirror/improvement-plan")
async def get_improvement_plan() -> Dict[str, Any]:
    """Get agent improvement plan from reflection history."""
    return default_mirror_agent.generate_improvement_plan()


class ConfidenceCalibrationRequest(BaseModel):
    """Confidence calibration request."""
    predicted: float = Field(ge=0.0, le=1.0)
    actual_correct: bool = True


@router.post("/mirror/calibrate")
async def calibrate_confidence(request: ConfidenceCalibrationRequest) -> Dict[str, Any]:
    """Calibrate confidence based on actual outcome."""
    multiplier = default_mirror_agent.calibrate_confidence(
        request.predicted, request.actual_correct
    )
    
    return {
        'predicted_confidence': request.predicted,
        'actual_outcome': request.actual_correct,
        'calibration_multiplier': multiplier,
        'suggested_confidence': request.predicted * multiplier,
    }


# ============================================================================
# Neurosymbolic Reasoning Endpoints
# ============================================================================

@router.post("/neurosymbolic/infer")
async def hybrid_inference(request: InferenceRequest) -> Dict[str, Any]:
    """Perform hybrid neural-symbolic inference."""
    try:
        # Add facts to reasoner
        for fact in request.facts:
            neurosymbolic_reasoner.add_fact(fact)
        
        # Perform inference
        result = neurosymbolic_reasoner.hybrid_inference(
            query=request.query,
            neural_context=request.neural_context,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )


@router.post("/neurosymbolic/forward-chain")
async def forward_chain(facts: List[str], max_iterations: int = 10) -> Dict[str, Any]:
    """Perform forward chaining inference."""
    # Add facts
    for fact in facts:
        neurosymbolic_reasoner.add_fact(fact)
    
    # Forward chain
    derived = neurosymbolic_reasoner.forward_chain(max_iterations)
    
    return {
        'initial_facts': len(facts),
        'derived_facts': list(derived),
        'total_facts': len(derived),
    }


@router.post("/neurosymbolic/backward-chain")
async def backward_chain(goal: str, facts: List[str], max_depth: int = 5) -> Dict[str, Any]:
    """Perform backward chaining to prove goal."""
    # Add facts
    for fact in facts:
        neurosymbolic_reasoner.add_fact(fact)
    
    # Backward chain
    proved, proof = neurosymbolic_reasoner.backward_chain(goal, max_depth)
    
    return {
        'goal': goal,
        'proved': proved,
        'proof_steps': proof,
    }


@router.get("/neurosymbolic/stats")
async def get_neurosymbolic_stats() -> Dict[str, Any]:
    """Get neurosymbolic reasoning statistics."""
    return neurosymbolic_reasoner.get_statistics()


# ============================================================================
# Temporal Knowledge Graph Endpoints
# ============================================================================

@router.post("/temporal/add-fact")
async def add_temporal_fact(request: TemporalFactRequest) -> Dict[str, Any]:
    """Add temporal fact to knowledge graph."""
    try:
        start_time = datetime.fromisoformat(request.start_time)
        end_time = datetime.fromisoformat(request.end_time) if request.end_time else None
        
        fact = temporal_kg.add_fact(
            subject=request.subject,
            predicate=request.predicate,
            obj=request.object,
            start_time=start_time,
            end_time=end_time,
            confidence=request.confidence,
        )
        
        return {'success': True, 'fact': fact.to_dict()}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add fact: {str(e)}"
        )


@router.post("/temporal/timeline")
async def get_timeline(request: TimelineRequest) -> Dict[str, Any]:
    """Get temporal timeline."""
    try:
        start = datetime.fromisoformat(request.start_time)
        end = datetime.fromisoformat(request.end_time)
        
        timeline = temporal_kg.get_timeline(start, end, request.entity)
        
        return {
            'start': request.start_time,
            'end': request.end_time,
            'entity': request.entity,
            'timeline': timeline,
            'item_count': len(timeline),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeline query failed: {str(e)}"
        )


@router.get("/temporal/query")
async def query_temporal_facts(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Query temporal facts."""
    try:
        query_time = datetime.fromisoformat(timestamp) if timestamp else None
        facts = temporal_kg.query_at_time(subject, predicate, query_time)
        
        return {
            'query_time': timestamp or datetime.now().isoformat(),
            'subject': subject,
            'predicate': predicate,
            'results': [f.to_dict() for f in facts],
            'count': len(facts),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/temporal/stats")
async def get_temporal_stats() -> Dict[str, Any]:
    """Get temporal knowledge graph statistics."""
    return temporal_kg.get_statistics()


@router.get("/temporal/reconstruct/{entity}")
async def reconstruct_state(entity: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """Reconstruct entity state at given time."""
    try:
        query_time = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        state = temporal_kg.reconstruct_state_at(entity, query_time)
        
        return state
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"State reconstruction failed: {str(e)}"
        )
