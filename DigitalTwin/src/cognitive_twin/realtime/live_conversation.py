"""
Live Conversation System

Provides real-time conversation capabilities with streaming responses
and live personality adaptation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

from .websocket_manager import WebSocketManager
from ..ai.conversation_ai import ConversationAI
from ..memory.memory_manager import MemoryManager
from ..events.event_bus import EventBus
from ..events.event_types import EventType, EventDataSchemas

logger = logging.getLogger(__name__)

class LiveConversation:
    """
    Real-time conversation system with streaming responses.
    
    Provides live conversation capabilities with personality-aware responses,
    real-time memory updates, and streaming message delivery.
    """
    
    def __init__(self, 
                 websocket_manager: WebSocketManager,
                 conversation_ai: ConversationAI,
                 memory_manager: MemoryManager,
                 event_bus: EventBus):
        """
        Initialize live conversation system.
        
        Args:
            websocket_manager: WebSocket manager for real-time communication
            conversation_ai: AI conversation system
            memory_manager: Memory management system
            event_bus: Event bus for system coordination
        """
        self.websocket_manager = websocket_manager
        self.conversation_ai = conversation_ai
        self.memory_manager = memory_manager
        self.event_bus = event_bus
        
        # Active conversations
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
        # Streaming responses
        self.streaming_responses: Dict[str, bool] = {}
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("Live conversation system initialized")
    
    def _register_handlers(self):
        """Register WebSocket message handlers"""
        self.websocket_manager.register_message_handler("start_conversation", self._handle_start_conversation)
        self.websocket_manager.register_message_handler("send_message", self._handle_send_message)
        self.websocket_manager.register_message_handler("end_conversation", self._handle_end_conversation)
        self.websocket_manager.register_message_handler("get_conversation_history", self._handle_get_history)
        self.websocket_manager.register_message_handler("update_personality", self._handle_update_personality)
    
    async def _handle_start_conversation(self, connection_id: str, message: Dict[str, Any]):
        """Handle conversation start request"""
        try:
            user_id = message.get("user_id")
            if not user_id:
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "user_id is required",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Start conversation
            conversation_id = await self._start_conversation(connection_id, user_id, message.get("options", {}))
            
            # Add to conversation group
            self.websocket_manager.add_to_group(connection_id, f"conversation_{conversation_id}")
            
            # Send confirmation
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "conversation_started",
                "conversation_id": conversation_id,
                "user_id": user_id,
                "message": "Conversation started successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Publish event
            await self.event_bus.publish(
                EventType.CONVERSATION_STARTED.value,
                {"user_id": user_id, "conversation_id": conversation_id, "connection_id": connection_id},
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Failed to start conversation: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_send_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle message send request"""
        try:
            user_message = message.get("message")
            conversation_id = message.get("conversation_id")
            user_id = message.get("user_id")
            
            if not all([user_message, conversation_id, user_id]):
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "message, conversation_id, and user_id are required",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Check if conversation exists
            if conversation_id not in self.active_conversations:
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "Conversation not found",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Send acknowledgment
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "message_received",
                "conversation_id": conversation_id,
                "message": "Processing your message...",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Process message with streaming response
            await self._process_message_with_streaming(
                connection_id, conversation_id, user_id, user_message
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Failed to process message: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_end_conversation(self, connection_id: str, message: Dict[str, Any]):
        """Handle conversation end request"""
        try:
            conversation_id = message.get("conversation_id")
            user_id = message.get("user_id")
            
            if not conversation_id:
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "conversation_id is required",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # End conversation
            await self._end_conversation(conversation_id, user_id)
            
            # Remove from group
            self.websocket_manager.remove_from_group(connection_id, f"conversation_{conversation_id}")
            
            # Send confirmation
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "conversation_ended",
                "conversation_id": conversation_id,
                "message": "Conversation ended",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Publish event
            await self.event_bus.publish(
                EventType.CONVERSATION_ENDED.value,
                {"user_id": user_id, "conversation_id": conversation_id},
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Failed to end conversation: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_get_history(self, connection_id: str, message: Dict[str, Any]):
        """Handle get conversation history request"""
        try:
            user_id = message.get("user_id")
            limit = message.get("limit", 10)
            
            if not user_id:
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "user_id is required",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Get conversation history
            history = await self.memory_manager.get_conversation_history(
                user_id=user_id,
                limit=limit,
                include_context=True
            )
            
            # Send history
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "conversation_history",
                "user_id": user_id,
                "history": history,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Failed to get history: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_update_personality(self, connection_id: str, message: Dict[str, Any]):
        """Handle personality update request"""
        try:
            user_id = message.get("user_id")
            personality_data = message.get("personality_data")
            
            if not all([user_id, personality_data]):
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "message": "user_id and personality_data are required",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Update personality
            await self.memory_manager.store_personality_data(
                user_id=user_id,
                personality_profile=personality_data,
                source="user_update"
            )
            
            # Send confirmation
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "personality_updated",
                "user_id": user_id,
                "message": "Personality updated successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Publish event
            await self.event_bus.publish(
                EventType.PERSONALITY_UPDATED.value,
                {"user_id": user_id, "personality_data": personality_data},
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error updating personality: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Failed to update personality: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _start_conversation(self, connection_id: str, user_id: str, options: Dict[str, Any]) -> str:
        """Start a new conversation"""
        conversation_id = f"conv_{user_id}_{datetime.utcnow().timestamp()}"
        
        # Get user's personality profile
        personality_profile = await self.memory_manager.get_personality_data(user_id)
        
        # Create conversation record
        self.active_conversations[conversation_id] = {
            "user_id": user_id,
            "connection_id": connection_id,
            "started_at": datetime.utcnow().isoformat(),
            "personality_profile": personality_profile,
            "message_count": 0,
            "options": options
        }
        
        logger.info(f"Started conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    async def _end_conversation(self, conversation_id: str, user_id: Optional[str] = None):
        """End a conversation"""
        if conversation_id in self.active_conversations:
            conversation = self.active_conversations[conversation_id]
            
            # Update conversation record
            conversation["ended_at"] = datetime.utcnow().isoformat()
            conversation["status"] = "ended"
            
            # Store conversation summary
            if user_id:
                await self.memory_manager.store_insight(
                    user_id=user_id,
                    insight=f"Conversation {conversation_id} ended with {conversation['message_count']} messages",
                    insight_type="conversation_summary",
                    confidence=1.0
                )
            
            # Remove from active conversations
            del self.active_conversations[conversation_id]
            
            logger.info(f"Ended conversation {conversation_id}")
    
    async def _process_message_with_streaming(
        self, 
        connection_id: str, 
        conversation_id: str, 
        user_id: str, 
        user_message: str
    ):
        """Process message with streaming response"""
        try:
            # Get conversation context
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                return
            
            # Get conversation context
            context = await self.memory_manager.get_context_for_conversation(
                user_id=user_id,
                current_message=user_message,
                context_window=5
            )
            
            # Generate streaming response
            response_stream = await self._generate_streaming_response(
                user_message, user_id, context, conversation
            )
            
            # Send streaming response
            full_response = ""
            async for chunk in response_stream:
                full_response += chunk
                
                # Send chunk to client
                await self.websocket_manager.send_to_connection(connection_id, {
                    "type": "response_chunk",
                    "conversation_id": conversation_id,
                    "chunk": chunk,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Send completion signal
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "response_complete",
                "conversation_id": conversation_id,
                "full_response": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Store conversation exchange
            await self.memory_manager.store_conversation(
                user_id=user_id,
                message=user_message,
                response=full_response,
                metadata={
                    "conversation_id": conversation_id,
                    "streaming": True,
                    "response_time": datetime.utcnow().isoformat()
                }
            )
            
            # Update conversation stats
            conversation["message_count"] += 1
            conversation["last_message_at"] = datetime.utcnow().isoformat()
            
            # Publish event
            await self.event_bus.publish(
                EventType.CONVERSATION_MESSAGE.value,
                EventDataSchemas.conversation_message(user_id, user_message, full_response, {
                    "conversation_id": conversation_id,
                    "streaming": True
                }),
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            await self.websocket_manager.send_to_connection(connection_id, {
                "type": "error",
                "message": f"Error generating response: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _generate_streaming_response(
        self, 
        user_message: str, 
        user_id: str, 
        context: Dict[str, Any],
        conversation: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            # Get personality profile
            personality_profile = conversation.get("personality_profile")
            
            # Generate AI response
            ai_response = await self.conversation_ai.generate_response(
                message=user_message,
                user_id=user_id,
                personality_profile=personality_profile,
                conversation_context=context,
                response_style="balanced"
            )
            
            response_text = ai_response.get("text", "")
            
            # Stream response in chunks
            chunk_size = 20  # characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield chunk
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"I apologize, but I'm having trouble processing your message right now. Error: {str(e)}"
    
    async def get_active_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active conversations"""
        if user_id:
            return [
                conv for conv in self.active_conversations.values()
                if conv["user_id"] == user_id
            ]
        else:
            return list(self.active_conversations.values())
    
    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_conversations = len(self.active_conversations)
        
        # Count by user
        user_counts = {}
        for conv in self.active_conversations.values():
            user_id = conv["user_id"]
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        # Calculate average message count
        total_messages = sum(conv["message_count"] for conv in self.active_conversations.values())
        avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
        
        return {
            "active_conversations": total_conversations,
            "conversations_by_user": user_counts,
            "total_messages": total_messages,
            "average_messages_per_conversation": avg_messages,
            "timestamp": datetime.utcnow().isoformat()
        }
