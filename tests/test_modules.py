"""
Tests for AegisTwin modules (pipeline, analysis, graph, memory).

@context_boundary: tests/modules
"""

import pytest
from pathlib import Path
import tempfile

from aegistwin.modules.pipeline import Pipeline, PipelineBuilder, TransformationResult
from aegistwin.modules.analysis import Analyzer, AnalysisResult
from aegistwin.modules.graph import GraphManager, Node, Edge
from aegistwin.modules.memory import MemoryStore, MemoryType


class TestPipeline:
    """Tests for Pipeline class."""
    
    def test_basic_processing(self):
        """Test basic record processing."""
        pipeline = Pipeline()
        records = [
            {"content": "Hello world", "timestamp": "2026-01-06"},
            {"content": "Another message", "timestamp": "2026-01-07"},
        ]
        
        result = pipeline.process(records, source="test")
        
        assert isinstance(result, TransformationResult)
        assert len(result.records) == 2
        assert len(result.transformations_applied) > 0
    
    def test_timestamp_normalization(self):
        """Test timestamp normalization."""
        pipeline = Pipeline()
        records = [{"timestamp": "2026/01/06 15:30:00"}]
        
        result = pipeline.process(records)
        
        assert "T" in result.records[0]["timestamp"]  # ISO format
    
    def test_text_normalization(self):
        """Test text normalization."""
        pipeline = Pipeline()
        records = [{"content": "  Hello   world  \r\n test  "}]
        
        result = pipeline.process(records)
        
        # Should be stripped and normalized
        assert result.records[0]["content"] == "Hello world test"
    
    def test_entity_extraction(self):
        """Test entity extraction from text."""
        pipeline = Pipeline()
        records = [{"content": "Contact me at test@example.com or visit https://example.com"}]
        
        result = pipeline.process(records)
        
        entities = result.records[0].get("_extracted_entities", [])
        assert len(entities) >= 2
        assert any(e["type"] == "email" for e in entities)
        assert any(e["type"] == "url" for e in entities)
    
    def test_content_hashing(self):
        """Test content hash generation."""
        pipeline = Pipeline()
        records = [{"content": "Same content", "id": "1"}]
        
        result = pipeline.process(records)
        
        assert "_content_hash" in result.records[0]
        assert len(result.records[0]["_content_hash"]) == 16
    
    def test_pipeline_builder(self):
        """Test custom pipeline building."""
        pipeline = (
            PipelineBuilder()
            .with_text_normalization()
            .with_hashing()
            .build()
        )
        
        result = pipeline.process([{"content": "test"}])
        
        assert "_normalize_text" in result.transformations_applied
        assert "_compute_hashes" in result.transformations_applied


class TestAnalyzer:
    """Tests for Analyzer class."""
    
    def test_sentiment_analysis_positive(self):
        """Test positive sentiment detection."""
        analyzer = Analyzer()
        records = [{"content": "I love this amazing product! It's wonderful and perfect."}]
        
        result = analyzer.analyze(records)
        
        assert result.sentiment["positive"] > result.sentiment["negative"]
    
    def test_sentiment_analysis_negative(self):
        """Test negative sentiment detection."""
        analyzer = Analyzer()
        records = [{"content": "This is terrible and awful. I hate it, total fail."}]
        
        result = analyzer.analyze(records)
        
        assert result.sentiment["negative"] > result.sentiment["positive"]
    
    def test_topic_extraction(self):
        """Test topic extraction."""
        analyzer = Analyzer()
        records = [{"content": "I have a meeting at the office with my colleague about the project deadline."}]
        
        result = analyzer.analyze(records)
        
        assert "work" in result.topics
    
    def test_relationship_detection(self):
        """Test relationship detection."""
        analyzer = Analyzer()
        records = [
            {"sender": "alice", "receiver": "bob", "content": "Hi Bob"},
            {"sender": "bob", "receiver": "alice", "content": "Hi Alice"},
        ]
        
        result = analyzer.analyze(records)
        
        assert len(result.relationships) > 0
        assert any(r["type"] == "communicates_with" for r in result.relationships)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        analyzer = Analyzer()
        
        # Few records = lower confidence
        result1 = analyzer.analyze([{"content": "test"}])
        
        # More records = higher confidence
        result2 = analyzer.analyze([{"content": f"message {i}"} for i in range(20)])
        
        assert result2.confidence >= result1.confidence


class TestGraphManager:
    """Tests for GraphManager class."""
    
    def test_add_node(self):
        """Test adding nodes."""
        graph = GraphManager()
        
        node = graph.add_node("n1", "person", {"name": "Alice"})
        
        assert node.id == "n1"
        assert node.type == "person"
        assert node.properties["name"] == "Alice"
    
    def test_add_edge(self):
        """Test adding edges."""
        graph = GraphManager()
        graph.add_node("n1", "person")
        graph.add_node("n2", "person")
        
        edge = graph.add_edge("n1", "n2", "knows")
        
        assert edge.source_id == "n1"
        assert edge.target_id == "n2"
        assert edge.type == "knows"
    
    def test_get_neighbors(self):
        """Test getting neighbors."""
        graph = GraphManager()
        graph.add_node("a", "person")
        graph.add_node("b", "person")
        graph.add_node("c", "person")
        graph.add_edge("a", "b", "knows")
        graph.add_edge("a", "c", "knows")
        
        neighbors = graph.get_neighbors("a", "outgoing")
        
        assert len(neighbors) == 2
        assert "b" in neighbors
        assert "c" in neighbors
    
    def test_find_path(self):
        """Test path finding."""
        graph = GraphManager()
        graph.add_node("a", "person")
        graph.add_node("b", "person")
        graph.add_node("c", "person")
        graph.add_edge("a", "b", "knows")
        graph.add_edge("b", "c", "knows")
        
        path = graph.find_path("a", "c")
        
        assert path == ["a", "b", "c"]
    
    def test_search(self):
        """Test node search."""
        graph = GraphManager()
        graph.add_node("alice", "person", {"name": "Alice Smith"})
        graph.add_node("bob", "person", {"name": "Bob Jones"})
        
        results = graph.search("alice")
        
        assert len(results) == 1
        assert results[0].id == "alice"
    
    def test_stats(self):
        """Test graph statistics."""
        graph = GraphManager()
        graph.add_node("n1", "person")
        graph.add_node("n2", "organization")
        graph.add_edge("n1", "n2", "works_at")
        
        stats = graph.get_stats()
        
        assert stats.node_count == 2
        assert stats.edge_count == 1
        assert stats.node_types["person"] == 1
        assert stats.node_types["organization"] == 1
    
    def test_persistence(self):
        """Test save and load."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        
        try:
            # Create and save
            graph1 = GraphManager()
            graph1.add_node("n1", "person", {"name": "Test"})
            graph1.save(path)
            
            # Load
            graph2 = GraphManager(storage_path=path)
            node = graph2.get_node("n1")
            
            assert node is not None
            assert node.properties["name"] == "Test"
        finally:
            path.unlink(missing_ok=True)


class TestMemoryStore:
    """Tests for MemoryStore class."""
    
    def test_add_memory(self):
        """Test adding memories."""
        store = MemoryStore()
        
        entry = store.add(MemoryType.EPISODIC, {"event": "meeting", "with": "Alice"})
        
        assert entry.type == MemoryType.EPISODIC
        assert entry.content["event"] == "meeting"
    
    def test_search_memories(self):
        """Test searching memories."""
        store = MemoryStore()
        store.add(MemoryType.EPISODIC, {"event": "meeting", "topic": "budget"})
        store.add(MemoryType.EPISODIC, {"event": "call", "topic": "project"})
        store.add(MemoryType.SEMANTIC, {"fact": "budget is $1000"})
        
        results = store.search("budget")
        
        assert len(results) >= 2
    
    def test_search_by_type(self):
        """Test searching with type filter."""
        store = MemoryStore()
        store.add(MemoryType.EPISODIC, {"event": "test"})
        store.add(MemoryType.SEMANTIC, {"fact": "test"})
        
        results = store.search("test", memory_type=MemoryType.EPISODIC)
        
        assert all(r.type == MemoryType.EPISODIC for r in results)
    
    def test_search_by_tags(self):
        """Test searching with tag filter."""
        store = MemoryStore()
        store.add(MemoryType.EPISODIC, {"event": "meeting"}, tags=["work"])
        store.add(MemoryType.EPISODIC, {"event": "party"}, tags=["personal"])
        
        results = store.search("", tags=["work"])
        
        assert len(results) == 1
        assert "work" in results[0].tags
    
    def test_consolidation(self):
        """Test memory consolidation."""
        store = MemoryStore()
        
        # Add low-importance memories
        store.add(MemoryType.EPISODIC, {"event": "minor1"}, importance=0.05)
        store.add(MemoryType.EPISODIC, {"event": "minor2"}, importance=0.05)
        store.add(MemoryType.EPISODIC, {"event": "important"}, importance=0.9)
        
        removed = store.consolidate(MemoryType.EPISODIC, threshold=0.1)
        
        assert removed == 2
        stats = store.get_stats()
        assert stats.episodic_count == 1
    
    def test_stats(self):
        """Test memory statistics."""
        store = MemoryStore()
        store.add(MemoryType.EPISODIC, {"e": 1})
        store.add(MemoryType.EPISODIC, {"e": 2})
        store.add(MemoryType.SEMANTIC, {"s": 1})
        store.add(MemoryType.PROCEDURAL, {"p": 1})
        
        stats = store.get_stats()
        
        assert stats.episodic_count == 2
        assert stats.semantic_count == 1
        assert stats.procedural_count == 1
        assert stats.total_count == 4
    
    def test_deduplication(self):
        """Test that duplicate content returns existing memory."""
        store = MemoryStore()
        
        entry1 = store.add(MemoryType.EPISODIC, {"event": "same"})
        entry2 = store.add(MemoryType.EPISODIC, {"event": "same"})
        
        assert entry1.id == entry2.id
        assert entry2.access_count == 1  # Incremented on second add
    
    def test_persistence(self):
        """Test save and load."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        
        try:
            # Create and save
            store1 = MemoryStore()
            store1.add(MemoryType.EPISODIC, {"event": "test"}, tags=["important"])
            store1.save(path)
            
            # Load
            store2 = MemoryStore(storage_path=path)
            stats = store2.get_stats()
            
            assert stats.episodic_count == 1
        finally:
            path.unlink(missing_ok=True)
