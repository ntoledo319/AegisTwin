# Changelog

All notable changes to AegisTwin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-06

### Added
- Initial release of AegisTwin productized agent runtime
- Event-driven architecture with typed Pydantic events
- Governance layer with configurable policy engine
- Deterministic replay capabilities for debugging
- Local memory graph (episodic, semantic, procedural)
- FastAPI REST API with OpenAPI documentation
- CLI interface with `aegistwin` command
- Three demonstration scenarios (pipeline, replay, policy)
- Comprehensive test suite with pytest
- PII scanner for data privacy verification
- Synthetic data generator for testing
- Complete documentation suite
- GitHub Actions CI pipeline (lint, test, demo, pii-scan)
- Examples directory with SDK usage patterns
- Diligence pack for acquisition (one-pager, SBOM, PII purge report)

### Architecture
- Core runtime engine (`aegistwin/runtime/`)
- Policy enforcement (`aegistwin/governance/`)
- Event schemas (`aegistwin/events/`)
- Module system (`aegistwin/modules/`)
  - Connectors (email, calendar, messages, social)
  - Pipeline (normalization, validation)
  - Analysis (cognitive, communication)
  - Graph (knowledge graph operations)
  - Memory (episodic, semantic, procedural)
- API control plane (`aegistwin/api/`)
- CLI interface (`aegistwin/cli.py`)

### Dependencies
- Python 3.10+
- pydantic >= 2.0
- fastapi >= 0.100
- uvicorn >= 0.22
- pyyaml >= 6.0

### License
- MIT License
- All dependencies use permissive licenses (MIT, BSD, Apache-2.0)

---

## [0.2.0] - 2026-01-07

### Added - Value Enhancement Release

#### Phase 1: Performance Benchmarks
- New `benchmarks/` package with comprehensive performance testing
- Event bus throughput benchmarks (1K, 10K, 100K events)
- Policy engine latency benchmarks with varying policy counts
- Replay verification speed benchmarks
- Memory footprint analysis
- `make benchmark` target for running all benchmarks
- JSON and Markdown output for benchmark results

#### Phase 2: OpenTelemetry Tracing
- New `aegistwin/observability/` module
- Distributed tracing with OpenTelemetry SDK
- Support for OTLP, console, and Jaeger exporters
- Prometheus metrics collection
- `@trace_event` decorator for automatic span creation
- Trace context propagation for distributed systems
- `/metrics` endpoint for Prometheus scraping

#### Phase 3: Async EventBus
- New `AsyncEventBus` for non-blocking event processing
- New `AsyncAegisTwinRuntime` for async applications
- `asyncio.Queue` based event buffering
- Background dispatch task for event distribution
- Concurrent query execution support
- `examples/05_async_usage.py` demonstration

#### Phase 4: LLM Integration
- New `aegistwin/modules/llm/` package
- Abstract `LLMProvider` interface
- `OpenAIProvider` and `AnthropicProvider` implementations
- `MockProvider` for testing without API keys
- `LLMRequestEvent` and `LLMResponseEvent` for audit trails
- Policy-gated LLM access with audit logging
- `examples/04_llm_integration.py` demonstration

#### Phase 5: WebSocket Event Stream
- Real-time event streaming via WebSocket
- `ConnectionManager` for multi-client broadcasting
- Event type and run ID filtering
- `/ws/events` and `/ws/events/{run_id}` endpoints
- `examples/06_websocket_client.py` client example

#### Phase 6: OPA/Rego Policy Integration
- New `aegistwin/governance/opa.py` module
- `OPAEvaluator` for Open Policy Agent integration
- External OPA server support via HTTP API
- Embedded Rego evaluation via CLI
- Default Rego policy in `aegistwin/governance/policies/`
- `examples/07_opa_policies.py` demonstration

#### Phase 7: Docker + Helm
- Production `Dockerfile` with multi-stage build
- Development `Dockerfile.dev` with hot reload
- `docker-compose.yml` with full observability stack
- Helm chart for Kubernetes deployment
- ConfigMap, Service, Deployment, Ingress templates
- Non-root container execution
- Health check probes

#### Phase 8: Integration Tests
- New `tests/integration/` test suite
- End-to-end pipeline tests
- Replay determinism verification
- Policy enforcement tests
- API endpoint tests
- Shared fixtures for consistent testing

#### Phase 9: Plugin Architecture
- New `aegistwin/plugins/` package
- `AegisTwinPlugin` protocol for extensibility
- `ConnectorPlugin`, `AnalyzerPlugin`, `PolicyPlugin` base classes
- `PluginRegistry` for plugin management
- Entry point discovery for installed plugins
- `examples/08_custom_plugin.py` demonstration

#### Phase 10: Metrics Dashboard
- Grafana dashboard for operational visibility
- Prometheus configuration for metric scraping
- Panels: Events/sec, Policy checks, Latency, Active runs
- Auto-provisioning for dashboards and datasources
- `observability/README.md` documentation

#### Phase 11: Enterprise Security
- New `aegistwin/security/` module
- JWT authentication with configurable expiry
- Role-Based Access Control (RBAC) system  
- AES-256-GCM encryption at rest
- Security middleware with rate limiting
- Redis-backed scalable event bus
- PostgreSQL storage backend

#### Phase 12: Enterprise Dashboard
- React + TypeScript admin dashboard
- Real-time event timeline with WebSocket
- Policy rule editor with CRUD operations
- System health monitoring
- Audit log viewer with filtering
- Run management and detail views

#### Phase 13: Agent Evaluation Framework
- New `aegistwin/evaluation/` package
- `EvaluationHarness` for systematic agent testing
- `BenchmarkSuite` with built-in test suites (safety, policy, replay, performance)
- `MetricsCollector` for evaluation metrics
- `ReportGenerator` for Markdown/JSON reports

#### Phase 14: Semantic Memory
- `VectorStore` with sentence-transformer embeddings
- Cosine similarity search
- `SemanticMemory` high-level interface
- Memory consolidation and importance scoring
- Persistence support

#### Phase 15: Framework Integrations
- LangChain integration (`AegisTwinCallbackHandler`)
- CrewAI integration (`AegisTwinCrewObserver`)
- AutoGen integration (`AegisTwinAutoGenMonitor`)
- Policy enforcement across all frameworks

#### Phase 16: TypeScript SDK
- Full type-safe client (`@aegistwin/sdk`)
- WebSocket event streaming
- All API endpoints covered
- npm package ready for publishing

#### Phase 17: Compliance Documentation
- SOC2 compliance mapping
- HIPAA considerations guide
- GDPR compliance documentation

### Changed
- `pyproject.toml` now includes `httpx` as core dependency
- `pyproject.toml` adds `[observability]` optional dependencies
- `PolicyEngine` now supports OPA evaluator integration
- `Makefile` extended with benchmark, docker, and helm targets
- API now includes WebSocket and metrics endpoints

### Documentation
- `docs/15_OBSERVABILITY.md` - Tracing and metrics guide
- `docs/16_PLUGINS.md` - Plugin development guide
- `benchmarks/README.md` - Benchmark usage guide
- `observability/README.md` - Observability stack guide
- Helm chart `README.md` - Kubernetes deployment guide

---

## [Unreleased]

### Planned
- Enhanced graph visualization
- Additional memory backends (PostgreSQL, Redis)
- Multi-agent coordination
- Advanced replay comparison tools

---

**Note:** This is the baseline release prepared for acquisition. All PII has been quarantined and synthetic fixtures are used throughout.
