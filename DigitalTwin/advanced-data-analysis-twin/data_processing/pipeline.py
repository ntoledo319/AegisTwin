"""
Data processing pipeline for the Advanced Data Analysis & Digital Twin System.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from core.logging import get_logger
from core.utils import generate_id, timestamp_now
from .connectors import get_connector_class, DataConnectorBase
from .processors import create_processor

logger = get_logger(__name__)

class DataPipeline:
    """
    Data processing pipeline that coordinates connectors and processors.
    
    This pipeline handles:
    - Data extraction from various sources
    - Data processing and transformation
    - Data normalization and standardization
    - Pipeline execution and monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the data pipeline.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - pipeline_id: Unique identifier for the pipeline
                - connectors: List of connector configurations
                - processors: List of processor configurations
                - max_concurrent_tasks: Maximum number of concurrent tasks
                - error_handling: Error handling strategy
        """
        self.config = config or {}
        self.pipeline_id = self.config.get("pipeline_id", generate_id("pipeline"))
        self.connectors: Dict[str, DataConnectorBase] = {}
        self.processors = {}
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 5)
        self.error_handling = self.config.get("error_handling", "continue")
        
        # Pipeline statistics
        self.stats = {
            "created_at": timestamp_now(),
            "last_run": None,
            "total_runs": 0,
            "total_items_processed": 0,
            "total_errors": 0,
            "average_processing_time": 0.0,
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the pipeline by setting up connectors and processors.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize connectors
            connector_configs = self.config.get("connectors", [])
            for connector_config in connector_configs:
                connector_type = connector_config.get("type")
                connector_id = connector_config.get("connector_id", generate_id("connector"))
                
                if not connector_type:
                    logger.error(f"Missing connector type in configuration: {connector_config}")
                    continue
                
                try:
                    connector_class = get_connector_class(connector_type)
                    connector = connector_class(connector_config)
                    self.connectors[connector_id] = connector
                    logger.info(f"Initialized connector: {connector_id} ({connector_type})")
                except Exception as e:
                    logger.error(f"Failed to initialize connector {connector_type}: {str(e)}")
            
            # Initialize processors
            processor_configs = self.config.get("processors", [])
            for processor_config in processor_configs:
                processor_type = processor_config.get("type")
                processor_id = processor_config.get("processor_id", generate_id("processor"))
                
                if not processor_type:
                    logger.error(f"Missing processor type in configuration: {processor_config}")
                    continue
                
                try:
                    processor = await create_processor(processor_type, processor_config)
                    self.processors[processor_id] = processor
                    logger.info(f"Initialized processor: {processor_id} ({processor_type})")
                except Exception as e:
                    logger.error(f"Failed to initialize processor {processor_type}: {str(e)}")
            
            logger.info(f"Pipeline {self.pipeline_id} initialized with {len(self.connectors)} connectors and {len(self.processors)} processors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            return False
    
    async def run(self, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the complete data pipeline.
        
        Args:
            parameters: Optional parameters for the pipeline run
                - connector_ids: List of connector IDs to use (default: all)
                - processor_ids: List of processor IDs to use (default: all)
                - connector_parameters: Parameters for connectors
                - processor_parameters: Parameters for processors
                - max_items: Maximum number of items to process
        
        Returns:
            Dictionary with pipeline results
        """
        start_time = datetime.now()
        parameters = parameters or {}
        
        # Track pipeline run
        run_id = generate_id("run")
        self.stats["last_run"] = timestamp_now()
        self.stats["total_runs"] += 1
        
        # Determine which connectors to use
        connector_ids = parameters.get("connector_ids", list(self.connectors.keys()))
        selected_connectors = {
            connector_id: self.connectors[connector_id]
            for connector_id in connector_ids
            if connector_id in self.connectors
        }
        
        # Determine which processors to use
        processor_ids = parameters.get("processor_ids", list(self.processors.keys()))
        selected_processors = {
            processor_id: self.processors[processor_id]
            for processor_id in processor_ids
            if processor_id in self.processors
        }
        
        # Prepare results
        results = {
            "run_id": run_id,
            "pipeline_id": self.pipeline_id,
            "timestamp": timestamp_now(),
            "parameters": parameters,
            "connector_results": {},
            "processor_results": {},
            "summary": {
                "total_items_extracted": 0,
                "total_items_processed": 0,
                "total_errors": 0,
                "processing_time": 0.0,
            }
        }
        
        try:
            # Extract data from connectors
            connector_results = await self._extract_data(selected_connectors, parameters.get("connector_parameters", {}))
            results["connector_results"] = connector_results
            
            # Combine all extracted data
            all_data = []
            for connector_id, connector_result in connector_results.items():
                if connector_result.get("success", False):
                    all_data.extend(connector_result.get("data", []))
            
            results["summary"]["total_items_extracted"] = len(all_data)
            
            # Apply processors to data
            processor_results = await self._process_data(all_data, selected_processors, parameters.get("processor_parameters", {}))
            results["processor_results"] = processor_results
            
            # Update summary
            results["summary"]["total_items_processed"] = len(all_data)
            results["summary"]["total_errors"] = sum(
                1 for result in connector_results.values() if not result.get("success", False)
            )
            
            # Update pipeline stats
            self.stats["total_items_processed"] += len(all_data)
            self.stats["total_errors"] += results["summary"]["total_errors"]
            
            processing_time = (datetime.now() - start_time).total_seconds()
            results["summary"]["processing_time"] = processing_time
            
            # Update average processing time
            if self.stats["total_runs"] == 1:
                self.stats["average_processing_time"] = processing_time
            else:
                prev_avg = self.stats["average_processing_time"]
                n = self.stats["total_runs"]
                self.stats["average_processing_time"] = prev_avg + (processing_time - prev_avg) / n
            
            logger.info(f"Pipeline {self.pipeline_id} run completed: {len(all_data)} items processed in {processing_time:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Pipeline run failed: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            return results
    
    async def _extract_data(self, connectors: Dict[str, DataConnectorBase], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from connectors.
        
        Args:
            connectors: Dictionary of connectors to use
            parameters: Parameters for connectors
            
        Returns:
            Dictionary with connector results
        """
        connector_results = {}
        
        # Create tasks for each connector
        tasks = []
        for connector_id, connector in connectors.items():
            connector_params = parameters.get(connector_id, {})
            task = asyncio.create_task(self._run_connector(connector_id, connector, connector_params))
            tasks.append(task)
        
        # Run tasks with concurrency limit
        for i in range(0, len(tasks), self.max_concurrent_tasks):
            batch = tasks[i:i + self.max_concurrent_tasks]
            batch_results = await asyncio.gather(*batch)
            
            for connector_id, result in batch_results:
                connector_results[connector_id] = result
        
        return connector_results
    
    async def _run_connector(self, connector_id: str, connector: DataConnectorBase, parameters: Dict[str, Any]) -> tuple:
        """
        Run a single connector.
        
        Args:
            connector_id: Connector ID
            connector: Connector instance
            parameters: Parameters for the connector
            
        Returns:
            Tuple of (connector_id, result)
        """
        try:
            result = await connector.get_data(parameters)
            return connector_id, result
        except Exception as e:
            logger.error(f"Connector {connector_id} failed: {str(e)}")
            return connector_id, {
                "success": False,
                "error": str(e),
                "data": [],
                "metadata": {
                    "connector_id": connector_id,
                    "timestamp": timestamp_now(),
                    "parameters": parameters,
                }
            }
    
    async def _process_data(self, data: List[Dict[str, Any]], processors: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data with processors.
        
        Args:
            data: Data to process
            processors: Dictionary of processors to use
            parameters: Parameters for processors
            
        Returns:
            Dictionary with processor results
        """
        processor_results = {}
        
        # Apply each processor to the data
        for processor_id, processor in processors.items():
            processor_params = parameters.get(processor_id, {})
            
            try:
                # Check if processor has a process_batch method
                if hasattr(processor, "process_batch"):
                    # Process all data at once
                    start_time = datetime.now()
                    processed_data = await processor.process_batch(data)
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    processor_results[processor_id] = {
                        "success": True,
                        "items_processed": len(data),
                        "processing_time": processing_time,
                        "metadata": {
                            "processor_id": processor_id,
                            "timestamp": timestamp_now(),
                            "parameters": processor_params,
                        }
                    }
                else:
                    # Process items individually
                    start_time = datetime.now()
                    processed_items = 0
                    
                    for item in data:
                        try:
                            # Check if processor has a process method
                            if hasattr(processor, "process"):
                                await processor.process(item)
                            # Check if processor has a process_text method (for text processors)
                            elif hasattr(processor, "process_text") and "content" in item:
                                text_result = await processor.process_text(item["content"])
                                item["analysis"] = text_result
                            
                            processed_items += 1
                        except Exception as e:
                            logger.warning(f"Failed to process item with {processor_id}: {str(e)}")
                            if self.error_handling == "fail":
                                raise
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    processor_results[processor_id] = {
                        "success": True,
                        "items_processed": processed_items,
                        "processing_time": processing_time,
                        "metadata": {
                            "processor_id": processor_id,
                            "timestamp": timestamp_now(),
                            "parameters": processor_params,
                        }
                    }
            
            except Exception as e:
                logger.error(f"Processor {processor_id} failed: {str(e)}")
                processor_results[processor_id] = {
                    "success": False,
                    "error": str(e),
                    "items_processed": 0,
                    "metadata": {
                        "processor_id": processor_id,
                        "timestamp": timestamp_now(),
                        "parameters": processor_params,
                    }
                }
                
                if self.error_handling == "fail":
                    raise
        
        return processor_results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the pipeline.
        
        Returns:
            Dictionary with pipeline status
        """
        return {
            "pipeline_id": self.pipeline_id,
            "connectors": {
                connector_id: connector.get_status()
                for connector_id, connector in self.connectors.items()
            },
            "processors": {
                processor_id: {
                    "processor_id": processor_id,
                    "processor_type": processor.__class__.__name__,
                }
                for processor_id, processor in self.processors.items()
            },
            "stats": self.stats,
            "config": {
                k: v for k, v in self.config.items()
                if k not in ["connectors", "processors"]
            }
        }