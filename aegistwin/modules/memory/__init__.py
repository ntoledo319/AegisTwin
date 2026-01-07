"""
AegisTwin Memory Module

Provides episodic, semantic, and procedural memory capabilities
with vector search support.

@ai_prompt: Use SemanticMemory for natural language queries, MemoryStore for structured storage.
@context_boundary: aegistwin/modules/memory
"""

from aegistwin.modules.memory.store import (
    MemoryEntry,
    MemoryStats,
    MemoryStore,
    MemoryType,
)

# Optional vector store imports (require sentence-transformers)
try:
    from aegistwin.modules.memory.semantic import MemoryFragment, SemanticMemory
    from aegistwin.modules.memory.vector_store import SearchResult, VectorEntry, VectorStore
    HAS_VECTOR_STORE = True
except ImportError:
    HAS_VECTOR_STORE = False

__all__ = [
    "MemoryStore",
    "MemoryEntry",
    "MemoryType",
    "MemoryStats",
    "VectorStore",
    "VectorEntry",
    "SearchResult",
    "SemanticMemory",
    "MemoryFragment",
    "HAS_VECTOR_STORE",
]
