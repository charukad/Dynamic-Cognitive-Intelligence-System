"""
Oneiroi API Routes

REST API for the Oneiroi dreaming system.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.core import get_logger
from src.services.advanced.oneiroi.dream_engine import dream_engine, DreamCycleResult, Insight
from src.services.advanced.oneiroi import oneiroi

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/oneiroi", tags=["oneiroi"])


# ============================================================================
# Request/Response Models
# ============================================================================

class InitiateDreamRequest(BaseModel):
    """Request to initiate dream cycle"""
    agent_id: str = Field(..., description="Agent identifier")
    experience_count: Optional[int] = Field(100, description="Number of experiences to process")
    config: Optional[dict] = Field(None, description="Dream cycle configuration")


class InitiateDreamResponse(BaseModel):
    """Response from dream cycle initiation"""
    cycle_id: UUID
    agent_id: str
    status: str = "initiated"
    eta_seconds: float
    experience_count: int


class DreamStatusResponse(BaseModel):
    """Dream cycle status response"""
    cycle_id: UUID
    agent_id: str
    phase: Optional[str]
    progress: float  # 0.0 to 1.0
    insights_count: int
    duration_seconds: float
    status: str  # running, completed, failed


class InsightResponse(BaseModel):
    """Insight response model"""
    id: UUID
    type: str
    content: str
    confidence: float
    impact_score: float
    timestamp: datetime
    applied: bool


class AgentInsightsResponse(BaseModel):
    """Agent insights response"""
    agent_id: str
    insights: List[InsightResponse]
    total_dreams: int
    total_insights: int
    avg_confidence: float


class ApplyInsightsRequest(BaseModel):
    """Request to apply insights"""
    agent_id: str
    insight_ids: List[UUID]


class DreamScheduleResponse(BaseModel):
    """Dream schedule for agents"""
    agent_id: str
    last_dream: Optional[datetime]
    next_dream: Optional[datetime]
    should_dream_now: bool
    total_dreams: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/dream/initiate/{agent_id}", response_model=InitiateDreamResponse)
async def initiate_dream(
    agent_id: str,
    request: InitiateDreamRequest,
    background_tasks: BackgroundTasks
):
    """
    Initiate a dream cycle for an agent.
    
    Starts an async dream cycle that processes recent experiences
    through REM, NREM, and Integration phases.
    """
    try:
        # Get recent experiences from replay buffer
        experiences = oneiroi.replay_buffer.sample(
            batch_size=request.experience_count or 100,
            min_reward=0.0
        )
        
        if len(experiences) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient experiences ({len(experiences)}). Need at least 10."
            )
        
        # Convert Experience objects to dicts
        exp_dicts = [
            {
                "id": exp.task_id,
                "agent_type": exp.agent_type,
                "prompt": exp.input_prompt,
                "response": exp.output_response,
                "reward": exp.reward,
                "metadata": exp.metadata,
                "context": exp.metadata.get("context", {})
            }
            for exp in experiences
        ]
        
        # Initiate dream cycle
        cycle_id = await dream_engine.initiate_dream_cycle(
            agent_id=agent_id,
            experiences=exp_dicts,
            config=request.config
        )
        
        # Estimate completion time (roughly 30-60 seconds per cycle)
        eta_seconds = min(len(exp_dicts) * 0.5, 120.0)
        
        logger.info(f"Initiated dream cycle {cycle_id} for agent {agent_id}")
        
        return InitiateDreamResponse(
            cycle_id=cycle_id,
            agent_id=agent_id,
            eta_seconds=eta_seconds,
            experience_count=len(exp_dicts)
        )
        
    except Exception as e:
        logger.error(f"Failed to initiate dream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/{cycle_id}", response_model=DreamStatusResponse)
async def get_dream_status(cycle_id: UUID):
    """
    Get the current status of a dream cycle.
    """
    cycle = dream_engine.get_cycle_status(cycle_id)
    
    if not cycle:
        raise HTTPException(status_code=404, detail="Dream cycle not found")
    
    # Determine current phase
    current_phase = None
    progress = 0.0
    
    if cycle.phases_completed:
        current_phase = cycle.phases_completed[-1].value
        progress = len(cycle.phases_completed) / 3.0  # 3 phases total
    
    status = "running" if cycle_id in dream_engine.active_cycles else \
             ("completed" if cycle.success else "failed")
    
    return DreamStatusResponse(
        cycle_id=cycle.cycle_id,
        agent_id=cycle.agent_id,
        phase=current_phase,
        progress=min(progress, 1.0),
        insights_count=len(cycle.insights_extracted),
        duration_seconds=cycle.duration_seconds,
        status=status
    )


@router.get("/insights/{agent_id}", response_model=AgentInsightsResponse)
async def get_agent_insights(
    agent_id: str,
    limit: int = 50,
    min_confidence: float = 0.0
):
    """
    Get all insights extracted for an agent.
    """
    try:
        # Get all completed cycles for agent
        agent_cycles = [
            c for c in dream_engine.completed_cycles
            if c.agent_id == agent_id
        ]
        
        # Collect all insights
        all_insights = []
        for cycle in agent_cycles:
            all_insights.extend(cycle.insights_extracted)
        
        # Filter by confidence
        filtered_insights = [
            i for i in all_insights
            if i.confidence >= min_confidence
        ]
        
        # Sort by impact score
        sorted_insights = sorted(
            filtered_insights,
            key=lambda x: x.impact_score,
            reverse=True
        )[:limit]
        
        # Calculate statistics
        avg_confidence = (
            sum(i.confidence for i in all_insights) / len(all_insights)
            if all_insights else 0.0
        )
        
        return AgentInsightsResponse(
            agent_id=agent_id,
            insights=[
                InsightResponse(
                    id=i.id,
                    type=i.type.value,
                    content=i.content,
                    confidence=i.confidence,
                    impact_score=i.impact_score,
                    timestamp=i.timestamp,
                    applied=i.applied
                )
                for i in sorted_insights
            ],
            total_dreams=len(agent_cycles),
            total_insights=len(all_insights),
            avg_confidence=avg_confidence
        )
        
    except Exception as e:
        logger.error(f"Failed to get insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/apply")
async def apply_insights(request: ApplyInsightsRequest):
    """
    Apply selected insights to an agent's knowledge base.
    """
    try:
        applied_count = 0
        
        # Find and mark insights as applied
        for cycle in dream_engine.completed_cycles:
            if cycle.agent_id != request.agent_id:
                continue
            
            for insight in cycle.insights_extracted:
                if insight.id in request.insight_ids and not insight.applied:
                    insight.applied = True
                    applied_count += 1
        
        logger.info(
            f"Applied {applied_count} insights to agent {request.agent_id}"
        )
        
        return {
            "agent_id": request.agent_id,
            "applied_count": applied_count,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to apply insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule", response_model=List[DreamScheduleResponse])
async def get_dream_schedules():
    """
    Get dream schedules for all agents.
    """
    stats = oneiroi.get_dreaming_stats()
    should_dream = await oneiroi.should_dream()
    
    # In production, track per-agent schedules
    # For now, return global schedule
    return [
        DreamScheduleResponse(
            agent_id="global",
            last_dream=oneiroi.last_dream_time,
            next_dream=None,  # Calculate based on frequency
            should_dream_now=should_dream,
            total_dreams=stats["total_dreams"]
        )
    ]


@router.get("/stats")
async def get_oneiroi_stats():
    """
    Get overall Oneiroi system statistics.
    """
    stats = oneiroi.get_dreaming_stats()
    
    # Add engine stats
    stats["engine"] = {
        "active_cycles": len(dream_engine.active_cycles),
        "completed_cycles": len(dream_engine.completed_cycles),
        "total_insights": sum(
            len(c.insights_extracted)
            for c in dream_engine.completed_cycles
        )
    }
    
    return stats
