"""
Unit Tests for Designer Agent

Tests all capabilities:
- AI design generation
- Color palette generation
- Layout optimization
- Design critique
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.services.agents.designer_agent import DesignerAgent


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent():
    """Create Designer Agent instance"""
    return DesignerAgent()


# ============================================================================
# Color Palette Tests
# ============================================================================

class TestColorPalettes:
    """Test color palette generation"""
    
    @pytest.mark.asyncio
    async def test_complementary_palette(self, agent):
        """Test complementary color palette"""
        result = await agent.generate_color_palette(
            base_color='#667eea',
            harmony='complementary'
        )
        
        assert 'colors' in result
        assert len(result['colors']) >= 2
        assert 'harmony_type' in result
        assert result['harmony_type'] == 'complementary'
    
    @pytest.mark.asyncio
    async def test_triadic_palette(self, agent):
        """Test triadic color palette"""
        result = await agent.generate_color_palette(
            base_color='#FF5733',
            harmony='triadic'
        )
        
        assert len(result['colors']) == 3
        assert result['harmony_type'] == 'triadic'
    
    @pytest.mark.asyncio
    async def test_analogous_palette(self, agent):
        """Test analogous color palette"""
        result = await agent.generate_color_palette(
            base_color='#3498db',
            harmony='analogous'
        )
        
        assert len(result['colors']) >= 3
        assert result['harmony_type'] == 'analogous'
    
    @pytest.mark.asyncio
    async def test_monochromatic_palette(self, agent):
        """Test monochromatic palette"""
        result = await agent.generate_color_palette(
            base_color='#2ecc71',
            harmony='monochromatic'
        )
        
        assert len(result['colors']) >= 5
        assert all('#' in color for color in result['colors'])
    
    @pytest.mark.asyncio
    async def test_color_hex_format(self, agent):
        """Test color output format"""
        result = await agent.generate_color_palette(
            base_color='#667eea',
            harmony='complementary'
        )
        
        for color in result['colors']:
            assert color.startswith('#')
            assert len(color) == 7  # #RRGGBB


# ============================================================================
# Layout Optimization Tests
# ============================================================================

class TestLayoutOptimization:
    """Test layout optimization"""
    
    @pytest.mark.asyncio
    async def test_golden_ratio_layout(self, agent):
        """Test golden ratio layout generation"""
        result = await agent.optimize_layout(
            width=1920,
            height=1080,
            algorithm='golden_ratio'
        )
        
        assert 'sections' in result
        assert 'algorithm' in result
        assert result['algorithm'] == 'golden_ratio'
    
    @pytest.mark.asyncio
    async def test_grid_layout(self, agent):
        """Test grid-based layout"""
        result = await agent.optimize_layout(
            width=1200,
            height=800,
            algorithm='grid',
            columns=12
        )
        
        assert 'grid' in result
        assert result['grid']['columns'] == 12
    
    @pytest.mark.asyncio
    async def test_layout_dimensions(self, agent):
        """Test layout dimension calculations"""
        result = await agent.optimize_layout(
            width=1920,
            height=1080,
            algorithm='golden_ratio'
        )
        
        for section in result['sections']:
            assert 'x' in section
            assert 'y' in section
            assert 'width' in section
            assert 'height' in section


# ============================================================================
# Design Critique Tests
# ============================================================================

class TestDesignCritique:
    """Test design critique system"""
    
    @pytest.mark.asyncio
    async def test_color_contrast_critique(self, agent):
        """Test color contrast analysis"""
        design = {
            'background': '#ffffff',
            'text': '#000000'
        }
        
        result = await agent.critique_design(design)
        
        assert 'contrast_score' in result
        assert result['contrast_score'] > 7.0  # High contrast
    
    @pytest.mark.asyncio
    async def test_layout_balance_critique(self, agent):
        """Test layout balance analysis"""
        design = {
            'elements': [
                {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                {'x': 900, 'y': 0, 'width': 100, 'height': 100}
            ]
        }
        
        result = await agent.critique_design(design)
        
        assert 'balance_score' in result
    
    @pytest.mark.asyncio
    async def test_suggestions(self, agent):
        """Test critique suggestions"""
        design = {
            'background': '#ffff00',  # Very bright yellow
            'text': '#ffffff'  # White - bad contrast
        }
        
        result = await agent.critique_design(design)
        
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0


# ============================================================================
# Design Generation Tests
# ============================================================================

class TestDesignGeneration:
    """Test AI design generation"""
    
    @pytest.mark.asyncio
    async def test_generate_ui_design(self, agent):
        """Test UI design generation"""
        result = await agent.generate_design(
            prompt="modern dashboard with cards",
            style="minimalist"
        )
        
        assert 'design_id' in result
        assert 'elements' in result or 'description' in result
    
    @pytest.mark.asyncio
    async def test_generate_logo(self, agent):
        """Test logo design generation"""
        result = await agent.generate_design(
            prompt="tech company logo",
            design_type="logo"
        )
        
        assert 'design_id' in result
    
    @pytest.mark.asyncio
    async def test_style_variations(self, agent):
        """Test different style variations"""
        styles = ['minimalist', 'modern', 'classic', 'bold']
        
        for style in styles:
            result = await agent.generate_design(
                prompt="landing page",
                style=style
            )
            
            assert 'design_id' in result
            assert 'style' in result
            assert result['style'] == style


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_full_design_workflow(self, agent):
        """Test complete design workflow"""
        # 1. Generate color palette
        palette = await agent.generate_color_palette(
            base_color='#667eea',
            harmony='triadic'
        )
        assert palette is not None
        
        # 2. Create layout
        layout = await agent.optimize_layout(
            width=1920,
            height=1080,
            algorithm='golden_ratio'
        )
        assert layout is not None
        
        # 3. Critique the design
        design = {
            'colors': palette['colors'],
            'layout': layout['sections']
        }
        critique = await agent.critique_design(design)
        assert critique is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_color_format(self, agent):
        """Test invalid color format"""
        with pytest.raises(ValueError):
            await agent.generate_color_palette(
                base_color='invalid',
                harmony='complementary'
            )
    
    @pytest.mark.asyncio
    async def test_invalid_dimensions(self, agent):
        """Test invalid layout dimensions"""
        with pytest.raises(ValueError):
            await agent.optimize_layout(
                width=-100,
                height=800,
                algorithm='grid'
            )
    
    @pytest.mark.asyncio
    async def test_empty_design_critique(self, agent):
        """Test critique with empty design"""
        with pytest.raises(ValueError):
            await agent.critique_design({})
