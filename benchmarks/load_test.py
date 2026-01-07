"""
Load Testing for AegisTwin

Tests system performance under concurrent load.

@ai_prompt: Run with `python benchmarks/load_test.py`
@context_boundary: benchmarks/load_test

# AI-GENERATED 2026-01-07
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median, stdev

from aegistwin.runtime.async_core import AsyncAegisTwinRuntime


async def benchmark_ingest(runtime: AsyncAegisTwinRuntime, id: int):
    """Benchmark single ingest operation."""
    data = {
        "records": [
            {"id": f"record_{id}_{i}", "content": f"Test content {i}"}
            for i in range(10)
        ]
    }
    
    start = time.perf_counter()
    await runtime.ingest(data, source=f"load_test_{id}")
    duration = time.perf_counter() - start
    
    return duration * 1000  # Convert to ms


async def benchmark_query(runtime: AsyncAegisTwinRuntime, id: int):
    """Benchmark single query operation."""
    start = time.perf_counter()
    await runtime.query(f"Test query {id}")
    duration = time.perf_counter() - start
    
    return duration * 1000  # Convert to ms


async def run_concurrent_load(operation: str, concurrency: int, iterations: int):
    """Run concurrent operations and measure performance."""
    runtime = AsyncAegisTwinRuntime()
    await runtime.start()
    
    print(f"\n{'='*70}")
    print(f"🔥 Load Test: {operation.upper()}")
    print(f"{'='*70}")
    print(f"Concurrency: {concurrency}")
    print(f"Iterations per worker: {iterations}")
    print(f"Total operations: {concurrency * iterations}")
    print()
    
    latencies = []
    start_time = time.perf_counter()
    
    # Run concurrent operations
    for batch in range(iterations):
        tasks = []
        for i in range(concurrency):
            if operation == "ingest":
                task = benchmark_ingest(runtime, batch * concurrency + i)
            else:  # query
                task = benchmark_query(runtime, batch * concurrency + i)
            tasks.append(task)
        
        batch_latencies = await asyncio.gather(*tasks)
        latencies.extend(batch_latencies)
    
    total_time = time.perf_counter() - start_time
    
    await runtime.stop()
    
    # Calculate statistics
    total_ops = concurrency * iterations
    throughput = total_ops / total_time
    
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    
    print(f"✅ Test Complete!")
    print(f"\n📊 RESULTS:")
    print(f"{'─'*70}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Total Operations: {total_ops}")
    print(f"Throughput: {throughput:.1f} ops/sec")
    print()
    print(f"Latency Statistics (ms):")
    print(f"  Mean: {mean(latencies):.2f}")
    print(f"  Median (P50): {p50:.2f}")
    print(f"  P95: {p95:.2f}")
    print(f"  P99: {p99:.2f}")
    print(f"  Min: {min(latencies):.2f}")
    print(f"  Max: {max(latencies):.2f}")
    if len(latencies) > 1:
        print(f"  StdDev: {stdev(latencies):.2f}")
    print(f"{'─'*70}")
    
    return {
        "operation": operation,
        "total_time": total_time,
        "total_ops": total_ops,
        "throughput": throughput,
        "latency_mean": mean(latencies),
        "latency_p50": p50,
        "latency_p95": p95,
        "latency_p99": p99,
        "latency_min": min(latencies),
        "latency_max": max(latencies),
    }


async def run_all_benchmarks():
    """Run comprehensive load tests."""
    print("=" * 70)
    print("🚀 AegisTwin Load Testing Suite")
    print("=" * 70)
    
    results = []
    
    # Test 1: Moderate concurrent ingestion
    result = await run_concurrent_load("ingest", concurrency=10, iterations=10)
    results.append(result)
    
    # Test 2: High concurrent queries
    result = await run_concurrent_load("query", concurrency=50, iterations=20)
    results.append(result)
    
    # Test 3: Sustained load
    result = await run_concurrent_load("ingest", concurrency=20, iterations=50)
    results.append(result)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 LOAD TEST SUMMARY")
    print("=" * 70)
    print()
    print("| Operation | Throughput | P50 Latency | P99 Latency |")
    print("|-----------|------------|-------------|-------------|")
    for r in results:
        print(f"| {r['operation']:9} | {r['throughput']:8.1f}/s | {r['latency_p50']:9.2f}ms | {r['latency_p99']:9.2f}ms |")
    print()
    
    print("✅ System Performance Assessment:")
    avg_throughput = mean([r['throughput'] for r in results])
    avg_p99 = mean([r['latency_p99'] for r in results])
    
    if avg_throughput > 100 and avg_p99 < 100:
        print("   🟢 EXCELLENT - Production ready for high load")
    elif avg_throughput > 50 and avg_p99 < 200:
        print("   🟡 GOOD - Suitable for moderate production load")
    else:
        print("   🟠 ACCEPTABLE - Suitable for low to moderate load")
    
    print()
    print(f"   Average Throughput: {avg_throughput:.1f} ops/sec")
    print(f"   Average P99 Latency: {avg_p99:.2f}ms")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
