"""
Service Coordinator

Coordinates communication between all Cognitive-Twin services
using the event bus for real-time updates and data flow.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from .event_bus import EventBus
from .event_types import EventType, EventDataSchemas

logger = logging.getLogger(__name__)

class ServiceCoordinator:
    """
    Coordinates all Cognitive-Twin services using event-driven architecture.
    
    Manages service discovery, health monitoring, and inter-service communication
    through the event bus system.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize service coordinator.
        
        Args:
            event_bus: Event bus instance
        """
        self.event_bus = event_bus
        self.services: Dict[str, Dict[str, Any]] = {}
        self.service_handlers: Dict[str, str] = {}
        self.health_checks: Dict[str, datetime] = {}
        
        # Service status
        self.service_status = {
            "data_processing": "unknown",
            "conversation_engine": "unknown", 
            "personality_analyzer": "unknown",
            "memory_manager": "unknown",
            "analysis_engine": "unknown",
            "web_interface": "unknown"
        }
        
        logger.info("Service coordinator initialized")
    
    async def start(self):
        """Start the service coordinator"""
        await self._register_event_handlers()
        await self._start_health_monitoring()
        logger.info("Service coordinator started")
    
    async def stop(self):
        """Stop the service coordinator"""
        await self._unregister_event_handlers()
        logger.info("Service coordinator stopped")
    
    async def _register_event_handlers(self):
        """Register event handlers for service coordination"""
        
        # Service lifecycle events
        await self.event_bus.subscribe(
            EventType.SERVICE_STARTED.value,
            self._handle_service_started,
            "service_coordinator_started"
        )
        
        await self.event_bus.subscribe(
            EventType.SERVICE_STOPPED.value,
            self._handle_service_stopped,
            "service_coordinator_stopped"
        )
        
        await self.event_bus.subscribe(
            EventType.SERVICE_ERROR.value,
            self._handle_service_error,
            "service_coordinator_error"
        )
        
        await self.event_bus.subscribe(
            EventType.SERVICE_HEALTH_CHECK.value,
            self._handle_health_check,
            "service_coordinator_health"
        )
        
        # Data flow events
        await self.event_bus.subscribe(
            EventType.DATA_IMPORTED.value,
            self._handle_data_imported,
            "service_coordinator_data_imported"
        )
        
        await self.event_bus.subscribe(
            EventType.DATA_PROCESSED.value,
            self._handle_data_processed,
            "service_coordinator_data_processed"
        )
        
        # Conversation events
        await self.event_bus.subscribe(
            EventType.CONVERSATION_MESSAGE.value,
            self._handle_conversation_message,
            "service_coordinator_conversation"
        )
        
        # Analysis events
        await self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED.value,
            self._handle_analysis_completed,
            "service_coordinator_analysis"
        )
        
        logger.info("Service coordinator event handlers registered")
    
    async def _unregister_event_handlers(self):
        """Unregister event handlers"""
        handler_ids = [
            "service_coordinator_started",
            "service_coordinator_stopped", 
            "service_coordinator_error",
            "service_coordinator_health",
            "service_coordinator_data_imported",
            "service_coordinator_data_processed",
            "service_coordinator_conversation",
            "service_coordinator_analysis"
        ]
        
        for handler_id in handler_ids:
            try:
                await self.event_bus.unsubscribe("*", handler_id)
            except Exception as e:
                logger.warning(f"Error unregistering handler {handler_id}: {e}")
    
    async def _start_health_monitoring(self):
        """Start health monitoring for all services"""
        # Start background health monitoring task
        asyncio.create_task(self._health_monitoring_loop())
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while True:
            try:
                await self._check_all_services()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        for service_name in self.service_status.keys():
            try:
                # Publish health check request
                await self.event_bus.publish(
                    EventType.SERVICE_HEALTH_CHECK.value,
                    {"service_name": service_name, "requested_by": "coordinator"},
                    correlation_id=f"health_check_{service_name}_{datetime.utcnow().timestamp()}"
                )
            except Exception as e:
                logger.error(f"Error checking health for {service_name}: {e}")
                self.service_status[service_name] = "error"
    
    # Event Handlers
    async def _handle_service_started(self, event: Dict[str, Any]):
        """Handle service started event"""
        service_name = event["data"].get("service_name")
        if service_name:
            self.services[service_name] = {
                "status": "running",
                "started_at": event["timestamp"],
                "last_seen": datetime.utcnow().isoformat()
            }
            self.service_status[service_name] = "running"
            logger.info(f"Service {service_name} started")
    
    async def _handle_service_stopped(self, event: Dict[str, Any]):
        """Handle service stopped event"""
        service_name = event["data"].get("service_name")
        if service_name:
            if service_name in self.services:
                self.services[service_name]["status"] = "stopped"
                self.services[service_name]["stopped_at"] = event["timestamp"]
            self.service_status[service_name] = "stopped"
            logger.info(f"Service {service_name} stopped")
    
    async def _handle_service_error(self, event: Dict[str, Any]):
        """Handle service error event"""
        service_name = event["data"].get("service_name")
        error = event["data"].get("error")
        
        if service_name:
            if service_name in self.services:
                self.services[service_name]["status"] = "error"
                self.services[service_name]["last_error"] = error
                self.services[service_name]["error_at"] = event["timestamp"]
            self.service_status[service_name] = "error"
            logger.error(f"Service {service_name} error: {error}")
    
    async def _handle_health_check(self, event: Dict[str, Any]):
        """Handle health check response"""
        service_name = event["data"].get("service_name")
        health_status = event["data"].get("status", "unknown")
        
        if service_name:
            self.service_status[service_name] = health_status
            self.health_checks[service_name] = datetime.utcnow()
            
            if service_name in self.services:
                self.services[service_name]["last_health_check"] = event["timestamp"]
                self.services[service_name]["health_status"] = health_status
    
    async def _handle_data_imported(self, event: Dict[str, Any]):
        """Handle data imported event"""
        user_id = event["data"].get("user_id")
        source = event["data"].get("source")
        record_count = event["data"].get("record_count")
        
        logger.info(f"Data imported for user {user_id}: {record_count} records from {source}")
        
        # Trigger data processing
        await self.event_bus.publish(
            EventType.DATA_PROCESSED.value,
            EventDataSchemas.data_imported(user_id, source, record_count, {}),
            user_id=user_id,
            correlation_id=event.get("correlation_id")
        )
    
    async def _handle_data_processed(self, event: Dict[str, Any]):
        """Handle data processed event"""
        user_id = event["data"].get("user_id")
        source = event["data"].get("source")
        
        logger.info(f"Data processed for user {user_id} from {source}")
        
        # Trigger analysis
        await self.event_bus.publish(
            EventType.ANALYSIS_STARTED.value,
            {"user_id": user_id, "data_source": source, "analysis_type": "comprehensive"},
            user_id=user_id,
            correlation_id=event.get("correlation_id")
        )
    
    async def _handle_conversation_message(self, event: Dict[str, Any]):
        """Handle conversation message event"""
        user_id = event["data"].get("user_id")
        message = event["data"].get("message")
        
        logger.info(f"Conversation message from user {user_id}")
        
        # Store in memory
        await self.event_bus.publish(
            EventType.MEMORY_STORED.value,
            EventDataSchemas.memory_stored(
                user_id, 
                f"conv_{datetime.utcnow().timestamp()}", 
                "conversation", 
                message
            ),
            user_id=user_id,
            correlation_id=event.get("correlation_id")
        )
        
        # Trigger personality analysis if needed
        await self.event_bus.publish(
            EventType.PERSONALITY_ANALYZED.value,
            {"user_id": user_id, "trigger": "conversation", "data": message},
            user_id=user_id,
            correlation_id=event.get("correlation_id")
        )
    
    async def _handle_analysis_completed(self, event: Dict[str, Any]):
        """Handle analysis completed event"""
        user_id = event["data"].get("user_id")
        analysis_type = event["data"].get("analysis_type")
        results = event["data"].get("results", {})
        
        logger.info(f"Analysis completed for user {user_id}: {analysis_type}")
        
        # Generate insights if analysis was successful
        if results:
            await self.event_bus.publish(
                EventType.INSIGHT_GENERATED.value,
                EventDataSchemas.insight_generated(
                    user_id,
                    analysis_type,
                    f"Analysis completed: {analysis_type}",
                    0.8
                ),
                user_id=user_id,
                correlation_id=event.get("correlation_id")
            )
    
    # Service Management Methods
    async def register_service(self, service_name: str, service_info: Dict[str, Any]):
        """Register a service with the coordinator"""
        self.services[service_name] = {
            "info": service_info,
            "status": "registered",
            "registered_at": datetime.utcnow().isoformat()
        }
        self.service_status[service_name] = "registered"
        
        # Announce service registration
        await self.event_bus.publish(
            EventType.SERVICE_STARTED.value,
            {"service_name": service_name, "service_info": service_info}
        )
        
        logger.info(f"Service {service_name} registered")
    
    async def unregister_service(self, service_name: str):
        """Unregister a service"""
        if service_name in self.services:
            del self.services[service_name]
        
        if service_name in self.service_status:
            self.service_status[service_name] = "unregistered"
        
        # Announce service unregistration
        await self.event_bus.publish(
            EventType.SERVICE_STOPPED.value,
            {"service_name": service_name}
        )
        
        logger.info(f"Service {service_name} unregistered")
    
    async def get_service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of services"""
        if service_name:
            return {
                "service_name": service_name,
                "status": self.service_status.get(service_name, "unknown"),
                "details": self.services.get(service_name, {}),
                "last_health_check": self.health_checks.get(service_name)
            }
        else:
            return {
                "services": self.service_status.copy(),
                "service_details": self.services.copy(),
                "health_checks": {k: v.isoformat() for k, v in self.health_checks.items()},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def trigger_service_action(self, service_name: str, action: str, data: Dict[str, Any]):
        """Trigger an action on a specific service"""
        await self.event_bus.publish(
            f"service.{service_name}.{action}",
            data,
            correlation_id=f"coordinator_action_{datetime.utcnow().timestamp()}"
        )
        
        logger.info(f"Triggered action {action} on service {service_name}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        healthy_services = sum(1 for status in self.service_status.values() if status == "running")
        total_services = len(self.service_status)
        
        health_percentage = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        return {
            "overall_health": "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy",
            "health_percentage": health_percentage,
            "healthy_services": healthy_services,
            "total_services": total_services,
            "service_status": self.service_status.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        return {
            "registered_services": len(self.services),
            "active_services": sum(1 for status in self.service_status.values() if status == "running"),
            "error_services": sum(1 for status in self.service_status.values() if status == "error"),
            "service_uptime": {
                service: self._calculate_uptime(service_info)
                for service, service_info in self.services.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_uptime(self, service_info: Dict[str, Any]) -> Optional[float]:
        """Calculate service uptime in seconds"""
        started_at = service_info.get("started_at")
        if not started_at:
            return None
        
        try:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            uptime = (datetime.utcnow() - start_time).total_seconds()
            return uptime
        except Exception:
            return None
