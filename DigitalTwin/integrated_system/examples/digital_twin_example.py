#!/usr/bin/env python3
"""
Digital Twin Example

This script demonstrates the functionality of the integrated digital twin system.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/digital_twin_example.log")
    ]
)
logger = logging.getLogger(__name__)

# Import digital twin
from integrated_system.digital_twin import DigitalTwin

async def main():
    """Main function to demonstrate digital twin functionality."""
    logger.info("Starting Digital Twin Example")
    
    # Create and initialize digital twin
    logger.info("Creating digital twin")
    twin = DigitalTwin()
    await twin.initialize()
    
    # Create a session
    logger.info("Creating interaction session")
    session = await twin.create_session(
        session_id="example_session",
        metadata={
            "purpose": "demonstration",
            "created_by": "example_script"
        }
    )
    logger.info(f"Session created: {session}")
    
    # Store some memories
    logger.info("Storing memories")
    
    # Store a personal memory
    personal_memory = await twin.store_memory(
        content="The user mentioned they enjoy hiking in the mountains.",
        memory_type="episodic",
        importance=0.7,
        metadata={
            "category": "user_preference",
            "topic": "hobbies"
        }
    )
    logger.info(f"Personal memory stored: {personal_memory['memory']['id']}")
    
    # Store a factual memory
    factual_memory = await twin.store_memory(
        content="The Appalachian Trail is approximately 2,190 miles long.",
        memory_type="semantic",
        importance=0.6,
        metadata={
            "category": "fact",
            "topic": "hiking"
        }
    )
    logger.info(f"Factual memory stored: {factual_memory['memory']['id']}")
    
    # Interact with the digital twin
    logger.info("Interacting with digital twin")
    
    # Send a greeting message
    greeting_response = await twin.interact(
        input_data="Hello! How are you today?",
        input_type="message",
        session_id="example_session"
    )
    logger.info(f"Greeting response: {greeting_response['text']}")
    
    # Ask about hiking
    hiking_response = await twin.interact(
        input_data="Do you know anything about hiking?",
        input_type="message",
        session_id="example_session"
    )
    logger.info(f"Hiking response: {hiking_response['text']}")
    
    # Send an event
    event_response = await twin.interact(
        input_data={
            "type": "user_activity",
            "content": {
                "activity": "viewed_hiking_article",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "article_title": "Best Hiking Trails in North America",
                    "time_spent": 120  # seconds
                }
            }
        },
        input_type="event",
        session_id="example_session"
    )
    logger.info(f"Event response: {event_response}")
    
    # Get conversation history
    logger.info("Getting conversation history")
    history = await twin.get_conversation_history(limit=5)
    logger.info(f"Conversation history: {json.dumps(history, indent=2)}")
    
    # Search memories
    logger.info("Searching memories")
    hiking_memories = await twin.search_memories("hiking", limit=5)
    logger.info(f"Hiking memories: {json.dumps(hiking_memories, indent=2)}")
    
    # Get digital twin state
    logger.info("Getting digital twin state")
    state = await twin.get_state()
    logger.info(f"Digital twin state summary: {json.dumps({
        'cognitive_state': state.get('cognitive', {}).get('cognitive', {}),
        'personality_traits': state.get('cognitive', {}).get('personality', {}).get('traits', {}),
        'memory_stats': state.get('cognitive', {}).get('memory', {}).get('total_memories', 0),
        'conversation_metrics': state.get('cognitive', {}).get('conversation', {}).get('insights', {}).get('metrics', {})
    }, indent=2)}")
    
    # Perform maintenance
    logger.info("Performing maintenance")
    await twin.maintenance()
    
    # End the session
    logger.info("Ending session")
    session_summary = await twin.end_session("example_session")
    logger.info(f"Session summary: {json.dumps(session_summary, indent=2)}")
    
    logger.info("Digital Twin Example completed")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    
    # Run the example
    asyncio.run(main())