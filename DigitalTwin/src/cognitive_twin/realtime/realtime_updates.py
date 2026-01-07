"""
Real-time Updates Module for Cognitive-Twin

Provides real-time updates and notifications for system events,
user interactions, and data changes using WebSockets and event streams.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class UpdateType(Enum):
    """Types of real-time updates"""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM_EVENT = "system_event"
    DATA_CHANGE = "data_change"
    STATUS_CHANGE = "status_change"
    ERROR = "error"
    NOTIFICATION = "notification"

@dataclass
class RealtimeUpdate:
    """Real-time update data structure"""
    update_id: str
    update_type: UpdateType
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high

class RealtimeUpdates:
    """
    Manages real-time updates and notifications for the Cognitive-Twin system.
    
    Provides update broadcasting, subscription management, and filtering
    for different types of real-time events and data changes.
    """
    
    def __init__(self):
        """Initialize real-time updates manager"""
        self.subscribers: Dict[str, Set[Callable]] = {}
        self.user_subscribers: Dict[str, Set[Callable]] = {}
        self.session_subscribers: Dict[str, Set[Callable]] = {}
        self.update_history: List[RealtimeUpdate] = []
        self.history_limit = 1000
        self.running = False
        
        # Initialize update type subscribers
        for update_type in UpdateType:
            self.subscribers[update_type.value] = set()
        
        logger.info("Real-time updates manager initialized")
    
    async def start(self):
        """Start the real-time updates system"""
        self.running = True
        logger.info("Real-time updates system started")
    
    async def stop(self):
        """Stop the real-time updates system"""
        self.running = False
        self.subscribers.clear()
        self.user_subscribers.clear()
        self.session_subscribers.clear()
        logger.info("Real-time updates system stopped")
    
    def subscribe(self, 
                  update_type: UpdateType, 
                  callback: Callable,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None):
        """
        Subscribe to real-time updates.
        
        Args:
            update_type: Type of updates to subscribe to
            callback: Callback function to receive updates
            user_id: Optional user ID for user-specific subscriptions
            session_id: Optional session ID for session-specific subscriptions
        """
        if not self.running:
            logger.warning("Cannot subscribe: real-time updates system not running")
            return
        
        # Add to type-based subscribers
        self.subscribers[update_type.value].add(callback)
        
        # Add to user-specific subscribers if user_id provided
        if user_id:
            if user_id not in self.user_subscribers:
                self.user_subscribers[user_id] = set()
            self.user_subscribers[user_id].add(callback)
        
        # Add to session-specific subscribers if session_id provided
        if session_id:
            if session_id not in self.session_subscribers:
                self.session_subscribers[session_id] = set()
            self.session_subscribers[session_id].add(callback)
        
        logger.info(f"Subscribed to {update_type.value} updates")
    
    def unsubscribe(self, 
                    update_type: UpdateType, 
                    callback: Callable,
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None):
        """
        Unsubscribe from real-time updates.
        
        Args:
            update_type: Type of updates to unsubscribe from
            callback: Callback function to remove
            user_id: Optional user ID for user-specific unsubscription
            session_id: Optional session ID for session-specific unsubscription
        """
        # Remove from type-based subscribers
        if update_type.value in self.subscribers:
            self.subscribers[update_type.value].discard(callback)
        
        # Remove from user-specific subscribers
        if user_id and user_id in self.user_subscribers:
            self.user_subscribers[user_id].discard(callback)
            if not self.user_subscribers[user_id]:
                del self.user_subscribers[user_id]
        
        # Remove from session-specific subscribers
        if session_id and session_id in self.session_subscribers:
            self.session_subscribers[session_id].discard(callback)
            if not self.session_subscribers[session_id]:
                del self.session_subscribers[session_id]
        
        logger.info(f"Unsubscribed from {update_type.value} updates")
    
    async def broadcast_update(self, update: RealtimeUpdate):
        """
        Broadcast an update to all relevant subscribers.
        
        Args:
            update: The update to broadcast
        """
        if not self.running:
            logger.warning("Cannot broadcast: real-time updates system not running")
            return
        
        # Add to history
        self.update_history.append(update)
        if len(self.update_history) > self.history_limit:
            self.update_history.pop(0)
        
        # Collect all relevant subscribers
        callbacks = set()
        
        # Type-based subscribers
        if update.update_type.value in self.subscribers:
            callbacks.update(self.subscribers[update.update_type.value])
        
        # User-specific subscribers
        if update.user_id and update.user_id in self.user_subscribers:
            callbacks.update(self.user_subscribers[update.user_id])
        
        # Session-specific subscribers
        if update.session_id and update.session_id in self.session_subscribers:
            callbacks.update(self.session_subscribers[update.session_id])
        
        # Broadcast to all relevant subscribers
        if callbacks:
            await self._notify_subscribers(callbacks, update)
        
        logger.debug(f"Broadcasted {update.update_type.value} update to {len(callbacks)} subscribers")
    
    async def _notify_subscribers(self, callbacks: Set[Callable], update: RealtimeUpdate):
        """Notify all subscribers about an update"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    async def send_user_message_update(self, 
                                       user_id: str, 
                                       message: str,
                                       session_id: Optional[str] = None,
                                       metadata: Optional[Dict[str, Any]] = None):
        """Send a user message update"""
        update = RealtimeUpdate(
            update_id=f"msg_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.USER_MESSAGE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            data={
                "message": message,
                "metadata": metadata or {}
            }
        )
        await self.broadcast_update(update)
    
    async def send_ai_response_update(self, 
                                      user_id: str, 
                                      response: str,
                                      session_id: Optional[str] = None,
                                      metadata: Optional[Dict[str, Any]] = None):
        """Send an AI response update"""
        update = RealtimeUpdate(
            update_id=f"ai_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.AI_RESPONSE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            data={
                "response": response,
                "metadata": metadata or {}
            }
        )
        await self.broadcast_update(update)
    
    async def send_system_event_update(self, 
                                       event_type: str, 
                                       event_data: Dict[str, Any],
                                       user_id: Optional[str] = None,
                                       session_id: Optional[str] = None,
                                       priority: int = 1):
        """Send a system event update"""
        update = RealtimeUpdate(
            update_id=f"sys_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.SYSTEM_EVENT,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            data={
                "event_type": event_type,
                "event_data": event_data
            }
        )
        await self.broadcast_update(update)
    
    async def send_data_change_update(self, 
                                      data_type: str, 
                                      change_type: str,
                                      data: Dict[str, Any],
                                      user_id: Optional[str] = None,
                                      session_id: Optional[str] = None):
        """Send a data change update"""
        update = RealtimeUpdate(
            update_id=f"data_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.DATA_CHANGE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            data={
                "data_type": data_type,
                "change_type": change_type,
                "data": data
            }
        )
        await self.broadcast_update(update)
    
    async def send_status_change_update(self, 
                                        component: str, 
                                        old_status: str,
                                        new_status: str,
                                        user_id: Optional[str] = None,
                                        session_id: Optional[str] = None):
        """Send a status change update"""
        update = RealtimeUpdate(
            update_id=f"status_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.STATUS_CHANGE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            data={
                "component": component,
                "old_status": old_status,
                "new_status": new_status
            }
        )
        await self.broadcast_update(update)
    
    async def send_error_update(self, 
                                error_type: str, 
                                error_message: str,
                                error_data: Optional[Dict[str, Any]] = None,
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None):
        """Send an error update"""
        update = RealtimeUpdate(
            update_id=f"err_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.ERROR,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            priority=3,  # High priority for errors
            data={
                "error_type": error_type,
                "error_message": error_message,
                "error_data": error_data or {}
            }
        )
        await self.broadcast_update(update)
    
    async def send_notification_update(self, 
                                       title: str, 
                                       message: str,
                                       notification_type: str = "info",
                                       user_id: Optional[str] = None,
                                       session_id: Optional[str] = None,
                                       priority: int = 2):
        """Send a notification update"""
        update = RealtimeUpdate(
            update_id=f"notif_{datetime.utcnow().timestamp()}",
            update_type=UpdateType.NOTIFICATION,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            data={
                "title": title,
                "message": message,
                "notification_type": notification_type
            }
        )
        await self.broadcast_update(update)
    
    def get_update_history(self, 
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           update_type: Optional[UpdateType] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get update history with optional filtering.
        
        Args:
            user_id: Filter by user ID
            session_id: Filter by session ID
            update_type: Filter by update type
            limit: Maximum number of updates to return
            
        Returns:
            List of update dictionaries
        """
        filtered_updates = self.update_history
        
        # Apply filters
        if user_id:
            filtered_updates = [u for u in filtered_updates if u.user_id == user_id]
        
        if session_id:
            filtered_updates = [u for u in filtered_updates if u.session_id == session_id]
        
        if update_type:
            filtered_updates = [u for u in filtered_updates if u.update_type == update_type]
        
        # Apply limit
        if limit:
            filtered_updates = filtered_updates[-limit:]
        
        # Convert to dictionaries
        return [
            {
                "update_id": update.update_id,
                "update_type": update.update_type.value,
                "timestamp": update.timestamp.isoformat(),
                "user_id": update.user_id,
                "session_id": update.session_id,
                "priority": update.priority,
                "data": update.data
            }
            for update in filtered_updates
        ]
    
    def get_subscriber_count(self) -> Dict[str, int]:
        """Get count of subscribers by type"""
        return {
            "by_type": {
                update_type: len(callbacks) 
                for update_type, callbacks in self.subscribers.items()
            },
            "by_user": len(self.user_subscribers),
            "by_session": len(self.session_subscribers),
            "total_history": len(self.update_history)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get real-time updates system status"""
        return {
            "running": self.running,
            "subscribers": self.get_subscriber_count(),
            "history_size": len(self.update_history),
            "history_limit": self.history_limit,
            "update_types": [t.value for t in UpdateType]
        }

# Global instance
realtime_updates = RealtimeUpdates()
