"""
Memory System for the Digital Twin.

This module provides the core functionality for managing different types of
memories for the Digital Twin.
"""

import logging
import uuid
import datetime
from typing import Dict, Any, List, Optional

from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .procedural import ProceduralMemory
from .index import MemoryIndex

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    System for managing digital twin memories.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the memory system.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.episodic_memory = EpisodicMemory(config)
        self.semantic_memory = SemanticMemory(config)
        self.procedural_memory = ProceduralMemory(config)
        self.memory_index = MemoryIndex(config)
        logger.info("Memory System initialized")

    async def store_memory(self, user_id: str, memory_type: str, content: Dict[str, Any]) -> str:
        """
        Store a memory.

        Args:
            user_id: User ID
            memory_type: Type of memory (episodic, semantic, procedural)
            content: Memory content

        Returns:
            Memory ID
        """
        # Add metadata
        memory = content.copy()
        memory["user_id"] = user_id
        memory["created_at"] = datetime.datetime.now().isoformat()
        memory["memory_type"] = memory_type
        memory["memory_id"] = str(uuid.uuid4())

        # Store in appropriate memory system
        if memory_type == "episodic":
            await self.episodic_memory.store(memory)
        elif memory_type == "semantic":
            await self.semantic_memory.store(memory)
        elif memory_type == "procedural":
            await self.procedural_memory.store(memory)
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

        # Index the memory
        await self.memory_index.index_memory(memory)

        logger.debug(f"Stored {memory_type} memory with ID {memory['memory_id']}")
        return memory["memory_id"]

    async def retrieve_memory(self, user_id: str, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories based on a query.

        Args:
            user_id: User ID
            query: Query dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            List of memories
        """
        # Get memory IDs from index
        memory_ids = await self.memory_index.search(user_id, query, limit)

        # Retrieve memories
        memories = []
        for memory_id in memory_ids:
            memory = await self.get_memory(memory_id)
            if memory:
                memories.append(memory)

        logger.debug(f"Retrieved {len(memories)} memories for user {user_id}")
        return memories

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # Try each memory system
        memory = await self.episodic_memory.get(memory_id)
        if memory:
            return memory

        memory = await self.semantic_memory.get(memory_id)
        if memory:
            return memory

        memory = await self.procedural_memory.get(memory_id)
        if memory:
            return memory

        logger.warning(f"Memory with ID {memory_id} not found")
        return None

    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory.

        Args:
            memory_id: Memory ID
            updates: Updates to apply

        Returns:
            True if successful, False otherwise
        """
        # Get the memory
        memory = await self.get_memory(memory_id)
        if not memory:
            logger.warning(f"Cannot update memory {memory_id}: not found")
            return False

        # Update in appropriate memory system
        memory_type = memory["memory_type"]
        if memory_type == "episodic":
            success = await self.episodic_memory.update(memory_id, updates)
        elif memory_type == "semantic":
            success = await self.semantic_memory.update(memory_id, updates)
        elif memory_type == "procedural":
            success = await self.procedural_memory.update(memory_id, updates)
        else:
            logger.warning(f"Cannot update memory {memory_id}: unknown type {memory_type}")
            return False

        # Update index if successful
        if success:
            updated_memory = await self.get_memory(memory_id)
            if updated_memory:
                await self.memory_index.update_memory(updated_memory)
                logger.debug(f"Updated memory {memory_id}")

        return success

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # Get the memory
        memory = await self.get_memory(memory_id)
        if not memory:
            logger.warning(f"Cannot delete memory {memory_id}: not found")
            return False

        # Delete from appropriate memory system
        memory_type = memory["memory_type"]
        if memory_type == "episodic":
            success = await self.episodic_memory.delete(memory_id)
        elif memory_type == "semantic":
            success = await self.semantic_memory.delete(memory_id)
        elif memory_type == "procedural":
            success = await self.procedural_memory.delete(memory_id)
        else:
            logger.warning(f"Cannot delete memory {memory_id}: unknown type {memory_type}")
            return False

        # Delete from index if successful
        if success:
            await self.memory_index.delete_memory(memory_id)
            logger.debug(f"Deleted memory {memory_id}")

        return success

    async def consolidate_memories(self, user_id: str) -> Dict[str, Any]:
        """
        Consolidate memories for a user.

        Args:
            user_id: User ID

        Returns:
            Consolidation results
        """
        # Consolidate episodic memories
        episodic_results = await self.episodic_memory.consolidate(user_id)

        # Consolidate semantic memories
        semantic_results = await self.semantic_memory.consolidate(user_id)

        # Consolidate procedural memories
        procedural_results = await self.procedural_memory.consolidate(user_id)

        logger.info(f"Consolidated memories for user {user_id}")
        
        # Return consolidated results
        return {
            "episodic": episodic_results,
            "semantic": semantic_results,
            "procedural": procedural_results
        }