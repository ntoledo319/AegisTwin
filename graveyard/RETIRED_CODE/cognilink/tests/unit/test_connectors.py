"""
Unit tests for CogniLink connectors.
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Import the connectors to test
from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.pipeline.connectors.email_connector import EmailConnector
from cognilink.pipeline.connectors.message_connector import MessageConnector
from cognilink.pipeline.connectors.ios_backup_connector import iOSBackupConnector
from cognilink.pipeline.connectors.android_backup_connector import AndroidBackupConnector
from cognilink.pipeline.connectors.whatsapp_connector import WhatsAppConnector

class TestBaseConnector:
    """Tests for the BaseConnector class."""
    
    def test_init(self):
        """Test BaseConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = BaseConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {"path": "test/path", "format": "json"}
        connector = BaseConnector(config)
        
        # Should not raise an exception
        connector.validate_config()
    
    def test_validate_config_invalid(self):
        """Test config validation with invalid config."""
        # Missing path
        config = {"format": "json"}
        connector = BaseConnector(config)
        
        with pytest.raises(ValueError):
            connector.validate_config()
        
        # Missing format
        config = {"path": "test/path"}
        connector = BaseConnector(config)
        
        with pytest.raises(ValueError):
            connector.validate_config()
    
    def test_load_data_not_implemented(self):
        """Test that load_data raises NotImplementedError."""
        config = {"path": "test/path", "format": "json"}
        connector = BaseConnector(config)
        
        with pytest.raises(NotImplementedError):
            connector.load_data()
    
    def test_process_data_not_implemented(self):
        """Test that process_data raises NotImplementedError."""
        config = {"path": "test/path", "format": "json"}
        connector = BaseConnector(config)
        
        with pytest.raises(NotImplementedError):
            connector.process_data([])
    
    def test_extract_not_implemented(self):
        """Test that extract raises NotImplementedError."""
        config = {"path": "test/path", "format": "json"}
        connector = BaseConnector(config)
        
        with pytest.raises(NotImplementedError):
            connector.extract()


class TestEmailConnector:
    """Tests for the EmailConnector class."""
    
    def test_init(self):
        """Test EmailConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = EmailConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_load_data_json(self, mock_open, mock_exists):
        """Test loading data from a JSON file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps([
            {"from": "sender@example.com", "to": "recipient@example.com", "subject": "Test", "body": "Test body"}
        ])
        
        # Create connector and load data
        config = {"path": "test/path", "format": "json"}
        connector = EmailConnector(config)
        connector.load_data()
        
        # Verify data was loaded
        assert len(connector.data) == 1
        assert connector.data[0]["from"] == "sender@example.com"
        assert connector.data[0]["to"] == "recipient@example.com"
    
    def test_process_data(self):
        """Test processing email data."""
        # Sample data
        data = [
            {"from": "sender@example.com", "to": "recipient@example.com", "subject": "Test", "body": "Test body"},
            {"from": "other@example.com", "to": "recipient@example.com", "subject": "Another", "body": "Another body"}
        ]
        
        # Create connector and process data
        config = {"path": "test/path", "format": "json"}
        connector = EmailConnector(config)
        processed_data = connector.process_data(data)
        
        # Verify processed data
        assert len(processed_data) == 2
        assert processed_data[0]["type"] == "email"
        assert processed_data[0]["sender"] == "sender@example.com"
        assert processed_data[0]["recipient"] == "recipient@example.com"
        assert processed_data[0]["content"] == "Test body"
        assert "metadata" in processed_data[0]
    
    @patch.object(EmailConnector, 'load_data')
    @patch.object(EmailConnector, 'process_data')
    def test_extract(self, mock_process_data, mock_load_data):
        """Test the extract method."""
        # Setup mocks
        mock_load_data.return_value = None  # Just to satisfy the method call
        mock_process_data.return_value = [
            {"type": "email", "sender": "sender@example.com", "content": "Test"}
        ]
        
        # Create connector and extract data
        config = {"path": "test/path", "format": "json"}
        connector = EmailConnector(config)
        connector.data = [{"from": "sender@example.com", "body": "Test"}]  # Set some data
        
        result = connector.extract()
        
        # Verify extract called the right methods and returned the processed data
        mock_load_data.assert_called_once()
        mock_process_data.assert_called_once_with(connector.data)
        assert result == mock_process_data.return_value


class TestMessageConnector:
    """Tests for the MessageConnector class."""
    
    def test_init(self):
        """Test MessageConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = MessageConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_load_data_json(self, mock_open, mock_exists):
        """Test loading data from a JSON file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps([
            {"sender": "Friend", "recipient": "User", "content": "Hello", "timestamp": "2023-01-01T12:00:00"}
        ])
        
        # Create connector and load data
        config = {"path": "test/path", "format": "json"}
        connector = MessageConnector(config)
        connector.load_data()
        
        # Verify data was loaded
        assert len(connector.data) == 1
        assert connector.data[0]["sender"] == "Friend"
        assert connector.data[0]["recipient"] == "User"
    
    def test_process_data(self):
        """Test processing message data."""
        # Sample data
        data = [
            {"sender": "Friend", "recipient": "User", "content": "Hello", "timestamp": "2023-01-01T12:00:00"},
            {"sender": "User", "recipient": "Friend", "content": "Hi", "timestamp": "2023-01-01T12:01:00"}
        ]
        
        # Create connector and process data
        config = {"path": "test/path", "format": "json"}
        connector = MessageConnector(config)
        processed_data = connector.process_data(data)
        
        # Verify processed data
        assert len(processed_data) == 2
        assert processed_data[0]["type"] == "message"
        assert processed_data[0]["sender"] == "Friend"
        assert processed_data[0]["recipient"] == "User"
        assert processed_data[0]["content"] == "Hello"
        assert "timestamp" in processed_data[0]
        assert "metadata" in processed_data[0]


class TestiOSBackupConnector:
    """Tests for the iOSBackupConnector class."""
    
    def test_init(self):
        """Test iOSBackupConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = iOSBackupConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []
    
    @patch('os.path.exists')
    @patch('os.walk')
    @patch('builtins.open', new_callable=MagicMock)
    def test_load_data(self, mock_open, mock_walk, mock_exists):
        """Test loading data from an iOS backup."""
        # Setup mocks
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("test/path", ["SMS"], []),
            ("test/path/SMS", [], ["sms.db"])
        ]
        
        # Mock sqlite3 connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "Friend", "User", "Hello", "2023-01-01 12:00:00"),
            (2, "User", "Friend", "Hi", "2023-01-01 12:01:00")
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        # Create connector with mocked sqlite3
        with patch('sqlite3.connect', return_value=mock_conn):
            config = {"path": "test/path", "format": "sqlite"}
            connector = iOSBackupConnector(config)
            
            # This is a simplified test since the actual implementation would be complex
            # Just verify that the method doesn't raise an exception
            connector.load_data()


class TestAndroidBackupConnector:
    """Tests for the AndroidBackupConnector class."""
    
    def test_init(self):
        """Test AndroidBackupConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = AndroidBackupConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []


class TestWhatsAppConnector:
    """Tests for the WhatsAppConnector class."""
    
    def test_init(self):
        """Test WhatsAppConnector initialization."""
        config = {"path": "test/path", "format": "json"}
        connector = WhatsAppConnector(config)
        
        assert connector.config == config
        assert connector.path == "test/path"
        assert connector.format == "json"
        assert connector.data == []