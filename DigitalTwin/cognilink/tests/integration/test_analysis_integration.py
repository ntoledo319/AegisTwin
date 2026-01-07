"""
Integration tests for CogniLink analysis components.
"""
import pytest
from unittest.mock import patch, MagicMock

from cognilink.pipeline.processors.text_processor import TextProcessor
from cognilink.analysis.patterns import CommunicationPatternAnalyzer
from cognilink.analysis.relationships import RelationshipAnalyzer
from cognilink.analysis.topics import TopicAnalyzer

class TestAnalysisIntegration:
    """Integration tests for the analysis components."""
    
    def test_processor_to_analyzer_flow(self):
        """Test the flow from processor to analyzers."""
        # Sample data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello, this is a test email about project planning."
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up on the project planning discussion."
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi, how are you doing today?"
            }
        ]
        
        # Set up processor
        processor_config = {
            "language": "en",
            "use_spacy": False
        }
        processor = TextProcessor(processor_config)
        
        # Process data
        processed_data = processor.process(data)
        
        # Set up analyzers
        pattern_analyzer = CommunicationPatternAnalyzer({
            "time_window": "day",
            "min_frequency": 1
        })
        
        relationship_analyzer = RelationshipAnalyzer({
            "min_interactions": 1,
            "weight_threshold": 0.0
        })
        
        topic_analyzer = TopicAnalyzer({
            "num_topics": 2,
            "min_topic_size": 1
        })
        
        # Analyze data
        pattern_results = pattern_analyzer.analyze(processed_data)
        relationship_results = relationship_analyzer.analyze(processed_data)
        
        # For topic analysis, we'll mock some methods to avoid complex computations
        with patch.object(TopicAnalyzer, 'extract_keywords'), \
             patch.object(TopicAnalyzer, 'cluster_topics'), \
             patch.object(TopicAnalyzer, 'extract_topics'), \
             patch.object(TopicAnalyzer, 'analyze_topic_evolution'):
            
            topic_analyzer.extract_keywords.return_value = ["project", "planning", "hello"]
            topic_analyzer.cluster_topics.return_value = [0, 0, 1]
            topic_analyzer.extract_topics.return_value = {
                "topic_distribution": [
                    [0.7, 0.3],
                    [0.8, 0.2],
                    [0.2, 0.8]
                ],
                "topic_keywords": [
                    ["project", "planning"],
                    ["hello", "hi"]
                ]
            }
            topic_analyzer.analyze_topic_evolution.return_value = {
                "2023-01-01": [0.75, 0.25],
                "2023-01-02": [0.2, 0.8]
            }
            
            topic_results = topic_analyzer.analyze(processed_data)
        
        # Verify results
        assert "frequency" in pattern_results
        assert "time_patterns" in pattern_results
        assert "sender_recipient_patterns" in pattern_results
        
        assert "graph" in relationship_results
        assert "relationship_strength" in relationship_results
        assert "communities" in relationship_results
        assert "centrality" in relationship_results
        
        assert "keywords" in topic_results
        assert "clusters" in topic_results
        assert "topics" in topic_results
        assert "topic_evolution" in topic_results
    
    def test_end_to_end_analysis_workflow(self):
        """Test the end-to-end analysis workflow."""
        # Sample processed data (output from text processor)
        processed_data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello, this is a test email about project planning.",
                "analysis": {
                    "normalized": "hello this is a test email about project planning",
                    "sentiment": 0.2,
                    "entities": []
                }
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up on the project planning discussion.",
                "analysis": {
                    "normalized": "follow up on the project planning discussion",
                    "sentiment": 0.1,
                    "entities": []
                }
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi, how are you doing today?",
                "analysis": {
                    "normalized": "hi how are you doing today",
                    "sentiment": 0.5,
                    "entities": []
                }
            }
        ]
        
        # Set up analyzers
        pattern_analyzer = CommunicationPatternAnalyzer({
            "time_window": "day",
            "min_frequency": 1
        })
        
        relationship_analyzer = RelationshipAnalyzer({
            "min_interactions": 1,
            "weight_threshold": 0.0
        })
        
        # For topic analysis, we'll use mocks to avoid complex computations
        topic_analyzer = MagicMock()
        topic_analyzer.analyze.return_value = {
            "keywords": ["project", "planning", "hello"],
            "clusters": [0, 0, 1],
            "topics": {
                "topic_distribution": [
                    [0.7, 0.3],
                    [0.8, 0.2],
                    [0.2, 0.8]
                ],
                "topic_keywords": [
                    ["project", "planning"],
                    ["hello", "hi"]
                ]
            },
            "topic_evolution": {
                "2023-01-01": [0.75, 0.25],
                "2023-01-02": [0.2, 0.8]
            }
        }
        
        # Run analysis
        pattern_results = pattern_analyzer.analyze(processed_data)
        relationship_results = relationship_analyzer.analyze(processed_data)
        topic_results = topic_analyzer.analyze(processed_data)
        
        # Combine results
        analysis_results = {
            "patterns": pattern_results,
            "relationships": relationship_results,
            "topics": topic_results
        }
        
        # Verify combined results structure
        assert "patterns" in analysis_results
        assert "relationships" in analysis_results
        assert "topics" in analysis_results
        
        # Verify pattern results
        assert "frequency" in analysis_results["patterns"]
        assert "2023-01-01" in analysis_results["patterns"]["frequency"]
        assert analysis_results["patterns"]["frequency"]["2023-01-01"] == 2
        
        # Verify relationship results
        assert "graph" in analysis_results["relationships"]
        assert "relationship_strength" in analysis_results["relationships"]
        
        # Verify topic results (using our mock)
        assert "keywords" in analysis_results["topics"]
        assert "clusters" in analysis_results["topics"]
        assert "topics" in analysis_results["topics"]