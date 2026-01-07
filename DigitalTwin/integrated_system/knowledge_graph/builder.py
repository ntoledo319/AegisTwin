"""
Knowledge graph builder module.

This module provides functionality for building and maintaining a knowledge graph,
including entity extraction, relationship extraction, and graph construction.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import asyncio
import json
import os
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Builder for knowledge graphs."""
    
    def __init__(self):
        """Initialize the knowledge graph builder."""
        self.entities = {}  # Dictionary of entities
        self.relationships = []  # List of relationships
        self.entity_types = set()  # Set of entity types
        self.relationship_types = set()  # Set of relationship types
        self.nlp_available = False
        self.initialized = False
        self.graph_path = "data/knowledge_graph.json"
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for entity extraction")
    
    async def initialize(self):
        """Initialize the knowledge graph builder."""
        logger.info("Initializing knowledge graph builder")
        
        # Try to load graph from file
        if await self._load_graph():
            logger.info("Loaded knowledge graph from file")
        else:
            logger.info("Starting with empty knowledge graph")
        
        self.initialized = True
        logger.info("Knowledge graph builder initialized")
    
    async def _load_graph(self) -> bool:
        """
        Load knowledge graph from file.
        
        Returns:
            True if graph was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.graph_path):
                with open(self.graph_path, 'r') as f:
                    graph_data = json.load(f)
                
                # Load entities
                if 'entities' in graph_data:
                    self.entities = graph_data['entities']
                
                # Load relationships
                if 'relationships' in graph_data:
                    self.relationships = graph_data['relationships']
                
                # Load entity types
                if 'entity_types' in graph_data:
                    self.entity_types = set(graph_data['entity_types'])
                
                # Load relationship types
                if 'relationship_types' in graph_data:
                    self.relationship_types = set(graph_data['relationship_types'])
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {str(e)}")
            return False
    
    async def _save_graph(self):
        """Save knowledge graph to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
            
            # Create graph data
            graph_data = {
                'entities': self.entities,
                'relationships': self.relationships,
                'entity_types': list(self.entity_types),
                'relationship_types': list(self.relationship_types),
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.graph_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            logger.info("Saved knowledge graph to file")
            return True
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {str(e)}")
            return False
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        logger.info("Extracting entities from text")
        
        if not self.initialized:
            await self.initialize()
        
        entities = []
        
        if self.nlp_available:
            try:
                # Process text with spaCy
                doc = self.nlp(text)
                
                # Extract named entities
                for ent in doc.ents:
                    entity = {
                        'text': ent.text,
                        'type': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    }
                    entities.append(entity)
                    
                    # Add entity type to set
                    self.entity_types.add(ent.label_)
            except Exception as e:
                logger.error(f"Error extracting entities: {str(e)}")
        else:
            # Fallback simple extraction
            # Extract potential entities (capitalized words)
            for match in re.finditer(r'\b[A-Z][a-zA-Z]*\b', text):
                entity = {
                    'text': match.group(),
                    'type': 'UNKNOWN',
                    'start': match.start(),
                    'end': match.end()
                }
                entities.append(entity)
                
                # Add entity type to set
                self.entity_types.add('UNKNOWN')
        
        return entities
    
    async def extract_relationships(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities from text.
        
        Args:
            text: Text to extract relationships from
            entities: List of entities
            
        Returns:
            List of extracted relationships
        """
        logger.info("Extracting relationships from text")
        
        if not self.initialized:
            await self.initialize()
        
        relationships = []
        
        if self.nlp_available and len(entities) >= 2:
            try:
                # Process text with spaCy
                doc = self.nlp(text)
                
                # Create entity spans
                entity_spans = []
                for entity in entities:
                    start_char = entity['start']
                    end_char = entity['end']
                    
                    # Find token indices for this span
                    start_token = None
                    end_token = None
                    for i, token in enumerate(doc):
                        if token.idx <= start_char < token.idx + len(token.text):
                            start_token = i
                        if token.idx <= end_char <= token.idx + len(token.text):
                            end_token = i + 1
                            break
                    
                    if start_token is not None and end_token is not None:
                        entity_spans.append((entity, doc[start_token:end_token]))
                
                # Extract relationships between entities
                for i, (entity1, span1) in enumerate(entity_spans):
                    for entity2, span2 in entity_spans[i+1:]:
                        # Skip self-relationships
                        if entity1['text'] == entity2['text']:
                            continue
                        
                        # Find the path between the two entities
                        if span1.root.head == span2.root or span2.root.head == span1.root:
                            # Direct relationship
                            if span1.root.head == span2.root:
                                relation = span2.root.dep_
                                source = entity2
                                target = entity1
                            else:
                                relation = span1.root.dep_
                                source = entity1
                                target = entity2
                            
                            relationship = {
                                'source': source['text'],
                                'source_type': source['type'],
                                'target': target['text'],
                                'target_type': target['type'],
                                'type': relation,
                                'confidence': 0.7
                            }
                            relationships.append(relationship)
                            
                            # Add relationship type to set
                            self.relationship_types.add(relation)
                        else:
                            # Indirect relationship - use a generic relation
                            relationship = {
                                'source': entity1['text'],
                                'source_type': entity1['type'],
                                'target': entity2['text'],
                                'target_type': entity2['type'],
                                'type': 'RELATED_TO',
                                'confidence': 0.3
                            }
                            relationships.append(relationship)
                            
                            # Add relationship type to set
                            self.relationship_types.add('RELATED_TO')
            except Exception as e:
                logger.error(f"Error extracting relationships: {str(e)}")
        
        return relationships
    
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
        
        # Create entity ID
        entity_id = f"{entity_type.lower()}_{entity_text.lower().replace(' ', '_')}"
        
        # Check if entity already exists
        if entity_id in self.entities:
            # Update existing entity
            self.entities[entity_id]['last_updated'] = datetime.now().isoformat()
            
            # Update properties if provided
            if properties:
                if 'properties' not in self.entities[entity_id]:
                    self.entities[entity_id]['properties'] = {}
                
                self.entities[entity_id]['properties'].update(properties)
            
            # Increment mention count
            if 'mention_count' in self.entities[entity_id]:
                self.entities[entity_id]['mention_count'] += 1
            else:
                self.entities[entity_id]['mention_count'] = 1
        else:
            # Create new entity
            self.entities[entity_id] = {
                'id': entity_id,
                'text': entity_text,
                'type': entity_type,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'mention_count': 1
            }
            
            # Add properties if provided
            if properties:
                self.entities[entity_id]['properties'] = properties
        
        # Add entity type to set
        self.entity_types.add(entity_type)
        
        # Save graph
        await self._save_graph()
        
        return self.entities[entity_id]
    
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
        
        # Check if entities exist
        if source_id not in self.entities:
            logger.warning(f"Source entity {source_id} not found")
            return {'error': f"Source entity {source_id} not found"}
        
        if target_id not in self.entities:
            logger.warning(f"Target entity {target_id} not found")
            return {'error': f"Target entity {target_id} not found"}
        
        # Create relationship ID
        relationship_id = f"{source_id}_{relationship_type}_{target_id}"
        
        # Check if relationship already exists
        for relationship in self.relationships:
            if relationship.get('id') == relationship_id:
                # Update existing relationship
                relationship['last_updated'] = datetime.now().isoformat()
                
                # Update properties if provided
                if properties:
                    if 'properties' not in relationship:
                        relationship['properties'] = {}
                    
                    relationship['properties'].update(properties)
                
                # Update confidence if higher
                if confidence > relationship.get('confidence', 0.0):
                    relationship['confidence'] = confidence
                
                # Save graph
                await self._save_graph()
                
                return relationship
        
        # Create new relationship
        relationship = {
            'id': relationship_id,
            'source': source_id,
            'target': target_id,
            'type': relationship_type,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'confidence': confidence
        }
        
        # Add properties if provided
        if properties:
            relationship['properties'] = properties
        
        # Add to relationships list
        self.relationships.append(relationship)
        
        # Add relationship type to set
        self.relationship_types.add(relationship_type)
        
        # Save graph
        await self._save_graph()
        
        return relationship
    
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
        
        # Extract entities
        entities = await self.extract_entities(text)
        
        # Extract relationships
        relationships = await self.extract_relationships(text, entities)
        
        # Add entities to graph
        added_entities = []
        for entity in entities:
            # Create properties from context if available
            properties = {}
            if context:
                properties['context'] = context
            
            # Add entity to graph
            added_entity = await self.add_entity(
                entity_text=entity['text'],
                entity_type=entity['type'],
                properties=properties
            )
            added_entities.append(added_entity)
        
        # Add relationships to graph
        added_relationships = []
        for relationship in relationships:
            # Find source entity ID
            source_id = None
            for entity in added_entities:
                if entity['text'] == relationship['source']:
                    source_id = entity['id']
                    break
            
            # Find target entity ID
            target_id = None
            for entity in added_entities:
                if entity['text'] == relationship['target']:
                    target_id = entity['id']
                    break
            
            if source_id and target_id:
                # Create properties from context if available
                properties = {}
                if context:
                    properties['context'] = context
                
                # Add relationship to graph
                added_relationship = await self.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=relationship['type'],
                    properties=properties,
                    confidence=relationship.get('confidence', 0.5)
                )
                
                if 'error' not in added_relationship:
                    added_relationships.append(added_relationship)
        
        return {
            'entities': added_entities,
            'relationships': added_relationships
        }
    
    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity from the knowledge graph.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity dictionary or None if not found
        """
        logger.info(f"Getting entity: {entity_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None
    
    async def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Get entities by type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            List of entities
        """
        logger.info(f"Getting entities by type: {entity_type}")
        
        if not self.initialized:
            await self.initialize()
        
        entities = []
        for entity_id, entity in self.entities.items():
            if entity['type'] == entity_type:
                entities.append(entity)
        
        return entities
    
    async def get_relationships(self, entity_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relationships for an entity.
        
        Args:
            entity_id: Entity ID
            relationship_type: Relationship type (optional)
            
        Returns:
            List of relationships
        """
        logger.info(f"Getting relationships for entity: {entity_id}")
        
        if not self.initialized:
            await self.initialize()
        
        relationships = []
        for relationship in self.relationships:
            if relationship['source'] == entity_id or relationship['target'] == entity_id:
                if relationship_type is None or relationship['type'] == relationship_type:
                    relationships.append(relationship)
        
        return relationships
    
    async def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """
        Search entities by text.
        
        Args:
            query: Search query
            
        Returns:
            List of matching entities
        """
        logger.info(f"Searching entities: {query}")
        
        if not self.initialized:
            await self.initialize()
        
        query = query.lower()
        entities = []
        
        for entity_id, entity in self.entities.items():
            if query in entity['text'].lower():
                entities.append(entity)
        
        return entities
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dictionary of graph statistics
        """
        logger.info("Getting knowledge graph statistics")
        
        if not self.initialized:
            await self.initialize()
        
        # Count entities by type
        entity_type_counts = {}
        for entity_type in self.entity_types:
            entity_type_counts[entity_type] = 0
        
        for entity in self.entities.values():
            entity_type = entity['type']
            if entity_type in entity_type_counts:
                entity_type_counts[entity_type] += 1
            else:
                entity_type_counts[entity_type] = 1
        
        # Count relationships by type
        relationship_type_counts = {}
        for relationship_type in self.relationship_types:
            relationship_type_counts[relationship_type] = 0
        
        for relationship in self.relationships:
            relationship_type = relationship['type']
            if relationship_type in relationship_type_counts:
                relationship_type_counts[relationship_type] += 1
            else:
                relationship_type_counts[relationship_type] = 1
        
        return {
            'entity_count': len(self.entities),
            'relationship_count': len(self.relationships),
            'entity_types': len(self.entity_types),
            'relationship_types': len(self.relationship_types),
            'entity_type_counts': entity_type_counts,
            'relationship_type_counts': relationship_type_counts
        }