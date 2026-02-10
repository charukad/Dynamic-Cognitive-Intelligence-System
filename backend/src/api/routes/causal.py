"""
Causal Reasoning API Endpoints

REST API for causal inference, interventions, and counterfactuals.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.advanced.causal import causal_service


router = APIRouter(prefix="/v1/causal", tags=["causal"])


# Request/Response Models
class CreateGraphRequest(BaseModel):
    """Request to create causal graph"""
    rules: Optional[List[Dict[str, str]]] = Field(None, description="Expert rules (cause → effect)")
    correlations: Optional[Dict] = Field(None, description="Correlation data")


class InterventionRequest(BaseModel):
    """Request to perform intervention"""
    variable: str = Field(..., description="Variable to intervene on")
    value: Any = Field(..., description="Value to set")
    observed: Optional[Dict[str, Any]] = Field(None, description="Observed values")


class CounterfactualRequest(BaseModel):
    """Request for counterfactual analysis"""
    actual_observations: Dict[str, Any] = Field(..., description="What actually happened")
    counterfactual_intervention: Dict[str, Any] = Field(..., description="What if this had been different")
    query_variable: str = Field(..., description="Variable to query")


class CausalEffectRequest(BaseModel):
    """Request to estimate causal effect"""
    treatment: str = Field(..., description="Treatment variable")
    outcome: str = Field(..., description="Outcome variable")
    confounders: Optional[List[str]] = Field(None, description="Confounding variables")


# Endpoints
@router.post("/graph/{graph_id}", status_code=status.HTTP_201_CREATED)
async def create_graph(graph_id: str, request: CreateGraphRequest):
    """
    Create a new causal graph from rules or correlations.
    """
    result = await causal_service.create_graph(
        graph_id,
        request.rules,
        request.correlations
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('validation', {}).get('issues', ['Invalid graph'])
        )
    
    return result


@router.get("/graph/{graph_id}", status_code=status.HTTP_200_OK)
async def get_graph(graph_id: str):
    """
    Get causal graph structure.
    """
    graph = await causal_service.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph {graph_id} not found"
        )
    
    return graph


@router.delete("/graph/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(graph_id: str):
    """
    Delete causal graph.
    """
    success = await causal_service.delete_graph(graph_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph {graph_id} not found"
        )
    
    return None


@router.get("/graphs", status_code=status.HTTP_200_OK)
async def list_graphs():
    """
    List all causal graphs.
    """
    graphs = await causal_service.list_graphs()
    
    return {"graphs": graphs, "total": len(graphs)}


@router.post("/graph/{graph_id}/intervene", status_code=status.HTTP_200_OK)
async def perform_intervention(graph_id: str, request: InterventionRequest):
    """
    Perform causal intervention do(X=x).
    
    Cuts incoming edges to X and sets it independently.
    """
    result = await causal_service.perform_intervention(
        graph_id,
        request.variable,
        request.value,
        request.observed
    )
    
    if 'error' in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result['error']
        )
    
    return result


@router.post("/graph/{graph_id}/counterfactual", status_code=status.HTTP_200_OK)
async def answer_counterfactual(graph_id: str, request: CounterfactualRequest):
    """
    Answer counterfactual "what if" question.
    
    Example: "What if X had been different? What would Y be?"
    """
    result = await causal_service.answer_counterfactual(
        graph_id,
        request.actual_observations,
        request.counterfactual_intervention,
        request.query_variable
    )
    
    if 'error' in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result['error']
        )
    
    return result


@router.post("/graph/{graph_id}/effect", status_code=status.HTTP_200_OK)
async def estimate_causal_effect(graph_id: str, request: CausalEffectRequest):
    """
    Estimate causal effect of treatment on outcome.
    
    Returns adjustment formula and identifiability analysis.
    """
    result = await causal_service.estimate_causal_effect(
        graph_id,
        request.treatment,
        request.outcome,
        request.confounders
    )
    
    if 'error' in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result['error']
        )
    
    return result
