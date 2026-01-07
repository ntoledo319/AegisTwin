"""
Pytest configuration and fixtures for HydraMind tests.

This module provides common test fixtures and configuration
for running HydraMind tests.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from hydramind.core.bus import EventBus
from hydramind.core.execs import Exec, ResourceManager
from hydramind.core.policy import PolicyGuard
from hydramind.core.event_store import EventStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def event_store(temp_dir: Path) -> EventStore:
    """Create a test event store."""
    db_path = temp_dir / "test_events.db"
    return EventStore(str(db_path))


@pytest.fixture
def event_bus(event_store: EventStore) -> EventBus:
    """Create a test event bus."""
    return EventBus(event_store)


@pytest.fixture
def exec_engine() -> Exec:
    """Create a test execution engine."""
    hint = ResourceManager().recommend()
    return Exec(hint)


@pytest.fixture
def policy_guard() -> PolicyGuard:
    """Create a test policy guard."""
    return PolicyGuard(None, 1000)  # No allowlist, 1000 events/sec


@pytest.fixture
def sample_config():
    """Sample configuration for tests."""
    return {
        'ring_capacity': 2048,
        'ring_item_bytes': 1024,
        'max_events_per_sec': 1000,
        'snapshot_dir': '/tmp/test_snapshots',
        'logging': {
            'level': 'INFO',
            'json': True
        }
    }


@pytest.fixture(autouse=True)
def cleanup_tasks():
    """Automatically cleanup any remaining tasks after each test."""
    yield
    try:
        # Cancel all remaining tasks
        loop = asyncio.get_running_loop()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            if not task.done():
                task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except RuntimeError:
        # No running event loop, skip cleanup
        pass
