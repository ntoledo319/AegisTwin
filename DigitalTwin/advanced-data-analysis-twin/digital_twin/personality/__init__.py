"""
Personality Engine module for the Digital Twin.

This module provides components for modeling and evolving the user's personality
based on their data.
"""

from .engine import PersonalityEngine
from .traits import PersonalityTraitExtractor
from .evolution import PersonalityEvolutionEngine
from .alignment import PersonalityAlignmentModule

__all__ = [
    "PersonalityEngine",
    "PersonalityTraitExtractor",
    "PersonalityEvolutionEngine",
    "PersonalityAlignmentModule",
]