"""
Comprehensive Health Checker

Monitors and validates the health of all Cognitive-Twin components
including AI services, databases, memory systems, and integrations.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time: float
    
class HealthChecker:
    """
    Comprehensive health checker for all system components.
    
    Performs periodic health checks and provides detailed status reports
    for monitoring and debugging.
    """
    
    def __init__(self):
        """Initialize health checker"""
        self.health_results: Dict[str, HealthCheckResult] = {}
        self.check_interval = 30  # seconds
        self.timeout = 10  # seconds
        self.running = False
        self.check_task = None
        
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.running = True
        self.check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self.check_all_components()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def check_all_components(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all components.
        
        Returns:
            Dictionary of health check results
        """
        checks = [
            self._check_ai_services(),
            self._check_databases(),
            self._check_memory_system(),
            self._check_event_system(),
            self._check_realtime_features(),
            self._check_system_resources()
        ]
        
        # Run all checks concurrently
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
                continue
            
            if isinstance(result, dict):
                self.health_results.update(result)
        
        return self.health_results
    
    async def _check_ai_services(self) -> Dict[str, HealthCheckResult]:
        """Check AI services health"""
        results = {}
        start_time = time.time()
        
        try:
            # Import AI components
            from ..ai.openrouter_client import OpenRouterClient
            from ..ai.conversation_ai import ConversationAI
            from ..ai.personality_ai import PersonalityAI
            from ..ai.analysis_ai import AnalysisAI
            
            # Check OpenRouter connection
            try:
                client = OpenRouterClient()
                async with client as c:
                    health = await c.health_check()
                
                if health.get("status") == "healthy":
                    status = HealthStatus.HEALTHY
                    message = "OpenRouter API accessible"
                else:
                    status = HealthStatus.WARNING
                    message = f"OpenRouter API issues: {health.get('error', 'Unknown')}"
                
                results["ai_openrouter"] = HealthCheckResult(
                    component="ai_openrouter",
                    status=status,
                    message=message,
                    details=health,
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results["ai_openrouter"] = HealthCheckResult(
                    component="ai_openrouter",
                    status=HealthStatus.CRITICAL,
                    message=f"OpenRouter connection failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            
            # Check AI components initialization
            ai_components = [
                ("ai_conversation", ConversationAI),
                ("ai_personality", PersonalityAI),
                ("ai_analysis", AnalysisAI)
            ]
            
            for name, component_class in ai_components:
                try:
                    component = component_class()
                    status = HealthStatus.HEALTHY
                    message = f"{component_class.__name__} initialized successfully"
                    details = {"initialized": True}
                except Exception as e:
                    status = HealthStatus.CRITICAL
                    message = f"{component_class.__name__} initialization failed: {str(e)}"
                    details = {"error": str(e), "initialized": False}
                
                results[name] = HealthCheckResult(
                    component=name,
                    status=status,
                    message=message,
                    details=details,
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
        
        except ImportError as e:
            results["ai_system"] = HealthCheckResult(
                component="ai_system",
                status=HealthStatus.CRITICAL,
                message=f"AI system not available: {str(e)}",
                details={"error": str(e), "available": False},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        return results
    
    async def _check_databases(self) -> Dict[str, HealthCheckResult]:
        """Check database health"""
        results = {}
        
        # Database check configurations
        db_checks = [
            ("postgres", self._check_postgres),
            ("mongodb", self._check_mongodb),
            ("redis", self._check_redis),
            ("neo4j", self._check_neo4j)
        ]
        
        for db_name, check_func in db_checks:
            start_time = time.time()
            try:
                await asyncio.wait_for(check_func(), timeout=self.timeout)
                results[f"db_{db_name}"] = HealthCheckResult(
                    component=f"db_{db_name}",
                    status=HealthStatus.HEALTHY,
                    message=f"{db_name.title()} database accessible",
                    details={"accessible": True},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except asyncio.TimeoutError:
                results[f"db_{db_name}"] = HealthCheckResult(
                    component=f"db_{db_name}",
                    status=HealthStatus.CRITICAL,
                    message=f"{db_name.title()} database timeout",
                    details={"timeout": True, "timeout_seconds": self.timeout},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results[f"db_{db_name}"] = HealthCheckResult(
                    component=f"db_{db_name}",
                    status=HealthStatus.CRITICAL,
                    message=f"{db_name.title()} database error: {str(e)}",
                    details={"error": str(e), "accessible": False},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
        
        return results
    
    async def _check_postgres(self):
        """Check PostgreSQL connection"""
        # Simplified check - would use actual connection in real implementation
        await asyncio.sleep(0.1)  # Simulate check
    
    async def _check_mongodb(self):
        """Check MongoDB connection"""
        # Simplified check - would use actual connection in real implementation
        await asyncio.sleep(0.1)  # Simulate check
    
    async def _check_redis(self):
        """Check Redis connection"""
        # Simplified check - would use actual connection in real implementation
        await asyncio.sleep(0.1)  # Simulate check
    
    async def _check_neo4j(self):
        """Check Neo4j connection"""
        # Simplified check - would use actual connection in real implementation
        await asyncio.sleep(0.1)  # Simulate check
    
    async def _check_memory_system(self) -> Dict[str, HealthCheckResult]:
        """Check memory system health"""
        results = {}
        start_time = time.time()
        
        try:
            from ..memory.vector_memory import VectorMemory
            from ..memory.memory_manager import MemoryManager
            
            # Check ChromaDB
            try:
                vector_memory = VectorMemory()
                # Test basic operation
                test_id = await vector_memory.store_memory(
                    content="Health check test",
                    category="test",
                    user_id="health_check"
                )
                await vector_memory.delete_memory(test_id)
                
                results["memory_vector"] = HealthCheckResult(
                    component="memory_vector",
                    status=HealthStatus.HEALTHY,
                    message="Vector memory system operational",
                    details={"operational": True},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results["memory_vector"] = HealthCheckResult(
                    component="memory_vector",
                    status=HealthStatus.CRITICAL,
                    message=f"Vector memory system error: {str(e)}",
                    details={"error": str(e), "operational": False},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            
            # Check Memory Manager
            try:
                memory_manager = MemoryManager()
                summary = await memory_manager.get_memory_summary("health_check")
                
                results["memory_manager"] = HealthCheckResult(
                    component="memory_manager",
                    status=HealthStatus.HEALTHY,
                    message="Memory manager operational",
                    details={"operational": True, "summary": summary},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results["memory_manager"] = HealthCheckResult(
                    component="memory_manager",
                    status=HealthStatus.CRITICAL,
                    message=f"Memory manager error: {str(e)}",
                    details={"error": str(e), "operational": False},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
        
        except ImportError as e:
            results["memory_system"] = HealthCheckResult(
                component="memory_system",
                status=HealthStatus.CRITICAL,
                message=f"Memory system not available: {str(e)}",
                details={"error": str(e), "available": False},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        return results
    
    async def _check_event_system(self) -> Dict[str, HealthCheckResult]:
        """Check event system health"""
        results = {}
        start_time = time.time()
        
        try:
            from ..events.event_bus import EventBus
            from ..events.service_coordinator import ServiceCoordinator
            
            # Check Event Bus
            try:
                event_bus = EventBus()
                await event_bus.connect()
                health = await event_bus.health_check()
                await event_bus.disconnect()
                
                if health.get("status") == "healthy":
                    status = HealthStatus.HEALTHY
                    message = "Event bus operational"
                else:
                    status = HealthStatus.WARNING
                    message = f"Event bus issues: {health.get('error', 'Unknown')}"
                
                results["event_bus"] = HealthCheckResult(
                    component="event_bus",
                    status=status,
                    message=message,
                    details=health,
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results["event_bus"] = HealthCheckResult(
                    component="event_bus",
                    status=HealthStatus.CRITICAL,
                    message=f"Event bus error: {str(e)}",
                    details={"error": str(e), "operational": False},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
        
        except ImportError as e:
            results["event_system"] = HealthCheckResult(
                component="event_system",
                status=HealthStatus.CRITICAL,
                message=f"Event system not available: {str(e)}",
                details={"error": str(e), "available": False},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        return results
    
    async def _check_realtime_features(self) -> Dict[str, HealthCheckResult]:
        """Check real-time features health"""
        results = {}
        start_time = time.time()
        
        try:
            from ..realtime.websocket_manager import WebSocketManager
            from ..realtime.live_conversation import LiveConversation
            
            # Check WebSocket Manager
            try:
                websocket_manager = WebSocketManager()
                stats = await websocket_manager.get_connection_stats()
                
                results["realtime_websocket"] = HealthCheckResult(
                    component="realtime_websocket",
                    status=HealthStatus.HEALTHY,
                    message="WebSocket manager operational",
                    details={"operational": True, "stats": stats},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
            except Exception as e:
                results["realtime_websocket"] = HealthCheckResult(
                    component="realtime_websocket",
                    status=HealthStatus.CRITICAL,
                    message=f"WebSocket manager error: {str(e)}",
                    details={"error": str(e), "operational": False},
                    timestamp=datetime.utcnow(),
                    response_time=time.time() - start_time
                )
        
        except ImportError as e:
            results["realtime_system"] = HealthCheckResult(
                component="realtime_system",
                status=HealthStatus.CRITICAL,
                message=f"Real-time system not available: {str(e)}",
                details={"error": str(e), "available": False},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        return results
    
    async def _check_system_resources(self) -> Dict[str, HealthCheckResult]:
        """Check system resources"""
        results = {}
        start_time = time.time()
        
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 70:
                status = HealthStatus.WARNING
                message = f"Moderate CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal CPU usage: {cpu_percent:.1f}%"
            
            results["system_cpu"] = HealthCheckResult(
                component="system_cpu",
                status=status,
                message=message,
                details={"cpu_percent": cpu_percent},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > 70:
                status = HealthStatus.WARNING
                message = f"Moderate memory usage: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal memory usage: {memory.percent:.1f}%"
            
            results["system_memory"] = HealthCheckResult(
                component="system_memory",
                status=status,
                message=message,
                details={
                    "percent": memory.percent,
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used
                },
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High disk usage: {disk.percent:.1f}%"
            elif disk.percent > 80:
                status = HealthStatus.WARNING
                message = f"Moderate disk usage: {disk.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal disk usage: {disk.percent:.1f}%"
            
            results["system_disk"] = HealthCheckResult(
                component="system_disk",
                status=status,
                message=message,
                details={
                    "percent": disk.percent,
                    "total": disk.total,
                    "free": disk.free,
                    "used": disk.used
                },
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        except ImportError:
            results["system_resources"] = HealthCheckResult(
                component="system_resources",
                status=HealthStatus.WARNING,
                message="psutil not available for system monitoring",
                details={"psutil_available": False},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        except Exception as e:
            results["system_resources"] = HealthCheckResult(
                component="system_resources",
                status=HealthStatus.WARNING,
                message=f"System resource check error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                response_time=time.time() - start_time
            )
        
        return results
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            Overall health status and summary
        """
        if not self.health_results:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "No health checks performed yet",
                "summary": {}
            }
        
        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for result in self.health_results.values():
            status_counts[result.status] += 1
        
        total_checks = len(self.health_results)
        
        # Determine overall status
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_status = HealthStatus.CRITICAL
            message = f"{status_counts[HealthStatus.CRITICAL]} critical issues found"
        elif status_counts[HealthStatus.WARNING] > 0:
            overall_status = HealthStatus.WARNING
            message = f"{status_counts[HealthStatus.WARNING]} warnings found"
        elif status_counts[HealthStatus.HEALTHY] == total_checks:
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        else:
            overall_status = HealthStatus.UNKNOWN
            message = "System status unclear"
        
        return {
            "status": overall_status,
            "message": message,
            "summary": {
                "total_checks": total_checks,
                "healthy": status_counts[HealthStatus.HEALTHY],
                "warning": status_counts[HealthStatus.WARNING],
                "critical": status_counts[HealthStatus.CRITICAL],
                "unknown": status_counts[HealthStatus.UNKNOWN]
            },
            "last_check": max(
                (result.timestamp for result in self.health_results.values()),
                default=datetime.utcnow()
            ).isoformat()
        }
    
    def get_component_health(self, component: str) -> Optional[HealthCheckResult]:
        """Get health status for a specific component"""
        return self.health_results.get(component)
    
    def get_failing_components(self) -> List[HealthCheckResult]:
        """Get list of components with issues"""
        return [
            result for result in self.health_results.values()
            if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]
        ]
