"""
Memory Footprint Benchmarks

Measures memory usage with varying numbers of events in the log.

@ai_prompt: Run with MemoryBenchmark().run() to get metrics.
@context_boundary: benchmarks/bench_memory

# AI-GENERATED 2026-01-07
"""

import gc
import sys
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Dict, List

from aegistwin.runtime.core import EventBus, AegisTwinRuntime
from aegistwin.events.schema import IngestRequested


@dataclass
class MemoryMetrics:
    """Metrics from memory benchmarks."""
    
    baseline_bytes: int = 0
    memory_with_events: Dict[int, int] = field(default_factory=dict)
    bytes_per_event: Dict[int, float] = field(default_factory=dict)
    runtime_baseline_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "baseline_bytes": self.baseline_bytes,
            "memory_with_events": self.memory_with_events,
            "bytes_per_event": self.bytes_per_event,
            "runtime_baseline_bytes": self.runtime_baseline_bytes,
        }


class MemoryBenchmark:
    """
    Benchmark suite for memory usage.
    
    Measures:
    - Baseline memory after import
    - Memory with 1K, 10K, 100K events in log
    - Bytes per event
    """
    
    EVENT_COUNTS = [1_000, 10_000, 100_000]
    
    def __init__(self):
        self.metrics = MemoryMetrics()
    
    def _create_test_event(self, index: int) -> IngestRequested:
        """Create a test event."""
        return IngestRequested(
            run_id=f"mem-{index % 1000}",
            source="memory_benchmark",
            data_type="test",
            payload={"index": index, "data": "x" * 100},
        )
    
    def benchmark_baseline_memory(self) -> int:
        """
        Measure baseline memory after importing aegistwin.
        
        Returns:
            Memory usage in bytes
        """
        gc.collect()
        tracemalloc.start()
        
        # Force fresh import measurement
        from aegistwin import AegisTwin
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return current
    
    def benchmark_runtime_baseline(self) -> int:
        """
        Measure memory after initializing runtime.
        
        Returns:
            Memory usage in bytes
        """
        gc.collect()
        tracemalloc.start()
        
        runtime = AegisTwinRuntime()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return current
    
    def benchmark_memory_with_events(self, event_count: int) -> Dict[str, Any]:
        """
        Measure memory with events in the log.
        
        Args:
            event_count: Number of events to add to the log
            
        Returns:
            Dictionary with memory metrics
        """
        gc.collect()
        tracemalloc.start()
        
        event_bus = EventBus()
        event_bus.start_recording()
        
        memory_before = tracemalloc.get_traced_memory()[0]
        
        # Create and publish events
        for i in range(event_count):
            event = self._create_test_event(i)
            event_bus.publish(event)
        
        memory_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_used = memory_after - memory_before
        bytes_per_event = memory_used / event_count if event_count > 0 else 0
        
        return {
            "event_count": event_count,
            "memory_before_bytes": memory_before,
            "memory_after_bytes": memory_after,
            "memory_used_bytes": memory_used,
            "bytes_per_event": bytes_per_event,
        }
    
    def benchmark_event_size(self) -> Dict[str, int]:
        """
        Estimate the size of a single event object.
        
        Returns:
            Dictionary with event size information
        """
        event = self._create_test_event(0)
        
        # Get object size (shallow)
        shallow_size = sys.getsizeof(event)
        
        # Estimate serialized size
        serialized = event.model_dump_json()
        serialized_size = len(serialized.encode())
        
        return {
            "shallow_size_bytes": shallow_size,
            "serialized_size_bytes": serialized_size,
        }
    
    def run(self) -> MemoryMetrics:
        """
        Run all memory benchmarks.
        
        Returns:
            MemoryMetrics with all benchmark results
        """
        print("Running Memory Benchmarks...")
        
        print("  Measuring baseline memory...")
        self.metrics.baseline_bytes = self.benchmark_baseline_memory()
        
        print("  Measuring runtime baseline...")
        self.metrics.runtime_baseline_bytes = self.benchmark_runtime_baseline()
        
        for count in self.EVENT_COUNTS:
            print(f"  Benchmarking memory with {count:,} events...")
            result = self.benchmark_memory_with_events(count)
            
            self.metrics.memory_with_events[count] = result["memory_used_bytes"]
            self.metrics.bytes_per_event[count] = result["bytes_per_event"]
        
        print("  Memory Benchmarks complete.")
        return self.metrics
    
    def get_summary(self) -> str:
        """Get a formatted summary of benchmark results."""
        lines = ["## Memory Benchmark Results\n"]
        
        lines.append("### Baseline Memory\n")
        lines.append(f"- **Import Baseline:** {self.metrics.baseline_bytes:,} bytes ({self.metrics.baseline_bytes / 1024:.1f} KB)")
        lines.append(f"- **Runtime Baseline:** {self.metrics.runtime_baseline_bytes:,} bytes ({self.metrics.runtime_baseline_bytes / 1024:.1f} KB)")
        
        lines.append("\n### Memory with Events\n")
        lines.append("| Event Count | Memory Used | Bytes/Event |")
        lines.append("|-------------|-------------|-------------|")
        
        for count in self.EVENT_COUNTS:
            memory = self.metrics.memory_with_events.get(count, 0)
            memory_kb = memory / 1024
            memory_mb = memory / (1024 * 1024)
            bytes_per = self.metrics.bytes_per_event.get(count, 0)
            
            if memory_mb >= 1:
                mem_str = f"{memory_mb:.1f} MB"
            else:
                mem_str = f"{memory_kb:.1f} KB"
            
            lines.append(f"| {count:,} | {mem_str} | {bytes_per:.0f} |")
        
        return "\n".join(lines)


if __name__ == "__main__":
    benchmark = MemoryBenchmark()
    benchmark.run()
    print(benchmark.get_summary())
