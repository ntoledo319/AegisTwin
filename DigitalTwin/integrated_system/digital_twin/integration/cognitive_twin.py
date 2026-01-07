"""
Cognitive twin integration module.

This module provides integration between the digital twin components and cognitive analysis,
creating a cohesive cognitive digital twin.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class CognitiveTwin:
    """Cognitive digital twin integration."""
    
    def __init__(self, personality_manager=None, memory_manager=None, conversation_manager=None):
        """
        Initialize the cognitive twin.
        
        Args:
            personality_manager: Personality manager instance
            memory_manager: Memory manager instance
            conversation_manager: Conversation manager instance
        """
        self.personality_manager = personality_manager
        self.memory_manager = memory_manager
        self.conversation_manager = conversation_manager
        self.cognitive_state = {
            'active_goals': [],
            'current_focus': None,
            'emotional_state': {
                'valence': 0.0,  # -1.0 to 1.0 (negative to positive)
                'arousal': 0.0,  # 0.0 to 1.0 (calm to excited)
                'dominance': 0.0  # -1.0 to 1.0 (submissive to dominant)
            },
            'last_updated': datetime.now().isoformat()
        }
        self.initialized = False
    
    async def initialize(self):
        """Initialize the cognitive twin."""
        logger.info("Initializing cognitive twin")
        
        # Initialize managers if provided
        if self.personality_manager:
            await self.personality_manager.initialize()
        
        if self.memory_manager:
            await self.memory_manager.initialize()
        
        if self.conversation_manager:
            await self.conversation_manager.initialize()
        
        self.initialized = True
        logger.info("Cognitive twin initialized")
    
    async def process_input(self, input_data: Any, input_type: str = 'message') -> Dict[str, Any]:
        """
        Process input data through the cognitive twin.
        
        Args:
            input_data: Input data to process
            input_type: Type of input (message, event, feedback, etc.)
            
        Returns:
            Dictionary containing the response
        """
        logger.info(f"Processing {input_type} input")
        
        if not self.initialized:
            await self.initialize()
        
        # Update cognitive state
        await self._update_cognitive_state(input_data, input_type)
        
        # Process based on input type
        if input_type == 'message':
            return await self._process_message(input_data)
        elif input_type == 'event':
            return await self._process_event(input_data)
        elif input_type == 'feedback':
            return await self._process_feedback(input_data)
        else:
            logger.warning(f"Unknown input type: {input_type}")
            return {'error': f"Unknown input type: {input_type}"}
    
    async def _process_message(self, message_data: Any) -> Dict[str, Any]:
        """
        Process a message input.
        
        Args:
            message_data: Message data
            
        Returns:
            Dictionary containing the response
        """
        # Extract message text and metadata
        if isinstance(message_data, str):
            message = message_data
            metadata = {}
            user_id = "user"
        elif isinstance(message_data, dict):
            message = message_data.get('text', '')
            metadata = message_data.get('metadata', {})
            user_id = message_data.get('user_id', 'user')
        else:
            return {'error': "Invalid message format"}
        
        # Get personality profile
        personality_profile = None
        if self.personality_manager:
            personality_profile = await self.personality_manager.get_personality_profile()
        
        # Get relevant memories
        memory_context = None
        if self.memory_manager:
            memories = await self.memory_manager.search_memories(message, limit=3)
            memory_context = {'relevant_memories': memories}
        
        # Process message with conversation manager
        if self.conversation_manager:
            response = await self.conversation_manager.process_message(
                message=message,
                user_id=user_id,
                metadata=metadata,
                personality_profile=personality_profile,
                memory_context=memory_context
            )
            
            # Store conversation as memory
            if self.memory_manager:
                await self.memory_manager.store_memory(
                    content={
                        'message': message,
                        'response': response['text']
                    },
                    memory_type='episodic',
                    importance=0.5,
                    metadata={
                        'user_id': user_id,
                        'entities': response.get('entities', []),
                        'topics': response.get('topics', [])
                    },
                    categories=['social']
                )
            
            return response
        else:
            return {'error': "Conversation manager not available"}
    
    async def _process_event(self, event_data: Any) -> Dict[str, Any]:
        """
        Process an event input.
        
        Args:
            event_data: Event data
            
        Returns:
            Dictionary containing the response
        """
        # Extract event details
        if not isinstance(event_data, dict):
            return {'error': "Invalid event format"}
        
        event_type = event_data.get('type', 'unknown')
        event_content = event_data.get('content', {})
        
        # Store event as memory
        if self.memory_manager:
            await self.memory_manager.store_memory(
                content=event_content,
                memory_type='episodic',
                importance=0.4,
                metadata={
                    'event_type': event_type
                },
                categories=['personal']
            )
        
        # Update personality based on event
        if self.personality_manager and event_type == 'personality_feedback':
            await self.personality_manager.adapt_personality(event_content)
        
        return {
            'status': 'event_processed',
            'event_type': event_type
        }
    
    async def _process_feedback(self, feedback_data: Any) -> Dict[str, Any]:
        """
        Process feedback input.
        
        Args:
            feedback_data: Feedback data
            
        Returns:
            Dictionary containing the response
        """
        # Extract feedback details
        if not isinstance(feedback_data, dict):
            return {'error': "Invalid feedback format"}
        
        feedback_type = feedback_data.get('type', 'general')
        feedback_content = feedback_data.get('content', {})
        
        # Process based on feedback type
        if feedback_type == 'conversation':
            # Feedback about conversation
            if self.conversation_manager:
                # Update conversation settings if provided
                if 'settings' in feedback_content:
                    await self.conversation_manager.update_settings(feedback_content['settings'])
        
        elif feedback_type == 'personality':
            # Feedback about personality
            if self.personality_manager:
                await self.personality_manager.adapt_personality(feedback_content)
        
        elif feedback_type == 'memory':
            # Feedback about memory
            if self.memory_manager and 'memory_id' in feedback_content:
                memory_id = feedback_content['memory_id']
                
                if feedback_content.get('action') == 'forget':
                    await self.memory_manager.forget_memory(memory_id)
                elif feedback_content.get('action') == 'update' and 'content' in feedback_content:
                    await self.memory_manager.update_memory(
                        memory_id=memory_id,
                        content=feedback_content['content'],
                        importance=feedback_content.get('importance')
                    )
        
        return {
            'status': 'feedback_processed',
            'feedback_type': feedback_type
        }
    
    async def _update_cognitive_state(self, input_data: Any, input_type: str):
        """
        Update the cognitive state based on input.
        
        Args:
            input_data: Input data
            input_type: Type of input
        """
        # Update last updated timestamp
        self.cognitive_state['last_updated'] = datetime.now().isoformat()
        
        # Update current focus
        self.cognitive_state['current_focus'] = input_type
        
        # Update emotional state based on input
        if input_type == 'message' and isinstance(input_data, dict) and 'sentiment' in input_data:
            sentiment = input_data['sentiment']
            if 'valence' in sentiment:
                self.cognitive_state['emotional_state']['valence'] = sentiment['valence']
            if 'arousal' in sentiment:
                self.cognitive_state['emotional_state']['arousal'] = sentiment['arousal']
    
    async def get_cognitive_state(self) -> Dict[str, Any]:
        """
        Get the current cognitive state.
        
        Returns:
            Dictionary containing the cognitive state
        """
        logger.info("Getting cognitive state")
        
        if not self.initialized:
            await self.initialize()
        
        # Get personality state
        personality_state = {}
        if self.personality_manager:
            personality_state = await self.personality_manager.get_personality_profile()
        
        # Get memory stats
        memory_stats = {}
        if self.memory_manager:
            memory_stats = await self.memory_manager.get_memory_stats()
        
        # Get conversation analysis
        conversation_analysis = {}
        if self.conversation_manager:
            conversation_analysis = await self.conversation_manager.analyze_conversation()
        
        # Combine with cognitive state
        state = {
            'cognitive': self.cognitive_state,
            'personality': personality_state,
            'memory': memory_stats,
            'conversation': conversation_analysis
        }
        
        return state
    
    async def maintenance(self):
        """Perform maintenance tasks."""
        logger.info("Performing cognitive twin maintenance")
        
        if not self.initialized:
            await self.initialize()
        
        # Perform memory maintenance
        if self.memory_manager:
            await self.memory_manager.maintenance()
        
        # Update cognitive state
        self.cognitive_state['last_updated'] = datetime.now().isoformat()
        
        logger.info("Cognitive twin maintenance complete")