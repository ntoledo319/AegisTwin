"""
AegisTwin Graph Module

Knowledge graph management from integrated_system/knowledge_graph.

@ai_prompt: Use GraphManager to build and query the knowledge graph.
@context_boundary: aegistwin/modules/graph

# ORIGINAL_INTENT: Wrap integrated_system/knowledge_graph
"""

from aegistwin.modules.graph.manager import (
    GraphManager,
    Node,
    Edge,
    GraphStats,
)

__all__ = ["GraphManager", "Node", "Edge", "GraphStats"]
