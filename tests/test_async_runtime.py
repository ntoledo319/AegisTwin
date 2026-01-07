"""
Tests for Async Runtime

Tests for AsyncAegisTwinRuntime and AsyncEventBus functionality.

@ai_prompt: Run with pytest tests/test_async_runtime.py
@context_boundary: tests/test_async_runtime

# AI-GENERATED 2026-01-07
"""

import asyncio
import pytest
from aegistwin.runtime.async_core import (
    AsyncAegisTwinRuntime,
    AsyncEventBus,
    run_concurrent_queries,
)
from aegistwin.events.schema import EventType, IngestRequested


class TestAsyncEventBus:
    """Tests for AsyncEventBus."""
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self):
        """Test async publish and subscribe."""
        bus = AsyncEventBus()
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        await bus.subscribe(EventType.INGEST_REQUESTED, handler)
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={"test": True},
        )
        
        await bus.publish(event)
        
        assert len(received_events) == 1
        assert received_events[0].event_id == event.event_id
    
    @pytest.mark.asyncio
    async def test_listener(self):
        """Test event listener for all events."""
        bus = AsyncEventBus()
        all_events = []
        
        async def listener(event):
            all_events.append(event)
        
        bus.add_listener(listener)
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        await bus.publish(event)
        
        assert len(all_events) == 1
        
        bus.remove_listener(listener)
        await bus.publish(event)
        
        # Should still be 1 since listener was removed
        assert len(all_events) == 1
    
    @pytest.mark.asyncio
    async def test_recording(self):
        """Test event recording."""
        bus = AsyncEventBus()
        
        bus.start_recording()
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        await bus.publish(event)
        await bus.publish(event)
        
        events = bus.stop_recording()
        
        assert len(events) == 2
    
    @pytest.mark.asyncio
    async def test_background_dispatch(self):
        """Test background dispatch loop."""
        bus = AsyncEventBus()
        received = []
        
        async def handler(event):
            received.append(event)
        
        await bus.subscribe(EventType.INGEST_REQUESTED, handler)
        await bus.start()
        
        event = IngestRequested(
            run_id="test-run",
            source="test",
            data_type="test",
            payload={},
        )
        
        await bus.publish(event)
        await asyncio.sleep(0.1)  # Allow dispatch
        
        await bus.stop()
        
        assert len(received) == 1


class TestAsyncAegisTwinRuntime:
    """Tests for AsyncAegisTwinRuntime."""
    
    @pytest.mark.asyncio
    async def test_ingest(self):
        """Test async ingestion."""
        runtime = AsyncAegisTwinRuntime()
        
        run_id = await runtime.ingest(
            data={"records": [{"id": 1}]},
            source="test"
        )
        
        assert run_id is not None
        assert len(run_id) == 8
    
    @pytest.mark.asyncio
    async def test_query(self):
        """Test async query."""
        runtime = AsyncAegisTwinRuntime()
        
        result = await runtime.query("test query")
        
        assert "answer" in result
        assert "confidence" in result
        assert result["confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_policy_check(self):
        """Test async policy check."""
        runtime = AsyncAegisTwinRuntime()
        
        # Default policy allows ingest
        allowed = await runtime.check_policy("ingest", "test")
        assert allowed is True
        
        # System modules are denied
        allowed = await runtime.check_policy("execute", "system.shell")
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test running queries concurrently."""
        runtime = AsyncAegisTwinRuntime()
        
        queries = ["query1", "query2", "query3"]
        results = await run_concurrent_queries(runtime, queries)
        
        assert len(results) == 3
        for result in results:
            assert "answer" in result
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test runtime start and stop."""
        runtime = AsyncAegisTwinRuntime()
        
        await runtime.start()
        assert runtime._started is True
        
        await runtime.stop()
        assert runtime._started is False
    
    @pytest.mark.asyncio
    async def test_run_lifecycle(self):
        """Test run start and end."""
        runtime = AsyncAegisTwinRuntime()
        
        run_id = await runtime.start_run()
        assert run_id is not None
        assert runtime.run_id == run_id
        
        summary = await runtime.end_run()
        assert summary["run_id"] == run_id
        assert runtime.run_id is None


class TestCancellation:
    """Tests for cancellation handling."""
    
    @pytest.mark.asyncio
    async def test_bus_cancellation(self):
        """Test that event bus handles cancellation gracefully."""
        bus = AsyncEventBus()
        await bus.start()
        
        # Stop should handle cancellation
        await bus.stop()
        
        assert bus._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
