"""
Slack Connector

Fetches messages from Slack using the Slack API.

@ai_prompt: Requires SLACK_BOT_TOKEN environment variable
@context_boundary: aegistwin/connectors/slack
"""

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

from aegistwin.connectors.base import BaseConnector, ConnectorRecord

try:
    from slack_sdk.web.async_client import AsyncWebClient
    HAS_SLACK = True
except ImportError:
    HAS_SLACK = False


@dataclass
class SlackConfig:
    """Slack connector configuration."""
    token: str | None = None
    channels: list[str] = None

    def __post_init__(self):
        if self.token is None:
            self.token = os.environ.get("SLACK_BOT_TOKEN")
        if self.channels is None:
            self.channels = []


class SlackConnector(BaseConnector):
    """Slack data source connector."""

    def __init__(self, config: SlackConfig | None = None):
        if not HAS_SLACK:
            raise RuntimeError("slack-sdk not installed. Install with: pip install slack-sdk")

        self.config = config or SlackConfig()
        self._client: AsyncWebClient | None = None

    @property
    def name(self) -> str:
        return "slack"

    async def connect(self) -> None:
        """Initialize Slack client."""
        if not self.config.token:
            raise ValueError("Slack token required. Set SLACK_BOT_TOKEN env var.")
        self._client = AsyncWebClient(token=self.config.token)

    async def disconnect(self) -> None:
        """Close client."""
        self._client = None

    async def fetch(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[ConnectorRecord]:
        """Fetch messages from configured channels."""
        if not self._client:
            raise RuntimeError("Not connected")

        channels = self.config.channels
        if not channels:
            result = await self._client.conversations_list(types="public_channel")
            channels = [c["id"] for c in result.get("channels", [])]

        oldest = str(since.timestamp()) if since else None

        for channel_id in channels:
            try:
                result = await self._client.conversations_history(
                    channel=channel_id,
                    oldest=oldest,
                    limit=limit,
                )

                for msg in result.get("messages", []):
                    yield self._parse_message(channel_id, msg)

            except Exception:
                continue

    def _parse_message(self, channel_id: str, msg: dict) -> ConnectorRecord:
        """Parse Slack message to ConnectorRecord."""
        ts = float(msg.get("ts", 0))
        timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)

        return ConnectorRecord(
            source="slack",
            source_id=f"{channel_id}:{msg.get('ts')}",
            timestamp=timestamp,
            content_type="message",
            content={
                "text": msg.get("text", ""),
                "user": msg.get("user", ""),
                "channel": channel_id,
                "thread_ts": msg.get("thread_ts"),
                "reactions": msg.get("reactions", []),
            },
            metadata={
                "type": msg.get("type"),
                "subtype": msg.get("subtype"),
            },
        )

    async def health_check(self) -> bool:
        """Check Slack API connectivity."""
        if not self._client:
            return False
        try:
            await self._client.auth_test()
            return True
        except Exception:
            return False
