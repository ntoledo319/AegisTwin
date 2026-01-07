# AegisTwin — Acquirer One-Pager

## What It Is

**AegisTwin** is a productized agent runtime that provides event-driven orchestration, governance, deterministic replay, and local memory graph capabilities.

**Tagline:** *Event-driven agent runtime + governance + deterministic replay + local memory graph.*

---

## The Problem

AI agents are increasingly deployed in production, but lack critical infrastructure:

- **No Governance** — Agents can perform unauthorized actions
- **No Auditability** — Can't explain or prove what happened
- **No Reproducibility** — Can't replay decisions for debugging
- **Cloud Lock-in** — Memory/context tied to external services

---

## The Solution

AegisTwin provides the missing infrastructure layer:

| Capability | Value |
|------------|-------|
| **Policy Gates** | Deny forbidden actions before they execute |
| **Audit Trail** | Every action logged with actor/resource/outcome |
| **Deterministic Replay** | Reproduce any run exactly |
| **Local Memory Graph** | No cloud dependency for agent memory |
| **Typed Events** | Clean SDK integration with Pydantic |

---

## Demo in 5 Minutes

```bash
git clone <repo>
cd aegistwin
pip install -e .
make demo
```

Three demos run automatically:
1. **Pipeline** — Full data flow with tracing
2. **Replay** — Deterministic reproduction
3. **Policy** — Access control with audit

---

## Technical Highlights

- **Python 3.10+** with modern typing
- **Pydantic v2** for event schemas
- **FastAPI** for REST API
- **Zero external dependencies** for core functionality
- **Pluggable architecture** for extensions

---

## What's Defensible

1. **Governance Layer** — Configurable policies with audit trail (required for enterprise)
2. **Replay Infrastructure** — Payload hashes enable exact reproduction
3. **Event Contract** — Typed events make integration predictable
4. **Local-First Memory** — No cloud dependency, data sovereignty

---

## Code Quality

- ✅ PII scanner prevents data leakage
- ✅ Synthetic fixtures for all demos
- ✅ CI pipeline (lint, test, demo smoke)
- ✅ Comprehensive documentation
- ✅ MIT license, permissive dependencies

---

## Integration Paths

| Path | Effort | Description |
|------|--------|-------------|
| **CLI** | Minutes | Run demos, ingest files |
| **SDK** | Hours | Embed in Python applications |
| **API** | Hours | REST endpoints for any language |
| **Full** | Days | Custom connectors, policies, events |

---

## Target Buyers

1. **Enterprise AI Teams** — Governance + audit requirements
2. **Security Vendors** — Agent monitoring and control
3. **MLOps Platforms** — Reproducibility infrastructure
4. **Consulting Firms** — Deployable agent framework
5. **Regulated Industries** — Compliance-ready agent runtime

---

## What's Included

```
aegistwin/           # Core package (runtime, governance, events, API)
docs/                # Architecture, security, embedding guides
fixtures/            # Synthetic demo data
tools/               # PII scanner, data generator
tests/               # Test suite
diligence_pack/      # This document, SBOM, PII report
```

---

## Contact

**For acquisition inquiries, technical due diligence, or demo walkthrough:**

- **Email:** contact@aegistwin.com
- **Repository:** https://github.com/aegistwin/aegistwin
- **Documentation:** https://github.com/aegistwin/aegistwin#readme

---

*AegisTwin — Buyable, not big.*
