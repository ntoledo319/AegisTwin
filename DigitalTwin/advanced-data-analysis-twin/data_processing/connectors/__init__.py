"""
Data connectors for the Advanced Data Analysis & Digital Twin System.
"""

from typing import Dict, Type

from .base import DataConnectorBase
from .email import EmailConnector
from .messaging import MessagingConnector
from .social import SocialMediaConnector
from .productivity import ProductivityConnector

# Register all connectors here
CONNECTOR_REGISTRY: Dict[str, Type[DataConnectorBase]] = {
    "email": EmailConnector,
    "messaging": MessagingConnector,
    "social": SocialMediaConnector,
    "productivity": ProductivityConnector,
}

def get_connector_class(connector_type: str) -> Type[DataConnectorBase]:
    """
    Get connector class by type.
    
    Args:
        connector_type: Type of connector
        
    Returns:
        Connector class
        
    Raises:
        ValueError: If connector type is not found
    """
    if connector_type not in CONNECTOR_REGISTRY:
        raise ValueError(f"Connector type not found: {connector_type}")
    
    return CONNECTOR_REGISTRY[connector_type]

def get_available_connectors() -> Dict[str, str]:
    """
    Get a dictionary of available connector types and their descriptions.
    
    Returns:
        Dictionary mapping connector types to descriptions
    """
    return {
        "email": "Connector for extracting data from email accounts using IMAP",
        "messaging": "Connector for extracting data from messaging platforms (WhatsApp, Telegram, Signal, SMS)",
        "social": "Connector for extracting data from social media platforms (Twitter, Facebook, LinkedIn, Instagram, Reddit)",
        "productivity": "Connector for extracting data from productivity tools (Google Workspace, Microsoft 365, Calendar, Documents)",
    }

__all__ = [
    "DataConnectorBase",
    "EmailConnector",
    "MessagingConnector",
    "SocialMediaConnector",
    "ProductivityConnector",
    "get_connector_class",
    "get_available_connectors",
    "CONNECTOR_REGISTRY",
]