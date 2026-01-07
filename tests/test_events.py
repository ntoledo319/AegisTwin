"""
Tests for AegisTwin event schema.

@context_boundary: tests/events
"""

import pytest
from datetime import datetime

from aegistwin.events.schema import (
    BaseEvent,
    IngestRequested,
    IngestCompleted,
    DataNormalized,
    AnalysisCompleted,
    GraphUpdated,
    MemoryUpdated,
    QueryRequested,
    QueryResponded,
    AuditLogged,
    ReplayStarted,
    ReplayCompleted,
    PolicyDenied,
    EventType,
)


class TestBaseEvent:
    """Tests for BaseEvent."""
    
    def test_ingest_requested_creation(self):
        """Test IngestRequested event creation."""
        event = IngestRequested(
            source="email",
            data_type="messages",
            payload={"records": [{"id": 1}]},
        )
        
        assert event.event_type == EventType.INGEST_REQUESTED
        assert event.source == "email"
        assert event.data_type == "messages"
        assert event.event_id is not None
        assert event.run_id is not None
        assert event.timestamp is not None
    
    def test_payload_hash_deterministic(self):
        """Test that payload hash is deterministic."""
        event1 = IngestCompleted(
            run_id="test",
            source="email",
            record_count=10,
            ingest_request_id="abc",
            duration_ms=15.0,
        )
        
        event2 = IngestCompleted(
            run_id="test",
            source="email",
            record_count=10,
            ingest_request_id="abc",
            duration_ms=15.0,
        )
        
        # Same content should produce same hash
        assert event1.payload_hash == event2.payload_hash
    
    def test_payload_hash_differs_with_content(self):
        """Test that different content produces different hash."""
        event1 = IngestCompleted(
            run_id="test",
            source="email",
            record_count=10,
            ingest_request_id="abc",
            duration_ms=15.0,
        )
        
        event2 = IngestCompleted(
            run_id="test",
            source="email",
            record_count=20,  # Different count
            ingest_request_id="abc",
            duration_ms=15.0,
        )
        
        assert event1.payload_hash != event2.payload_hash
    
    def test_event_immutability(self):
        """Test that events are immutable."""
        event = IngestRequested(
            source="email",
            data_type="messages",
            payload={},
        )
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            event.source = "calendar"
    
    def test_to_trace_dict(self):
        """Test trace dictionary conversion."""
        event = IngestRequested(
            source="email",
            data_type="messages",
            payload={},
        )
        
        trace = event.to_trace_dict()
        
        assert "event_id" in trace
        assert "event_type" in trace
        assert "timestamp" in trace
        assert "run_id" in trace
        assert "payload_hash" in trace
        assert trace["event_type"] == "ingest.requested"


class TestPipelineEvents:
    """Tests for pipeline event types."""
    
    def test_data_normalized(self):
        """Test DataNormalized event."""
        event = DataNormalized(
            source="email",
            normalized_records=[{"id": 1, "text": "hello"}],
            schema_version="1.0.0",
            transformations_applied=["lowercase"],
        )
        
        assert event.event_type == EventType.DATA_NORMALIZED
        assert len(event.normalized_records) == 1
    
    def test_analysis_completed(self):
        """Test AnalysisCompleted event."""
        event = AnalysisCompleted(
            analysis_type="sentiment",
            results={"score": 0.8},
            confidence=0.9,
            entities_extracted=[{"type": "person", "name": "Alex"}],
        )
        
        assert event.event_type == EventType.ANALYSIS_COMPLETED
        assert event.confidence == 0.9
    
    def test_graph_updated(self):
        """Test GraphUpdated event."""
        event = GraphUpdated(
            nodes_added=5,
            edges_added=3,
            nodes_updated=2,
        )
        
        assert event.event_type == EventType.GRAPH_UPDATED
        assert event.nodes_added == 5
    
    def test_memory_updated(self):
        """Test MemoryUpdated event."""
        event = MemoryUpdated(
            memory_type="episodic",
            entries_added=10,
        )
        
        assert event.event_type == EventType.MEMORY_UPDATED
        assert event.memory_type == "episodic"


class TestQueryEvents:
    """Tests for query events."""
    
    def test_query_requested(self):
        """Test QueryRequested event."""
        event = QueryRequested(
            query_text="What happened?",
            query_type="search",
        )
        
        assert event.event_type == EventType.QUERY_REQUESTED
        assert event.query_text == "What happened?"
    
    def test_query_responded(self):
        """Test QueryResponded event."""
        event = QueryResponded(
            query_request_id="abc",
            response={"answer": "Something happened"},
            confidence=0.85,
            latency_ms=25.0,
        )
        
        assert event.event_type == EventType.QUERY_RESPONDED
        assert event.confidence == 0.85


class TestGovernanceEvents:
    """Tests for governance events."""
    
    def test_audit_logged(self):
        """Test AuditLogged event."""
        event = AuditLogged(
            action="export",
            actor="user_123",
            resource="data",
            outcome="denied",
            reason="Not permitted",
        )
        
        assert event.event_type == EventType.AUDIT_LOGGED
        assert event.outcome == "denied"
    
    def test_policy_denied(self):
        """Test PolicyDenied event."""
        event = PolicyDenied(
            action="execute",
            policy_id="deny-shell",
            reason="Shell access denied",
        )
        
        assert event.event_type == EventType.POLICY_DENIED
        assert event.policy_id == "deny-shell"


class TestReplayEvents:
    """Tests for replay events."""
    
    def test_replay_started(self):
        """Test ReplayStarted event."""
        event = ReplayStarted(
            original_run_id="abc123",
            replay_mode="verify",
            event_count=10,
        )
        
        assert event.event_type == EventType.REPLAY_STARTED
        assert event.original_run_id == "abc123"
    
    def test_replay_completed(self):
        """Test ReplayCompleted event."""
        event = ReplayCompleted(
            original_run_id="abc123",
            events_replayed=10,
            events_matched=10,
            events_diverged=0,
        )
        
        assert event.event_type == EventType.REPLAY_COMPLETED
        assert event.events_diverged == 0
