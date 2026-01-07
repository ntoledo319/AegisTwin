# AegisTwin Observability Guide

This document describes how to enable and configure observability features in AegisTwin, including distributed tracing with OpenTelemetry and metrics with Prometheus.

## Quick Start

```python
from aegistwin import AegisTwin
from aegistwin.observability import init_tracing, init_metrics

# Initialize tracing
init_tracing("aegistwin-service")

# Initialize metrics
init_metrics("aegistwin-service")

# Use AegisTwin normally
twin = AegisTwin()
twin.run_demo()
```

## Installation

Install AegisTwin with observability dependencies:

```bash
pip install aegistwin[observability]
```

Or install OpenTelemetry packages directly:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

## Tracing

### Configuration

Tracing can be configured via environment variables or programmatically.

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_SERVICE_NAME` | Service name for traces | `aegistwin` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | None |
| `OTEL_TRACES_EXPORTER` | Exporter type (`otlp`, `console`, `none`) | `otlp` |

#### Programmatic Configuration

```python
from aegistwin.observability import init_tracing, TracingConfig

# Using parameters
init_tracing(
    service_name="my-aegistwin-app",
    otlp_endpoint="http://localhost:4317",
    console_export=True,  # Also print to console
)

# Using config object
config = TracingConfig(
    service_name="my-aegistwin-app",
    otlp_endpoint="http://jaeger:4317",
    console_export=False,
    enabled=True,
)
init_tracing(config=config)
```

### Using Traces

#### Function Decorator

```python
from aegistwin.observability import trace_event

@trace_event("process_data")
def process_data(data):
    # This function will be traced
    return transform(data)
```

#### Context Manager

```python
from aegistwin.observability.tracing import trace_span

with trace_span("my_operation", {"key": "value"}):
    # Operations here are traced
    result = do_something()
```

#### Manual Spans

```python
from aegistwin.observability import get_tracer

tracer = get_tracer("my-module")

with tracer.start_as_current_span("custom-operation") as span:
    span.set_attribute("custom.attribute", "value")
    result = perform_operation()
```

### Span Attributes

AegisTwin automatically adds these attributes to event-related spans:

| Attribute | Description |
|-----------|-------------|
| `aegistwin.event.type` | Event type (e.g., `ingest.requested`) |
| `aegistwin.event.id` | Unique event identifier |
| `aegistwin.event.run_id` | Pipeline run identifier |
| `aegistwin.event.parent_id` | Parent event ID (if any) |

## Metrics

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `aegistwin_events_total` | Counter | Total events by type |
| `aegistwin_policy_checks_total` | Counter | Policy checks by outcome |
| `aegistwin_event_latency_seconds` | Histogram | Event processing latency |
| `aegistwin_active_runs` | Gauge | Currently active runs |

### Recording Metrics

```python
from aegistwin.observability import (
    record_event,
    record_policy_check,
    record_latency,
)

# Record an event
record_event("ingest.completed")

# Record policy check
record_policy_check("allow")  # or "deny"

# Record latency
record_latency(0.025, "query")  # 25ms for query operation
```

### Latency Timer

```python
from aegistwin.observability.metrics import LatencyTimer

with LatencyTimer("query"):
    result = execute_query()
# Latency is automatically recorded
```

### Prometheus Endpoint

When using the API, metrics are exposed at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

## Integration Examples

### Jaeger

```bash
# Start Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Configure AegisTwin
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=aegistwin

# Run your application
python -m aegistwin.api
```

Access Jaeger UI at http://localhost:16686

### Grafana + Prometheus

1. Start the observability stack:

```bash
cd docker
docker-compose up -d prometheus grafana
```

2. Access Grafana at http://localhost:3000 (admin/admin)

3. Import the AegisTwin dashboard from `observability/grafana/dashboards/`

### Datadog

```python
from aegistwin.observability import init_tracing

init_tracing(
    service_name="aegistwin",
    otlp_endpoint="http://localhost:4317",  # Datadog Agent OTLP endpoint
)
```

Configure Datadog Agent to accept OTLP:

```yaml
# datadog.yaml
otlp_config:
  receiver:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
```

## Docker Compose Stack

The included `docker-compose.yml` provides a full observability stack:

```bash
cd docker
docker-compose up -d
```

Services:
- **AegisTwin**: http://localhost:8000
- **Jaeger UI**: http://localhost:16686
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Troubleshooting

### Traces Not Appearing

1. Check OTLP endpoint is reachable:
   ```bash
   curl -v http://localhost:4317
   ```

2. Enable console export for debugging:
   ```bash
   export OTEL_TRACES_EXPORTER=console
   ```

3. Verify tracing is initialized:
   ```python
   from aegistwin.observability.tracing import _initialized
   print(f"Tracing initialized: {_initialized}")
   ```

### High Memory Usage

If metrics are causing memory issues:

1. Reduce histogram bucket count
2. Increase export interval
3. Disable unused metrics

### Missing Dependencies

```bash
# Check if OpenTelemetry is installed
python -c "from opentelemetry import trace; print('OK')"

# Install if missing
pip install aegistwin[observability]
```

## Best Practices

1. **Initialize Early**: Call `init_tracing()` before any traced operations
2. **Use Descriptive Names**: Span names should describe the operation
3. **Add Context**: Include relevant attributes for debugging
4. **Don't Over-Trace**: Trace meaningful operations, not every function
5. **Handle Errors**: Ensure spans are closed even on exceptions

---

*Last updated: 2026-01-07*
