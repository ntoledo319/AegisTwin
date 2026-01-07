"""
Tests for EventBus functionality.

Tests the event bus messaging system, subscriptions, and message routing.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock
from hydramind.core.bus import EventBus, Message
from hydramind.core.event_store import EventStore
from hydramind.core.exceptions import EventBusError


class TestEventBus:
    """Test EventBus core functionality."""

    @pytest.fixture
    def event_store(self, temp_dir):
        """Create a test event store."""
        db_path = temp_dir / "test_events.db"
        return EventStore(str(db_path))

    @pytest.fixture
    def event_bus(self, event_store):
        """Create a test event bus."""
        return EventBus(event_store)

    @pytest.mark.asyncio
    async def test_event_bus_initialization(self, event_bus):
        """Test EventBus initializes correctly."""
        assert event_bus.store is not None
        assert isinstance(event_bus.subscriptions, dict)
        assert len(event_bus.subscriptions) == 0

    @pytest.mark.asyncio
    async def test_message_creation(self, event_bus):
        """Test Message creation and validation."""
        # Valid message
        msg = Message("test/topic", {"key": "value"})
        assert msg.topic == "test/topic"
        assert msg.data == {"key": "value"}
        assert msg.timestamp > 0

        # Test invalid topic
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            Message("", {"key": "value"})

        # Test invalid data
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            Message("test/topic", "invalid_data")

    def test_message_creation(self):
        """Test Message creation and validation."""
        # Valid message
        msg = Message("test/topic", {"key": "value"})
        assert msg.topic == "test/topic"
        assert msg.data == {"key": "value"}
        assert msg.qos == 0
        assert msg.key is None

        # Test invalid data type
        with pytest.raises(TypeError, match="Message data must be a dict"):
            Message("test/topic", "invalid_data")

        # Test invalid QoS
        with pytest.raises(ValueError, match="QoS must be 0 or 1"):
            Message("test/topic", {"key": "value"}, qos=2)

    @pytest.mark.asyncio
    async def test_publish_message(self, event_bus):
        """Test publishing messages to the bus."""
        # Mock the store's append method
        event_bus.store.append = AsyncMock()

        # Publish a message
        msg = Message("test/topic", {"key": "value"})
        await event_bus.publish(msg)

        # Verify the message was stored
        event_bus.store.append.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_dispatch(self, event_bus):
        """Test message dispatching to subscribers."""
        # Create mock subscribers
        subscriber1 = AsyncMock()
        subscriber2 = AsyncMock()

        # Add subscribers to the bus
        event_bus._subscribers = [subscriber1, subscriber2]

        # Publish a message
        msg = Message("test/topic", {"key": "value"})
        await event_bus._dispatch(msg)

        # Both subscribers should receive the message
        subscriber1.on_message.assert_called_once_with(msg)
        subscriber2.on_message.assert_called_once_with(msg)

    @pytest.mark.asyncio
    async def test_safe_deliver(self, event_bus):
        """Test safe message delivery with error handling."""
        # Create a subscriber that raises an exception
        error_subscriber = AsyncMock()
        error_subscriber.on_message.side_effect = Exception("Test error")

        # Create a normal subscriber
        normal_subscriber = AsyncMock()

        event_bus._subscribers = [error_subscriber, normal_subscriber]

        # Publish a message
        msg = Message("test/topic", {"key": "value"})
        await event_bus._dispatch(msg)

        # Error subscriber should have been called and failed
        error_subscriber.on_message.assert_called_once_with(msg)

        # Normal subscriber should still receive the message
        normal_subscriber.on_message.assert_called_once_with(msg)

    @pytest.mark.asyncio
    async def test_event_bus_run_stop(self, event_bus):
        """Test running and stopping the event bus."""
        # Initially not running
        assert event_bus._task is None

        # Start the bus
        await event_bus.run()

        # Should have a running task
        assert event_bus._task is not None
        assert not event_bus._task.done()

        # Stop the bus
        await event_bus.wait_until_stopped()

        # Task should be done
        assert event_bus._task.done()

    @pytest.mark.asyncio
    async def test_event_store_integration(self, event_bus, temp_dir):
        """Test integration with EventStore."""
        # Create a real event store for this test
        db_path = temp_dir / "integration_test.db"
        store = EventStore(str(db_path))
        bus = EventBus(store)

        # Publish a message
        msg = Message("integration/topic", {"test": "data"})
        await bus.publish(msg)

        # Verify the message was stored
        events = await store.query("integration/topic", limit=10)
        assert len(events) == 1
        assert events[0].topic == "integration/topic"
        assert events[0].data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, event_bus):
        """Test thread safety of concurrent operations."""
        results = []

        async def handler(msg):
            results.append(msg.topic)
            await asyncio.sleep(0.01)  # Simulate processing time

        # Subscribe multiple handlers
        await event_bus.subscribe("concurrent/topic", "module1", handler)
        await event_bus.subscribe("concurrent/topic", "module2", handler)

        # Publish multiple messages concurrently
        messages = [
            Message("concurrent/topic", {"id": i})
            for i in range(10)
        ]

        # Publish all messages concurrently
        tasks = [event_bus._route_message(msg) for msg in messages]
        await asyncio.gather(*tasks)

        # All handlers should have been called (20 total calls for 2 handlers x 10 messages)
        assert len(results) == 20
        assert results.count("concurrent/topic") == 20


class TestMessage:
    """Test Message class functionality."""

    def test_message_timestamp(self):
        """Test that messages get proper timestamps."""
        msg = Message("test/topic", {"key": "value"})

        assert isinstance(msg.timestamp, float)
        assert msg.timestamp > 0

        # Test that timestamp is reasonably current
        current_time = asyncio.get_event_loop().time()
        assert abs(msg.timestamp - current_time) < 1.0  # Within 1 second

    def test_message_equality(self):
        """Test message equality comparison."""
        msg1 = Message("test/topic", {"key": "value"})
        msg2 = Message("test/topic", {"key": "value"})
        msg3 = Message("other/topic", {"key": "value"})

        # Same topic and data should be equal (ignoring timestamp)
        assert msg1 == msg2

        # Different topic should not be equal
        assert msg1 != msg3

    def test_message_repr(self):
        """Test message string representation."""
        msg = Message("test/topic", {"key": "value"})

        repr_str = repr(msg)
        assert "test/topic" in repr_str
        assert "key" in repr_str
        assert "value" in repr_str
