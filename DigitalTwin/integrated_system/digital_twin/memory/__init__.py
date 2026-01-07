"""
Memory module for the digital twin.

This module provides memory capabilities for the digital twin,
including memory storage, retrieval, and modeling.
"""

import logging
from typing import Dict, List, Any, Optional
from .system import MemorySystem
from .model import MemoryModel

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manager for digital twin memory components."""
    
    def __init__(self):
        """Initialize the memory manager."""
        self.system = MemorySystem()
        self.model = MemoryModel()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the memory manager."""
        logger.info("Initializing memory manager")
        
        # Initialize system
        await self.system.initialize()
        
        # Initialize model
        await self.model.initialize()
        
        self.initialized = True
        logger.info("Memory manager initialized")
    
    async def store_memory(self, content: Any, memory_type: str = 'episodic', 
                          importance: float = 0.5, metadata: Dict[str, Any] = None,
                          categories: List[str] = None) -> Dict[str, Any]:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory (episodic, semantic, procedural, emotional)
            importance: Importance of memory (0.0 to 1.0)
            metadata: Additional metadata
            categories: Memory categories for the model
            
        Returns:
            Dictionary containing the stored memory
        """
        logger.info(f"Storing new {memory_type} memory")
        
        if not self.initialized:
            await self.initialize()
        
        # Store in system
        memory = await self.system.store_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata
        )
        
        # Register with model
        if not categories:
            # Map memory_type to categories
            categories = ['personal']  # Default
            if memory_type == 'episodic':
                categories = ['personal']
            elif memory_type == 'semantic':
                categories = ['factual']
            elif memory_type == 'procedural':
                categories = ['procedural']
            elif memory_type == 'emotional':
                categories = ['emotional']
        
        model_result = await self.model.register_memory(
            memory_id=memory['id'],
            content=content,
            categories=categories,
            initial_strength=importance
        )
        
        # Combine results
        result = {
            'memory': memory,
            'model': model_result
        }
        
        return result
    
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
        
        # Retrieve from system
        memory = await self.system.retrieve_memory(memory_id)
        
        if memory:
            # Update model
            model_result = await self.model.recall_memory(memory_id)
            
            # Combine results
            result = {
                'memory': memory,
                'model': model_result
            }
            
            return result
        else:
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
        
        # Search in system
        memories = await self.system.search_memories(
            query=query,
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance
        )
        
        # Update model for each retrieved memory
        for memory in memories:
            await self.model.recall_memory(memory['id'])
        
        return memories
    
    async def find_similar_memories(self, memory_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find memories similar to the given memory.
        
        Args:
            memory_id: Memory ID
            limit: Maximum number of results
            
        Returns:
            List of similar memories
        """
        logger.info(f"Finding memories similar to {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        # Find similar memories in model
        similar_ids = await self.model.find_similar_memories(memory_id, limit)
        
        # Retrieve memories from system
        similar_memories = []
        for similar_id, similarity in similar_ids:
            memory = await self.system.retrieve_memory(similar_id)
            if memory:
                similar_memories.append({
                    'memory': memory,
                    'similarity': similarity
                })
        
        return similar_memories
    
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
        
        # Update in system
        memory = await self.system.update_memory(
            memory_id=memory_id,
            content=content,
            importance=importance,
            metadata=metadata
        )
        
        if memory:
            # Update model
            if importance is not None:
                self.model.memory_strength[memory_id] = importance
                await self.model._save_model()
            
            return memory
        else:
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
        
        # Remove from system
        result = await self.system.forget_memory(memory_id)
        
        if result:
            # Remove from model
            if memory_id in self.model.memory_strength:
                del self.model.memory_strength[memory_id]
            
            if memory_id in self.model.memory_decay_rates:
                del self.model.memory_decay_rates[memory_id]
            
            if memory_id in self.model.memory_last_recalled:
                del self.model.memory_last_recalled[memory_id]
            
            if memory_id in self.model.memory_recall_count:
                del self.model.memory_recall_count[memory_id]
            
            if memory_id in self.model.memory_embeddings:
                del self.model.memory_embeddings[memory_id]
            
            # Remove from categories
            for category, memories in self.model.memory_categories.items():
                if memory_id in memories:
                    memories.remove(memory_id)
            
            # Remove from clusters
            for cluster, members in list(self.model.memory_clusters.items()):
                if memory_id in members:
                    members.remove(memory_id)
                    if not members:
                        del self.model.memory_clusters[cluster]
            
            await self.model._save_model()
        
        return result
    
    async def maintenance(self):
        """Perform memory maintenance tasks."""
        logger.info("Performing memory maintenance")
        
        if not self.initialized:
            await self.initialize()
        
        # Update memory decay
        await self.model.update_memory_decay()
        
        # Consolidate memories
        await self.system.consolidate_memories()
        
        # Cluster memories
        await self.model.cluster_memories()
        
        logger.info("Memory maintenance complete")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system and model.
        
        Returns:
            Dictionary of memory statistics
        """
        logger.info("Getting memory statistics")
        
        if not self.initialized:
            await self.initialize()
        
        # Get model stats
        model_stats = await self.model.get_memory_stats()
        
        # Count memories by type
        type_counts = {}
        for memory_type, memories in self.system.memory_types.items():
            type_counts[memory_type] = len(memories)
        
        # Combine stats
        stats = {
            'total_memories': len(self.system.memories),
            'type_counts': type_counts,
            'model_stats': model_stats
        }
        
        return stats