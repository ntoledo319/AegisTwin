"""
Evaluation Metrics

Metrics collection and aggregation for evaluations.

@ai_prompt: Use MetricsCollector to track custom metrics during evaluation
@context_boundary: aegistwin/evaluation/metrics
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Metric:
    """Single metric measurement."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: dict[str, str] = field(default_factory=dict)
    unit: str | None = None


@dataclass
class MetricSummary:
    """Aggregated summary of a metric."""
    name: str
    count: int
    min: float
    max: float
    mean: float
    median: float
    std_dev: float
    p50: float
    p90: float
    p99: float


class MetricsCollector:
    """
    Collects and aggregates evaluation metrics.

    Supports:
    - Recording individual measurements
    - Time-series storage
    - Statistical aggregation
    - Percentile calculations
    """

    def __init__(self):
        self._metrics: dict[str, list[Metric]] = {}

    def record(self, metric: Metric) -> None:
        """Record a metric measurement."""
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)

    def record_value(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
        unit: str | None = None,
    ) -> None:
        """Convenience method to record a value."""
        self.record(Metric(
            name=name,
            value=value,
            tags=tags or {},
            unit=unit,
        ))

    def get_values(self, name: str) -> list[float]:
        """Get all values for a metric."""
        return [m.value for m in self._metrics.get(name, [])]

    def summarize(self, name: str) -> MetricSummary | None:
        """Get statistical summary for a metric."""
        values = self.get_values(name)
        if not values:
            return None

        sorted_values = sorted(values)
        n = len(values)

        return MetricSummary(
            name=name,
            count=n,
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if n > 1 else 0.0,
            p50=self._percentile(sorted_values, 50),
            p90=self._percentile(sorted_values, 90),
            p99=self._percentile(sorted_values, 99),
        )

    def aggregate(self) -> dict[str, float]:
        """Aggregate all metrics into summary dict."""
        result = {}
        for name in self._metrics:
            summary = self.summarize(name)
            if summary:
                result[f"{name}_mean"] = summary.mean
                result[f"{name}_p50"] = summary.p50
                result[f"{name}_p99"] = summary.p99
        return result

    def reset(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()

    @staticmethod
    def _percentile(sorted_values: list[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        if f == c:
            return sorted_values[f]
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)
