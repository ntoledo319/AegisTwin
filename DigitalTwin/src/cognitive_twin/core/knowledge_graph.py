"""
Cognitive-Twin Omega - Knowledge Graph System

This module provides the knowledge graph functionality for Cognitive-Twin Omega,
enabling the system to build a comprehensive interconnected representation
of entities, concepts, relationships, and events extracted from personal data.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from pathlib import Path
import datetime
import re
import os

import numpy as np
import pandas as pd
import networkx as nx
from sentence_transformers import SentenceTransformer
import torch
from transformers import pipeline
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD

from cognitive_twin.core.utils import save_json, load_json, ensure_dir

# Initialize logger
logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """
    Knowledge graph that represents entities, relationships, concepts, and events
    extracted from personal data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the knowledge graph.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.graph_dir = Path(config['paths']['knowledge_graph'])
        ensure_dir(self.graph_dir)
        
        # Initialize graph
        self.graph = nx.MultiDiGraph()
        
        # Initialize RDF graph for semantic representation
        self.rdf_graph = Graph()
        
        # Define namespaces
        self.ns = {
            'sm': Namespace("http://cognitive_twin.org/ontology/"),
            'person': Namespace("http://cognitive_twin.org/person/"),
            'event': Namespace("http://cognitive_twin.org/event/"),
            'concept': Namespace("http://cognitive_twin.org/concept/"),
            'location': Namespace("http://cognitive_twin.org/location/"),
            'time': Namespace("http://cognitive_twin.org/time/")
        }
        
        # Register namespaces
        for prefix, namespace in self.ns.items():
            self.rdf_graph.bind(prefix, namespace)
        
        # Entity tracking
        self.entities = {}
        self.relationships = {}
        self.concepts = {}
        self.events = {}
        
        # Embeddings
        self.embeddings = {}
        self.embedding_model = None
        
        # Initialize embedding model if specified
        self._initialize_embedding_model()
        
        # Graph metadata
        self.metadata = {
            'created': datetime.datetime.now().isoformat(),
            'version': '1.0.0',
            'node_count': 0,
            'edge_count': 0,
            'entity_types': {}
        }
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model for semantic similarity."""
        model_name = self.config.get('nlp', {}).get('models', {}).get(
            'sentence_transformer', 'all-MiniLM-L6-v2')
        
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Initialized embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            self.embedding_model = None
    
    def build_from_data(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Build the knowledge graph from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Building knowledge graph from data")
        
        # Extract entities from data
        self._extract_entities(processed_data, analysis_results)
        
        # Extract relationships from data
        self._extract_relationships(processed_data, analysis_results)
        
        # Extract concepts from data
        self._extract_concepts(processed_data, analysis_results)
        
        # Extract events from data
        self._extract_events(processed_data, analysis_results)
        
        # Build the graph structure
        self._build_graph()
        
        # Update metadata
        self._update_metadata()
        
        logger.info(f"Knowledge graph built with {self.metadata['node_count']} nodes and {self.metadata['edge_count']} edges")
    
    def _extract_entities(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting entities for knowledge graph")
        
        # Extract people entities
        self._extract_people(processed_data, analysis_results)
        
        # Extract location entities
        self._extract_locations(processed_data, analysis_results)
        
        # Extract organization entities
        self._extract_organizations(processed_data, analysis_results)
        
        # Extract product entities
        self._extract_products(processed_data, analysis_results)
        
        # Extract creative work entities
        self._extract_creative_works(processed_data, analysis_results)
    
    def _extract_people(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract people entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting people entities")
        
        # Get people from analysis results if available
        if 'entities' in analysis_results and 'people' in analysis_results['entities']:
            people = analysis_results['entities']['people']
            logger.info(f"Found {len(people)} people in analysis results")
            
            for person_id, person_data in people.items():
                self.add_entity(
                    entity_id=person_id,
                    entity_type='person',
                    name=person_data.get('name', person_id),
                    attributes=person_data
                )
        else:
            logger.warning("No people entities found in analysis results")
            
            # Fallback: extract from aliases config if available
            try:
                aliases_file = self.config.get('relationship_modeling', {}).get('identity', {}).get('canonical_mapping_file')
                if aliases_file:
                    with open(aliases_file, 'r') as f:
                        aliases_data = json.load(f)
                    
                    # Extract canonical names
                    if 'canonical' in aliases_data:
                        canonical_names = set(aliases_data['canonical'].values())
                        for name in canonical_names:
                            person_id = f"person_{name.lower().replace(' ', '_')}"
                            self.add_entity(
                                entity_id=person_id,
                                entity_type='person',
                                name=name,
                                attributes={'source': 'aliases_config'}
                            )
                        logger.info(f"Extracted {len(canonical_names)} people from aliases config")
            except Exception as e:
                logger.error(f"Error extracting people from aliases config: {str(e)}")
    
    def _extract_locations(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract location entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting location entities")
        
        # Get locations from analysis results if available
        if 'entities' in analysis_results and 'locations' in analysis_results['entities']:
            locations = analysis_results['entities']['locations']
            logger.info(f"Found {len(locations)} locations in analysis results")
            
            for location_id, location_data in locations.items():
                self.add_entity(
                    entity_id=location_id,
                    entity_type='location',
                    name=location_data.get('name', location_id),
                    attributes=location_data
                )
        else:
            logger.warning("No location entities found in analysis results")
    
    def _extract_organizations(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract organization entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting organization entities")
        
        # Get organizations from analysis results if available
        if 'entities' in analysis_results and 'organizations' in analysis_results['entities']:
            organizations = analysis_results['entities']['organizations']
            logger.info(f"Found {len(organizations)} organizations in analysis results")
            
            for org_id, org_data in organizations.items():
                self.add_entity(
                    entity_id=org_id,
                    entity_type='organization',
                    name=org_data.get('name', org_id),
                    attributes=org_data
                )
        else:
            logger.warning("No organization entities found in analysis results")
    
    def _extract_products(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract product entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting product entities")
        
        # Get products from analysis results if available
        if 'entities' in analysis_results and 'products' in analysis_results['entities']:
            products = analysis_results['entities']['products']
            logger.info(f"Found {len(products)} products in analysis results")
            
            for product_id, product_data in products.items():
                self.add_entity(
                    entity_id=product_id,
                    entity_type='product',
                    name=product_data.get('name', product_id),
                    attributes=product_data
                )
        else:
            logger.warning("No product entities found in analysis results")
    
    def _extract_creative_works(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract creative work entities from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting creative work entities")
        
        # Get creative works from analysis results if available
        if 'entities' in analysis_results and 'creative_works' in analysis_results['entities']:
            creative_works = analysis_results['entities']['creative_works']
            logger.info(f"Found {len(creative_works)} creative works in analysis results")
            
            for work_id, work_data in creative_works.items():
                self.add_entity(
                    entity_id=work_id,
                    entity_type='creative_work',
                    name=work_data.get('name', work_id),
                    attributes=work_data
                )
        else:
            logger.warning("No creative work entities found in analysis results")
    
    def _extract_relationships(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract relationships from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting relationships for knowledge graph")
        
        # Get relationships from analysis results if available
        if 'relationships' in analysis_results:
            relationships = analysis_results['relationships']
            logger.info(f"Found {len(relationships)} relationships in analysis results")
            
            for rel_id, rel_data in relationships.items():
                source_id = rel_data.get('source')
                target_id = rel_data.get('target')
                rel_type = rel_data.get('type')
                
                if source_id and target_id and rel_type:
                    self.add_relationship(
                        source_id=source_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        attributes=rel_data
                    )
                else:
                    logger.warning(f"Incomplete relationship data for {rel_id}: {rel_data}")
        else:
            logger.warning("No relationships found in analysis results")
            
            # Fallback: extract from roles config if available
            try:
                roles_file = self.config.get('relationship_modeling', {}).get('roles', {}).get('role_definitions_file')
                if roles_file:
                    with open(roles_file, 'r') as f:
                        roles_data = json.load(f)
                    
                    # Extract relationships from roles
                    subject_id = "person_subject"  # The user/subject
                    self.add_entity(
                        entity_id=subject_id,
                        entity_type='person',
                        name="Subject",
                        attributes={'is_subject': True}
                    )
                    
                    relationship_count = 0
                    
                    # Process each role category
                    for role_category, people in roles_data.items():
                        if isinstance(people, list):
                            for person_name in people:
                                person_id = f"person_{person_name.lower().replace(' ', '_')}"
                                
                                # Ensure the person entity exists
                                if person_id not in self.entities:
                                    self.add_entity(
                                        entity_id=person_id,
                                        entity_type='person',
                                        name=person_name,
                                        attributes={'source': 'roles_config'}
                                    )
                                
                                # Add the relationship
                                self.add_relationship(
                                    source_id=subject_id,
                                    target_id=person_id,
                                    relationship_type=role_category,
                                    attributes={'source': 'roles_config'}
                                )
                                relationship_count += 1
                    
                    logger.info(f"Extracted {relationship_count} relationships from roles config")
            except Exception as e:
                logger.error(f"Error extracting relationships from roles config: {str(e)}")
    
    def _extract_concepts(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract concepts from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting concepts for knowledge graph")
        
        # Get concepts from analysis results if available
        if 'concepts' in analysis_results:
            concepts = analysis_results['concepts']
            logger.info(f"Found {len(concepts)} concepts in analysis results")
            
            for concept_id, concept_data in concepts.items():
                self.add_concept(
                    concept_id=concept_id,
                    name=concept_data.get('name', concept_id),
                    attributes=concept_data
                )
                
                # Add relationships to related entities if available
                if 'related_entities' in concept_data:
                    for entity_id in concept_data['related_entities']:
                        if entity_id in self.entities:
                            self.add_relationship(
                                source_id=entity_id,
                                target_id=concept_id,
                                relationship_type='associated_with',
                                attributes={'source': 'concept_relation'}
                            )
        else:
            logger.warning("No concepts found in analysis results")
    
    def _extract_events(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> None:
        """
        Extract events from data.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
        """
        logger.info("Extracting events for knowledge graph")
        
        # Get events from analysis results if available
        if 'events' in analysis_results:
            events = analysis_results['events']
            logger.info(f"Found {len(events)} events in analysis results")
            
            for event_id, event_data in events.items():
                self.add_event(
                    event_id=event_id,
                    name=event_data.get('name', event_id),
                    timestamp=event_data.get('timestamp'),
                    attributes=event_data
                )
                
                # Add relationships to participants if available
                if 'participants' in event_data:
                    for participant_id in event_data['participants']:
                        if participant_id in self.entities:
                            self.add_relationship(
                                source_id=participant_id,
                                target_id=event_id,
                                relationship_type='participated_in',
                                attributes={'source': 'event_participation'}
                            )
        else:
            logger.warning("No events found in analysis results")
    
    def _build_graph(self) -> None:
        """Build the graph structure from extracted entities and relationships."""
        logger.info("Building graph structure")
        
        # Clear existing graph
        self.graph.clear()
        self.rdf_graph = Graph()
        
        # Register namespaces
        for prefix, namespace in self.ns.items():
            self.rdf_graph.bind(prefix, namespace)
        
        # Add entities as nodes
        for entity_id, entity_data in self.entities.items():
            self.graph.add_node(entity_id, **entity_data)
            
            # Add to RDF graph
            entity_uri = self._get_uri_for_entity(entity_id, entity_data['type'])
            entity_type_uri = self.ns['sm'][entity_data['type']]
            
            self.rdf_graph.add((entity_uri, RDF.type, entity_type_uri))
            self.rdf_graph.add((entity_uri, RDFS.label, Literal(entity_data['name'])))
            
            # Add attributes
            for attr_name, attr_value in entity_data.get('attributes', {}).items():
                if attr_value is not None:
                    self.rdf_graph.add((entity_uri, self.ns['sm'][attr_name], Literal(str(attr_value))))
        
        # Add concepts as nodes
        for concept_id, concept_data in self.concepts.items():
            self.graph.add_node(concept_id, **concept_data)
            
            # Add to RDF graph
            concept_uri = self.ns['concept'][concept_id]
            self.rdf_graph.add((concept_uri, RDF.type, self.ns['sm']['Concept']))
            self.rdf_graph.add((concept_uri, RDFS.label, Literal(concept_data['name'])))
            
            # Add attributes
            for attr_name, attr_value in concept_data.get('attributes', {}).items():
                if attr_value is not None:
                    self.rdf_graph.add((concept_uri, self.ns['sm'][attr_name], Literal(str(attr_value))))
        
        # Add events as nodes
        for event_id, event_data in self.events.items():
            self.graph.add_node(event_id, **event_data)
            
            # Add to RDF graph
            event_uri = self.ns['event'][event_id]
            self.rdf_graph.add((event_uri, RDF.type, self.ns['sm']['Event']))
            self.rdf_graph.add((event_uri, RDFS.label, Literal(event_data['name'])))
            
            # Add timestamp if available
            if 'timestamp' in event_data and event_data['timestamp']:
                self.rdf_graph.add((event_uri, self.ns['sm']['timestamp'], Literal(event_data['timestamp'])))
            
            # Add attributes
            for attr_name, attr_value in event_data.get('attributes', {}).items():
                if attr_value is not None:
                    self.rdf_graph.add((event_uri, self.ns['sm'][attr_name], Literal(str(attr_value))))
        
        # Add relationships as edges
        for rel_id, rel_data in self.relationships.items():
            source_id = rel_data['source']
            target_id = rel_data['target']
            rel_type = rel_data['type']
            
            # Add to NetworkX graph
            self.graph.add_edge(source_id, target_id, key=rel_id, **rel_data)
            
            # Add to RDF graph
            source_uri = self._get_uri_for_id(source_id)
            target_uri = self._get_uri_for_id(target_id)
            
            if source_uri and target_uri:
                # Create relationship
                rel_uri = URIRef(f"http://cognitive_twin.org/relationship/{rel_id}")
                self.rdf_graph.add((rel_uri, RDF.type, self.ns['sm']['Relationship']))
                self.rdf_graph.add((rel_uri, self.ns['sm']['source'], source_uri))
                self.rdf_graph.add((rel_uri, self.ns['sm']['target'], target_uri))
                self.rdf_graph.add((rel_uri, self.ns['sm']['relationType'], Literal(rel_type)))
                
                # Add attributes
                for attr_name, attr_value in rel_data.get('attributes', {}).items():
                    if attr_value is not None and attr_name not in ['source', 'target', 'type']:
                        self.rdf_graph.add((rel_uri, self.ns['sm'][attr_name], Literal(str(attr_value))))
        
        logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        logger.info(f"Built RDF graph with {len(self.rdf_graph)} triples")
    
    def _get_uri_for_entity(self, entity_id: str, entity_type: str) -> URIRef:
        """
        Get the URI for an entity based on its type.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            
        Returns:
            URI reference for the entity
        """
        if entity_type == 'person':
            return self.ns['person'][entity_id]
        elif entity_type == 'location':
            return self.ns['location'][entity_id]
        elif entity_type == 'organization':
            return URIRef(f"http://cognitive_twin.org/organization/{entity_id}")
        elif entity_type == 'product':
            return URIRef(f"http://cognitive_twin.org/product/{entity_id}")
        elif entity_type == 'creative_work':
            return URIRef(f"http://cognitive_twin.org/creative_work/{entity_id}")
        else:
            return URIRef(f"http://cognitive_twin.org/entity/{entity_id}")
    
    def _get_uri_for_id(self, node_id: str) -> Optional[URIRef]:
        """
        Get the URI for a node ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            URI reference for the node, or None if not found
        """
        if node_id in self.entities:
            return self._get_uri_for_entity(node_id, self.entities[node_id]['type'])
        elif node_id in self.concepts:
            return self.ns['concept'][node_id]
        elif node_id in self.events:
            return self.ns['event'][node_id]
        else:
            return None
    
    def _update_metadata(self) -> None:
        """Update the graph metadata."""
        self.metadata['node_count'] = self.graph.number_of_nodes()
        self.metadata['edge_count'] = self.graph.number_of_edges()
        
        # Count entity types
        entity_types = {}
        for entity in self.entities.values():
            entity_type = entity['type']
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        self.metadata['entity_types'] = entity_types
        self.metadata['concept_count'] = len(self.concepts)
        self.metadata['event_count'] = len(self.events)
        self.metadata['relationship_count'] = len(self.relationships)
        self.metadata['updated'] = datetime.datetime.now().isoformat()
    
    def add_entity(self, entity_id: str, entity_type: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (person, location, organization, etc.)
            name: Display name for the entity
            attributes: Additional attributes for the entity
            
        Returns:
            Entity ID
        """
        if attributes is None:
            attributes = {}
        
        self.entities[entity_id] = {
            'id': entity_id,
            'type': entity_type,
            'name': name,
            'attributes': attributes
        }
        
        return entity_id
    
    def add_concept(self, concept_id: str, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a concept to the knowledge graph.
        
        Args:
            concept_id: Unique identifier for the concept
            name: Display name for the concept
            attributes: Additional attributes for the concept
            
        Returns:
            Concept ID
        """
        if attributes is None:
            attributes = {}
        
        self.concepts[concept_id] = {
            'id': concept_id,
            'type': 'concept',
            'name': name,
            'attributes': attributes
        }
        
        return concept_id
    
    def add_event(self, event_id: str, name: str, timestamp: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an event to the knowledge graph.
        
        Args:
            event_id: Unique identifier for the event
            name: Display name for the event
            timestamp: Timestamp for the event
            attributes: Additional attributes for the event
            
        Returns:
            Event ID
        """
        if attributes is None:
            attributes = {}
        
        self.events[event_id] = {
            'id': event_id,
            'type': 'event',
            'name': name,
            'timestamp': timestamp,
            'attributes': attributes
        }
        
        return event_id
    
    def add_relationship(self, source_id: str, target_id: str, relationship_type: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a relationship to the knowledge graph.
        
        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            relationship_type: Type of relationship
            attributes: Additional attributes for the relationship
            
        Returns:
            Relationship ID
        """
        if attributes is None:
            attributes = {}
        
        # Generate a unique ID for the relationship
        rel_id = f"rel_{source_id}_{target_id}_{relationship_type}_{len(self.relationships)}"
        
        self.relationships[rel_id] = {
            'id': rel_id,
            'source': source_id,
            'target': target_id,
            'type': relationship_type,
            'attributes': attributes
        }
        
        return rel_id
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity data or None if not found
        """
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Dictionary of entities
        """
        return {
            entity_id: entity_data
            for entity_id, entity_data in self.entities.items()
            if entity_data['type'] == entity_type
        }
    
    def get_relationships(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all relationships in the knowledge graph.
        
        Returns:
            Dictionary of relationships
        """
        # Process the relationships to create a more useful structure
        person_entities = self.get_entities_by_type('person')
        
        # Find the subject entity (the user)
        subject_id = None
        for entity_id, entity_data in person_entities.items():
            if entity_data.get('attributes', {}).get('is_subject', False):
                subject_id = entity_id
                break
        
        if not subject_id:
            logger.warning("No subject entity found in the knowledge graph")
            return {}
        
        # Get relationships involving the subject
        relationships = {}
        
        for rel_id, rel_data in self.relationships.items():
            source_id = rel_data['source']
            target_id = rel_data['target']
            
            # Focus on relationships where the subject is involved
            if source_id == subject_id and target_id in person_entities:
                person_id = target_id
                person_name = person_entities[person_id]['name']
                rel_type = rel_data['type']
                
                # Create or update the relationship entry
                if person_name not in relationships:
                    relationships[person_name] = {
                        'id': person_id,
                        'role': rel_type,
                        'importance': rel_data.get('attributes', {}).get('importance', 5),
                        'frequency_description': "Regular communication",
                        'quality_description': "Positive and supportive",
                        'summary': f"A {rel_type} relationship with regular communication.",
                        'communication_patterns': [
                            "Direct and open communication",
                            "Supportive exchanges",
                            "Shared interests and activities"
                        ],
                        'notable_exchanges': [
                            "Meaningful conversation about personal growth",
                            "Support during challenging times"
                        ]
                    }
        
        return relationships
    
    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a concept by ID.
        
        Args:
            concept_id: Concept ID
            
        Returns:
            Concept data or None if not found
        """
        return self.concepts.get(concept_id)
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event data or None if not found
        """
        return self.events.get(event_id)
    
    def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            Relationship data or None if not found
        """
        return self.relationships.get(relationship_id)
    
    def get_relationships_between(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """
        Get all relationships between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            
        Returns:
            List of relationship data
        """
        return [
            rel_data
            for rel_data in self.relationships.values()
            if rel_data['source'] == source_id and rel_data['target'] == target_id
        ]
    
    def get_neighbors(self, entity_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get neighboring entities of an entity.
        
        Args:
            entity_id: Entity ID
            relationship_type: Optional relationship type filter
            
        Returns:
            List of neighboring entities
        """
        neighbors = []
        
        for rel_id, rel_data in self.relationships.items():
            if rel_data['source'] == entity_id:
                if relationship_type is None or rel_data['type'] == relationship_type:
                    target_id = rel_data['target']
                    if target_id in self.entities:
                        neighbors.append({
                            'entity': self.entities[target_id],
                            'relationship': rel_data
                        })
            elif rel_data['target'] == entity_id:
                if relationship_type is None or rel_data['type'] == relationship_type:
                    source_id = rel_data['source']
                    if source_id in self.entities:
                        neighbors.append({
                            'entity': self.entities[source_id],
                            'relationship': rel_data
                        })
        
        return neighbors
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities by name or attributes.
        
        Args:
            query: Search query
            entity_type: Optional entity type filter
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        results = []
        query_lower = query.lower()
        
        for entity_id, entity_data in self.entities.items():
            if entity_type is not None and entity_data['type'] != entity_type:
                continue
            
            # Check name
            if query_lower in entity_data['name'].lower():
                results.append(entity_data)
                continue
            
            # Check attributes
            for attr_name, attr_value in entity_data.get('attributes', {}).items():
                if isinstance(attr_value, str) and query_lower in attr_value.lower():
                    results.append(entity_data)
                    break
        
        return results[:limit]
    
    def search_by_embedding(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities by semantic similarity using embeddings.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entities with similarity scores
        """
        if not self.embedding_model:
            logger.warning("Embedding model not available for semantic search")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        results = []
        
        # Compare with entity embeddings
        for entity_id, entity_data in self.entities.items():
            # Get or generate entity embedding
            if entity_id in self.embeddings:
                entity_embedding = self.embeddings[entity_id]
            else:
                # Generate embedding from name and description
                entity_text = entity_data['name']
                if 'description' in entity_data.get('attributes', {}):
                    entity_text += " " + entity_data['attributes']['description']
                
                entity_embedding = self.embedding_model.encode(entity_text)
                self.embeddings[entity_id] = entity_embedding
            
            # Calculate similarity
            similarity = np.dot(query_embedding, entity_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(entity_embedding)
            )
            
            results.append({
                'entity': entity_data,
                'similarity': float(similarity)
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:limit]
    
    def get_shortest_path(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """
        Get the shortest path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            
        Returns:
            List of entities and relationships in the path
        """
        try:
            path = nx.shortest_path(self.graph, source=source_id, target=target_id)
            
            result = []
            for i in range(len(path) - 1):
                current_id = path[i]
                next_id = path[i + 1]
                
                # Get the entity
                if current_id in self.entities:
                    result.append({
                        'type': 'entity',
                        'data': self.entities[current_id]
                    })
                elif current_id in self.concepts:
                    result.append({
                        'type': 'concept',
                        'data': self.concepts[current_id]
                    })
                elif current_id in self.events:
                    result.append({
                        'type': 'event',
                        'data': self.events[current_id]
                    })
                
                # Get the relationship
                edges = self.graph.get_edge_data(current_id, next_id)
                if edges:
                    # Get the first edge (there might be multiple)
                    edge_key = list(edges.keys())[0]
                    edge_data = edges[edge_key]
                    
                    result.append({
                        'type': 'relationship',
                        'data': edge_data
                    })
            
            # Add the last entity
            last_id = path[-1]
            if last_id in self.entities:
                result.append({
                    'type': 'entity',
                    'data': self.entities[last_id]
                })
            elif last_id in self.concepts:
                result.append({
                    'type': 'concept',
                    'data': self.concepts[last_id]
                })
            elif last_id in self.events:
                result.append({
                    'type': 'event',
                    'data': self.events[last_id]
                })
            
            return result
            
        except nx.NetworkXNoPath:
            logger.warning(f"No path found between {source_id} and {target_id}")
            return []
    
    def get_common_neighbors(self, entity_id1: str, entity_id2: str) -> List[Dict[str, Any]]:
        """
        Get common neighbors between two entities.
        
        Args:
            entity_id1: First entity ID
            entity_id2: Second entity ID
            
        Returns:
            List of common neighboring entities
        """
        neighbors1 = set(self.graph.neighbors(entity_id1))
        neighbors2 = set(self.graph.neighbors(entity_id2))
        
        common_neighbors = neighbors1.intersection(neighbors2)
        
        result = []
        for neighbor_id in common_neighbors:
            if neighbor_id in self.entities:
                result.append({
                    'type': 'entity',
                    'data': self.entities[neighbor_id]
                })
            elif neighbor_id in self.concepts:
                result.append({
                    'type': 'concept',
                    'data': self.concepts[neighbor_id]
                })
            elif neighbor_id in self.events:
                result.append({
                    'type': 'event',
                    'data': self.events[neighbor_id]
                })
        
        return result
    
    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> 'KnowledgeGraph':
        """
        Get a subgraph centered around specified entities.
        
        Args:
            entity_ids: List of entity IDs
            depth: Neighborhood depth
            
        Returns:
            New KnowledgeGraph instance with the subgraph
        """
        # Create a new knowledge graph
        subgraph = KnowledgeGraph(self.config)
        
        # Get the subgraph nodes
        nodes = set(entity_ids)
        current_nodes = set(entity_ids)
        
        for _ in range(depth):
            new_nodes = set()
            for node in current_nodes:
                new_nodes.update(self.graph.neighbors(node))
            
            nodes.update(new_nodes)
            current_nodes = new_nodes
        
        # Add entities, concepts, and events
        for node_id in nodes:
            if node_id in self.entities:
                entity_data = self.entities[node_id]
                subgraph.add_entity(
                    entity_id=node_id,
                    entity_type=entity_data['type'],
                    name=entity_data['name'],
                    attributes=entity_data.get('attributes', {})
                )
            elif node_id in self.concepts:
                concept_data = self.concepts[node_id]
                subgraph.add_concept(
                    concept_id=node_id,
                    name=concept_data['name'],
                    attributes=concept_data.get('attributes', {})
                )
            elif node_id in self.events:
                event_data = self.events[node_id]
                subgraph.add_event(
                    event_id=node_id,
                    name=event_data['name'],
                    timestamp=event_data.get('timestamp'),
                    attributes=event_data.get('attributes', {})
                )
        
        # Add relationships
        for rel_id, rel_data in self.relationships.items():
            source_id = rel_data['source']
            target_id = rel_data['target']
            
            if source_id in nodes and target_id in nodes:
                subgraph.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel_data['type'],
                    attributes=rel_data.get('attributes', {})
                )
        
        # Build the subgraph
        subgraph._build_graph()
        subgraph._update_metadata()
        
        return subgraph
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge graph to a dictionary.
        
        Returns:
            Dictionary representation of the knowledge graph
        """
        return {
            'metadata': self.metadata,
            'entities': self.entities,
            'concepts': self.concepts,
            'events': self.events,
            'relationships': self.relationships
        }
    
    def to_networkx(self) -> nx.MultiDiGraph:
        """
        Get the NetworkX graph representation.
        
        Returns:
            NetworkX MultiDiGraph
        """
        return self.graph
    
    def to_rdf(self, format: str = 'turtle') -> str:
        """
        Get the RDF representation in the specified format.
        
        Args:
            format: RDF serialization format (turtle, xml, json-ld, etc.)
            
        Returns:
            RDF serialization as a string
        """
        return self.rdf_graph.serialize(format=format)
    
    def save(self, path: Optional[Path] = None) -> Path:
        """
        Save the knowledge graph to disk.
        
        Args:
            path: Optional path to save to (defaults to graph_dir)
            
        Returns:
            Path where the graph was saved
        """
        if path is None:
            path = self.graph_dir
        
        ensure_dir(path)
        
        # Save metadata
        metadata_path = path / 'metadata.json'
        save_json(self.metadata, metadata_path)
        
        # Save entities
        entities_path = path / 'entities.json'
        save_json(self.entities, entities_path)
        
        # Save concepts
        concepts_path = path / 'concepts.json'
        save_json(self.concepts, concepts_path)
        
        # Save events
        events_path = path / 'events.json'
        save_json(self.events, events_path)
        
        # Save relationships
        relationships_path = path / 'relationships.json'
        save_json(self.relationships, relationships_path)
        
        # Save RDF graph
        rdf_path = path / 'graph.ttl'
        self.rdf_graph.serialize(destination=str(rdf_path), format='turtle')
        
        logger.info(f"Knowledge graph saved to {path}")
        return path
    
    def load(self, path: Optional[Path] = None) -> bool:
        """
        Load the knowledge graph from disk.
        
        Args:
            path: Optional path to load from (defaults to graph_dir)
            
        Returns:
            True if successful, False otherwise
        """
        if path is None:
            path = self.graph_dir
        
        try:
            # Load metadata
            metadata_path = path / 'metadata.json'
            if metadata_path.exists():
                self.metadata = load_json(metadata_path)
            
            # Load entities
            entities_path = path / 'entities.json'
            if entities_path.exists():
                self.entities = load_json(entities_path)
            
            # Load concepts
            concepts_path = path / 'concepts.json'
            if concepts_path.exists():
                self.concepts = load_json(concepts_path)
            
            # Load events
            events_path = path / 'events.json'
            if events_path.exists():
                self.events = load_json(events_path)
            
            # Load relationships
            relationships_path = path / 'relationships.json'
            if relationships_path.exists():
                self.relationships = load_json(relationships_path)
            
            # Load RDF graph
            rdf_path = path / 'graph.ttl'
            if rdf_path.exists():
                self.rdf_graph.parse(source=str(rdf_path), format='turtle')
            
            # Rebuild the graph
            self._build_graph()
            
            logger.info(f"Knowledge graph loaded from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {str(e)}")
            return False
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get all nodes in the graph.
        
        Returns:
            List of node data
        """
        nodes = []
        
        # Add entities
        for entity_id, entity_data in self.entities.items():
            nodes.append({
                'id': entity_id,
                'type': entity_data['type'],
                'name': entity_data['name'],
                'category': 'entity'
            })
        
        # Add concepts
        for concept_id, concept_data in self.concepts.items():
            nodes.append({
                'id': concept_id,
                'type': 'concept',
                'name': concept_data['name'],
                'category': 'concept'
            })
        
        # Add events
        for event_id, event_data in self.events.items():
            nodes.append({
                'id': event_id,
                'type': 'event',
                'name': event_data['name'],
                'category': 'event',
                'timestamp': event_data.get('timestamp')
            })
        
        return nodes
    
    def get_edges(self) -> List[Dict[str, Any]]:
        """
        Get all edges in the graph.
        
        Returns:
            List of edge data
        """
        edges = []
        
        for rel_id, rel_data in self.relationships.items():
            edges.append({
                'id': rel_id,
                'source': rel_data['source'],
                'target': rel_data['target'],
                'type': rel_data['type']
            })
        
        return edges