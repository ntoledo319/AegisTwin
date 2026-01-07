"""
Core Data Processing Pipeline

Provides the main data processing pipeline that orchestrates data ingestion,
processing, analysis, and storage for the Cognitive-Twin system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    processed_count: int
    error_count: int
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class DataPipeline:
    """
    Main data processing pipeline for Cognitive-Twin.
    
    Orchestrates the complete data processing workflow from ingestion
    through analysis and storage.
    """
    
    def __init__(self):
        """Initialize the data processing pipeline"""
        self.connectors = {}
        self.processors = {}
        self.analyzers = {}
        self.storage_backends = {}
        self.pipeline_steps = []
        self.initialized = False
        
        logger.info("Data processing pipeline initialized")
    
    async def initialize(self):
        """Initialize pipeline components"""
        try:
            # Initialize connectors
            await self._initialize_connectors()
            
            # Initialize processors
            await self._initialize_processors()
            
            # Initialize analyzers
            await self._initialize_analyzers()
            
            # Initialize storage
            await self._initialize_storage()
            
            self.initialized = True
            logger.info("Data processing pipeline initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize data processing pipeline: {e}")
            raise
    
    async def _initialize_connectors(self):
        """Initialize data connectors"""
        try:
            # Import connectors
            from ..connectors.email import EmailConnector
            from ..connectors.messages import MessagesConnector
            from ..connectors.social import SocialConnector
            from ..connectors.calendar import CalendarConnector
            
            # Initialize connectors
            self.connectors = {
                'email': EmailConnector(),
                'messages': MessagesConnector(),
                'social': SocialConnector(),
                'calendar': CalendarConnector()
            }
            
            # Initialize each connector
            for name, connector in self.connectors.items():
                if hasattr(connector, 'initialize'):
                    await connector.initialize()
                    logger.info(f"Initialized {name} connector")
            
        except Exception as e:
            logger.error(f"Failed to initialize connectors: {e}")
            # Continue with available connectors - partial initialization is acceptable
            logger.warning("Some connectors may not be available, but pipeline will continue with available ones")
    
    async def _initialize_processors(self):
        """Initialize data processors"""
        try:
            # Basic processing functions
            self.processors = {
                'text_cleaner': self._clean_text,
                'data_normalizer': self._normalize_data,
                'duplicate_remover': self._remove_duplicates,
                'validator': self._validate_data
            }
            
            logger.info("Data processors initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize processors: {e}")
            logger.warning("Processor initialization failed, some processing features may be unavailable")
    
    async def _initialize_analyzers(self):
        """Initialize data analyzers"""
        try:
            # Import analyzers
            from ...analysis.communication.patterns import CommunicationAnalyzer
            from ...analysis.advanced.nlp import AdvancedAnalyzer
            from ...analysis.cognitive.personality import CognitiveAnalyzer
            
            # Initialize analyzers
            self.analyzers = {
                'communication': CommunicationAnalyzer(),
                'advanced': AdvancedAnalyzer(),
                'cognitive': CognitiveAnalyzer()
            }
            
            # Initialize each analyzer
            for name, analyzer in self.analyzers.items():
                if hasattr(analyzer, 'initialize'):
                    await analyzer.initialize()
                    logger.info(f"Initialized {name} analyzer")
            
        except Exception as e:
            logger.error(f"Failed to initialize analyzers: {e}")
            # Continue without analyzers - basic pipeline can still function
            logger.warning("Analyzer initialization failed, advanced analysis features may be unavailable")
    
    async def _initialize_storage(self):
        """Initialize storage backends"""
        try:
            # Import storage backends
            from ..storage.document_store import DocumentStore
            from ..storage.vector_store import VectorStore
            from ..storage.graph_store import GraphStore
            
            # Initialize storage backends
            self.storage_backends = {
                'documents': DocumentStore(),
                'vectors': VectorStore(),
                'graph': GraphStore()
            }
            
            # Initialize each storage backend
            for name, storage in self.storage_backends.items():
                if hasattr(storage, 'initialize'):
                    await storage.initialize()
                    logger.info(f"Initialized {name} storage")
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            # Continue without storage - pipeline can still process data but won't persist results
            logger.warning("Storage initialization failed, processed data will not be persisted")
    
    async def process_data(self, 
                          data_source: str, 
                          data: Any,
                          options: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process data through the complete pipeline.
        
        Args:
            data_source: Source of the data (email, messages, etc.)
            data: Raw data to process
            options: Processing options
            
        Returns:
            ProcessingResult with details of the processing
        """
        if not self.initialized:
            await self.initialize()
        
        options = options or {}
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting data processing for source: {data_source}")
            
            # Step 1: Data validation and normalization
            normalized_data = await self._normalize_data(data)
            
            # Step 2: Data cleaning
            cleaned_data = await self._clean_data(normalized_data)
            
            # Step 3: Data analysis
            analysis_results = await self._analyze_data(data_source, cleaned_data, options)
            
            # Step 4: Data storage
            storage_results = await self._store_data(data_source, cleaned_data, analysis_results, options)
            
            # Step 5: Generate insights
            insights = await self._generate_insights(data_source, analysis_results, options)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ProcessingResult(
                success=True,
                processed_count=len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                error_count=0,
                data={
                    'processed_data': cleaned_data,
                    'analysis_results': analysis_results,
                    'storage_results': storage_results,
                    'insights': insights
                },
                metadata={
                    'processing_time': processing_time,
                    'data_source': data_source,
                    'options': options
                }
            )
            
            logger.info(f"Data processing completed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Data processing failed: {e}")
            
            return ProcessingResult(
                success=False,
                processed_count=0,
                error_count=1,
                errors=[str(e)],
                metadata={
                    'processing_time': processing_time,
                    'data_source': data_source,
                    'error_traceback': traceback.format_exc()
                }
            )
    
    async def _normalize_data(self, data: Any) -> Any:
        """Normalize data format"""
        try:
            if isinstance(data, dict):
                # Ensure consistent field names
                normalized = {}
                for key, value in data.items():
                    # Convert key to lowercase and standardize
                    norm_key = key.lower().replace(' ', '_').replace('-', '_')
                    normalized[norm_key] = value
                return normalized
            elif isinstance(data, list):
                return [await self._normalize_data(item) for item in data]
            else:
                return data
        except Exception as e:
            logger.warning(f"Data normalization failed: {e}")
            return data
    
    async def _clean_data(self, data: Any) -> Any:
        """Clean and validate data"""
        try:
            if isinstance(data, dict):
                cleaned = {}
                for key, value in data.items():
                    if value is not None and value != '':
                        if isinstance(value, str):
                            # Basic text cleaning
                            value = value.strip()
                            if value:  # Only add non-empty strings
                                cleaned[key] = value
                        else:
                            cleaned[key] = value
                return cleaned
            elif isinstance(data, list):
                return [await self._clean_data(item) for item in data if item is not None]
            else:
                return data
        except Exception as e:
            logger.warning(f"Data cleaning failed: {e}")
            return data
    
    async def _analyze_data(self, 
                           data_source: str, 
                           data: Any, 
                           options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data using available analyzers"""
        analysis_results = {}
        
        for name, analyzer in self.analyzers.items():
            try:
                if hasattr(analyzer, 'analyze'):
                    result = await analyzer.analyze(data, source=data_source, **options)
                    analysis_results[name] = result
                    logger.debug(f"Analysis completed: {name}")
            except Exception as e:
                logger.warning(f"Analysis failed for {name}: {e}")
                analysis_results[name] = {'error': str(e)}
        
        return analysis_results
    
    async def _store_data(self, 
                         data_source: str, 
                         data: Any, 
                         analysis_results: Dict[str, Any],
                         options: Dict[str, Any]) -> Dict[str, Any]:
        """Store processed data and analysis results"""
        storage_results = {}
        
        for name, storage in self.storage_backends.items():
            try:
                if hasattr(storage, 'store'):
                    result = await storage.store(
                        data=data,
                        analysis=analysis_results,
                        source=data_source,
                        **options
                    )
                    storage_results[name] = result
                    logger.debug(f"Storage completed: {name}")
            except Exception as e:
                logger.warning(f"Storage failed for {name}: {e}")
                storage_results[name] = {'error': str(e)}
        
        return storage_results
    
    async def _generate_insights(self, 
                                data_source: str, 
                                analysis_results: Dict[str, Any],
                                options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis results"""
        try:
            insights = {
                'data_source': data_source,
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'total_analyses': len(analysis_results),
                    'successful_analyses': sum(1 for r in analysis_results.values() if 'error' not in r),
                    'failed_analyses': sum(1 for r in analysis_results.values() if 'error' in r)
                },
                'key_findings': [],
                'recommendations': []
            }
            
            # Extract key findings from analysis results
            for analysis_name, results in analysis_results.items():
                if 'error' not in results:
                    if 'insights' in results:
                        insights['key_findings'].extend(results['insights'])
                    if 'recommendations' in results:
                        insights['recommendations'].extend(results['recommendations'])
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # Helper methods for processors
    async def _clean_text(self, text: str) -> str:
        """Clean text data"""
        if not isinstance(text, str):
            return text
        
        # Basic text cleaning
        cleaned = text.strip()
        # Remove excessive whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    async def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data structure"""
        return data
    
    async def _remove_duplicates(self, data: List[Any]) -> List[Any]:
        """Remove duplicate entries"""
        if not isinstance(data, list):
            return data
        
        seen = set()
        unique_data = []
        
        for item in data:
            # Create a simple hash for comparison
            item_hash = str(item)
            if item_hash not in seen:
                seen.add(item_hash)
                unique_data.append(item)
        
        return unique_data
    
    async def _validate_data(self, data: Any) -> bool:
        """Validate data structure"""
        try:
            # Basic validation - ensure data is not None or empty
            if data is None:
                return False
            
            if isinstance(data, (list, dict, str)) and len(data) == 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def shutdown(self):
        """Shutdown pipeline components"""
        logger.info("Shutting down data processing pipeline")
        
        # Shutdown storage backends
        for name, storage in self.storage_backends.items():
            try:
                if hasattr(storage, 'shutdown'):
                    await storage.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name} storage: {e}")
        
        # Shutdown analyzers
        for name, analyzer in self.analyzers.items():
            try:
                if hasattr(analyzer, 'shutdown'):
                    await analyzer.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name} analyzer: {e}")
        
        # Shutdown connectors
        for name, connector in self.connectors.items():
            try:
                if hasattr(connector, 'shutdown'):
                    await connector.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {name} connector: {e}")
        
        self.initialized = False
        logger.info("Data processing pipeline shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            'initialized': self.initialized,
            'connectors': list(self.connectors.keys()),
            'processors': list(self.processors.keys()),
            'analyzers': list(self.analyzers.keys()),
            'storage_backends': list(self.storage_backends.keys()),
            'pipeline_steps': len(self.pipeline_steps)
        }
