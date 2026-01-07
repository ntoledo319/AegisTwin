# Embedding Guide

**How to embed AegisTwin as an SDK in your application**

---

## Overview

AegisTwin can be used as a standalone tool or embedded as an SDK in your Python applications. This guide covers embedding patterns and best practices.

## Installation

```bash
pip install aegistwin

# With full dependencies
pip install aegistwin[full]
```

## Basic Embedding

### Minimal Integration

```python
from aegistwin import AegisTwin

# Create instance
twin = AegisTwin()

# Ingest data
run_id = twin.ingest(
    data={"records": [{"text": "Hello world"}]},
    source="my_app"
)

# Query
result = twin.query("What was said?")
print(result["answer"])
```

### With Custom Configuration

```python
from aegistwin import AegisTwin

twin = AegisTwin(config_path="my_config.yaml")
```

Configuration file:

```yaml
# my_config.yaml
runs_dir: "./my_runs"
enable_replay: true
enable_audit: true
policy_mode: "enforce"
```

## Advanced Integration

### Direct Runtime Access

For fine-grained control, use `AegisTwinRuntime` directly:

```python
from aegistwin import AegisTwinRuntime
from aegistwin.events import (
    IngestRequested,
    IngestCompleted,
    EventType
)

runtime = AegisTwinRuntime()

# Subscribe to events
def on_ingest_complete(event):
    print(f"Ingested {event.record_count} records")

runtime.event_bus.subscribe(EventType.INGEST_COMPLETED, on_ingest_complete)

# Start a run
run_id = runtime.start_run()

# Publish custom events
event = IngestRequested(
    run_id=run_id,
    source="my_source",
    data_type="custom",
    payload={"key": "value"}
)
runtime.event_bus.publish(event)

# End run
summary = runtime.end_run()
```

### Custom Policy Integration

```python
from aegistwin import AegisTwinRuntime
from aegistwin.governance import Policy, PolicyEffect

runtime = AegisTwinRuntime()

# Add custom policies
runtime.policy_engine.add_policy(Policy(
    id="my-app-policy",
    action="export",
    resource="sensitive_data",
    effect=PolicyEffect.DENY,
    reason="Export requires approval",
    priority=500
))

# Check before action
allowed, reason = runtime.policy_engine.check("export", "sensitive_data")
if not allowed:
    raise PermissionError(reason)
```

### Custom Event Types

```python
from aegistwin.events.schema import BaseEvent, EventType
from pydantic import Field

class MyCustomEvent(BaseEvent):
    """Custom event for my application."""
    event_type: EventType = EventType.ANALYSIS_COMPLETED  # Reuse existing
    my_field: str
    my_data: dict = Field(default_factory=dict)

# Use it
event = MyCustomEvent(
    run_id="abc123",
    my_field="custom_value",
    my_data={"key": "value"}
)
runtime.event_bus.publish(event)
```

## Framework Integration

### FastAPI

```python
from fastapi import FastAPI, Depends
from aegistwin import AegisTwin

app = FastAPI()
twin = AegisTwin()

def get_twin():
    return twin

@app.post("/ingest")
async def ingest_data(data: dict, twin: AegisTwin = Depends(get_twin)):
    run_id = twin.ingest(data, source="api")
    return {"run_id": run_id}

@app.get("/query")
async def query(q: str, twin: AegisTwin = Depends(get_twin)):
    return twin.query(q)
```

### Flask

```python
from flask import Flask, request, jsonify
from aegistwin import AegisTwin

app = Flask(__name__)
twin = AegisTwin()

@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.json
    run_id = twin.ingest(data, source="api")
    return jsonify({"run_id": run_id})

@app.route("/query")
def query():
    q = request.args.get("q")
    return jsonify(twin.query(q))
```

### Celery

```python
from celery import Celery
from aegistwin import AegisTwin

app = Celery("tasks")

@app.task
def process_data(data: dict):
    twin = AegisTwin()
    run_id = twin.ingest(data, source="celery")
    return run_id
```

## Patterns

### Singleton Runtime

```python
from aegistwin import AegisTwinRuntime

_runtime = None

def get_runtime():
    global _runtime
    if _runtime is None:
        _runtime = AegisTwinRuntime()
    return _runtime
```

### Context Manager

```python
from contextlib import contextmanager
from aegistwin import AegisTwinRuntime

@contextmanager
def aegis_run():
    runtime = AegisTwinRuntime()
    run_id = runtime.start_run()
    try:
        yield runtime, run_id
    finally:
        runtime.end_run()

# Usage
with aegis_run() as (runtime, run_id):
    runtime.ingest(data, source="my_app")
```

### Event Middleware

```python
from aegistwin import AegisTwinRuntime
from aegistwin.events import EventType

def logging_middleware(event):
    print(f"[{event.timestamp}] {event.event_type.value}")

runtime = AegisTwinRuntime()

# Subscribe middleware to all events
for event_type in EventType:
    runtime.event_bus.subscribe(event_type, logging_middleware)
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `runs_dir` | str | `"runs"` | Directory for run artifacts |
| `enable_replay` | bool | `True` | Enable event recording |
| `enable_audit` | bool | `True` | Enable audit logging |
| `policy_mode` | str | `"enforce"` | Policy mode: enforce, warn, disabled |
| `max_events_per_run` | int | `10000` | Maximum events per run |

## Error Handling

```python
from aegistwin import AegisTwin

twin = AegisTwin()

try:
    twin.ingest(data, source="restricted_source")
except PermissionError as e:
    print(f"Policy denied: {e}")
except FileNotFoundError as e:
    print(f"Run not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

```python
import pytest
from aegistwin import AegisTwinRuntime

@pytest.fixture
def runtime():
    rt = AegisTwinRuntime()
    rt.config["runs_dir"] = "./test_runs"
    return rt

def test_ingest(runtime):
    run_id = runtime.start_run()
    # ... test logic ...
    summary = runtime.end_run()
    assert summary["event_count"] > 0
```

## Performance Considerations

1. **Reuse runtime instances** — Don't create new instances per request
2. **Batch ingestion** — Ingest multiple records in one call
3. **Disable replay in high-throughput scenarios** — If you don't need it
4. **Use async patterns** — For I/O-bound operations

## Best Practices

1. **Initialize early** — Create runtime at app startup
2. **Use typed events** — Don't bypass the event system
3. **Check policies** — Before sensitive operations
4. **Log run IDs** — For debugging and tracing
5. **Test replay** — Verify determinism in CI
