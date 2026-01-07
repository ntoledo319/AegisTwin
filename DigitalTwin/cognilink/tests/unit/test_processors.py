"""
Unit tests for CogniLink processors.
"""
import pytest
from unittest.mock import patch, MagicMock

from cognilink.pipeline.processors.text_processor import TextProcessor

class TestTextProcessor:
    """Tests for the TextProcessor class."""
    
    def test_init(self):
        """Test TextProcessor initialization."""
        config = {"language": "en", "use_spacy": True}
        processor = TextProcessor(config)
        
        assert processor.config == config
        assert processor.language == "en"
        assert processor.use_spacy == True
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {"language": "en", "use_spacy": True}
        processor = TextProcessor(config)
        
        # Should not raise an exception
        processor.validate_config()
    
    def test_validate_config_invalid(self):
        """Test config validation with invalid config."""
        # Missing language
        config = {"use_spacy": True}
        processor = TextProcessor(config)
        
        with pytest.raises(ValueError):
            processor.validate_config()
    
    def test_normalize_text(self):
        """Test text normalization."""
        config = {"language": "en", "use_spacy": False}
        processor = TextProcessor(config)
        
        # Test basic normalization
        text = "  Hello,   World!  "
        normalized = processor.normalize_text(text)
        assert normalized == "hello, world!"
        
        # Test with special characters
        text = "Hello\n\tWorld! This is a test."
        normalized = processor.normalize_text(text)
        assert normalized == "hello world! this is a test."
        
        # Test with URLs and emails
        text = "Check out https://example.com or email me at user@example.com"
        normalized = processor.normalize_text(text)
        assert "example.com" in normalized
        assert "user@example.com" in normalized
    
    @patch('spacy.load')
    def test_extract_entities_with_spacy(self, mock_spacy_load):
        """Test entity extraction with spaCy."""
        # Mock spaCy
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_ent = MagicMock()
        mock_ent.text = "John"
        mock_ent.label_ = "PERSON"
        mock_doc.ents = [mock_ent]
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp
        
        config = {"language": "en", "use_spacy": True}
        processor = TextProcessor(config)
        
        text = "John went to the store."
        entities = processor.extract_entities(text)
        
        assert len(entities) == 1
        assert entities[0]["text"] == "John"
        assert entities[0]["type"] == "PERSON"
    
    def test_extract_entities_without_spacy(self):
        """Test entity extraction without spaCy."""
        config = {"language": "en", "use_spacy": False}
        processor = TextProcessor(config)
        
        text = "John went to the store."
        entities = processor.extract_entities(text)
        
        # Without spaCy, we should get a basic extraction or empty list
        assert isinstance(entities, list)
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis."""
        config = {"language": "en", "use_spacy": False}
        processor = TextProcessor(config)
        
        # Test positive sentiment
        text = "I love this product! It's amazing."
        sentiment = processor.analyze_sentiment(text)
        assert sentiment > 0
        
        # Test negative sentiment
        text = "I hate this product. It's terrible."
        sentiment = processor.analyze_sentiment(text)
        assert sentiment < 0
        
        # Test neutral sentiment
        text = "This is a product."
        sentiment = processor.analyze_sentiment(text)
        assert -0.1 < sentiment < 0.1
    
    def test_process_text(self):
        """Test the process_text method."""
        config = {"language": "en", "use_spacy": False}
        processor = TextProcessor(config)
        
        text = "Hello, John! I'm happy to meet you."
        result = processor.process_text(text)
        
        assert "normalized" in result
        assert "entities" in result
        assert "sentiment" in result
        assert isinstance(result["sentiment"], float)
    
    def test_process(self):
        """Test the process method with communication data."""
        config = {"language": "en", "use_spacy": False}
        processor = TextProcessor(config)
        
        # Sample communication data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "content": "Hello, John! I'm happy to meet you.",
                "metadata": {"subject": "Meeting"}
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "content": "I'm not feeling well today.",
                "metadata": {"platform": "SMS"}
            }
        ]
        
        processed_data = processor.process(data)
        
        assert len(processed_data) == 2
        assert "analysis" in processed_data[0]
        assert "normalized" in processed_data[0]["analysis"]
        assert "sentiment" in processed_data[0]["analysis"]
        assert processed_data[0]["analysis"]["sentiment"] > 0  # "Happy to meet you" is positive
        assert processed_data[1]["analysis"]["sentiment"] < 0  # "Not feeling well" is negative