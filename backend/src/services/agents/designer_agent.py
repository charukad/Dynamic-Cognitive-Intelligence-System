"""
Designer/Creative Agent - Visual Design and Creative Generation

Expert in visual design, UI/UX, color theory, and creative generation.
Integrates generative AI for design creation and optimization.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import colorsys

from pydantic import BaseModel

from src.services.agents.base_agent import BaseAgent
from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums and Types
# ============================================================================

class ColorSchemeType(str, Enum):
    """Color scheme types"""
    COMPLEMENTARY = "complementary"
    ANALOGOUS = "analogous"
    TRIADIC = "triadic"
    TETRADIC = "tetradic"
    MONOCHROMATIC = "monochromatic"
    SPLIT_COMPLEMENTARY = "split_complementary"


class DesignStyle(str, Enum):
    """Design styles"""
    MINIMALIST = "minimalist"
    MODERN = "modern"
    VINTAGE = "vintage"
    FUTURISTIC = "futuristic"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"


# ============================================================================
# Data Models
# ============================================================================

class Color(BaseModel):
    """Color representation"""
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[float, float, float]
    name: str


class ColorPalette(BaseModel):
    """Color palette with harmonious colors"""
    primary: Color
    secondary: Color
    accent: Color
    background: Color
    text: Color
    scheme_type: ColorSchemeType
    css_variables: Dict[str, str]


class DesignOutput(BaseModel):
    """Design generation output"""
    image_url: str
    style: str
    prompt: str
    dimensions: Tuple[int, int]
    design_tokens: Dict[str, Any] = {}


class LayoutComponent(BaseModel):
    """UI component for layout"""
    id: str
    width: float
    height: float
    priority: int = 1


class Layout(BaseModel):
    """Optimized layout"""
    components: List[Dict[str, Any]]
    css_grid: str
    explanation: str


class DesignCritique(BaseModel):
    """Design critique/feedback"""
    overall_score: float  # 0-10
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    accessibility_score: float


# ============================================================================
# Designer Agent
# ============================================================================

class DesignerAgent(BaseAgent):
    """
    Expert in visual design, UI/UX, and creative generation.
    
    Capabilities:
    - Generate designs with AI (Stable Diffusion/DALL-E)
    - Create harmonious color palettes
    - Optimize layouts with design principles
    - Typography recommendations
    - Design critique and feedback
    - Brand identity creation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialty = "design"
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt"""
        return """You are an expert Designer Agent with deep knowledge in:

- Visual design principles (contrast, hierarchy, balance, rhythm)
- Color theory and harmonious palettes
- Typography and readability
- UI/UX best practices
- Accessibility (WCAG 2.1)
- Modern design trends
- Brand identity and consistency

Your role is to:
1. Create stunning visual designs
2. Generate harmonious color schemes
3. Optimize layouts for usability
4. Recommend appropriate typography
5. Provide constructive design critiques
6. Ensure accessibility compliance

Always provide:
- Visual examples where possible
- Clear design rationale
- Multiple options for client choice
- Accessibility considerations
"""
    
    async def generate_design(
        self,
        prompt: str,
        style: DesignStyle = DesignStyle.MODERN,
        width: int = 1024,
        height: int = 1024
    ) -> DesignOutput:
        """
        Generate design using AI.
        
        Args:
            prompt: Design description
            style: Visual style
            width, height: Dimensions in pixels
            
        Returns:
            Generated design
        """
        # In production, integrate Stable Diffusion or DALL-E:
        # from diffusers import StableDiffusionPipeline
        # import torch
        # 
        # pipe = StableDiffusionPipeline.from_pretrained(
        #     "stabilityai/stable-diffusion-2-1",
        #     torch_dtype=torch.float16
        # )
        # pipe = pipe.to("cuda")
        # 
        # full_prompt = f"{prompt}, {style.value} style, high quality, detailed"
        # image = pipe(full_prompt, height=height, width=width).images[0]
        # 
        # # Save to storage
        # image_url = await storage.upload_image(image)
        
        logger.info(f"Generating {style.value} design: {prompt}")
        
        # Simulated output
        image_url = f"https://placeholder.com/{width}x{height}/design.png"
        
        # Extract design tokens
        design_tokens = {
            'dominant_colors': ['#667eea', '#764ba2', '#f093fb'],
            'style_keywords': [style.value, 'modern', 'clean'],
            'composition': 'rule_of_thirds'
        }
        
        return DesignOutput(
            image_url=image_url,
            style=style.value,
            prompt=prompt,
            dimensions=(width, height),
            design_tokens=design_tokens
        )
    
    async def suggest_color_palette(
        self,
        base_color: Optional[str] = None,
        mood: Optional[str] = None,
        scheme_type: ColorSchemeType = ColorSchemeType.COMPLEMENTARY
    ) -> ColorPalette:
        """
        Generate harmonious color palette.
        
        Args:
            base_color: Starting color (hex)
            mood: Desired mood (energetic, calm, professional, playful)
            scheme_type: Color harmony type
            
        Returns:
            Color palette
        """
        logger.info(f"Generating {scheme_type.value} palette")
        
        # Parse base color or generate from mood
        if base_color:
            base_rgb = self._hex_to_rgb(base_color)
        elif mood:
            base_rgb = self._mood_to_color(mood)
        else:
            # Default: nice purple
            base_rgb = (102, 126, 234)
        
        # Convert to HSL for manipulation
        base_hsl = self._rgb_to_hsl(*base_rgb)
        
        # Generate palette based on scheme
        colors = self._generate_color_scheme(base_hsl, scheme_type)
        
        # Create Color objects
        primary = self._create_color(colors[0], "Primary")
        secondary = self._create_color(colors[1], "Secondary")
        accent = self._create_color(colors[2], "Accent")
        
        # Background and text (calculated for contrast)
        background = self._create_color((247, 247, 250), "Background")
        text = self._create_color((26, 26, 46), "Text")
        
        # CSS variables
        css_variables = {
            '--color-primary': primary.hex,
            '--color-secondary': secondary.hex,
            '--color-accent': accent.hex,
            '--color-background': background.hex,
            '--color-text': text.hex
        }
        
        return ColorPalette(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text=text,
            scheme_type=scheme_type,
            css_variables=css_variables
        )
    
    def _generate_color_scheme(
        self,
        base_hsl: Tuple[float, float, float],
        scheme_type: ColorSchemeType
    ) -> List[Tuple[int, int, int]]:
        """Generate color scheme from base HSL"""
        h, s, l = base_hsl
        colors = []
        
        if scheme_type == ColorSchemeType.COMPLEMENTARY:
            # Base + opposite on color wheel
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb((h + 180) % 360, s, l),
                self._hsl_to_rgb((h + 30) % 360, s * 0.8, l * 1.1)
            ]
            
        elif scheme_type == ColorSchemeType.ANALOGOUS:
            # Base + neighbors
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb((h + 30) % 360, s, l),
                self._hsl_to_rgb((h - 30) % 360, s, l)
            ]
            
        elif scheme_type == ColorSchemeType.TRIADIC:
            # Three evenly spaced colors
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb((h + 120) % 360, s, l),
                self._hsl_to_rgb((h + 240) % 360, s, l)
            ]
            
        elif scheme_type == ColorSchemeType.TETRADIC:
            # Four colors (two pairs of complements)
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb((h + 90) % 360, s, l),
                self._hsl_to_rgb((h + 180) % 360, s, l),
                self._hsl_to_rgb((h + 270) % 360, s, l)
            ][:3]
            
        elif scheme_type == ColorSchemeType.MONOCHROMATIC:
            # Variations of saturation and lightness
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb(h, s * 0.7, l * 1.2),
                self._hsl_to_rgb(h, s * 1.2, l * 0.8)
            ]
            
        elif scheme_type == ColorSchemeType.SPLIT_COMPLEMENTARY:
            # Base + two adjacent to complement
            colors = [
                self._hsl_to_rgb(h, s, l),
                self._hsl_to_rgb((h + 150) % 360, s, l),
                self._hsl_to_rgb((h + 210) % 360, s, l)
            ]
        
        return colors
    
    async def optimize_layout(
        self,
        components: List[LayoutComponent],
        container_width: int = 1200,
        use_golden_ratio: bool = True
    ) -> Layout:
        """
        Optimize component layout using design principles.
        
        Args:
            components: List of components to layout
            container_width: Container width in pixels
            use_golden_ratio: Use golden ratio for proportions
            
        Returns:
            Optimized layout
        """
        logger.info(f"Optimizing layout for {len(components)} components")
        
        golden_ratio = 1.618 if use_golden_ratio else 1.5
        
        # Sort by priority (high to low)
        sorted_components = sorted(
            components,
            key=lambda c: c.priority,
            reverse=True
        )
        
        # Calculate grid
        grid_columns = 12  # 12-column grid
        layout_items = []
        
        for idx, component in enumerate(sorted_components):
            # Calculate column span based on priority and golden ratio
            if component.priority >= 3:
                col_span = grid_columns  # Full width
            elif component.priority == 2:
                col_span = int(grid_columns / golden_ratio)  # ~7 columns
            else:
                col_span = int(grid_columns / (golden_ratio ** 2))  # ~4 columns
            
            layout_items.append({
                'id': component.id,
                'grid_column': f'span {col_span}',
                'aspect_ratio': f'{component.width} / {component.height}',
                'priority': component.priority
            })
        
        # CSS Grid template
        css_grid = f"""
.container {{
  display: grid;
  grid-template-columns: repeat({grid_columns}, 1fr);
  gap: 2rem;
  max-width: {container_width}px;
}}

.component {{
  grid-column: var(--grid-column);
}}
"""
        
        explanation = f"""
Layout optimized using:
- 12-column grid system
- Golden ratio ({golden_ratio:.3f}) for proportions
- Priority-based sizing (high priority = full width)
- Responsive gap spacing (2rem)
- Maximum container width: {container_width}px
"""
        
        return Layout(
            components=layout_items,
            css_grid=css_grid.strip(),
            explanation=explanation.strip()
        )
    
    async def critique_design(
        self,
        design_description: str,
        design_url: Optional[str] = None
    ) -> DesignCritique:
        """
        Provide design critique and feedback.
        
        Args:
            design_description: Text description of design
            design_url: Optional image URL
            
        Returns:
            Design critique
        """
        # In production, use vision model to analyze design_url
        # and LLM to generate detailed critique
        
        logger.info("Analyzing design for critique")
        
        # Simulated critique based on description analysis
        desc_lower = design_description.lower()
        
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Analyze description for keywords
        if "contrast" in desc_lower or "color" in desc_lower:
            strengths.append("Good use of color contrast")
        else:
            weaknesses.append("Color contrast not explicitly addressed")
            suggestions.append("Ensure WCAG AA contrast ratio (4.5:1 minimum)")
        
        if "hierarchy" in desc_lower or "layout" in desc_lower:
            strengths.append("Clear visual hierarchy")
        else:
            suggestions.append("Establish clear visual hierarchy with size/weight/color")
        
        if "white space" in desc_lower or "spacing" in desc_lower:
            strengths.append("Effective use of white space")
        else:
            suggestions.append("Add breathing room with generous white space")
        
        # Score based on strengths/weaknesses
        overall_score = 7.0 + len(strengths) * 0.5 - len(weaknesses) * 0.5
        overall_score = max(0, min(10, overall_score))
        
        accessibility_score = 8.0
        
        return DesignCritique(
            overall_score=overall_score,
            strengths=strengths or ["Well-structured design approach"],
            weaknesses=weaknesses or ["Minor improvements needed"],
            suggestions=suggestions,
            accessibility_score=accessibility_score
        )
    
    # Helper methods for color manipulation
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB to hex"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSL"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (h * 360, s * 100, l * 100)
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        h, s, l = h / 360, s / 100, l / 100
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _mood_to_color(self, mood: str) -> Tuple[int, int, int]:
        """Map mood to base color"""
        mood_colors = {
            'energetic': (255, 107, 107),  # Vibrant red
            'calm': (108, 156, 234),       # Soft blue
            'professional': (52, 73, 94),  # Dark blue-gray
            'playful': (255, 195, 0),      # Bright yellow
            'elegant': (75, 46, 131),      # Deep purple
            'natural': (67, 160, 71)       # Green
        }
        
        return mood_colors.get(mood.lower(), (102, 126, 234))
    
    def _create_color(self, rgb: Tuple[int, int, int], name: str) -> Color:
        """Create Color object from RGB"""
        hex_color = self._rgb_to_hex(*rgb)
        hsl = self._rgb_to_hsl(*rgb)
        
        return Color(
            hex=hex_color,
            rgb=rgb,
            hsl=hsl,
            name=name
        )


# Register agent
def create_designer_agent(agent_id: str = "designer") -> DesignerAgent:
    """Create Designer Agent instance"""
    return DesignerAgent(
        agent_id=agent_id,
        name="Designer",
        description="Expert in visual design, color theory, and creative generation"
    )
