# AegisTwin

**Event-driven agent runtime + governance + deterministic replay + local memory graph.**

[![CI](https://github.com/aegistwin/aegistwin/workflows/CI/badge.svg)](https://github.com/aegistwin/aegistwin/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What It Is

AegisTwin is a **productized agent runtime** that provides:

- 🔄 **Event-Driven Architecture** — All module communication through typed, traceable events
- 🛡️ **Built-in Governance** — Policy gates that deny forbidden actions with audit logging
- 🔁 **Deterministic Replay** — Record and replay agent decisions for debugging and verification
- 🧠 **Local Memory Graph** — Episodic, semantic, and procedural memory systems

## Why It Matters

Modern AI agents need more than inference — they need **governance**, **auditability**, and **reproducibility**. AegisTwin provides the infrastructure to build agents that are:

- **Auditable** — Every decision is logged with full trace
- **Controllable** — Policy gates prevent unauthorized actions
- **Debuggable** — Replay any run to understand behavior
- **Embeddable** — Use as SDK in your own applications

## Quick Start

```bash
# Install
pip install -e .

# Run all 3 demos in under 5 minutes
make demo
```

That's it. You'll see:
1. **Pipeline Demo** — Data flows through ingest → normalize → analyze → graph → memory → query
2. **Replay Demo** — Previous run is replayed with hash verification
3. **Policy Demo** — Forbidden actions are denied and logged

## Demo Output

```
✅ Pipeline demo complete!
   Run ID: 8fd669f4
   Events: 8
   Artifacts: runs/8fd669f4/

✅ Replay demo complete!
   Deterministic: True
   Events Matched: 8/8

✅ Policy demo complete!
   Denials logged: 2 (system.shell, pii_export)
```

## What's Defensible

| Capability | Why It's Valuable |
|------------|-------------------|
| **Governance Layer** | Configurable policy gates with audit trail — required for enterprise/regulated use |
| **Deterministic Replay** | Reproduce any agent run exactly — critical for debugging and compliance |
| **Event Tracing** | Full provenance chain with payload hashes — enables accountability |
| **Local Memory Graph** | No cloud dependency for memory — data sovereignty and privacy |
| **Typed Event Contract** | Pydantic models for all events — clean SDK integration |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AegisTwin                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────┐  │
│  │ Ingest  │→ │ Pipeline │→ │ Analyze │→ │ Graph/Memory  │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────┘  │
│       ↓            ↓             ↓              ↓           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Event Bus                          │   │
│  │    (typed events + payload hashes + parent chains)    │   │
│  └──────────────────────────────────────────────────────┘   │
│       ↓            ↓             ↓              ↓           │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────────┐  │
│  │ Policy  │  │  Audit   │  │ Replay  │  │     API       │  │
│  │ Engine  │  │  Logger  │  │ Service │  │   (FastAPI)   │  │
│  └─────────┘  └──────────┘  └─────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### As CLI

```bash
# Run demos
aegistwin demo pipeline
aegistwin demo replay
aegistwin demo policy

# Ingest data
aegistwin ingest fixtures/demo_small.json

# Query
aegistwin query "What topics were discussed?"
```

### As SDK

```python
from aegistwin import AegisTwin

twin = AegisTwin()

# Ingest data
run_id = twin.ingest({"records": [...]}, source="my_app")

# Query
result = twin.query("What patterns emerged?")

# Access runtime directly for fine-grained control
from aegistwin import AegisTwinRuntime, PolicyEngine

runtime = AegisTwinRuntime()
runtime.policy_engine.add_policy(my_custom_policy)
```

### As API

```bash
# Start server
make api

# Or directly
uvicorn aegistwin.api:app --reload
```

Endpoints:
- `GET /health` — Health check
- `POST /demo/{name}` — Run a demo
- `POST /ingest` — Ingest data
- `POST /query` — Query the system
- `POST /replay` — Replay a run
- `GET /policies` — List policies

## Project Structure

```
aegistwin/
├── __init__.py          # Main entry point
├── cli.py               # Command-line interface
├── runtime/             # Core runtime engine
├── governance/          # Policy engine + audit
├── events/              # Pydantic event schemas
├── modules/             # Connectors, pipeline, analysis, graph, memory
├── api/                 # FastAPI control plane
└── demos/               # Buyer demos

docs/                    # Documentation
fixtures/                # Synthetic test data
tools/                   # PII scanner, synthetic data generator
tests/                   # Test suite
diligence_pack/          # Acquirer materials
```

## Documentation

- [Architecture](docs/10_ARCHITECTURE.md)
- [Event Schema](docs/02_EVENT_SCHEMA.md)
- [Security & Governance](docs/11_SECURITY_GOVERNANCE.md)
- [Replay & Debugging](docs/12_REPLAY_DEBUGGING.md)
- [Embedding Guide](docs/13_EMBEDDING_GUIDE.md)
- [License & Provenance](docs/14_LICENSE_PROVENANCE.md)

## Requirements

- Python 3.10+
- pydantic >= 2.0
- fastapi >= 0.100
- pyyaml >= 6.0

## License

MIT License — See [LICENSE](LICENSE) for details.

---

**AegisTwin** — *Buyable, not big.*
