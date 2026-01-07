"""
Health Diagnostics Module for Cognitive-Twin

Provides comprehensive system health diagnostics, component testing,
and automated troubleshooting for the Cognitive-Twin system.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import traceback

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration: float
    error: Optional[str] = None

class HealthDiagnostics:
    """
    Comprehensive health diagnostics for the Cognitive-Twin system.
    
    Provides automated testing, monitoring, and troubleshooting capabilities
    for all system components and integrations.
    """
    
    def __init__(self):
        """Initialize health diagnostics"""
        self.checks = {}
        self.check_history = []
        self.history_limit = 1000
        self.running = False
        
        # Register built-in health checks
        self._register_builtin_checks()
        
        logger.info("Health diagnostics initialized")
    
    def _register_builtin_checks(self):
        """Register built-in health checks"""
        self.checks.update({
            "system_memory": self._check_system_memory,
            "system_disk": self._check_system_disk,
            "python_environment": self._check_python_environment,
            "dependencies": self._check_dependencies,
            "configuration": self._check_configuration,
            "database_connections": self._check_database_connections,
            "ai_services": self._check_ai_services,
            "memory_system": self._check_memory_system,
            "event_system": self._check_event_system,
            "api_endpoints": self._check_api_endpoints
        })
    
    async def start(self):
        """Start health diagnostics"""
        self.running = True
        logger.info("Health diagnostics started")
    
    async def stop(self):
        """Stop health diagnostics"""
        self.running = False
        logger.info("Health diagnostics stopped")
    
    def register_check(self, name: str, check_function):
        """Register a custom health check"""
        self.checks[name] = check_function
        logger.info(f"Registered health check: {name}")
    
    def unregister_check(self, name: str):
        """Unregister a health check"""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Unregistered health check: {name}")
    
    async def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found",
                details={},
                timestamp=datetime.utcnow(),
                duration=0.0,
                error="Check not found"
            )
        
        start_time = time.time()
        timestamp = datetime.utcnow()
        
        try:
            check_function = self.checks[name]
            
            if asyncio.iscoroutinefunction(check_function):
                result = await check_function()
            else:
                result = check_function()
            
            duration = time.time() - start_time
            
            if isinstance(result, HealthCheck):
                result.duration = duration
                result.timestamp = timestamp
                health_check = result
            else:
                # Handle legacy check functions that return tuples
                if isinstance(result, tuple) and len(result) >= 3:
                    status, message, details = result[:3]
                    error = result[3] if len(result) > 3 else None
                else:
                    status = HealthStatus.UNKNOWN
                    message = "Invalid check result format"
                    details = {"result": str(result)}
                    error = "Invalid result format"
                
                health_check = HealthCheck(
                    name=name,
                    status=status,
                    message=message,
                    details=details,
                    timestamp=timestamp,
                    duration=duration,
                    error=error
                )
            
        except Exception as e:
            duration = time.time() - start_time
            health_check = HealthCheck(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                details={"exception": str(e), "traceback": traceback.format_exc()},
                timestamp=timestamp,
                duration=duration,
                error=str(e)
            )
            logger.error(f"Health check '{name}' failed: {e}")
        
        # Store in history
        self.check_history.append(health_check)
        if len(self.check_history) > self.history_limit:
            self.check_history.pop(0)
        
        return health_check
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        results = {}
        
        for name in self.checks:
            results[name] = await self.run_check(name)
        
        return results
    
    async def run_checks(self, check_names: List[str]) -> Dict[str, HealthCheck]:
        """Run specific health checks"""
        results = {}
        
        for name in check_names:
            results[name] = await self.run_check(name)
        
        return results
    
    # Built-in health check functions
    
    async def _check_system_memory(self) -> HealthCheck:
        """Check system memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {memory.percent:.1f}%"
            elif memory.percent > 80:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent:.1f}%"
            
            details = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
            
        except ImportError:
            status = HealthStatus.WARNING
            message = "psutil not available for memory monitoring"
            details = {"psutil_available": False}
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Memory check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            name="system_memory",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_system_disk(self) -> HealthCheck:
        """Check system disk usage"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            
            if disk.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {disk.percent:.1f}%"
            elif disk.percent > 80:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {disk.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk.percent:.1f}%"
            
            details = {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent,
                "used": disk.used
            }
            
        except ImportError:
            status = HealthStatus.WARNING
            message = "psutil not available for disk monitoring"
            details = {"psutil_available": False}
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Disk check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            name="system_disk",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_python_environment(self) -> HealthCheck:
        """Check Python environment"""
        try:
            import sys
            import platform
            
            status = HealthStatus.HEALTHY
            message = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} running"
            
            details = {
                "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": platform.platform(),
                "executable": sys.executable,
                "path": sys.path[:3]  # First 3 entries
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Python environment check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            name="python_environment",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_dependencies(self) -> HealthCheck:
        """Check critical dependencies"""
        critical_deps = [
            "fastapi", "uvicorn", "pydantic", "sqlalchemy",
            "asyncpg", "redis", "motor", "chromadb"
        ]
        
        missing_deps = []
        available_deps = []
        
        for dep in critical_deps:
            try:
                __import__(dep)
                available_deps.append(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if len(missing_deps) > 3:
            status = HealthStatus.CRITICAL
            message = f"Multiple critical dependencies missing: {missing_deps}"
        elif missing_deps:
            status = HealthStatus.WARNING
            message = f"Some dependencies missing: {missing_deps}"
        else:
            status = HealthStatus.HEALTHY
            message = "All critical dependencies available"
        
        details = {
            "available": available_deps,
            "missing": missing_deps,
            "total_checked": len(critical_deps)
        }
        
        return HealthCheck(
            name="dependencies",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_configuration(self) -> HealthCheck:
        """Check system configuration"""
        try:
            # Try to import and initialize settings
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
            
            from cognitive_twin.config.settings import Settings
            
            settings = Settings()
            
            # Check critical configuration
            config_issues = []
            
            if not hasattr(settings, 'openrouter_api_key') or not settings.openrouter_api_key:
                config_issues.append("OpenRouter API key not configured")
            
            if not hasattr(settings, 'database_url') or not settings.database_url:
                config_issues.append("Database URL not configured")
            
            if config_issues:
                status = HealthStatus.WARNING
                message = f"Configuration issues: {', '.join(config_issues)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Configuration appears valid"
            
            details = {
                "issues": config_issues,
                "settings_loaded": True
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Configuration check failed: {str(e)}"
            details = {"error": str(e), "settings_loaded": False}
        
        return HealthCheck(
            name="configuration",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_database_connections(self) -> HealthCheck:
        """Check database connections"""
        try:
            # This is a simplified check - would need actual connection testing
            connection_status = {
                "postgresql": "not_tested",
                "mongodb": "not_tested",
                "redis": "not_tested",
                "neo4j": "not_tested"
            }
            
            # Try Redis connection
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, decode_responses=True)
                r.ping()
                connection_status["redis"] = "connected"
            except Exception:
                connection_status["redis"] = "failed"
            
            # Count successful connections
            connected = sum(1 for status in connection_status.values() if status == "connected")
            failed = sum(1 for status in connection_status.values() if status == "failed")
            
            if failed > 2:
                status = HealthStatus.CRITICAL
                message = f"Multiple database connections failed"
            elif failed > 0:
                status = HealthStatus.WARNING
                message = f"Some database connections failed"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connections appear healthy"
            
            details = {
                "connections": connection_status,
                "connected": connected,
                "failed": failed
            }
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Database connection check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            name="database_connections",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_ai_services(self) -> HealthCheck:
        """Check AI services"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
            
            from cognitive_twin.ai.openrouter_client import OpenRouterClient
            
            # Try to initialize AI client
            client = OpenRouterClient()
            
            if not client.api_key:
                status = HealthStatus.WARNING
                message = "AI services not configured (missing API key)"
                details = {"api_key_configured": False}
            else:
                status = HealthStatus.HEALTHY
                message = "AI services configured"
                details = {"api_key_configured": True}
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"AI services check failed: {str(e)}"
            details = {"error": str(e)}
        
        return HealthCheck(
            name="ai_services",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_memory_system(self) -> HealthCheck:
        """Check memory system"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
            
            from cognitive_twin.memory.memory_manager import MemoryManager
            
            # Try to initialize memory manager
            memory_manager = MemoryManager()
            
            status = HealthStatus.HEALTHY
            message = "Memory system initialized"
            details = {"memory_manager_available": True}
            
        except Exception as e:
            status = HealthStatus.WARNING
            message = f"Memory system check failed: {str(e)}"
            details = {"error": str(e), "memory_manager_available": False}
        
        return HealthCheck(
            name="memory_system",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_event_system(self) -> HealthCheck:
        """Check event system"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
            
            from cognitive_twin.events.event_bus import EventBus
            
            # Try to initialize event bus
            event_bus = EventBus()
            
            status = HealthStatus.HEALTHY
            message = "Event system initialized"
            details = {"event_bus_available": True}
            
        except Exception as e:
            status = HealthStatus.WARNING
            message = f"Event system check failed: {str(e)}"
            details = {"error": str(e), "event_bus_available": False}
        
        return HealthCheck(
            name="event_system",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    async def _check_api_endpoints(self) -> HealthCheck:
        """Check API endpoints"""
        try:
            # This would test actual API endpoint health
            # For now, just check if the API modules can be imported
            
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
            
            from integrated_system.api.endpoints import digital_twin
            
            status = HealthStatus.HEALTHY
            message = "API endpoints available"
            details = {"api_modules_importable": True}
            
        except Exception as e:
            status = HealthStatus.WARNING
            message = f"API endpoints check failed: {str(e)}"
            details = {"error": str(e), "api_modules_importable": False}
        
        return HealthCheck(
            name="api_endpoints",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            duration=0.0
        )
    
    def get_check_history(self, 
                          check_name: Optional[str] = None,
                          hours: Optional[int] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get health check history.
        
        Args:
            check_name: Filter by check name
            hours: Number of hours of history to return
            limit: Maximum number of records to return
            
        Returns:
            List of health check results
        """
        history = self.check_history
        
        # Filter by check name
        if check_name:
            history = [check for check in history if check.name == check_name]
        
        # Filter by time
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            history = [check for check in history if check.timestamp > cutoff_time]
        
        # Limit results
        if limit:
            history = history[-limit:]
        
        # Convert to dictionaries
        return [
            {
                "name": check.name,
                "status": check.status.value,
                "message": check.message,
                "details": check.details,
                "timestamp": check.timestamp.isoformat(),
                "duration": check.duration,
                "error": check.error
            }
            for check in history
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get diagnostics system status"""
        return {
            "running": self.running,
            "registered_checks": list(self.checks.keys()),
            "check_count": len(self.checks),
            "history_size": len(self.check_history),
            "history_limit": self.history_limit
        }

# Global instance
health_diagnostics = HealthDiagnostics()
