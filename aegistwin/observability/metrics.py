"""
AegisTwin Prometheus Metrics

Provides metrics collection using OpenTelemetry metrics API.

@ai_prompt: Initialize metrics at startup, then use record_* functions.
@context_boundary: aegistwin/observability/metrics

## Exported Metrics
- aegistwin_events_total: Counter of events by type
- aegistwin_policy_checks_total: Counter of policy checks by outcome
- aegistwin_event_latency_seconds: Histogram of event processing latency
- aegistwin_active_runs: Gauge of currently active runs

# AI-GENERATED 2026-01-07
"""

import time
from dataclasses import dataclass
from typing import Any, Optional

# Try importing OpenTelemetry metrics
try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None
    MeterProvider = None

# Try importing Prometheus exporter
try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    PrometheusMetricReader = None


@dataclass
class MetricsRegistry:
    """
    Registry holding all AegisTwin metrics.

    Attributes:
        events_total: Counter for total events by type
        policy_checks_total: Counter for policy checks by outcome
        event_latency: Histogram for event latency
        active_runs: Gauge for active run count
    """
    events_total: Any = None
    policy_checks_total: Any = None
    event_latency: Any = None
    active_runs: Any = None
    _active_run_count: int = 0

    def increment_events(self, event_type: str, count: int = 1) -> None:
        """Increment event counter."""
        if self.events_total:
            self.events_total.add(count, {"event_type": event_type})

    def increment_policy_checks(self, outcome: str, count: int = 1) -> None:
        """Increment policy check counter."""
        if self.policy_checks_total:
            self.policy_checks_total.add(count, {"outcome": outcome})

    def record_latency(self, latency_seconds: float, operation: str = "event") -> None:
        """Record operation latency."""
        if self.event_latency:
            self.event_latency.record(latency_seconds, {"operation": operation})

    def increment_active_runs(self) -> None:
        """Increment active run count."""
        self._active_run_count += 1
        if self.active_runs:
            self.active_runs.set(self._active_run_count)

    def decrement_active_runs(self) -> None:
        """Decrement active run count."""
        self._active_run_count = max(0, self._active_run_count - 1)
        if self.active_runs:
            self.active_runs.set(self._active_run_count)


# Global state
_meter_provider: Optional["MeterProvider"] = None
_registry: MetricsRegistry | None = None
_initialized: bool = False


def init_metrics(
    service_name: str = "aegistwin",
    prometheus_port: int | None = None,
    console_export: bool = False,
) -> MetricsRegistry:
    """
    Initialize OpenTelemetry metrics.

    Args:
        service_name: Name of the service
        prometheus_port: Port for Prometheus endpoint (optional)
        console_export: Whether to export to console

    Returns:
        MetricsRegistry with initialized metrics
    """
    global _meter_provider, _registry, _initialized

    if _initialized and _registry:
        return _registry

    _registry = MetricsRegistry()

    if not METRICS_AVAILABLE:
        print("Warning: OpenTelemetry metrics not available.")
        _initialized = True
        return _registry

    # Create resource
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
    })

    readers = []

    # Add Prometheus reader if available and port specified
    if prometheus_port and PROMETHEUS_AVAILABLE:
        prometheus_reader = PrometheusMetricReader()
        readers.append(prometheus_reader)

    # Add console exporter if requested
    if console_export:
        console_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=5000,
        )
        readers.append(console_reader)

    # Create provider with readers
    if readers:
        _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    else:
        _meter_provider = MeterProvider(resource=resource)

    metrics.set_meter_provider(_meter_provider)

    # Create meter and metrics
    meter = metrics.get_meter("aegistwin", "0.1.0")

    _registry.events_total = meter.create_counter(
        name="aegistwin_events_total",
        description="Total number of events processed",
        unit="1",
    )

    _registry.policy_checks_total = meter.create_counter(
        name="aegistwin_policy_checks_total",
        description="Total number of policy checks",
        unit="1",
    )

    _registry.event_latency = meter.create_histogram(
        name="aegistwin_event_latency_seconds",
        description="Event processing latency",
        unit="s",
    )

    # For gauge, we use an observable gauge with callback
    def get_active_runs(options):
        yield metrics.Observation(_registry._active_run_count)

    _registry.active_runs = meter.create_observable_gauge(
        name="aegistwin_active_runs",
        description="Number of currently active runs",
        unit="1",
        callbacks=[get_active_runs],
    )

    _initialized = True
    return _registry


def get_meter(name: str = "aegistwin") -> Any:
    """
    Get a meter instance.

    Args:
        name: Name for the meter

    Returns:
        OpenTelemetry Meter or None if not available
    """
    if not METRICS_AVAILABLE or not _initialized:
        return None

    return metrics.get_meter(name)


def get_registry() -> MetricsRegistry:
    """
    Get the global metrics registry.

    Returns:
        MetricsRegistry instance
    """
    global _registry

    if _registry is None:
        _registry = MetricsRegistry()

    return _registry


def record_event(event_type: str, count: int = 1) -> None:
    """
    Record an event metric.

    Args:
        event_type: Type of event
        count: Number of events (default 1)
    """
    registry = get_registry()
    registry.increment_events(event_type, count)


def record_policy_check(outcome: str, count: int = 1) -> None:
    """
    Record a policy check metric.

    Args:
        outcome: Outcome of the check (allow, deny, error)
        count: Number of checks (default 1)
    """
    registry = get_registry()
    registry.increment_policy_checks(outcome, count)


def record_latency(latency_seconds: float, operation: str = "event") -> None:
    """
    Record operation latency.

    Args:
        latency_seconds: Latency in seconds
        operation: Type of operation
    """
    registry = get_registry()
    registry.record_latency(latency_seconds, operation)


class LatencyTimer:
    """
    Context manager for timing operations.

    Example:
        with LatencyTimer("query"):
            result = execute_query()
    """

    def __init__(self, operation: str = "event"):
        self.operation = operation
        self.start_time: float | None = None

    def __enter__(self) -> "LatencyTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        if self.start_time:
            elapsed = time.perf_counter() - self.start_time
            record_latency(elapsed, self.operation)


def generate_prometheus_metrics() -> str:
    """
    Generate Prometheus-format metrics output.

    This is useful for /metrics endpoint when not using
    the automatic Prometheus exporter.

    Returns:
        Prometheus format metrics string
    """
    registry = get_registry()

    lines = [
        "# HELP aegistwin_events_total Total number of events processed",
        "# TYPE aegistwin_events_total counter",
        "# HELP aegistwin_policy_checks_total Total number of policy checks",
        "# TYPE aegistwin_policy_checks_total counter",
        "# HELP aegistwin_active_runs Number of currently active runs",
        "# TYPE aegistwin_active_runs gauge",
        f"aegistwin_active_runs {registry._active_run_count}",
    ]

    return "\n".join(lines)
