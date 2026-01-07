"""
Example script demonstrating data import and processing using the integrated system.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components from integrated system
from core.config import config
from core.db import db_manager
from data_processing.pipeline import DataPipeline
from data_processing.storage import DocumentStore, GraphStore, VectorStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DataImportExample:
    """Example of data import and processing using the integrated system."""
    
    def __init__(self):
        """Initialize the example."""
        self.pipeline = None
        self.document_store = None
        self.graph_store = None
        self.vector_store = None
        
    async def initialize(self):
        """Initialize the components."""
        logger.info("Initializing components...")
        
        # Initialize database connections
        await db_manager.initialize()
        
        # Initialize data pipeline
        self.pipeline = DataPipeline()
        await self.pipeline.initialize()
        
        # Initialize storage components
        self.document_store = DocumentStore()
        await self.document_store.initialize()
        
        self.graph_store = GraphStore()
        await self.graph_store.initialize()
        
        self.vector_store = VectorStore()
        await self.vector_store.initialize()
        
        logger.info("Components initialized")
        
    async def shutdown(self):
        """Shutdown the components."""
        logger.info("Shutting down components...")
        
        # Shutdown data pipeline
        if self.pipeline:
            await self.pipeline.shutdown()
            
        # Close database connections
        await db_manager.shutdown()
        
        logger.info("Components shut down")
        
    async def run_example(self):
        """Run the data import example."""
        logger.info("Running data import example...")
        
        # Create example data directory if it doesn't exist
        example_data_dir = os.path.join("examples", "data")
        os.makedirs(example_data_dir, exist_ok=True)
        
        # Create example email data
        email_data_path = await self._create_example_email_data(example_data_dir)
        
        # Create example message data
        message_data_path = await self._create_example_message_data(example_data_dir)
        
        # Create example calendar data
        calendar_data_path = await self._create_example_calendar_data(example_data_dir)
        
        # Create example social media data
        social_data_path = await self._create_example_social_data(example_data_dir)
        
        # Import email data
        email_result = await self.pipeline.import_data(
            source="email",
            path=email_data_path,
            options={
                "format": "json"
            }
        )
        logger.info(f"Imported {email_result['record_count']} emails")
        
        # Import message data
        message_result = await self.pipeline.import_data(
            source="messages",
            path=message_data_path,
            options={
                "format": "json",
                "platform": "whatsapp"
            }
        )
        logger.info(f"Imported {message_result['record_count']} messages")
        
        # Import calendar data
        calendar_result = await self.pipeline.import_data(
            source="calendar",
            path=calendar_data_path,
            options={
                "format": "json"
            }
        )
        logger.info(f"Imported {calendar_result['record_count']} calendar events")
        
        # Import social media data
        social_result = await self.pipeline.import_data(
            source="social",
            path=social_data_path,
            options={
                "format": "json",
                "platform": "twitter",
                "content_type": "posts"
            }
        )
        logger.info(f"Imported {social_result['record_count']} social media posts")
        
        # Process all imported data
        processing_result = await self.pipeline.process_all()
        logger.info(f"Processed {processing_result['total_records']} records from {len(processing_result['sources'])} sources")
        
        # Store processed data in document store
        document_id = await self.document_store.store_document(
            document_type="processed_data",
            document=processing_result,
            metadata={
                "description": "Example processed data",
                "sources": processing_result["sources"]
            }
        )
        logger.info(f"Stored processed data in document store: {document_id}")
        
        # Create graph nodes and relationships
        await self._create_graph_from_data(processing_result)
        
        # Create vector embeddings
        await self._create_vectors_from_data(processing_result)
        
        logger.info("Data import example completed")
        
    async def _create_example_email_data(self, data_dir: str) -> str:
        """
        Create example email data.
        
        Args:
            data_dir: Directory to store the data
            
        Returns:
            Path to the created data file
        """
        email_data = {
            "messages": [
                {
                    "message_id": "<example1@example.com>",
                    "from": "sender@example.com",
                    "to": "recipient@example.com",
                    "subject": "Project Update",
                    "date": "2023-01-05T10:30:00Z",
                    "body": "Here's the latest update on the project. We're making good progress!",
                    "headers": {
                        "content-type": "text/plain"
                    }
                },
                {
                    "message_id": "<example2@example.com>",
                    "from": "colleague@example.com",
                    "to": "recipient@example.com",
                    "subject": "Meeting Tomorrow",
                    "date": "2023-01-06T14:45:00Z",
                    "body": "Don't forget about our meeting tomorrow at 10 AM. We'll discuss the new features.",
                    "headers": {
                        "content-type": "text/plain"
                    }
                },
                {
                    "message_id": "<example3@example.com>",
                    "from": "recipient@example.com",
                    "to": "client@example.com",
                    "subject": "Proposal Draft",
                    "date": "2023-01-07T09:15:00Z",
                    "body": "Please find attached the draft proposal for your review.",
                    "headers": {
                        "content-type": "text/plain"
                    }
                }
            ],
            "metadata": {
                "source": "example",
                "count": 3,
                "date_range": {
                    "start": "2023-01-05T10:30:00Z",
                    "end": "2023-01-07T09:15:00Z"
                }
            }
        }
        
        # Write to file
        email_data_path = os.path.join(data_dir, "example_emails.json")
        with open(email_data_path, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2)
            
        logger.info(f"Created example email data: {email_data_path}")
        
        return email_data_path
        
    async def _create_example_message_data(self, data_dir: str) -> str:
        """
        Create example message data.
        
        Args:
            data_dir: Directory to store the data
            
        Returns:
            Path to the created data file
        """
        message_data = {
            "messages": [
                {
                    "sender": "Friend",
                    "content": "Hey, how are you doing?",
                    "timestamp": "2023-01-10T18:30:00Z",
                    "type": "text"
                },
                {
                    "sender": "Me",
                    "content": "I'm good! Just working on that project we discussed.",
                    "timestamp": "2023-01-10T18:32:00Z",
                    "type": "text"
                },
                {
                    "sender": "Friend",
                    "content": "Great! How's it coming along?",
                    "timestamp": "2023-01-10T18:33:00Z",
                    "type": "text"
                },
                {
                    "sender": "Me",
                    "content": "Making good progress. Should be done by next week.",
                    "timestamp": "2023-01-10T18:35:00Z",
                    "type": "text"
                },
                {
                    "sender": "Friend",
                    "content": "Awesome! Let's catch up this weekend.",
                    "timestamp": "2023-01-10T18:36:00Z",
                    "type": "text"
                }
            ],
            "name": "Friend",
            "type": "individual",
            "participants": ["Friend", "Me"]
        }
        
        # Write to file
        message_data_path = os.path.join(data_dir, "example_messages.json")
        with open(message_data_path, 'w', encoding='utf-8') as f:
            json.dump(message_data, f, indent=2)
            
        logger.info(f"Created example message data: {message_data_path}")
        
        return message_data_path
        
    async def _create_example_calendar_data(self, data_dir: str) -> str:
        """
        Create example calendar data.
        
        Args:
            data_dir: Directory to store the data
            
        Returns:
            Path to the created data file
        """
        calendar_data = {
            "events": [
                {
                    "uid": "event1@example.com",
                    "summary": "Team Meeting",
                    "description": "Weekly team sync meeting",
                    "location": "Conference Room A",
                    "start": "2023-01-15T10:00:00Z",
                    "end": "2023-01-15T11:00:00Z",
                    "all_day": False,
                    "recurring": False,
                    "attendees": ["person1@example.com", "person2@example.com"]
                },
                {
                    "uid": "event2@example.com",
                    "summary": "Project Deadline",
                    "description": "Final submission for Q1 project",
                    "location": "Office",
                    "start": "2023-01-20T17:00:00Z",
                    "end": "2023-01-20T18:00:00Z",
                    "all_day": False,
                    "recurring": False,
                    "attendees": []
                },
                {
                    "uid": "event3@example.com",
                    "summary": "Lunch with Client",
                    "description": "Discuss new project opportunities",
                    "location": "Downtown Cafe",
                    "start": "2023-01-25T12:00:00Z",
                    "end": "2023-01-25T13:30:00Z",
                    "all_day": False,
                    "recurring": False,
                    "attendees": ["client@example.com"]
                }
            ]
        }
        
        # Write to file
        calendar_data_path = os.path.join(data_dir, "example_calendar.json")
        with open(calendar_data_path, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, indent=2)
            
        logger.info(f"Created example calendar data: {calendar_data_path}")
        
        return calendar_data_path
        
    async def _create_example_social_data(self, data_dir: str) -> str:
        """
        Create example social media data.
        
        Args:
            data_dir: Directory to store the data
            
        Returns:
            Path to the created data file
        """
        social_data = {
            "user": {
                "id": "user123",
                "username": "example_user",
                "name": "Example User",
                "description": "This is an example user profile",
                "followers_count": 1000,
                "following_count": 500,
                "created_at": "2020-01-01T00:00:00Z"
            },
            "tweets": [
                {
                    "id": "tweet1",
                    "text": "Just started working on an exciting new project! #coding #project",
                    "created_at": "2023-01-08T09:00:00Z",
                    "retweet_count": 5,
                    "favorite_count": 10,
                    "reply_count": 2,
                    "entities": {
                        "hashtags": [
                            {"text": "coding"},
                            {"text": "project"}
                        ],
                        "user_mentions": [],
                        "urls": []
                    }
                },
                {
                    "id": "tweet2",
                    "text": "Great meeting with @colleague today about the new features.",
                    "created_at": "2023-01-12T15:30:00Z",
                    "retweet_count": 0,
                    "favorite_count": 3,
                    "reply_count": 1,
                    "entities": {
                        "hashtags": [],
                        "user_mentions": [
                            {"screen_name": "colleague"}
                        ],
                        "urls": []
                    }
                },
                {
                    "id": "tweet3",
                    "text": "Check out this interesting article: https://example.com/article",
                    "created_at": "2023-01-18T12:45:00Z",
                    "retweet_count": 8,
                    "favorite_count": 15,
                    "reply_count": 0,
                    "entities": {
                        "hashtags": [],
                        "user_mentions": [],
                        "urls": [
                            {"expanded_url": "https://example.com/article"}
                        ]
                    }
                }
            ]
        }
        
        # Write to file
        social_data_path = os.path.join(data_dir, "example_social.json")
        with open(social_data_path, 'w', encoding='utf-8') as f:
            json.dump(social_data, f, indent=2)
            
        logger.info(f"Created example social media data: {social_data_path}")
        
        return social_data_path
        
    async def _create_graph_from_data(self, processed_data: Dict[str, Any]):
        """
        Create graph nodes and relationships from processed data.
        
        Args:
            processed_data: Processed data
        """
        logger.info("Creating graph from processed data...")
        
        # Create user node
        user_id = await self.graph_store.create_node(
            label="User",
            properties={
                "name": "Example User",
                "email": "recipient@example.com"
            }
        )
        logger.info(f"Created user node: {user_id}")
        
        # Create contact nodes
        contacts = {
            "sender@example.com": await self.graph_store.create_node(
                label="Contact",
                properties={
                    "email": "sender@example.com",
                    "name": "Sender"
                }
            ),
            "colleague@example.com": await self.graph_store.create_node(
                label="Contact",
                properties={
                    "email": "colleague@example.com",
                    "name": "Colleague"
                }
            ),
            "client@example.com": await self.graph_store.create_node(
                label="Contact",
                properties={
                    "email": "client@example.com",
                    "name": "Client"
                }
            ),
            "Friend": await self.graph_store.create_node(
                label="Contact",
                properties={
                    "name": "Friend",
                    "platform": "whatsapp"
                }
            )
        }
        logger.info(f"Created {len(contacts)} contact nodes")
        
        # Create communication relationships
        for contact_id in contacts.values():
            await self.graph_store.create_relationship(
                source_id=user_id,
                target_id=contact_id,
                type_name="COMMUNICATES_WITH",
                properties={
                    "frequency": "regular",
                    "last_communication": datetime.now().isoformat()
                }
            )
        logger.info(f"Created communication relationships")
        
        # Create event nodes
        events = [
            await self.graph_store.create_node(
                label="Event",
                properties={
                    "name": "Team Meeting",
                    "date": "2023-01-15T10:00:00Z",
                    "location": "Conference Room A"
                }
            ),
            await self.graph_store.create_node(
                label="Event",
                properties={
                    "name": "Project Deadline",
                    "date": "2023-01-20T17:00:00Z",
                    "location": "Office"
                }
            ),
            await self.graph_store.create_node(
                label="Event",
                properties={
                    "name": "Lunch with Client",
                    "date": "2023-01-25T12:00:00Z",
                    "location": "Downtown Cafe"
                }
            )
        ]
        logger.info(f"Created {len(events)} event nodes")
        
        # Create participation relationships
        await self.graph_store.create_relationship(
            source_id=user_id,
            target_id=events[0],
            type_name="PARTICIPATES_IN",
            properties={}
        )
        await self.graph_store.create_relationship(
            source_id=contacts["colleague@example.com"],
            target_id=events[0],
            type_name="PARTICIPATES_IN",
            properties={}
        )
        await self.graph_store.create_relationship(
            source_id=user_id,
            target_id=events[1],
            type_name="PARTICIPATES_IN",
            properties={}
        )
        await self.graph_store.create_relationship(
            source_id=user_id,
            target_id=events[2],
            type_name="PARTICIPATES_IN",
            properties={}
        )
        await self.graph_store.create_relationship(
            source_id=contacts["client@example.com"],
            target_id=events[2],
            type_name="PARTICIPATES_IN",
            properties={}
        )
        logger.info(f"Created participation relationships")
        
    async def _create_vectors_from_data(self, processed_data: Dict[str, Any]):
        """
        Create vector embeddings from processed data.
        
        Args:
            processed_data: Processed data
        """
        logger.info("Creating vector embeddings from processed data...")
        
        # In a real implementation, we would use a proper embedding model
        # For this example, we'll create random vectors
        
        # Create email embeddings
        for i, result in enumerate(processed_data["processing_results"].values()):
            if "processed_messages" in result:
                for j, message in enumerate(result["processed_messages"]):
                    if "content" in message:
                        # Create a simple embedding (random for this example)
                        embedding = [float(hash(message["content"] + str(j)) % 1000) / 1000 for _ in range(10)]
                        
                        # Store in vector store
                        await self.vector_store.store_vector(
                            collection="messages",
                            vector_id=f"message_{i}_{j}",
                            vector=embedding,
                            metadata={
                                "content": message["content"],
                                "sender": message.get("sender", ""),
                                "timestamp": message.get("timestamp", ""),
                                "platform": message.get("platform", "")
                            }
                        )
            elif "processed_posts" in result:
                for j, post in enumerate(result["processed_posts"]):
                    if "text" in post:
                        # Create a simple embedding (random for this example)
                        embedding = [float(hash(post["text"] + str(j)) % 1000) / 1000 for _ in range(10)]
                        
                        # Store in vector store
                        await self.vector_store.store_vector(
                            collection="posts",
                            vector_id=f"post_{i}_{j}",
                            vector=embedding,
                            metadata={
                                "text": post["text"],
                                "created_at": post.get("created_at", ""),
                                "platform": post.get("platform", "")
                            }
                        )
                        
        logger.info("Created vector embeddings")

async def main():
    """Run the data import example."""
    example = DataImportExample()
    try:
        await example.initialize()
        await example.run_example()
    finally:
        await example.shutdown()

if __name__ == "__main__":
    asyncio.run(main())