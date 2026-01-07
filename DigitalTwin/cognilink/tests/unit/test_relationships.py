"""
Unit tests for CogniLink relationships analysis.
"""
import pytest
from unittest.mock import patch, MagicMock
import networkx as nx

from cognilink.analysis.relationships import RelationshipAnalyzer

class TestRelationshipAnalyzer:
    """Tests for the RelationshipAnalyzer class."""
    
    def test_init(self):
        """Test RelationshipAnalyzer initialization."""
        config = {"min_interactions": 3, "weight_threshold": 0.5}
        analyzer = RelationshipAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.min_interactions == 3
        assert analyzer.weight_threshold == 0.5
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {"min_interactions": 3, "weight_threshold": 0.5}
        analyzer = RelationshipAnalyzer(config)
        
        # Should not raise an exception
        analyzer.validate_config()
    
    def test_validate_config_invalid(self):
        """Test config validation with invalid config."""
        # Missing min_interactions
        config = {"weight_threshold": 0.5}
        analyzer = RelationshipAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
        
        # Invalid weight_threshold
        config = {"min_interactions": 3, "weight_threshold": -0.1}
        analyzer = RelationshipAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
    
    def test_build_interaction_graph(self):
        """Test building the interaction graph."""
        config = {"min_interactions": 1, "weight_threshold": 0.0}
        analyzer = RelationshipAnalyzer(config)
        
        # Sample data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello",
                "analysis": {"sentiment": 0.5}
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up",
                "analysis": {"sentiment": 0.2}
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi",
                "analysis": {"sentiment": 0.8}
            }
        ]
        
        graph = analyzer.build_interaction_graph(data)
        
        assert isinstance(graph, nx.Graph)
        assert "sender@example.com" in graph.nodes
        assert "recipient@example.com" in graph.nodes
        assert "Friend" in graph.nodes
        assert "User" in graph.nodes
        assert graph.has_edge("sender@example.com", "recipient@example.com")
        assert graph.has_edge("Friend", "User")
        assert graph.edges["sender@example.com", "recipient@example.com"]["weight"] == 2
        assert graph.edges["Friend", "User"]["weight"] == 1
    
    def test_calculate_relationship_strength(self):
        """Test calculating relationship strength."""
        config = {"min_interactions": 1, "weight_threshold": 0.0}
        analyzer = RelationshipAnalyzer(config)
        
        # Create a simple graph
        graph = nx.Graph()
        graph.add_edge("A", "B", weight=5, sentiment=0.8)
        graph.add_edge("A", "C", weight=2, sentiment=0.3)
        graph.add_edge("B", "C", weight=1, sentiment=-0.2)
        
        strengths = analyzer.calculate_relationship_strength(graph)
        
        assert ("A", "B") in strengths
        assert ("A", "C") in strengths
        assert ("B", "C") in strengths
        assert strengths[("A", "B")] > strengths[("A", "C")]
        assert strengths[("A", "C")] > strengths[("B", "C")]
    
    def test_identify_communities(self):
        """Test identifying communities in the graph."""
        config = {"min_interactions": 1, "weight_threshold": 0.0}
        analyzer = RelationshipAnalyzer(config)
        
        # Create a graph with two communities
        graph = nx.Graph()
        # Community 1
        graph.add_edge("A", "B", weight=5)
        graph.add_edge("A", "C", weight=4)
        graph.add_edge("B", "C", weight=3)
        # Community 2
        graph.add_edge("D", "E", weight=5)
        graph.add_edge("D", "F", weight=4)
        graph.add_edge("E", "F", weight=3)
        # Weak connection between communities
        graph.add_edge("C", "D", weight=1)
        
        communities = analyzer.identify_communities(graph)
        
        assert isinstance(communities, list)
        assert len(communities) >= 1  # Should identify at least one community
        
        # Check if nodes from the same community are grouped together
        for community in communities:
            if "A" in community:
                assert "B" in community  # A and B should be in the same community
    
    def test_calculate_centrality(self):
        """Test calculating node centrality."""
        config = {"min_interactions": 1, "weight_threshold": 0.0}
        analyzer = RelationshipAnalyzer(config)
        
        # Create a simple graph
        graph = nx.Graph()
        graph.add_edge("A", "B", weight=1)
        graph.add_edge("A", "C", weight=1)
        graph.add_edge("A", "D", weight=1)
        graph.add_edge("B", "C", weight=1)
        
        centrality = analyzer.calculate_centrality(graph)
        
        assert "A" in centrality
        assert "B" in centrality
        assert "C" in centrality
        assert "D" in centrality
        assert centrality["A"] > centrality["B"]  # A has more connections
        assert centrality["A"] > centrality["C"]
        assert centrality["A"] > centrality["D"]
    
    def test_analyze(self):
        """Test the analyze method."""
        config = {"min_interactions": 1, "weight_threshold": 0.0}
        analyzer = RelationshipAnalyzer(config)
        
        # Sample data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello",
                "analysis": {"sentiment": 0.5}
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up",
                "analysis": {"sentiment": 0.2}
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi",
                "analysis": {"sentiment": 0.8}
            }
        ]
        
        results = analyzer.analyze(data)
        
        assert "graph" in results
        assert "relationship_strength" in results
        assert "communities" in results
        assert "centrality" in results
        assert isinstance(results["graph"], nx.Graph)
        assert isinstance(results["relationship_strength"], dict)
        assert isinstance(results["communities"], list)
        assert isinstance(results["centrality"], dict)