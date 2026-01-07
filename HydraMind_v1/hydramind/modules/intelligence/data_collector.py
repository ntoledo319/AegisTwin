"""
Data Collector Module - Autonomous Data Gathering and Processing

Collects, aggregates, and processes data from various system sources.
Inspired by data collection drones from SEED swarm architecture.
"""

import asyncio
import logging
import time
import json
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from ...core.module import Module
from ...core.bus import Message


logger = logging.getLogger(__name__)


class CollectionType(Enum):
    """Types of data collection"""
    SYSTEM_METRICS = "system_metrics"
    MODULE_PERFORMANCE = "module_performance"
    EVENT_PATTERNS = "event_patterns"
    ERROR_LOGS = "error_logs"
    USAGE_ANALYTICS = "usage_analytics"


@dataclass
class CollectionResult:
    """Result of a data collection operation"""
    collection_type: CollectionType
    records_collected: int
    data_summary: Dict[str, Any]
    insights: List[str]
    timestamp: float


@dataclass
class DataSeries:
    """Time series data storage"""
    name: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add(self, value: Any, timestamp: Optional[float] = None):
        """Add value to series"""
        if timestamp is None:
            timestamp = time.time()
        self.values.append({'value': value, 'timestamp': timestamp})
    
    def get_recent(self, n: int = 100) -> List[Any]:
        """Get n most recent values"""
        return list(self.values)[-n:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistical summary"""
        if not self.values:
            return {}
        
        numeric_values = [v['value'] for v in self.values if isinstance(v['value'], (int, float))]
        if not numeric_values:
            return {'count': len(self.values)}
        
        return {
            'count': len(numeric_values),
            'min': min(numeric_values),
            'max': max(numeric_values),
            'mean': sum(numeric_values) / len(numeric_values),
            'last': numeric_values[-1]
        }


class DataCollector(Module):
    """
    Autonomous data collection and aggregation module.
    
    Continuously collects data from various system sources, aggregates it,
    and generates insights. Inspired by data collection drones.
    
    Events consumed:
    - collector/start: Start collection
    - collector/stop: Stop collection
    - collector/collect: Manual collection trigger
    - health/telemetry: System telemetry
    - module/performance: Module performance data
    - module/error: Module errors
    
    Events emitted:
    - collector/result: Collection result
    - collector/insight: Data insight discovered
    - collector/summary: Periodic data summary
    """
    
    name = "data_collector"
    
    def __init__(
        self, 
        bus, 
        ex, 
        policy, 
        collection_interval=60.0,
        summary_interval=300.0
    ):
        """
        Initialize data collector.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            collection_interval: Seconds between collections (default: 1 min)
            summary_interval: Seconds between summaries (default: 5 min)
        """
        super().__init__(bus, ex, policy)
        self.collection_interval = collection_interval
        self.summary_interval = summary_interval
        
        # Data storage
        self.data_series: Dict[str, DataSeries] = {}
        self.collection_results: List[CollectionResult] = []
        
        # Collection state
        self._collection_task: Optional[asyncio.Task] = None
        self._summary_task: Optional[asyncio.Task] = None
        self._collecting = False
        self._last_collection_time = 0.0
        self._last_summary_time = 0.0
        
        # Aggregation buffers
        self.event_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.performance_metrics = defaultdict(list)
        
        # Initialize default data series
        self._init_data_series()
    
    def _init_data_series(self) -> None:
        """Initialize default data series"""
        series_names = [
            'cpu_usage',
            'memory_usage',
            'disk_usage',
            'event_rate',
            'error_rate',
            'module_count',
            'message_throughput'
        ]
        
        for name in series_names:
            self.data_series[name] = DataSeries(name)
    
    async def start(self) -> None:
        """Start data collection"""
        await super().start()
        
        # Subscribe to data sources
        await self.bus.subscribe("collector/start", self._handle_start)
        await self.bus.subscribe("collector/stop", self._handle_stop)
        await self.bus.subscribe("collector/collect", self._handle_collect)
        await self.bus.subscribe("health/telemetry", self._handle_telemetry)
        await self.bus.subscribe("module/performance", self._handle_performance)
        await self.bus.subscribe("module/error", self._handle_error)
        await self.bus.subscribe("*", self._handle_any_event)
        
        # Start collection loop
        self._collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._summary_task = asyncio.create_task(self._summary_loop())
        
        self.log.info("Data collector started")
    
    async def stop(self) -> None:
        """Stop data collection"""
        self._collecting = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        if self._summary_task:
            self._summary_task.cancel()
            try:
                await self._summary_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.log.info("Data collector stopped")
    
    async def _collection_loop(self) -> None:
        """Periodic data collection loop"""
        while self._collecting:
            try:
                await asyncio.sleep(self.collection_interval)
                
                # Collect data from all sources
                results = await self._collect_all_data()
                
                # Generate insights
                insights = self._generate_insights(results)
                
                # Emit insights
                for insight in insights:
                    await self.emit("collector/insight", {
                        "insight": insight,
                        "timestamp": time.time()
                    })
                
                self._last_collection_time = time.time()
                
            except Exception as e:
                self.log.error(f"Collection loop error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _summary_loop(self) -> None:
        """Periodic summary generation loop"""
        while self._collecting:
            try:
                await asyncio.sleep(self.summary_interval)
                
                # Generate summary of collected data
                summary = self._generate_summary()
                
                # Emit summary
                await self.emit("collector/summary", summary)
                
                self._last_summary_time = time.time()
                
            except Exception as e:
                self.log.error(f"Summary loop error: {e}")
                await asyncio.sleep(self.summary_interval)
    
    async def _handle_start(self, msg: Message) -> None:
        """Handle start collection request"""
        self._collecting = True
        self.log.info("Data collection started via event")
    
    async def _handle_stop(self, msg: Message) -> None:
        """Handle stop collection request"""
        self._collecting = False
        self.log.info("Data collection stopped via event")
    
    async def _handle_collect(self, msg: Message) -> None:
        """Handle manual collection request"""
        try:
            collection_type = msg.data.get('type', 'all')
            
            if collection_type == 'all':
                results = await self._collect_all_data()
            else:
                # Collect specific type
                results = [await self._collect_specific_data(CollectionType(collection_type))]
            
            # Emit results
            await self.emit("collector/result", {
                "request_id": msg.data.get('request_id'),
                "results": [self._result_to_dict(r) for r in results],
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.log.error(f"Error handling collect request: {e}")
    
    async def _handle_telemetry(self, msg: Message) -> None:
        """Handle incoming telemetry data"""
        try:
            data = msg.data
            
            # Store telemetry in data series
            if 'cpu' in data:
                self.data_series['cpu_usage'].add(data['cpu'])
            if 'mem' in data:
                self.data_series['memory_usage'].add(data['mem'])
            if 'disk' in data:
                self.data_series['disk_usage'].add(data['disk'])
            
        except Exception as e:
            self.log.error(f"Error handling telemetry: {e}")
    
    async def _handle_performance(self, msg: Message) -> None:
        """Handle module performance data"""
        try:
            data = msg.data
            module_name = data.get('module', 'unknown')
            
            # Store performance metrics
            self.performance_metrics[module_name].append({
                'latency': data.get('latency', 0),
                'throughput': data.get('throughput', 0),
                'timestamp': time.time()
            })
            
            # Keep buffer size manageable
            if len(self.performance_metrics[module_name]) > 1000:
                self.performance_metrics[module_name] = self.performance_metrics[module_name][-500:]
            
        except Exception as e:
            self.log.error(f"Error handling performance: {e}")
    
    async def _handle_error(self, msg: Message) -> None:
        """Handle module error data"""
        try:
            data = msg.data
            module_name = data.get('module', 'unknown')
            error_type = data.get('error_type', 'unknown')
            
            # Count errors
            self.error_counts[f"{module_name}:{error_type}"] += 1
            
            # Update error rate series
            current_total = sum(self.error_counts.values())
            self.data_series['error_rate'].add(current_total)
            
        except Exception as e:
            self.log.error(f"Error handling error: {e}")
    
    async def _handle_any_event(self, msg: Message) -> None:
        """Handle any event for pattern tracking"""
        try:
            # Count events by topic
            self.event_counts[msg.topic] += 1
            
            # Update event rate series
            current_total = sum(self.event_counts.values())
            self.data_series['event_rate'].add(current_total)
            
        except Exception as e:
            pass  # Silent failure for catch-all handler
    
    async def _collect_all_data(self) -> List[CollectionResult]:
        """Collect data from all sources"""
        results = []
        
        for collection_type in CollectionType:
            try:
                result = await self._collect_specific_data(collection_type)
                results.append(result)
                self.collection_results.append(result)
                
                # Keep results history manageable
                if len(self.collection_results) > 1000:
                    self.collection_results = self.collection_results[-500:]
                
            except Exception as e:
                self.log.error(f"Error collecting {collection_type.value}: {e}")
        
        return results
    
    async def _collect_specific_data(self, collection_type: CollectionType) -> CollectionResult:
        """Collect specific type of data"""
        if collection_type == CollectionType.SYSTEM_METRICS:
            return await self._collect_system_metrics()
        elif collection_type == CollectionType.MODULE_PERFORMANCE:
            return await self._collect_module_performance()
        elif collection_type == CollectionType.EVENT_PATTERNS:
            return await self._collect_event_patterns()
        elif collection_type == CollectionType.ERROR_LOGS:
            return await self._collect_error_logs()
        else:  # USAGE_ANALYTICS
            return await self._collect_usage_analytics()
    
    async def _collect_system_metrics(self) -> CollectionResult:
        """Collect system metrics"""
        # Get stats from data series
        cpu_stats = self.data_series['cpu_usage'].get_stats()
        mem_stats = self.data_series['memory_usage'].get_stats()
        disk_stats = self.data_series['disk_usage'].get_stats()
        
        summary = {
            'cpu': cpu_stats,
            'memory': mem_stats,
            'disk': disk_stats
        }
        
        insights = []
        
        # Generate insights based on metrics
        if cpu_stats.get('mean', 0) > 80:
            insights.append("High average CPU usage detected")
        if mem_stats.get('mean', 0) > 85:
            insights.append("High memory usage trend detected")
        if disk_stats.get('last', 0) > 90:
            insights.append("Disk space critical")
        
        return CollectionResult(
            collection_type=CollectionType.SYSTEM_METRICS,
            records_collected=cpu_stats.get('count', 0),
            data_summary=summary,
            insights=insights,
            timestamp=time.time()
        )
    
    async def _collect_module_performance(self) -> CollectionResult:
        """Collect module performance data"""
        summary = {}
        insights = []
        total_records = 0
        
        for module_name, metrics in self.performance_metrics.items():
            if metrics:
                recent = metrics[-100:]  # Last 100 samples
                
                avg_latency = sum(m['latency'] for m in recent) / len(recent)
                avg_throughput = sum(m['throughput'] for m in recent) / len(recent)
                
                summary[module_name] = {
                    'avg_latency': avg_latency,
                    'avg_throughput': avg_throughput,
                    'sample_count': len(recent)
                }
                
                total_records += len(recent)
                
                # Generate insights
                if avg_latency > 1000:
                    insights.append(f"High latency in {module_name}: {avg_latency:.1f}ms")
                if avg_throughput < 10:
                    insights.append(f"Low throughput in {module_name}: {avg_throughput:.1f} ops/s")
        
        return CollectionResult(
            collection_type=CollectionType.MODULE_PERFORMANCE,
            records_collected=total_records,
            data_summary=summary,
            insights=insights,
            timestamp=time.time()
        )
    
    async def _collect_event_patterns(self) -> CollectionResult:
        """Collect event pattern data"""
        # Get top event topics
        top_events = sorted(
            self.event_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        total_events = sum(self.event_counts.values())
        
        summary = {
            'total_events': total_events,
            'unique_topics': len(self.event_counts),
            'top_events': [{'topic': topic, 'count': count} for topic, count in top_events]
        }
        
        insights = []
        
        # Generate insights
        if top_events:
            dominant_topic, dominant_count = top_events[0]
            if dominant_count > total_events * 0.5:
                insights.append(f"Dominant event pattern: {dominant_topic} ({dominant_count} events)")
        
        return CollectionResult(
            collection_type=CollectionType.EVENT_PATTERNS,
            records_collected=total_events,
            data_summary=summary,
            insights=insights,
            timestamp=time.time()
        )
    
    async def _collect_error_logs(self) -> CollectionResult:
        """Collect error log data"""
        # Get top errors
        top_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        total_errors = sum(self.error_counts.values())
        
        summary = {
            'total_errors': total_errors,
            'unique_error_types': len(self.error_counts),
            'top_errors': [{'error': error, 'count': count} for error, count in top_errors]
        }
        
        insights = []
        
        # Generate insights
        if total_errors > 100:
            insights.append(f"High error rate: {total_errors} total errors")
        
        if top_errors:
            top_error, top_count = top_errors[0]
            if top_count > total_errors * 0.5:
                insights.append(f"Recurring error pattern: {top_error} ({top_count} occurrences)")
        
        return CollectionResult(
            collection_type=CollectionType.ERROR_LOGS,
            records_collected=total_errors,
            data_summary=summary,
            insights=insights,
            timestamp=time.time()
        )
    
    async def _collect_usage_analytics(self) -> CollectionResult:
        """Collect usage analytics"""
        # Calculate usage stats from event patterns
        total_events = sum(self.event_counts.values())
        event_rate = self.data_series['event_rate'].get_stats()
        
        summary = {
            'total_events': total_events,
            'event_rate': event_rate,
            'active_modules': len(self.performance_metrics)
        }
        
        insights = []
        
        # Generate insights
        if event_rate.get('mean', 0) > 1000:
            insights.append("High system activity detected")
        
        return CollectionResult(
            collection_type=CollectionType.USAGE_ANALYTICS,
            records_collected=total_events,
            data_summary=summary,
            insights=insights,
            timestamp=time.time()
        )
    
    def _generate_insights(self, results: List[CollectionResult]) -> List[str]:
        """Generate insights from collection results"""
        all_insights = []
        
        for result in results:
            all_insights.extend(result.insights)
        
        # Add cross-collection insights
        # (e.g., correlating high errors with high CPU usage)
        
        return all_insights
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all collected data"""
        summary = {
            'timestamp': time.time(),
            'collection_results_count': len(self.collection_results),
            'data_series': {},
            'top_events': [],
            'top_errors': [],
            'system_health_indicators': {}
        }
        
        # Summarize data series
        for name, series in self.data_series.items():
            summary['data_series'][name] = series.get_stats()
        
        # Top events
        top_events = sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        summary['top_events'] = [{'topic': t, 'count': c} for t, c in top_events]
        
        # Top errors
        top_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        summary['top_errors'] = [{'error': e, 'count': c} for e, c in top_errors]
        
        # System health indicators
        summary['system_health_indicators'] = {
            'total_errors': sum(self.error_counts.values()),
            'total_events': sum(self.event_counts.values()),
            'active_data_series': len([s for s in self.data_series.values() if len(s.values) > 0])
        }
        
        return summary
    
    def _result_to_dict(self, result: CollectionResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'collection_type': result.collection_type.value,
            'records_collected': result.records_collected,
            'data_summary': result.data_summary,
            'insights': result.insights,
            'timestamp': result.timestamp
        }
    
    async def on_message(self, msg: Message) -> None:
        """Handle incoming messages"""
        # Handled by specific subscribers
        pass
    
    def get_stats(self) -> dict:
        """Get collector statistics"""
        stats = super().get_stats()
        
        stats.update({
            "collecting": self._collecting,
            "data_series_count": len(self.data_series),
            "collection_results_count": len(self.collection_results),
            "last_collection_time": self._last_collection_time,
            "last_summary_time": self._last_summary_time,
            "total_events_tracked": sum(self.event_counts.values()),
            "total_errors_tracked": sum(self.error_counts.values()),
            "modules_tracked": len(self.performance_metrics)
        })
        return stats
