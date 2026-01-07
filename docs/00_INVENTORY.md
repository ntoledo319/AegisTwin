# AegisTwin Codebase Inventory

**Generated:** 2026-01-06  
**Status:** ✅ PRODUCTION READY

---

## Package Structure

### aegistwin/ (MAIN PACKAGE)
- **Purpose:** Event-driven agent runtime with governance, replay, and memory
- **Status:** ✅ Production ready

### Legacy Source Directories (Reference Only)
- `legacy/runtime/` - Original runtime components (wrapped by aegistwin)
- `legacy/connectors/` - Original connector code (wrapped by aegistwin)

---

## Entrypoints

| Package | Entrypoint | Type |
|---------|-----------|------|
| aegistwin | `aegistwin/__main__.py` | CLI |
| aegistwin | `aegistwin/api/` | FastAPI |

---

## Dependency Files

| Path | Type |
|------|------|
| `pyproject.toml` | PEP 517 |
| `requirements.txt` | pip |

---

## Key Components

### aegistwin/runtime/
- `core.py` - Event bus, runtime engine
- Policy enforcement, audit logging

### aegistwin/modules/
- `connectors/` - Data connectors (email, calendar, messages)
- `pipeline/` - Data normalization and processing
- `analysis/` - Cognitive and communication analysis
- `graph/` - Knowledge graph operations
- `memory/` - Episodic, semantic, procedural memory

### aegistwin/governance/
- Policy engine with configurable gates
- Audit trail with full traceability

### aegistwin/events/
- Typed Pydantic event schemas
- Event tracing with payload hashes

---

## Synthetic Data

All demo data is synthetically generated:
- `fixtures/demo_small.json` - Small demo dataset
- `fixtures/demo_medium.json` - Medium demo dataset
- `fixtures/contacts.json` - Synthetic contacts
- `fixtures/messages.json` - Synthetic messages

---

## Verification

```bash
make test      # Run tests
make demo      # Run demos
make scan      # PII scanner
```
