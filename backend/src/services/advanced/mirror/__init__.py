"""
Mirror Protocol - Digital Twin System

Creates digital twins of users by analyzing interaction patterns,
communication style, and personality traits.
"""

from .mirror_service import MirrorService, DigitalTwin
from .persona_extractor import PersonaExtractor
from .style_transfer import StyleTransfer
from .personality_model import PersonalityModel

__all__ = [
    "MirrorService",
    "DigitalTwin",
    "PersonaExtractor",
    "StyleTransfer",
    "PersonalityModel",
]
