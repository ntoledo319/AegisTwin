"""
Unit tests for CogniLink patterns analysis.
"""
import pytest
from unittest.mock import patch, MagicMock
import datetime

from cognilink.analysis.patterns import CommunicationPatternAnalyzer

class TestCommunicationPatternAnalyzer:
    """Tests for the CommunicationPatternAnalyzer class."""
    
    def test_init(self):
        """Test CommunicationPatternAnalyzer initialization."""
        config = {"time_window": "day", "min_frequency": 5}
        analyzer = CommunicationPatternAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.time_window == "day"
        assert analyzer.min_frequency == 5
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {"time_window": "day", "min_frequency": 5}
        analyzer = CommunicationPatternAnalyzer(config)
        
        # Should not raise an exception
        analyzer.validate_config()
    
    def test_validate_config_invalid(self):
        """Test config validation with invalid config."""
        # Invalid time_window
        config = {"time_window": "invalid", "min_frequency": 5}
        analyzer = CommunicationPatternAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
        
        # Missing min_frequency
        config = {"time_window": "day"}
        analyzer = CommunicationPatternAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
    
    def test_analyze_frequency(self):
        """Test frequency analysis."""
        config = {"time_window": "day", "min_frequency": 1}
        analyzer = CommunicationPatternAnalyzer(config)
        
        # Sample data with timestamps
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello"
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up"
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi"
            }
        ]
        
        frequency = analyzer.analyze_frequency(data)
        
        assert "2023-01-01" in frequency
        assert frequency["2023-01-01"] == 2
        assert "2023-01-02" in frequency
        assert frequency["2023-01-02"] == 1
    
    def test_analyze_time_patterns(self):
        """Test time pattern analysis."""
        config = {"time_window": "hour", "min_frequency": 1}
        analyzer = CommunicationPatternAnalyzer(config)
        
        # Sample data with timestamps
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:15:00",
                "content": "Hello"
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:45:00",
                "content": "Follow-up"
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-01T14:30:00",
                "content": "Hi"
            }
        ]
        
        time_patterns = analyzer.analyze_time_patterns(data)
        
        assert 10 in time_patterns  # 10 AM
        assert time_patterns[10] == 2
        assert 14 in time_patterns  # 2 PM
        assert time_patterns[14] == 1
    
    def test_analyze_sender_recipient_patterns(self):
        """Test sender-recipient pattern analysis."""
        config = {"time_window": "day", "min_frequency": 1}
        analyzer = CommunicationPatternAnalyzer(config)
        
        # Sample data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello"
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T14:00:00",
                "content": "Follow-up"
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-02T09:00:00",
                "content": "Hi"
            }
        ]
        
        patterns = analyzer.analyze_sender_recipient_patterns(data)
        
        assert ("sender@example.com", "recipient@example.com") in patterns
        assert patterns[("sender@example.com", "recipient@example.com")] == 2
        assert ("Friend", "User") in patterns
        assert patterns[("Friend", "User")] == 1
    
    def test_analyze(self):
        """Test the analyze method."""
        config = {"time_window": "day", "min_frequency": 1}
        analyzer = CommunicationPatternAnalyzer(config)
        
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
        
        assert "frequency" in results
        assert "time_patterns" in results
        assert "sender_recipient_patterns" in results
        assert "response_times" in results
        assert "sentiment_over_time" in results