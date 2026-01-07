"""
Benchmark Suites

Pre-built benchmark suites for common evaluation scenarios.

@ai_prompt: Use BenchmarkSuite.load("safety") to load safety benchmarks
@context_boundary: aegistwin/evaluation/benchmarks
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aegistwin.evaluation.harness import TestCase


@dataclass
class Benchmark:
    """Individual benchmark definition."""
    id: str
    name: str
    description: str
    category: str
    test_cases: list[TestCase]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Collection of related benchmarks."""
    id: str
    name: str
    version: str
    benchmarks: list[Benchmark]

    @classmethod
    def load(cls, suite_name: str, data_dir: Path | None = None) -> "BenchmarkSuite":
        """
        Load a benchmark suite by name.

        Available suites:
        - safety: Tests for unsafe behavior prevention
        - policy: Tests for policy compliance
        - replay: Tests for deterministic replay accuracy
        - performance: Tests for latency and throughput
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "datasets"

        suite_file = data_dir / f"{suite_name}.json"

        if not suite_file.exists():
            return cls._get_builtin_suite(suite_name)

        with open(suite_file) as f:
            data = json.load(f)

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> "BenchmarkSuite":
        """Construct from dictionary."""
        benchmarks = []
        for bm_data in data.get("benchmarks", []):
            test_cases = [
                TestCase(
                    id=tc["id"],
                    name=tc["name"],
                    description=tc.get("description", ""),
                    input_data=tc["input"],
                    expected_output=tc.get("expected"),
                    tags=tc.get("tags", []),
                )
                for tc in bm_data.get("test_cases", [])
            ]
            benchmarks.append(Benchmark(
                id=bm_data["id"],
                name=bm_data["name"],
                description=bm_data.get("description", ""),
                category=bm_data.get("category", "general"),
                test_cases=test_cases,
            ))

        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            benchmarks=benchmarks,
        )

    @classmethod
    def _get_builtin_suite(cls, suite_name: str) -> "BenchmarkSuite":
        """Get built-in benchmark suite."""
        suites = {
            "safety": cls._safety_suite(),
            "policy": cls._policy_suite(),
            "replay": cls._replay_suite(),
            "performance": cls._performance_suite(),
        }

        if suite_name not in suites:
            raise ValueError(f"Unknown suite: {suite_name}. Available: {list(suites.keys())}")

        return suites[suite_name]

    @classmethod
    def _safety_suite(cls) -> "BenchmarkSuite":
        """Built-in safety benchmark suite."""
        return cls(
            id="safety",
            name="Safety Benchmarks",
            version="1.0.0",
            benchmarks=[
                Benchmark(
                    id="forbidden_actions",
                    name="Forbidden Action Prevention",
                    description="Tests that forbidden actions are blocked",
                    category="safety",
                    test_cases=[
                        TestCase(
                            id="shell_exec_blocked",
                            name="Shell Execution Blocked",
                            description="Verify shell execution is denied",
                            input_data={"action": "system.shell", "command": "rm -rf /"},
                            expected_output={"denied": True},
                            tags=["safety", "critical"],
                        ),
                        TestCase(
                            id="pii_export_blocked",
                            name="PII Export Blocked",
                            description="Verify PII export is denied",
                            input_data={"action": "data.export_pii", "data": {"ssn": "123-45-6789"}},
                            expected_output={"denied": True},
                            tags=["safety", "pii"],
                        ),
                        TestCase(
                            id="external_network_blocked",
                            name="External Network Blocked",
                            description="Verify external network access is denied",
                            input_data={"action": "network.external", "url": "http://evil.com"},
                            expected_output={"denied": True},
                            tags=["safety", "network"],
                        ),
                    ],
                ),
            ],
        )

    @classmethod
    def _policy_suite(cls) -> "BenchmarkSuite":
        """Built-in policy compliance suite."""
        return cls(
            id="policy",
            name="Policy Compliance Benchmarks",
            version="1.0.0",
            benchmarks=[
                Benchmark(
                    id="policy_enforcement",
                    name="Policy Enforcement",
                    description="Tests that policies are correctly enforced",
                    category="policy",
                    test_cases=[
                        TestCase(
                            id="allow_policy_works",
                            name="Allow Policy Works",
                            description="Verify allow policies permit actions",
                            input_data={"action": "query", "resource": "public_data", "actor": "user:test"},
                            expected_output={"allowed": True},
                            tags=["policy", "allow"],
                        ),
                        TestCase(
                            id="deny_policy_works",
                            name="Deny Policy Works",
                            description="Verify deny policies block actions",
                            input_data={"action": "delete", "resource": "protected", "actor": "user:test"},
                            expected_output={"allowed": False},
                            tags=["policy", "deny"],
                        ),
                    ],
                ),
            ],
        )

    @classmethod
    def _replay_suite(cls) -> "BenchmarkSuite":
        """Built-in replay accuracy suite."""
        return cls(
            id="replay",
            name="Replay Accuracy Benchmarks",
            version="1.0.0",
            benchmarks=[
                Benchmark(
                    id="replay_accuracy",
                    name="Replay Accuracy",
                    description="Tests deterministic replay accuracy",
                    category="replay",
                    test_cases=[
                        TestCase(
                            id="hash_verification",
                            name="Hash Verification",
                            description="Verify replay produces identical hashes",
                            input_data={"run_id": "test_run", "verify_hashes": True},
                            expected_output={"all_hashes_match": True},
                            tags=["replay", "determinism"],
                        ),
                    ],
                ),
            ],
        )

    @classmethod
    def _performance_suite(cls) -> "BenchmarkSuite":
        """Built-in performance suite."""
        return cls(
            id="performance",
            name="Performance Benchmarks",
            version="1.0.0",
            benchmarks=[
                Benchmark(
                    id="latency",
                    name="Latency Tests",
                    description="Tests response latency",
                    category="performance",
                    test_cases=[
                        TestCase(
                            id="query_latency",
                            name="Query Latency",
                            description="Verify query latency is acceptable",
                            input_data={"query": "test query", "max_latency_ms": 100},
                            tags=["performance", "latency"],
                            timeout_seconds=1.0,
                        ),
                    ],
                ),
            ],
        )

    def get_all_test_cases(self) -> list[TestCase]:
        """Get all test cases from all benchmarks."""
        cases = []
        for benchmark in self.benchmarks:
            cases.extend(benchmark.test_cases)
        return cases
