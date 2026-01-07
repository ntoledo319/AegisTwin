# CogniLink Tests

This directory contains tests for the CogniLink application. The tests are organized into unit tests and integration tests.

## Test Structure

- `unit/`: Contains unit tests for individual components
  - `test_connectors.py`: Tests for data connectors
  - `test_processors.py`: Tests for data processors
  - `test_patterns.py`: Tests for communication pattern analysis
  - `test_relationships.py`: Tests for relationship analysis
  - `test_topics.py`: Tests for topic analysis
- `integration/`: Contains integration tests for component interactions
  - `test_pipeline_integration.py`: Tests for connector-processor pipeline
  - `test_analysis_integration.py`: Tests for processor-analyzer pipeline
  - `test_interface_integration.py`: Tests for interface components
- `conftest.py`: Contains pytest fixtures shared across tests
- `pytest.ini`: Configuration for pytest

## Running Tests

### Prerequisites

Ensure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Test Categories

To run only unit tests:

```bash
pytest cognilink/tests/unit/
```

To run only integration tests:

```bash
pytest cognilink/tests/integration/
```

To run a specific test file:

```bash
pytest cognilink/tests/unit/test_connectors.py
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=cognilink
```

To generate an HTML coverage report:

```bash
pytest --cov=cognilink --cov-report=html
```

This will create a `htmlcov` directory with the coverage report.

## Test Data

The tests use fixtures defined in `conftest.py` to create sample data for testing. This includes:

- Sample configuration
- Sample email data
- Sample message data
- Temporary directories and files

## Adding New Tests

When adding new tests:

1. For unit tests, create a new file in the `unit/` directory following the naming convention `test_*.py`
2. For integration tests, create a new file in the `integration/` directory
3. Use the fixtures defined in `conftest.py` where appropriate
4. Follow the existing test structure and patterns

## Test Markers

The following markers are available for tests:

- `@pytest.mark.unit`: Marks tests as unit tests
- `@pytest.mark.integration`: Marks tests as integration tests
- `@pytest.mark.slow`: Marks tests as slow (skipped by default)

To run tests with a specific marker:

```bash
pytest -m unit
```