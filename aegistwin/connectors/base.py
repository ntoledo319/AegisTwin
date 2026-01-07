"""
Base Connector Interface

Abstract interface for data source connectors.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConnectorRecord:
    """Standardized record from connector."""
    source: str
    source_id: str
    timestamp: datetime
    content_type: str
    content: dict[str, Any]
    metadata: dict[str, Any]


class BaseConnector(ABC):
    """Abstract base class for data source connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data source."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    async def fetch(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[ConnectorRecord]:
        """
        Fetch records from data source.

        Args:
            since: Only fetch records after this timestamp
            limit: Maximum records to fetch

        Yields:
            ConnectorRecord for each fetched item
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        pass
