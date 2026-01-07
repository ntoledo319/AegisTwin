# Security & Governance

**AegisTwin Security Documentation**

---

## Overview

AegisTwin provides built-in security and governance capabilities for agent systems. This document covers the security model, policy configuration, and audit capabilities.

## Security Principles

1. **Deny by Default for Dangerous Operations** — Forbidden modules are always denied
2. **Audit Everything** — All actions are logged with full context
3. **Policy-Driven Access** — Configurable rules control what's allowed
4. **No PII Leakage** — Scanner prevents sensitive data from shipping

## Policy Engine

### Policy Structure

```python
Policy(
    id="unique-policy-id",
    action="action_pattern",      # Supports wildcards: *, ingest, export
    resource="resource_pattern",  # Supports wildcards: *, system.*, *pii*
    effect=PolicyEffect.DENY,     # ALLOW, DENY, REQUIRE_APPROVAL
    actor="actor_pattern",        # Optional: who is performing action
    reason="Human-readable reason",
    priority=100                  # Higher = evaluated first
)
```

### Default Policies

| Policy ID | Action | Resource | Effect | Reason |
|-----------|--------|----------|--------|--------|
| `deny-forbidden-modules` | `*` | `system.*` | DENY | System modules are restricted |
| `deny-pii-export` | `export` | `*pii*` | DENY | PII export not permitted |
| `deny-external-network` | `*` | `network.external` | DENY | External network restricted |
| `allow-ingest` | `ingest` | `*` | ALLOW | Ingestion is allowed |
| `allow-query` | `query` | `*` | ALLOW | Queries are allowed |
| `allow-analysis` | `analyze` | `*` | ALLOW | Analysis is allowed |

### Forbidden Modules

These are hardcoded and cannot be overridden by policy:

```python
FORBIDDEN_MODULES = [
    "system.shell",      # Shell execution
    "system.exec",       # Arbitrary code execution
    "network.external",  # External network access
    "data.export_pii",   # PII export
]
```

### Adding Custom Policies

```python
from aegistwin.governance import PolicyEngine, Policy, PolicyEffect

engine = PolicyEngine()

# Add a custom deny policy
engine.add_policy(Policy(
    id="deny-late-night-queries",
    action="query",
    resource="*",
    effect=PolicyEffect.DENY,
    reason="Queries not allowed after midnight",
    priority=200
))

# Check policy
allowed, reason = engine.check("query", "memory_graph", "user_123")
```

## Audit Logging

### Audit Events

Every policy decision generates an audit event:

```python
AuditLogged(
    action="export",
    actor="user_123",
    resource="user_data",
    outcome="denied",         # success, denied, error
    policy_id="deny-pii-export",
    reason="PII export not permitted"
)
```

### Audit Log Format

Audit logs are stored in `runs/<run-id>/audit.json`:

```json
[
  {
    "event_id": "abc123",
    "timestamp": "2026-01-06T15:30:00Z",
    "action": "export",
    "actor": "user_123",
    "resource": "user_data",
    "outcome": "denied",
    "policy_id": "deny-pii-export",
    "reason": "PII export not permitted"
  }
]
```

### Querying Audit Logs

```python
# Load audit log
import json
with open("runs/abc123/audit.json") as f:
    audits = json.load(f)

# Find all denials
denials = [a for a in audits if a["outcome"] == "denied"]

# Find actions by actor
user_actions = [a for a in audits if a["actor"] == "user_123"]
```

## PII Protection

### PII Scanner

Run before any release or commit:

```bash
python tools/pii_scan.py
```

The scanner checks for:
- Suspicious filenames (contact, messages, conversation, etc.)
- Suspicious directories (exports, raw_data, etc.)
- Content patterns (emails, phone numbers, SSNs)
- Personal names from known list
- SQLite databases with suspicious tables

### Scanner Configuration

Patterns are defined in `tools/pii_scan.py`:

```python
SUSPICIOUS_FILENAME_PATTERNS = [
    r'raw_data',
    r'contact',
    r'messages?',
    r'conversation',
    # ...
]

PII_CONTENT_PATTERNS = [
    (r'email_regex', 'email', 'MEDIUM'),
    (r'phone_regex', 'phone_number', 'HIGH'),
    # ...
]
```

### Quarantine

Suspicious files are moved to `/graveyard/PII/`:

```
graveyard/              # Quarantined data directory (gitignored, deleted)
└── [all PII removed]   # Directory has been permanently deleted
```

## Replay Security

### Deterministic Verification

Replay enables verification that agent behavior is consistent:

```python
runtime = AegisTwinRuntime()
result = runtime.replay("original_run_id")

if result["replay_results"]["deterministic"]:
    print("Behavior is reproducible")
else:
    print("Divergence detected!")
    print(result["replay_results"]["divergence_details"])
```

### Payload Hashes

Every event includes a `payload_hash` for verification:

```python
event = IngestCompleted(source="email", record_count=10, ...)
print(event.payload_hash)  # Deterministic hash of event content
```

During replay, hashes are compared to detect any divergence.

## Security Checklist

Before release:

- [ ] `python tools/pii_scan.py` passes (or findings are acknowledged)
- [ ] `/graveyard/PII/` is in `.gitignore`
- [ ] Git history is purged of PII (if applicable)
- [ ] Default policies are appropriate for use case
- [ ] Forbidden modules list is not modified
- [ ] Audit logging is enabled
- [ ] Synthetic fixtures are used for demos

## Incident Response

If PII is discovered in the codebase:

1. **Quarantine immediately** — Move to `/graveyard/PII/`
2. **Update .gitignore** — Prevent reintroduction
3. **Purge git history** — Use `tools/purge_history.sh`
4. **Force push** — Update remote (notify collaborators)
5. **Document** — Update `diligence_pack/PII_PURGE_REPORT.md`
