"""
Data processing module for the Advanced Data Analysis & Digital Twin System.
"""

from typing import Dict, Any, Optional

from .pipeline import DataPipeline
from .connectors import (
    DataConnectorBase,
    EmailConnector,
    MessagingConnector,
    SocialMediaConnector,
    ProductivityConnector,
    get_connector_class,
    get_available_connectors,
    CONNECTOR_REGISTRY,
)
from .processors import (
    TextProcessor,
    EntityProcessor,
    NormalizationProcessor,
    get_processor_class,
    get_available_processors,
    create_processor,
    PROCESSOR_REGISTRY,
)

async def create_pipeline(config: Optional[Dict[str, Any]] = None) -> DataPipeline:
    """
    Create and initialize a data pipeline.
    
    Args:
        config: Pipeline configuration
        
    Returns:
        Initialized DataPipeline instance
    """
    pipeline = DataPipeline(config)
    await pipeline.initialize()
    return pipeline

__all__ = [
    "DataPipeline",
    "create_pipeline",
    "DataConnectorBase",
    "EmailConnector",
    "MessagingConnector",
    "SocialMediaConnector",
    "ProductivityConnector",
    "get_connector_class",
    "get_available_connectors",
    "CONNECTOR_REGISTRY",
    "TextProcessor",
    "EntityProcessor",
    "NormalizationProcessor",
    "get_processor_class",
    "get_available_processors",
    "create_processor",
    "PROCESSOR_REGISTRY",
]