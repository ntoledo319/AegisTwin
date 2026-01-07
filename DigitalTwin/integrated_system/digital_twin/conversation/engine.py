"""
Conversation engine for the digital twin.

This module provides the core conversation engine for the digital twin,
responsible for generating and processing conversational interactions.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationEngine:
    """Core conversation engine for the digital twin."""
    
    def __init__(self):
        """Initialize the conversation engine."""
        self.conversation_history = []
        self.context = {}
        self.conversation_state = "idle"
        self.conversation_settings = {
            "response_length": "medium",  # short, medium, long
            "formality_level": "neutral",  # casual, neutral, formal
            "creativity_level": "balanced",  # conservative, balanced, creative
            "empathy_level": "medium"  # low, medium, high
        }
        self.initialized = False
        self.history_path = "data/conversation_history.json"
        self.max_history_length = 100  # Maximum number of messages to keep in history
    
    async def initialize(self):
        """Initialize the conversation engine."""
        logger.info("Initializing conversation engine")
        
        # Try to load conversation history from file
        if await self._load_history():
            logger.info("Loaded conversation history from file")
        else:
            logger.info("Starting with empty conversation history")
        
        self.initialized = True
        logger.info("Conversation engine initialized")
    
    async def _load_history(self) -> bool:
        """
        Load conversation history from file.
        
        Returns:
            True if history was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r') as f:
                    history_data = json.load(f)
                
                # Load conversation history
                if 'history' in history_data:
                    self.conversation_history = history_data['history']
                
                # Load context
                if 'context' in history_data:
                    self.context = history_data['context']
                
                # Load settings
                if 'settings' in history_data:
                    self.conversation_settings = history_data['settings']
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
            return False
    
    async def _save_history(self):
        """Save conversation history to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            
            # Create history data
            history_data = {
                'history': self.conversation_history[-self.max_history_length:],  # Keep only recent history
                'context': self.context,
                'settings': self.conversation_settings,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logger.info("Saved conversation history to file")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation history: {str(e)}")
            return False
    
    async def process_message(self, message: str, user_id: str = "user", 
                             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process an incoming message.
        
        Args:
            message: The message text
            user_id: ID of the user sending the message
            metadata: Additional message metadata
            
        Returns:
            Dictionary containing the response
        """
        logger.info(f"Processing message from {user_id}")
        
        if not self.initialized:
            await self.initialize()
        
        # Create message object
        timestamp = datetime.now().isoformat()
        message_obj = {
            'text': message,
            'user_id': user_id,
            'timestamp': timestamp,
            'type': 'incoming'
        }
        
        # Add metadata if provided
        if metadata:
            message_obj['metadata'] = metadata
        
        # Add to history
        self.conversation_history.append(message_obj)
        
        # Update conversation state
        self.conversation_state = "processing"
        
        # Generate response
        response = await self._generate_response(message, user_id)
        
        # Create response object
        response_obj = {
            'text': response['text'],
            'user_id': 'digital_twin',
            'timestamp': datetime.now().isoformat(),
            'type': 'outgoing'
        }
        
        # Add metadata if provided
        if 'metadata' in response:
            response_obj['metadata'] = response['metadata']
        
        # Add to history
        self.conversation_history.append(response_obj)
        
        # Update conversation state
        self.conversation_state = "idle"
        
        # Save history
        await self._save_history()
        
        return response
    
    async def _generate_response(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Generate a response to a message using real AI.
        
        Args:
            message: The message text
            user_id: ID of the user sending the message
            
        Returns:
            Dictionary containing the response text and metadata
        """
        try:
            # Import AI modules
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../src'))
            
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.ai.personality_ai import PersonalityAI
            
            # Initialize AI components
            conversation_ai = ConversationAI()
            personality_ai = PersonalityAI()
            
            # Get user's personality profile
            personality_profile = None
            try:
                # Try to get existing personality profile
                personality_profile = await self._get_user_personality(user_id)
            except Exception as e:
                logger.warning(f"Could not load personality profile for user {user_id}: {e}")
            
            # Get conversation context
            conversation_context = await self._get_conversation_context(user_id)
            
            # Determine response style based on personality
            response_style = "balanced"
            if personality_profile:
                traits = personality_profile.get("big_five", {})
                if traits.get("openness", 0.5) > 0.7:
                    response_style = "creative"
                elif traits.get("conscientiousness", 0.5) > 0.7:
                    response_style = "analytical"
                elif traits.get("agreeableness", 0.5) > 0.7:
                    response_style = "empathetic"
            
            # Generate AI response
            ai_response = await conversation_ai.generate_response(
                message=message,
                user_id=user_id,
                personality_profile=personality_profile,
                conversation_context=conversation_context,
                response_style=response_style
            )
            
            # Extract response and metadata
            response_text = ai_response.get("text", "I'm having trouble processing your message right now.")
            ai_metadata = ai_response.get("metadata", {})
            
            # Combine with our metadata
            metadata = {
                'response_type': 'ai_generated',
                'model_used': ai_metadata.get('model_used', 'unknown'),
                'provider': ai_metadata.get('provider', 'unknown'),
                'personality_applied': ai_metadata.get('personality_applied', False),
                'response_style': response_style,
                'confidence': ai_metadata.get('response_analysis', {}).get('personality_consistency', 0.8),
                'processing_time': 0.5,  # AI processing takes longer
                'cost_estimate': ai_metadata.get('cost_estimate', 0.0)
            }
            
            return {
                'text': response_text,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            
            # Fallback to intelligent placeholder
            fallback_response = self._generate_fallback_response(message, user_id)
            
            return {
                'text': fallback_response,
                'metadata': {
                    'response_type': 'fallback',
                    'error': str(e),
                    'processing_time': 0.1,
                    'confidence': 0.3
                }
            }
    
    async def _get_user_personality(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's personality profile"""
        try:
            # Try to load from personality manager
            if hasattr(self, 'personality_manager') and self.personality_manager:
                return await self.personality_manager.get_profile(user_id)
            
            # Try to load from memory manager
            if hasattr(self, 'memory_manager') and self.memory_manager:
                personality_data = await self.memory_manager.get_personality_data(user_id)
                if personality_data:
                    return personality_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not load personality for user {user_id}: {e}")
            return None
    
    async def _get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context for user"""
        try:
            # Get recent conversation history
            recent_history = await self.get_conversation_history(limit=5, user_id=user_id)
            
            if not recent_history:
                return None
            
            # Extract context information
            context = {
                "recent_topics": [],
                "conversation_tone": "neutral",
                "user_preferences": {},
                "conversation_length": len(recent_history)
            }
            
            # Analyze recent messages for context
            recent_messages = [h.get("message", "") for h in recent_history[-3:]]
            if recent_messages:
                # Simple topic extraction
                all_words = []
                for msg in recent_messages:
                    words = msg.lower().split()
                    all_words.extend([w for w in words if len(w) > 4])
                
                from collections import Counter
                word_counts = Counter(all_words)
                context["recent_topics"] = [word for word, count in word_counts.most_common(3)]
            
            return context
            
        except Exception as e:
            logger.warning(f"Could not get conversation context for user {user_id}: {e}")
            return None
    
    def _generate_fallback_response(self, message: str, user_id: str) -> str:
        """Generate intelligent fallback response when AI fails"""
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm your digital twin. I'm here to help you understand yourself better through our conversations."
        
        elif any(word in message_lower for word in ["how", "what", "why", "when", "where"]):
            return "That's an interesting question. I'm designed to help you explore your thoughts and patterns. Could you tell me more about what you're thinking?"
        
        elif any(word in message_lower for word in ["help", "assist", "support"]):
            return "I'm here to help you understand your communication patterns, personality traits, and behavioral insights. What would you like to explore?"
        
        elif any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
            return "You're welcome! I enjoy our conversations and learning about your unique perspective."
        
        elif any(word in message_lower for word in ["feel", "feeling", "emotion", "mood"]):
            return "I can sense you're sharing something personal. I'm designed to understand emotional patterns and help you process your feelings."
        
        else:
            return f"I understand you're saying: '{message}'. I'm your digital twin, designed to mirror and understand your communication style. What would you like to explore about yourself?"
    
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
        
        # Filter by user ID if provided
        if user_id:
            filtered_history = [msg for msg in self.conversation_history if msg.get('user_id') == user_id]
        else:
            filtered_history = self.conversation_history
        
        # Return most recent messages first
        return list(reversed(filtered_history))[-limit:]
    
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
        
        # Update settings
        for key, value in settings.items():
            if key in self.conversation_settings:
                self.conversation_settings[key] = value
        
        # Save history
        await self._save_history()
        
        return self.conversation_settings
    
    async def clear_history(self) -> bool:
        """
        Clear conversation history.
        
        Returns:
            True if history was cleared successfully
        """
        logger.info("Clearing conversation history")
        
        if not self.initialized:
            await self.initialize()
        
        # Clear history
        self.conversation_history = []
        
        # Save history
        await self._save_history()
        
        return True
    
    async def analyze_conversation(self) -> Dict[str, Any]:
        """
        Analyze the conversation history.
        
        Returns:
            Dictionary of analysis results
        """
        logger.info("Analyzing conversation")
        
        if not self.initialized:
            await self.initialize()
        
        # Count messages by user
        user_counts = {}
        for msg in self.conversation_history:
            user_id = msg.get('user_id', 'unknown')
            if user_id in user_counts:
                user_counts[user_id] += 1
            else:
                user_counts[user_id] = 1
        
        # Calculate average message length
        total_length = 0
        message_count = 0
        for msg in self.conversation_history:
            if 'text' in msg:
                total_length += len(msg['text'])
                message_count += 1
        
        avg_length = total_length / message_count if message_count > 0 else 0
        
        # Calculate conversation duration
        duration = 0
        if len(self.conversation_history) >= 2:
            try:
                first_msg = self.conversation_history[0]
                last_msg = self.conversation_history[-1]
                
                first_time = datetime.fromisoformat(first_msg['timestamp'])
                last_time = datetime.fromisoformat(last_msg['timestamp'])
                
                duration = (last_time - first_time).total_seconds()
            except:
                pass
        
        return {
            'message_count': len(self.conversation_history),
            'user_counts': user_counts,
            'avg_message_length': avg_length,
            'conversation_duration': duration
        }