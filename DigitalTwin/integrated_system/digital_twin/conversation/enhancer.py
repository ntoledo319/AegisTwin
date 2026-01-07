"""
Conversation enhancer for the digital twin.

This module provides advanced conversation capabilities for the digital twin,
enhancing the basic conversation engine with context awareness, memory integration,
and personality-driven responses.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ConversationEnhancer:
    """Advanced conversation enhancer for the digital twin."""
    
    def __init__(self):
        """Initialize the conversation enhancer."""
        self.context_window = []  # Recent conversation context
        self.context_window_size = 10  # Number of messages to keep in context window
        self.topic_history = []  # History of conversation topics
        self.entity_memory = {}  # Memory of entities mentioned in conversation
        self.conversation_metrics = {
            'user_engagement': 0.5,
            'conversation_depth': 0.5,
            'topic_coherence': 0.5,
            'emotional_tone': 'neutral'
        }
        self.nlp_available = False
        self.initialized = False
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for conversation enhancement")
    
    async def initialize(self):
        """Initialize the conversation enhancer."""
        logger.info("Initializing conversation enhancer")
        
        self.initialized = True
        logger.info("Conversation enhancer initialized")
    
    async def enhance_response(self, message: str, draft_response: str, 
                              conversation_history: List[Dict[str, Any]],
                              personality_profile: Dict[str, Any] = None,
                              memory_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhance a draft response with context awareness and personality.
        
        Args:
            message: The incoming message
            draft_response: The draft response to enhance
            conversation_history: Recent conversation history
            personality_profile: Personality profile (optional)
            memory_context: Memory context (optional)
            
        Returns:
            Dictionary containing the enhanced response
        """
        logger.info("Enhancing conversation response")
        
        if not self.initialized:
            await self.initialize()
        
        # Update context window
        self._update_context_window(message, conversation_history)
        
        # Extract entities and topics
        entities, topics = await self._extract_entities_and_topics(message)
        
        # Update entity memory
        self._update_entity_memory(entities)
        
        # Update topic history
        self._update_topic_history(topics)
        
        # Analyze conversation metrics
        self._analyze_conversation_metrics(conversation_history)
        
        # Apply personality to response if profile is provided
        if personality_profile:
            enhanced_response = await self._apply_personality(draft_response, personality_profile)
        else:
            enhanced_response = draft_response
        
        # Integrate memory context if provided
        if memory_context:
            enhanced_response = await self._integrate_memory(enhanced_response, memory_context)
        
        # Ensure response coherence with context
        enhanced_response = await self._ensure_coherence(enhanced_response, self.context_window)
        
        # Add contextual references
        enhanced_response = await self._add_contextual_references(enhanced_response, entities, topics)
        
        return {
            'text': enhanced_response,
            'entities': entities,
            'topics': topics,
            'metrics': self.conversation_metrics
        }
    
    def _update_context_window(self, message: str, conversation_history: List[Dict[str, Any]]):
        """
        Update the context window with recent messages.
        
        Args:
            message: The current message
            conversation_history: Recent conversation history
        """
        # Add recent messages to context window
        recent_messages = conversation_history[-self.context_window_size:] if conversation_history else []
        
        # Create context window
        self.context_window = []
        for msg in recent_messages:
            if 'text' in msg:
                self.context_window.append({
                    'text': msg['text'],
                    'user_id': msg.get('user_id', 'unknown'),
                    'timestamp': msg.get('timestamp', '')
                })
        
        # Add current message
        self.context_window.append({
            'text': message,
            'user_id': 'user',
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit context window size
        self.context_window = self.context_window[-self.context_window_size:]
    
    async def _extract_entities_and_topics(self, text: str) -> tuple:
        """
        Extract entities and topics from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (entities, topics)
        """
        entities = []
        topics = []
        
        if self.nlp_available:
            try:
                # Process text with spaCy
                doc = self.nlp(text)
                
                # Extract named entities
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                
                # Extract noun chunks as potential topics
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) <= 3:  # Limit to short phrases
                        topics.append(chunk.text.lower())
                
                # Remove duplicates
                topics = list(set(topics))
            except Exception as e:
                logger.error(f"Error extracting entities and topics: {str(e)}")
        else:
            # Fallback simple extraction
            # Extract potential entities (capitalized words)
            for match in re.finditer(r'\b[A-Z][a-zA-Z]*\b', text):
                entities.append({
                    'text': match.group(),
                    'label': 'UNKNOWN',
                    'start': match.start(),
                    'end': match.end()
                })
            
            # Extract potential topics (nouns)
            words = text.lower().split()
            topics = [word for word in words if len(word) > 3]  # Simple heuristic
        
        return entities, topics
    
    def _update_entity_memory(self, entities: List[Dict[str, Any]]):
        """
        Update entity memory with new entities.
        
        Args:
            entities: List of entities
        """
        for entity in entities:
            entity_text = entity['text']
            entity_type = entity['label']
            
            if entity_text in self.entity_memory:
                # Update existing entity
                self.entity_memory[entity_text]['count'] += 1
                self.entity_memory[entity_text]['last_mentioned'] = datetime.now().isoformat()
            else:
                # Add new entity
                self.entity_memory[entity_text] = {
                    'type': entity_type,
                    'count': 1,
                    'first_mentioned': datetime.now().isoformat(),
                    'last_mentioned': datetime.now().isoformat()
                }
    
    def _update_topic_history(self, topics: List[str]):
        """
        Update topic history with new topics.
        
        Args:
            topics: List of topics
        """
        timestamp = datetime.now().isoformat()
        
        for topic in topics:
            # Check if topic already in history
            existing = False
            for topic_entry in self.topic_history:
                if topic_entry['topic'] == topic:
                    topic_entry['count'] += 1
                    topic_entry['last_mentioned'] = timestamp
                    existing = True
                    break
            
            # Add new topic if not existing
            if not existing:
                self.topic_history.append({
                    'topic': topic,
                    'count': 1,
                    'first_mentioned': timestamp,
                    'last_mentioned': timestamp
                })
        
        # Limit topic history size
        self.topic_history = sorted(self.topic_history, key=lambda x: x['last_mentioned'], reverse=True)[:50]
    
    def _analyze_conversation_metrics(self, conversation_history: List[Dict[str, Any]]):
        """
        Analyze conversation metrics.
        
        Args:
            conversation_history: Recent conversation history
        """
        if not conversation_history:
            return
        
        # Calculate user engagement (based on message frequency and length)
        user_messages = [msg for msg in conversation_history if msg.get('user_id') != 'digital_twin']
        if user_messages:
            # Calculate average message length
            avg_length = sum(len(msg.get('text', '')) for msg in user_messages) / len(user_messages)
            
            # Normalize to 0-1 range
            normalized_length = min(1.0, avg_length / 100)  # Assume 100 chars is "fully engaged"
            
            # Calculate message frequency
            if len(user_messages) >= 2:
                try:
                    first_msg = user_messages[0]
                    last_msg = user_messages[-1]
                    
                    first_time = datetime.fromisoformat(first_msg.get('timestamp', datetime.now().isoformat()))
                    last_time = datetime.fromisoformat(last_msg.get('timestamp', datetime.now().isoformat()))
                    
                    duration = (last_time - first_time).total_seconds()
                    if duration > 0:
                        frequency = len(user_messages) / (duration / 60)  # Messages per minute
                        normalized_frequency = min(1.0, frequency / 3)  # Assume 3 msgs/min is "fully engaged"
                    else:
                        normalized_frequency = 0.5
                except:
                    normalized_frequency = 0.5
            else:
                normalized_frequency = 0.5
            
            # Combine length and frequency
            self.conversation_metrics['user_engagement'] = (normalized_length * 0.5) + (normalized_frequency * 0.5)
        
        # Calculate conversation depth (based on topic consistency and message complexity)
        if len(self.topic_history) > 0:
            # Calculate topic consistency
            top_topics = sorted(self.topic_history, key=lambda x: x['count'], reverse=True)[:3]
            top_topic_count = sum(topic['count'] for topic in top_topics)
            total_topic_mentions = sum(topic['count'] for topic in self.topic_history)
            
            topic_consistency = top_topic_count / total_topic_mentions if total_topic_mentions > 0 else 0.5
            
            # Calculate message complexity
            all_messages = [msg.get('text', '') for msg in conversation_history if 'text' in msg]
            avg_words_per_message = sum(len(msg.split()) for msg in all_messages) / len(all_messages) if all_messages else 0
            
            normalized_complexity = min(1.0, avg_words_per_message / 20)  # Assume 20 words is "complex"
            
            # Combine consistency and complexity
            self.conversation_metrics['conversation_depth'] = (topic_consistency * 0.5) + (normalized_complexity * 0.5)
        
        # Calculate topic coherence
        if len(self.topic_history) > 0:
            recent_topics = [topic for topic in self.topic_history if 
                            (datetime.now() - datetime.fromisoformat(topic['last_mentioned'])).total_seconds() < 300]
            
            if recent_topics:
                # Higher coherence if fewer recent topics
                topic_coherence = 1.0 - min(1.0, (len(recent_topics) - 1) / 5)  # 1-2 topics is high coherence
                self.conversation_metrics['topic_coherence'] = topic_coherence
        
        # Determine emotional tone (placeholder - would use sentiment analysis in real implementation)
        self.conversation_metrics['emotional_tone'] = 'neutral'
    
    async def _apply_personality(self, response: str, personality_profile: Dict[str, Any]) -> str:
        """
        Apply personality traits to a response.
        
        Args:
            response: Draft response
            personality_profile: Personality profile
            
        Returns:
            Personality-enhanced response
        """
        # Extract relevant personality traits
        traits = personality_profile.get('traits', {})
        openness = traits.get('openness', 0.5)
        conscientiousness = traits.get('conscientiousness', 0.5)
        extraversion = traits.get('extraversion', 0.5)
        agreeableness = traits.get('agreeableness', 0.5)
        neuroticism = traits.get('neuroticism', 0.5)
        
        # Apply personality traits to response
        enhanced_response = response
        
        # Adjust response based on extraversion
        if extraversion > 0.7:
            # More enthusiastic, expressive language
            enhanced_response = enhanced_response.replace(".", "!")
            enhanced_response = re.sub(r'\b(good|nice|great)\b', r'fantastic', enhanced_response, flags=re.IGNORECASE)
        elif extraversion < 0.3:
            # More reserved language
            enhanced_response = enhanced_response.replace("!", ".")
            enhanced_response = re.sub(r'\b(fantastic|amazing|excellent)\b', r'good', enhanced_response, flags=re.IGNORECASE)
        
        # Adjust response based on agreeableness
        if agreeableness > 0.7:
            # More agreeable, supportive language
            enhanced_response = f"I'm happy to help! {enhanced_response}"
        elif agreeableness < 0.3:
            # More direct, less agreeable language
            enhanced_response = re.sub(r'^(I\'m happy to help!|Certainly!|Of course!)\s+', '', enhanced_response)
        
        # Adjust response based on conscientiousness
        if conscientiousness > 0.7:
            # More detailed, thorough responses
            enhanced_response = f"{enhanced_response} Let me know if you need any clarification or have additional questions."
        
        # Adjust response based on openness
        if openness > 0.7:
            # More creative, exploratory language
            enhanced_response = f"{enhanced_response} This opens up some interesting possibilities to explore."
        
        # Adjust response based on neuroticism
        if neuroticism > 0.7:
            # More cautious language
            enhanced_response = enhanced_response.replace("definitely", "probably")
            enhanced_response = enhanced_response.replace("certainly", "likely")
        
        return enhanced_response
    
    async def _integrate_memory(self, response: str, memory_context: Dict[str, Any]) -> str:
        """
        Integrate memory context into response.
        
        Args:
            response: Draft response
            memory_context: Memory context
            
        Returns:
            Memory-enhanced response
        """
        enhanced_response = response
        
        # Check if memory context contains relevant memories
        if 'relevant_memories' in memory_context and memory_context['relevant_memories']:
            # Get most relevant memory
            memory = memory_context['relevant_memories'][0]
            
            # Add memory reference if appropriate
            if 'content' in memory:
                memory_content = memory['content']
                if isinstance(memory_content, str):
                    # Add memory reference
                    enhanced_response = f"{enhanced_response} I recall that {memory_content}"
        
        return enhanced_response
    
    async def _ensure_coherence(self, response: str, context_window: List[Dict[str, Any]]) -> str:
        """
        Ensure response is coherent with conversation context.
        
        Args:
            response: Draft response
            context_window: Recent conversation context
            
        Returns:
            Coherent response
        """
        # Simple coherence check - avoid repeating the exact same response
        if context_window and len(context_window) >= 2:
            previous_responses = [msg['text'] for msg in context_window if msg.get('user_id') == 'digital_twin']
            
            if previous_responses and response in previous_responses:
                # Avoid repetition by adding a prefix
                response = f"As I mentioned, {response}"
        
        return response
    
    async def _add_contextual_references(self, response: str, entities: List[Dict[str, Any]], topics: List[str]) -> str:
        """
        Add contextual references to entities and topics.
        
        Args:
            response: Draft response
            entities: Entities from current message
            topics: Topics from current message
            
        Returns:
            Response with contextual references
        """
        enhanced_response = response
        
        # Add reference to a frequently mentioned entity if appropriate
        frequent_entities = []
        for entity_text, entity_data in self.entity_memory.items():
            if entity_data['count'] > 2:
                frequent_entities.append((entity_text, entity_data))
        
        if frequent_entities and not any(entity['text'] in response for entity in entities):
            # Sort by count (most frequent first)
            frequent_entities.sort(key=lambda x: x[1]['count'], reverse=True)
            
            # Add reference to most frequent entity
            entity_text = frequent_entities[0][0]
            if entity_text not in response:
                enhanced_response = f"{enhanced_response} This relates to our previous discussion about {entity_text}."
        
        return enhanced_response
    
    async def get_conversation_insights(self) -> Dict[str, Any]:
        """
        Get insights about the conversation.
        
        Returns:
            Dictionary of conversation insights
        """
        logger.info("Getting conversation insights")
        
        if not self.initialized:
            await self.initialize()
        
        # Get top entities
        top_entities = []
        for entity_text, entity_data in sorted(self.entity_memory.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            top_entities.append({
                'text': entity_text,
                'type': entity_data['type'],
                'count': entity_data['count']
            })
        
        # Get top topics
        top_topics = sorted(self.topic_history, key=lambda x: x['count'], reverse=True)[:5]
        
        # Get conversation metrics
        metrics = self.conversation_metrics.copy()
        
        return {
            'top_entities': top_entities,
            'top_topics': top_topics,
            'metrics': metrics
        }