"""
Adapters for integrating external components with the Digital Twin.

This module provides adapters for integrating SpiderMind Omega and other
external components with the Digital Twin system.
"""

from .pattern_hydra import BehavioralPatternAnalyzer
from .quantum_profile import QuantumProfileAdapter
from .compatibility_layer import SpiderMindCompatibilityLayer
from .recommendation_engine import RecommendationEngine
from .social_network import SocialNetworkAdapter

__all__ = [
    "BehavioralPatternAnalyzer", 
    "QuantumProfileAdapter", 
    "SpiderMindCompatibilityLayer",
    "RecommendationEngine",
    "SocialNetworkAdapter"
]