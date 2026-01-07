"""
Semantic Memory Manager

High-level interface for semantic memory operations.

@ai_prompt: Use SemanticMemory for natural language memory queries
@context_boundary: aegistwin/modules/memory/semantic
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aegistwin.modules.memory.vector_store import VectorStore


@dataclass
class MemoryFragment:
    """A fragment of semantic memory."""
    id: str
    content: str
    memory_type: str
    importance: float
    access_count: int
    created_at: datetime
    last_accessed: datetime
    metadata: dict[str, Any]


class SemanticMemory:
    """
    Semantic memory system with vector search.

    Provides:
    - Natural language memory storage
    - Semantic similarity search
    - Memory consolidation
    - Importance-based retrieval

    Attributes:
        vector_store: Underlying vector store
    """

    def __init__(
        self,
        persist_dir: Path | None = None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        persist_path = persist_dir / "semantic_memory.json" if persist_dir else None
        self.vector_store = VectorStore(
            model_name=model_name,
            persist_path=persist_path,
        )
        self._access_counts: dict[str, int] = {}

    def remember(
        self,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store a memory.

        Args:
            content: Memory content
            memory_type: Type (e.g., "fact", "experience", "preference")
            importance: Importance score 0-1
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        now = datetime.now(timezone.utc).isoformat()

        full_metadata = {
            "memory_type": memory_type,
            "importance": importance,
            "created_at": now,
            "last_accessed": now,
            **(metadata or {}),
        }

        return self.vector_store.add(
            content=content,
            metadata=full_metadata,
        )

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
        min_importance: float = 0.0,
    ) -> list[MemoryFragment]:
        """
        Recall memories similar to query.

        Args:
            query: Natural language query
            top_k: Maximum memories to return
            memory_type: Optional filter by type
            min_importance: Minimum importance threshold

        Returns:
            List of MemoryFragment sorted by relevance
        """
        filter_metadata = {}
        if memory_type:
            filter_metadata["memory_type"] = memory_type

        results = self.vector_store.search(
            query=query,
            top_k=top_k * 2,
            filter_metadata=filter_metadata if filter_metadata else None,
        )

        fragments = []
        for result in results:
            importance = result.metadata.get("importance", 0.5)
            if importance < min_importance:
                continue

            self._access_counts[result.id] = self._access_counts.get(result.id, 0) + 1

            fragments.append(MemoryFragment(
                id=result.id,
                content=result.content,
                memory_type=result.metadata.get("memory_type", "general"),
                importance=importance,
                access_count=self._access_counts[result.id],
                created_at=datetime.fromisoformat(result.metadata.get("created_at", datetime.now(timezone.utc).isoformat())),
                last_accessed=datetime.now(timezone.utc),
                metadata=result.metadata,
            ))

        return fragments[:top_k]

    def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        return self.vector_store.delete(memory_id)

    def consolidate(
        self,
        similarity_threshold: float = 0.9,
        max_memories: int | None = None,
    ) -> int:
        """
        Consolidate similar memories.

        Merges highly similar memories to reduce redundancy.

        Args:
            similarity_threshold: Threshold for considering memories similar
            max_memories: Maximum memories to keep (removes lowest importance)

        Returns:
            Number of memories removed
        """
        removed = 0
        entries = list(self.vector_store._entries.values())

        seen_ids = set()
        for _i, entry in enumerate(entries):
            if entry.id in seen_ids:
                continue

            similar = self.vector_store.search(
                query=entry.content,
                top_k=10,
                min_score=similarity_threshold,
            )

            if len(similar) > 1:
                sorted_similar = sorted(
                    similar,
                    key=lambda x: x.metadata.get("importance", 0),
                    reverse=True,
                )

                for s in sorted_similar[1:]:
                    if s.id != entry.id and s.id not in seen_ids:
                        self.vector_store.delete(s.id)
                        seen_ids.add(s.id)
                        removed += 1

        if max_memories and self.vector_store.count() > max_memories:
            entries = sorted(
                self.vector_store._entries.values(),
                key=lambda e: e.metadata.get("importance", 0),
            )

            to_remove = len(entries) - max_memories
            for entry in entries[:to_remove]:
                self.vector_store.delete(entry.id)
                removed += 1

        return removed

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        entries = list(self.vector_store._entries.values())

        if not entries:
            return {"count": 0}

        importances = [e.metadata.get("importance", 0.5) for e in entries]
        types = {}
        for e in entries:
            t = e.metadata.get("memory_type", "general")
            types[t] = types.get(t, 0) + 1

        return {
            "count": len(entries),
            "avg_importance": sum(importances) / len(importances),
            "types": types,
            "total_accesses": sum(self._access_counts.values()),
        }
