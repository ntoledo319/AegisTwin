"""
Knowledge graph module for the integrated system.

This module provides knowledge graph capabilities for the integrated system,
including graph building, querying, and visualization.
"""

import logging
from typing import Dict, List, Any, Optional
from .builder import KnowledgeGraphBuilder
from .query import KnowledgeGraphQuery
from .visualization import KnowledgeGraphVisualization

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Main knowledge graph class."""
    
    def __init__(self):
        """Initialize the knowledge graph."""
        # Create components
        self.builder = KnowledgeGraphBuilder()
        self.query = KnowledgeGraphQuery(builder=self.builder)
        self.visualization = KnowledgeGraphVisualization(query_engine=self.query)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the knowledge graph."""
        logger.info("Initializing knowledge graph")
        
        # Initialize components
        await self.builder.initialize()
        await self.query.initialize()
        await self.visualization.initialize()
        
        self.initialized = True
        logger.info("Knowledge graph initialized")
    
    async def process_text(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process text to extract entities and relationships and add them to the knowledge graph.
        
        Args:
            text: Text to process
            context: Additional context
            
        Returns:
            Dictionary containing processing results
        """
        logger.info("Processing text for knowledge graph")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.builder.process_text(text, context)
    
    async def add_entity(self, entity_text: str, entity_type: str, 
                        properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity_text: Entity text
            entity_type: Entity type
            properties: Entity properties
            
        Returns:
            Dictionary containing the added entity
        """
        logger.info(f"Adding entity: {entity_text} ({entity_type})")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.builder.add_entity(entity_text, entity_type, properties)
    
    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str,
                              properties: Dict[str, Any] = None, confidence: float = 1.0) -> Dict[str, Any]:
        """
        Add a relationship to the knowledge graph.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Relationship type
            properties: Relationship properties
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Dictionary containing the added relationship
        """
        logger.info(f"Adding relationship: {source_id} --[{relationship_type}]--> {target_id}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.builder.add_relationship(source_id, target_id, relationship_type, properties, confidence)
    
    async def query_entities(self, filters: Dict[str, Any] = None, 
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query entities based on filters.
        
        Args:
            filters: Dictionary of filters
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        logger.info(f"Querying entities with filters: {filters}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.query.query_entities(filters, limit)
    
    async def query_relationships(self, filters: Dict[str, Any] = None, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query relationships based on filters.
        
        Args:
            filters: Dictionary of filters
            limit: Maximum number of results
            
        Returns:
            List of matching relationships
        """
        logger.info(f"Querying relationships with filters: {filters}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.query.query_relationships(filters, limit)
    
    async def get_entity_neighbors(self, entity_id: str, 
                                  relationship_type: Optional[str] = None,
                                  direction: str = 'both') -> List[Dict[str, Any]]:
        """
        Get neighboring entities of an entity.
        
        Args:
            entity_id: Entity ID
            relationship_type: Relationship type (optional)
            direction: Relationship direction ('outgoing', 'incoming', or 'both')
            
        Returns:
            List of neighboring entities with their relationships
        """
        logger.info(f"Getting neighbors for entity: {entity_id}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.query.get_entity_neighbors(entity_id, relationship_type, direction)
    
    async def find_path(self, source_id: str, target_id: str, 
                       max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Find a path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_depth: Maximum path depth
            
        Returns:
            List of entities and relationships in the path
        """
        logger.info(f"Finding path from {source_id} to {target_id}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.query.find_path(source_id, target_id, max_depth)
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search on entities.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entities with similarity scores
        """
        logger.info(f"Performing semantic search: {query}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.query.semantic_search(query, limit)
    
    async def create_graph_visualization(self, entity_ids: List[str] = None, 
                                        include_relationships: bool = True,
                                        layout: str = 'spring',
                                        width: int = 800,
                                        height: int = 600) -> Dict[str, Any]:
        """
        Create a visualization of the knowledge graph.
        
        Args:
            entity_ids: List of entity IDs to include (optional)
            include_relationships: Whether to include relationships
            layout: Graph layout algorithm
            width: Image width
            height: Image height
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info("Creating graph visualization")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.visualization.create_graph_visualization(
            entity_ids, include_relationships, layout, width, height
        )
    
    async def create_interactive_visualization(self, entity_ids: List[str] = None,
                                              include_relationships: bool = True) -> Dict[str, Any]:
        """
        Create an interactive visualization of the knowledge graph.
        
        Args:
            entity_ids: List of entity IDs to include (optional)
            include_relationships: Whether to include relationships
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info("Creating interactive visualization")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.visualization.create_interactive_visualization(
            entity_ids, include_relationships
        )
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dictionary of graph statistics
        """
        logger.info("Getting knowledge graph statistics")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.builder.get_graph_stats()