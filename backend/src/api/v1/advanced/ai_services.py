"""
Advanced AI API Routes - Unified Endpoint

Provides centralized access to all advanced AI capabilities:
- Oneiroi dreaming
- GAIA tournaments
- Multi-modal processing
- Service status monitoring
"""

from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import base64

from src.core import get_logger
from src.services.advanced.ai_services_manager import (
    get_ai_services_manager,
    DreamCycleRequest,
    MatchRequest
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/ai-services", tags=["advanced-ai"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RunDreamRequest(BaseModel):
    """Request to run dream cycle"""
    agent_id: str
    num_experiences: int = 100
    focus_areas: List[str] = []


class RunMatchRequest(BaseModel):
    """Request to run GAIA match"""
    agent_id: str
    opponent_type: str = "synthetic"  # synthetic, historical, peer, self
    num_rounds: int = 5


class ProcessImageRequest(BaseModel):
    """Request to process image"""
    image_base64: str
    operations: List[str] = ["caption", "detect", "ocr"]


class ProcessAudioRequest(BaseModel):
    """Request to process audio"""
    audio_base64: str
    operations: List[str] = ["transcribe", "diarize", "classify"]


class SearchSimilarRequest(BaseModel):
    """Request to search similar content"""
    query_embedding: List[float]
    modality: str  # 'image' or 'audio'
    top_k: int = 5


# ============================================================================
# Oneiroi Dreaming Endpoints
# ============================================================================

@router.post("/dream/run")
async def run_dream_cycle(request: RunDreamRequest):
    """
    Execute a complete Oneiroi dream cycle.
    
    Phases:
    - REM: Hindsight experience replay
    - NREM: Pattern mining and insight extraction
    - Integration: Apply insights to agent behavior
    
    Returns:
    - Dream cycle results with insights
    - Performance improvement metrics
    - Pattern discoveries
    """
    try:
        manager = get_ai_services_manager()
        
        dream_request = DreamCycleRequest(
            agent_id=request.agent_id,
            num_experiences=request.num_experiences,
            focus_areas=request.focus_areas or None
        )
        
        result = await manager.run_dream_cycle(dream_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Dream cycle failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/insights/{agent_id}")
async def get_dream_insights(agent_id: str, limit: int = 10):
    """
    Get recent insights from dream cycles.
    
    Returns:
    - List of insights with applicability scores
    - Patterns discovered
    - Performance metrics
    """
    try:
        manager = get_ai_services_manager()
        insights = await manager.get_dream_insights(agent_id, limit)
        
        return {"agent_id": agent_id, "insights": insights}
        
    except Exception as e:
        logger.error(f"Get insights failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GAIA Tournament Endpoints
# ============================================================================

@router.post("/gaia/match")
async def run_gaia_match(request: RunMatchRequest):
    """
    Run a GAIA competitive match.
    
    Opponent types:
    - synthetic: AI-generated opponent
    - historical: Past agent versions
    - peer: Other live agents
    - self: Agent vs itself
    
    Returns:
    - Match results
    - ELO rating changes
    - Performance analysis
    """
    try:
        manager = get_ai_services_manager()
        
        match_request = MatchRequest(
            agent_id=request.agent_id,
            opponent_type=request.opponent_type,
            num_rounds=request.num_rounds
        )
        
        result = await manager.run_match(match_request)
        
        return result
        
    except Exception as e:
        logger.error(f"GAIA match failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaia/elo/{agent_id}")
async def get_agent_elo(agent_id: str):
    """
    Get current ELO rating for agent.
    
    Returns:
    - Current ELO rating
    - Rank among all agents
    - Win/loss record
    """
    try:
        manager = get_ai_services_manager()
        elo = await manager.get_agent_elo(agent_id)
        
        return {"agent_id": agent_id, "elo_rating": elo}
        
    except Exception as e:
        logger.error(f"Get ELO failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaia/history/{agent_id}")
async def get_match_history(agent_id: str, limit: int = 20):
    """
    Get recent match history.
    
    Returns:
    - List of recent matches
    - Win/loss outcomes
    - ELO progression
    """
    try:
        manager = get_ai_services_manager()
        history = await manager.get_match_history(agent_id, limit)
        
        return {"agent_id": agent_id, "matches": history}
        
    except Exception as e:
        logger.error(f"Get history failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Multi-modal Processing Endpoints
# ============================================================================

@router.post("/multimodal/image")
async def process_image(request: ProcessImageRequest):
    """
    Process image with AI operations.
    
    Operations:
    - caption: Generate descriptive caption
    - detect: Object detection with bounding boxes
    - ocr: Extract text
    - segment: Image segmentation
    
    Returns:
    - Results from requested operations
    - Generated embedding for similarity search
    """
    try:
        manager = get_ai_services_manager()
        
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)
        
        result = await manager.process_image(image_data, request.operations)
        
        return result
        
    except Exception as e:
        logger.error(f"Image processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal/audio")
async def process_audio(request: ProcessAudioRequest):
    """
    Process audio with AI operations.
    
    Operations:
    - transcribe: Speech-to-text
    - diarize: Speaker segmentation
    - classify: Sound classification
    
    Returns:
    - Results from requested operations
    - Generated embedding for similarity search
    """
    try:
        manager = get_ai_services_manager()
        
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio_base64)
        
        result = await manager.process_audio(audio_data, request.operations)
        
        return result
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal/search")
async def search_similar_content(request: SearchSimilarRequest):
    """
    Search for similar content across modalities.
    
    Uses vector similarity search on embeddings.
    
    Returns:
    - List of similar items with similarity scores
    - Metadata for each result
    """
    try:
        manager = get_ai_services_manager()
        
        results = await manager.search_similar(
            query_embedding=request.query_embedding,
            modality=request.modality,
            top_k=request.top_k
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Similarity search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Service Status Endpoint
# ============================================================================

@router.get("/status")
async def get_services_status():
    """
    Get status of all advanced AI services.
    
    Returns:
    - Status for each service (online/busy/offline)
    - Last activity timestamps
    - Success rates
    - Total requests processed
    """
    try:
        manager = get_ai_services_manager()
        status = manager.get_service_status()
        
        return {
            "services": {
                name: {
                    "service_name": s.service_name,
                    "status": s.status,
                    "last_activity": s.last_activity.isoformat(),
                    "total_requests": s.total_requests,
                    "success_rate": s.success_rate
                }
                for name, s in status.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Get status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
