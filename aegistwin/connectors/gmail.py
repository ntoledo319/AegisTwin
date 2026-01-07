"""
Gmail Connector

Fetches emails from Gmail using the Gmail API.

@ai_prompt: Requires OAuth2 credentials. Set GOOGLE_APPLICATION_CREDENTIALS env var.
@context_boundary: aegistwin/connectors/gmail
"""

import base64
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

from aegistwin.connectors.base import BaseConnector, ConnectorRecord

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials  # noqa: F401
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


@dataclass
class GmailConfig:
    """Gmail connector configuration."""
    credentials_file: str = "credentials.json"
    token_file: str = "token.json"
    scopes: list[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailConnector(BaseConnector):
    """
    Gmail data source connector.

    Fetches emails from Gmail API and normalizes to ConnectorRecord format.
    """

    def __init__(self, config: GmailConfig | None = None):
        if not HAS_GOOGLE:
            raise RuntimeError(
                "Google API libraries not installed. Install with: "
                "pip install google-auth-oauthlib google-api-python-client"
            )

        self.config = config or GmailConfig()
        self._service = None
        self._credentials = None

    @property
    def name(self) -> str:
        return "gmail"

    async def connect(self) -> None:
        """Establish connection using OAuth2."""
        import os
        import pickle

        creds = None

        if os.path.exists(self.config.token_file):
            with open(self.config.token_file, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_file,
                    self.config.scopes,
                )
                creds = flow.run_local_server(port=0)

            with open(self.config.token_file, "wb") as f:
                pickle.dump(creds, f)

        self._credentials = creds
        self._service = build("gmail", "v1", credentials=creds)

    async def disconnect(self) -> None:
        """Close connection."""
        self._service = None
        self._credentials = None

    async def fetch(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[ConnectorRecord]:
        """Fetch emails from Gmail."""
        if not self._service:
            raise RuntimeError("Not connected")

        query = ""
        if since:
            query = f"after:{int(since.timestamp())}"

        results = self._service.users().messages().list(
            userId="me",
            q=query,
            maxResults=limit,
        ).execute()

        messages = results.get("messages", [])

        for msg_info in messages:
            msg = self._service.users().messages().get(
                userId="me",
                id=msg_info["id"],
                format="full",
            ).execute()

            yield self._parse_message(msg)

    def _parse_message(self, msg: dict) -> ConnectorRecord:
        """Parse Gmail message to ConnectorRecord."""
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        body = ""
        payload = msg.get("payload", {})
        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break

        internal_date = int(msg.get("internalDate", 0)) / 1000
        timestamp = datetime.fromtimestamp(internal_date, tz=timezone.utc)

        return ConnectorRecord(
            source="gmail",
            source_id=msg["id"],
            timestamp=timestamp,
            content_type="email",
            content={
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "body": body[:10000],
                "snippet": msg.get("snippet", ""),
                "labels": msg.get("labelIds", []),
            },
            metadata={
                "thread_id": msg.get("threadId"),
                "size_estimate": msg.get("sizeEstimate"),
            },
        )

    async def health_check(self) -> bool:
        """Check Gmail API connectivity."""
        if not self._service:
            return False
        try:
            self._service.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False
