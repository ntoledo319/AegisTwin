"""
Tests for EventStore functionality.

Tests the event storage, querying, and persistence capabilities.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from hydramind.core.event_store import EventStore
from hydramind.core.exceptions import StorageError


class TestEventStore:
    """Test EventStore core functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test databases."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def event_store(self, temp_dir):
        """Create a test event store."""
        db_path = temp_dir / "test_events.db"
        return EventStore(str(db_path))

    def test_event_store_creation(self, event_store):
        """Test EventStore creation and basic functionality."""
        # Test that store was created successfully
        assert event_store is not None
        assert hasattr(event_store, 'db_path')
        assert hasattr(event_store, 'connection')

    @pytest.mark.asyncio
    async def test_event_store_initialization(self, event_store, temp_dir):
        """Test EventStore initializes correctly."""
        db_path = temp_dir / "test_events.db"
        assert str(event_store.db_path) == str(db_path)
        assert event_store.connection is not None

    @pytest.mark.asyncio
    async def test_append_event(self, event_store):
        """Test appending events to the store."""
        event = {"topic": "test/topic", "data": {"key": "value"}, "timestamp": 1234567890.0}

        # Append the event
        event_id = await event_store.append(event)

        assert event_id is not None
        assert isinstance(event_id, int)

        # Verify the event was stored by querying
        events = await event_store.query("test/topic")
        assert len(events) == 1
        assert events[0].topic == "test/topic"
        assert events[0].data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_append_multiple_events(self, event_store):
        """Test appending multiple events."""
        events = [
            {"topic": "topic1", "data": {"id": 1}, "timestamp": 1000.0},
            {"topic": "topic1", "data": {"id": 2}, "timestamp": 1001.0},
            {"topic": "topic2", "data": {"id": 3}, "timestamp": 1002.0},
        ]

        # Append all events
        event_ids = []
        for event in events:
            event_id = await event_store.append(event)
            event_ids.append(event_id)

        # Verify all events were stored
        assert len(event_ids) == 3
        assert len(set(event_ids)) == 3  # All IDs should be unique

        # Query by topic1
        topic1_events = await event_store.query("topic1")
        assert len(topic1_events) == 2
        assert topic1_events[0].data["id"] == 1
        assert topic1_events[1].data["id"] == 2

        # Query by topic2
        topic2_events = await event_store.query("topic2")
        assert len(topic2_events) == 1
        assert topic2_events[0].data["id"] == 3

    @pytest.mark.asyncio
    async def test_query_with_limit(self, event_store):
        """Test querying events with limit."""
        # Add multiple events
        for i in range(5):
            event = {"topic": "test/topic", "data": {"id": i}, "timestamp": float(1000 + i)}
            await event_store.append(event)

        # Query with limit
        events = await event_store.query("test/topic", limit=3)
        assert len(events) == 3
        assert events[0].data["id"] == 0  # Should be in timestamp order
        assert events[1].data["id"] == 1
        assert events[2].data["id"] == 2

    @pytest.mark.asyncio
    async def test_query_with_timestamp_range(self, event_store):
        """Test querying events within timestamp range."""
        # Add events with different timestamps
        timestamps = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0]
        for i, ts in enumerate(timestamps):
            event = {"topic": "test/topic", "data": {"id": i}, "timestamp": ts}
            await event_store.append(event)

        # Query within range
        events = await event_store.query(
            "test/topic",
            start_time=1001.5,
            end_time=1003.5
        )
        assert len(events) == 2
        assert events[0].data["id"] == 2  # timestamp 1002.0
        assert events[1].data["id"] == 3  # timestamp 1003.0

    @pytest.mark.asyncio
    async def test_query_nonexistent_topic(self, event_store):
        """Test querying a topic with no events."""
        events = await event_store.query("nonexistent/topic")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_dir):
        """Test that events persist across EventStore instances."""
        db_path = temp_dir / "persistent_test.db"

        # Create first instance and add events
        store1 = EventStore(str(db_path))
        event1 = {"topic": "persistent/topic", "data": {"key": "value1"}, "timestamp": 1000.0}
        event2 = {"topic": "persistent/topic", "data": {"key": "value2"}, "timestamp": 1001.0}

        await store1.append(event1)
        await store1.append(event2)

        # Close first instance
        await store1.close()

        # Create second instance with same database
        store2 = EventStore(str(db_path))

        # Verify events are still there
        events = await store2.query("persistent/topic")
        assert len(events) == 2
        assert events[0].data["key"] == "value1"
        assert events[1].data["key"] == "value2"

        await store2.close()

    @pytest.mark.asyncio
    async def test_concurrent_appends(self, event_store):
        """Test concurrent event appending."""
        async def append_event(event_id):
            event = {"topic": "concurrent/topic", "data": {"id": event_id}, "timestamp": float(1000 + event_id)}
            return await event_store.append(event)

        # Append events concurrently
        tasks = [append_event(i) for i in range(10)]
        event_ids = await asyncio.gather(*tasks)

        # Verify all events were stored
        assert len(event_ids) == 10
        assert len(set(event_ids)) == 10  # All IDs should be unique

        # Verify all events can be retrieved
        events = await event_store.query("concurrent/topic")
        assert len(events) == 10

        # Events should be in timestamp order
        for i, event in enumerate(events):
            assert event.data["id"] == i

    @pytest.mark.asyncio
    async def test_database_error_handling(self, temp_dir):
        """Test error handling for database operations."""
        # Create store with invalid path
        invalid_store = EventStore("/invalid/path/that/does/not/exist/test.db")

        # Try to append an event (should fail gracefully)
        # Create a simple event-like dict for testing
        event_data = {"topic": "test/topic", "data": {"key": "value"}, "timestamp": 1000.0}

        # This might raise an exception or handle it internally
        # The exact behavior depends on the implementation
        try:
            await invalid_store.append(event_data)
        except Exception as e:
            assert isinstance(e, (StorageError, OSError, sqlite3.Error))

        await invalid_store.close()

    @pytest.mark.asyncio
    async def test_close_store(self, event_store):
        """Test closing the event store."""
        # Verify store is open
        assert event_store.connection is not None

        # Close the store
        await event_store.close()

        # Connection should be closed
        assert event_store.connection is None

        # Trying to append after close should fail
        event = {"topic": "test/topic", "data": {"key": "value"}, "timestamp": 1000.0}
        with pytest.raises(Exception):  # Could be various types of errors
            await event_store.append(event)

    @pytest.mark.asyncio
    async def test_get_stats(self, event_store):
        """Test getting store statistics."""
        # Initially empty
        stats = await event_store.get_stats()
        assert isinstance(stats, dict)
        assert "total_events" in stats
        assert "topics_count" in stats
        assert stats["total_events"] == 0
        assert stats["topics_count"] == 0

        # Add some events
        await event_store.append({"topic": "topic1", "data": {"id": 1}, "timestamp": 1000.0})
        await event_store.append({"topic": "topic1", "data": {"id": 2}, "timestamp": 1001.0})
        await event_store.append({"topic": "topic2", "data": {"id": 3}, "timestamp": 1002.0})

        # Check updated stats
        stats = await event_store.get_stats()
        assert stats["total_events"] == 3
        assert stats["topics_count"] == 2
        assert "topic1" in stats["topics"]
        assert "topic2" in stats["topics"]
        assert stats["topics"]["topic1"] == 2
        assert stats["topics"]["topic2"] == 1


