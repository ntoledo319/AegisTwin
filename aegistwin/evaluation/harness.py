"""
Agent Evaluation Harness

Core infrastructure for running agent evaluations.

@ai_prompt: Create an EvaluationHarness instance and call run() with your agent
@context_boundary: aegistwin/evaluation/harness
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from aegistwin.evaluation.metrics import Metric, MetricsCollector


class EvaluationStatus(str, Enum):
    """Status of an evaluation run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """Individual test case for evaluation."""
    id: str
    name: str
    description: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    validators: list[Callable[[Any, Any], bool]] = field(default_factory=list)
    timeout_seconds: float = 30.0
    tags: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of a single test case."""
    test_id: str
    status: EvaluationStatus
    actual_output: Any | None = None
    error_message: str | None = None
    duration_ms: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    evaluation_id: str
    started_at: datetime
    completed_at: datetime
    agent_id: str
    benchmark_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    test_results: list[TestResult]
    aggregate_metrics: dict[str, float]

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def success(self) -> bool:
        """Check if evaluation was successful."""
        return self.failed_tests == 0 and self.error_tests == 0


class AgentProtocol(Protocol):
    """Protocol for agents that can be evaluated."""

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input and return output."""
        ...


class EvaluationHarness:
    """
    Main harness for running agent evaluations.

    Provides:
    - Test case execution with timeouts
    - Metrics collection
    - Result aggregation
    - Report generation

    Attributes:
        metrics_collector: Collects evaluation metrics
        test_cases: Registered test cases
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self._test_cases: list[TestCase] = []
        self._hooks: dict[str, list[Callable]] = {
            "before_all": [],
            "after_all": [],
            "before_each": [],
            "after_each": [],
        }

    def register_test(self, test_case: TestCase) -> None:
        """Register a test case."""
        self._test_cases.append(test_case)

    def register_tests(self, test_cases: list[TestCase]) -> None:
        """Register multiple test cases."""
        self._test_cases.extend(test_cases)

    def add_hook(self, hook_type: str, callback: Callable) -> None:
        """Add a lifecycle hook."""
        if hook_type in self._hooks:
            self._hooks[hook_type].append(callback)

    async def run(
        self,
        agent: AgentProtocol,
        agent_id: str = "unknown",
        benchmark_id: str = "default",
        tags: list[str] | None = None,
    ) -> EvaluationResult:
        """
        Run evaluation against an agent.

        Args:
            agent: Agent implementing AgentProtocol
            agent_id: Identifier for the agent
            benchmark_id: Identifier for the benchmark suite
            tags: Optional tags to filter test cases

        Returns:
            Complete evaluation result
        """
        import secrets

        evaluation_id = secrets.token_hex(8)
        started_at = datetime.now(timezone.utc)

        # Filter test cases by tags if provided
        test_cases = self._test_cases
        if tags:
            test_cases = [tc for tc in test_cases if any(t in tc.tags for t in tags)]

        # Run before_all hooks
        for hook in self._hooks["before_all"]:
            await self._run_hook(hook)

        # Execute test cases
        test_results: list[TestResult] = []

        for test_case in test_cases:
            result = await self._run_test(agent, test_case)
            test_results.append(result)

        # Run after_all hooks
        for hook in self._hooks["after_all"]:
            await self._run_hook(hook)

        # Aggregate results
        completed_at = datetime.now(timezone.utc)

        passed = sum(1 for r in test_results if r.status == EvaluationStatus.PASSED)
        failed = sum(1 for r in test_results if r.status == EvaluationStatus.FAILED)
        errors = sum(1 for r in test_results if r.status == EvaluationStatus.ERROR)
        skipped = sum(1 for r in test_results if r.status == EvaluationStatus.SKIPPED)

        # Aggregate metrics
        aggregate_metrics = self.metrics_collector.aggregate()

        return EvaluationResult(
            evaluation_id=evaluation_id,
            started_at=started_at,
            completed_at=completed_at,
            agent_id=agent_id,
            benchmark_id=benchmark_id,
            total_tests=len(test_results),
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            skipped_tests=skipped,
            test_results=test_results,
            aggregate_metrics=aggregate_metrics,
        )

    async def _run_test(
        self,
        agent: AgentProtocol,
        test_case: TestCase,
    ) -> TestResult:
        """Execute a single test case."""
        # Run before_each hooks
        for hook in self._hooks["before_each"]:
            await self._run_hook(hook, test_case)

        start_time = time.perf_counter()

        try:
            # Execute with timeout
            actual_output = await asyncio.wait_for(
                agent.process(test_case.input_data),
                timeout=test_case.timeout_seconds,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Collect latency metric
            self.metrics_collector.record(
                Metric(name="latency_ms", value=duration_ms, tags={"test_id": test_case.id})
            )

            # Validate output
            status = EvaluationStatus.PASSED
            error_message = None

            if test_case.expected_output is not None:
                if actual_output != test_case.expected_output:
                    status = EvaluationStatus.FAILED
                    error_message = f"Output mismatch: expected {test_case.expected_output}, got {actual_output}"

            for validator in test_case.validators:
                try:
                    if not validator(actual_output, test_case.expected_output):
                        status = EvaluationStatus.FAILED
                        error_message = "Validator failed"
                        break
                except Exception as e:
                    status = EvaluationStatus.ERROR
                    error_message = f"Validator error: {e}"
                    break

            result = TestResult(
                test_id=test_case.id,
                status=status,
                actual_output=actual_output,
                error_message=error_message,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = TestResult(
                test_id=test_case.id,
                status=EvaluationStatus.ERROR,
                error_message=f"Timeout after {test_case.timeout_seconds}s",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            result = TestResult(
                test_id=test_case.id,
                status=EvaluationStatus.ERROR,
                error_message=str(e),
                duration_ms=duration_ms,
            )

        # Run after_each hooks
        for hook in self._hooks["after_each"]:
            await self._run_hook(hook, test_case, result)

        return result

    async def _run_hook(self, hook: Callable, *args) -> None:
        """Run a hook safely."""
        try:
            if asyncio.iscoroutinefunction(hook):
                await hook(*args)
            else:
                hook(*args)
        except Exception:
            pass  # Hooks should not fail evaluation
