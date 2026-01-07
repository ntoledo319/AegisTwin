"""
Integration Test Fixtures

Shared fixtures for integration tests.

@ai_prompt: Import fixtures from conftest in your integration tests.
@context_boundary: tests/integration/conftest

# AI-GENERATED 2026-01-07
"""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.runtime.async_core import AsyncAegisTwinRuntime
from aegistwin.api.main import create_app


@pytest.fixture
def temp_runs_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test runs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def runtime(temp_runs_dir: Path) -> AegisTwinRuntime:
    """Create a fresh AegisTwinRuntime with temp directory."""
    runtime = AegisTwinRuntime()
    runtime._runs_dir = temp_runs_dir
    return runtime


@pytest.fixture
def async_runtime(temp_runs_dir: Path) -> AsyncAegisTwinRuntime:
    """Create a fresh AsyncAegisTwinRuntime with temp directory."""
    runtime = AsyncAegisTwinRuntime()
    runtime._runs_dir = temp_runs_dir
    return runtime


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient for FastAPI."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_data() -> dict:
    """Load sample data for testing."""
    return {
        "records": [
            {"id": 1, "type": "email", "subject": "Test Email 1"},
            {"id": 2, "type": "email", "subject": "Test Email 2"},
            {"id": 3, "type": "calendar", "title": "Test Event"},
        ],
        "type": "mixed",
    }


@pytest.fixture
def sample_emails() -> dict:
    """Load sample email data."""
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    emails_file = fixtures_dir / "emails.json"
    
    if emails_file.exists():
        with open(emails_file) as f:
            return json.load(f)
    
    # Fallback sample data
    return {
        "records": [
            {
                "id": "email-1",
                "from": "alice@example.com",
                "to": "bob@example.com",
                "subject": "Project Update",
                "body": "Here's the latest update on the project.",
                "timestamp": "2026-01-07T10:00:00Z",
            },
            {
                "id": "email-2",
                "from": "bob@example.com",
                "to": "alice@example.com",
                "subject": "Re: Project Update",
                "body": "Thanks for the update!",
                "timestamp": "2026-01-07T10:30:00Z",
            },
        ],
        "type": "email",
    }


@pytest.fixture
def sample_calendar() -> dict:
    """Load sample calendar data."""
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    calendar_file = fixtures_dir / "calendar_events.json"
    
    if calendar_file.exists():
        with open(calendar_file) as f:
            return json.load(f)
    
    # Fallback sample data
    return {
        "records": [
            {
                "id": "event-1",
                "title": "Team Meeting",
                "start": "2026-01-07T14:00:00Z",
                "end": "2026-01-07T15:00:00Z",
                "attendees": ["alice", "bob", "charlie"],
            },
        ],
        "type": "calendar",
    }


@pytest.fixture
def large_dataset() -> dict:
    """Generate a large dataset for stress testing."""
    return {
        "records": [
            {"id": i, "type": "test", "value": f"item-{i}"}
            for i in range(1000)
        ],
        "type": "bulk",
    }
