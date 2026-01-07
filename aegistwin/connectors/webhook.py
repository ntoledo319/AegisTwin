"""
Webhook Connector

Generic webhook receiver for real-time data ingestion.

@ai_prompt: Mount WebhookConnector.router on FastAPI app
@context_boundary: aegistwin/connectors/webhook
"""

import asyncio
import hashlib
import hmac
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from aegistwin.connectors.base import BaseConnector, ConnectorRecord


class WebhookPayload(BaseModel):
    """Generic webhook payload."""
    source: str
    event_type: str
    data: dict[str, Any]
    timestamp: str | None = None


@dataclass
class WebhookConfig:
    """Webhook connector configuration."""
    secret: str | None = None
    max_queue_size: int = 1000
    allowed_sources: list[str] = field(default_factory=list)


class WebhookConnector(BaseConnector):
    """
    Webhook receiver connector.

    Provides a FastAPI router for receiving webhooks.
    """

    def __init__(self, config: WebhookConfig | None = None):
        self.config = config or WebhookConfig()
        self._queue: asyncio.Queue[ConnectorRecord] = asyncio.Queue(maxsize=self.config.max_queue_size)
        self._handlers: list[Callable[[ConnectorRecord], None]] = []
        self._running = False

        self.router = APIRouter(prefix="/webhooks", tags=["webhooks"])
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure webhook routes."""

        @self.router.post("/ingest")
        async def receive_webhook(
            payload: WebhookPayload,
            request: Request,
            x_webhook_signature: str | None = Header(None),
        ):
            if self.config.secret:
                if not x_webhook_signature:
                    raise HTTPException(401, "Signature required")

                body = await request.body()
                expected = hmac.new(
                    self.config.secret.encode(),
                    body,
                    hashlib.sha256,
                ).hexdigest()

                if not hmac.compare_digest(f"sha256={expected}", x_webhook_signature):
                    raise HTTPException(401, "Invalid signature")

            if self.config.allowed_sources and payload.source not in self.config.allowed_sources:
                raise HTTPException(403, f"Source '{payload.source}' not allowed")

            record = ConnectorRecord(
                source=f"webhook:{payload.source}",
                source_id=hashlib.sha256(str(payload.data).encode()).hexdigest()[:16],
                timestamp=datetime.fromisoformat(payload.timestamp) if payload.timestamp else datetime.now(timezone.utc),
                content_type=payload.event_type,
                content=payload.data,
                metadata={"source": payload.source},
            )

            try:
                self._queue.put_nowait(record)
            except asyncio.QueueFull:
                raise HTTPException(503, "Queue full") from None

            for handler in self._handlers:
                try:
                    handler(record)
                except Exception:
                    pass

            return {"status": "accepted", "id": record.source_id}

        @self.router.get("/health")
        async def webhook_health():
            return {
                "status": "healthy",
                "queue_size": self._queue.qsize(),
                "max_queue_size": self.config.max_queue_size,
            }

    @property
    def name(self) -> str:
        return "webhook"

    async def connect(self) -> None:
        """Start webhook receiver."""
        self._running = True

    async def disconnect(self) -> None:
        """Stop webhook receiver."""
        self._running = False

    async def fetch(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[ConnectorRecord]:
        """Yield queued webhook records."""
        count = 0
        while count < limit:
            try:
                record = self._queue.get_nowait()
                if since and record.timestamp < since:
                    continue
                yield record
                count += 1
            except asyncio.QueueEmpty:
                break

    async def health_check(self) -> bool:
        """Check if webhook receiver is running."""
        return self._running

    def on_receive(self, handler: Callable[[ConnectorRecord], None]) -> None:
        """Register handler for received webhooks."""
        self._handlers.append(handler)
