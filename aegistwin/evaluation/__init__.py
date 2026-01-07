"""
AegisTwin Agent Evaluation Framework

Provides benchmarking, testing, and evaluation infrastructure for AI agents.

@ai_prompt: Use EvaluationHarness to run agent evaluations
@context_boundary: aegistwin/evaluation
"""

from aegistwin.evaluation.benchmarks import Benchmark, BenchmarkSuite
from aegistwin.evaluation.harness import EvaluationHarness, EvaluationResult
from aegistwin.evaluation.metrics import Metric, MetricsCollector
from aegistwin.evaluation.reports import ReportGenerator

__all__ = [
    "EvaluationHarness",
    "EvaluationResult",
    "BenchmarkSuite",
    "Benchmark",
    "MetricsCollector",
    "Metric",
    "ReportGenerator",
]
