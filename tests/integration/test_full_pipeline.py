"""
Full Pipeline Integration Tests

Tests the complete data flow: ingest → normalize → analyze → graph → memory → query

@ai_prompt: Run with pytest tests/integration/test_full_pipeline.py -v
@context_boundary: tests/integration/test_full_pipeline

# AI-GENERATED 2026-01-07
"""

import pytest
from pathlib import Path

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.events.schema import EventType


class TestFullPipeline:
    """End-to-end pipeline tests."""
    
    def test_ingest_creates_run(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that ingestion creates a run with artifacts."""
        run_id = runtime.ingest(sample_data, source="test")
        
        assert run_id is not None
        assert len(run_id) == 8
        
        # Check run directory exists
        run_dir = runtime._runs_dir / run_id
        assert run_dir.exists()
    
    def test_ingest_records_events(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that ingestion records expected events."""
        runtime.event_bus.start_recording()
        
        run_id = runtime.ingest(sample_data, source="test")
        
        events = runtime.event_bus.get_event_log()
        event_types = [e.event_type for e in events]
        
        # Should have at least ingest requested and completed
        assert EventType.INGEST_REQUESTED in event_types
        assert EventType.INGEST_COMPLETED in event_types
    
    def test_ingest_writes_trace(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that ingestion writes a trace file."""
        run_id = runtime.ingest(sample_data, source="test")
        
        trace_path = runtime._runs_dir / run_id / "trace.json"
        assert trace_path.exists()
        
        import json
        with open(trace_path) as f:
            trace = json.load(f)
        
        assert len(trace) >= 2
        assert trace[0]["event_type"] == "ingest.requested"
    
    def test_query_after_ingest(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test querying after ingestion."""
        runtime.ingest(sample_data, source="test")
        
        response = runtime.query("What data was ingested?")
        
        assert "answer" in response
        assert "confidence" in response
        assert response["confidence"] > 0
    
    def test_multiple_ingests(self, runtime: AegisTwinRuntime):
        """Test multiple sequential ingests."""
        run_ids = []
        
        for i in range(3):
            data = {"records": [{"id": i, "value": f"batch-{i}"}]}
            run_id = runtime.ingest(data, source=f"source-{i}")
            run_ids.append(run_id)
        
        # All run IDs should be unique
        assert len(set(run_ids)) == 3
        
        # All run directories should exist
        for run_id in run_ids:
            assert (runtime._runs_dir / run_id).exists()
    
    def test_event_ordering(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that events are ordered correctly."""
        runtime.event_bus.start_recording()
        
        runtime.ingest(sample_data, source="test")
        
        events = runtime.event_bus.get_event_log()
        
        # Events should be in chronological order
        for i in range(1, len(events)):
            assert events[i].timestamp >= events[i-1].timestamp
    
    def test_run_summary(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that run summary is generated."""
        run_id = runtime.ingest(sample_data, source="test")
        
        summary_path = runtime._runs_dir / run_id / "summary.md"
        assert summary_path.exists()
        
        content = summary_path.read_text()
        assert run_id in content
        assert "Events:" in content


class TestPipelineWithLargeData:
    """Tests with larger datasets."""
    
    def test_large_ingest(self, runtime: AegisTwinRuntime, large_dataset: dict):
        """Test ingestion of large dataset."""
        run_id = runtime.ingest(large_dataset, source="bulk")
        
        assert run_id is not None
        
        # Check trace was written
        trace_path = runtime._runs_dir / run_id / "trace.json"
        assert trace_path.exists()
    
    def test_record_count_accuracy(self, runtime: AegisTwinRuntime, large_dataset: dict):
        """Test that record count is accurate."""
        runtime.event_bus.start_recording()
        
        runtime.ingest(large_dataset, source="bulk")
        
        events = runtime.event_bus.get_event_log()
        
        # Find IngestCompleted event
        completed = next(
            e for e in events 
            if e.event_type == EventType.INGEST_COMPLETED
        )
        
        assert completed.record_count == len(large_dataset["records"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
