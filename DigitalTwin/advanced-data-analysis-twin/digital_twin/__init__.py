"""
Digital Twin module for the Advanced Data Analysis & Digital Twin System.

This module provides the core components for creating a digital twin of the user,
including personality modeling, memory management, and conversation capabilities.
"""

from .personality import PersonalityEngine
from .memory import MemorySystem
from .conversation import ConversationEngine

__all__ = ["PersonalityEngine", "MemorySystem", "ConversationEngine"]