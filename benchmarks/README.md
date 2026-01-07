# AegisTwin Benchmarks

Performance benchmarking suite for measuring throughput, latency, and memory usage.

## Quick Start

```bash
# Run all benchmarks
python -m benchmarks.run_benchmarks

# Run with custom output directory
python -m benchmarks.run_benchmarks --output-dir ./my_results

# Quiet mode (no console output)
python -m benchmarks.run_benchmarks --quiet
```

## Benchmark Suites

### Event Bus Benchmarks (`bench_event_bus.py`)

Measures EventBus performance:
- **Events per second** — Throughput with 1K, 10K, 100K events
- **Memory delta** — Memory used during publishing
- **Latency** — Per-event latency (mean, p50, p95, p99)

### Policy Engine Benchmarks (`bench_policy.py`)

Measures PolicyEngine performance:
- **Check latency** — With 0, 10, 100, 1000 policies loaded
- **Checks per second** — Throughput at different policy counts
- **Wildcard vs Exact** — Pattern matching performance comparison

### Replay Benchmarks (`bench_replay.py`)

Measures replay verification performance:
- **Verification speed** — Events verified per second
- **Hash computation** — SHA256 hash computation latency
- **Full replay** — Including file I/O overhead

### Memory Benchmarks (`bench_memory.py`)

Measures memory footprint:
- **Baseline memory** — After importing aegistwin
- **Runtime baseline** — After initializing runtime
- **Events in log** — Memory with 1K, 10K, 100K events
- **Bytes per event** — Average memory per event

## Output

After running benchmarks, results are saved to:

- `benchmarks/results/latest.json` — Machine-readable JSON
- `benchmarks/results/RESULTS.md` — Human-readable Markdown

### Sample Output

```json
{
  "system_info": {
    "python_version": "3.11.0",
    "os": "Darwin",
    "cpu_count": 8
  },
  "benchmarks": {
    "event_bus": {
      "events_per_second": {
        "1000": 150000,
        "10000": 145000,
        "100000": 140000
      }
    }
  }
}
```

## Interpreting Results

### Event Bus

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Events/sec | > 100K | 50K-100K | < 50K |
| Mean Latency | < 10µs | 10-50µs | > 50µs |
| P99 Latency | < 100µs | 100-500µs | > 500µs |

### Policy Engine

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Checks/sec | > 500K | 100K-500K | < 100K |
| Latency (100 policies) | < 5µs | 5-20µs | > 20µs |

### Memory

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Bytes/Event | < 500 | 500-1000 | > 1000 |
| 100K Events | < 50MB | 50-100MB | > 100MB |

## Running Individual Benchmarks

```python
from benchmarks.bench_event_bus import EventBusBenchmark

bench = EventBusBenchmark()
metrics = bench.run()
print(bench.get_summary())
```

## Adding Custom Benchmarks

1. Create a new file `bench_*.py` in the benchmarks directory
2. Create a benchmark class with a `run()` method
3. Add to `run_benchmarks.py` to include in the full suite

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class MyMetrics:
    custom_value: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {"custom_value": self.custom_value}

class MyBenchmark:
    def __init__(self):
        self.metrics = MyMetrics()
    
    def run(self) -> MyMetrics:
        # Your benchmark logic
        self.metrics.custom_value = 42.0
        return self.metrics
```

## CI Integration

Add to your CI pipeline:

```yaml
- name: Run Benchmarks
  run: python -m benchmarks.run_benchmarks --quiet

- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-results
    path: benchmarks/results/
```

---

*Last updated: 2026-01-07*
