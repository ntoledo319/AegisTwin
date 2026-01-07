"""
Base connector class for data source integration.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.logging import get_logger
from core.utils import generate_id, timestamp_now

logger = get_logger(__name__)

class DataConnectorBase(ABC):
    """
    Base class for all data connectors.
    
    This class defines the interface that all data connectors must implement.
    It provides common functionality for connecting to data sources, extracting
    data, and transforming it into a standardized format.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Configuration dictionary for the connector
        """
        self.config = config
        self.connector_id = config.get("connector_id", generate_id("connector"))
        self.connector_type = self.__class__.__name__
        self.connection = None
        self.connected = False
        self.last_extraction = None
        self.extraction_stats = {
            "total_extractions": 0,
            "total_items": 0,
            "last_extraction_time": None,
            "average_extraction_time": 0,
        }
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the data source.
        
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
    async def extract_data(self, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract data from the source.
        
        Args:
            parameters: Optional parameters for extraction
            
        Returns:
            List of extracted data items
        """
        pass
    
    @abstractmethod
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw data into standardized format.
        
        Args:
            raw_data: Raw data from the source
            
        Returns:
            Transformed data in standardized format
        """
        pass
    
    async def get_data(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to get and process data.
        
        This method handles the full data extraction process:
        1. Connect to the data source
        2. Extract raw data
        3. Transform the data
        4. Disconnect from the source
        5. Return the processed data with metadata
        
        Args:
            parameters: Optional parameters for extraction
            
        Returns:
            Dictionary containing processed data and metadata
        """
        start_time = datetime.now()
        
        try:
            # Connect to data source
            if not self.connected:
                connection_success = await self.connect()
                if not connection_success:
                    return {
                        "success": False,
                        "error": "Failed to connect to data source",
                        "data": [],
                        "metadata": {
                            "connector_id": self.connector_id,
                            "connector_type": self.connector_type,
                            "timestamp": timestamp_now(),
                            "parameters": parameters,
                        }
                    }
            
            # Extract raw data
            raw_data = await self.extract_data(parameters)
            
            # Transform data
            processed_data = await self.transform_data(raw_data)
            
            # Update extraction stats
            self.extraction_stats["total_extractions"] += 1
            self.extraction_stats["total_items"] += len(processed_data)
            self.extraction_stats["last_extraction_time"] = timestamp_now()
            
            extraction_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate running average extraction time
            if self.extraction_stats["total_extractions"] == 1:
                self.extraction_stats["average_extraction_time"] = extraction_time
            else:
                prev_avg = self.extraction_stats["average_extraction_time"]
                n = self.extraction_stats["total_extractions"]
                self.extraction_stats["average_extraction_time"] = prev_avg + (extraction_time - prev_avg) / n
            
            return {
                "success": True,
                "data": processed_data,
                "metadata": {
                    "connector_id": self.connector_id,
                    "connector_type": self.connector_type,
                    "timestamp": timestamp_now(),
                    "parameters": parameters,
                    "item_count": len(processed_data),
                    "extraction_time_seconds": extraction_time,
                }
            }
            
        except Exception as e:
            logger.exception(f"Error in data extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "metadata": {
                    "connector_id": self.connector_id,
                    "connector_type": self.connector_type,
                    "timestamp": timestamp_now(),
                    "parameters": parameters,
                }
            }
        finally:
            # Disconnect if needed
            if self.config.get("disconnect_after_extraction", True) and self.connected:
                await self.disconnect()
    
    async def validate_config(self) -> Dict[str, Any]:
        """
        Validate the connector configuration.
        
        Returns:
            Dictionary with validation results
        """
        # Base validation that all connectors should have
        required_fields = ["connector_id"]
        missing_fields = [field for field in required_fields if field not in self.config]
        
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "message": f"Missing required configuration fields: {', '.join(missing_fields)}"
            }
        
        return {
            "valid": True,
            "message": "Configuration is valid"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the connector.
        
        Returns:
            Dictionary with connector status
        """
        return {
            "connector_id": self.connector_id,
            "connector_type": self.connector_type,
            "connected": self.connected,
            "last_extraction": self.last_extraction,
            "extraction_stats": self.extraction_stats,
            "config": {k: v for k, v in self.config.items() if k not in ["password", "api_key", "secret"]}
        }