"""
Tests for the data processing components of the integrated system.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processing.connectors import (
    BaseConnector,
    EmailConnector,
    MessagesConnector,
    CalendarConnector,
    SocialConnector
)
from data_processing.pipeline import DataPipeline
from data_processing.storage import DocumentStore, GraphStore, VectorStore

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_email_connector():
    """Test the email connector."""
    # Create connector
    connector = EmailConnector()
    
    # Test connection
    credentials = {"provider": "gmail", "email": "test@gmail.com", "password": "password"}
    result = await connector.connect(credentials)
    assert result is True
    assert connector.is_connected is True
    
    # Test disconnection
    result = await connector.disconnect()
    assert result is True
    assert connector.is_connected is False

@pytest.mark.asyncio
async def test_messages_connector():
    """Test the messages connector."""
    # Create connector
    connector = MessagesConnector()
    
    # Test connection
    credentials = {"provider": "whatsapp"}
    result = await connector.connect(credentials)
    assert result is True
    assert connector.is_connected is True
    
    # Test disconnection
    result = await connector.disconnect()
    assert result is True
    assert connector.is_connected is False

@pytest.mark.asyncio
async def test_calendar_connector():
    """Test the calendar connector."""
    # Create connector
    connector = CalendarConnector()
    
    # Test connection
    credentials = {"provider": "google"}
    result = await connector.connect(credentials)
    assert result is True
    assert connector.is_connected is True
    
    # Test disconnection
    result = await connector.disconnect()
    assert result is True
    assert connector.is_connected is False

@pytest.mark.asyncio
async def test_social_connector():
    """Test the social connector."""
    # Create connector
    connector = SocialConnector()
    
    # Test connection
    credentials = {"provider": "twitter"}
    result = await connector.connect(credentials)
    assert result is True
    assert connector.is_connected is True
    
    # Test disconnection
    result = await connector.disconnect()
    assert result is True
    assert connector.is_connected is False

@pytest.mark.asyncio
async def test_data_pipeline():
    """Test the data pipeline."""
    # Create pipeline
    pipeline = DataPipeline()
    
    # Mock connectors
    pipeline.connectors = {
        "email": MagicMock(),
        "messages": MagicMock(),
        "calendar": MagicMock(),
        "social": MagicMock()
    }
    
    # Mock import_data method
    pipeline.connectors["email"].import_data = MagicMock(return_value=asyncio.Future())
    pipeline.connectors["email"].import_data.return_value.set_result({
        "status": "success",
        "message": "Imported 3 emails",
        "record_count": 3,
        "messages": [{"id": 1}, {"id": 2}, {"id": 3}],
        "metadata": {"source": "email"}
    })
    
    # Test import_data
    result = await pipeline.import_data("email", "path/to/data.json")
    assert result["status"] == "success"
    assert result["record_count"] == 3
    assert "import_id" in result
    
    # Mock process_batch method
    pipeline.connectors["email"].process_batch = MagicMock(return_value=asyncio.Future())
    pipeline.connectors["email"].process_batch.return_value.set_result({
        "status": "success",
        "message": "Processed 3 emails",
        "record_count": 3,
        "processed_messages": [{"id": 1}, {"id": 2}, {"id": 3}],
        "metadata": {"source": "email"}
    })
    
    # Test process_batch
    result = await pipeline.process_batch("email", {"messages": [{"id": 1}, {"id": 2}, {"id": 3}]})
    assert result["status"] == "success"
    assert result["record_count"] == 3
    assert "batch_id" in result

@pytest.mark.asyncio
async def test_document_store():
    """Test the document store."""
    # Create document store
    document_store = DocumentStore()
    
    # Initialize
    await document_store.initialize()
    
    # Create test document
    test_document = {
        "title": "Test Document",
        "content": "This is a test document.",
        "tags": ["test", "document"]
    }
    
    # Store document
    document_id = await document_store.store_document(
        document_type="test",
        document=test_document,
        metadata={"description": "Test document for unit tests"}
    )
    
    # Verify document ID
    assert document_id is not None
    assert document_id.startswith("test_")
    
    # Get document
    document = await document_store.get_document(document_id)
    
    # Verify document
    assert document is not None
    assert document["document_type"] == "test"
    assert document["document"]["title"] == "Test Document"
    assert document["document"]["content"] == "This is a test document."
    assert "test" in document["document"]["tags"]
    assert document["metadata"]["description"] == "Test document for unit tests"
    
    # Update document
    result = await document_store.update_document(
        document_id=document_id,
        updates={"document": {"title": "Updated Test Document"}}
    )
    
    # Verify update
    assert result is True
    
    # Get updated document
    updated_document = await document_store.get_document(document_id)
    
    # Verify updated document
    assert updated_document is not None
    assert updated_document["document"]["title"] == "Updated Test Document"
    
    # Delete document
    result = await document_store.delete_document(document_id)
    
    # Verify deletion
    assert result is True
    
    # Try to get deleted document
    deleted_document = await document_store.get_document(document_id)
    
    # Verify document is deleted
    assert deleted_document is None

@pytest.mark.asyncio
async def test_graph_store():
    """Test the graph store."""
    # Create graph store
    graph_store = GraphStore()
    
    # Initialize
    await graph_store.initialize()
    
    # Create test nodes
    user_id = await graph_store.create_node(
        label="User",
        properties={
            "name": "Test User",
            "email": "test@example.com"
        }
    )
    
    contact_id = await graph_store.create_node(
        label="Contact",
        properties={
            "name": "Test Contact",
            "email": "contact@example.com"
        }
    )
    
    # Verify node IDs
    assert user_id is not None
    assert contact_id is not None
    
    # Create test relationship
    relationship_id = await graph_store.create_relationship(
        source_id=user_id,
        target_id=contact_id,
        type_name="KNOWS",
        properties={
            "since": "2023-01-01"
        }
    )
    
    # Verify relationship ID
    assert relationship_id is not None
    
    # Get nodes
    user_node = await graph_store.get_node(user_id)
    contact_node = await graph_store.get_node(contact_id)
    
    # Verify nodes
    assert user_node is not None
    assert user_node["properties"]["name"] == "Test User"
    assert user_node["properties"]["email"] == "test@example.com"
    
    assert contact_node is not None
    assert contact_node["properties"]["name"] == "Test Contact"
    assert contact_node["properties"]["email"] == "contact@example.com"
    
    # Get relationship
    relationship = await graph_store.get_relationship(relationship_id)
    
    # Verify relationship
    assert relationship is not None
    assert relationship["source_id"] == user_id
    assert relationship["target_id"] == contact_id
    assert relationship["type"] == "KNOWS"
    assert relationship["properties"]["since"] == "2023-01-01"
    
    # Get neighbors
    neighbors = await graph_store.get_neighbors(user_id)
    
    # Verify neighbors
    assert len(neighbors) == 1
    assert neighbors[0]["node"]["properties"]["name"] == "Test Contact"
    assert neighbors[0]["relationship"]["type"] == "KNOWS"
    
    # Update node
    result = await graph_store.update_node(
        node_id=user_id,
        properties={"name": "Updated Test User"}
    )
    
    # Verify update
    assert result is True
    
    # Get updated node
    updated_user = await graph_store.get_node(user_id)
    
    # Verify updated node
    assert updated_user is not None
    assert updated_user["properties"]["name"] == "Updated Test User"
    
    # Delete relationship
    result = await graph_store.delete_relationship(relationship_id)
    
    # Verify deletion
    assert result is True
    
    # Delete nodes
    result1 = await graph_store.delete_node(user_id)
    result2 = await graph_store.delete_node(contact_id)
    
    # Verify deletion
    assert result1 is True
    assert result2 is True

@pytest.mark.asyncio
async def test_vector_store():
    """Test the vector store."""
    # Create vector store
    vector_store = VectorStore()
    
    # Initialize
    await vector_store.initialize()
    
    # Create test vector
    vector_id = "test_vector"
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]
    metadata = {"description": "Test vector"}
    
    result = await vector_store.store_vector(
        collection="test_collection",
        vector_id=vector_id,
        vector=vector,
        metadata=metadata
    )
    
    # Verify storage
    assert result is True
    
    # Get vector
    vector_data = await vector_store.get_vector("test_collection", vector_id)
    
    # Verify vector
    assert vector_data is not None
    assert vector_data["id"] == vector_id
    assert vector_data["collection"] == "test_collection"
    assert vector_data["vector"] == vector
    assert vector_data["metadata"]["description"] == "Test vector"
    
    # Update vector metadata
    result = await vector_store.update_vector_metadata(
        collection="test_collection",
        vector_id=vector_id,
        metadata={"description": "Updated test vector"}
    )
    
    # Verify update
    assert result is True
    
    # Get updated vector
    updated_vector = await vector_store.get_vector("test_collection", vector_id)
    
    # Verify updated vector
    assert updated_vector is not None
    assert updated_vector["metadata"]["description"] == "Updated test vector"
    
    # Search vectors
    # For this test, we'll just search for the vector we just created
    search_results = await vector_store.search_vectors(
        collection="test_collection",
        query_vector=vector,
        limit=10
    )
    
    # Verify search results
    assert len(search_results) > 0
    assert search_results[0]["id"] == vector_id
    assert search_results[0]["similarity"] > 0.9  # Should be very similar to itself
    
    # Delete vector
    result = await vector_store.delete_vector("test_collection", vector_id)
    
    # Verify deletion
    assert result is True
    
    # Try to get deleted vector
    deleted_vector = await vector_store.get_vector("test_collection", vector_id)
    
    # Verify vector is deleted
    assert deleted_vector is None