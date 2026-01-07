"""
Memory Manager for Cognitive-Twin

High-level memory management system that coordinates different types of memory
including conversation history, personality data, and contextual information.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging

from .vector_memory import VectorMemory
from .conversation_memory import ConversationMemory
from .personality_memory import PersonalityMemory

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Central memory management system for Cognitive-Twin.
    
    Coordinates different types of memory storage and retrieval,
    providing a unified interface for all memory operations.
    """
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 api_key: Optional[str] = None):
        """
        Initialize memory manager.
        
        Args:
            persist_directory: Directory for persistent storage
            api_key: OpenRouter API key for embeddings
        """
        self.persist_directory = persist_directory
        self.api_key = api_key
        
        # Initialize memory components
        self.vector_memory = VectorMemory(persist_directory, api_key)
        self.conversation_memory = ConversationMemory(self.vector_memory)
        self.personality_memory = PersonalityMemory(self.vector_memory)
        
        # Memory cache for frequently accessed data
        self.memory_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Memory manager initialized")
    
    async def store_conversation(
        self,
        user_id: str,
        message: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation exchange.
        
        Args:
            user_id: User identifier
            message: User message
            response: AI response
            metadata: Additional metadata
            
        Returns:
            Conversation ID
        """
        return await self.conversation_memory.store_exchange(
            user_id=user_id,
            message=message,
            response=response,
            metadata=metadata
        )
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations
            include_context: Include contextual information
            
        Returns:
            List of conversation exchanges
        """
        return await self.conversation_memory.get_history(
            user_id=user_id,
            limit=limit,
            include_context=include_context
        )
    
    async def store_personality_data(
        self,
        user_id: str,
        personality_profile: Dict[str, Any],
        source: str = "analysis"
    ) -> str:
        """
        Store personality data for a user.
        
        Args:
            user_id: User identifier
            personality_profile: Personality profile data
            source: Source of personality data
            
        Returns:
            Personality data ID
        """
        return await self.personality_memory.store_profile(
            user_id=user_id,
            profile=personality_profile,
            source=source
        )
    
    async def get_personality_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get personality data for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Personality profile or None
        """
        return await self.personality_memory.get_profile(user_id)
    
    async def get_context_for_conversation(
        self,
        user_id: str,
        current_message: str,
        context_window: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant context for a conversation.
        
        Args:
            user_id: User identifier
            current_message: Current message being processed
            context_window: Number of recent conversations to include
            
        Returns:
            Context information
        """
        # Get recent conversation history
        recent_history = await self.get_conversation_history(
            user_id=user_id,
            limit=context_window
        )
        
        # Get personality context
        personality_data = await self.get_personality_data(user_id)
        
        # Get relevant memories
        relevant_memories = await self.vector_memory.retrieve_memories(
            query=current_message,
            user_id=user_id,
            limit=5
        )
        
        # Build context
        context = {
            "recent_conversations": recent_history,
            "personality_profile": personality_data,
            "relevant_memories": relevant_memories,
            "context_timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        
        return context
    
    async def store_insight(
        self,
        user_id: str,
        insight: str,
        insight_type: str = "general",
        confidence: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an insight about the user.
        
        Args:
            user_id: User identifier
            insight: Insight text
            insight_type: Type of insight
            confidence: Confidence score
            metadata: Additional metadata
            
        Returns:
            Insight ID
        """
        insight_metadata = {
            "insight_type": insight_type,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            insight_metadata.update(metadata)
        
        return await self.vector_memory.store_memory(
            content=insight,
            category="insights",
            user_id=user_id,
            metadata=insight_metadata
        )
    
    async def get_insights(
        self,
        user_id: str,
        insight_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get insights for a user.
        
        Args:
            user_id: User identifier
            insight_type: Type of insights to retrieve
            limit: Maximum number of insights
            
        Returns:
            List of insights
        """
        where_clause = {"user_id": user_id}
        if insight_type:
            where_clause["insight_type"] = insight_type
        
        memories = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="insights",
            limit=limit
        )
        
        # Filter by insight type if specified
        if insight_type:
            memories = [
                m for m in memories 
                if m["metadata"].get("insight_type") == insight_type
            ]
        
        return memories
    
    async def store_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a user preference.
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            preference_value: Preference value
            metadata: Additional metadata
            
        Returns:
            Preference ID
        """
        preference_metadata = {
            "preference_type": preference_type,
            "preference_value": json.dumps(preference_value),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            preference_metadata.update(metadata)
        
        return await self.vector_memory.store_memory(
            content=f"{preference_type}: {preference_value}",
            category="preferences",
            user_id=user_id,
            metadata=preference_metadata
        )
    
    async def get_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User identifier
            preference_type: Type of preferences to retrieve
            
        Returns:
            Dictionary of preferences
        """
        memories = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="preferences"
        )
        
        preferences = {}
        
        for memory in memories:
            meta = memory["metadata"]
            pref_type = meta.get("preference_type")
            pref_value = meta.get("preference_value")
            
            if preference_type is None or pref_type == preference_type:
                try:
                    preferences[pref_type] = json.loads(pref_value)
                except (json.JSONDecodeError, TypeError):
                    preferences[pref_type] = pref_value
        
        return preferences
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        categories: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search across all user memories.
        
        Args:
            query: Search query
            user_id: User identifier
            categories: Memory categories to search
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        all_results = []
        
        if categories:
            for category in categories:
                results = await self.vector_memory.retrieve_memories(
                    query=query,
                    category=category,
                    user_id=user_id,
                    limit=limit
                )
                all_results.extend(results)
        else:
            # Search all categories
            all_results = await self.vector_memory.retrieve_memories(
                query=query,
                user_id=user_id,
                limit=limit
            )
        
        # Sort by similarity and remove duplicates
        seen_ids = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x["similarity"], reverse=True):
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)
        
        return unique_results[:limit]
    
    async def get_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's memory data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Memory summary
        """
        # Get memory statistics
        stats = await self.vector_memory.get_memory_stats(user_id)
        
        # Get recent activity
        recent_conversations = await self.get_conversation_history(user_id, limit=5)
        recent_insights = await self.get_insights(user_id, limit=5)
        
        # Get personality summary
        personality_data = await self.get_personality_data(user_id)
        
        summary = {
            "user_id": user_id,
            "memory_stats": stats,
            "recent_activity": {
                "conversations": len(recent_conversations),
                "insights": len(recent_insights),
                "last_conversation": recent_conversations[0]["timestamp"] if recent_conversations else None
            },
            "personality_available": personality_data is not None,
            "summary_timestamp": datetime.utcnow().isoformat()
        }
        
        return summary
    
    async def clear_user_data(self, user_id: str, categories: Optional[List[str]] = None) -> int:
        """
        Clear user data from memory.
        
        Args:
            user_id: User identifier
            categories: Categories to clear (None for all)
            
        Returns:
            Number of memories deleted
        """
        if categories:
            total_deleted = 0
            for category in categories:
                deleted = await self.vector_memory.clear_user_memories(user_id, category)
                total_deleted += deleted
            return total_deleted
        else:
            return await self.vector_memory.clear_user_memories(user_id)
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete user data export
        """
        # Get all user memories
        all_memories = await self.vector_memory.get_user_memories(user_id, limit=10000)
        
        # Organize by category
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "conversations": [],
            "personality": [],
            "insights": [],
            "preferences": [],
            "context": [],
            "other": []
        }
        
        for memory in all_memories:
            category = memory["category"]
            if category in export_data:
                export_data[category].append(memory)
            else:
                export_data["other"].append(memory)
        
        return export_data
    
    async def import_user_data(self, user_id: str, data: Dict[str, Any]) -> int:
        """
        Import user data.
        
        Args:
            user_id: User identifier
            data: Data to import
            
        Returns:
            Number of memories imported
        """
        imported_count = 0
        
        for category, memories in data.items():
            if category in ["conversations", "personality", "insights", "preferences", "context", "other"]:
                for memory in memories:
                    try:
                        await self.vector_memory.store_memory(
                            content=memory["content"],
                            category=category,
                            user_id=user_id,
                            metadata=memory["metadata"],
                            memory_id=memory["id"]
                        )
                        imported_count += 1
                    except Exception as e:
                        logger.warning(f"Error importing memory {memory['id']}: {e}")
        
        return imported_count
