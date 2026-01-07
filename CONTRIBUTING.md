# Contributing to AegisTwin

Thank you for your interest in contributing to AegisTwin!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/aegistwin/aegistwin.git
cd aegistwin

# Install with dev dependencies
make dev

# Verify installation
make test
```

## Development Workflow

### 1. Code Style

We use automated tools to maintain code quality:

```bash
# Format code
make format

# Run linter
make lint

# Type checking is enforced via mypy
```

**Standards:**
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Add docstrings to all public functions and classes
- Keep functions focused and under 50 lines when possible

### 2. Testing

All contributions must include tests:

```bash
# Run tests
make test

# Run tests with coverage
make coverage

# Quick test (no coverage)
make test-quick
```

**Testing Requirements:**
- Minimum 80% code coverage for new code
- Unit tests for all new functions
- Integration tests for new modules
- Use synthetic fixtures (never real PII)

### 3. Documentation

Update documentation for all changes:

- Add docstrings using Google style
- Update relevant `.md` files in `docs/`
- Add usage examples when introducing new features
- Update `CHANGELOG.md` with your changes

### 4. Privacy & Security

**CRITICAL: No PII in the codebase**

```bash
# Run PII scanner before committing
make scan
```

- Use synthetic data from `fixtures/`
- Never commit real names, emails, phone numbers
- All demo data must be clearly fictional
- Run `tools/pii_scan.py` before every commit

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, well-documented code
- Add tests for new functionality
- Update documentation as needed

### 3. Run Validation

```bash
# Run all checks
make check

# This runs: lint, test, scan
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: Add feature description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, no logic change)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Open a pull request with:
- Clear description of changes
- Link to related issues
- Screenshots/demos if applicable
- Test results

## Code Review

All submissions require code review:

1. **Automated Checks** — CI must pass (lint, test, demo, PII scan)
2. **Manual Review** — Maintainer reviews code quality and design
3. **Testing** — New features must include tests
4. **Documentation** — Updates must include docs

## Project Structure

```
aegistwin/
├── __init__.py          # Main entry point
├── cli.py               # Command-line interface
├── runtime/             # Core runtime engine
├── governance/          # Policy engine + audit
├── events/              # Pydantic event schemas
├── modules/             # Connectors, pipeline, analysis, graph, memory
└── api/                 # FastAPI control plane

docs/                    # Documentation
fixtures/                # Synthetic test data
tools/                   # PII scanner, synthetic data generator
tests/                   # Test suite
examples/                # Usage examples
```

## Adding New Modules

To add a new module to `aegistwin/modules/`:

1. Create module directory with `__init__.py`
2. Define module interface (input/output events)
3. Implement core logic
4. Add unit tests in `tests/`
5. Add integration test with event bus
6. Document in `docs/10_ARCHITECTURE.md`
7. Add example in `examples/`

## Adding New Events

To add new event types:

1. Define in `aegistwin/events/schema.py` using Pydantic
2. Add to `EventType` enum
3. Update event bus handlers if needed
4. Add tests in `tests/test_events.py`
5. Document in `docs/02_EVENT_SCHEMA.md`

## Adding New Policies

To add new policy types:

1. Define policy in `aegistwin/governance/policy.py`
2. Add policy tests
3. Add demo in `aegistwin/demos/`
4. Document in `docs/11_SECURITY_GOVERNANCE.md`

## Questions?

- Check existing issues: https://github.com/aegistwin/aegistwin/issues
- Review documentation: `docs/`
- Run demos: `make demo`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
