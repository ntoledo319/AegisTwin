"""
AegisTwin Synthetic Data Connector

Connector for loading synthetic/fixture data.

@ai_prompt: Use SyntheticConnector to load demo fixtures.
@context_boundary: aegistwin/modules/connectors/synthetic

# AI-GENERATED 2026-01-06
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegistwin.modules.connectors.base import BaseConnector, ConnectorRegistry


@ConnectorRegistry.register
class SyntheticConnector(BaseConnector):
    """
    Connector for synthetic/fixture data.
    
    Loads JSON fixtures from the fixtures/ directory.
    """
    
    name = "synthetic"
    supported_types = ["messages", "contacts", "calendar", "email"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._fixtures_dir = Path(config.get("fixtures_dir", "fixtures")) if config else Path("fixtures")
        self._connected = False
        self._data: Dict[str, List[Dict[str, Any]]] = {}
    
    def connect(self) -> bool:
        """Verify fixtures directory exists."""
        if self._fixtures_dir.exists():
            self._connected = True
            return True
        return False
    
    def fetch(
        self,
        data_type: Optional[str] = None,
        filename: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from fixtures.
        
        Args:
            data_type: Type of data to fetch (messages, contacts, etc.)
            filename: Specific fixture file to load
            
        Returns:
            List of records from the fixture
        """
        if not self._connected:
            self.connect()
        
        # Determine which file to load
        if filename:
            filepath = self._fixtures_dir / filename
        elif data_type:
            filepath = self._fixtures_dir / f"{data_type}.json"
        else:
            filepath = self._fixtures_dir / "demo_small.json"
        
        if not filepath.exists():
            # Try with demo_ prefix
            filepath = self._fixtures_dir / f"demo_{data_type}.json" if data_type else filepath
        
        if not filepath.exists():
            return []
        
        with open(filepath) as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Return the relevant key or all records
            if data_type and data_type in data:
                return data[data_type]
            # Flatten all lists in the dict
            records = []
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            item["_source_type"] = key
                            records.append(item)
            return records
        
        return []
    
    def disconnect(self) -> None:
        """Disconnect from fixtures."""
        self._connected = False
        self._data.clear()
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate fixture data."""
        # Must have at least an id or some identifier
        return bool(data.get("id") or data.get("_id") or data.get("message_id"))


@ConnectorRegistry.register
class JSONConnector(BaseConnector):
    """
    Connector for arbitrary JSON files.
    """
    
    name = "json"
    supported_types = ["json"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._filepath: Optional[Path] = None
        self._connected = False
    
    def connect(self) -> bool:
        """Check if file path is set."""
        filepath = self.config.get("filepath")
        if filepath:
            self._filepath = Path(filepath)
            self._connected = self._filepath.exists()
            return self._connected
        return False
    
    def fetch(self, filepath: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Fetch data from JSON file."""
        if filepath:
            self._filepath = Path(filepath)
        
        if not self._filepath or not self._filepath.exists():
            return []
        
        with open(self._filepath) as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If dict has a 'records' or 'data' key, use that
            for key in ["records", "data", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Otherwise return as single-item list
            return [data]
        
        return []
    
    def disconnect(self) -> None:
        """Disconnect."""
        self._connected = False
        self._filepath = None
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate JSON data."""
        return isinstance(data, dict)
