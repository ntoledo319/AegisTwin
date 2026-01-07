"""
Event Bus Benchmarks

Measures event throughput, latency, and memory usage during event publishing.

@ai_prompt: Run with EventBusBenchmark().run() to get metrics.
@context_boundary: benchmarks/bench_event_bus

# AI-GENERATED 2026-01-07
"""

import gc
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Dict, List

from aegistwin.runtime.core import EventBus
from aegistwin.events.schema import IngestRequested, EventType


@dataclass
class EventBusMetrics:
    """Metrics from event bus benchmarks."""
    
    events_per_second: Dict[int, float] = field(default_factory=dict)
    memory_delta_bytes: Dict[int, int] = field(default_factory=dict)
    latency_ns: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "events_per_second": self.events_per_second,
            "memory_delta_bytes": self.memory_delta_bytes,
            "latency_ns": self.latency_ns,
        }


class EventBusBenchmark:
    """
    Benchmark suite for EventBus performance.
    
    Measures:
    - Events per second (1K, 10K, 100K events)
    - Memory delta during publishing
    - Latency per event (mean, p50, p95, p99)
    """
    
    EVENT_COUNTS = [1_000, 10_000, 100_000]
    
    def __init__(self):
        self.metrics = EventBusMetrics()
    
    def _create_test_event(self, index: int) -> IngestRequested:
        """Create a test event for benchmarking."""
        return IngestRequested(
            run_id=f"bench-{index % 1000}",
            source="benchmark",
            data_type="test",
            payload={"index": index, "data": "benchmark_payload"},
        )
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from a sorted list."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)
    
    def benchmark_throughput(self, event_count: int) -> Dict[str, Any]:
        """
        Benchmark event throughput for a given count.
        
        Args:
            event_count: Number of events to publish
            
        Returns:
            Dictionary with throughput and latency metrics
        """
        event_bus = EventBus()
        latencies_ns: List[float] = []
        
        # Force garbage collection before measurement
        gc.collect()
        
        # Start memory tracking
        tracemalloc.start()
        memory_before = tracemalloc.get_traced_memory()[0]
        
        # Pre-create events to avoid creation overhead in timing
        events = [self._create_test_event(i) for i in range(event_count)]
        
        # Measure publishing
        start_time = time.perf_counter_ns()
        
        for event in events:
            event_start = time.perf_counter_ns()
            event_bus.publish(event)
            event_end = time.perf_counter_ns()
            latencies_ns.append(event_end - event_start)
        
        end_time = time.perf_counter_ns()
        
        # Get memory after
        memory_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        # Calculate metrics
        total_time_seconds = (end_time - start_time) / 1e9
        events_per_second = event_count / total_time_seconds if total_time_seconds > 0 else 0
        memory_delta = memory_after - memory_before
        
        # Latency statistics
        mean_latency = statistics.mean(latencies_ns) if latencies_ns else 0
        p50_latency = self._calculate_percentile(latencies_ns, 50)
        p95_latency = self._calculate_percentile(latencies_ns, 95)
        p99_latency = self._calculate_percentile(latencies_ns, 99)
        
        return {
            "event_count": event_count,
            "total_time_seconds": total_time_seconds,
            "events_per_second": events_per_second,
            "memory_delta_bytes": memory_delta,
            "latency_ns": {
                "mean": mean_latency,
                "p50": p50_latency,
                "p95": p95_latency,
                "p99": p99_latency,
            },
        }
    
    def benchmark_with_subscribers(self, event_count: int, subscriber_count: int) -> Dict[str, Any]:
        """
        Benchmark throughput with multiple subscribers.
        
        Args:
            event_count: Number of events to publish
            subscriber_count: Number of subscribers to register
            
        Returns:
            Dictionary with throughput metrics
        """
        event_bus = EventBus()
        handler_calls = [0]
        
        def handler(event):
            handler_calls[0] += 1
        
        # Register subscribers
        for _ in range(subscriber_count):
            event_bus.subscribe(EventType.INGEST_REQUESTED, handler)
        
        gc.collect()
        
        events = [self._create_test_event(i) for i in range(event_count)]
        
        start_time = time.perf_counter_ns()
        for event in events:
            event_bus.publish(event)
        end_time = time.perf_counter_ns()
        
        total_time_seconds = (end_time - start_time) / 1e9
        events_per_second = event_count / total_time_seconds if total_time_seconds > 0 else 0
        
        return {
            "event_count": event_count,
            "subscriber_count": subscriber_count,
            "handler_calls": handler_calls[0],
            "total_time_seconds": total_time_seconds,
            "events_per_second": events_per_second,
        }
    
    def run(self) -> EventBusMetrics:
        """
        Run all event bus benchmarks.
        
        Returns:
            EventBusMetrics with all benchmark results
        """
        print("Running Event Bus Benchmarks...")
        
        for count in self.EVENT_COUNTS:
            print(f"  Benchmarking {count:,} events...")
            result = self.benchmark_throughput(count)
            
            self.metrics.events_per_second[count] = result["events_per_second"]
            self.metrics.memory_delta_bytes[count] = result["memory_delta_bytes"]
            self.metrics.latency_ns[count] = result["latency_ns"]
        
        print("  Event Bus Benchmarks complete.")
        return self.metrics
    
    def get_summary(self) -> str:
        """Get a formatted summary of benchmark results."""
        lines = ["## Event Bus Benchmark Results\n"]
        lines.append("| Event Count | Events/sec | Memory Delta | Mean Latency (µs) | P99 Latency (µs) |")
        lines.append("|-------------|------------|--------------|-------------------|------------------|")
        
        for count in self.EVENT_COUNTS:
            eps = self.metrics.events_per_second.get(count, 0)
            mem = self.metrics.memory_delta_bytes.get(count, 0)
            latency = self.metrics.latency_ns.get(count, {})
            mean_us = latency.get("mean", 0) / 1000
            p99_us = latency.get("p99", 0) / 1000
            
            lines.append(
                f"| {count:,} | {eps:,.0f} | {mem:,} bytes | {mean_us:.2f} | {p99_us:.2f} |"
            )
        
        return "\n".join(lines)


if __name__ == "__main__":
    benchmark = EventBusBenchmark()
    benchmark.run()
    print(benchmark.get_summary())
