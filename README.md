# AegisTwin

**Event-driven agent runtime + governance + deterministic replay + local memory graph.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 94 passing](https://img.shields.io/badge/tests-94%20passing-brightgreen)](./tests)
[![Benchmarks: published](https://img.shields.io/badge/benchmarks-published-orange)](./BENCHMARKS.md)

> 📦 **The full production package** (brand assets, sales materials, IP transfer, exclusive license) is available at **[toledotechnologies.com/codebases/aegistwin](https://toledotechnologies.com/codebases/aegistwin)**.
>
> This public repo is the source for evaluation and community contributions. The paid package is for buyers who want to ship AegisTwin commercially under their own brand with a clean IP transfer.

---

## Why this exists in public

We're publishing the source so technical buyers can verify what they're getting — read the code, run the [benchmarks](./BENCHMARKS.md), check the [comparison](./COMPARISON.md) vs LangChain/AutoGen/CrewAI — before they commit to the production package.

If you're a developer who finds this useful for personal or research use, take it (MIT). If you're a company shipping it commercially and want IP transfer + exclusive rights, that's the paid path.

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

### Docker Quickstart

```bash
# Build and run with Docker Compose (includes Grafana, Prometheus, Jaeger)
cd docker
docker-compose up --build

# Test the API
curl http://localhost:8000/health

# Access services:
# - AegisTwin API: http://localhost:8000
# - Grafana Dashboard: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - Jaeger Tracing: http://localhost:16686
```

### Kubernetes Deployment

```bash
# Deploy with Helm
helm install aegistwin ./docker/helm/aegistwin

# Check status
kubectl get pods -l app.kubernetes.io/name=aegistwin
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

**Interactive API Documentation:**
- OpenAPI/Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Endpoints:**
- `GET /health` — Health check
- `POST /demo/{name}` — Run a demo
- `POST /ingest` — Ingest data
- `POST /query` — Query the system
- `POST /replay` — Replay a run
- `GET /policies` — List policies

## Project Structure

```
aegistwin/               # Main package (production-ready)
├── __init__.py          # Main entry point
├── cli.py               # Command-line interface
├── api/                 # FastAPI control plane
├── connectors/          # Data source connectors
├── demos/               # Buyer demos
├── evaluation/          # Agent evaluation framework
├── events/              # Pydantic event schemas
├── governance/          # Policy engine + audit
├── integrations/        # LangChain, CrewAI, AutoGen integrations
├── modules/             # Pipeline, analysis, graph, memory, LLM
├── observability/       # OpenTelemetry tracing + metrics
├── plugins/             # Plugin architecture
├── runtime/             # Core runtime engine
├── security/            # Auth, RBAC, encryption
└── storage/             # PostgreSQL, Redis backends

docs/                    # Documentation
fixtures/                # Synthetic test data
tools/                   # PII scanner, synthetic data generator
tests/                   # Test suite
examples/                # Usage examples
benchmarks/              # Performance benchmarks
observability/           # Grafana + Prometheus configs
docker/                  # Docker + Helm deployment
diligence_pack/          # Acquirer materials
```

## Documentation

- [Architecture](docs/10_ARCHITECTURE.md)
- [Event Schema](docs/02_EVENT_SCHEMA.md)
- [Security & Governance](docs/11_SECURITY_GOVERNANCE.md)
- [Replay & Debugging](docs/12_REPLAY_DEBUGGING.md)
- [Embedding Guide](docs/13_EMBEDDING_GUIDE.md)
- [License & Provenance](docs/14_LICENSE_PROVENANCE.md)
- [Observability & Tracing](docs/15_OBSERVABILITY.md)
- [Plugin Development](docs/16_PLUGINS.md)

## Requirements

- Python 3.10+
- pydantic >= 2.0
- fastapi >= 0.100
- pyyaml >= 6.0

## License

MIT License — See [LICENSE](LICENSE) for details.

---

**AegisTwin** — *Buyable, not big.*
