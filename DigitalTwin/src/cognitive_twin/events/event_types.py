"""
Event Types and Definitions

Defines all event types used in the Cognitive-Twin system
for service communication and coordination.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

class EventType(Enum):
    """Event types in the Cognitive-Twin system"""
    
    # User Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Data Events
    DATA_IMPORTED = "data.imported"
    DATA_PROCESSED = "data.processed"
    DATA_ANALYZED = "data.analyzed"
    DATA_EXPORTED = "data.exported"
    
    # Conversation Events
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_MESSAGE = "conversation.message"
    CONVERSATION_ENDED = "conversation.ended"
    CONVERSATION_ANALYZED = "conversation.analyzed"
    
    # Personality Events
    PERSONALITY_ANALYZED = "personality.analyzed"
    PERSONALITY_UPDATED = "personality.updated"
    PERSONALITY_INSIGHT_GENERATED = "personality.insight_generated"
    
    # Memory Events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_DELETED = "memory.deleted"
    
    # Analysis Events
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    INSIGHT_GENERATED = "insight.generated"
    
    # Service Events
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_ERROR = "service.error"
    SERVICE_HEALTH_CHECK = "service.health_check"
    
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

@dataclass
class Event:
    """Standard event structure"""
    id: str
    type: EventType
    data: Dict[str, Any]
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None
    namespace: str = "cognitive_twin"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

# Event Data Schemas
class EventDataSchemas:
    """Standard event data schemas"""
    
    @staticmethod
    def user_created(user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def data_imported(user_id: str, source: str, record_count: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "source": source,
            "record_count": record_count,
            "metadata": metadata,
            "imported_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def conversation_message(user_id: str, message: str, response: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "message": message,
            "response": response,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def personality_analyzed(user_id: str, personality_profile: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "personality_profile": personality_profile,
            "confidence": confidence,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def memory_stored(user_id: str, memory_id: str, category: str, content: str) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "memory_id": memory_id,
            "category": category,
            "content": content,
            "stored_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def analysis_completed(user_id: str, analysis_type: str, results: Dict[str, Any], duration: float) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "analysis_type": analysis_type,
            "results": results,
            "duration": duration,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def insight_generated(user_id: str, insight_type: str, insight: str, confidence: float) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "insight_type": insight_type,
            "insight": insight,
            "confidence": confidence,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def service_error(service_name: str, error: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "service_name": service_name,
            "error": error,
            "context": context,
            "occurred_at": datetime.utcnow().isoformat()
        }

# Event Handlers Registry
class EventHandlerRegistry:
    """Registry for event handlers"""
    
    def __init__(self):
        self.handlers: Dict[EventType, list] = {}
    
    def register(self, event_type: EventType, handler):
        """Register an event handler"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unregister(self, event_type: EventType, handler):
        """Unregister an event handler"""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def get_handlers(self, event_type: EventType) -> list:
        """Get handlers for an event type"""
        return self.handlers.get(event_type, [])
    
    def get_all_handlers(self) -> Dict[EventType, list]:
        """Get all registered handlers"""
        return self.handlers.copy()

# Event Filtering
class EventFilter:
    """Event filtering utilities"""
    
    @staticmethod
    def by_user_id(events: list, user_id: str) -> list:
        """Filter events by user ID"""
        return [event for event in events if event.get("user_id") == user_id]
    
    @staticmethod
    def by_type(events: list, event_type: EventType) -> list:
        """Filter events by type"""
        return [event for event in events if event.get("type") == event_type.value]
    
    @staticmethod
    def by_time_range(events: list, start_time: str, end_time: str) -> list:
        """Filter events by time range"""
        return [
            event for event in events
            if start_time <= event.get("timestamp", "") <= end_time
        ]
    
    @staticmethod
    def by_correlation_id(events: list, correlation_id: str) -> list:
        """Filter events by correlation ID"""
        return [event for event in events if event.get("correlation_id") == correlation_id]

# Event Aggregation
class EventAggregator:
    """Event aggregation utilities"""
    
    @staticmethod
    def count_by_type(events: list) -> Dict[str, int]:
        """Count events by type"""
        counts = {}
        for event in events:
            event_type = event.get("type", "unknown")
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    @staticmethod
    def count_by_user(events: list) -> Dict[str, int]:
        """Count events by user"""
        counts = {}
        for event in events:
            user_id = event.get("user_id", "anonymous")
            counts[user_id] = counts.get(user_id, 0) + 1
        return counts
    
    @staticmethod
    def get_timeline(events: list) -> list:
        """Get events sorted by timestamp"""
        return sorted(events, key=lambda x: x.get("timestamp", ""))
    
    @staticmethod
    def get_recent_events(events: list, hours: int = 24) -> list:
        """Get events from the last N hours"""
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()
        
        return [
            event for event in events
            if event.get("timestamp", "") > cutoff_iso
        ]
