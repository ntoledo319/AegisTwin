"""
AI Integration Module for Cognitive-Twin

This module provides unified access to multiple AI providers:
- OpenAI GPT-4 (conversation, reasoning)
- Anthropic Claude (analysis, safety)
- Google AI (multimodal, embeddings)

All requests are routed through OpenRouter for optimal model selection.
"""

from .openrouter_client import OpenRouterClient
from .conversation_ai import ConversationAI
from .personality_ai import PersonalityAI
from .analysis_ai import AnalysisAI

__all__ = [
    'OpenRouterClient',
    'ConversationAI', 
    'PersonalityAI',
    'AnalysisAI'
]
