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

from aegistwin.observability.tracing import (
    init_tracing,
    get_tracer,
    trace_event,
    shutdown_tracing,
    TracingConfig,
)
from aegistwin.observability.metrics import (
    init_metrics,
    get_meter,
    record_event,
    record_policy_check,
    record_latency,
    MetricsRegistry,
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
