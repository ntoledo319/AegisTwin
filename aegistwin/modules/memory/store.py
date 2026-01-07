"""
AegisTwin Memory Store

Three-tier memory system: episodic, semantic, procedural.

@ai_prompt: Use MemoryStore for long-term storage and retrieval.
@context_boundary: aegistwin/modules/memory/store

# AI-GENERATED 2026-01-06
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class MemoryType(str, Enum):
    """Types of memory."""
    EPISODIC = "episodic"      # Specific events and experiences
    SEMANTIC = "semantic"      # Facts and relationships
    PROCEDURAL = "procedural"  # Learned patterns and behaviors


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    type: MemoryType
    content: dict[str, Any]
    embedding: list[float] | None = None
    importance: float = 0.5
    access_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "importance": self.importance,
            "access_count": self.access_count,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "tags": self.tags,
        }


@dataclass
class MemoryStats:
    """Statistics about memory stores."""
    episodic_count: int
    semantic_count: int
    procedural_count: int
    total_count: int
    state_hash: str


class MemoryStore:
    """
    Three-tier memory system.

    - Episodic: Stores specific events and experiences
    - Semantic: Stores facts and general knowledge
    - Procedural: Stores learned patterns and behaviors
    """

    def __init__(self, storage_path: Path | None = None):
        self._memories: dict[str, MemoryEntry] = {}
        self._by_type: dict[MemoryType, list[str]] = {
            MemoryType.EPISODIC: [],
            MemoryType.SEMANTIC: [],
            MemoryType.PROCEDURAL: [],
        }
        self._storage_path = storage_path

        if storage_path and storage_path.exists():
            self._load()

    def add(
        self,
        memory_type: MemoryType,
        content: dict[str, Any],
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        """
        Add a new memory.

        Args:
            memory_type: Type of memory
            content: Memory content
            importance: Importance score (0-1)
            tags: Optional tags for retrieval

        Returns:
            Created memory entry
        """
        # Generate ID from content hash
        content_str = json.dumps(content, sort_keys=True)
        memory_id = hashlib.sha256(content_str.encode()).hexdigest()[:12]

        # Check for duplicates
        if memory_id in self._memories:
            existing = self._memories[memory_id]
            existing.access_count += 1
            existing.last_accessed = datetime.now(timezone.utc).isoformat()
            return existing

        entry = MemoryEntry(
            id=memory_id,
            type=memory_type,
            content=content,
            importance=min(1.0, max(0.0, importance)),
            tags=tags or [],
        )

        self._memories[memory_id] = entry
        self._by_type[memory_type].append(memory_id)

        return entry

    def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a memory by ID."""
        entry = self._memories.get(memory_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc).isoformat()
        return entry

    def search(
        self,
        query: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """
        Search memories by content, type, or tags.

        Args:
            query: Search query (matches content fields)
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            limit: Maximum results

        Returns:
            Matching memories sorted by relevance
        """
        results: list[tuple[float, MemoryEntry]] = []
        query_lower = query.lower()

        for entry in self._memories.values():
            # Filter by type
            if memory_type and entry.type != memory_type:
                continue

            # Filter by tags
            if tags and not any(t in entry.tags for t in tags):
                continue

            # Score by content match
            score = self._compute_match_score(query_lower, entry)
            if score > 0:
                results.append((score, entry))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        # Update access for returned results
        for _, entry in results[:limit]:
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc).isoformat()

        return [entry for _, entry in results[:limit]]

    def _compute_match_score(self, query: str, entry: MemoryEntry) -> float:
        """Compute relevance score for a query-entry pair."""
        score = 0.0

        # Check content fields
        content_str = json.dumps(entry.content).lower()
        if query in content_str:
            score += 1.0
            # Bonus for exact field match
            for value in entry.content.values():
                if isinstance(value, str) and query in value.lower():
                    score += 0.5

        # Check tags
        for tag in entry.tags:
            if query in tag.lower():
                score += 0.3

        # Weight by importance and recency
        score *= (0.5 + entry.importance * 0.5)

        return score

    def get_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """Get memories of a specific type."""
        memory_ids = self._by_type.get(memory_type, [])
        return [self._memories[mid] for mid in memory_ids[:limit]]

    def consolidate(
        self,
        memory_type: MemoryType,
        threshold: float = 0.1,
    ) -> int:
        """
        Consolidate memories by removing low-importance duplicates.

        Returns number of memories removed.
        """
        memory_ids = self._by_type.get(memory_type, [])
        to_remove = []

        for mid in memory_ids:
            entry = self._memories.get(mid)
            if entry and entry.importance < threshold and entry.access_count < 2:
                to_remove.append(mid)

        for mid in to_remove:
            del self._memories[mid]
            self._by_type[memory_type].remove(mid)

        return len(to_remove)

    def update_importance(
        self,
        memory_id: str,
        importance: float,
    ) -> MemoryEntry | None:
        """Update importance of a memory."""
        entry = self._memories.get(memory_id)
        if entry:
            entry.importance = min(1.0, max(0.0, importance))
        return entry

    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        episodic = len(self._by_type[MemoryType.EPISODIC])
        semantic = len(self._by_type[MemoryType.SEMANTIC])
        procedural = len(self._by_type[MemoryType.PROCEDURAL])

        # Compute state hash
        all_ids = sorted(self._memories.keys())
        state_str = ",".join(all_ids)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]

        return MemoryStats(
            episodic_count=episodic,
            semantic_count=semantic,
            procedural_count=procedural,
            total_count=episodic + semantic + procedural,
            state_hash=state_hash,
        )

    def clear(self, memory_type: MemoryType | None = None) -> int:
        """
        Clear memories.

        Args:
            memory_type: If specified, only clear this type. Otherwise clear all.

        Returns:
            Number of memories cleared.
        """
        if memory_type:
            memory_ids = self._by_type.get(memory_type, [])
            count = len(memory_ids)
            for mid in memory_ids:
                del self._memories[mid]
            self._by_type[memory_type] = []
            return count
        else:
            count = len(self._memories)
            self._memories.clear()
            for mt in MemoryType:
                self._by_type[mt] = []
            return count

    def save(self, path: Path | None = None) -> None:
        """Save memories to JSON file."""
        path = path or self._storage_path
        if not path:
            raise ValueError("No storage path specified")

        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "memories": [m.to_dict() for m in self._memories.values()]
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load memories from JSON file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        with open(self._storage_path) as f:
            data = json.load(f)

        for mem_data in data.get("memories", []):
            entry = MemoryEntry(
                id=mem_data["id"],
                type=MemoryType(mem_data["type"]),
                content=mem_data["content"],
                importance=mem_data.get("importance", 0.5),
                access_count=mem_data.get("access_count", 0),
                created_at=mem_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                last_accessed=mem_data.get("last_accessed", datetime.now(timezone.utc).isoformat()),
                tags=mem_data.get("tags", []),
            )
            self._memories[entry.id] = entry
            self._by_type[entry.type].append(entry.id)
