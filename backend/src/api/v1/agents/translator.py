"""
Translator Agent API Routes

REST API for translation and localization capabilities.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import get_logger
from src.services.agents.translator_agent import create_translator_agent

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/agents/translator", tags=["translator"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TranslateRequest(BaseModel):
    """Request to translate text"""
    text: str
    source_lang: Optional[str] = None  # Auto-detect if None
    target_lang: str = "en"
    context: Optional[str] = None


class DetectLanguageRequest(BaseModel):
    """Request to detect language"""
    text: str


class LocalizeRequest(BaseModel):
    """Request to localize content"""
    content: Dict[str, str]
    target_locale: str  # e.g., 'en-US', 'fr-FR'


class BatchTranslateRequest(BaseModel):
    """Request for batch translation"""
    texts: List[str]
    target_lang: str
    source_lang: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """
    Translate text with context preservation.
    
    Features:
    - Auto language detection
    - Context-aware translation
    - Alternative translations
    - Confidence scoring
    - Translation memory caching
    
    Returns:
    - Translated text
    - Confidence score
    - Alternative translations
    - Detected topics
    """
    try:
        agent = create_translator_agent()
        
        translation = await agent.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            context=request.context
        )
        
        return translation.dict()
        
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect")
async def detect_language(request: DetectLanguageRequest):
    """
    Detect language of text.
    
    Supports 100+ languages including:
    - English, Spanish, French, German
    - Chinese, Japanese, Korean
    - Arabic, Russian, Hindi
    - And many more...
    
    Returns:
    - Detected language code
    - Language name
    - Confidence score
    - Alternative possibilities
    """
    try:
        agent = create_translator_agent()
        
        detection = await agent.detect_language(request.text)
        
        return detection.dict()
        
    except Exception as e:
        logger.error(f"Language detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/localize")
async def localize_content(request: LocalizeRequest):
    """
    Full content localization with cultural adaptation.
    
    Includes:
    - Text translation
    - Date/time format localization
    - Currency symbol adaptation
    - Number format localization
    - Cultural references adaptation
    
    Returns:
    - Localized content
    - Applied localization rules
    - Locale-specific formats
    """
    try:
        agent = create_translator_agent()
        
        localized = await agent.localize(
            content=request.content,
            target_locale=request.target_locale
        )
        
        return localized.dict()
        
    except Exception as e:
        logger.error(f"Localization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-translate")
async def batch_translate(request: BatchTranslateRequest):
    """
    Translate multiple texts efficiently.
    
    Optimized for:
    - Large translation jobs
    - Consistent terminology
    - Batch API efficiency
    
    Returns:
    - List of translations with metadata
    """
    try:
        agent = create_translator_agent()
        
        translations = await agent.batch_translate(
            texts=request.texts,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )
        
        return {"translations": [t.dict() for t in translations]}
        
    except Exception as e:
        logger.error(f"Batch translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
