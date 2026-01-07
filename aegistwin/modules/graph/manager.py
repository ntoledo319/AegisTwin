"""
AegisTwin Knowledge Graph Manager

Local knowledge graph for entity and relationship storage.

@ai_prompt: Use GraphManager to build and query the knowledge graph.
@context_boundary: aegistwin/modules/graph/manager

# AI-GENERATED 2026-01-06
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class Node:
    """Graph node representing an entity."""
    id: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Edge:
    """Graph edge representing a relationship."""
    source_id: str
    target_id: str
    type: str
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class GraphStats:
    """Statistics about the graph."""
    node_count: int
    edge_count: int
    node_types: dict[str, int]
    edge_types: dict[str, int]
    version: int


class GraphManager:
    """
    Local knowledge graph manager.

    Provides:
    - Node and edge CRUD operations
    - Graph traversal and querying
    - Persistence to JSON
    - Version tracking
    """

    def __init__(self, storage_path: Path | None = None):
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []
        self._adjacency: dict[str, set[str]] = {}  # source -> targets
        self._reverse_adjacency: dict[str, set[str]] = {}  # target -> sources
        self._version: int = 0
        self._storage_path = storage_path

        if storage_path and storage_path.exists():
            self._load()

    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: dict[str, Any] | None = None,
    ) -> Node:
        """Add or update a node."""
        if node_id in self._nodes:
            # Update existing node
            node = self._nodes[node_id]
            node.properties.update(properties or {})
            node.updated_at = datetime.now(timezone.utc).isoformat()
        else:
            # Create new node
            node = Node(
                id=node_id,
                type=node_type,
                properties=properties or {},
            )
            self._nodes[node_id] = node
            self._adjacency[node_id] = set()
            self._reverse_adjacency[node_id] = set()

        self._version += 1
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> Edge:
        """Add an edge between nodes."""
        # Ensure nodes exist
        if source_id not in self._nodes:
            self.add_node(source_id, "unknown")
        if target_id not in self._nodes:
            self.add_node(target_id, "unknown")

        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            type=edge_type,
            weight=weight,
            properties=properties or {},
        )

        self._edges.append(edge)
        self._adjacency[source_id].add(target_id)
        self._reverse_adjacency[target_id].add(source_id)

        self._version += 1
        return edge

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        return [n for n in self._nodes.values() if n.type == node_type]

    def get_edges(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        edge_type: str | None = None,
    ) -> list[Edge]:
        """Get edges with optional filtering."""
        edges = self._edges

        if source_id:
            edges = [e for e in edges if e.source_id == source_id]
        if target_id:
            edges = [e for e in edges if e.target_id == target_id]
        if edge_type:
            edges = [e for e in edges if e.type == edge_type]

        return edges

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
    ) -> list[str]:
        """Get neighboring node IDs."""
        if direction == "outgoing":
            return list(self._adjacency.get(node_id, set()))
        elif direction == "incoming":
            return list(self._reverse_adjacency.get(node_id, set()))
        else:  # both
            outgoing = self._adjacency.get(node_id, set())
            incoming = self._reverse_adjacency.get(node_id, set())
            return list(outgoing | incoming)

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> list[str] | None:
        """Find shortest path between nodes using BFS."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor in self.get_neighbors(current, "both"):
                if neighbor == target_id:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def search(
        self,
        query: str,
        node_types: list[str] | None = None,
        limit: int = 10,
    ) -> list[Node]:
        """Search nodes by property values."""
        results = []
        query_lower = query.lower()

        for node in self._nodes.values():
            if node_types and node.type not in node_types:
                continue

            # Check ID
            if query_lower in node.id.lower():
                results.append(node)
                continue

            # Check properties
            for value in node.properties.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(node)
                    break

        return results[:limit]

    def get_stats(self) -> GraphStats:
        """Get graph statistics."""
        node_types: dict[str, int] = {}
        for node in self._nodes.values():
            node_types[node.type] = node_types.get(node.type, 0) + 1

        edge_types: dict[str, int] = {}
        for edge in self._edges:
            edge_types[edge.type] = edge_types.get(edge.type, 0) + 1

        return GraphStats(
            node_count=len(self._nodes),
            edge_count=len(self._edges),
            node_types=node_types,
            edge_types=edge_types,
            version=self._version,
        )

    def clear(self) -> None:
        """Clear all graph data."""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()
        self._version = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "version": self._version,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "properties": n.properties,
                    "created_at": n.created_at,
                    "updated_at": n.updated_at,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "type": e.type,
                    "weight": e.weight,
                    "properties": e.properties,
                    "created_at": e.created_at,
                }
                for e in self._edges
            ],
        }

    def save(self, path: Path | None = None) -> None:
        """Save graph to JSON file."""
        path = path or self._storage_path
        if not path:
            raise ValueError("No storage path specified")

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def _load(self) -> None:
        """Load graph from JSON file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        with open(self._storage_path) as f:
            data = json.load(f)

        self._version = data.get("version", 0)

        for node_data in data.get("nodes", []):
            node = Node(
                id=node_data["id"],
                type=node_data["type"],
                properties=node_data.get("properties", {}),
                created_at=node_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                updated_at=node_data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            )
            self._nodes[node.id] = node
            self._adjacency[node.id] = set()
            self._reverse_adjacency[node.id] = set()

        for edge_data in data.get("edges", []):
            edge = Edge(
                source_id=edge_data["source_id"],
                target_id=edge_data["target_id"],
                type=edge_data["type"],
                weight=edge_data.get("weight", 1.0),
                properties=edge_data.get("properties", {}),
                created_at=edge_data.get("created_at", datetime.now(timezone.utc).isoformat()),
            )
            self._edges.append(edge)
            self._adjacency[edge.source_id].add(edge.target_id)
            self._reverse_adjacency[edge.target_id].add(edge.source_id)
