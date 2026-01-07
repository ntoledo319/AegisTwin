"""
Storage Base Classes

Abstract interfaces for storage backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class TraceStore(ABC):
    """Abstract base for trace storage."""

    @abstractmethod
    async def save_trace(self, run_id: str, events: list[dict]) -> None:
        """Save event trace for a run."""
        pass

    @abstractmethod
    async def load_trace(self, run_id: str) -> list[dict] | None:
        """Load event trace for a run."""
        pass

    @abstractmethod
    async def list_runs(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List available runs."""
        pass

    @abstractmethod
    async def delete_run(self, run_id: str) -> bool:
        """Delete a run and its trace."""
        pass


class AuditStore(ABC):
    """Abstract base for audit log storage."""

    @abstractmethod
    async def log(
        self,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        metadata: dict | None = None,
    ) -> str:
        """Log an audit entry."""
        pass

    @abstractmethod
    async def query(
        self,
        actor: str | None = None,
        action: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query audit logs."""
        pass
