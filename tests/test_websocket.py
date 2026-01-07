"""
Tests for WebSocket Functionality

Tests for WebSocket connection management and event broadcasting.

@ai_prompt: Run with pytest tests/test_websocket.py
@context_boundary: tests/test_websocket

# AI-GENERATED 2026-01-07
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from aegistwin.api.websocket import (
    ConnectionManager,
    event_to_json,
)
from aegistwin.events.schema import (
    IngestRequested,
    IngestCompleted,
    EventType,
)


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.accepted = False
        self.messages_sent = []
        self.closed = False
    
    async def accept(self):
        self.accepted = True
    
    async def send_text(self, message: str):
        if self.closed:
            raise Exception("WebSocket closed")
        self.messages_sent.append(message)
    
    async def send_json(self, data: dict):
        import json
        await self.send_text(json.dumps(data))
    
    async def receive_text(self):
        await asyncio.sleep(100)  # Block indefinitely
    
    def close(self):
        self.closed = True


class TestEventToJson:
    """Tests for event serialization."""
    
    def test_serialize_ingest_requested(self):
        """Test serializing IngestRequested event."""
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={"key": "value"},
        )
        
        json_str = event_to_json(event)
        
        assert "test-run" in json_str
        assert "ingest.requested" in json_str
        assert "test" in json_str
    
    def test_serialize_ingest_completed(self):
        """Test serializing IngestCompleted event."""
        event = IngestCompleted(
            run_id="test-run",
            source="test",
            record_count=5,
            ingest_request_id="req-123",
            duration_ms=100.5,
        )
        
        json_str = event_to_json(event)
        
        assert "ingest.completed" in json_str
        assert "5" in json_str or "record_count" in json_str


class TestConnectionManager:
    """Tests for ConnectionManager."""
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test accepting a connection."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        
        await manager.connect(ws)
        
        assert ws.accepted
        assert ws in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        
        await manager.connect(ws)
        await manager.disconnect(ws)
        
        assert ws not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting an event."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        await manager.connect(ws1)
        await manager.connect(ws2)
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        sent_count = await manager.broadcast(event)
        
        assert sent_count == 2
        assert len(ws1.messages_sent) == 1
        assert len(ws2.messages_sent) == 1
    
    @pytest.mark.asyncio
    async def test_event_type_filter(self):
        """Test filtering by event type."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        
        await manager.connect(ws, event_types=["ingest.completed"])
        
        # This should be filtered out
        event1 = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        # This should pass through
        event2 = IngestCompleted(
            run_id="test-run",
            source="test",
            record_count=1,
            ingest_request_id="req-1",
            duration_ms=10.0,
        )
        
        await manager.broadcast(event1)
        await manager.broadcast(event2)
        
        # Only event2 should have been sent
        assert len(ws.messages_sent) == 1
        assert "ingest.completed" in ws.messages_sent[0]
    
    @pytest.mark.asyncio
    async def test_run_filter(self):
        """Test filtering by run ID."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        
        await manager.connect(ws, run_id="run-123")
        
        event1 = IngestRequested(
            run_id="run-456",  # Different run
            source="test",
            data_type="test",
            payload={},
        )
        
        event2 = IngestRequested(
            run_id="run-123",  # Matching run
            source="test",
            data_type="test",
            payload={},
        )
        
        await manager.broadcast(event1)
        await manager.broadcast(event2)
        
        # Only event2 should have been sent
        assert len(ws.messages_sent) == 1
        assert "run-123" in ws.messages_sent[0]
    
    @pytest.mark.asyncio
    async def test_connection_info(self):
        """Test getting connection info."""
        manager = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        await manager.connect(ws1, event_types=["ingest.completed"])
        await manager.connect(ws2, run_id="run-123")
        
        info = manager.get_connection_info()
        
        assert info["total_connections"] == 2
        assert len(info["connections"]) == 2
    
    @pytest.mark.asyncio
    async def test_closed_connection_cleanup(self):
        """Test that closed connections are cleaned up."""
        manager = ConnectionManager()
        ws = MockWebSocket()
        
        await manager.connect(ws)
        ws.close()
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        # This should fail and trigger cleanup
        await manager.broadcast(event)
        
        # Connection should be removed
        assert ws not in manager.active_connections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
