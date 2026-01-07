"""
Test configuration for Digital Twin tests.

This module provides fixtures and configuration for testing the Digital Twin components.
"""

import pytest
import os
import sys
import asyncio
from typing import Dict, Any

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import Digital Twin components
from digital_twin import PersonalityEngine, MemorySystem, ConversationEngine
from digital_twin.config import get_config


@pytest.fixture
def config():
    """
    Fixture for test configuration.
    """
    # Get the configuration
    config = get_config()
    
    # Override configuration for testing
    config.set("memory_system.episodic_memory_dir", "tests/data/memories/episodic")
    config.set("memory_system.semantic_memory_dir", "tests/data/memories/semantic")
    config.set("memory_system.procedural_memory_dir", "tests/data/memories/procedural")
    config.set("memory_system.index_dir", "tests/data/memories/index")
    
    return config


@pytest.fixture
def personality_engine(config):
    """
    Fixture for PersonalityEngine.
    """
    return PersonalityEngine(config.get_section("personality_engine"))


@pytest.fixture
def memory_system(config):
    """
    Fixture for MemorySystem.
    """
    return MemorySystem(config.get_section("memory_system"))


@pytest.fixture
def conversation_engine(personality_engine, memory_system, config):
    """
    Fixture for ConversationEngine.
    """
    return ConversationEngine(
        personality_engine=personality_engine,
        memory_system=memory_system,
        config=config.get_section("conversation_engine")
    )


@pytest.fixture
def sample_user_data():
    """
    Fixture for sample user data.
    """
    return {
        "text": {
            "content": """
            I really enjoy hiking in the mountains and exploring nature. It gives me time to think
            and appreciate the beauty around us. I also love reading science fiction books and
            watching documentaries about space and technology. I believe it's important to keep
            learning throughout life. While I enjoy social gatherings with close friends, I also
            value my alone time to recharge and reflect.
            """
        },
        "communication": {
            "messages": [
                {
                    "content": "Hey, how are you doing today?",
                    "timestamp": "2025-09-26T10:15:30",
                    "is_sender": True
                },
                {
                    "content": "I'm doing well, thanks for asking! How about you?",
                    "timestamp": "2025-09-26T10:16:45",
                    "is_sender": False
                },
                {
                    "content": "Pretty good. I was wondering if you'd like to join us for dinner on Friday?",
                    "timestamp": "2025-09-26T10:17:30",
                    "is_sender": True
                }
            ]
        }
    }


@pytest.fixture
def sample_memory_content():
    """
    Fixture for sample memory content.
    """
    return {
        "title": "First hiking trip",
        "description": "Went hiking in the Rocky Mountains for the first time",
        "date": "2025-08-15",
        "location": "Rocky Mountain National Park",
        "people": ["Alex", "Jamie"],
        "emotions": ["excited", "peaceful", "accomplished"],
        "details": "Started at Bear Lake trailhead, hiked to Emerald Lake. Weather was perfect."
    }


@pytest.fixture
def run_async():
    """
    Fixture for running async functions in tests.
    """
    def _run_async(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    return _run_async