"""
AegisTwin Benchmark Runner

Main entry point for running all benchmarks and generating reports.

Usage:
    python -m benchmarks.run_benchmarks

@ai_prompt: Run this module to generate benchmarks/results/latest.json and RESULTS.md
@context_boundary: benchmarks/run_benchmarks

# AI-GENERATED 2026-01-07
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.bench_event_bus import EventBusBenchmark
from benchmarks.bench_policy import PolicyBenchmark
from benchmarks.bench_replay import ReplayBenchmark
from benchmarks.bench_memory import MemoryBenchmark


def get_system_info() -> Dict[str, Any]:
    """
    Collect system information for benchmark context.
    
    Returns:
        Dictionary with system details
    """
    import aegistwin
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": os.cpu_count(),
        "aegistwin_version": aegistwin.__version__,
    }


def run_all_benchmarks(verbose: bool = True) -> Dict[str, Any]:
    """
    Run all benchmark suites.
    
    Args:
        verbose: Whether to print progress
        
    Returns:
        Dictionary with all benchmark results
    """
    if verbose:
        print("=" * 60)
        print("AegisTwin Performance Benchmarks")
        print("=" * 60)
        print()
    
    results = {
        "system_info": get_system_info(),
        "benchmarks": {},
    }
    
    # Event Bus Benchmarks
    if verbose:
        print("[1/4] Event Bus Benchmarks")
    event_bus_bench = EventBusBenchmark()
    event_bus_bench.run()
    results["benchmarks"]["event_bus"] = event_bus_bench.metrics.to_dict()
    
    # Policy Benchmarks
    if verbose:
        print("\n[2/4] Policy Engine Benchmarks")
    policy_bench = PolicyBenchmark()
    policy_bench.run()
    results["benchmarks"]["policy"] = policy_bench.metrics.to_dict()
    
    # Replay Benchmarks
    if verbose:
        print("\n[3/4] Replay Benchmarks")
    replay_bench = ReplayBenchmark()
    replay_bench.run()
    results["benchmarks"]["replay"] = replay_bench.metrics.to_dict()
    
    # Memory Benchmarks
    if verbose:
        print("\n[4/4] Memory Benchmarks")
    memory_bench = MemoryBenchmark()
    memory_bench.run()
    results["benchmarks"]["memory"] = memory_bench.metrics.to_dict()
    
    if verbose:
        print("\n" + "=" * 60)
        print("All benchmarks complete!")
        print("=" * 60)
    
    return results


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """
    Generate a Markdown report from benchmark results.
    
    Args:
        results: Benchmark results dictionary
        
    Returns:
        Markdown formatted report
    """
    lines = ["# AegisTwin Benchmark Results\n"]
    
    # System Info
    sys_info = results["system_info"]
    lines.append("## System Information\n")
    lines.append(f"- **Date:** {sys_info['timestamp']}")
    lines.append(f"- **Python:** {sys_info['python_version']} ({sys_info['python_implementation']})")
    lines.append(f"- **OS:** {sys_info['os']} {sys_info['os_release']}")
    lines.append(f"- **CPU:** {sys_info['processor']} ({sys_info['cpu_count']} cores)")
    lines.append(f"- **AegisTwin:** v{sys_info['aegistwin_version']}")
    lines.append("")
    
    # Event Bus Results
    lines.append("## Event Bus Performance\n")
    eb_data = results["benchmarks"]["event_bus"]
    lines.append("| Event Count | Events/sec | Memory Delta | Mean Latency (µs) | P99 Latency (µs) |")
    lines.append("|-------------|------------|--------------|-------------------|------------------|")
    
    for count_str, eps in eb_data["events_per_second"].items():
        count = int(count_str)
        mem = eb_data["memory_delta_bytes"].get(count_str, 0)
        latency = eb_data["latency_ns"].get(count_str, {})
        mean_us = latency.get("mean", 0) / 1000
        p99_us = latency.get("p99", 0) / 1000
        
        lines.append(f"| {count:,} | {eps:,.0f} | {mem:,} bytes | {mean_us:.2f} | {p99_us:.2f} |")
    
    lines.append("")
    
    # Policy Results
    lines.append("## Policy Engine Performance\n")
    pol_data = results["benchmarks"]["policy"]
    lines.append("### Check Latency by Policy Count\n")
    lines.append("| Policy Count | Checks/sec | Mean Latency (µs) | P99 Latency (µs) |")
    lines.append("|--------------|------------|-------------------|------------------|")
    
    for count_str, cps in pol_data["checks_per_second"].items():
        count = int(count_str)
        latency = pol_data["check_latency_ns"].get(count_str, {})
        mean_us = latency.get("mean", 0) / 1000
        p99_us = latency.get("p99", 0) / 1000
        
        lines.append(f"| {count} | {cps:,.0f} | {mean_us:.2f} | {p99_us:.2f} |")
    
    lines.append("\n### Wildcard vs Exact Match\n")
    lines.append("| Match Type | Mean Latency (µs) | P99 Latency (µs) |")
    lines.append("|------------|-------------------|------------------|")
    
    for match_type in ["exact", "wildcard"]:
        data = pol_data["wildcard_vs_exact"].get(match_type, {})
        mean_us = data.get("mean_ns", 0) / 1000
        p99_us = data.get("p99_ns", 0) / 1000
        lines.append(f"| {match_type} | {mean_us:.2f} | {p99_us:.2f} |")
    
    lines.append("")
    
    # Replay Results
    lines.append("## Replay Performance\n")
    rp_data = results["benchmarks"]["replay"]
    lines.append("| Event Count | Total Time (s) | Events Verified/sec |")
    lines.append("|-------------|----------------|---------------------|")
    
    for count_str, time_s in rp_data["replay_time_seconds"].items():
        count = int(count_str)
        eps = rp_data["events_verified_per_second"].get(count_str, 0)
        
        lines.append(f"| {count:,} | {time_s:.4f} | {eps:,.0f} |")
    
    hash_data = rp_data["hash_computation_ns"]
    mean_us = hash_data.get("mean_ns", 0) / 1000
    p99_us = hash_data.get("p99_ns", 0) / 1000
    lines.append(f"\n**Hash Computation:** Mean {mean_us:.2f} µs, P99 {p99_us:.2f} µs")
    lines.append("")
    
    # Memory Results
    lines.append("## Memory Usage\n")
    mem_data = results["benchmarks"]["memory"]
    
    baseline = mem_data["baseline_bytes"]
    runtime_baseline = mem_data["runtime_baseline_bytes"]
    lines.append(f"- **Import Baseline:** {baseline:,} bytes ({baseline / 1024:.1f} KB)")
    lines.append(f"- **Runtime Baseline:** {runtime_baseline:,} bytes ({runtime_baseline / 1024:.1f} KB)")
    lines.append("")
    
    lines.append("| Event Count | Memory Used | Bytes/Event |")
    lines.append("|-------------|-------------|-------------|")
    
    for count_str, memory in mem_data["memory_with_events"].items():
        count = int(count_str)
        memory_kb = memory / 1024
        memory_mb = memory / (1024 * 1024)
        bytes_per = mem_data["bytes_per_event"].get(count_str, 0)
        
        if memory_mb >= 1:
            mem_str = f"{memory_mb:.1f} MB"
        else:
            mem_str = f"{memory_kb:.1f} KB"
        
        lines.append(f"| {count:,} | {mem_str} | {bytes_per:.0f} |")
    
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated: {sys_info['timestamp']}*")
    
    return "\n".join(lines)


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run AegisTwin performance benchmarks"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmarks/results",
        help="Directory for output files (default: benchmarks/results)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only generate JSON output, skip Markdown",
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run benchmarks
    results = run_all_benchmarks(verbose=not args.quiet)
    
    # Save JSON results
    json_path = output_dir / "latest.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    if not args.quiet:
        print(f"\nJSON results saved to: {json_path}")
    
    # Generate and save Markdown report
    if not args.json_only:
        markdown = generate_markdown_report(results)
        md_path = output_dir / "RESULTS.md"
        with open(md_path, "w") as f:
            f.write(markdown)
        
        if not args.quiet:
            print(f"Markdown report saved to: {md_path}")
            print()
            print(markdown)


if __name__ == "__main__":
    main()
