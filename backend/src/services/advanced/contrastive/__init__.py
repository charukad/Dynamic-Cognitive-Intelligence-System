"""
Contrastive Learning System

Detects contradictions, ensures knowledge consistency, and alerts on cognitive dissonance.
"""

from .contrastive_service import ContrastiveService, ContradictionResult
from .contradiction_detector import ContradictionDetector
from .consistency_checker import ConsistencyChecker

__all__ = [
    "ContrastiveService",
    "ContradictionResult",
    "ContradictionDetector",
    "ConsistencyChecker",
]
