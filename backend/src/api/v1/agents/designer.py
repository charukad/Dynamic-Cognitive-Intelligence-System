"""
Designer Agent API Routes

REST API for design and creative capabilities.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import get_logger
from src.services.agents.designer_agent import (
    create_designer_agent,
    DesignStyle,
    ColorSchemeType,
    LayoutComponent
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/agents/designer", tags=["designer"])


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateDesignRequest(BaseModel):
    """Request to generate design"""
    prompt: str
    style: DesignStyle = DesignStyle.MODERN
    width: int = 1024
    height: int = 1024


class ColorPaletteRequest(BaseModel):
    """Request for color palette"""
    base_color: Optional[str] = None  # Hex color
    mood: Optional[str] = None
    scheme_type: ColorSchemeType = ColorSchemeType.COMPLEMENTARY


class OptimizeLayoutRequest(BaseModel):
    """Request to optimize layout"""
    components: List[LayoutComponent]
    container_width: int = 1200
    use_golden_ratio: bool = True


class DesignCritiqueRequest(BaseModel):
    """Request for design critique"""
    design_description: str
    design_url: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate")
async def generate_design(request: GenerateDesignRequest):
    """
    Generate design using AI.
    
    Styles:
    - minimalist
    - modern
    - vintage
    - futuristic
    - playful
    - professional
    
    Returns:
    - image_url: Generated design URL
    - design_tokens: Extracted design elements
    """
    try:
        agent = create_designer_agent()
        
        design = await agent.generate_design(
            prompt=request.prompt,
            style=request.style,
            width=request.width,
            height=request.height
        )
        
        return design.dict()
        
    except Exception as e:
        logger.error(f"Design generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/color-palette")
async def create_color_palette(request: ColorPaletteRequest):
    """
    Generate harmonious color palette.
    
    Scheme types:
    - complementary: Base + opposite color
    - analogous: Base + neighboring colors
    - triadic: Three evenly spaced colors
    - tetradic: Four colors (rectangle)
    - monochromatic: Variations of one hue
    - split_complementary: Base + two adjacent to complement
    
    Returns:
    - 5 colors (primary, secondary, accent, background, text)
    - CSS variables for easy use
    """
    try:
        agent = create_designer_agent()
        
        palette = await agent.suggest_color_palette(
            base_color=request.base_color,
            mood=request.mood,
            scheme_type=request.scheme_type
        )
        
        return palette.dict()
        
    except Exception as e:
        logger.error(f"Color palette generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-layout")
async def optimize_layout(request: OptimizeLayoutRequest):
    """
    Optimize component layout using design principles.
    
    Uses:
    - 12-column grid system
    - Golden ratio for proportions
    - Priority-based sizing
    
    Returns:
    - Optimized component positions
    - CSS Grid template
    - Design explanation
    """
    try:
        agent = create_designer_agent()
        
        layout = await agent.optimize_layout(
            components=request.components,
            container_width=request.container_width,
            use_golden_ratio=request.use_golden_ratio
        )
        
        return layout.dict()
        
    except Exception as e:
        logger.error(f"Layout optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/critique")
async def critique_design(request: DesignCritiqueRequest):
    """
    Provide design critique and feedback.
    
    Analyzes:
    - Visual hierarchy
    - Color contrast
    - Typography
    - White space
    - Accessibility
    
    Returns:
    - Overall score (0-10)
    - Strengths and weaknesses
    - Actionable suggestions
    - Accessibility score
    """
    try:
        agent = create_designer_agent()
        
        critique = await agent.critique_design(
            design_description=request.design_description,
            design_url=request.design_url
        )
        
        return critique.dict()
        
    except Exception as e:
        logger.error(f"Design critique failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
