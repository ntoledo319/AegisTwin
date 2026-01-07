# SpiderMind Omega Makefile

.PHONY: all setup install install-dev run clean test lint format help docker docker-run docker-build docker-clean

# Default target
all: help

# Configuration
PYTHON := python3
PIP := pip
VENV := .venv
CONFIG := config/config.yaml
DOCKER_IMAGE := spidermind-omega
DOCKER_TAG := latest
DATA_DIR := data

# Help message
help:
	@echo "SpiderMind Omega - Personal Digital Twin"
	@echo ""
	@echo "Usage:"
	@echo "  make setup         Create virtual environment and install dependencies"
	@echo "  make install       Install the package"
	@echo "  make install-dev   Install the package in development mode"
	@echo "  make run           Run the SpiderMind Omega pipeline"
	@echo "  make run-api       Run the API server"
	@echo "  make run-dashboard Run the dashboard"
	@echo "  make clean         Remove build artifacts and cache files"
	@echo "  make test          Run tests"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code"
	@echo "  make docker        Build and run Docker container"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run Docker container"
	@echo "  make docker-clean  Remove Docker image"
	@echo ""
	@echo "Environment variables:"
	@echo "  CONFIG             Path to configuration file (default: $(CONFIG))"
	@echo "  DATA_DIR           Path to data directory (default: $(DATA_DIR))"
	@echo ""

# Setup virtual environment and install dependencies
setup:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing dependencies..."
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e .
	@echo "Installing spaCy model..."
	$(VENV)/bin/python -m spacy download en_core_web_sm
	@echo "Setup complete. Activate the virtual environment with: source $(VENV)/bin/activate"

# Install the package
install:
	$(PIP) install .

# Install the package in development mode
install-dev:
	$(PIP) install -e ".[dev]"

# Run the SpiderMind Omega pipeline
run:
	$(PYTHON) -m spidermind.cli run --all --config $(CONFIG)

# Run specific pipeline steps
run-ingest:
	$(PYTHON) -m spidermind.cli run --steps ingest --config $(CONFIG)

run-preprocess:
	$(PYTHON) -m spidermind.cli run --steps preprocess --config $(CONFIG)

run-analyze:
	$(PYTHON) -m spidermind.cli run --steps analyze --config $(CONFIG)

run-model:
	$(PYTHON) -m spidermind.cli run --steps model --config $(CONFIG)

run-export:
	$(PYTHON) -m spidermind.cli run --steps export --config $(CONFIG)

# Run the API server
run-api:
	$(PYTHON) -m spidermind.cli serve --port 8000 --config $(CONFIG)

# Run the dashboard
run-dashboard:
	$(PYTHON) -m spidermind.cli serve --dashboard-port 8050 --config $(CONFIG)

# Clean build artifacts and cache files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type f -name "*.bak" -delete
	find . -type f -name "*.swp" -delete
	find . -type f -name "*.swo" -delete
	find . -type f -name "*.~" -delete
	find . -type f -name "*.orig" -delete
	find . -type f -name "*.rej" -delete

# Run tests
test:
	pytest

# Run linters
lint:
	flake8 src tests
	mypy src tests
	black --check src tests
	isort --check-only src tests

# Format code
format:
	black src tests
	isort src tests

# Docker commands
docker: docker-build docker-run

# Build Docker image
docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run Docker container
docker-run:
	docker run --rm -it \
		-v "$(PWD)/$(DATA_DIR):/app/$(DATA_DIR)" \
		-v "$(PWD)/$(CONFIG):/app/$(CONFIG)" \
		-p 8000:8000 \
		-p 8050:8050 \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		run --all --config $(CONFIG)

# Run Docker container with interactive shell
docker-shell:
	docker run --rm -it \
		-v "$(PWD)/$(DATA_DIR):/app/$(DATA_DIR)" \
		-v "$(PWD)/$(CONFIG):/app/$(CONFIG)" \
		-p 8000:8000 \
		-p 8050:8050 \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		/bin/bash

# Clean Docker image
docker-clean:
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG)

# Create directory structure
create-dirs:
	mkdir -p $(DATA_DIR)/raw
	mkdir -p $(DATA_DIR)/interim
	mkdir -p $(DATA_DIR)/processed
	mkdir -p $(DATA_DIR)/models
	mkdir -p config
	mkdir -p logs
	mkdir -p exports

# Initialize project
init: create-dirs
	@echo "Project initialized. Please add your data files to $(DATA_DIR)/raw directory."