"""
Digital Twin endpoints for the integrated system.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import db_manager
from core.engine import Engine

# Import AI components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))

try:
    from cognitive_twin.ai.conversation_ai import ConversationAI
    from cognitive_twin.ai.personality_ai import PersonalityAI
    from cognitive_twin.memory.memory_manager import MemoryManager
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    print(f"AI components not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()

# Create engine instance
engine = Engine()

@router.post("/message")
async def send_message(
    message: Dict[str, Any],
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Send a message to the digital twin with real AI processing.
    """
    try:
        # Extract message components
        message_text = message.get("text", "")
        context = message.get("context", {})
        user_id = message.get("user_id", "anonymous")
        
        if not message_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message text is required"
            )
        
        if AI_AVAILABLE:
            # Initialize AI components
            conversation_ai = ConversationAI()
            memory_manager = MemoryManager()
            
            # Get user's personality profile
            personality_profile = await memory_manager.get_personality_data(user_id)
            
            # Get conversation context
            conversation_context = await memory_manager.get_context_for_conversation(
                user_id=user_id,
                current_message=message_text,
                context_window=5
            )
            
            # Generate AI response
            ai_response = await conversation_ai.generate_response(
                message=message_text,
                user_id=user_id,
                personality_profile=personality_profile,
                conversation_context=conversation_context,
                response_style="balanced"
            )
            
            # Store conversation in memory
            await memory_manager.store_conversation(
                user_id=user_id,
                message=message_text,
                response=ai_response.get("text", ""),
                metadata={
                    "endpoint": "/message",
                    "context": context,
                    "model_used": ai_response.get("metadata", {}).get("model_used", "unknown")
                }
            )
            
            # Format response
            response = {
                "text": ai_response.get("text", "I'm having trouble processing your message right now."),
                "type": "text",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "message_id": f"msg_{datetime.utcnow().timestamp()}",
                    "conversation_id": context.get("conversation_id", f"conv_{user_id}_{datetime.utcnow().timestamp()}"),
                    "confidence": ai_response.get("metadata", {}).get("confidence", 0.8),
                    "model_used": ai_response.get("metadata", {}).get("model_used", "unknown"),
                    "response_type": ai_response.get("metadata", {}).get("response_type", "ai_generated")
                }
            }
        else:
            # Fallback when AI is not available
            logger.warning("AI components not available, using fallback response")
            response = {
                "text": f"I understand you're saying: '{message_text}'. I'm your digital twin, but I'm currently operating in limited mode. My full AI capabilities will be available once the system is properly configured.",
                "type": "text",
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "message_id": f"msg_{datetime.utcnow().timestamp()}",
                    "conversation_id": context.get("conversation_id", f"conv_{user_id}_{datetime.utcnow().timestamp()}"),
                    "confidence": 0.3,
                    "response_type": "fallback"
                }
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_message endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/profile")
async def get_digital_twin_profile(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Get the digital twin profile with real personality data.
    """
    try:
        if not user_id:
            user_id = "anonymous"
        
        if AI_AVAILABLE:
            # Initialize memory manager
            memory_manager = MemoryManager()
            
            # Get real personality data
            personality_data = await memory_manager.get_personality_data(user_id)
            
            # Get memory summary
            memory_summary = await memory_manager.get_memory_summary(user_id)
            
            # Get insights
            insights = await memory_manager.get_insights(user_id, limit=5)
            
            if personality_data:
                profile = {
                    "personality": {
                        "big_five": personality_data.get("big_five", {}),
                        "communication_style": personality_data.get("communication_style", {}),
                        "decision_style": personality_data.get("decision_style", {}),
                        "behavioral_patterns": personality_data.get("behavioral_patterns", {}),
                        "confidence": personality_data.get("confidence_scores", {}).get("overall_confidence", 0.5)
                    },
                    "memory": {
                        "memory_stats": memory_summary.get("memory_stats", {}),
                        "recent_activity": memory_summary.get("recent_activity", {}),
                        "personality_available": memory_summary.get("personality_available", False)
                    },
                    "insights": [
                        {
                            "text": insight.get("content", ""),
                            "type": insight.get("metadata", {}).get("insight_type", "general"),
                            "confidence": insight.get("metadata", {}).get("confidence", 0.5),
                            "timestamp": insight.get("metadata", {}).get("timestamp", "")
                        }
                        for insight in insights
                    ],
                    "analysis_metadata": {
                        "last_analysis": personality_data.get("analysis_timestamp", ""),
                        "analysis_method": personality_data.get("analysis_method", "unknown"),
                        "data_quality": "high" if len(insights) > 3 else "medium"
                    }
                }
            else:
                # No personality data available yet
                profile = {
                    "personality": {
                        "big_five": {
                            "openness": 0.5,
                            "conscientiousness": 0.5,
                            "extraversion": 0.5,
                            "agreeableness": 0.5,
                            "neuroticism": 0.5
                        },
                        "communication_style": {},
                        "decision_style": {},
                        "behavioral_patterns": {},
                        "confidence": 0.0
                    },
                    "memory": memory_summary,
                    "insights": [],
                    "analysis_metadata": {
                        "status": "no_data",
                        "message": "No personality analysis available yet. Start a conversation to begin analysis."
                    }
                }
        else:
            # Fallback when AI is not available
            logger.warning("AI components not available, using fallback profile")
            profile = {
                "personality": {
                    "big_five": {
                        "openness": 0.5,
                        "conscientiousness": 0.5,
                        "extraversion": 0.5,
                        "agreeableness": 0.5,
                        "neuroticism": 0.5
                    },
                    "communication_style": {
                        "formality": 0.5,
                        "verbosity": 0.5,
                        "emotionality": 0.5,
                        "assertiveness": 0.5
                    },
                    "confidence": 0.3
                },
                "memory": {
                    "memory_stats": {"note": "Memory system not available"},
                    "recent_activity": {}
                },
                "insights": [],
                "analysis_metadata": {
                    "status": "limited_mode",
                    "message": "Digital twin is operating in limited mode. Full AI capabilities not available."
                }
            }
        
        return profile
        
    except Exception as e:
        logger.error(f"Error in get_digital_twin_profile endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@router.get("/memory")
async def query_digital_twin_memory(
    query: str,
    user_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Query the digital twin memory using real vector search.
    """
    try:
        if not user_id:
            user_id = "anonymous"
        
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query parameter is required"
            )
        
        if AI_AVAILABLE:
            # Initialize memory manager
            memory_manager = MemoryManager()
            
            # Determine categories to search
            categories = [memory_type] if memory_type else None
            
            # Search memories using vector search
            memory_results = await memory_manager.search_memories(
                query=query,
                user_id=user_id,
                categories=categories,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for memory in memory_results:
                formatted_memory = {
                    "id": memory.get("id", ""),
                    "type": memory.get("category", "unknown"),
                    "content": memory.get("content", ""),
                    "timestamp": memory.get("metadata", {}).get("timestamp", ""),
                    "similarity": memory.get("similarity", 0.0),
                    "metadata": memory.get("metadata", {}),
                    "related_entities": memory.get("metadata", {}).get("entities", [])
                }
                formatted_results.append(formatted_memory)
            
            return {
                "query": query,
                "user_id": user_id,
                "memory_type": memory_type,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "search_metadata": {
                    "search_type": "vector_semantic",
                    "categories_searched": categories or ["all"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        else:
            # Fallback when AI is not available
            logger.warning("AI components not available, using fallback memory search")
            
            # Simple keyword-based fallback
            fallback_results = [
                {
                    "id": f"fallback_{i}",
                    "type": "fallback",
                    "content": f"Fallback memory about '{query}' - Real memory search not available",
                    "timestamp": datetime.utcnow().isoformat(),
                    "similarity": 0.3,
                    "metadata": {"source": "fallback"},
                    "related_entities": []
                }
                for i in range(min(3, limit))
            ]
            
            return {
                "query": query,
                "user_id": user_id,
                "memory_type": memory_type,
                "results": fallback_results,
                "total_found": len(fallback_results),
                "search_metadata": {
                    "search_type": "fallback",
                    "message": "Memory system operating in limited mode",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in query_digital_twin_memory endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory query failed: {str(e)}"
        )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with the digital twin.
    """
    connection_id = None
    user_id = "anonymous"
    
    try:
        # Accept connection
        await websocket.accept()
        
        if AI_AVAILABLE:
            # Initialize real-time components
            from cognitive_twin.realtime.websocket_manager import WebSocketManager
            from cognitive_twin.realtime.live_conversation import LiveConversation
            from cognitive_twin.ai.conversation_ai import ConversationAI
            from cognitive_twin.memory.memory_manager import MemoryManager
            from cognitive_twin.events.event_bus import EventBus
            
            # Initialize components
            websocket_manager = WebSocketManager()
            conversation_ai = ConversationAI()
            memory_manager = MemoryManager()
            event_bus = EventBus()
            
            # Initialize live conversation system
            live_conversation = LiveConversation(
                websocket_manager=websocket_manager,
                conversation_ai=conversation_ai,
                memory_manager=memory_manager,
                event_bus=event_bus
            )
            
            # Register connection
            connection_id = await websocket_manager.connect(
                websocket=websocket,
                user_id=user_id,
                connection_type="digital_twin"
            )
            
            # Handle messages
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process with live conversation system
                await live_conversation.handle_message(connection_id, data)
        else:
            # Fallback WebSocket handling
            logger.warning("AI components not available, using fallback WebSocket")
            
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Extract message components
                message_text = data.get("text", "")
                context = data.get("context", {})
                message_type = data.get("type", "message")
                
                # Handle different message types
                if message_type == "ping":
                    response = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif message_type == "message" and message_text:
                    response = {
                        "text": f"I understand you're saying: '{message_text}'. I'm your digital twin operating in limited mode. Full real-time capabilities will be available once the system is properly configured.",
                        "type": "text",
                        "timestamp": datetime.utcnow().isoformat(),
                        "context": {
                            "message_id": f"ws_msg_{datetime.utcnow().timestamp()}",
                            "conversation_id": context.get("conversation_id", f"ws_conv_{datetime.utcnow().timestamp()}"),
                            "confidence": 0.3,
                            "mode": "fallback"
                        }
                    }
                else:
                    response = {
                        "type": "error",
                        "message": "Invalid message format or type",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Send response to client
                await websocket.send_json(response)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        if AI_AVAILABLE and connection_id:
            await websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if websocket.client_state == websocket.client_state.CONNECTED:
            await websocket.send_json({
                "type": "error",
                "message": f"WebSocket error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        if AI_AVAILABLE and connection_id:
            await websocket_manager.disconnect(connection_id)