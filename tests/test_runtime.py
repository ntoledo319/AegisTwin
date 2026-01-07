"""
Tests for AegisTwin runtime.

@context_boundary: tests/runtime
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from aegistwin.runtime.core import AegisTwinRuntime, EventBus
from aegistwin.events.schema import IngestRequested, EventType


class TestEventBus:
    """Tests for EventBus class."""
    
    def test_subscribe_and_publish(self):
        """Test event subscription and publishing."""
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.INGEST_REQUESTED, handler)
        
        event = IngestRequested(
            source="test",
            data_type="test",
            payload={},
        )
        bus.publish(event)
        
        assert len(received) == 1
        assert received[0] == event
    
    def test_recording(self):
        """Test event recording."""
        bus = EventBus()
        
        bus.start_recording()
        
        event = IngestRequested(
            source="test",
            data_type="test",
            payload={},
        )
        bus.publish(event)
        
        log = bus.stop_recording()
        
        assert len(log) == 1
        assert log[0] == event
    
    def test_get_event_log(self):
        """Test getting event log during recording."""
        bus = EventBus()
        
        bus.start_recording()
        
        event = IngestRequested(
            source="test",
            data_type="test",
            payload={},
        )
        bus.publish(event)
        
        log = bus.get_event_log()
        
        assert len(log) == 1


class TestAegisTwinRuntime:
    """Tests for AegisTwinRuntime class."""
    
    @pytest.fixture
    def runtime(self):
        """Create a runtime with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = AegisTwinRuntime()
            runtime._runs_dir = Path(tmpdir)
            yield runtime
    
    def test_start_and_end_run(self, runtime):
        """Test starting and ending a run."""
        run_id = runtime.start_run()
        
        assert run_id is not None
        assert runtime.run_id == run_id
        
        summary = runtime.end_run()
        
        assert summary["run_id"] == run_id
        assert runtime.run_id is None
    
    def test_run_creates_artifacts(self, runtime):
        """Test that runs create artifact files."""
        run_id = runtime.start_run()
        
        # Publish an event
        event = IngestRequested(
            run_id=run_id,
            source="test",
            data_type="test",
            payload={},
        )
        runtime.event_bus.publish(event)
        
        summary = runtime.end_run()
        
        # Check trace file exists
        trace_path = runtime._runs_dir / run_id / "trace.json"
        assert trace_path.exists()
        
        with open(trace_path) as f:
            trace = json.load(f)
        assert len(trace) >= 1
    
    def test_check_policy_allowed(self, runtime):
        """Test policy check for allowed action."""
        runtime.start_run()
        
        allowed = runtime.check_policy("ingest", "email")
        
        assert allowed
        
        runtime.end_run()
    
    def test_check_policy_denied(self, runtime):
        """Test policy check for denied action."""
        runtime.start_run()
        
        allowed = runtime.check_policy("execute", "system.shell")
        
        assert not allowed
        
        runtime.end_run()
    
    def test_ingest(self, runtime):
        """Test data ingestion."""
        data = {"records": [{"id": 1}]}
        
        run_id = runtime.ingest(data, source="test")
        
        assert run_id is not None
    
    def test_ingest_denied_source(self, runtime):
        """Test ingestion from denied source."""
        # Add a deny policy for test source
        from aegistwin.governance.policy import Policy, PolicyEffect
        
        runtime.policy_engine.add_policy(Policy(
            id="deny-test-source",
            action="ingest",
            resource="forbidden_source",
            effect=PolicyEffect.DENY,
            priority=1000,
        ))
        
        with pytest.raises(PermissionError):
            runtime.ingest({}, source="forbidden_source")
    
    def test_query(self, runtime):
        """Test query execution."""
        result = runtime.query("What happened?")
        
        assert "answer" in result
        assert "confidence" in result
    
    def test_replay(self, runtime):
        """Test replay functionality."""
        # First, create a run to replay
        run_id = runtime.start_run()
        
        event = IngestRequested(
            run_id=run_id,
            source="test",
            data_type="test",
            payload={},
        )
        runtime.event_bus.publish(event)
        
        runtime.end_run()
        
        # Now replay it
        result = runtime.replay(run_id)
        
        assert "replay_results" in result
        assert result["replay_results"]["original_run_id"] == run_id
        assert result["replay_results"]["events_replayed"] >= 1
    
    def test_replay_nonexistent_run(self, runtime):
        """Test replay of non-existent run."""
        with pytest.raises(FileNotFoundError):
            runtime.replay("nonexistent_run_id")
