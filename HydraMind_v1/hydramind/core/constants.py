"""
HydraMind Constants and Type Definitions

Centralized constants, enums, and type definitions for the entire HydraMind system.
Provides consistency and maintainability across all modules.
"""

from __future__ import annotations
import enum
from typing import Dict, Any, Optional, Union, Protocol, List, Tuple
from pathlib import Path


# =============================================================================
# CONSTANTS
# =============================================================================

# Default configuration values
DEFAULT_CONFIG = {
    'server': {
        'enabled': False,
        'host': '0.0.0.0',
        'port': 8765,
        'cors': ['*']
    },
    'logging': {
        'level': 'INFO',
        'json': True,
        'file_path': './logs/hydramind.log',
        'rotate_bytes': 15_000_000,  # 15MB
        'backups': 5
    },
    'event_db': './brain_events.sqlite',
    'snapshot_dir': './snapshots',
    'ring_name': 'hydra_ring',
    'ring_capacity': 16384,
    'ring_item_bytes': 2048,
    'max_events_per_sec': 50_000,
    'policy_allowlist': None
}

# Performance tuning constants
PERFORMANCE = {
    'event_bus_queue_size': 500_000,
    'thread_pool_workers': None,  # Auto-determined
    'process_pool_workers': None,  # Auto-determined
    'cache_ttl': 1.0,
    'health_check_interval': 0.5,
    'module_start_timeout': 30.0,
    'shutdown_timeout': 10.0
}

# System limits
LIMITS = {
    'max_topic_length': 255,
    'max_message_size': 1024 * 1024,  # 1MB
    'max_ring_items': 1_000_000,
    'max_cache_entries': 100_000,
    'max_concurrent_modules': 1000
}

# Event topics patterns
TOPIC_PATTERNS = {
    'system': 'system/*',
    'health': 'health/*',
    'telemetry': 'telemetry/*',
    'optimization': 'optimizer/*',
    'learning': 'learn/*',
    'anomaly': 'anomaly/*',
    'prediction': 'predictor/*',
    'coordination': 'swarm/*',
    'sensors': 'sensors/*'
}


# =============================================================================
# ENUMS
# =============================================================================

class LogLevel(str, enum.Enum):
    """Standard logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ModuleState(str, enum.Enum):
    """Module lifecycle states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ExecutionType(str, enum.Enum):
    """Types of execution contexts"""
    SYNC = "sync"
    THREAD = "thread"
    PROCESS = "process"
    ASYNC = "async"


class DataFormat(str, enum.Enum):
    """Supported data formats"""
    JSON = "json"
    BINARY = "binary"
    TEXT = "text"
    NUMPY = "numpy"


class OptimizationDomain(str, enum.Enum):
    """Optimization domains for self-optimization"""
    PERFORMANCE = "performance"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"


class PredictionType(str, enum.Enum):
    """Types of predictions"""
    EVENT = "event"  # Predict next event
    METRIC = "metric"  # Predict metric values
    ANOMALY = "anomaly"  # Predict anomalies
    LOAD = "load"  # Predict system load
    FAILURE = "failure"  # Predict failures


class AgentRole(str, enum.Enum):
    """Roles for autonomous agents"""
    WORKER = "worker"  # Performs tasks
    MONITOR = "monitor"  # System monitoring
    OPTIMIZER = "optimizer"  # Performance optimization
    HEALER = "healer"  # Self-healing operations
    COLLECTOR = "collector"  # Data collection
    LEARNER = "learner"  # Pattern learning


class PatternType(str, enum.Enum):
    """Types of patterns"""
    TEMPORAL = "temporal"  # Time-based patterns
    SEQUENTIAL = "sequential"  # Event sequence patterns
    CORRELATION = "correlation"  # Metric relationships
    ANOMALY = "anomaly"  # Deviation from baseline
    TREND = "trend"  # Long-term directional changes


class CollectionType(str, enum.Enum):
    """Types of data collection"""
    SYSTEM_METRICS = "system_metrics"
    MODULE_PERFORMANCE = "module_performance"
    EVENT_PATTERNS = "event_patterns"
    ERROR_LOGS = "error_logs"
    USAGE_ANALYTICS = "usage_analytics"


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

# Basic types
Topic = str
MessageId = str
Timestamp = float
JSONData = Dict[str, Any]

# Configuration types
ConfigDict = Dict[str, Any]
FeatureFlags = Dict[str, bool]

# Event types
EventData = Dict[str, Any]
EventKey = Optional[str]
EventQoS = int  # 0=fire-and-forget, 1=at-least-once

# Module types
ModuleName = str
ModuleConfig = Dict[str, Any]

# Statistics types
StatsDict = Dict[str, Any]
MetricsDict = Dict[str, Any]

# Data layer types
RingBufferName = str
RingBufferCapacity = int
RingBufferItemSize = int

# Execution types
ThreadPoolSize = int
ProcessPoolSize = int

# Cache types
CacheKey = str
CacheValue = Any
CacheTTL = float


# =============================================================================
# PROTOCOLS
# =============================================================================

class SubscriberProtocol(Protocol):
    """Protocol for event subscribers"""

    async def on_message(self, message: "Message") -> None:
        """Handle incoming message"""
        ...


class ModuleProtocol(Protocol):
    """Protocol for HydraMind modules"""

    name: str
    state: ModuleState

    async def start(self) -> None:
        """Start the module"""
        ...

    async def stop(self) -> None:
        """Stop the module"""
        ...

    async def on_message(self, message: "Message") -> None:
        """Handle incoming message"""
        ...

    def get_stats(self) -> StatsDict:
        """Get module statistics"""
        ...


class ExecutorProtocol(Protocol):
    """Protocol for execution engines"""

    async def submit(self, func, *args, **kwargs) -> Any:
        """Submit work for execution"""
        ...

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor"""
        ...


class DataStoreProtocol(Protocol):
    """Protocol for data storage backends"""

    def persist(self, topic: Topic, data: EventData, qos: EventQoS, key: EventKey) -> None:
        """Persist event data"""
        ...

    def query(self, topic_pattern: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query stored events"""
        ...


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def validate_topic(topic: str) -> bool:
    """Validate event topic format"""
    if not topic or len(topic) > LIMITS['max_topic_length']:
        return False
    # Basic validation - could be extended
    return True


def validate_message_size(data: EventData) -> bool:
    """Validate message size"""
    try:
        import json
        size = len(json.dumps(data).encode('utf-8'))
        return size <= LIMITS['max_message_size']
    except (TypeError, ValueError):
        return False


def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize configuration values"""
    sanitized = {}

    for key, value in config.items():
        if key == 'password' or 'secret' in key.lower() or 'key' in key.lower():
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_config(value)
        else:
            sanitized[key] = value

    return sanitized


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

DEFAULT_MODULE_CONFIG = {
    'start_timeout': PERFORMANCE['module_start_timeout'],
    'health_check_interval': PERFORMANCE['health_check_interval'],
    'max_concurrent_operations': 10,
    'retry_attempts': 3,
    'retry_delay': 1.0
}

DEFAULT_EXECUTOR_CONFIG = {
    'thread_pool_size': PERFORMANCE['thread_pool_workers'],
    'process_pool_size': PERFORMANCE['process_pool_workers'],
    'shutdown_timeout': PERFORMANCE['shutdown_timeout']
}

DEFAULT_CACHE_CONFIG = {
    'default_ttl': PERFORMANCE['cache_ttl'],
    'max_entries': LIMITS['max_cache_entries'],
    'cleanup_interval': 60.0
}

# Type aliases for common use cases
ResourceHint = Dict[str, Union[int, float, str]]
SystemMetrics = Dict[str, Union[int, float]]
ModuleHealth = Dict[str, Union[str, float, bool]]
