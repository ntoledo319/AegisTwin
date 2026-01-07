"""
Semantic Memory for the Digital Twin.

This module provides functionality for storing and retrieving semantic memories,
which are memories of facts, concepts, and knowledge.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
import datetime

logger = logging.getLogger(__name__)


class SemanticMemory:
    """
    Module for managing semantic memories.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the semantic memory module.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.memory_dir = self.config.get("semantic_memory_dir", "semantic_memories")
        self.mongodb = None
        self._initialize_mongodb()
        logger.info("Semantic Memory module initialized")

    def _initialize_mongodb(self) -> None:
        """
        Initialize MongoDB connection for memory storage.
        """
        try:
            # Try to import the MongoDB client
            from ....core.db.mongodb import MongoDBClient
            
            # Initialize the MongoDB client
            self.mongodb = MongoDBClient()
            logger.info("MongoDB client initialized for semantic memory")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {str(e)}")
            logger.warning("Using fallback file-based storage for semantic memory")
            self.mongodb = None
            
            # Create memory directory if it doesn't exist
            os.makedirs(self.memory_dir, exist_ok=True)

    async def store(self, memory: Dict[str, Any]) -> None:
        """
        Store a semantic memory.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            logger.warning("Cannot store semantic memory: missing memory_id or user_id")
            return
            
        # Add memory type if not present
        if "memory_type" not in memory:
            memory["memory_type"] = "semantic"
            
        # Add confidence score if not present
        if "confidence" not in memory:
            memory["confidence"] = await self._calculate_confidence(memory)
            
        # Add tags if not present
        if "tags" not in memory:
            memory["tags"] = await self._extract_tags(memory)
            
        # Add related concepts if not present
        if "related_concepts" not in memory:
            memory["related_concepts"] = await self._extract_related_concepts(memory)
            
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                await self.mongodb.insert_one(
                    collection="semantic_memories",
                    document=memory
                )
                
                logger.debug(f"Stored semantic memory {memory_id} in MongoDB")
            except Exception as e:
                logger.error(f"Error storing semantic memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based storage")
                await self._fallback_store(memory)
        else:
            # Use fallback file-based storage
            await self._fallback_store(memory)

    async def _fallback_store(self, memory: Dict[str, Any]) -> None:
        """
        Fallback method to store a semantic memory using file-based storage.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            return
            
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.memory_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save memory to file
        memory_path = os.path.join(user_dir, f"{memory_id}.json")
        
        with open(memory_path, 'w') as f:
            json.dump(memory, f)
            
        logger.debug(f"Stored semantic memory {memory_id} using file-based storage")

    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a semantic memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memory = await self.mongodb.find_one(
                    collection="semantic_memories",
                    query={"memory_id": memory_id}
                )
                
                if memory:
                    logger.debug(f"Retrieved semantic memory {memory_id} from MongoDB")
                    return memory
                    
            except Exception as e:
                logger.error(f"Error retrieving semantic memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get(memory_id)

    async def _fallback_get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to get a semantic memory using file-based storage.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # Search for the memory file in all user directories
        for user_dir in os.listdir(self.memory_dir):
            user_dir_path = os.path.join(self.memory_dir, user_dir)
            
            if os.path.isdir(user_dir_path):
                memory_path = os.path.join(user_dir_path, f"{memory_id}.json")
                
                if os.path.exists(memory_path):
                    try:
                        with open(memory_path, 'r') as f:
                            memory = json.load(f)
                            logger.debug(f"Retrieved semantic memory {memory_id} from file-based storage")
                            return memory
                    except Exception as e:
                        logger.error(f"Error reading memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Semantic memory {memory_id} not found")
        return None

    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a semantic memory.

        Args:
            memory_id: Memory ID
            updates: Updates to apply

        Returns:
            True if successful, False otherwise
        """
        # Get the current memory
        memory = await self.get(memory_id)
        if not memory:
            logger.warning(f"Cannot update semantic memory {memory_id}: not found")
            return False
            
        # Apply updates
        for key, value in updates.items():
            # Don't update memory_id, user_id, or memory_type
            if key not in ["memory_id", "user_id", "memory_type"]:
                memory[key] = value
                
        # Update confidence if relevant fields changed
        confidence_fields = ["concept", "information", "source"]
        if any(field in updates for field in confidence_fields):
            memory["confidence"] = await self._calculate_confidence(memory)
            
        # Update tags if relevant fields changed
        tag_fields = ["concept", "information", "category"]
        if any(field in updates for field in tag_fields):
            memory["tags"] = await self._extract_tags(memory)
            
        # Update related concepts if relevant fields changed
        related_fields = ["concept", "information", "related_concepts"]
        if any(field in updates for field in related_fields):
            memory["related_concepts"] = await self._extract_related_concepts(memory)
            
        # Update timestamp
        memory["updated_at"] = datetime.datetime.now().isoformat()
        
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.update_one(
                    collection="semantic_memories",
                    query={"memory_id": memory_id},
                    update={"$set": memory}
                )
                
                if result and result.modified_count > 0:
                    logger.debug(f"Updated semantic memory {memory_id} in MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to update semantic memory {memory_id} in MongoDB")
                    
            except Exception as e:
                logger.error(f"Error updating semantic memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based update")
                
        # Use fallback file-based update
        return await self._fallback_update(memory)

    async def _fallback_update(self, memory: Dict[str, Any]) -> bool:
        """
        Fallback method to update a semantic memory using file-based storage.

        Args:
            memory: Updated memory dictionary

        Returns:
            True if successful, False otherwise
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            return False
            
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.memory_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save updated memory to file
        memory_path = os.path.join(user_dir, f"{memory_id}.json")
        
        try:
            with open(memory_path, 'w') as f:
                json.dump(memory, f)
                
            logger.debug(f"Updated semantic memory {memory_id} using file-based storage")
            return True
        except Exception as e:
            logger.error(f"Error updating memory file {memory_path}: {str(e)}")
            return False

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a semantic memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.delete_one(
                    collection="semantic_memories",
                    query={"memory_id": memory_id}
                )
                
                if result and result.deleted_count > 0:
                    logger.debug(f"Deleted semantic memory {memory_id} from MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to delete semantic memory {memory_id} from MongoDB")
                    
            except Exception as e:
                logger.error(f"Error deleting semantic memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based deletion")
                
        # Use fallback file-based deletion
        return await self._fallback_delete(memory_id)

    async def _fallback_delete(self, memory_id: str) -> bool:
        """
        Fallback method to delete a semantic memory using file-based storage.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # Search for the memory file in all user directories
        for user_dir in os.listdir(self.memory_dir):
            user_dir_path = os.path.join(self.memory_dir, user_dir)
            
            if os.path.isdir(user_dir_path):
                memory_path = os.path.join(user_dir_path, f"{memory_id}.json")
                
                if os.path.exists(memory_path):
                    try:
                        os.remove(memory_path)
                        logger.debug(f"Deleted semantic memory {memory_id} from file-based storage")
                        return True
                    except Exception as e:
                        logger.error(f"Error deleting memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Semantic memory {memory_id} not found for deletion")
        return False

    async def consolidate(self, user_id: str) -> Dict[str, Any]:
        """
        Consolidate semantic memories for a user.

        Args:
            user_id: User ID

        Returns:
            Consolidation results
        """
        # Get all semantic memories for the user
        memories = await self._get_user_memories(user_id)
        
        # Group memories by category
        category_groups = {}
        for memory in memories:
            category = memory.get("category", "general")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(memory)
            
        # Group memories by concept
        concept_groups = {}
        for memory in memories:
            concept = memory.get("concept", "").lower()
            if concept not in concept_groups:
                concept_groups[concept] = []
            concept_groups[concept].append(memory)
            
        # Identify contradictions
        contradictions = await self._identify_contradictions(memories)
        
        # Identify knowledge gaps
        knowledge_gaps = await self._identify_knowledge_gaps(memories)
        
        # Update memory confidence based on contradictions
        await self._update_confidence_based_on_contradictions(memories, contradictions)
        
        # Build concept graph
        concept_graph = await self._build_concept_graph(memories)
        
        logger.info(f"Consolidated {len(memories)} semantic memories for user {user_id}")
        
        return {
            "memory_count": len(memories),
            "category_groups": len(category_groups),
            "concept_groups": len(concept_groups),
            "contradictions": contradictions,
            "knowledge_gaps": knowledge_gaps,
            "concept_graph": {
                "nodes": len(concept_graph["nodes"]),
                "edges": len(concept_graph["edges"])
            }
        }

    async def _get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all semantic memories for a user.

        Args:
            user_id: User ID

        Returns:
            List of memory dictionaries
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memories = await self.mongodb.find(
                    collection="semantic_memories",
                    query={"user_id": user_id}
                )
                
                if memories:
                    logger.debug(f"Retrieved {len(memories)} semantic memories for user {user_id} from MongoDB")
                    return memories
                    
            except Exception as e:
                logger.error(f"Error retrieving semantic memories from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get_user_memories(user_id)

    async def _fallback_get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fallback method to get all semantic memories for a user using file-based storage.

        Args:
            user_id: User ID

        Returns:
            List of memory dictionaries
        """
        memories = []
        
        # Check if user directory exists
        user_dir = os.path.join(self.memory_dir, user_id)
        if not os.path.exists(user_dir):
            return memories
            
        # Get all memory files
        memory_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
        
        # Load all memories
        for file_name in memory_files:
            file_path = os.path.join(user_dir, file_name)
            try:
                with open(file_path, 'r') as f:
                    memory = json.load(f)
                    memories.append(memory)
            except Exception as e:
                logger.error(f"Error loading memory file {file_path}: {str(e)}")
                
        logger.debug(f"Retrieved {len(memories)} semantic memories for user {user_id} from file-based storage")
        return memories

    async def _identify_contradictions(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify contradictions in semantic memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of identified contradictions
        """
        contradictions = []
        
        # Group memories by concept
        concept_groups = {}
        for memory in memories:
            concept = memory.get("concept", "").lower()
            if concept:
                if concept not in concept_groups:
                    concept_groups[concept] = []
                concept_groups[concept].append(memory)
                
        # Check for contradictions within each concept group
        for concept, group in concept_groups.items():
            if len(group) < 2:
                continue
                
            # Compare each pair of memories
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    memory1 = group[i]
                    memory2 = group[j]
                    
                    # Check if information contradicts
                    if await self._is_contradiction(memory1, memory2):
                        contradictions.append({
                            "concept": concept,
                            "memory1_id": memory1.get("memory_id"),
                            "memory2_id": memory2.get("memory_id"),
                            "memory1_info": memory1.get("information", ""),
                            "memory2_info": memory2.get("information", ""),
                            "memory1_confidence": memory1.get("confidence", 0.5),
                            "memory2_confidence": memory2.get("confidence", 0.5)
                        })
                        
        return contradictions

    async def _is_contradiction(self, memory1: Dict[str, Any], memory2: Dict[str, Any]) -> bool:
        """
        Check if two memories contradict each other.

        Args:
            memory1: First memory dictionary
            memory2: Second memory dictionary

        Returns:
            True if the memories contradict, False otherwise
        """
        # This is a simplified implementation
        # In a real implementation, this would use NLP techniques to detect contradictions
        
        # Check if both memories have information
        info1 = memory1.get("information", "").lower()
        info2 = memory2.get("information", "").lower()
        
        if not info1 or not info2:
            return False
            
        # Check for negation patterns
        negation_patterns = [
            ("is ", "is not "),
            ("are ", "are not "),
            ("has ", "has not "),
            ("have ", "have not "),
            ("can ", "cannot "),
            ("will ", "will not "),
            ("should ", "should not "),
            ("must ", "must not "),
            ("always ", "never ")
        ]
        
        for pos, neg in negation_patterns:
            if (pos in info1 and neg in info2 and info1.replace(pos, "") == info2.replace(neg, "")) or \
               (neg in info1 and pos in info2 and info1.replace(neg, "") == info2.replace(pos, "")):
                return True
                
        # Check for opposite statements
        opposite_pairs = [
            ("true", "false"),
            ("yes", "no"),
            ("positive", "negative"),
            ("good", "bad"),
            ("right", "wrong"),
            ("correct", "incorrect"),
            ("enable", "disable"),
            ("allow", "forbid"),
            ("include", "exclude")
        ]
        
        for word1, word2 in opposite_pairs:
            if (word1 in info1 and word2 in info2) or (word2 in info1 and word1 in info2):
                return True
                
        return False

    async def _identify_knowledge_gaps(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify knowledge gaps in semantic memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of identified knowledge gaps
        """
        knowledge_gaps = []
        
        # Extract all concepts
        concepts = set()
        for memory in memories:
            concept = memory.get("concept", "").lower()
            if concept:
                concepts.add(concept)
                
        # Extract all related concepts
        related_concepts = set()
        for memory in memories:
            related = memory.get("related_concepts", [])
            related_concepts.update([r.lower() for r in related])
                
        # Identify concepts that are mentioned as related but don't have their own memories
        missing_concepts = related_concepts - concepts
        
        for concept in missing_concepts:
            # Find memories that reference this concept
            referencing_memories = []
            for memory in memories:
                related = memory.get("related_concepts", [])
                if concept in [r.lower() for r in related]:
                    referencing_memories.append(memory.get("memory_id"))
                    
            if referencing_memories:
                knowledge_gaps.append({
                    "concept": concept,
                    "referenced_by": referencing_memories,
                    "gap_type": "missing_concept"
                })
                
        # Identify concepts with low confidence
        low_confidence_threshold = 0.4
        for memory in memories:
            confidence = memory.get("confidence", 0.5)
            if confidence < low_confidence_threshold:
                knowledge_gaps.append({
                    "concept": memory.get("concept", ""),
                    "memory_id": memory.get("memory_id"),
                    "confidence": confidence,
                    "gap_type": "low_confidence"
                })
                
        return knowledge_gaps

    async def _update_confidence_based_on_contradictions(self, memories: List[Dict[str, Any]], contradictions: List[Dict[str, Any]]) -> None:
        """
        Update memory confidence based on identified contradictions.

        Args:
            memories: List of memory dictionaries
            contradictions: List of identified contradictions
        """
        # Create a map of memory IDs to confidence adjustments
        confidence_adjustments = {}
        
        for contradiction in contradictions:
            memory1_id = contradiction.get("memory1_id")
            memory2_id = contradiction.get("memory2_id")
            memory1_confidence = contradiction.get("memory1_confidence", 0.5)
            memory2_confidence = contradiction.get("memory2_confidence", 0.5)
            
            # Reduce confidence for both memories
            if memory1_id not in confidence_adjustments:
                confidence_adjustments[memory1_id] = 0.0
            if memory2_id not in confidence_adjustments:
                confidence_adjustments[memory2_id] = 0.0
                
            # Apply larger reduction to the memory with lower confidence
            if memory1_confidence < memory2_confidence:
                confidence_adjustments[memory1_id] -= 0.1
                confidence_adjustments[memory2_id] -= 0.05
            else:
                confidence_adjustments[memory1_id] -= 0.05
                confidence_adjustments[memory2_id] -= 0.1
                
        # Apply confidence adjustments
        for memory in memories:
            memory_id = memory.get("memory_id")
            if memory_id in confidence_adjustments:
                adjustment = confidence_adjustments[memory_id]
                if adjustment != 0.0:
                    current_confidence = memory.get("confidence", 0.5)
                    new_confidence = max(0.1, min(1.0, current_confidence + adjustment))
                    
                    # Update memory if confidence changed significantly
                    if abs(new_confidence - current_confidence) >= 0.05:
                        await self.update(memory_id, {"confidence": new_confidence})

    async def _build_concept_graph(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a concept graph from semantic memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            Concept graph dictionary
        """
        nodes = set()
        edges = []
        
        # Add nodes for all concepts
        for memory in memories:
            concept = memory.get("concept", "").lower()
            if concept:
                nodes.add(concept)
                
        # Add nodes and edges for related concepts
        for memory in memories:
            concept = memory.get("concept", "").lower()
            related = memory.get("related_concepts", [])
            
            if concept and related:
                for related_concept in related:
                    related_concept = related_concept.lower()
                    nodes.add(related_concept)
                    edges.append({
                        "source": concept,
                        "target": related_concept,
                        "memory_id": memory.get("memory_id")
                    })
                    
        return {
            "nodes": list(nodes),
            "edges": edges
        }

    async def _calculate_confidence(self, memory: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a semantic memory.

        Args:
            memory: Memory dictionary

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence_score = 0.5  # Default confidence
        
        # Check for explicit confidence
        if "confidence" in memory and isinstance(memory["confidence"], (int, float)):
            return max(0.0, min(1.0, float(memory["confidence"])))
            
        # Factor 1: Source reliability
        source = memory.get("source", "")
        source_score = 0.5  # Default source reliability
        
        if source:
            reliable_sources = ["academic", "scientific", "official", "expert", "verified", "published"]
            unreliable_sources = ["rumor", "unverified", "anecdotal", "social media", "hearsay"]
            
            # Check for reliable source indicators
            if any(s in source.lower() for s in reliable_sources):
                source_score = 0.8
            # Check for unreliable source indicators
            elif any(s in source.lower() for s in unreliable_sources):
                source_score = 0.2
                
        # Factor 2: Information completeness
        information = memory.get("information", "")
        completeness_score = 0.0
        
        if information:
            # Simple heuristic: longer information might be more complete
            word_count = len(information.split())
            completeness_score = min(1.0, word_count / 50)  # Normalize to 50 words
            
        # Factor 3: Verification status
        verification_score = 0.5  # Default verification
        verification_status = memory.get("verification_status", "")
        
        if verification_status:
            if verification_status.lower() in ["verified", "confirmed", "validated"]:
                verification_score = 0.9
            elif verification_status.lower() in ["unverified", "unconfirmed", "questionable"]:
                verification_score = 0.2
                
        # Factor 4: Recency
        recency_score = 0.5  # Default recency
        created_at = memory.get("created_at", "")
        
        if created_at:
            try:
                created_datetime = datetime.datetime.fromisoformat(created_at)
                now = datetime.datetime.now()
                days_ago = (now - created_datetime).days
                
                # More recent memories might have higher confidence
                recency_score = max(0.3, min(0.7, 0.7 - (days_ago / 365)))  # Normalize to 1 year
            except (ValueError, TypeError):
                pass
                
        # Combine factors with weights
        confidence_score = (
            source_score * 0.4 +
            completeness_score * 0.3 +
            verification_score * 0.2 +
            recency_score * 0.1
        )
        
        return max(0.1, min(1.0, confidence_score))

    async def _extract_tags(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract tags from a semantic memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of tags
        """
        tags = set()
        
        # Check for explicit tags
        if "tags" in memory and isinstance(memory["tags"], list):
            tags.update(memory["tags"])
            
        # Add concept as tag
        concept = memory.get("concept", "")
        if concept:
            tags.add(concept.lower())
            
        # Add category as tag
        category = memory.get("category", "")
        if category:
            tags.add(category.lower())
            
        # Extract tags from information
        information = memory.get("information", "")
        if information:
            # Extract key terms from information
            words = information.lower().split()
            # Filter out common words
            stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "as"]
            key_terms = [w for w in words if len(w) > 4 and w not in stop_words]
            # Add most frequent terms as tags
            from collections import Counter
            term_counts = Counter(key_terms)
            common_terms = [term for term, count in term_counts.most_common(3) if count > 1]
            tags.update(common_terms)
            
        return list(tags)

    async def _extract_related_concepts(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract related concepts from a semantic memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of related concepts
        """
        related_concepts = set()
        
        # Check for explicit related concepts
        if "related_concepts" in memory and isinstance(memory["related_concepts"], list):
            related_concepts.update(memory["related_concepts"])
            
        # Extract related concepts from information
        concept = memory.get("concept", "").lower()
        information = memory.get("information", "")
        
        if concept and information:
            # This is a simplified implementation
            # In a real implementation, this would use NLP techniques to extract related concepts
            
            # Look for phrases like "related to X" or "associated with X"
            relation_patterns = [
                "related to ",
                "associated with ",
                "connected to ",
                "linked to ",
                "part of ",
                "type of ",
                "kind of ",
                "similar to "
            ]
            
            for pattern in relation_patterns:
                if pattern in information.lower():
                    parts = information.lower().split(pattern)
                    for i in range(1, len(parts)):
                        # Extract the word or phrase after the pattern
                        related = parts[i].split()[0].strip(",.;:!?")
                        if related and related != concept:
                            related_concepts.add(related)
                            
        return list(related_concepts)