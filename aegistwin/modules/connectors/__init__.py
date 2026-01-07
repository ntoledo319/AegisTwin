"""
AegisTwin Connectors Module

Adapters for data source connectors from integrated_system.

@ai_prompt: Use connectors to ingest data from various sources.
@context_boundary: aegistwin/modules/connectors

# ORIGINAL_INTENT: Wrap integrated_system/data_processing/connectors
"""

from aegistwin.modules.connectors.base import BaseConnector, ConnectorRegistry

__all__ = ["BaseConnector", "ConnectorRegistry"]
