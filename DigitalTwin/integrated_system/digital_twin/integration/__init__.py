"""
Integration module for the digital twin.

This module provides integration components for the digital twin,
connecting the personality, memory, and conversation components.
"""

import logging
from typing import Dict, List, Any, Optional
from .cognitive_twin import CognitiveTwin
from .interface import DigitalTwinInterface

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Manager for digital twin integration components."""
    
    def __init__(self, personality_manager=None, memory_manager=None, conversation_manager=None):
        """
        Initialize the integration manager.
        
        Args:
            personality_manager: Personality manager instance
            memory_manager: Memory manager instance
            conversation_manager: Conversation manager instance
        """
        self.personality_manager = personality_manager
        self.memory_manager = memory_manager
        self.conversation_manager = conversation_manager
        
        # Create cognitive twin
        self.cognitive_twin = CognitiveTwin(
            personality_manager=personality_manager,
            memory_manager=memory_manager,
            conversation_manager=conversation_manager
        )
        
        # Create interface
        self.interface = DigitalTwinInterface(
            cognitive_twin=self.cognitive_twin
        )
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the integration manager."""
        logger.info("Initializing integration manager")
        
        # Initialize interface (which will initialize cognitive twin)
        await self.interface.initialize()
        
        self.initialized = True
        logger.info("Integration manager initialized")
    
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
        
        return await self.interface.interact(input_data, input_type, session_id)
    
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
        
        return await self.interface.create_session(session_id, metadata)
    
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
        
        return await self.interface.end_session(session_id)
    
    async def get_twin_state(self) -> Dict[str, Any]:
        """
        Get the current state of the digital twin.
        
        Returns:
            Dictionary containing the twin state
        """
        logger.info("Getting digital twin state")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.interface.get_twin_state()
    
    async def maintenance(self):
        """Perform maintenance tasks."""
        logger.info("Performing integration maintenance")
        
        if not self.initialized:
            await self.initialize()
        
        await self.interface.maintenance()
        
        logger.info("Integration maintenance complete")