"""
Replay Determinism Integration Tests

Tests that replay produces consistent results.

@ai_prompt: Run with pytest tests/integration/test_replay_determinism.py -v
@context_boundary: tests/integration/test_replay_determinism

# AI-GENERATED 2026-01-07
"""

import json
import pytest
from pathlib import Path

from aegistwin.runtime.core import AegisTwinRuntime


class TestReplayDeterminism:
    """Tests for deterministic replay."""
    
    def test_replay_matches_original(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that replay matches original run."""
        # Run original
        original_run_id = runtime.ingest(sample_data, source="test")
        
        # Replay
        replay_result = runtime.replay(original_run_id)
        
        assert replay_result["replay_results"]["deterministic"] is True
        assert replay_result["replay_results"]["events_diverged"] == 0
    
    def test_replay_counts_events(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that replay counts events correctly."""
        # Run original
        original_run_id = runtime.ingest(sample_data, source="test")
        
        # Check original trace
        trace_path = runtime._runs_dir / original_run_id / "trace.json"
        with open(trace_path) as f:
            original_trace = json.load(f)
        
        # Replay
        replay_result = runtime.replay(original_run_id)
        
        assert replay_result["replay_results"]["events_replayed"] == len(original_trace)
        assert replay_result["replay_results"]["events_matched"] == len(original_trace)
    
    def test_replay_creates_new_run(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that replay creates a new run."""
        original_run_id = runtime.ingest(sample_data, source="test")
        
        replay_result = runtime.replay(original_run_id)
        
        # Replay should have its own run ID
        assert replay_result["run_id"] != original_run_id
        
        # Replay run directory should exist
        replay_run_dir = runtime._runs_dir / replay_result["run_id"]
        assert replay_run_dir.exists()
    
    def test_replay_nonexistent_run(self, runtime: AegisTwinRuntime):
        """Test replaying a non-existent run."""
        with pytest.raises(FileNotFoundError):
            runtime.replay("nonexistent-run")
    
    def test_multiple_replays_consistent(self, runtime: AegisTwinRuntime, sample_data: dict):
        """Test that multiple replays produce consistent results."""
        original_run_id = runtime.ingest(sample_data, source="test")
        
        results = []
        for _ in range(3):
            result = runtime.replay(original_run_id)
            results.append(result["replay_results"])
        
        # All replays should match
        for result in results:
            assert result["deterministic"] is True
            assert result["events_matched"] == results[0]["events_matched"]


class TestReplayWithDifferentSizes:
    """Tests replay with varying event counts."""
    
    @pytest.mark.parametrize("record_count", [10, 100, 500])
    def test_replay_various_sizes(self, runtime: AegisTwinRuntime, record_count: int):
        """Test replay with different data sizes."""
        data = {
            "records": [{"id": i, "value": f"item-{i}"} for i in range(record_count)],
            "type": "test",
        }
        
        original_run_id = runtime.ingest(data, source="test")
        replay_result = runtime.replay(original_run_id)
        
        assert replay_result["replay_results"]["deterministic"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
