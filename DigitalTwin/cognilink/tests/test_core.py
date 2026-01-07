"""
Tests for CogniLink core components.
"""

import os
import unittest
import tempfile
import json
from datetime import datetime

from cognilink.core.config import get_config_manager
from cognilink.core.comm_graph import CommunicationGraph
from cognilink.core.utils import normalize_email, normalize_phone, generate_message_id

class TestConfig(unittest.TestCase):
    """Tests for the configuration system."""
    
    def test_get_config_manager(self):
        """Test getting the config manager."""
        config_manager = get_config_manager()
        self.assertIsNotNone(config_manager)
    
    def test_get_value(self):
        """Test getting configuration values."""
        config_manager = get_config_manager()
        
        # Test with default value
        value = config_manager.get_value('nonexistent', 'nonexistent', 'default')
        self.assertEqual(value, 'default')

class TestCommunicationGraph(unittest.TestCase):
    """Tests for the communication graph."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.graph = CommunicationGraph()
        
        # Add some test communications
        self.graph.add_communication(
            sender="alice@example.com",
            recipients=["bob@example.com"],
            timestamp=datetime.now(),
            message_id="msg1",
            metadata={"subject": "Test", "content": "Hello Bob"}
        )
        
        self.graph.add_communication(
            sender="bob@example.com",
            recipients=["alice@example.com"],
            timestamp=datetime.now(),
            message_id="msg2",
            metadata={"subject": "Re: Test", "content": "Hello Alice"}
        )
        
        self.graph.add_communication(
            sender="alice@example.com",
            recipients=["charlie@example.com"],
            timestamp=datetime.now(),
            message_id="msg3",
            metadata={"subject": "Hello", "content": "Hello Charlie"}
        )
    
    def test_graph_structure(self):
        """Test the graph structure."""
        # Check nodes
        self.assertEqual(self.graph.graph.number_of_nodes(), 3)
        self.assertIn("alice@example.com", self.graph.graph.nodes())
        self.assertIn("bob@example.com", self.graph.graph.nodes())
        self.assertIn("charlie@example.com", self.graph.graph.nodes())
        
        # Check edges
        self.assertEqual(self.graph.graph.number_of_edges(), 3)
        self.assertTrue(self.graph.graph.has_edge("alice@example.com", "bob@example.com"))
        self.assertTrue(self.graph.graph.has_edge("bob@example.com", "alice@example.com"))
        self.assertTrue(self.graph.graph.has_edge("alice@example.com", "charlie@example.com"))
    
    def test_top_communicators(self):
        """Test getting top communicators."""
        top = self.graph.get_top_communicators(2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0][0], "alice@example.com")  # Alice should be first
    
    def test_strongest_relationships(self):
        """Test getting strongest relationships."""
        strongest = self.graph.get_strongest_relationships(1)
        self.assertEqual(len(strongest), 1)
        self.assertEqual(strongest[0][0], "alice@example.com")
        self.assertEqual(strongest[0][1], "bob@example.com")
    
    def test_save_load(self):
        """Test saving and loading the graph."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            filepath = tmp.name
        
        try:
            # Save the graph
            self.graph.save_to_file(filepath)
            
            # Load the graph
            loaded_graph = CommunicationGraph.load_from_file(filepath)
            
            # Check that the loaded graph has the same structure
            self.assertEqual(loaded_graph.graph.number_of_nodes(), self.graph.graph.number_of_nodes())
            self.assertEqual(loaded_graph.graph.number_of_edges(), self.graph.graph.number_of_edges())
            
            # Check that the metadata was preserved
            self.assertEqual(loaded_graph.metadata['message_count'], self.graph.metadata['message_count'])
        
        finally:
            # Clean up
            if os.path.exists(filepath):
                os.remove(filepath)

class TestUtils(unittest.TestCase):
    """Tests for utility functions."""
    
    def test_normalize_email(self):
        """Test email normalization."""
        self.assertEqual(normalize_email("Alice@Example.COM"), "alice@example.com")
        self.assertEqual(normalize_email(" alice@example.com "), "alice@example.com")
        self.assertEqual(normalize_email("mailto:alice@example.com"), "alice@example.com")
    
    def test_normalize_phone(self):
        """Test phone number normalization."""
        self.assertEqual(normalize_phone("+1 (555) 123-4567"), "5551234567")
        self.assertEqual(normalize_phone("555-123-4567"), "5551234567")
        self.assertEqual(normalize_phone("15551234567"), "5551234567")
    
    def test_generate_message_id(self):
        """Test message ID generation."""
        # Same message data should produce the same ID
        message1 = {
            "sender": "alice@example.com",
            "recipients": ["bob@example.com"],
            "subject": "Test",
            "content": "Hello"
        }
        
        message2 = {
            "sender": "alice@example.com",
            "recipients": ["bob@example.com"],
            "subject": "Test",
            "content": "Hello"
        }
        
        self.assertEqual(generate_message_id(message1), generate_message_id(message2))
        
        # Different message data should produce different IDs
        message3 = {
            "sender": "alice@example.com",
            "recipients": ["charlie@example.com"],
            "subject": "Test",
            "content": "Hello"
        }
        
        self.assertNotEqual(generate_message_id(message1), generate_message_id(message3))

if __name__ == '__main__':
    unittest.main()