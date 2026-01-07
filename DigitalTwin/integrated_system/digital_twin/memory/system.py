"""
Memory system for the digital twin.

This module provides the core memory system for the digital twin,
responsible for storing, retrieving, and managing memories.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import asyncio
import numpy as np
from datetime import datetime
import json
import os
import uuid

logger = logging.getLogger(__name__)

class MemorySystem:
    """Core memory system for the digital twin."""
    
    def __init__(self):
        """Initialize the memory system."""
        self.memories = []
        self.memory_index = {}
        self.memory_types = {
            'episodic': [],  # Event-based memories
            'semantic': [],  # Fact-based memories
            'procedural': [],  # Skill-based memories
            'emotional': []  # Emotion-based memories
        }
        self.memory_importance = {}
        self.memory_recency = {}
        self.memory_associations = {}
        self.initialized = False
        self.memory_path = "data/memories.json"
    
    async def initialize(self):
        """Initialize the memory system."""
        logger.info("Initializing memory system")
        
        # Try to load memories from file
        if await self._load_memories():
            logger.info("Loaded memories from file")
        else:
            # Initialize with empty memories
            logger.info("Starting with empty memory system")
        
        self.initialized = True
        logger.info("Memory system initialized")
    
    async def _load_memories(self) -> bool:
        """
        Load memories from file.
        
        Returns:
            True if memories were loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r') as f:
                    memory_data = json.load(f)
                
                # Load memories
                if 'memories' in memory_data:
                    self.memories = memory_data['memories']
                
                # Load memory types
                if 'memory_types' in memory_data:
                    self.memory_types = memory_data['memory_types']
                
                # Load memory importance
                if 'memory_importance' in memory_data:
                    self.memory_importance = memory_data['memory_importance']
                
                # Load memory recency
                if 'memory_recency' in memory_data:
                    self.memory_recency = memory_data['memory_recency']
                
                # Load memory associations
                if 'memory_associations' in memory_data:
                    self.memory_associations = memory_data['memory_associations']
                
                # Rebuild memory index
                self._rebuild_memory_index()
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading memories: {str(e)}")
            return False
    
    async def _save_memories(self):
        """Save memories to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
            
            # Create memory data
            memory_data = {
                'memories': self.memories,
                'memory_types': self.memory_types,
                'memory_importance': self.memory_importance,
                'memory_recency': self.memory_recency,
                'memory_associations': self.memory_associations,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.memory_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            logger.info("Saved memories to file")
            return True
        except Exception as e:
            logger.error(f"Error saving memories: {str(e)}")
            return False
    
    def _rebuild_memory_index(self):
        """Rebuild the memory index."""
        self.memory_index = {}
        
        for i, memory in enumerate(self.memories):
            if 'id' in memory:
                self.memory_index[memory['id']] = i
    
    async def store_memory(self, content: Any, memory_type: str = 'episodic', 
                          importance: float = 0.5, metadata: Dict[str, Any] = None,
                          associations: List[str] = None) -> Dict[str, Any]:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory (episodic, semantic, procedural, emotional)
            importance: Importance of memory (0.0 to 1.0)
            metadata: Additional metadata
            associations: List of associated memory IDs
            
        Returns:
            Dictionary containing the stored memory
        """
        logger.info(f"Storing new {memory_type} memory")
        
        if not self.initialized:
            await self.initialize()
        
        # Validate memory type
        if memory_type not in self.memory_types:
            logger.warning(f"Invalid memory type: {memory_type}, defaulting to episodic")
            memory_type = 'episodic'
        
        # Create memory ID
        memory_id = str(uuid.uuid4())
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Create memory object
        memory = {
            'id': memory_id,
            'content': content,
            'type': memory_type,
            'created_at': timestamp,
            'last_accessed': timestamp
        }
        
        # Add metadata if provided
        if metadata:
            memory['metadata'] = metadata
        
        # Store memory
        self.memories.append(memory)
        self.memory_index[memory_id] = len(self.memories) - 1
        self.memory_types[memory_type].append(memory_id)
        self.memory_importance[memory_id] = importance
        self.memory_recency[memory_id] = timestamp
        
        # Store associations if provided
        if associations:
            self.memory_associations[memory_id] = associations
            
            # Create bidirectional associations
            for assoc_id in associations:
                if assoc_id in self.memory_associations:
                    if memory_id not in self.memory_associations[assoc_id]:
                        self.memory_associations[assoc_id].append(memory_id)
                else:
                    self.memory_associations[assoc_id] = [memory_id]
        
        # Save memories
        await self._save_memories()
        
        return memory
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory dictionary or None if not found
        """
        logger.info(f"Retrieving memory: {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if memory_id in self.memory_index:
            # Get memory
            memory_idx = self.memory_index[memory_id]
            memory = self.memories[memory_idx]
            
            # Update last accessed timestamp
            memory['last_accessed'] = datetime.now().isoformat()
            self.memory_recency[memory_id] = memory['last_accessed']
            
            # Save memories
            await self._save_memories()
            
            return memory
        else:
            logger.warning(f"Memory not found: {memory_id}")
            return None
    
    async def search_memories(self, query: str, memory_type: Optional[str] = None, 
                             limit: int = 10, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search memories by query.
        
        Args:
            query: Search query
            memory_type: Type of memories to search (optional)
            limit: Maximum number of results
            min_importance: Minimum importance threshold
            
        Returns:
            List of matching memories
        """
        logger.info(f"Searching memories for: {query}")
        
        if not self.initialized:
            await self.initialize()
        
        # Convert query to lowercase for case-insensitive search
        query = query.lower()
        
        # Filter memories by type if specified
        if memory_type and memory_type in self.memory_types:
            memory_ids = self.memory_types[memory_type]
            candidate_memories = [self.memories[self.memory_index[mid]] for mid in memory_ids if mid in self.memory_index]
        else:
            candidate_memories = self.memories
        
        # Filter by importance
        if min_importance > 0:
            candidate_memories = [m for m in candidate_memories if self.memory_importance.get(m['id'], 0) >= min_importance]
        
        # Search for query in memory content
        results = []
        for memory in candidate_memories:
            content = str(memory['content']).lower()
            if query in content:
                # Calculate relevance score
                relevance = self._calculate_relevance(memory, query)
                
                # Add to results with relevance score
                results.append({
                    'memory': memory,
                    'relevance': relevance
                })
        
        # Sort by relevance
        results = sorted(results, key=lambda x: x['relevance'], reverse=True)
        
        # Limit results
        results = results[:limit]
        
        # Update last accessed timestamp for retrieved memories
        for result in results:
            memory_id = result['memory']['id']
            result['memory']['last_accessed'] = datetime.now().isoformat()
            self.memory_recency[memory_id] = result['memory']['last_accessed']
        
        # Save memories
        await self._save_memories()
        
        # Return just the memories
        return [r['memory'] for r in results]
    
    def _calculate_relevance(self, memory: Dict[str, Any], query: str) -> float:
        """
        Calculate relevance score for a memory.
        
        Args:
            memory: Memory dictionary
            query: Search query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # Base relevance on content match
        content = str(memory['content']).lower()
        query = query.lower()
        
        # Count occurrences of query in content
        occurrences = content.count(query)
        
        # Calculate content relevance
        content_relevance = min(1.0, occurrences * 0.2)
        
        # Factor in importance
        importance = self.memory_importance.get(memory['id'], 0.5)
        
        # Factor in recency
        recency = 0.5
        if memory['id'] in self.memory_recency:
            last_accessed = datetime.fromisoformat(self.memory_recency[memory['id']])
            now = datetime.now()
            days_since_access = (now - last_accessed).days
            recency = max(0.1, 1.0 - (days_since_access / 30))  # Decay over 30 days
        
        # Combine factors
        relevance = (content_relevance * 0.6) + (importance * 0.25) + (recency * 0.15)
        
        return relevance
    
    async def update_memory(self, memory_id: str, content: Any = None, 
                           importance: Optional[float] = None, 
                           metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of the memory to update
            content: New memory content (optional)
            importance: New importance value (optional)
            metadata: New or updated metadata (optional)
            
        Returns:
            Updated memory dictionary or None if not found
        """
        logger.info(f"Updating memory: {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if memory_id in self.memory_index:
            # Get memory
            memory_idx = self.memory_index[memory_id]
            memory = self.memories[memory_idx]
            
            # Update content if provided
            if content is not None:
                memory['content'] = content
            
            # Update importance if provided
            if importance is not None:
                self.memory_importance[memory_id] = importance
            
            # Update metadata if provided
            if metadata:
                if 'metadata' in memory:
                    memory['metadata'].update(metadata)
                else:
                    memory['metadata'] = metadata
            
            # Update last modified timestamp
            memory['last_modified'] = datetime.now().isoformat()
            
            # Save memories
            await self._save_memories()
            
            return memory
        else:
            logger.warning(f"Memory not found: {memory_id}")
            return None
    
    async def forget_memory(self, memory_id: str) -> bool:
        """
        Remove a memory.
        
        Args:
            memory_id: ID of the memory to remove
            
        Returns:
            True if memory was removed, False otherwise
        """
        logger.info(f"Forgetting memory: {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if memory_id in self.memory_index:
            # Get memory index
            memory_idx = self.memory_index[memory_id]
            memory = self.memories[memory_idx]
            
            # Remove from memories list
            self.memories.pop(memory_idx)
            
            # Remove from memory index
            del self.memory_index[memory_id]
            
            # Remove from memory types
            memory_type = memory.get('type', 'episodic')
            if memory_id in self.memory_types.get(memory_type, []):
                self.memory_types[memory_type].remove(memory_id)
            
            # Remove from importance
            if memory_id in self.memory_importance:
                del self.memory_importance[memory_id]
            
            # Remove from recency
            if memory_id in self.memory_recency:
                del self.memory_recency[memory_id]
            
            # Remove from associations
            if memory_id in self.memory_associations:
                # Remove bidirectional associations
                for assoc_id in self.memory_associations[memory_id]:
                    if assoc_id in self.memory_associations and memory_id in self.memory_associations[assoc_id]:
                        self.memory_associations[assoc_id].remove(memory_id)
                
                del self.memory_associations[memory_id]
            
            # Rebuild memory index
            self._rebuild_memory_index()
            
            # Save memories
            await self._save_memories()
            
            return True
        else:
            logger.warning(f"Memory not found: {memory_id}")
            return False
    
    async def get_associated_memories(self, memory_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories associated with a given memory.
        
        Args:
            memory_id: ID of the memory
            limit: Maximum number of results
            
        Returns:
            List of associated memories
        """
        logger.info(f"Getting memories associated with: {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if memory_id not in self.memory_associations:
            return []
        
        # Get associated memory IDs
        assoc_ids = self.memory_associations[memory_id]
        
        # Get associated memories
        associated_memories = []
        for assoc_id in assoc_ids:
            if assoc_id in self.memory_index:
                memory_idx = self.memory_index[assoc_id]
                memory = self.memories[memory_idx]
                
                # Calculate association strength
                strength = self._calculate_association_strength(memory_id, assoc_id)
                
                associated_memories.append({
                    'memory': memory,
                    'strength': strength
                })
        
        # Sort by association strength
        associated_memories = sorted(associated_memories, key=lambda x: x['strength'], reverse=True)
        
        # Limit results
        associated_memories = associated_memories[:limit]
        
        # Update last accessed timestamp for retrieved memories
        for assoc in associated_memories:
            assoc_id = assoc['memory']['id']
            assoc['memory']['last_accessed'] = datetime.now().isoformat()
            self.memory_recency[assoc_id] = assoc['memory']['last_accessed']
        
        # Save memories
        await self._save_memories()
        
        # Return just the memories
        return [a['memory'] for a in associated_memories]
    
    def _calculate_association_strength(self, memory_id1: str, memory_id2: str) -> float:
        """
        Calculate association strength between two memories.
        
        Args:
            memory_id1: First memory ID
            memory_id2: Second memory ID
            
        Returns:
            Association strength (0.0 to 1.0)
        """
        # Base strength
        strength = 0.5
        
        # Factor in importance of both memories
        importance1 = self.memory_importance.get(memory_id1, 0.5)
        importance2 = self.memory_importance.get(memory_id2, 0.5)
        avg_importance = (importance1 + importance2) / 2
        
        # Factor in recency of both memories
        recency1 = 0.5
        recency2 = 0.5
        
        if memory_id1 in self.memory_recency:
            last_accessed1 = datetime.fromisoformat(self.memory_recency[memory_id1])
            now = datetime.now()
            days_since_access1 = (now - last_accessed1).days
            recency1 = max(0.1, 1.0 - (days_since_access1 / 30))  # Decay over 30 days
        
        if memory_id2 in self.memory_recency:
            last_accessed2 = datetime.fromisoformat(self.memory_recency[memory_id2])
            now = datetime.now()
            days_since_access2 = (now - last_accessed2).days
            recency2 = max(0.1, 1.0 - (days_since_access2 / 30))  # Decay over 30 days
        
        avg_recency = (recency1 + recency2) / 2
        
        # Combine factors
        strength = (strength * 0.3) + (avg_importance * 0.4) + (avg_recency * 0.3)
        
        return strength
    
    async def consolidate_memories(self):
        """Consolidate memories to improve recall and connections."""
        logger.info("Consolidating memories")
        
        if not self.initialized:
            await self.initialize()
        
        # Identify important memories
        important_memories = []
        for memory_id, importance in self.memory_importance.items():
            if importance >= 0.7 and memory_id in self.memory_index:
                memory_idx = self.memory_index[memory_id]
                memory = self.memories[memory_idx]
                important_memories.append(memory)
        
        # Identify recent memories
        recent_memories = []
        now = datetime.now()
        for memory_id, last_accessed in self.memory_recency.items():
            if memory_id in self.memory_index:
                last_accessed_dt = datetime.fromisoformat(last_accessed)
                days_since_access = (now - last_accessed_dt).days
                
                if days_since_access <= 7:  # Within last week
                    memory_idx = self.memory_index[memory_id]
                    memory = self.memories[memory_idx]
                    recent_memories.append(memory)
        
        # Find potential new associations
        new_associations = []
        
        # Between important memories
        for i, memory1 in enumerate(important_memories):
            for memory2 in important_memories[i+1:]:
                if self._should_associate(memory1, memory2):
                    new_associations.append((memory1['id'], memory2['id']))
        
        # Between recent memories
        for i, memory1 in enumerate(recent_memories):
            for memory2 in recent_memories[i+1:]:
                if self._should_associate(memory1, memory2):
                    new_associations.append((memory1['id'], memory2['id']))
        
        # Create new associations
        for memory_id1, memory_id2 in new_associations:
            # Check if association already exists
            if memory_id1 in self.memory_associations and memory_id2 in self.memory_associations[memory_id1]:
                continue
            
            # Add bidirectional association
            if memory_id1 in self.memory_associations:
                self.memory_associations[memory_id1].append(memory_id2)
            else:
                self.memory_associations[memory_id1] = [memory_id2]
            
            if memory_id2 in self.memory_associations:
                self.memory_associations[memory_id2].append(memory_id1)
            else:
                self.memory_associations[memory_id2] = [memory_id1]
        
        # Save memories
        await self._save_memories()
        
        logger.info(f"Created {len(new_associations)} new memory associations")
    
    def _should_associate(self, memory1: Dict[str, Any], memory2: Dict[str, Any]) -> bool:
        """
        Determine if two memories should be associated.
        
        Args:
            memory1: First memory
            memory2: Second memory
            
        Returns:
            True if memories should be associated, False otherwise
        """
        # Don't associate with self
        if memory1['id'] == memory2['id']:
            return False
        
        # Check if same type
        if memory1.get('type') == memory2.get('type'):
            return True
        
        # Check content similarity
        content1 = str(memory1.get('content', '')).lower()
        content2 = str(memory2.get('content', '')).lower()
        
        # Simple word overlap check
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1.intersection(words2)) / min(len(words1), len(words2))
            if overlap >= 0.3:  # At least 30% word overlap
                return True
        
        # Check metadata similarity if available
        if 'metadata' in memory1 and 'metadata' in memory2:
            metadata1 = memory1['metadata']
            metadata2 = memory2['metadata']
            
            # Check for common keys
            common_keys = set(metadata1.keys()).intersection(set(metadata2.keys()))
            
            for key in common_keys:
                if metadata1[key] == metadata2[key]:
                    return True
        
        return False