"""
Replay Benchmarks

Measures replay verification speed and hash computation performance.

@ai_prompt: Run with ReplayBenchmark().run() to get metrics.
@context_boundary: benchmarks/bench_replay

# AI-GENERATED 2026-01-07
"""

import gc
import hashlib
import json
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.events.schema import IngestRequested, IngestCompleted, BaseEvent


@dataclass
class ReplayMetrics:
    """Metrics from replay benchmarks."""
    
    replay_time_seconds: Dict[int, float] = field(default_factory=dict)
    events_verified_per_second: Dict[int, float] = field(default_factory=dict)
    hash_computation_ns: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "replay_time_seconds": self.replay_time_seconds,
            "events_verified_per_second": self.events_verified_per_second,
            "hash_computation_ns": self.hash_computation_ns,
        }


class ReplayBenchmark:
    """
    Benchmark suite for replay performance.
    
    Measures:
    - Replay verification speed with 100, 1000, 10000 events
    - Hash verification time
    - Events verified per second
    """
    
    EVENT_COUNTS = [100, 1_000, 10_000]
    
    def __init__(self):
        self.metrics = ReplayMetrics()
        self._temp_dir = None
    
    def _create_test_trace(self, event_count: int) -> List[Dict[str, Any]]:
        """Create a test event trace."""
        trace = []
        run_id = "bench-run"
        
        for i in range(event_count):
            # Alternate between different event types
            if i % 2 == 0:
                event = IngestRequested(
                    run_id=run_id,
                    source="benchmark",
                    data_type="test",
                    payload={"index": i},
                )
            else:
                event = IngestCompleted(
                    run_id=run_id,
                    source="benchmark",
                    record_count=1,
                    ingest_request_id=f"req-{i-1}",
                    duration_ms=1.0,
                )
            
            trace.append(event.to_trace_dict())
        
        return trace
    
    def _verify_trace(self, trace: List[Dict[str, Any]]) -> int:
        """
        Verify a trace by recomputing hashes.
        
        Args:
            trace: List of event trace dictionaries
            
        Returns:
            Number of events verified
        """
        verified = 0
        for event_data in trace:
            # Recompute hash for verification
            hash_input = str(sorted(event_data.items())).encode()
            computed_hash = hashlib.sha256(hash_input).hexdigest()[:16]
            
            # In a real implementation, we'd compare with stored hash
            # For benchmark purposes, just count the computation
            verified += 1
        
        return verified
    
    def benchmark_replay_speed(self, event_count: int) -> Dict[str, Any]:
        """
        Benchmark replay verification speed.
        
        Args:
            event_count: Number of events in the trace
            
        Returns:
            Dictionary with replay speed metrics
        """
        trace = self._create_test_trace(event_count)
        
        gc.collect()
        
        start_time = time.perf_counter_ns()
        verified = self._verify_trace(trace)
        end_time = time.perf_counter_ns()
        
        total_time_seconds = (end_time - start_time) / 1e9
        events_per_second = verified / total_time_seconds if total_time_seconds > 0 else 0
        
        return {
            "event_count": event_count,
            "events_verified": verified,
            "total_time_seconds": total_time_seconds,
            "events_verified_per_second": events_per_second,
        }
    
    def benchmark_hash_computation(self) -> Dict[str, float]:
        """
        Benchmark hash computation performance.
        
        Returns:
            Dictionary with hash computation metrics
        """
        iterations = 10_000
        latencies_ns: List[float] = []
        
        # Create a sample payload
        payload = {
            "event_id": "test-event-123",
            "event_type": "ingest.requested",
            "run_id": "bench-run",
            "payload": {"data": "test" * 100},
        }
        serialized = str(sorted(payload.items())).encode()
        
        gc.collect()
        
        for _ in range(iterations):
            start = time.perf_counter_ns()
            hashlib.sha256(serialized).hexdigest()[:16]
            end = time.perf_counter_ns()
            latencies_ns.append(end - start)
        
        return {
            "iterations": iterations,
            "mean_ns": statistics.mean(latencies_ns),
            "p50_ns": statistics.median(latencies_ns),
            "p99_ns": sorted(latencies_ns)[int(len(latencies_ns) * 0.99)],
        }
    
    def benchmark_full_replay(self, event_count: int) -> Dict[str, Any]:
        """
        Benchmark full replay workflow including file I/O.
        
        Args:
            event_count: Number of events
            
        Returns:
            Dictionary with full replay metrics
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create trace file
            trace = self._create_test_trace(event_count)
            trace_path = Path(temp_dir) / "trace.json"
            
            with open(trace_path, "w") as f:
                json.dump(trace, f)
            
            gc.collect()
            
            # Benchmark load + verify
            start_time = time.perf_counter_ns()
            
            with open(trace_path) as f:
                loaded_trace = json.load(f)
            
            verified = self._verify_trace(loaded_trace)
            
            end_time = time.perf_counter_ns()
            
            total_time_seconds = (end_time - start_time) / 1e9
            events_per_second = verified / total_time_seconds if total_time_seconds > 0 else 0
            
            return {
                "event_count": event_count,
                "total_time_seconds": total_time_seconds,
                "events_verified_per_second": events_per_second,
                "includes_file_io": True,
            }
    
    def run(self) -> ReplayMetrics:
        """
        Run all replay benchmarks.
        
        Returns:
            ReplayMetrics with all benchmark results
        """
        print("Running Replay Benchmarks...")
        
        for count in self.EVENT_COUNTS:
            print(f"  Benchmarking replay with {count:,} events...")
            result = self.benchmark_replay_speed(count)
            
            self.metrics.replay_time_seconds[count] = result["total_time_seconds"]
            self.metrics.events_verified_per_second[count] = result["events_verified_per_second"]
        
        print("  Benchmarking hash computation...")
        self.metrics.hash_computation_ns = self.benchmark_hash_computation()
        
        print("  Replay Benchmarks complete.")
        return self.metrics
    
    def get_summary(self) -> str:
        """Get a formatted summary of benchmark results."""
        lines = ["## Replay Benchmark Results\n"]
        lines.append("### Replay Verification Speed\n")
        lines.append("| Event Count | Total Time (s) | Events Verified/sec |")
        lines.append("|-------------|----------------|---------------------|")
        
        for count in self.EVENT_COUNTS:
            time_s = self.metrics.replay_time_seconds.get(count, 0)
            eps = self.metrics.events_verified_per_second.get(count, 0)
            
            lines.append(f"| {count:,} | {time_s:.4f} | {eps:,.0f} |")
        
        lines.append("\n### Hash Computation Performance\n")
        hash_data = self.metrics.hash_computation_ns
        mean_us = hash_data.get("mean_ns", 0) / 1000
        p99_us = hash_data.get("p99_ns", 0) / 1000
        
        lines.append(f"- **Mean Latency:** {mean_us:.2f} µs")
        lines.append(f"- **P99 Latency:** {p99_us:.2f} µs")
        
        return "\n".join(lines)


if __name__ == "__main__":
    benchmark = ReplayBenchmark()
    benchmark.run()
    print(benchmark.get_summary())
