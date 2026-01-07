"""
Integration tests for CogniLink pipeline components.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock

from cognilink.pipeline.connectors.email_connector import EmailConnector
from cognilink.pipeline.connectors.message_connector import MessageConnector
from cognilink.pipeline.processors.text_processor import TextProcessor

class TestPipelineIntegration:
    """Integration tests for the pipeline components."""
    
    def test_connector_to_processor_flow(self, sample_email_file, sample_message_file):
        """Test the flow from connectors to processors."""
        # Set up email connector
        email_config = {
            "path": str(sample_email_file),
            "format": "json"
        }
        email_connector = EmailConnector(email_config)
        
        # Set up message connector
        message_config = {
            "path": str(sample_message_file),
            "format": "json"
        }
        message_connector = MessageConnector(message_config)
        
        # Set up text processor
        processor_config = {
            "language": "en",
            "use_spacy": False
        }
        text_processor = TextProcessor(processor_config)
        
        # Extract data from connectors
        email_data = email_connector.extract()
        message_data = message_connector.extract()
        
        # Combine data
        combined_data = email_data + message_data
        
        # Process data
        processed_data = text_processor.process(combined_data)
        
        # Verify results
        assert len(processed_data) == len(combined_data)
        for item in processed_data:
            assert "analysis" in item
            assert "normalized" in item["analysis"]
            assert "sentiment" in item["analysis"]
            assert "entities" in item["analysis"]
    
    def test_multiple_connector_integration(self, temp_data_dir):
        """Test integration with multiple connectors."""
        # Create sample data files
        email_file = temp_data_dir / "emails.json"
        with open(email_file, 'w') as f:
            json.dump([
                {
                    "from": "sender@example.com",
                    "to": "recipient@example.com",
                    "subject": "Test Email",
                    "body": "This is a test email for testing purposes.",
                    "date": "2023-01-01T12:00:00"
                }
            ], f)
        
        message_file = temp_data_dir / "messages.json"
        with open(message_file, 'w') as f:
            json.dump([
                {
                    "sender": "Friend",
                    "recipient": "User",
                    "content": "Hey, how are you doing?",
                    "timestamp": "2023-01-01T10:15:00",
                    "platform": "SMS"
                }
            ], f)
        
        # Set up connectors
        email_connector = EmailConnector({
            "path": str(email_file),
            "format": "json"
        })
        
        message_connector = MessageConnector({
            "path": str(message_file),
            "format": "json"
        })
        
        # Set up processor
        text_processor = TextProcessor({
            "language": "en",
            "use_spacy": False
        })
        
        # Extract and process data
        all_data = []
        all_data.extend(email_connector.extract())
        all_data.extend(message_connector.extract())
        
        processed_data = text_processor.process(all_data)
        
        # Verify results
        assert len(processed_data) == 2
        assert processed_data[0]["type"] == "email"
        assert processed_data[1]["type"] == "message"
        assert "analysis" in processed_data[0]
        assert "analysis" in processed_data[1]
    
    @patch('os.path.exists')
    def test_error_handling_in_pipeline(self, mock_exists):
        """Test error handling in the pipeline."""
        # Make file existence check fail
        mock_exists.return_value = False
        
        # Set up email connector with non-existent file
        email_config = {
            "path": "non_existent_file.json",
            "format": "json"
        }
        email_connector = EmailConnector(email_config)
        
        # Attempt to extract data (should handle the error)
        with pytest.raises(FileNotFoundError):
            email_connector.extract()