"""
AegisTwin Connectors Module

Data source connectors for ingestion.
"""

from aegistwin.connectors.base import BaseConnector
from aegistwin.connectors.gmail import GmailConnector
from aegistwin.connectors.slack import SlackConnector
from aegistwin.connectors.webhook import WebhookConnector

__all__ = [
    "BaseConnector",
    "GmailConnector",
    "SlackConnector",
    "WebhookConnector",
]
