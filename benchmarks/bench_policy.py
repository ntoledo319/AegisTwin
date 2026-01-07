"""
Policy Engine Benchmarks

Measures policy check latency with varying numbers of policies.

@ai_prompt: Run with PolicyBenchmark().run() to get metrics.
@context_boundary: benchmarks/bench_policy

# AI-GENERATED 2026-01-07
"""

import gc
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from aegistwin.governance.policy import PolicyEngine, Policy, PolicyEffect


@dataclass
class PolicyMetrics:
    """Metrics from policy benchmarks."""
    
    check_latency_ns: Dict[int, Dict[str, float]] = field(default_factory=dict)
    checks_per_second: Dict[int, float] = field(default_factory=dict)
    wildcard_vs_exact: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "check_latency_ns": self.check_latency_ns,
            "checks_per_second": self.checks_per_second,
            "wildcard_vs_exact": self.wildcard_vs_exact,
        }


class PolicyBenchmark:
    """
    Benchmark suite for PolicyEngine performance.
    
    Measures:
    - Policy check latency with 0, 10, 100, 1000 policies
    - Wildcard vs exact match performance
    """
    
    POLICY_COUNTS = [0, 10, 100, 1000]
    CHECK_ITERATIONS = 10_000
    
    def __init__(self):
        self.metrics = PolicyMetrics()
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from a sorted list."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)
    
    def _create_test_policies(self, count: int, use_wildcards: bool = False) -> List[Policy]:
        """Create test policies."""
        policies = []
        for i in range(count):
            if use_wildcards:
                action = f"action.{i % 10}.*"
                resource = f"resource.{i % 20}.*"
            else:
                action = f"action.{i}"
                resource = f"resource.{i}"
            
            policies.append(Policy(
                id=f"test-policy-{i}",
                action=action,
                resource=resource,
                effect=PolicyEffect.ALLOW if i % 2 == 0 else PolicyEffect.DENY,
                reason=f"Test policy {i}",
                priority=i,
            ))
        return policies
    
    def benchmark_check_latency(self, policy_count: int) -> Dict[str, Any]:
        """
        Benchmark policy check latency.
        
        Args:
            policy_count: Number of policies to load
            
        Returns:
            Dictionary with latency metrics
        """
        engine = PolicyEngine()
        
        # Clear default policies and add test ones
        engine._policies = []
        policies = self._create_test_policies(policy_count)
        for policy in policies:
            engine.add_policy(policy)
        
        latencies_ns: List[float] = []
        
        gc.collect()
        
        # Benchmark checks
        start_time = time.perf_counter_ns()
        
        for i in range(self.CHECK_ITERATIONS):
            action = f"action.{i % 100}"
            resource = f"resource.{i % 200}"
            
            check_start = time.perf_counter_ns()
            engine.check(action, resource, "test-actor")
            check_end = time.perf_counter_ns()
            
            latencies_ns.append(check_end - check_start)
        
        end_time = time.perf_counter_ns()
        
        total_time_seconds = (end_time - start_time) / 1e9
        checks_per_second = self.CHECK_ITERATIONS / total_time_seconds if total_time_seconds > 0 else 0
        
        return {
            "policy_count": policy_count,
            "iterations": self.CHECK_ITERATIONS,
            "total_time_seconds": total_time_seconds,
            "checks_per_second": checks_per_second,
            "latency_ns": {
                "mean": statistics.mean(latencies_ns),
                "p50": self._calculate_percentile(latencies_ns, 50),
                "p95": self._calculate_percentile(latencies_ns, 95),
                "p99": self._calculate_percentile(latencies_ns, 99),
            },
        }
    
    def benchmark_wildcard_vs_exact(self) -> Dict[str, Dict[str, float]]:
        """
        Compare wildcard pattern matching vs exact match performance.
        
        Returns:
            Dictionary comparing wildcard and exact match metrics
        """
        results = {}
        
        for match_type, use_wildcards in [("exact", False), ("wildcard", True)]:
            engine = PolicyEngine()
            engine._policies = []
            
            policies = self._create_test_policies(100, use_wildcards=use_wildcards)
            for policy in policies:
                engine.add_policy(policy)
            
            latencies_ns: List[float] = []
            
            gc.collect()
            
            for i in range(self.CHECK_ITERATIONS):
                action = f"action.{i % 10}.sub"
                resource = f"resource.{i % 20}.item"
                
                check_start = time.perf_counter_ns()
                engine.check(action, resource, "test-actor")
                check_end = time.perf_counter_ns()
                
                latencies_ns.append(check_end - check_start)
            
            results[match_type] = {
                "mean_ns": statistics.mean(latencies_ns),
                "p50_ns": self._calculate_percentile(latencies_ns, 50),
                "p95_ns": self._calculate_percentile(latencies_ns, 95),
                "p99_ns": self._calculate_percentile(latencies_ns, 99),
            }
        
        return results
    
    def run(self) -> PolicyMetrics:
        """
        Run all policy benchmarks.
        
        Returns:
            PolicyMetrics with all benchmark results
        """
        print("Running Policy Engine Benchmarks...")
        
        for count in self.POLICY_COUNTS:
            print(f"  Benchmarking with {count} policies...")
            result = self.benchmark_check_latency(count)
            
            self.metrics.check_latency_ns[count] = result["latency_ns"]
            self.metrics.checks_per_second[count] = result["checks_per_second"]
        
        print("  Benchmarking wildcard vs exact match...")
        self.metrics.wildcard_vs_exact = self.benchmark_wildcard_vs_exact()
        
        print("  Policy Engine Benchmarks complete.")
        return self.metrics
    
    def get_summary(self) -> str:
        """Get a formatted summary of benchmark results."""
        lines = ["## Policy Engine Benchmark Results\n"]
        lines.append("### Check Latency by Policy Count\n")
        lines.append("| Policy Count | Checks/sec | Mean Latency (µs) | P99 Latency (µs) |")
        lines.append("|--------------|------------|-------------------|------------------|")
        
        for count in self.POLICY_COUNTS:
            cps = self.metrics.checks_per_second.get(count, 0)
            latency = self.metrics.check_latency_ns.get(count, {})
            mean_us = latency.get("mean", 0) / 1000
            p99_us = latency.get("p99", 0) / 1000
            
            lines.append(f"| {count} | {cps:,.0f} | {mean_us:.2f} | {p99_us:.2f} |")
        
        lines.append("\n### Wildcard vs Exact Match\n")
        lines.append("| Match Type | Mean Latency (µs) | P99 Latency (µs) |")
        lines.append("|------------|-------------------|------------------|")
        
        for match_type in ["exact", "wildcard"]:
            data = self.metrics.wildcard_vs_exact.get(match_type, {})
            mean_us = data.get("mean_ns", 0) / 1000
            p99_us = data.get("p99_ns", 0) / 1000
            lines.append(f"| {match_type} | {mean_us:.2f} | {p99_us:.2f} |")
        
        return "\n".join(lines)


if __name__ == "__main__":
    benchmark = PolicyBenchmark()
    benchmark.run()
    print(benchmark.get_summary())
