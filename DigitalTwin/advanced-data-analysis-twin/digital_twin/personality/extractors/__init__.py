"""
Personality Trait Extractors for the Digital Twin.

This module provides extractors for different types of user data.
"""

from .textual import TextualTraitExtractor
from .communication import CommunicationTraitExtractor
from .activity import ActivityTraitExtractor
from .social import SocialTraitExtractor
from .consumption import ConsumptionTraitExtractor

__all__ = [
    "TextualTraitExtractor",
    "CommunicationTraitExtractor",
    "ActivityTraitExtractor",
    "SocialTraitExtractor",
    "ConsumptionTraitExtractor",
]