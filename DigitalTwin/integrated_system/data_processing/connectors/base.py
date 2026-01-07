"""
Base connector for data sources.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from core.config import config

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """Base class for all data connectors."""
    
    def __init__(self, connector_type: str, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the connector.
        
        Args:
            connector_type: Type of connector (email, messages, calendar, social, etc.)
            config_override: Optional configuration override
        """
        self.connector_type = connector_type
        self.config = self._load_config(config_override)
        self.is_connected = False
        
    def _load_config(self, config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration for this connector.
        
        Args:
            config_override: Optional configuration override
            
        Returns:
            Configuration dictionary
        """
        # Load default configuration from config system
        connector_config = config.get(f"data_processing.connectors.{self.connector_type}", {})
        
        # Override with provided configuration if any
        if config_override:
            connector_config.update(config_override)
            
        return connector_config
        
    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to the data source.
        
        Args:
            credentials: Credentials for the data source
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the data source.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
        
    @abstractmethod
    async def import_data(self, 
                         source_path: Optional[str] = None, 
                         start_date: Optional[Union[str, datetime]] = None,
                         end_date: Optional[Union[str, datetime]] = None,
                         limit: Optional[int] = None,
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Import data from the data source.
        
        Args:
            source_path: Optional path to data source file
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Optional maximum number of records to import
            options: Optional additional options
            
        Returns:
            Dictionary with import results
        """
        pass
        
    @abstractmethod
    async def process_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a batch of data.
        
        Args:
            batch_data: Batch of data to process
            
        Returns:
            Processing results
        """
        pass
        
    def _parse_date(self, date_value: Union[str, datetime]) -> datetime:
        """
        Parse a date value.
        
        Args:
            date_value: Date value as string or datetime
            
        Returns:
            Datetime object
        """
        if isinstance(date_value, datetime):
            return date_value
            
        # Try different date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_value, date_format)
            except ValueError:
                continue
                
        raise ValueError(f"Could not parse date: {date_value}")
        
    def _validate_options(self, options: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate options dictionary.
        
        Args:
            options: Options dictionary
            required_keys: List of required keys
            
        Returns:
            True if options are valid, False otherwise
        """
        if not options:
            return False
            
        for key in required_keys:
            if key not in options:
                logger.error(f"Missing required option: {key}")
                return False
                
        return True