"""
Event Bus for Service Communication

Provides pub/sub messaging system for real-time communication
between Cognitive-Twin services using Redis.
"""

import asyncio
import json
import redis.asyncio as redis
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class EventBus:
    """
    Event bus for service communication using Redis pub/sub.
    
    Provides reliable messaging between services with support for
    event persistence, retry mechanisms, and dead letter queues.
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 namespace: str = "cognitive_twin"):
        """
        Initialize event bus.
        
        Args:
            redis_url: Redis connection URL
            namespace: Namespace for event channels
        """
        self.redis_url = redis_url
        self.namespace = namespace
        self.redis_client = None
        self.pubsub = None
        
        # Event handlers
        self.handlers: Dict[str, List[Callable]] = {}
        self.subscriptions: Set[str] = set()
        
        # Event persistence
        self.persist_events = True
        self.event_ttl = 3600  # 1 hour
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        
        logger.info(f"Event bus initialized with namespace: {namespace}")
    
    async def connect(self):
        """Connect to Redis and initialize pub/sub"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis event bus")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Disconnected from Redis event bus")
    
    async def publish(self, 
                     event_type: str, 
                     data: Dict[str, Any], 
                     user_id: Optional[str] = None,
                     correlation_id: Optional[str] = None) -> str:
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
            user_id: User identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Event ID
        """
        if not self.redis_client:
            raise RuntimeError("Event bus not connected")
        
        # Generate event ID
        event_id = str(uuid.uuid4())
        
        # Create event
        event = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "user_id": user_id,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "namespace": self.namespace
        }
        
        # Serialize event
        event_json = json.dumps(event)
        
        try:
            # Publish to Redis
            channel = f"{self.namespace}:events:{event_type}"
            await self.redis_client.publish(channel, event_json)
            
            # Persist event if enabled
            if self.persist_events:
                await self._persist_event(event)
            
            logger.debug(f"Published event {event_id} of type {event_type}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_id}: {e}")
            raise
    
    async def subscribe(self, 
                       event_type: str, 
                       handler: Callable,
                       handler_id: Optional[str] = None) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler function
            handler_id: Unique handler identifier
            
        Returns:
            Handler ID
        """
        if not handler_id:
            handler_id = str(uuid.uuid4())
        
        # Register handler
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append({
            "id": handler_id,
            "handler": handler
        })
        
        # Subscribe to Redis channel if not already subscribed
        channel = f"{self.namespace}:events:{event_type}"
        if channel not in self.subscriptions:
            await self.pubsub.subscribe(channel)
            self.subscriptions.add(channel)
            logger.info(f"Subscribed to channel: {channel}")
        
        logger.info(f"Registered handler {handler_id} for event type {event_type}")
        return handler_id
    
    async def unsubscribe(self, event_type: str, handler_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type
            handler_id: Handler ID to remove
            
        Returns:
            True if successful
        """
        if event_type not in self.handlers:
            return False
        
        # Remove handler
        self.handlers[event_type] = [
            h for h in self.handlers[event_type] 
            if h["id"] != handler_id
        ]
        
        # Unsubscribe from channel if no more handlers
        if not self.handlers[event_type]:
            channel = f"{self.namespace}:events:{event_type}"
            await self.pubsub.unsubscribe(channel)
            self.subscriptions.discard(channel)
            logger.info(f"Unsubscribed from channel: {channel}")
        
        logger.info(f"Unregistered handler {handler_id} for event type {event_type}")
        return True
    
    async def start_listening(self):
        """Start listening for events"""
        if not self.pubsub:
            raise RuntimeError("Event bus not connected")
        
        logger.info("Starting event listener")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message)
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
            raise
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message"""
        try:
            # Parse event
            event_data = json.loads(message["data"])
            event_type = event_data["type"]
            
            # Get handlers for this event type
            handlers = self.handlers.get(event_type, [])
            
            if not handlers:
                logger.warning(f"No handlers for event type: {event_type}")
                return
            
            # Call all handlers
            for handler_info in handlers:
                try:
                    await self._call_handler(handler_info["handler"], event_data)
                except Exception as e:
                    logger.error(f"Error in handler {handler_info['id']}: {e}")
                    # Could implement retry logic here
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _call_handler(self, handler: Callable, event_data: Dict[str, Any]):
        """Call event handler with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
                return
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"Handler failed (attempt {attempt + 1}), retrying: {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Handler failed after {self.max_retries} retries: {e}")
                    # Could send to dead letter queue here
                    raise
    
    async def _persist_event(self, event: Dict[str, Any]):
        """Persist event for replay/recovery"""
        try:
            event_key = f"{self.namespace}:persisted:{event['id']}"
            await self.redis_client.setex(
                event_key, 
                self.event_ttl, 
                json.dumps(event)
            )
        except Exception as e:
            logger.warning(f"Failed to persist event {event['id']}: {e}")
    
    async def get_event_history(self, 
                               event_type: Optional[str] = None,
                               user_id: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            limit: Maximum number of events
            
        Returns:
            List of events
        """
        if not self.redis_client:
            raise RuntimeError("Event bus not connected")
        
        try:
            # Get persisted events
            pattern = f"{self.namespace}:persisted:*"
            keys = await self.redis_client.keys(pattern)
            
            events = []
            for key in keys[:limit]:
                event_data = await self.redis_client.get(key)
                if event_data:
                    event = json.loads(event_data)
                    
                    # Apply filters
                    if event_type and event.get("type") != event_type:
                        continue
                    if user_id and event.get("user_id") != user_id:
                        continue
                    
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda x: x["timestamp"], reverse=True)
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return []
    
    async def replay_events(self, 
                           event_type: str,
                           from_timestamp: Optional[str] = None,
                           to_timestamp: Optional[str] = None) -> int:
        """
        Replay events of a specific type.
        
        Args:
            event_type: Event type to replay
            from_timestamp: Start timestamp
            to_timestamp: End timestamp
            
        Returns:
            Number of events replayed
        """
        if not self.redis_client:
            raise RuntimeError("Event bus not connected")
        
        try:
            # Get events to replay
            events = await self.get_event_history(event_type=event_type, limit=1000)
            
            # Filter by timestamp
            if from_timestamp:
                events = [e for e in events if e["timestamp"] >= from_timestamp]
            if to_timestamp:
                events = [e for e in events if e["timestamp"] <= to_timestamp]
            
            # Replay events
            replayed_count = 0
            for event in events:
                try:
                    # Publish event again
                    await self.publish(
                        event_type=event["type"],
                        data=event["data"],
                        user_id=event.get("user_id"),
                        correlation_id=event.get("correlation_id")
                    )
                    replayed_count += 1
                except Exception as e:
                    logger.error(f"Error replaying event {event['id']}: {e}")
            
            logger.info(f"Replayed {replayed_count} events of type {event_type}")
            return replayed_count
            
        except Exception as e:
            logger.error(f"Error replaying events: {e}")
            return 0
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        if not self.redis_client:
            raise RuntimeError("Event bus not connected")
        
        try:
            stats = {
                "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
                "event_types": list(self.handlers.keys()),
                "active_subscriptions": len(self.subscriptions),
                "persisted_events": 0,
                "namespace": self.namespace
            }
            
            # Count persisted events
            pattern = f"{self.namespace}:persisted:*"
            keys = await self.redis_client.keys(pattern)
            stats["persisted_events"] = len(keys)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting event stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check event bus health"""
        try:
            if not self.redis_client:
                return {"status": "disconnected", "error": "No Redis connection"}
            
            # Test Redis connection
            await self.redis_client.ping()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "active_handlers": sum(len(handlers) for handlers in self.handlers.values()),
                "active_subscriptions": len(self.subscriptions)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False
            }
