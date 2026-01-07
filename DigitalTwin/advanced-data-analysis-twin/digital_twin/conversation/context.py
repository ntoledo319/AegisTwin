"""
Context Manager for the Digital Twin's Conversation Engine.

This module provides functionality for managing conversation context,
including topic tracking, entity tracking, and conversation state.
"""

import logging
import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manager for conversation context.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the context manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.max_context_history = self.config.get("max_context_history", 10)
        self.max_topics_history = self.config.get("max_topics_history", 5)
        self.max_entities_history = self.config.get("max_entities_history", 20)
        self.max_intents_history = self.config.get("max_intents_history", 5)
        logger.info("Context Manager initialized")

    async def update_context(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the conversation context based on a new message.

        Args:
            user_id: User ID
            message: User message
            context: Current conversation context

        Returns:
            Updated conversation context
        """
        # Create a copy of the context to update
        updated_context = context.copy()
        
        # Update basic context information
        updated_context["last_update_time"] = datetime.datetime.now().isoformat()
        updated_context["turn_count"] = context.get("turn_count", 0) + 1
        
        # Add the current message to the history
        if "message_history" not in updated_context:
            updated_context["message_history"] = []
            
        message_entry = {
            "role": "user",
            "content": message,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        updated_context["message_history"].append(message_entry)
        
        # Limit the history size
        if len(updated_context["message_history"]) > self.max_context_history:
            updated_context["message_history"] = updated_context["message_history"][-self.max_context_history:]
            
        # Update the current topic (will be filled by the ConversationAnalyzer)
        if "current_topic" in updated_context and updated_context["current_topic"]:
            # Move current topic to previous topics if it's going to change
            if "previous_topics" not in updated_context:
                updated_context["previous_topics"] = []
                
            # Only add to previous topics if not already there
            if updated_context["current_topic"] not in updated_context["previous_topics"]:
                updated_context["previous_topics"].insert(0, updated_context["current_topic"])
                
                # Limit the previous topics size
                if len(updated_context["previous_topics"]) > self.max_topics_history:
                    updated_context["previous_topics"] = updated_context["previous_topics"][:self.max_topics_history]
                    
        # Initialize entities_mentioned if not present
        if "entities_mentioned" not in updated_context:
            updated_context["entities_mentioned"] = []
            
        # Initialize user_intents if not present
        if "user_intents" not in updated_context:
            updated_context["user_intents"] = []
            
        # Update conversation state based on turn count
        if updated_context["turn_count"] == 1:
            updated_context["conversation_state"] = "greeting"
        elif updated_context["turn_count"] > 10:
            updated_context["conversation_state"] = "ongoing"
        else:
            updated_context["conversation_state"] = "exploration"
            
        logger.debug(f"Updated context for user {user_id}, turn {updated_context['turn_count']}")
        return updated_context

    async def update_context_with_analysis(self, context: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the conversation context with analysis results.

        Args:
            context: Current conversation context
            analysis: Message analysis results

        Returns:
            Updated conversation context
        """
        # Create a copy of the context to update
        updated_context = context.copy()
        
        # Update topic
        if "topic" in analysis and analysis["topic"]:
            updated_context["current_topic"] = analysis["topic"]
            
        # Update entities
        if "entities" in analysis and analysis["entities"]:
            if "entities_mentioned" not in updated_context:
                updated_context["entities_mentioned"] = []
                
            # Add new entities
            for entity in analysis["entities"]:
                if entity not in updated_context["entities_mentioned"]:
                    updated_context["entities_mentioned"].insert(0, entity)
                    
            # Limit the entities size
            if len(updated_context["entities_mentioned"]) > self.max_entities_history:
                updated_context["entities_mentioned"] = updated_context["entities_mentioned"][:self.max_entities_history]
                
        # Update intents
        if "intent" in analysis and analysis["intent"]:
            if "user_intents" not in updated_context:
                updated_context["user_intents"] = []
                
            # Add new intent
            if analysis["intent"] not in updated_context["user_intents"]:
                updated_context["user_intents"].insert(0, analysis["intent"])
                
            # Limit the intents size
            if len(updated_context["user_intents"]) > self.max_intents_history:
                updated_context["user_intents"] = updated_context["user_intents"][:self.max_intents_history]
                
        # Update sentiment
        if "sentiment" in analysis:
            updated_context["current_sentiment"] = analysis["sentiment"]
            
        # Update conversation state based on intent
        if "intent" in analysis:
            intent = analysis["intent"]
            
            if intent in ["goodbye", "end_conversation", "exit"]:
                updated_context["conversation_state"] = "ending"
            elif intent in ["help", "confused"]:
                updated_context["conversation_state"] = "helping"
            elif intent in ["angry", "frustrated"]:
                updated_context["conversation_state"] = "de-escalating"
                
        logger.debug(f"Updated context with analysis results")
        return updated_context

    async def merge_contexts(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two conversation contexts.

        Args:
            context1: First context
            context2: Second context

        Returns:
            Merged context
        """
        # Create a copy of the first context
        merged_context = context1.copy()
        
        # Merge basic fields
        merged_context["turn_count"] = max(context1.get("turn_count", 0), context2.get("turn_count", 0))
        merged_context["last_update_time"] = max(
            context1.get("last_update_time", ""),
            context2.get("last_update_time", "")
        )
        
        # Merge message history
        if "message_history" in context1 and "message_history" in context2:
            # Combine and sort by timestamp
            combined_history = context1["message_history"] + context2["message_history"]
            combined_history.sort(key=lambda x: x.get("timestamp", ""))
            
            # Limit the history size
            merged_context["message_history"] = combined_history[-self.max_context_history:]
        elif "message_history" in context2:
            merged_context["message_history"] = context2["message_history"]
            
        # Merge topics
        if "current_topic" in context2 and context2["current_topic"]:
            merged_context["current_topic"] = context2["current_topic"]
            
        # Merge previous topics
        if "previous_topics" in context1 and "previous_topics" in context2:
            # Combine topics, keeping order and removing duplicates
            topics = []
            for topic in context2["previous_topics"] + context1["previous_topics"]:
                if topic not in topics:
                    topics.append(topic)
                    
            # Limit the topics size
            merged_context["previous_topics"] = topics[:self.max_topics_history]
        elif "previous_topics" in context2:
            merged_context["previous_topics"] = context2["previous_topics"]
            
        # Merge entities
        if "entities_mentioned" in context1 and "entities_mentioned" in context2:
            # Combine entities, removing duplicates
            entities = []
            for entity in context2["entities_mentioned"] + context1["entities_mentioned"]:
                if entity not in entities:
                    entities.append(entity)
                    
            # Limit the entities size
            merged_context["entities_mentioned"] = entities[:self.max_entities_history]
        elif "entities_mentioned" in context2:
            merged_context["entities_mentioned"] = context2["entities_mentioned"]
            
        # Merge intents
        if "user_intents" in context1 and "user_intents" in context2:
            # Combine intents, removing duplicates
            intents = []
            for intent in context2["user_intents"] + context1["user_intents"]:
                if intent not in intents:
                    intents.append(intent)
                    
            # Limit the intents size
            merged_context["user_intents"] = intents[:self.max_intents_history]
        elif "user_intents" in context2:
            merged_context["user_intents"] = context2["user_intents"]
            
        # Use the most recent conversation state
        if "conversation_state" in context2:
            merged_context["conversation_state"] = context2["conversation_state"]
            
        logger.debug(f"Merged two conversation contexts")
        return merged_context

    async def get_context_summary(self, context: Dict[str, Any]) -> str:
        """
        Generate a summary of the conversation context.

        Args:
            context: Conversation context

        Returns:
            Context summary string
        """
        summary_parts = []
        
        # Add conversation ID
        conversation_id = context.get("conversation_id", "unknown")
        summary_parts.append(f"Conversation ID: {conversation_id}")
        
        # Add turn count
        turn_count = context.get("turn_count", 0)
        summary_parts.append(f"Turns: {turn_count}")
        
        # Add current topic
        current_topic = context.get("current_topic", "none")
        if current_topic:
            summary_parts.append(f"Current topic: {current_topic}")
            
        # Add previous topics
        previous_topics = context.get("previous_topics", [])
        if previous_topics:
            topics_str = ", ".join(previous_topics[:3])
            summary_parts.append(f"Previous topics: {topics_str}")
            
        # Add entities
        entities = context.get("entities_mentioned", [])
        if entities:
            entities_str = ", ".join(entities[:5])
            summary_parts.append(f"Entities: {entities_str}")
            
        # Add conversation state
        state = context.get("conversation_state", "unknown")
        summary_parts.append(f"State: {state}")
        
        # Add current sentiment
        sentiment = context.get("current_sentiment", "neutral")
        summary_parts.append(f"Sentiment: {sentiment}")
        
        return " | ".join(summary_parts)

    async def get_recent_messages(self, context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Get the most recent messages from the conversation history.

        Args:
            context: Conversation context
            count: Number of messages to retrieve

        Returns:
            List of recent messages
        """
        message_history = context.get("message_history", [])
        return message_history[-count:]

    async def get_conversation_duration(self, context: Dict[str, Any]) -> float:
        """
        Calculate the duration of the conversation in minutes.

        Args:
            context: Conversation context

        Returns:
            Conversation duration in minutes
        """
        start_time = context.get("start_time", "")
        last_update_time = context.get("last_update_time", "")
        
        if not start_time or not last_update_time:
            return 0.0
            
        try:
            start_datetime = datetime.datetime.fromisoformat(start_time)
            last_datetime = datetime.datetime.fromisoformat(last_update_time)
            
            duration = (last_datetime - start_datetime).total_seconds() / 60
            return max(0.0, duration)
        except (ValueError, TypeError):
            return 0.0