"""
Conversation Memory System

Specialized memory management for conversation history and context.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Specialized memory system for conversation history and context.
    
    Manages conversation exchanges, context retrieval, and conversation
    pattern analysis.
    """
    
    def __init__(self, vector_memory: VectorMemory):
        """
        Initialize conversation memory.
        
        Args:
            vector_memory: Vector memory instance
        """
        self.vector_memory = vector_memory
        self.conversation_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def store_exchange(
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
            Exchange ID
        """
        # Create conversation content
        conversation_content = f"User: {message}\nAssistant: {response}"
        
        # Prepare metadata
        exchange_metadata = {
            "message": message,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "exchange_type": "conversation"
        }
        
        if metadata:
            exchange_metadata.update(metadata)
        
        # Store in vector memory
        exchange_id = await self.vector_memory.store_memory(
            content=conversation_content,
            category="conversation",
            user_id=user_id,
            metadata=exchange_metadata
        )
        
        # Clear cache for this user
        if user_id in self.conversation_cache:
            del self.conversation_cache[user_id]
        
        logger.info(f"Stored conversation exchange {exchange_id} for user {user_id}")
        return exchange_id
    
    async def get_history(
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
        # Check cache first
        cache_key = f"{user_id}_{limit}_{include_context}"
        if cache_key in self.conversation_cache:
            cached_data, timestamp = self.conversation_cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Get conversations from vector memory
        conversations = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="conversation",
            limit=limit
        )
        
        # Process conversations
        processed_conversations = []
        for conv in conversations:
            processed_conv = {
                "id": conv["id"],
                "message": conv["metadata"].get("message", ""),
                "response": conv["metadata"].get("response", ""),
                "timestamp": conv["metadata"].get("timestamp", ""),
                "metadata": conv["metadata"]
            }
            
            # Add context if requested
            if include_context:
                processed_conv["context"] = await self._get_exchange_context(
                    user_id, conv["id"]
                )
            
            processed_conversations.append(processed_conv)
        
        # Sort by timestamp (newest first)
        processed_conversations.sort(
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        # Cache result
        self.conversation_cache[cache_key] = (
            processed_conversations, 
            datetime.utcnow()
        )
        
        return processed_conversations
    
    async def _get_exchange_context(
        self, 
        user_id: str, 
        exchange_id: str
    ) -> Dict[str, Any]:
        """Get contextual information for a conversation exchange"""
        try:
            # Get related memories
            exchange = await self.vector_memory.get_memory_by_id(exchange_id)
            if not exchange:
                return {}
            
            # Search for related conversations
            related_memories = await self.vector_memory.retrieve_memories(
                query=exchange["content"],
                user_id=user_id,
                category="conversation",
                limit=3
            )
            
            # Extract context
            context = {
                "related_conversations": len(related_memories),
                "conversation_topics": self._extract_topics(exchange["content"]),
                "sentiment": self._analyze_sentiment(exchange["content"]),
                "conversation_length": len(exchange["content"].split())
            }
            
            return context
            
        except Exception as e:
            logger.warning(f"Error getting exchange context: {e}")
            return {}
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from conversation content"""
        # Simple topic extraction - could be enhanced with NLP
        words = content.lower().split()
        
        # Filter out common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "may", "might", "can", "this", "that", "these", "those", "i", "you",
            "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        }
        
        # Extract meaningful words
        topics = []
        for word in words:
            if len(word) > 3 and word not in stop_words:
                topics.append(word)
        
        # Return most common topics
        from collections import Counter
        topic_counts = Counter(topics)
        return [topic for topic, count in topic_counts.most_common(5)]
    
    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis"""
        positive_words = {
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "love", "like", "enjoy", "happy", "pleased", "satisfied", "positive"
        }
        
        negative_words = {
            "bad", "terrible", "awful", "horrible", "hate", "dislike", "angry",
            "sad", "disappointed", "frustrated", "negative", "problem", "issue"
        }
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def get_conversation_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze conversation patterns for a user.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Conversation pattern analysis
        """
        # Get conversations from the specified period
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conversations = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="conversation",
            limit=1000
        )
        
        # Filter by date
        recent_conversations = [
            conv for conv in conversations
            if conv["metadata"].get("timestamp", "") > cutoff_date
        ]
        
        if not recent_conversations:
            return {"error": "No recent conversations found"}
        
        # Analyze patterns
        patterns = {
            "total_conversations": len(recent_conversations),
            "average_message_length": 0,
            "common_topics": [],
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "conversation_frequency": {},
            "response_patterns": {}
        }
        
        # Calculate average message length
        total_length = 0
        all_topics = []
        sentiments = []
        
        for conv in recent_conversations:
            message = conv["metadata"].get("message", "")
            response = conv["metadata"].get("response", "")
            
            total_length += len(message) + len(response)
            
            # Extract topics
            topics = self._extract_topics(message + " " + response)
            all_topics.extend(topics)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(message + " " + response)
            sentiments.append(sentiment)
        
        patterns["average_message_length"] = total_length / len(recent_conversations)
        
        # Get common topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        patterns["common_topics"] = [topic for topic, count in topic_counts.most_common(10)]
        
        # Sentiment distribution
        sentiment_counts = Counter(sentiments)
        total_sentiments = len(sentiments)
        patterns["sentiment_distribution"] = {
            sentiment: count / total_sentiments
            for sentiment, count in sentiment_counts.items()
        }
        
        return patterns
    
    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search through conversation history.
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        # Search using vector memory
        results = await self.vector_memory.retrieve_memories(
            query=query,
            category="conversation",
            user_id=user_id,
            limit=limit
        )
        
        # Process results
        conversations = []
        for result in results:
            conv = {
                "id": result["id"],
                "message": result["metadata"].get("message", ""),
                "response": result["metadata"].get("response", ""),
                "timestamp": result["metadata"].get("timestamp", ""),
                "similarity": result["similarity"],
                "metadata": result["metadata"]
            }
            conversations.append(conv)
        
        return conversations
    
    async def get_conversation_summary(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get a summary of recent conversations.
        
        Args:
            user_id: User identifier
            days: Number of days to summarize
            
        Returns:
            Conversation summary
        """
        # Get recent conversations
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        conversations = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="conversation",
            limit=1000
        )
        
        recent_conversations = [
            conv for conv in conversations
            if conv["metadata"].get("timestamp", "") > cutoff_date
        ]
        
        if not recent_conversations:
            return {
                "summary": "No recent conversations",
                "conversation_count": 0,
                "period_days": days
            }
        
        # Generate summary
        summary = {
            "conversation_count": len(recent_conversations),
            "period_days": days,
            "first_conversation": min(
                conv["metadata"].get("timestamp", "") for conv in recent_conversations
            ),
            "last_conversation": max(
                conv["metadata"].get("timestamp", "") for conv in recent_conversations
            ),
            "total_messages": len(recent_conversations) * 2,  # User + AI messages
            "common_topics": [],
            "overall_sentiment": "neutral"
        }
        
        # Extract common topics
        all_topics = []
        sentiments = []
        
        for conv in recent_conversations:
            message = conv["metadata"].get("message", "")
            response = conv["metadata"].get("response", "")
            
            topics = self._extract_topics(message + " " + response)
            all_topics.extend(topics)
            
            sentiment = self._analyze_sentiment(message + " " + response)
            sentiments.append(sentiment)
        
        # Get top topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        summary["common_topics"] = [topic for topic, count in topic_counts.most_common(5)]
        
        # Overall sentiment
        sentiment_counts = Counter(sentiments)
        if sentiment_counts:
            summary["overall_sentiment"] = sentiment_counts.most_common(1)[0][0]
        
        return summary
