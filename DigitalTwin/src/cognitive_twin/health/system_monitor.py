"""
System Monitor for Cognitive-Twin

Provides continuous monitoring of system performance, resource usage,
and health metrics with alerting and reporting capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque
import json

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available. Install with: pip install psutil")

logger = logging.getLogger(__name__)

@dataclass
class MetricSnapshot:
    """System metric snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]

class SystemMonitor:
    """
    Continuous system monitoring with metrics collection and alerting.
    
    Monitors system resources, performance metrics, and application health
    with configurable thresholds and alert mechanisms.
    """
    
    def __init__(self, 
                 collection_interval: float = 30.0,
                 history_size: int = 288):  # 24 hours at 5-minute intervals
        """
        Initialize system monitor.
        
        Args:
            collection_interval: Interval between metric collections in seconds
            history_size: Number of metric snapshots to keep in history
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        
        # Metric storage
        self.metrics_history: deque = deque(maxlen=history_size)
        self.current_metrics: Optional[MetricSnapshot] = None
        
        # Monitoring state
        self.running = False
        self.monitor_task = None
        self.start_time = None
        
        # Alert thresholds
        self.thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        # Performance tracking
        self.collection_count = 0
        self.last_collection_time = None
        
        logger.info(f"System monitor initialized with {collection_interval}s interval")
    
    async def start(self):
        """Start system monitoring"""
        if not PSUTIL_AVAILABLE:
            logger.error("Cannot start system monitor: psutil not available")
            return
        
        self.running = True
        self.start_time = datetime.utcnow()
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("System monitoring started")
    
    async def stop(self):
        """Stop system monitoring"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        try:
            start_time = time.time()
            
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Get load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                load_avg = [0.0, 0.0, 0.0]
            
            # Create snapshot
            snapshot = MetricSnapshot(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                process_count=len(psutil.pids()),
                load_average=load_avg
            )
            
            # Store snapshot
            self.metrics_history.append(snapshot)
            self.current_metrics = snapshot
            
            # Check for alerts
            await self._check_alerts(snapshot)
            
            # Update collection stats
            self.collection_count += 1
            self.last_collection_time = time.time()
            
            collection_time = self.last_collection_time - start_time
            logger.debug(f"Metrics collected in {collection_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def _check_alerts(self, snapshot: MetricSnapshot):
        """Check metrics against thresholds and trigger alerts"""
        alerts = []
        
        # CPU alerts
        if snapshot.cpu_percent >= self.thresholds["cpu_critical"]:
            alerts.append({
                "type": "cpu",
                "level": "critical",
                "message": f"CPU usage critical: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds["cpu_critical"]
            })
        elif snapshot.cpu_percent >= self.thresholds["cpu_warning"]:
            alerts.append({
                "type": "cpu",
                "level": "warning",
                "message": f"CPU usage high: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds["cpu_warning"]
            })
        
        # Memory alerts
        if snapshot.memory_percent >= self.thresholds["memory_critical"]:
            alerts.append({
                "type": "memory",
                "level": "critical",
                "message": f"Memory usage critical: {snapshot.memory_percent:.1f}%",
                "value": snapshot.memory_percent,
                "threshold": self.thresholds["memory_critical"]
            })
        elif snapshot.memory_percent >= self.thresholds["memory_warning"]:
            alerts.append({
                "type": "memory",
                "level": "warning",
                "message": f"Memory usage high: {snapshot.memory_percent:.1f}%",
                "value": snapshot.memory_percent,
                "threshold": self.thresholds["memory_warning"]
            })
        
        # Disk alerts
        if snapshot.disk_percent >= self.thresholds["disk_critical"]:
            alerts.append({
                "type": "disk",
                "level": "critical",
                "message": f"Disk usage critical: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds["disk_critical"]
            })
        elif snapshot.disk_percent >= self.thresholds["disk_warning"]:
            alerts.append({
                "type": "disk",
                "level": "warning",
                "message": f"Disk usage high: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds["disk_warning"]
            })
        
        # Trigger alert callbacks
        for alert in alerts:
            await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
        logger.info(f"Added alert callback: {callback.__name__}")
    
    def remove_alert_callback(self, callback: Callable):
        """Remove alert callback function"""
        try:
            self.alert_callbacks.remove(callback)
            logger.info(f"Removed alert callback: {callback.__name__}")
        except ValueError:
            logger.warning(f"Alert callback not found: {callback.__name__}")
    
    def set_threshold(self, metric: str, value: float):
        """Set alert threshold for a metric"""
        if metric in self.thresholds:
            self.thresholds[metric] = value
            logger.info(f"Updated threshold {metric}: {value}")
        else:
            logger.warning(f"Unknown threshold metric: {metric}")
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current system metrics"""
        if not self.current_metrics:
            return None
        
        return {
            "timestamp": self.current_metrics.timestamp.isoformat(),
            "cpu_percent": self.current_metrics.cpu_percent,
            "memory_percent": self.current_metrics.memory_percent,
            "disk_percent": self.current_metrics.disk_percent,
            "network_io": self.current_metrics.network_io,
            "process_count": self.current_metrics.process_count,
            "load_average": self.current_metrics.load_average
        }
    
    def get_metrics_history(self, 
                           hours: Optional[int] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get metrics history.
        
        Args:
            hours: Number of hours of history to return
            limit: Maximum number of records to return
            
        Returns:
            List of metric snapshots
        """
        metrics = list(self.metrics_history)
        
        # Filter by time if specified
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        # Limit results if specified
        if limit:
            metrics = metrics[-limit:]
        
        # Convert to dictionaries
        return [
            {
                "timestamp": metric.timestamp.isoformat(),
                "cpu_percent": metric.cpu_percent,
                "memory_percent": metric.memory_percent,
                "disk_percent": metric.disk_percent,
                "network_io": metric.network_io,
                "process_count": metric.process_count,
                "load_average": metric.load_average
            }
            for metric in metrics
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        # Calculate averages and ranges
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        disk_values = [m.disk_percent for m in self.metrics_history]
        
        return {
            "monitoring_duration": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            "collection_count": self.collection_count,
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0
            },
            "disk": {
                "current": disk_values[-1] if disk_values else 0,
                "average": sum(disk_values) / len(disk_values) if disk_values else 0,
                "min": min(disk_values) if disk_values else 0,
                "max": max(disk_values) if disk_values else 0
            }
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get static system information"""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}
        
        try:
            return {
                "platform": psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else "unix",
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "python_version": f"{psutil.version_info.major}.{psutil.version_info.minor}.{psutil.version_info.micro}"
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        return {
            "running": self.running,
            "collection_interval": self.collection_interval,
            "history_size": self.history_size,
            "metrics_collected": len(self.metrics_history),
            "collection_count": self.collection_count,
            "last_collection": self.last_collection_time,
            "uptime": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            "thresholds": self.thresholds.copy(),
            "alert_callbacks": len(self.alert_callbacks),
            "psutil_available": PSUTIL_AVAILABLE
        }
    
    async def force_collection(self) -> Dict[str, Any]:
        """Force immediate metric collection"""
        await self._collect_metrics()
        return self.get_current_metrics()
