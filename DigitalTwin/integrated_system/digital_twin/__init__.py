"""
Digital twin module for the integrated system.

This module provides a comprehensive digital twin implementation,
including personality modeling, memory management, conversation capabilities,
and integration components.
"""

import logging
from typing import Dict, List, Any, Optional
from .personality import PersonalityManager
from .memory import MemoryManager
from .conversation import ConversationManager
from .integration import IntegrationManager

logger = logging.getLogger(__name__)

class DigitalTwin:
    """Main digital twin class."""
    
    def __init__(self):
        """Initialize the digital twin."""
        # Create component managers
        self.personality_manager = PersonalityManager()
        self.memory_manager = MemoryManager()
        self.conversation_manager = ConversationManager()
        
        # Create integration manager
        self.integration_manager = IntegrationManager(
            personality_manager=self.personality_manager,
            memory_manager=self.memory_manager,
            conversation_manager=self.conversation_manager
        )
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the digital twin."""
        logger.info("Initializing digital twin")
        
        # Initialize integration manager (which will initialize all components)
        await self.integration_manager.initialize()
        
        self.initialized = True
        logger.info("Digital twin initialized")
    
    async def interact(self, input_data: Any, input_type: str = 'message', 
                      session_id: str = 'default') -> Dict[str, Any]:
        """
        Interact with the digital twin.
        
        Args:
            input_data: Input data
            input_type: Type of input (message, event, feedback, etc.)
            session_id: Session identifier
            
        Returns:
            Dictionary containing the response
        """
        logger.info(f"Processing {input_type} interaction")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.integration_manager.interact(input_data, input_type, session_id)
    
    async def create_session(self, session_id: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new interaction session.
        
        Args:
            session_id: Session identifier (optional)
            metadata: Additional session metadata
            
        Returns:
            Dictionary containing session information
        """
        logger.info("Creating new interaction session")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.integration_manager.create_session(session_id, metadata)
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End an interaction session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session summary
        """
        logger.info(f"Ending session {session_id}")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.integration_manager.end_session(session_id)
    
    async def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the digital twin.
        
        Returns:
            Dictionary containing the twin state
        """
        logger.info("Getting digital twin state")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.integration_manager.get_twin_state()
    
    async def maintenance(self):
        """Perform maintenance tasks."""
        logger.info("Performing digital twin maintenance")
        
        if not self.initialized:
            await self.initialize()
        
        await self.integration_manager.maintenance()
        
        logger.info("Digital twin maintenance complete")
    
    # Direct access to component managers for advanced usage
    
    async def get_personality_profile(self) -> Dict[str, Any]:
        """
        Get the personality profile.
        
        Returns:
            Dictionary containing the personality profile
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.personality_manager.get_personality_profile()
    
    async def store_memory(self, content: Any, memory_type: str = 'episodic', 
                          importance: float = 0.5, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance of memory
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the stored memory
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.memory_manager.store_memory(content, memory_type, importance, metadata)
    
    async def search_memories(self, query: str, memory_type: Optional[str] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by query.
        
        Args:
            query: Search query
            memory_type: Type of memories to search (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.memory_manager.search_memories(query, memory_type, limit)
    
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        if not self.initialized:
            await self.initialize()
        
        return await self.conversation_manager.get_conversation_history(limit)