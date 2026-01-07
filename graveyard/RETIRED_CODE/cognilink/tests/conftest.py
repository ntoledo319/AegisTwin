"""
Test fixtures for CogniLink tests.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def sample_config():
    """Return a sample configuration dictionary for testing."""
    return {
        "connectors": {
            "email": {
                "enabled": True,
                "path": "path/to/emails"
            },
            "message": {
                "enabled": True,
                "path": "path/to/messages"
            }
        },
        "processors": {
            "text": {
                "enabled": True,
                "language": "en"
            }
        },
        "analysis": {
            "patterns": {
                "enabled": True
            },
            "relationships": {
                "enabled": True
            },
            "topics": {
                "enabled": True
            }
        },
        "interface": {
            "cli": {
                "enabled": True,
                "color": True
            },
            "web": {
                "enabled": False,
                "port": 8080
            }
        }
    }

@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)

@pytest.fixture
def sample_email_data():
    """Return sample email data for testing."""
    return [
        {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email for testing purposes.",
            "date": "2023-01-01T12:00:00",
            "attachments": []
        },
        {
            "from": "another@example.com",
            "to": "recipient@example.com",
            "subject": "Another Test",
            "body": "This is another test email with different content.",
            "date": "2023-01-02T14:30:00",
            "attachments": []
        }
    ]

@pytest.fixture
def sample_message_data():
    """Return sample message data for testing."""
    return [
        {
            "sender": "Friend",
            "recipient": "User",
            "content": "Hey, how are you doing?",
            "timestamp": "2023-01-01T10:15:00",
            "platform": "SMS"
        },
        {
            "sender": "User",
            "recipient": "Friend",
            "content": "I'm good, thanks! How about you?",
            "timestamp": "2023-01-01T10:16:00",
            "platform": "SMS"
        },
        {
            "sender": "Colleague",
            "recipient": "User",
            "content": "Can you send me that report?",
            "timestamp": "2023-01-02T09:30:00",
            "platform": "SMS"
        }
    ]

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_email_file(temp_data_dir, sample_email_data):
    """Create a sample email file for testing."""
    email_file = temp_data_dir / "emails.json"
    with open(email_file, 'w') as f:
        json.dump(sample_email_data, f)
    return email_file

@pytest.fixture
def sample_message_file(temp_data_dir, sample_message_data):
    """Create a sample message file for testing."""
    message_file = temp_data_dir / "messages.json"
    with open(message_file, 'w') as f:
        json.dump(sample_message_data, f)
    return message_file

@pytest.fixture
def mock_connector_config():
    """Return a mock connector configuration."""
    return {
        "path": "path/to/data",
        "format": "json",
        "encoding": "utf-8",
        "options": {
            "recursive": True,
            "include_metadata": True
        }
    }