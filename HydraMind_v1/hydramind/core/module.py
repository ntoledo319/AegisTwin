"""
Base module system and DAG executor for HydraMind.

Modules are the building blocks - each encapsulates specific functionality
and communicates via the EventBus. This module provides the foundation
for creating maintainable, standardized modules.
"""

from __future__ import annotations
import asyncio
import logging
import time
import psutil
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Coroutine, Optional, Set, Union, Tuple

from .bus import EventBus, Message
from .execs import Exec
from .policy import PolicyGuard
from .constants import (
    ModuleName, ModuleState, StatsDict, JSONData, Topic,
    DEFAULT_MODULE_CONFIG, PERFORMANCE, LIMITS
)
from .exceptions import (
    ModuleError, ModuleInitializationError, ModuleLifecycleError,
    handle_exception
)
from .utils import measure_time, measure_async_time, get_system_info

logger = logging.getLogger(__name__)


@dataclass
class ModuleHealth:
    """
    Module health status information.

    Provides comprehensive health metrics for monitoring and debugging.
    """
    state: ModuleState
    uptime: float
    message_count: int
    error_count: int
    last_error: Optional[str]
    memory_usage: int
    cpu_usage: float
    health_score: float  # 0.0 to 1.0


class Module:
    """
    Base class for all HydraMind modules.

    Modules are the fundamental building blocks of HydraMind:
    - Subscribe to event topics via EventBus
    - Process events asynchronously with error isolation
    - Emit events to communicate with other modules
    - Have standardized lifecycle management (start/stop)
    - Provide health monitoring and statistics

    To create a module:
    1. Inherit from Module
    2. Set the 'name' class attribute
    3. Implement on_message() to handle events
    4. Optionally override start() for initialization
    5. Optionally override stop() for cleanup
    """

    name: ModuleName = "module"

    def __init__(
        self,
        bus: EventBus,
        ex: Exec,
        policy: PolicyGuard,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize module with dependencies and configuration.

        Args:
            bus: EventBus for event communication
            ex: Execution engine for async operations
            policy: Policy guard for security and rate limiting
            config: Optional module-specific configuration
        """
        # Core dependencies
        self.bus = bus
        self.exec = ex
        self.policy = policy

        # Configuration
        self.config = {**DEFAULT_MODULE_CONFIG, **(config or {})}

        # State management
        self.state = ModuleState.UNINITIALIZED
        self._start_time: Optional[float] = None
        self._stop_time: Optional[float] = None

        # Health tracking
        self._message_count = 0
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._subscriptions: Set[str] = set()

        # Logger for this module
        self.log = logging.getLogger(f"{__name__}.{self.name}")

        # Health monitoring task
        self._health_task: Optional[asyncio.Task] = None

        self.log.debug(f"Module '{self.name}' initialized")
    
    @measure_async_time
    async def start(self) -> None:
        """
        Start the module with proper state management and error handling.

        Override this to add custom initialization logic.
        Always call super().start() first!

        Raises:
            ModuleLifecycleError: If module fails to start
        """
        if self.state != ModuleState.UNINITIALIZED:
            raise ModuleLifecycleError(
                f"Cannot start module '{self.name}' in state {self.state}",
                details={'module': self.name, 'current_state': self.state.value}
            )

        try:
            self.state = ModuleState.INITIALIZING
            self._start_time = time.time()

            # Start health monitoring
            self._health_task = asyncio.create_task(self._health_monitor())

            # Custom initialization
            await self._initialize()

            self.state = ModuleState.RUNNING
            self.log.info(f"Module '{self.name}' started successfully")

        except Exception as e:
            self.state = ModuleState.ERROR
            self._last_error = str(e)
            self._error_count += 1

            raise ModuleLifecycleError(
                f"Failed to start module '{self.name}': {e}",
                details={'module': self.name, 'error': str(e)}
            ) from e

    async def _initialize(self) -> None:
        """
        Custom initialization logic.

        Override this method to add module-specific initialization.
        """
        pass  # Default implementation does nothing

    @measure_async_time
    async def stop(self) -> None:
        """
        Stop the module with proper cleanup and state management.

        Override this to add custom cleanup logic.
        Always call super().stop() first!

        Raises:
            ModuleLifecycleError: If module fails to stop
        """
        if self.state == ModuleState.STOPPED:
            return  # Already stopped

        if self.state not in (ModuleState.RUNNING, ModuleState.ERROR):
            self.log.warning(f"Stopping module '{self.name}' from unexpected state: {self.state}")

        try:
            self.state = ModuleState.STOPPING
            self._stop_time = time.time()

            # Stop health monitoring
            if self._health_task and not self._health_task.done():
                self._health_task.cancel()
                try:
                    await self._health_task
                except asyncio.CancelledError:
                    pass

            # Custom cleanup
            await self._cleanup()

            self.state = ModuleState.STOPPED
            self.log.info(f"Module '{self.name}' stopped successfully")

        except Exception as e:
            self.state = ModuleState.ERROR
            self._last_error = str(e)
            self._error_count += 1

            raise ModuleLifecycleError(
                f"Failed to stop module '{self.name}': {e}",
                details={'module': self.name, 'error': str(e)}
            ) from e

    async def _cleanup(self) -> None:
        """
        Custom cleanup logic.

        Override this method to add module-specific cleanup.
        """
        pass  # Default implementation does nothing
    
    async def on_message(self, msg: Message) -> None:
        """
        Handle incoming event message with error isolation and metrics.

        Override this to implement module logic.

        Args:
            msg: Event message to process
        """
        self._message_count += 1

        try:
            await self._handle_message(msg)
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)

            self.log.error(
                f"Error handling message '{msg.topic}': {e}",
                extra={'topic': msg.topic, 'error': str(e)}
            )

            # Emit error event for monitoring
            try:
                await self._emit_error_event(msg, e)
            except Exception as emit_error:
                self.log.error(f"Failed to emit error event: {emit_error}")

    async def _handle_message(self, msg: Message) -> None:
        """
        Process the actual message.

        Override this method to implement your module's message handling logic.
        """
        self.log.warning(f"{self.name} received message but _handle_message() not implemented")

    async def _emit_error_event(self, original_msg: Message, error: Exception) -> None:
        """Emit error event for monitoring."""
        await self.emit("module/error", {
            'module': self.name,
            'original_topic': original_msg.topic,
            'error': str(error),
            'timestamp': time.time()
        })

    async def _health_monitor(self) -> None:
        """Periodic health monitoring task with proper cancellation handling."""
        interval = self.config.get('health_check_interval', PERFORMANCE['health_check_interval'])

        try:
            while self.state in (ModuleState.RUNNING, ModuleState.INITIALIZING):
                try:
                    # Emit health telemetry
                    health = self.get_health()
                    await self.emit("health/telemetry", {
                        'module': self.name,
                        'health': health,
                        'timestamp': time.time()
                    })

                    # Use asyncio.wait_for to ensure proper cancellation
                    await asyncio.wait_for(
                        asyncio.sleep(interval),
                        timeout=interval + 1.0  # Add small buffer for cleanup
                    )

                except asyncio.TimeoutError:
                    # This shouldn't happen with wait_for, but handle it
                    continue
                except asyncio.CancelledError:
                    self.log.debug(f"Health monitoring cancelled for module '{self.name}'")
                    break
                except Exception as e:
                    self.log.error(f"Health monitoring error for module '{self.name}': {e}")
                    # Continue monitoring even if there's an error
                    try:
                        await asyncio.sleep(min(interval, 1.0))  # Brief pause on error
                    except asyncio.CancelledError:
                        break
        except asyncio.CancelledError:
            self.log.debug(f"Health monitoring task cancelled for module '{self.name}'")
        finally:
            self.log.debug(f"Health monitoring stopped for module '{self.name}'")

    def get_health(self) -> ModuleHealth:
        """
        Get current health status of the module.

        Returns:
            ModuleHealth object with comprehensive health metrics
        """
        uptime = 0.0
        if self._start_time:
            uptime = time.time() - self._start_time

        # Calculate health score (0.0 to 1.0)
        error_rate = self._error_count / max(self._message_count, 1)
        health_score = max(0.0, 1.0 - error_rate)

        # Get memory usage (approximate)
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            memory_usage = 0

        # Get CPU usage (approximate)
        try:
            cpu_usage = process.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cpu_usage = 0.0

        return ModuleHealth(
            state=self.state,
            uptime=uptime,
            message_count=self._message_count,
            error_count=self._error_count,
            last_error=self._last_error,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            health_score=health_score
        )
    
    async def emit(
        self,
        topic: str,
        data: Dict[str, Any],
        qos: int = 0,
        key: Optional[str] = None
    ) -> bool:
        """
        Emit an event to the bus.

        Args:
            topic: Event topic
            data: Event payload (must be JSON-serializable dict)
            qos: Quality of service (0 or 1)
            key: Optional key for deduplication

        Returns:
            True if message was accepted by policy

        Raises:
            ValueError: If input parameters are invalid
        """
        # Input validation
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"Topic must be a non-empty string, got: {topic}")

        if not isinstance(data, dict):
            raise ValueError(f"Data must be a dictionary, got: {type(data)}")

        if qos not in (0, 1):
            raise ValueError(f"QoS must be 0 or 1, got: {qos}")

        if key is not None and not isinstance(key, str):
            raise ValueError(f"Key must be a string or None, got: {type(key)}")

        # Validate data size to prevent memory issues
        try:
            import json
            data_size = len(json.dumps(data).encode('utf-8'))
            if data_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError(f"Data payload too large: {data_size} bytes (max: 10MB)")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Data is not JSON serializable: {e}") from e

        msg = Message(topic, data, qos, key)

        if self.policy.verify(msg):
            await self.bus.publish(msg)
            return True
        else:
            self.log.warning(f"Policy rejected message: {topic}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        return {
            "name": self.name,
            "running": self._running,
            "messages_handled": self._message_count,
            "errors": self._error_count
        }


@dataclass
class TaskNode:
    """
    Node in a task DAG (Directed Acyclic Graph).
    
    Attributes:
        id: Unique task identifier
        fn: Function to execute (can be sync or async)
        deps: List of task IDs this task depends on
        params: Parameters to pass to function
        tier: Execution tier (0=async, 1=thread, 2=process)
    """
    id: str
    fn: Callable[..., Any] | Callable[..., Coroutine[Any, Any, Any]]
    deps: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    tier: int = 1  # 0=async, 1=thread, 2+=process
    
    def __post_init__(self):
        """Validate task node."""
        if self.tier < 0:
            raise ValueError("Tier must be >= 0")
        if not self.id:
            raise ValueError("Task ID cannot be empty")


class DAG(Module):
    """
    Directed Acyclic Graph executor for task orchestration.
    
    Enables:
    - Dependency-based task execution
    - Parallel execution of independent tasks
    - Automatic tier-based execution (async/thread/process)
    - Result passing between tasks
    
    Example:
        dag = DAG(bus, ex, policy)
        dag.add(TaskNode("fetch", fn=fetch_data, tier=1))
        dag.add(TaskNode("process", fn=process, deps=["fetch"], tier=2))
        dag.add(TaskNode("store", fn=store, deps=["process"], tier=1))
        
        results = await dag.run(["store"])  # Runs all dependencies
    """
    
    name = "dag"
    
    def __init__(self, bus: EventBus, ex: Exec, policy: PolicyGuard):
        super().__init__(bus, ex, policy)
        self.graph: Dict[str, TaskNode] = {}
        self._execution_count = 0
    
    def add(self, node: TaskNode) -> None:
        """
        Add task node to DAG.
        
        Args:
            node: Task node to add
        """
        if node.id in self.graph:
            self.log.warning(f"Overwriting existing task: {node.id}")
        
        self.graph[node.id] = node
        self.log.debug(f"Added task '{node.id}' with deps={node.deps}")
    
    def remove(self, task_id: str) -> bool:
        """
        Remove task from DAG.
        
        Args:
            task_id: Task ID to remove
            
        Returns:
            True if task was removed
        """
        if task_id in self.graph:
            del self.graph[task_id]
            self.log.debug(f"Removed task '{task_id}'")
            return True
        return False
    
    def _check_cycle(self, start_id: str, visited: Optional[Set[str]] = None) -> bool:
        """
        Check for cycles in the DAG starting from a node.
        
        Args:
            start_id: Starting task ID
            visited: Set of visited nodes
            
        Returns:
            True if cycle detected
        """
        if visited is None:
            visited = set()
        
        if start_id in visited:
            return True
        
        if start_id not in self.graph:
            return False
        
        visited.add(start_id)
        
        for dep_id in self.graph[start_id].deps:
            if self._check_cycle(dep_id, visited.copy()):
                return True
        
        return False
    
    async def run(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        Execute tasks with dependency resolution.
        
        Tasks are executed in dependency order, with independent tasks
        running in parallel.
        
        Args:
            task_ids: List of task IDs to execute (dependencies auto-included)
            
        Returns:
            Dictionary mapping task IDs to results
            
        Raises:
            ValueError: If task not found or cycle detected
            RuntimeError: If dependency resolution fails
        """
        self._execution_count += 1
        start_time = time.time()
        
        # Validate tasks exist
        for tid in task_ids:
            if tid not in self.graph:
                raise ValueError(f"Task '{tid}' not found in DAG")
            if self._check_cycle(tid):
                raise ValueError(f"Cycle detected starting at task '{tid}'")
        
        results: Dict[str, Any] = {}
        pending = set(task_ids)
        
        # Expand to include all dependencies
        def add_deps(tid: str):
            if tid in pending:
                return
            pending.add(tid)
            for dep_id in self.graph[tid].deps:
                add_deps(dep_id)
        
        for tid in task_ids:
            add_deps(tid)
        
        self.log.info(f"Executing DAG: {len(pending)} tasks")
        
        # Execute in waves
        wave = 0
        while pending:
            wave += 1
            
            # Find tasks with all dependencies satisfied
            ready = [
                tid for tid in pending
                if all(dep_id in results for dep_id in self.graph[tid].deps)
            ]
            
            if not ready:
                unresolved = {tid: self.graph[tid].deps for tid in pending}
                raise ModuleError(
                    f"Dependency cycle detected or missing tasks. "
                    f"Unresolved: {unresolved}",
                    details={'unresolved_tasks': unresolved}
                )
            
            self.log.debug(f"Wave {wave}: executing {len(ready)} tasks")
            
            # Execute ready tasks in parallel
            tasks = []
            for tid in ready:
                tasks.append((tid, self._execute_task(tid, results)))
            
            # Wait for wave to complete
            for tid, task in tasks:
                try:
                    result = await task
                    results[tid] = result
                    pending.remove(tid)
                    
                except Exception as e:
                    self.log.error(f"Task '{tid}' failed: {e}", exc_info=True)
                    # Store exception as result
                    results[tid] = e
                    pending.remove(tid)
        
        elapsed = time.time() - start_time
        self.log.info(
            f"DAG execution completed: {len(results)} tasks in {elapsed:.3f}s "
            f"({wave} waves)"
        )
        
        return results
    
    async def _execute_task(
        self,
        task_id: str,
        results: Dict[str, Any]
    ) -> Any:
        """
        Execute a single task.
        
        Args:
            task_id: Task to execute
            results: Current results (for dependency injection)
            
        Returns:
            Task result
        """
        node = self.graph[task_id]
        
        # Inject dependency results into params
        params = node.params.copy()
        for dep_id in node.deps:
            params[f"dep_{dep_id}"] = results.get(dep_id)
        
        self.log.debug(f"Executing task '{task_id}' (tier={node.tier})")
        
        try:
            # Execute based on tier
            if asyncio.iscoroutinefunction(node.fn):
                # Async function - run directly
                result = await node.fn(**params)
                
            elif node.tier >= 2:
                # CPU-bound - use process pool
                result = await self.ex.process(node.fn, **params)
                
            elif node.tier >= 1:
                # I/O-bound - use thread pool
                result = await self.ex.thread(node.fn, **params)
                
            else:
                # Tier 0 - run in current thread
                result = node.fn(**params)
            
            return result
            
        except Exception as e:
            self.log.error(f"Task '{task_id}' failed: {e}")
            raise
    
    async def on_message(self, msg: Message) -> None:
        """Handle DAG execution requests."""
        if msg.topic == "dag/run":
            try:
                task_ids = msg.data.get("tasks", [])
                results = await self.run(task_ids)
                
                # Convert exceptions to strings for JSON serialization
                safe_results = {}
                for tid, result in results.items():
                    if isinstance(result, Exception):
                        safe_results[tid] = {"error": str(result)}
                    else:
                        safe_results[tid] = result
                
                await self.emit("dag/result", {
                    "tasks": task_ids,
                    "results": safe_results
                })
                
            except Exception as e:
                self.log.error(f"DAG execution failed: {e}", exc_info=True)
                await self.emit("dag/error", {
                    "error": str(e)
                })
    
    def get_stats(self) -> dict:
        """Get DAG statistics."""
        stats = super().get_stats()
        stats.update({
            "tasks_registered": len(self.graph),
            "executions": self._execution_count
        })
        return stats


class Health(Module):
    """
    System health monitoring module.
    
    Periodically emits telemetry about CPU, memory, and disk usage.
    Useful for monitoring, anomaly detection, and optimization.
    """
    
    name = "health"
    
    def __init__(
        self,
        bus: EventBus,
        ex: Exec,
        policy: PolicyGuard,
        interval: float = 0.5
    ):
        """
        Initialize health monitor.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            interval: Telemetry interval in seconds
        """
        super().__init__(bus, ex, policy)
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start health monitoring loop."""
        await super().start()
        self._task = asyncio.create_task(self._loop())
    
    async def stop(self) -> None:
        """Stop health monitoring."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
    
    async def _loop(self) -> None:
        """Telemetry emission loop."""
        while self._running:
            try:
                # Gather system metrics
                cpu_pct = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Emit telemetry
                await self.emit("health/telemetry", {
                    "cpu": cpu_pct,
                    "mem": mem.percent,
                    "mem_available_gb": mem.available / (1024 ** 3),
                    "disk": disk.percent,
                    "ts": time.time()
                })
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                self.log.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.interval)
