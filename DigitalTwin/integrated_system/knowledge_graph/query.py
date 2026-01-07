"""
Knowledge graph query engine module.

This module provides functionality for querying the knowledge graph,
including graph queries, semantic search, and path finding.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import asyncio
import json
import os
from datetime import datetime
import heapq

logger = logging.getLogger(__name__)

class KnowledgeGraphQuery:
    """Query engine for knowledge graphs."""
    
    def __init__(self, builder=None):
        """
        Initialize the knowledge graph query engine.
        
        Args:
            builder: Knowledge graph builder instance
        """
        self.builder = builder
        self.entities = {}
        self.relationships = []
        self.entity_index = {}  # Index for faster entity lookup
        self.relationship_index = {}  # Index for faster relationship lookup
        self.vector_search_available = False
        self.initialized = False
        
        # Try to import vector search libraries
        try:
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            self.vectorizer = TfidfVectorizer(max_features=100)
            self.vector_search_available = True
            logger.info("Vector search available for knowledge graph queries")
        except ImportError:
            logger.warning("Vector search not available for knowledge graph queries")
    
    async def initialize(self):
        """Initialize the knowledge graph query engine."""
        logger.info("Initializing knowledge graph query engine")
        
        # Load entities and relationships from builder if available
        if self.builder:
            if not self.builder.initialized:
                await self.builder.initialize()
            
            self.entities = self.builder.entities
            self.relationships = self.builder.relationships
        
        # Build indices
        self._build_indices()
        
        self.initialized = True
        logger.info("Knowledge graph query engine initialized")
    
    def _build_indices(self):
        """Build indices for faster querying."""
        logger.info("Building knowledge graph indices")
        
        # Build entity index
        self.entity_index = {}
        for entity_id, entity in self.entities.items():
            # Index by text (case-insensitive)
            text = entity['text'].lower()
            if text in self.entity_index:
                self.entity_index[text].append(entity_id)
            else:
                self.entity_index[text] = [entity_id]
            
            # Index by type
            entity_type = entity['type']
            type_key = f"type:{entity_type}"
            if type_key in self.entity_index:
                self.entity_index[type_key].append(entity_id)
            else:
                self.entity_index[type_key] = [entity_id]
        
        # Build relationship index
        self.relationship_index = {}
        for relationship in self.relationships:
            # Index by source
            source = relationship['source']
            if source in self.relationship_index:
                self.relationship_index[source].append(relationship)
            else:
                self.relationship_index[source] = [relationship]
            
            # Index by target
            target = relationship['target']
            if target in self.relationship_index:
                self.relationship_index[target].append(relationship)
            else:
                self.relationship_index[target] = [relationship]
            
            # Index by type
            rel_type = relationship['type']
            type_key = f"type:{rel_type}"
            if type_key in self.relationship_index:
                self.relationship_index[type_key].append(relationship)
            else:
                self.relationship_index[type_key] = [relationship]
    
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
        
        # If no filters, return all entities up to limit
        if not filters:
            return list(self.entities.values())[:limit]
        
        # Apply filters
        results = set(self.entities.keys())
        
        for key, value in filters.items():
            if key == 'type':
                # Filter by entity type
                type_key = f"type:{value}"
                if type_key in self.entity_index:
                    results = results.intersection(set(self.entity_index[type_key]))
                else:
                    results = set()
            elif key == 'text':
                # Filter by entity text
                text = value.lower()
                matching_ids = set()
                for entity_id in results:
                    entity = self.entities[entity_id]
                    if text in entity['text'].lower():
                        matching_ids.add(entity_id)
                results = matching_ids
            elif key == 'property':
                # Filter by entity property
                if isinstance(value, dict):
                    prop_name = value.get('name')
                    prop_value = value.get('value')
                    
                    if prop_name and prop_value:
                        matching_ids = set()
                        for entity_id in results:
                            entity = self.entities[entity_id]
                            if 'properties' in entity and prop_name in entity['properties']:
                                if entity['properties'][prop_name] == prop_value:
                                    matching_ids.add(entity_id)
                        results = matching_ids
        
        # Convert results to entities
        entities = [self.entities[entity_id] for entity_id in results]
        
        # Limit results
        return entities[:limit]
    
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
        
        # If no filters, return all relationships up to limit
        if not filters:
            return self.relationships[:limit]
        
        # Apply filters
        results = self.relationships.copy()
        
        for key, value in filters.items():
            if key == 'type':
                # Filter by relationship type
                results = [r for r in results if r['type'] == value]
            elif key == 'source':
                # Filter by source entity
                results = [r for r in results if r['source'] == value]
            elif key == 'target':
                # Filter by target entity
                results = [r for r in results if r['target'] == value]
            elif key == 'confidence':
                # Filter by minimum confidence
                min_confidence = float(value)
                results = [r for r in results if r.get('confidence', 0.0) >= min_confidence]
        
        # Limit results
        return results[:limit]
    
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
        
        neighbors = []
        
        # Check if entity exists
        if entity_id not in self.entities:
            logger.warning(f"Entity {entity_id} not found")
            return []
        
        # Get relationships for this entity
        if entity_id in self.relationship_index:
            for relationship in self.relationship_index[entity_id]:
                # Check relationship type if specified
                if relationship_type and relationship['type'] != relationship_type:
                    continue
                
                # Check direction
                is_outgoing = relationship['source'] == entity_id
                is_incoming = relationship['target'] == entity_id
                
                if (direction == 'outgoing' and not is_outgoing) or \
                   (direction == 'incoming' and not is_incoming):
                    continue
                
                # Get neighbor entity ID
                neighbor_id = relationship['target'] if is_outgoing else relationship['source']
                
                # Get neighbor entity
                if neighbor_id in self.entities:
                    neighbor = self.entities[neighbor_id]
                    
                    # Add to neighbors list
                    neighbors.append({
                        'entity': neighbor,
                        'relationship': relationship,
                        'direction': 'outgoing' if is_outgoing else 'incoming'
                    })
        
        return neighbors
    
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
        
        # Check if entities exist
        if source_id not in self.entities:
            logger.warning(f"Source entity {source_id} not found")
            return []
        
        if target_id not in self.entities:
            logger.warning(f"Target entity {target_id} not found")
            return []
        
        # Use breadth-first search to find path
        queue = [(source_id, [])]  # (entity_id, path_so_far)
        visited = set([source_id])
        
        while queue:
            current_id, path = queue.pop(0)
            
            # Check if we've reached the target
            if current_id == target_id:
                # Construct full path with entities and relationships
                full_path = []
                for i, item in enumerate(path):
                    if i % 2 == 0:
                        # Entity
                        full_path.append({
                            'type': 'entity',
                            'data': self.entities[item]
                        })
                    else:
                        # Relationship
                        for rel in self.relationships:
                            if rel['id'] == item:
                                full_path.append({
                                    'type': 'relationship',
                                    'data': rel
                                })
                                break
                
                # Add target entity
                full_path.append({
                    'type': 'entity',
                    'data': self.entities[target_id]
                })
                
                return full_path
            
            # Check if we've reached max depth
            if len(path) // 2 >= max_depth:
                continue
            
            # Get neighbors
            neighbors = await self.get_entity_neighbors(current_id)
            
            for neighbor in neighbors:
                neighbor_id = neighbor['entity']['id']
                relationship = neighbor['relationship']
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path + [relationship['id'], neighbor_id]
                    queue.append((neighbor_id, new_path))
        
        # No path found
        return []
    
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
        
        if not self.vector_search_available:
            logger.warning("Vector search not available for semantic search")
            # Fall back to text search
            results = []
            for entity_id, entity in self.entities.items():
                if query.lower() in entity['text'].lower():
                    results.append({
                        'entity': entity,
                        'score': 0.5  # Default score
                    })
            
            # Sort by entity text length (shorter is better)
            results.sort(key=lambda x: len(x['entity']['text']))
            
            return results[:limit]
        
        try:
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Collect entity texts
            entity_texts = []
            entity_ids = []
            
            for entity_id, entity in self.entities.items():
                entity_text = entity['text']
                
                # Add properties if available
                if 'properties' in entity:
                    for prop_name, prop_value in entity['properties'].items():
                        if isinstance(prop_value, str):
                            entity_text += f" {prop_value}"
                
                entity_texts.append(entity_text)
                entity_ids.append(entity_id)
            
            # Add query to texts
            all_texts = entity_texts + [query]
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Get query vector
            query_vector = tfidf_matrix[-1]
            
            # Calculate similarity scores
            similarities = cosine_similarity(query_vector, tfidf_matrix[:-1])[0]
            
            # Create results
            results = []
            for i, entity_id in enumerate(entity_ids):
                score = similarities[i]
                if score > 0:  # Only include non-zero scores
                    results.append({
                        'entity': self.entities[entity_id],
                        'score': float(score)
                    })
            
            # Sort by score (descending)
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            return []
    
    async def get_subgraph(self, entity_ids: List[str], 
                          include_relationships: bool = True,
                          max_relationships: int = 100) -> Dict[str, Any]:
        """
        Get a subgraph containing specified entities and their relationships.
        
        Args:
            entity_ids: List of entity IDs
            include_relationships: Whether to include relationships
            max_relationships: Maximum number of relationships to include
            
        Returns:
            Dictionary containing the subgraph
        """
        logger.info(f"Getting subgraph for {len(entity_ids)} entities")
        
        if not self.initialized:
            await self.initialize()
        
        # Get entities
        entities = {}
        for entity_id in entity_ids:
            if entity_id in self.entities:
                entities[entity_id] = self.entities[entity_id]
        
        # Get relationships if requested
        relationships = []
        if include_relationships:
            # Get relationships between these entities
            relationship_count = 0
            for relationship in self.relationships:
                if relationship['source'] in entities and relationship['target'] in entities:
                    relationships.append(relationship)
                    relationship_count += 1
                    
                    if relationship_count >= max_relationships:
                        break
        
        return {
            'entities': entities,
            'relationships': relationships
        }
    
    async def analyze_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Analyze an entity and its connections.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing entity: {entity_id}")
        
        if not self.initialized:
            await self.initialize()
        
        # Check if entity exists
        if entity_id not in self.entities:
            logger.warning(f"Entity {entity_id} not found")
            return {'error': f"Entity {entity_id} not found"}
        
        entity = self.entities[entity_id]
        
        # Get neighbors
        neighbors = await self.get_entity_neighbors(entity_id)
        
        # Count relationship types
        relationship_counts = {}
        for neighbor in neighbors:
            rel_type = neighbor['relationship']['type']
            if rel_type in relationship_counts:
                relationship_counts[rel_type] += 1
            else:
                relationship_counts[rel_type] = 1
        
        # Count neighbor entity types
        neighbor_type_counts = {}
        for neighbor in neighbors:
            entity_type = neighbor['entity']['type']
            if entity_type in neighbor_type_counts:
                neighbor_type_counts[entity_type] += 1
            else:
                neighbor_type_counts[entity_type] = 1
        
        # Get top connected entities
        top_connected = []
        for neighbor in neighbors:
            neighbor_id = neighbor['entity']['id']
            neighbor_neighbors = await self.get_entity_neighbors(neighbor_id)
            
            top_connected.append({
                'entity': neighbor['entity'],
                'connection_count': len(neighbor_neighbors)
            })
        
        # Sort by connection count
        top_connected.sort(key=lambda x: x['connection_count'], reverse=True)
        
        return {
            'entity': entity,
            'neighbor_count': len(neighbors),
            'relationship_counts': relationship_counts,
            'neighbor_type_counts': neighbor_type_counts,
            'top_connected': top_connected[:5]
        }