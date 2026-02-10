"""Advanced AI features API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# ✅ FIXED: Import from actual module files
from src.services.advanced.active_learning import active_learner
from src.services.advanced.agent_forge import agent_forge
from src.services.advanced.chain_of_verification import chain_of_verification

router = APIRouter(prefix="/advanced", tags=["advanced"])


# Request/Response Models

class VerificationRequest(BaseModel):
    """Chain-of-Verification request."""
    
    query: str = Field(..., min_length=1, description="Original query")
    response: str = Field(..., min_length=1, description="Response to verify")
    session_id: Optional[str] = Field(None, description="Session ID")


class ForgeAgentRequest(BaseModel):
    """Agent forge request."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    role: str = Field(..., min_length=1, description="Agent role description")
    capabilities: List[str] = Field(..., min_items=1, description="Required capabilities")
    template: str = Field(default="specialist", description="Agent template (specialist, creative, analyst, generalist)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Custom temperature")


class UncertaintyAnalysisRequest(BaseModel):
    """Active learning uncertainty analysis request."""
    
    query: str = Field(..., min_length=1, description="Query")
    response: str = Field(..., min_length=1, description="Response to analyze")


class FeedbackRefinementRequest(BaseModel):
    """Active learning feedback refinement request."""
    
    query: str = Field(..., min_length=1, description="Original query")
    response: str = Field(..., min_length=1, description="Original response")
    feedback: str = Field(..., min_length=1, description="User feedback")


# Endpoints

@router.post("/verify")
async def verify_response(request: VerificationRequest) -> dict:
    """
    Verify a response using Chain-of-Verification.
    
    Args:
        request: Verification request
        
    Returns:
        Verification results with revised response
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        result = await chain_of_verification.verify_response(
            query=request.query,
            response=request.response,
            session_id=request.session_id,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.post("/forge-agent")
async def forge_new_agent(request: ForgeAgentRequest) -> dict:
    """
    Forge a new custom agent.
    
    Args:
        request: Agent forge request
        
    Returns:
        Created agent
        
    Raises:
        HTTPException: If agent creation fails
    """
    try:
        agent = await agent_forge.forge_agent(
            name=request.name,
            role=request.role,
            capabilities=request.capabilities,
            agent_template=request.template,
            temperature=request.temperature,
        )
        
        return {
            "id": str(agent.id),
            "name": agent.name,
            "agent_type": agent.agent_type.value,
            "system_prompt": agent.system_prompt,
            "temperature": agent.temperature,
            "capabilities": agent.capabilities,
            "metadata": agent.metadata,
            "created_at": agent.created_at.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent forging failed: {str(e)}",
        )


@router.get("/forged-agents")
async def list_forged_agents() -> dict:
    """
    List all forged (custom) agents.
    
    Returns:
        List of forged agents
    """
    try:
        agents = await agent_forge.list_forged_agents()
        
        return {
            "agents": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "agent_type": a.agent_type.value,
                    "capabilities": a.capabilities,
                    "metadata": a.metadata,
                }
                for a in agents
            ],
            "count": len(agents),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/analyze-uncertainty")
async def analyze_uncertainty(request: UncertaintyAnalysisRequest) -> dict:
    """
    Analyze uncertainty in a response.
    
    Args:
        request: Uncertainty analysis request
        
    Returns:
        Uncertainty analysis with clarifying questions
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        analysis = await active_learner.analyze_uncertainty(
            query=request.query,
            response=request.response,
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Uncertainty analysis failed: {str(e)}",
        )


@router.post("/refine-with-feedback")
async def refine_with_feedback(request: FeedbackRefinementRequest) -> dict:
    """
    Refine response based on user feedback.
    
    Args:
        request: Feedback refinement request
        
    Returns:
        Refined response
        
    Raises:
        HTTPException: If refinement fails
    """
    try:
        refined_response = await active_learner.refine_with_feedback(
            query=request.query,
            response=request.response,
            user_feedback=request.feedback,
        )
        
        return {
            "original_response": request.response,
            "refined_response": refined_response,
            "feedback_applied": request.feedback,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refinement failed: {str(e)}",
        )


class StrategySimulationRequest(BaseModel):
    """Strategy simulation request."""
    
    query: str = Field(..., min_length=1, description="Problem or query to simulate")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context data")


@router.post("/simulate-strategy")
async def simulate_strategy(request: StrategySimulationRequest) -> dict:
    """
    Simulate optimal strategy using Gaia MCTS.
    
    Args:
        request: Strategy simulation request
        
    Returns:
        Recommended strategy with expected reward
        
    Raises:
        HTTPException: If simulation fails
    """
    try:
        from src.services.advanced.gaia import gaia_simulator
        
        result = await gaia_simulator.simulate_conversation_strategy(
            query=request.query,
            context=request.context or {},
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy simulation failed: {str(e)}",
        )

