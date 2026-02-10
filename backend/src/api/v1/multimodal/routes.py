"""
Multi-modal API Routes

REST API for multi-modal processing.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import base64

from src.core import get_logger
from src.services.advanced.multimodal.vision_processor import vision_processor
from src.services.advanced.multimodal.audio_processor import audio_processor
from src.services.advanced.multimodal.fusion_layer import fusion_layer, ModalityEmbedding

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/multimodal", tags=["multimodal"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ProcessImageRequest(BaseModel):
    """Request to process image"""
    image_base64: str
    include_caption: bool = True
    include_objects: bool = True
    include_ocr: bool = True


class ProcessAudioRequest(BaseModel):
    """Request to process audio"""
    audio_base64: str
    include_transcription: bool = True
    include_diarization: bool = False


class FuseEmbeddingsRequest(BaseModel):
    """Request to fuse embeddings"""
    embeddings: List[dict]  # List of {modality, vector, weight}
    strategy: str = "attention"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/vision/analyze")
async def analyze_image(request: ProcessImageRequest):
    """
    Analyze an image comprehensively.
    
    Returns:
    - Caption: Natural language description
    - Objects: Detected objects with bounding boxes
    - OCR: Extracted text
    - Embedding: CLIP embedding vector
    """
    try:
        # Decode base64
        image_data = base64.b64decode(request.image_base64)
        
        # Process image
        analysis = await vision_processor.process_image(
            image_data=image_data,
            include_caption=request.include_caption,
            include_objects=request.include_objects,
            include_ocr=request.include_ocr,
            include_embedding=True
        )
        
        return {
            "caption": analysis.caption,
            "objects": [obj.dict() for obj in analysis.objects],
            "ocr_text": analysis.ocr_text,
            "embedding": analysis.embedding.dict() if analysis.embedding else None,
            "metadata": analysis.metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/transcribe")
async def transcribe_audio(request: ProcessAudioRequest):
    """
    Transcribe audio to text.
    
    Returns:
    - Transcription: Speech-to-text
    - Speakers: Speaker diarization (who spoke when)
    - Language: Detected language
    - Embedding: Audio embedding vector
    """
    try:
        # Decode base64
        audio_data = base64.b64decode(request.audio_base64)
        
        # Process audio
        analysis = await audio_processor.process_audio(
            audio_data=audio_data,
            include_transcription=request.include_transcription,
            include_diarization=request.include_diarization,
            include_embedding=True
        )
        
        return {
            "transcription": analysis.transcription.dict() if analysis.transcription else None,
            "embedding": analysis.embedding.dict() if analysis.embedding else None,
            "sound_classes": analysis.sound_classes,
            "metadata": analysis.metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fusion/combine")
async def fuse_embeddings(request: FuseEmbeddingsRequest):
    """
    Fuse embeddings from multiple modalities.
    
    Strategies:
    - early: Concatenate then project
    - late: Weighted average
    - attention: Cross-modal attention
    """
    try:
        # Convert to ModalityEmbedding objects
        embeddings = [
            ModalityEmbedding(
                modality=emb["modality"],
                vector=emb["vector"],
                weight=emb.get("weight", 1.0)
            )
            for emb in request.embeddings
        ]
        
        # Fuse
        unified = await fusion_layer.fuse_embeddings(
            embeddings=embeddings,
            strategy=request.strategy
        )
        
        return unified.dict()
        
    except Exception as e:
        logger.error(f"Failed to fuse embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def multimodal_search(
    query_text: Optional[str] = None,
    query_image_base64: Optional[str] = None,
    query_audio_base64: Optional[str] = None,
    limit: int = 10
):
    """
    Search across modalities using unified embeddings.
    
    Accepts text, image, or audio queries.
    """
    try:
        query_embeddings = []
        
        # Process text (if provided)
        if query_text:
            # In production: use text embedding model
            query_embeddings.append(ModalityEmbedding(
                modality="text",
                vector=[0.0] * 512,  # Placeholder
                weight=1.0
            ))
        
        # Process image (if provided)
        if query_image_base64:
            image_data = base64.b64decode(query_image_base64)
            analysis = await vision_processor.process_image(image_data)
            
            if analysis.embedding:
                query_embeddings.append(ModalityEmbedding(
                    modality="image",
                    vector=analysis.embedding.vector,
                    weight=1.0
                ))
        
        # Process audio (if provided)
        if query_audio_base64:
            audio_data = base64.b64decode(query_audio_base64)
            analysis = await audio_processor.process_audio(audio_data)
            
            if analysis.embedding:
                query_embeddings.append(ModalityEmbedding(
                    modality="audio",
                    vector=analysis.embedding.vector,
                    weight=1.0
                ))
        
        if not query_embeddings:
            raise HTTPException(
                status_code=400,
                detail="No query provided"
            )
        
        # Fuse query embeddings
        query_unified = await fusion_layer.fuse_embeddings(query_embeddings)
        
        # In production: search in vector database (Chroma, Pinecone)
        # results = vector_db.search(query_unified.vector, limit=limit)
        
        # Simulated results
        results = [
            {
                "id": f"result_{i}",
                "score": 0.9 - i * 0.1,
                "modality": "mixed"
            }
            for i in range(min(limit, 5))
        ]
        
        return {
            "query_modalities": query_unified.modalities_used,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed multimodal search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_multimodal_stats():
    """
    Get multi-modal system statistics.
    """
    return {
        "vision_processor": {
            "embedding_dim": vision_processor.embedding_dim,
            "models": ["CLIP", "SAM", "OCR"]
        },
        "audio_processor": {
            "embedding_dim": audio_processor.embedding_dim,
            "models": ["Whisper", "Wav2Vec", "Diarization"]
        },
        "fusion_layer": {
            "target_dim": fusion_layer.target_dim,
            "strategies": ["early", "late", "attention"]
        }
    }
