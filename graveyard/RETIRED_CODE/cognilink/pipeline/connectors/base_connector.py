"""
Base Connector for CogniLink

This module provides a base connector class that all connectors should inherit from.
It defines the common interface and functionality for data connectors.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator, Union
import os
import json

from cognilink.core.utils import generate_message_id

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """
    Base class for all data connectors.
    
    This abstract class defines the common interface and functionality that
    all data connectors should implement.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the base connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        self.config = config or {}
        self.item_count = 0
        self.error_count = 0
        self.platform_name = "unknown"
    
    @abstractmethod
    def extract_from_file(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a file.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments specific to the connector
            
        Yields:
            Dictionaries containing normalized data
        """
        pass
    
    def extract_from_directory(self, directory_path: str, file_pattern: str = "*", **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from files in a directory.
        
        Args:
            directory_path: Path to the directory
            file_pattern: Pattern to match files (e.g., "*.json")
            **kwargs: Additional arguments specific to the connector
            
        Yields:
            Dictionaries containing normalized data
        """
        import glob
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return
        
        # Find matching files
        pattern = os.path.join(directory_path, file_pattern)
        files = glob.glob(pattern)
        
        if not files:
            logger.warning(f"No files matching pattern '{file_pattern}' found in {directory_path}")
            return
        
        logger.info(f"Found {len(files)} files matching pattern '{file_pattern}' in {directory_path}")
        
        # Process each file
        for file_path in files:
            try:
                yield from self.extract_from_file(file_path, **kwargs)
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def extract_from_json(self, json_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            **kwargs: Additional arguments specific to the connector
            
        Yields:
            Dictionaries containing normalized data
        """
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process the JSON data
            yield from self._process_json_data(data, **kwargs)
            
        except Exception as e:
            logger.error(f"Failed to process JSON file {json_path}: {str(e)}")
    
    def _process_json_data(self, data: Union[Dict[str, Any], List[Any]], **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Process JSON data and extract normalized items.
        
        Args:
            data: JSON data as dictionary or list
            **kwargs: Additional arguments specific to the connector
            
        Yields:
            Dictionaries containing normalized data
        """
        # This is a placeholder method that should be overridden by subclasses
        # Default implementation for simple list of items
        items = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try to find a list of items in the dictionary
            for key, value in data.items():
                if isinstance(value, list) and value:
                    items = value
                    break
        
        if not items:
            logger.warning("No items found in JSON data")
            return
        
        logger.info(f"Processing {len(items)} items from JSON data")
        
        for item in items:
            try:
                normalized_item = self._normalize_item(item, **kwargs)
                if normalized_item:
                    self.item_count += 1
                    yield normalized_item
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing item: {str(e)}")
    
    @abstractmethod
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
            
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        pass
    
    def _generate_id(self, item: Dict[str, Any]) -> str:
        """
        Generate a unique ID for an item.
        
        Args:
            item: Item data
            
        Returns:
            Unique ID string
        """
        return generate_message_id(item)
    
    def _apply_filters(self, item: Dict[str, Any]) -> bool:
        """
        Apply filters to determine if an item should be included.
        
        Args:
            item: Item data
            
        Returns:
            True if the item should be included, False otherwise
        """
        # Get filter settings from config
        filters = self.config.get('filters', {})
        
        # Check minimum date
        if 'min_date' in filters and filters['min_date'] and 'timestamp' in item:
            try:
                min_date = filters['min_date']
                if item['timestamp'] < min_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Check maximum date
        if 'max_date' in filters and filters['max_date'] and 'timestamp' in item:
            try:
                max_date = filters['max_date']
                if item['timestamp'] > max_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Check minimum content length
        if 'min_content_length' in filters and 'content' in item:
            min_length = filters.get('min_content_length', 0)
            if len(item.get('content', '')) < min_length:
                return False
        
        # Check platform inclusion
        if 'include_platforms' in filters and filters['include_platforms']:
            if self.platform_name not in filters['include_platforms']:
                return False
        
        # Check platform exclusion
        if 'exclude_platforms' in filters and filters['exclude_platforms']:
            if self.platform_name in filters['exclude_platforms']:
                return False
        
        return True