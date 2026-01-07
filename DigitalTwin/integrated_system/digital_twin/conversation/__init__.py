"""
Conversation module for the digital twin.

This module provides conversation capabilities for the digital twin,
including message processing, response generation, and conversation analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from .engine import ConversationEngine
from .enhancer import ConversationEnhancer

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manager for digital twin conversation components."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.engine = ConversationEngine()
        self.enhancer = ConversationEnhancer()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the conversation manager."""
        logger.info("Initializing conversation manager")
        
        # Initialize engine
        await self.engine.initialize()
        
        # Initialize enhancer
        await self.enhancer.initialize()
        
        self.initialized = True
        logger.info("Conversation manager initialized")
    
    async def process_message(self, message: str, user_id: str = "user", 
                             metadata: Dict[str, Any] = None,
                             personality_profile: Dict[str, Any] = None,
                             memory_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response.
        
        Args:
            message: The message text
            user_id: ID of the user sending the message
            metadata: Additional message metadata
            personality_profile: Personality profile (optional)
            memory_context: Memory context (optional)
            
        Returns:
            Dictionary containing the response
        """
        logger.info(f"Processing message from {user_id}")
        
        if not self.initialized:
            await self.initialize()
        
        # Process message with engine
        engine_response = await self.engine.process_message(message, user_id, metadata)
        
        # Get conversation history
        conversation_history = await self.engine.get_conversation_history(limit=10)
        
        # Enhance response with personality and memory
        enhanced_response = await self.enhancer.enhance_response(
            message=message,
            draft_response=engine_response['text'],
            conversation_history=conversation_history,
            personality_profile=personality_profile,
            memory_context=memory_context
        )
        
        # Create final response
        response = {
            'text': enhanced_response['text'],
            'entities': enhanced_response.get('entities', []),
            'topics': enhanced_response.get('topics', []),
            'metrics': enhanced_response.get('metrics', {}),
            'metadata': engine_response.get('metadata', {})
        }
        
        return response
    
    async def get_conversation_history(self, limit: int = 10, 
                                      user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            limit: Maximum number of messages to return
            user_id: Filter by user ID (optional)
            
        Returns:
            List of message dictionaries
        """
        logger.info(f"Getting conversation history (limit={limit})")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.engine.get_conversation_history(limit, user_id)
    
    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update conversation settings.
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Dictionary of updated settings
        """
        logger.info("Updating conversation settings")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.engine.update_settings(settings)
    
    async def clear_history(self) -> bool:
        """
        Clear conversation history.
        
        Returns:
            True if history was cleared successfully
        """
        logger.info("Clearing conversation history")
        
        if not self.initialized:
            await self.initialize()
        
        return await self.engine.clear_history()
    
    async def analyze_conversation(self) -> Dict[str, Any]:
        """
        Analyze the conversation.
        
        Returns:
            Dictionary of analysis results
        """
        logger.info("Analyzing conversation")
        
        if not self.initialized:
            await self.initialize()
        
        # Get basic analysis from engine
        basic_analysis = await self.engine.analyze_conversation()
        
        # Get insights from enhancer
        insights = await self.enhancer.get_conversation_insights()
        
        # Combine results
        analysis = {
            'basic': basic_analysis,
            'insights': insights
        }
        
        return analysis
    
    async def create_personality_profile(self, traits: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Create a personality profile for conversation.
        
        Args:
            traits: Dictionary of personality traits (optional)
            
        Returns:
            Dictionary containing the personality profile
        """
        logger.info("Creating personality profile for conversation")
        
        # Default traits if not provided
        if not traits:
            traits = {
                'openness': 0.7,
                'conscientiousness': 0.6,
                'extraversion': 0.5,
                'agreeableness': 0.6,
                'neuroticism': 0.4
            }
        
        # Create communication style based on traits
        communication_style = {
            'assertiveness': 0.5 + (traits['extraversion'] - 0.5) * 0.5,
            'emotionality': 0.5 + (traits['neuroticism'] - 0.5) * 0.5,
            'formality': 0.5 + (traits['conscientiousness'] - 0.5) * 0.5
        }
        
        # Create descriptors
        descriptors = []
        if traits['openness'] > 0.6:
            descriptors.append('creative')
        if traits['conscientiousness'] > 0.6:
            descriptors.append('organized')
        if traits['extraversion'] > 0.6:
            descriptors.append('outgoing')
        if traits['agreeableness'] > 0.6:
            descriptors.append('friendly')
        if traits['neuroticism'] < 0.4:
            descriptors.append('calm')
        
        communication_style['descriptors'] = descriptors
        
        # Create profile
        profile = {
            'traits': traits,
            'communication_style': communication_style
        }
        
        return profile