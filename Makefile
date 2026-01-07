# AegisTwin Makefile
# Event-driven agent runtime + governance + deterministic replay + local memory graph

.PHONY: help install dev demo test lint clean scan api benchmark test-integration docker-build docker-run

# Default target
help:
	@echo "AegisTwin - Make targets:"
	@echo ""
	@echo "  make install    Install package"
	@echo "  make dev        Install with dev dependencies"
	@echo "  make demo       Run all 3 buyer demos"
	@echo "  make test       Run test suite"
	@echo "  make lint       Run linter"
	@echo "  make scan       Run PII scanner"
	@echo "  make api        Start API server"
	@echo "  make clean      Clean build artifacts"
	@echo ""

# Install package
install:
	pip install -e .

# Install with dev dependencies
dev:
	pip install -e ".[dev]"

# Run all demos (the money shot)
demo: install
	@echo "=============================================="
	@echo "AegisTwin - Running All Buyer Demos"
	@echo "=============================================="
	python -m aegistwin.demos.runner

# Run specific demo
demo-pipeline:
	python -c "from aegistwin.demos import run_demo; run_demo('pipeline')"

demo-replay:
	python -c "from aegistwin.demos import run_demo; run_demo('replay')"

demo-policy:
	python -c "from aegistwin.demos import run_demo; run_demo('policy')"

# Run tests
test:
	pytest tests/ -v --cov=aegistwin --cov-report=term-missing

# Quick test (no coverage)
test-quick:
	pytest tests/ -v

# Generate coverage report
coverage:
	pytest tests/ -v --cov=aegistwin --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

# Coverage badge
coverage-badge:
	pytest tests/ -v --cov=aegistwin --cov-report=xml
	@echo "Coverage XML generated for badge generation"

# Run linter
lint:
	ruff check aegistwin/ tests/
	mypy aegistwin/ --ignore-missing-imports

# Format code
format:
	ruff format aegistwin/ tests/

# Run PII scanner
scan:
	python tools/pii_scan.py

# Generate synthetic data
synth:
	python tools/synth_data_gen.py

# Start API server
api:
	uvicorn aegistwin.api:app --reload --host 0.0.0.0 --port 8000

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean runs (demo artifacts)
clean-runs:
	rm -rf runs/

# Full clean
clean-all: clean clean-runs

# Build package
build: clean
	python -m build

# Check before release
check: lint test scan
	@echo "All checks passed!"

# Generate documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs
	@echo "Documentation generation would go here"

# Run benchmarks
benchmark:
	python -m benchmarks.run_benchmarks

# Run integration tests
test-integration:
	pytest tests/integration -v

# Docker targets
docker-build:
	cd docker && docker build -t aegistwin:latest -f Dockerfile ..

docker-run:
	docker run -p 8000:8000 aegistwin:latest

docker-compose-up:
	cd docker && docker-compose up --build

docker-compose-down:
	cd docker && docker-compose down

# Helm targets
helm-install:
	helm install aegistwin ./docker/helm/aegistwin

helm-upgrade:
	helm upgrade aegistwin ./docker/helm/aegistwin

helm-uninstall:
	helm uninstall aegistwin
