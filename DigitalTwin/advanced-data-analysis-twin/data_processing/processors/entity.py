"""
Entity processor for extracting and linking entities from text.
"""

import re
import string
from typing import Dict, Any, List, Optional, Set, Tuple
import asyncio
import nltk
from nltk.tokenize import word_tokenize
from nltk.chunk import ne_chunk
from collections import Counter

from core.logging import get_logger
from core.utils import generate_id, timestamp_now

logger = get_logger(__name__)

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('chunkers/maxent_ne_chunker')
    nltk.data.find('corpora/words')
except LookupError:
    logger.info("Downloading required NLTK resources...")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class EntityProcessor:
    """
    Processor for extracting and linking entities from text.
    
    This processor provides functionality for:
    - Named entity recognition (people, organizations, locations, etc.)
    - Entity linking and disambiguation
    - Entity relationship extraction
    - Entity metadata enrichment
    - Entity frequency and importance analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the entity processor.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - language: Language code (default: "en")
                - use_spacy: Whether to use spaCy for NER (default: False)
                - min_entity_frequency: Minimum frequency for entity inclusion (default: 1)
                - max_entities: Maximum number of entities to extract (default: 100)
                - entity_types: List of entity types to extract (default: all)
        """
        self.config = config or {}
        self.processor_id = generate_id("entity_processor")
        self.language = self.config.get("language", "en")
        self.use_spacy = self.config.get("use_spacy", False)
        self.min_entity_frequency = self.config.get("min_entity_frequency", 1)
        self.max_entities = self.config.get("max_entities", 100)
        self.entity_types = self.config.get("entity_types", ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "TIME", "MONEY", "PERCENT", "FACILITY", "GPE"])
        
        # Initialize spaCy if enabled
        self.nlp = None
        if self.use_spacy:
            try:
                import spacy
                self.nlp = spacy.load(f"{self.language}_core_web_sm")
                logger.info(f"Loaded spaCy model: {self.language}_core_web_sm")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {str(e)}")
                self.use_spacy = False
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text and extract entities.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary with extracted entities and metadata
        """
        if not text:
            return {
                "entities": [],
                "entity_counts": {},
                "entity_relationships": [],
                "metadata": {
                    "processor_id": self.processor_id,
                    "timestamp": timestamp_now(),
                    "text_length": 0,
                    "processing_time": 0.0
                }
            }
        
        start_time = asyncio.get_event_loop().time()
        
        # Extract entities
        entities = await self.extract_entities(text)
        
        # Count entity occurrences
        entity_counts = self.count_entities(entities)
        
        # Extract entity relationships
        entity_relationships = await self.extract_entity_relationships(text, entities)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "entities": entities,
            "entity_counts": entity_counts,
            "entity_relationships": entity_relationships,
            "metadata": {
                "processor_id": self.processor_id,
                "timestamp": timestamp_now(),
                "text_length": len(text),
                "processing_time": processing_time
            }
        }
    
    async def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Process a batch of texts.
        
        Args:
            texts: List of texts to process
            
        Returns:
            List of dictionaries with extracted entities and metadata
        """
        results = []
        for text in texts:
            result = await self.process_text(text)
            results.append(result)
        return results
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries with text, type, and position
        """
        if not text:
            return []
        
        entities = []
        
        if self.use_spacy and self.nlp:
            # Use spaCy for entity extraction
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in self.entity_types or not self.entity_types:
                    entities.append({
                        "text": ent.text,
                        "type": ent.label_,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "confidence": 0.9  # spaCy doesn't provide confidence scores
                    })
        else:
            # Use NLTK for basic NER
            tokens = word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            current_entity = []
            current_type = None
            current_start = 0
            current_end = 0
            char_index = 0
            
            # Track character positions
            token_positions = []
            char_index = 0
            for token in tokens:
                # Find the token in the original text, starting from char_index
                token_start = text.find(token, char_index)
                if token_start >= 0:
                    token_end = token_start + len(token)
                    token_positions.append((token_start, token_end))
                    char_index = token_end
                else:
                    # If token not found, use the previous end position
                    if token_positions:
                        prev_end = token_positions[-1][1]
                        token_positions.append((prev_end, prev_end + len(token)))
                        char_index = prev_end + len(token)
                    else:
                        token_positions.append((0, len(token)))
                        char_index = len(token)
            
            # Process named entities
            for i, chunk in enumerate(chunks):
                if hasattr(chunk, 'label'):
                    # This is a named entity
                    if current_entity and current_type != chunk.label():
                        # Save previous entity
                        entity_text = ' '.join([word for word, tag in current_entity])
                        if current_entity:
                            start_pos = token_positions[current_start][0]
                            end_pos = token_positions[current_start + len(current_entity) - 1][1]
                            
                            if current_type in self.entity_types or not self.entity_types:
                                entities.append({
                                    "text": entity_text,
                                    "type": current_type,
                                    "start_char": start_pos,
                                    "end_char": end_pos,
                                    "confidence": 0.7
                                })
                        
                        current_entity = []
                        current_start = i
                    
                    if not current_entity:
                        current_start = i
                    
                    current_type = chunk.label()
                    current_entity.extend(chunk.leaves())
                elif current_entity:
                    # Save previous entity
                    entity_text = ' '.join([word for word, tag in current_entity])
                    if current_entity:
                        start_pos = token_positions[current_start][0]
                        end_pos = token_positions[current_start + len(current_entity) - 1][1]
                        
                        if current_type in self.entity_types or not self.entity_types:
                            entities.append({
                                "text": entity_text,
                                "type": current_type,
                                "start_char": start_pos,
                                "end_char": end_pos,
                                "confidence": 0.7
                            })
                    
                    current_entity = []
                    current_type = None
            
            # Save last entity if any
            if current_entity:
                entity_text = ' '.join([word for word, tag in current_entity])
                start_pos = token_positions[current_start][0]
                end_pos = token_positions[current_start + len(current_entity) - 1][1]
                
                if current_type in self.entity_types or not self.entity_types:
                    entities.append({
                        "text": entity_text,
                        "type": current_type,
                        "start_char": start_pos,
                        "end_char": end_pos,
                        "confidence": 0.7
                    })
        
        # Add unique IDs to entities
        for i, entity in enumerate(entities):
            entity["id"] = f"ent_{i}_{generate_id('entity')}"
        
        return entities
    
    def count_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Count entity occurrences by type and text.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dictionary with entity counts by type and text
        """
        entity_counts = {}
        
        # Count by type
        type_counter = Counter([entity["type"] for entity in entities])
        
        # Count by text for each type
        for entity_type in type_counter:
            type_entities = [entity for entity in entities if entity["type"] == entity_type]
            text_counter = Counter([entity["text"].lower() for entity in type_entities])
            
            # Filter by minimum frequency
            text_counter = {text: count for text, count in text_counter.items() if count >= self.min_entity_frequency}
            
            # Sort by frequency and limit to max_entities
            sorted_entities = sorted(text_counter.items(), key=lambda x: x[1], reverse=True)[:self.max_entities]
            
            entity_counts[entity_type] = {
                "count": type_counter[entity_type],
                "entities": dict(sorted_entities)
            }
        
        return entity_counts
    
    async def extract_entity_relationships(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities based on proximity.
        
        Args:
            text: Input text
            entities: List of extracted entities
            
        Returns:
            List of entity relationship dictionaries
        """
        relationships = []
        
        # Sort entities by position
        sorted_entities = sorted(entities, key=lambda x: x["start_char"])
        
        # Look for entities that appear close to each other
        for i, entity1 in enumerate(sorted_entities):
            for j in range(i + 1, len(sorted_entities)):
                entity2 = sorted_entities[j]
                
                # Check if entities are within a reasonable distance (e.g., 100 characters)
                distance = entity2["start_char"] - entity1["end_char"]
                if distance <= 100:
                    # Extract the text between the entities
                    between_text = text[entity1["end_char"]:entity2["start_char"]]
                    
                    # Look for relationship indicators
                    relationship_type = self.determine_relationship_type(between_text)
                    
                    if relationship_type:
                        relationships.append({
                            "source": entity1["id"],
                            "target": entity2["id"],
                            "source_text": entity1["text"],
                            "target_text": entity2["text"],
                            "source_type": entity1["type"],
                            "target_type": entity2["type"],
                            "relationship": relationship_type,
                            "confidence": 0.6
                        })
        
        return relationships
    
    def determine_relationship_type(self, text: str) -> Optional[str]:
        """
        Determine the relationship type based on the text between entities.
        
        Args:
            text: Text between two entities
            
        Returns:
            Relationship type or None if no relationship is detected
        """
        # Clean the text
        text = text.lower().strip()
        
        # Define relationship patterns
        relationship_patterns = {
            "works_for": ["works for", "employed by", "works at", "employee of"],
            "located_in": ["located in", "based in", "situated in", "in the", "from"],
            "associated_with": ["associated with", "related to", "connected to", "linked to"],
            "part_of": ["part of", "member of", "belongs to", "division of"],
            "created_by": ["created by", "developed by", "founded by", "established by"],
            "owns": ["owns", "possesses", "has", "holds", "acquired"],
            "leads": ["leads", "directs", "manages", "heads", "runs", "ceo of", "president of"],
            "reports_to": ["reports to", "supervised by", "managed by", "directed by"],
            "married_to": ["married to", "spouse of", "husband of", "wife of"],
            "parent_of": ["parent of", "father of", "mother of", "son of", "daughter of"],
            "born_in": ["born in", "native of", "originated from"],
            "died_in": ["died in", "passed away in", "deceased in"],
            "founded": ["founded", "established", "created", "started", "launched"],
            "acquired": ["acquired", "purchased", "bought", "took over"],
            "collaborated_with": ["collaborated with", "worked with", "partnered with"],
            "competed_with": ["competed with", "rival of", "competitor to"],
            "succeeded": ["succeeded", "followed", "replaced", "came after"],
            "preceded": ["preceded", "came before", "was before"]
        }
        
        # Check for relationship patterns
        for relationship, patterns in relationship_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return relationship
        
        # If no specific relationship is found, but entities are close, assume a generic association
        if len(text) < 20:
            return "associated_with"
        
        return None
    
    async def enrich_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich entities with additional metadata.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            List of enriched entity dictionaries
        """
        # This is a placeholder for entity enrichment
        # In a real implementation, this would connect to knowledge bases or APIs
        # to add additional information about entities
        
        enriched_entities = []
        
        for entity in entities:
            enriched_entity = entity.copy()
            
            # Add entity metadata based on type
            if entity["type"] == "PERSON":
                enriched_entity["metadata"] = {
                    "category": "person",
                    "importance": 0.8 if entity["confidence"] > 0.8 else 0.5
                }
            elif entity["type"] == "ORGANIZATION":
                enriched_entity["metadata"] = {
                    "category": "organization",
                    "importance": 0.7 if entity["confidence"] > 0.8 else 0.4
                }
            elif entity["type"] == "LOCATION" or entity["type"] == "GPE":
                enriched_entity["metadata"] = {
                    "category": "location",
                    "importance": 0.6 if entity["confidence"] > 0.8 else 0.3
                }
            elif entity["type"] == "DATE" or entity["type"] == "TIME":
                enriched_entity["metadata"] = {
                    "category": "temporal",
                    "importance": 0.5 if entity["confidence"] > 0.8 else 0.2
                }
            else:
                enriched_entity["metadata"] = {
                    "category": "other",
                    "importance": 0.4 if entity["confidence"] > 0.8 else 0.1
                }
            
            enriched_entities.append(enriched_entity)
        
        return enriched_entities