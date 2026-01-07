"""
Data processing pipeline for the integrated system.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from core.config import config
from core.db import db_manager
from data_processing.connectors import (
    BaseConnector,
    EmailConnector,
    MessagesConnector,
    CalendarConnector,
    SocialConnector
)

logger = logging.getLogger(__name__)

class DataPipeline:
    """Data processing pipeline for the integrated system."""
    
    def __init__(self):
        """Initialize the data pipeline."""
        self.connectors = {}
        self.active_jobs = {}
        self.results_cache = {}
        
    async def initialize(self):
        """Initialize the data pipeline."""
        logger.info("Initializing data pipeline...")
        
        # Initialize connectors
        await self._initialize_connectors()
        
        logger.info("Data pipeline initialization complete")
        
    async def shutdown(self):
        """Shutdown the data pipeline."""
        logger.info("Shutting down data pipeline...")
        
        # Disconnect all connectors
        for connector_type, connector in self.connectors.items():
            try:
                await connector.disconnect()
                logger.info(f"Disconnected {connector_type} connector")
            except Exception as e:
                logger.error(f"Error disconnecting {connector_type} connector: {str(e)}")
                
        # Clear active jobs
        self.active_jobs = {}
        
        # Clear results cache
        self.results_cache = {}
        
        logger.info("Data pipeline shutdown complete")
        
    async def _initialize_connectors(self):
        """Initialize data connectors."""
        # Initialize email connector
        if config.get("data_processing.connectors.email.enabled", True):
            self.connectors["email"] = EmailConnector()
            logger.info("Initialized email connector")
            
        # Initialize messages connector
        if config.get("data_processing.connectors.messages.enabled", True):
            self.connectors["messages"] = MessagesConnector()
            logger.info("Initialized messages connector")
            
        # Initialize calendar connector
        if config.get("data_processing.connectors.calendar.enabled", True):
            self.connectors["calendar"] = CalendarConnector()
            logger.info("Initialized calendar connector")
            
        # Initialize social connector
        if config.get("data_processing.connectors.social.enabled", True):
            self.connectors["social"] = SocialConnector()
            logger.info("Initialized social connector")
            
    async def import_data(self, 
                         source: str, 
                         path: str, 
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Import data from a specific source.
        
        Args:
            source: Source type (email, messages, calendar, social)
            path: Path to data file or directory
            options: Additional options
            
        Returns:
            Dictionary with import results
        """
        try:
            # Check if source is supported
            if source not in self.connectors:
                return {
                    "status": "error",
                    "message": f"Unsupported data source: {source}",
                    "record_count": 0
                }
                
            # Get connector
            connector = self.connectors[source]
            
            # Import data
            logger.info(f"Importing data from {source}: {path}")
            result = await connector.import_data(path, options=options)
            
            # Cache result
            import_id = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{source}"
            self.results_cache[import_id] = result
            
            # Add import ID to result
            result["import_id"] = import_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing data from {source}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error importing data from {source}: {str(e)}",
                "record_count": 0
            }
            
    async def process_batch(self, 
                           source: str, 
                           batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a batch of data.
        
        Args:
            source: Source type (email, messages, calendar, social)
            batch_data: Batch of data to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Check if source is supported
            if source not in self.connectors:
                return {
                    "status": "error",
                    "message": f"Unsupported data source: {source}",
                    "record_count": 0
                }
                
            # Get connector
            connector = self.connectors[source]
            
            # Process batch
            logger.info(f"Processing batch from {source}")
            result = await connector.process_batch(batch_data)
            
            # Cache result
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{source}"
            self.results_cache[batch_id] = result
            
            # Add batch ID to result
            result["batch_id"] = batch_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing batch from {source}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing batch from {source}: {str(e)}",
                "record_count": 0
            }
            
    async def process_all(self) -> Dict[str, Any]:
        """
        Process all imported data.
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Get all import results from cache
            import_results = {k: v for k, v in self.results_cache.items() if k.startswith("import_")}
            
            if not import_results:
                return {
                    "status": "error",
                    "message": "No imported data to process",
                    "total_records": 0
                }
                
            # Process each import result
            processing_results = {}
            total_records = 0
            sources = set()
            
            for import_id, import_result in import_results.items():
                # Extract source from import ID
                source = import_id.split("_")[-1]
                sources.add(source)
                
                # Process batch
                batch_result = await self.process_batch(source, import_result)
                
                # Add to processing results
                processing_results[import_id] = batch_result
                
                # Update total records
                total_records += batch_result.get("record_count", 0)
                
            # Create result
            result = {
                "status": "success",
                "message": f"Processed {total_records} records from {len(sources)} sources",
                "total_records": total_records,
                "sources": list(sources),
                "processing_results": processing_results
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing all data: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing all data: {str(e)}",
                "total_records": 0
            }
            
    async def get_import_status(self, import_id: str) -> Dict[str, Any]:
        """
        Get the status of a data import.
        
        Args:
            import_id: Import ID
            
        Returns:
            Dictionary with import status
        """
        try:
            # Check if import ID exists
            if import_id not in self.results_cache:
                return {
                    "status": "error",
                    "message": f"Import ID not found: {import_id}",
                    "record_count": 0
                }
                
            # Get import result
            import_result = self.results_cache[import_id]
            
            # Create status result
            status_result = {
                "import_id": import_id,
                "status": import_result.get("status", "unknown"),
                "message": import_result.get("message", ""),
                "record_count": import_result.get("record_count", 0),
                "metadata": import_result.get("metadata", {})
            }
            
            return status_result
            
        except Exception as e:
            logger.error(f"Error getting import status: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting import status: {str(e)}",
                "record_count": 0
            }
            
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the status of a data batch.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Dictionary with batch status
        """
        try:
            # Check if batch ID exists
            if batch_id not in self.results_cache:
                return {
                    "status": "error",
                    "message": f"Batch ID not found: {batch_id}",
                    "record_count": 0
                }
                
            # Get batch result
            batch_result = self.results_cache[batch_id]
            
            # Create status result
            status_result = {
                "batch_id": batch_id,
                "status": batch_result.get("status", "unknown"),
                "message": batch_result.get("message", ""),
                "record_count": batch_result.get("record_count", 0),
                "metadata": batch_result.get("metadata", {})
            }
            
            return status_result
            
        except Exception as e:
            logger.error(f"Error getting batch status: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting batch status: {str(e)}",
                "record_count": 0
            }
            
    async def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get all data for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user data
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, we would:
            # 1. Query the database for user data
            # 2. Retrieve data from various sources
            # 3. Combine and return the data
            
            # Simulate user data
            user_data = {
                "user_id": user_id,
                "email": {
                    "messages": [],
                    "contacts": [],
                    "statistics": {}
                },
                "messages": {
                    "conversations": [],
                    "contacts": [],
                    "statistics": {}
                },
                "calendar": {
                    "events": [],
                    "statistics": {}
                },
                "social": {
                    "posts": [],
                    "profile": {},
                    "statistics": {}
                }
            }
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting user data: {str(e)}",
                "user_id": user_id
            }