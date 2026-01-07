"""
Example script demonstrating the usage of the Digital Twin components.

This script shows how to initialize and use the Personality Engine, Memory System,
and Conversation Engine components of the Digital Twin.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any, List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import Digital Twin components
from digital_twin import PersonalityEngine, MemorySystem, ConversationEngine
from digital_twin.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


async def main():
    """
    Main function demonstrating Digital Twin usage.
    """
    logger.info("Initializing Digital Twin components...")
    
    # Get configuration
    config = get_config()
    
    # Initialize components
    personality_engine = PersonalityEngine(config.get_section("personality_engine"))
    memory_system = MemorySystem(config.get_section("memory_system"))
    conversation_engine = ConversationEngine(
        personality_engine=personality_engine,
        memory_system=memory_system,
        config=config.get_section("conversation_engine")
    )
    
    # Example user data
    user_id = "user123"
    user_data = {
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
    
    # Extract personality traits
    logger.info("Extracting personality traits...")
    traits = await personality_engine.extract_traits(user_data)
    logger.info(f"Extracted traits: {json.dumps(traits, indent=2)}")
    
    # Create personality profile
    logger.info("Creating personality profile...")
    profile = await personality_engine.create_personality_profile(user_id, traits)
    logger.info(f"Created profile with dimensions: {json.dumps(profile['dimensions'], indent=2)}")
    
    # Store a memory
    logger.info("Storing a memory...")
    memory_content = {
        "title": "First hiking trip",
        "description": "Went hiking in the Rocky Mountains for the first time",
        "date": "2025-08-15",
        "location": "Rocky Mountain National Park",
        "people": ["Alex", "Jamie"],
        "emotions": ["excited", "peaceful", "accomplished"],
        "details": "Started at Bear Lake trailhead, hiked to Emerald Lake. Weather was perfect."
    }
    
    memory_id = await memory_system.store_memory(
        user_id=user_id,
        memory_type="episodic",
        content=memory_content
    )
    logger.info(f"Stored memory with ID: {memory_id}")
    
    # Process a conversation message
    logger.info("Processing a conversation message...")
    message = "Tell me about hiking trails in the Rocky Mountains."
    context = {}
    
    response = await conversation_engine.process_message(
        user_id=user_id,
        message=message,
        context=context
    )
    
    logger.info(f"Response: {response['response']}")
    logger.info(f"Updated context: {json.dumps(response['context'], indent=2)}")
    logger.info(f"Message analysis: {json.dumps(response['analysis'], indent=2)}")
    
    # Retrieve a memory
    logger.info("Retrieving memories...")
    memories = await memory_system.retrieve_memory(
        user_id=user_id,
        query={"keywords": ["hiking", "mountains"]},
        limit=5
    )
    
    logger.info(f"Retrieved {len(memories)} memories")
    for memory in memories:
        logger.info(f"Memory: {json.dumps(memory, indent=2)}")
    
    logger.info("Digital Twin example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())