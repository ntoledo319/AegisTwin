"""
Unit tests for analysis components.

This module provides unit tests for the analysis components of the integrated system.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.communication import CommunicationAnalyzer
from analysis.advanced import AdvancedAnalyzer
from analysis.cognitive import CognitiveAnalyzer
from analysis import AnalysisManager

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        {
            "id": "msg1",
            "sender": "user1",
            "recipient": "user2",
            "timestamp": "2023-01-01T10:00:00Z",
            "content": "Hello, how are you doing today?",
            "metadata": {"source": "email"}
        },
        {
            "id": "msg2",
            "sender": "user2",
            "recipient": "user1",
            "timestamp": "2023-01-01T10:05:00Z",
            "content": "I'm doing well, thank you! How about you?",
            "metadata": {"source": "email"}
        },
        {
            "id": "msg3",
            "sender": "user1",
            "recipient": "user2",
            "timestamp": "2023-01-01T10:10:00Z",
            "content": "I'm great. Let's discuss the project tomorrow.",
            "metadata": {"source": "email"}
        }
    ]

@pytest.fixture
def communication_analyzer():
    """Create a CommunicationAnalyzer instance for testing."""
    analyzer = CommunicationAnalyzer()
    return analyzer

@pytest.fixture
def advanced_analyzer():
    """Create an AdvancedAnalyzer instance for testing."""
    analyzer = AdvancedAnalyzer()
    return analyzer

@pytest.fixture
def cognitive_analyzer():
    """Create a CognitiveAnalyzer instance for testing."""
    analyzer = CognitiveAnalyzer()
    return analyzer

@pytest.fixture
def analysis_manager():
    """Create an AnalysisManager instance for testing."""
    manager = AnalysisManager()
    return manager

class TestCommunicationAnalyzer:
    """Test cases for CommunicationAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, communication_analyzer):
        """Test that the analyzer initializes correctly."""
        assert hasattr(communication_analyzer, 'pattern_analyzer')
        assert hasattr(communication_analyzer, 'relationship_analyzer')
        assert hasattr(communication_analyzer, 'topic_analyzer')
    
    @pytest.mark.asyncio
    async def test_analyze(self, communication_analyzer, sample_messages):
        """Test the analyze method."""
        # Mock the analyzers
        communication_analyzer.pattern_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        communication_analyzer.pattern_analyzer.analyze.return_value.set_result({
            "patterns": {
                "frequency": {"avg_messages_per_day": 3},
                "timing": {"peak_hour": 10},
                "style": {"avg_length": 40}
            }
        })
        
        communication_analyzer.relationship_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        communication_analyzer.relationship_analyzer.analyze.return_value.set_result({
            "relationships": {
                "contact_frequency": {"user2": 3},
                "sentiment": {"user2": 0.8},
                "strength": {"user2": 0.7}
            }
        })
        
        communication_analyzer.topic_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        communication_analyzer.topic_analyzer.analyze.return_value.set_result({
            "topics": {
                "keywords": ["project"],
                "topics": ["work"],
                "trends": {"project": [{"date": "2023-01-01", "count": 1}]}
            }
        })
        
        # Analyze messages
        results = await communication_analyzer.analyze(sample_messages)
        
        # Check results
        assert "patterns" in results
        assert "relationships" in results
        assert "topics" in results
        
        assert results["patterns"]["frequency"]["avg_messages_per_day"] == 3
        assert results["relationships"]["sentiment"]["user2"] == 0.8
        assert "project" in results["topics"]["keywords"]
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, communication_analyzer, sample_messages):
        """Test the generate_insights method."""
        # Mock the analyze method
        communication_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        communication_analyzer.analyze.return_value.set_result({
            "patterns": {
                "frequency": {"avg_messages_per_day": 3},
                "timing": {"peak_hour": 10},
                "style": {"avg_length": 40}
            },
            "relationships": {
                "contact_frequency": {"user2": 3},
                "sentiment": {"user2": 0.8},
                "strength": {"user2": 0.7}
            },
            "topics": {
                "keywords": ["project"],
                "topics": ["work"],
                "trends": {"project": [{"date": "2023-01-01", "count": 1}]}
            }
        })
        
        # Generate insights
        insights = await communication_analyzer.generate_insights(sample_messages)
        
        # Check insights
        assert len(insights) > 0
        assert all(isinstance(insight, dict) for insight in insights)
        assert all("title" in insight for insight in insights)
        assert all("description" in insight for insight in insights)
        assert all("score" in insight for insight in insights)

class TestAdvancedAnalyzer:
    """Test cases for AdvancedAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, advanced_analyzer):
        """Test that the analyzer initializes correctly."""
        assert hasattr(advanced_analyzer, 'nlp_analyzer')
        assert hasattr(advanced_analyzer, 'temporal_analyzer')
        assert hasattr(advanced_analyzer, 'network_analyzer')
    
    @pytest.mark.asyncio
    async def test_analyze(self, advanced_analyzer, sample_messages):
        """Test the analyze method."""
        # Mock the analyzers
        advanced_analyzer.nlp_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        advanced_analyzer.nlp_analyzer.analyze.return_value.set_result({
            "sentiment": {"avg_score": 0.7},
            "entities": ["project"],
            "statistics": {"avg_word_count": 8}
        })
        
        advanced_analyzer.temporal_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        advanced_analyzer.temporal_analyzer.analyze.return_value.set_result({
            "statistics": {"total_duration": 600},
            "time_distribution": {"morning": 3},
            "trends": {"increasing": True}
        })
        
        advanced_analyzer.network_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        advanced_analyzer.network_analyzer.analyze.return_value.set_result({
            "statistics": {"node_count": 2, "edge_count": 2},
            "centrality": {"user1": 0.5, "user2": 0.5},
            "communities": [["user1", "user2"]]
        })
        
        # Create mock communication results
        communication_results = {
            "patterns": {},
            "relationships": {},
            "topics": {}
        }
        
        # Analyze messages
        results = await advanced_analyzer.analyze(sample_messages, communication_results)
        
        # Check results
        assert "nlp" in results
        assert "temporal" in results
        assert "network" in results
        
        assert results["nlp"]["sentiment"]["avg_score"] == 0.7
        assert results["temporal"]["statistics"]["total_duration"] == 600
        assert results["network"]["statistics"]["node_count"] == 2
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, advanced_analyzer, sample_messages):
        """Test the generate_insights method."""
        # Mock the analyze method
        advanced_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        advanced_analyzer.analyze.return_value.set_result({
            "nlp": {
                "sentiment": {"avg_score": 0.7},
                "entities": ["project"],
                "statistics": {"avg_word_count": 8}
            },
            "temporal": {
                "statistics": {"total_duration": 600},
                "time_distribution": {"morning": 3},
                "trends": {"increasing": True}
            },
            "network": {
                "statistics": {"node_count": 2, "edge_count": 2},
                "centrality": {"user1": 0.5, "user2": 0.5},
                "communities": [["user1", "user2"]]
            }
        })
        
        # Generate insights
        insights = await advanced_analyzer.generate_insights(sample_messages)
        
        # Check insights
        assert len(insights) > 0
        assert all(isinstance(insight, dict) for insight in insights)
        assert all("title" in insight for insight in insights)
        assert all("description" in insight for insight in insights)
        assert all("score" in insight for insight in insights)

class TestCognitiveAnalyzer:
    """Test cases for CognitiveAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, cognitive_analyzer):
        """Test that the analyzer initializes correctly."""
        assert hasattr(cognitive_analyzer, 'personality_analyzer')
        assert hasattr(cognitive_analyzer, 'values_analyzer')
        assert hasattr(cognitive_analyzer, 'decision_analyzer')
        assert hasattr(cognitive_analyzer, 'memory_analyzer')
    
    @pytest.mark.asyncio
    async def test_analyze(self, cognitive_analyzer, sample_messages):
        """Test the analyze method."""
        # Mock the analyzers
        cognitive_analyzer.personality_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        cognitive_analyzer.personality_analyzer.analyze.return_value.set_result({
            "traits": {
                "openness": 0.7,
                "conscientiousness": 0.8,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            },
            "communication_style": {
                "assertiveness": 0.6,
                "emotionality": 0.4,
                "formality": 0.7
            }
        })
        
        cognitive_analyzer.values_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        cognitive_analyzer.values_analyzer.analyze.return_value.set_result({
            "values": {
                "achievement": 0.8,
                "benevolence": 0.9,
                "conformity": 0.5,
                "hedonism": 0.3,
                "power": 0.4,
                "security": 0.7,
                "self_direction": 0.8,
                "stimulation": 0.6,
                "tradition": 0.4,
                "universalism": 0.7
            }
        })
        
        cognitive_analyzer.decision_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        cognitive_analyzer.decision_analyzer.analyze.return_value.set_result({
            "decision_styles": {
                "analytical": 0.8,
                "intuitive": 0.4,
                "deliberate": 0.7,
                "spontaneous": 0.3
            },
            "decision_processes": {
                "problem_identification": 0.8,
                "information_gathering": 0.9,
                "alternative_evaluation": 0.7,
                "decision_making": 0.8,
                "implementation": 0.6
            }
        })
        
        cognitive_analyzer.memory_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        cognitive_analyzer.memory_analyzer.analyze.return_value.set_result({
            "recall_patterns": {
                "accuracy": 0.8,
                "consistency": 0.7
            },
            "reference_patterns": {
                "self_references": 5,
                "other_references": 8
            },
            "memory_consistency": 0.8,
            "memory_decay": 0.2
        })
        
        # Create mock communication and advanced results
        communication_results = {"patterns": {}, "relationships": {}, "topics": {}}
        advanced_results = {"nlp": {}, "temporal": {}, "network": {}}
        
        # Analyze messages
        results = await cognitive_analyzer.analyze(sample_messages, communication_results, advanced_results)
        
        # Check results
        assert "personality" in results
        assert "values" in results
        assert "decision" in results
        assert "memory" in results
        
        assert results["personality"]["traits"]["openness"] == 0.7
        assert results["values"]["values"]["achievement"] == 0.8
        assert results["decision"]["decision_styles"]["analytical"] == 0.8
        assert results["memory"]["recall_patterns"]["accuracy"] == 0.8
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, cognitive_analyzer, sample_messages):
        """Test the generate_insights method."""
        # Mock the analyze method
        cognitive_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        cognitive_analyzer.analyze.return_value.set_result({
            "personality": {
                "traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.8,
                    "extraversion": 0.6,
                    "agreeableness": 0.9,
                    "neuroticism": 0.3
                }
            },
            "values": {
                "values": {
                    "achievement": 0.8,
                    "benevolence": 0.9
                }
            },
            "decision": {
                "decision_styles": {
                    "analytical": 0.8,
                    "intuitive": 0.4
                }
            },
            "memory": {
                "recall_patterns": {
                    "accuracy": 0.8,
                    "consistency": 0.7
                }
            }
        })
        
        # Generate insights
        insights = await cognitive_analyzer.generate_insights(sample_messages)
        
        # Check insights
        assert len(insights) > 0
        assert all(isinstance(insight, dict) for insight in insights)
        assert all("title" in insight for insight in insights)
        assert all("description" in insight for insight in insights)
        assert all("score" in insight for insight in insights)

class TestAnalysisManager:
    """Test cases for AnalysisManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, analysis_manager):
        """Test that the manager initializes correctly."""
        assert hasattr(analysis_manager, 'communication_analyzer')
        assert hasattr(analysis_manager, 'advanced_analyzer')
        assert hasattr(analysis_manager, 'cognitive_analyzer')
    
    @pytest.mark.asyncio
    async def test_analyze(self, analysis_manager, sample_messages):
        """Test the analyze method."""
        # Mock the analyzers
        analysis_manager.communication_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        analysis_manager.communication_analyzer.analyze.return_value.set_result({
            "patterns": {"frequency": {"avg_messages_per_day": 3}},
            "relationships": {"sentiment": {"user2": 0.8}},
            "topics": {"keywords": ["project"]}
        })
        
        analysis_manager.advanced_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        analysis_manager.advanced_analyzer.analyze.return_value.set_result({
            "nlp": {"sentiment": {"avg_score": 0.7}},
            "temporal": {"statistics": {"total_duration": 600}},
            "network": {"statistics": {"node_count": 2}}
        })
        
        analysis_manager.cognitive_analyzer.analyze = MagicMock(return_value=asyncio.Future())
        analysis_manager.cognitive_analyzer.analyze.return_value.set_result({
            "personality": {"traits": {"openness": 0.7}},
            "values": {"values": {"achievement": 0.8}},
            "decision": {"decision_styles": {"analytical": 0.8}},
            "memory": {"recall_patterns": {"accuracy": 0.8}}
        })
        
        # Analyze messages
        results = await analysis_manager.analyze(sample_messages)
        
        # Check results
        assert "communication" in results
        assert "advanced" in results
        assert "cognitive" in results
        
        assert results["communication"]["patterns"]["frequency"]["avg_messages_per_day"] == 3
        assert results["advanced"]["nlp"]["sentiment"]["avg_score"] == 0.7
        assert results["cognitive"]["personality"]["traits"]["openness"] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, analysis_manager, sample_messages):
        """Test the generate_insights method."""
        # Mock the analyzers' generate_insights methods
        analysis_manager.communication_analyzer.generate_insights = MagicMock(return_value=asyncio.Future())
        analysis_manager.communication_analyzer.generate_insights.return_value.set_result([
            {
                "title": "Communication Insight 1",
                "description": "Description 1",
                "score": 0.8
            },
            {
                "title": "Communication Insight 2",
                "description": "Description 2",
                "score": 0.7
            }
        ])
        
        analysis_manager.advanced_analyzer.generate_insights = MagicMock(return_value=asyncio.Future())
        analysis_manager.advanced_analyzer.generate_insights.return_value.set_result([
            {
                "title": "Advanced Insight 1",
                "description": "Description 1",
                "score": 0.9
            }
        ])
        
        analysis_manager.cognitive_analyzer.generate_insights = MagicMock(return_value=asyncio.Future())
        analysis_manager.cognitive_analyzer.generate_insights.return_value.set_result([
            {
                "title": "Cognitive Insight 1",
                "description": "Description 1",
                "score": 0.85
            }
        ])
        
        # Generate insights
        insights = await analysis_manager.generate_insights(sample_messages)
        
        # Check insights
        assert len(insights) == 4  # Total from all analyzers
        assert insights[0]["title"] == "Advanced Insight 1"  # Highest score first
        assert insights[1]["title"] == "Cognitive Insight 1"
        assert insights[2]["title"] == "Communication Insight 1"
        assert insights[3]["title"] == "Communication Insight 2"