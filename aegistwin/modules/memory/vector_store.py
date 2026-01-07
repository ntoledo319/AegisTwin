"""
Vector Store for Semantic Memory

Provides vector embedding storage and similarity search.

@ai_prompt: Use VectorStore for semantic search across memories
@context_boundary: aegistwin/modules/memory/vector_store
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    _SentenceTransformer = None  # type: ignore[misc, assignment]
    HAS_EMBEDDINGS = False


@dataclass
class VectorEntry:
    """Entry in the vector store."""
    id: str
    content: str
    embedding: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SearchResult:
    """Result from similarity search."""
    id: str
    content: str
    score: float
    metadata: dict[str, Any]


class VectorStore:
    """
    In-memory vector store with similarity search.

    Uses sentence-transformers for embeddings and cosine similarity for search.

    Attributes:
        model_name: Name of the sentence-transformer model
        entries: Stored vector entries
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_path: Path | None = None,
    ):
        if not HAS_EMBEDDINGS:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.persist_path = persist_path
        self._model: "SentenceTransformer | None" = None  # noqa: UP037
        self._entries: dict[str, VectorEntry] = {}

        if persist_path and persist_path.exists():
            self._load()

    @property
    def model(self) -> "SentenceTransformer":
        """Lazy-load the embedding model."""
        if self._model is None:
            self._model = _SentenceTransformer(self.model_name)
        return self._model

    def add(
        self,
        content: str,
        id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add content to the vector store.

        Args:
            content: Text content to store
            id: Optional ID (generated if not provided)
            metadata: Optional metadata dict

        Returns:
            Entry ID
        """
        if id is None:
            id = hashlib.sha256(content.encode()).hexdigest()[:16]

        embedding = self.model.encode(content, convert_to_numpy=True)

        entry = VectorEntry(
            id=id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
        )

        self._entries[id] = entry

        if self.persist_path:
            self._save()

        return id

    def add_batch(
        self,
        contents: list[str],
        ids: list[str] | None = None,
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """Add multiple entries efficiently."""
        if ids is None:
            ids = [hashlib.sha256(c.encode()).hexdigest()[:16] for c in contents]
        if metadatas is None:
            metadatas = [{} for _ in contents]

        embeddings = self.model.encode(contents, convert_to_numpy=True)

        result_ids = []
        for i, (content, id_, meta) in enumerate(zip(contents, ids, metadatas, strict=False)):
            entry = VectorEntry(
                id=id_,
                content=content,
                embedding=embeddings[i],
                metadata=meta,
            )
            self._entries[id_] = entry
            result_ids.append(id_)

        if self.persist_path:
            self._save()

        return result_ids

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar content.

        Args:
            query: Search query text
            top_k: Maximum results to return
            min_score: Minimum similarity score (0-1)
            filter_metadata: Optional metadata filter

        Returns:
            List of SearchResult sorted by score descending
        """
        if not self._entries:
            return []

        query_embedding = self.model.encode(query, convert_to_numpy=True)

        results = []
        for entry in self._entries.values():
            if filter_metadata:
                match = all(
                    entry.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue

            score = self._cosine_similarity(query_embedding, entry.embedding)

            if score >= min_score:
                results.append(SearchResult(
                    id=entry.id,
                    content=entry.content,
                    score=float(score),
                    metadata=entry.metadata,
                ))

        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def get(self, id: str) -> VectorEntry | None:
        """Get entry by ID."""
        return self._entries.get(id)

    def delete(self, id: str) -> bool:
        """Delete entry by ID."""
        if id in self._entries:
            del self._entries[id]
            if self.persist_path:
                self._save()
            return True
        return False

    def count(self) -> int:
        """Get number of entries."""
        return len(self._entries)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _save(self) -> None:
        """Persist to disk."""
        if not self.persist_path:
            return

        data = {
            "model_name": self.model_name,
            "entries": [
                {
                    "id": e.id,
                    "content": e.content,
                    "embedding": e.embedding.tolist(),
                    "metadata": e.metadata,
                    "created_at": e.created_at.isoformat(),
                }
                for e in self._entries.values()
            ],
        }

        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "w") as f:
            json.dump(data, f)

    def _load(self) -> None:
        """Load from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return

        with open(self.persist_path) as f:
            data = json.load(f)

        for entry_data in data.get("entries", []):
            entry = VectorEntry(
                id=entry_data["id"],
                content=entry_data["content"],
                embedding=np.array(entry_data["embedding"]),
                metadata=entry_data.get("metadata", {}),
                created_at=datetime.fromisoformat(entry_data["created_at"]),
            )
            self._entries[entry.id] = entry
