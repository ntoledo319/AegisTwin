"""
Base Connector and Registry

Provides the base class for all connectors and a registry for managing them.

@ai_prompt: Subclass BaseConnector to create new data source connectors.
@context_boundary: aegistwin/modules/connectors/base

# AI-GENERATED 2026-01-06
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class BaseConnector(ABC):
    """
    Abstract base class for data source connectors.
    
    Subclass this to create connectors for specific data sources
    like email, calendar, messages, etc.
    """
    
    name: str = "base"
    supported_types: List[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the data source."""
        pass
    
    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch data from the source."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source."""
        pass
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate fetched data. Override for custom validation."""
        return True


class ConnectorRegistry:
    """
    Registry for managing connector instances.
    
    Provides a central place to register and retrieve connectors by name.
    """
    
    _connectors: Dict[str, Type[BaseConnector]] = {}
    _instances: Dict[str, BaseConnector] = {}
    
    @classmethod
    def register(cls, connector_class: Type[BaseConnector]) -> Type[BaseConnector]:
        """Register a connector class."""
        cls._connectors[connector_class.name] = connector_class
        return connector_class
    
    @classmethod
    def get(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseConnector:
        """Get or create a connector instance."""
        if name not in cls._instances:
            if name not in cls._connectors:
                raise ValueError(f"Unknown connector: {name}")
            cls._instances[name] = cls._connectors[name](config)
        return cls._instances[name]
    
    @classmethod
    def list_connectors(cls) -> List[str]:
        """List all registered connector names."""
        return list(cls._connectors.keys())
