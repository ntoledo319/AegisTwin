# AegisTwin Rego Policies

This directory contains Open Policy Agent (OPA) Rego policies for AegisTwin authorization.

## Policy Structure

### Input Schema

All policies receive input in the following format:

```json
{
  "action": "query",
  "resource": "memory_graph",
  "actor": "user",
  "context": {
    "run_id": "abc123",
    "timestamp": "2026-01-07T00:00:00Z"
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | The action being performed (query, ingest, analyze, export, llm.query) |
| `resource` | string | The resource being accessed (memory_graph, system.shell, llm.external) |
| `actor` | string | Who is performing the action (user, system, admin) |
| `context` | object | Additional context (run_id, timestamp, etc.) |

## Default Policy

The `default.rego` policy implements:

### Allowed Actions
- `query` - Always allowed
- `ingest` - Allowed for non-system resources
- `analyze` - Always allowed
- `llm.query` on `llm.mock` - Allowed
- `replay` - Always allowed
- Any action by `admin` actor - Allowed

### Denied Actions
- Access to `system.shell` - Forbidden
- Access to `system.exec` - Forbidden
- `export` of resources containing `pii` - Forbidden
- Access to `network.external` - Restricted

## Writing Custom Policies

### Basic Allow Rule

```rego
package aegistwin.authz

allow if {
    input.action == "my_action"
    input.actor == "authorized_user"
}
```

### Deny with Reason

```rego
deny contains reason if {
    input.action == "dangerous_action"
    reason := "This action requires approval"
}
```

### Context-Based Rules

```rego
allow if {
    input.action == "query"
    input.context.rate_limit_remaining > 0
}
```

## Using with AegisTwin

### Via OPA Server

```python
from aegistwin.governance.opa import OPAEvaluator

evaluator = OPAEvaluator(opa_url="http://localhost:8181")
allowed, reason = evaluator.check("query", "memory_graph", "user")
```

### Via Embedded Policy

```python
from aegistwin.governance.opa import OPAEvaluator

evaluator = OPAEvaluator(
    policy_path="aegistwin/governance/policies/default.rego"
)
allowed, reason = evaluator.check("query", "memory_graph", "user")
```

### With PolicyEngine Integration

```python
from aegistwin.governance.policy import PolicyEngine
from aegistwin.governance.opa import OPAEvaluator

engine = PolicyEngine()
evaluator = OPAEvaluator(opa_url="http://localhost:8181")
engine.set_opa_evaluator(evaluator)

# Now policy checks will use OPA
allowed, reason = engine.check("query", "memory_graph")
```

## Testing Policies

### Using OPA CLI

```bash
# Test a policy
opa eval -d default.rego -i input.json "data.aegistwin.authz.allow"

# Interactive REPL
opa run default.rego
> data.aegistwin.authz.allow with input as {"action": "query", "resource": "test", "actor": "user"}
```

### Example Input File

```json
{
  "action": "query",
  "resource": "memory_graph",
  "actor": "user",
  "context": {}
}
```

## Running OPA Server

```bash
# Start OPA with policies
docker run -p 8181:8181 -v $(pwd):/policies \
  openpolicyagent/opa run --server /policies

# Or with the OPA binary
opa run --server ./default.rego
```

## Best Practices

1. **Fail Closed**: Default deny, explicitly allow
2. **Log Denials**: Use deny rules with reasons
3. **Test Thoroughly**: Test all policy paths
4. **Version Control**: Keep policies in git
5. **Separate Concerns**: One policy file per domain

---

*Last updated: 2026-01-07*
