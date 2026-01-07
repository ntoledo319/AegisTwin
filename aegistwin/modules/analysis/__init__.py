"""
AegisTwin Analysis Module

Minimal analyzer for entity extraction and relationship detection.

@ai_prompt: Use Analyzer to extract insights from normalized data.
@context_boundary: aegistwin/modules/analysis
"""

from aegistwin.modules.analysis.analyzer import (
    AnalysisResult,
    Analyzer,
    Entity,
    Relationship,
)

__all__ = ["Analyzer", "AnalysisResult", "Entity", "Relationship"]
