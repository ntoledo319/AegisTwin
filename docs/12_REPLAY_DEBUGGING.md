# Replay & Debugging Guide

**AegisTwin Deterministic Replay Documentation**

---

## Overview

AegisTwin's replay system allows you to record agent runs and replay them later for debugging, verification, and compliance purposes.

## Why Replay Matters

1. **Debugging** — Reproduce issues exactly as they occurred
2. **Verification** — Confirm behavior is deterministic
3. **Compliance** — Prove what happened and why
4. **Testing** — Use recorded runs as test fixtures

## Recording Runs

Recording happens automatically when `enable_replay: true` (default):

```python
from aegistwin import AegisTwinRuntime

runtime = AegisTwinRuntime()
run_id = runtime.start_run()  # Recording starts

# ... do work ...

summary = runtime.end_run()  # Recording stops, artifacts saved
```

### Run Artifacts

Each run creates a directory with:

```
runs/<run-id>/
├── trace.json    # Event trace with payload hashes
├── audit.json    # Audit log entries
└── summary.md    # Human-readable summary
```

## Trace Format

`trace.json` contains the event sequence:

```json
[
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "ingest.requested",
    "timestamp": "2026-01-06T15:30:00Z",
    "run_id": "abc123",
    "parent_event_id": null,
    "payload_hash": "a1b2c3d4e5f6"
  },
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440001",
    "event_type": "ingest.completed",
    "timestamp": "2026-01-06T15:30:01Z",
    "run_id": "abc123",
    "parent_event_id": "550e8400-e29b-41d4-a716-446655440000",
    "payload_hash": "b2c3d4e5f6g7"
  }
]
```

## Replaying Runs

### Via CLI

```bash
aegistwin replay abc123
```

### Via SDK

```python
from aegistwin import AegisTwinRuntime

runtime = AegisTwinRuntime()
result = runtime.replay("abc123")

print(f"Deterministic: {result['replay_results']['deterministic']}")
print(f"Events matched: {result['replay_results']['events_matched']}")
```

### Via API

```bash
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"run_id": "abc123"}'
```

## Replay Results

```python
{
    "run_id": "def456",           # New run ID for replay
    "original_run_id": "abc123",
    "events_replayed": 8,
    "events_matched": 8,
    "events_diverged": 0,
    "deterministic": True,
    "divergence_details": []
}
```

### Handling Divergence

If replay diverges from original:

```python
{
    "events_diverged": 2,
    "deterministic": False,
    "divergence_details": [
        {
            "event_index": 3,
            "original_hash": "a1b2c3d4",
            "replay_hash": "x9y8z7w6",
            "event_type": "analysis.completed"
        }
    ]
}
```

## Debugging Workflow

### Step 1: Identify Problem Run

```bash
ls runs/
# abc123/  def456/  ghi789/
```

### Step 2: Examine Trace

```bash
cat runs/abc123/trace.json | jq '.'
```

Or load in Python:

```python
import json
with open("runs/abc123/trace.json") as f:
    trace = json.load(f)

for event in trace:
    print(f"{event['event_type']}: {event['payload_hash'][:8]}")
```

### Step 3: Examine Audit Log

```bash
cat runs/abc123/audit.json | jq '.'
```

### Step 4: Replay and Compare

```python
result = runtime.replay("abc123")

if not result["replay_results"]["deterministic"]:
    for divergence in result["replay_results"]["divergence_details"]:
        print(f"Diverged at event {divergence['event_index']}")
        print(f"  Expected: {divergence['original_hash']}")
        print(f"  Got: {divergence['replay_hash']}")
```

## Payload Hashes

Each event has a deterministic `payload_hash` computed from its content (excluding volatile fields like `event_id` and `timestamp`):

```python
from aegistwin.events import IngestCompleted

event = IngestCompleted(
    source="email",
    record_count=10,
    ingest_request_id="abc",
    duration_ms=15.0
)

print(event.payload_hash)  # Same hash for same content
```

### Hash Calculation

```python
def compute_hash(event):
    data = event.model_dump(exclude={"event_id", "timestamp", "payload_hash"})
    serialized = str(sorted(data.items()))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]
```

## Use Cases

### Regression Testing

Record a run, then replay after code changes:

```python
# Record baseline
runtime.start_run()
# ... run pipeline ...
baseline = runtime.end_run()

# After code changes, replay and verify
result = runtime.replay(baseline["run_id"])
assert result["replay_results"]["deterministic"]
```

### Incident Investigation

When something goes wrong:

1. Get the run ID from logs
2. Load the trace and audit log
3. Walk through events to find the issue
4. Identify the event where behavior diverged

### Compliance Audit

Prove what the agent did:

```python
# Load trace for specific run
with open(f"runs/{run_id}/trace.json") as f:
    trace = json.load(f)

# Generate compliance report
for event in trace:
    print(f"{event['timestamp']}: {event['event_type']}")
```

## Best Practices

1. **Always enable replay in production** — The overhead is minimal
2. **Archive run artifacts** — Keep traces for compliance
3. **Test replay regularly** — Verify determinism hasn't broken
4. **Use payload hashes** — Don't rely on timestamps for comparison
5. **Log run IDs** — Make it easy to find traces later
