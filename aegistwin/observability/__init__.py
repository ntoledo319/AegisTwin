"""
AegisTwin Observability Module

OpenTelemetry tracing and Prometheus metrics for production observability.

@ai_prompt: Call init_tracing() at application startup before using tracers.
@context_boundary: aegistwin/observability

## Quick Start
```python
from aegistwin.observability import init_tracing, get_tracer

init_tracing("aegistwin-service")
tracer = get_tracer("my-module")

with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

# AI-GENERATED 2026-01-07
"""

from aegistwin.observability.metrics import (
    MetricsRegistry,
    get_meter,
    init_metrics,
    record_event,
    record_latency,
    record_policy_check,
)
from aegistwin.observability.tracing import (
    TracingConfig,
    get_tracer,
    init_tracing,
    shutdown_tracing,
    trace_event,
)

__all__ = [
    # Tracing
    "init_tracing",
    "get_tracer",
    "trace_event",
    "shutdown_tracing",
    "TracingConfig",
    # Metrics
    "init_metrics",
    "get_meter",
    "record_event",
    "record_policy_check",
    "record_latency",
    "MetricsRegistry",
]
