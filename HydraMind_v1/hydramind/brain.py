"""
HydraMind Brain - Main orchestrator and entry point.

The Brain initializes all components and coordinates the cognitive kernel.
"""

from __future__ import annotations
import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
import logging

from .core.config import load_config, BrainConfig
from .core.logging import setup_logging, MetricsLogger
from .core.event_store import EventStore
from .core.bus import EventBus, Message
from .core.execs import ResourceManager, Exec
from .core.policy import PolicyGuard
from .core.data import RingBuffer, MMapSnapshot, TTLCache
from .core.module import DAG, TaskNode, Health, Module, ModuleState
from .core.constants import (
    DEFAULT_CONFIG, PERFORMANCE, LIMITS,
    ModuleName, StatsDict, JSONData
)
from .core.exceptions import (
    HydraMindError, ConfigurationError, ModuleError,
    handle_exception, create_error_context
)
from .core.utils import (
    measure_time, measure_async_time, get_system_info,
    retry_async, deep_merge
)

# Lazy import functions to avoid circular imports
def _import_intelligence_modules():
    """Lazy import intelligence modules to avoid circular imports."""
    try:
        from .modules.intelligence.seed_optimizer import SeedOptimizer as SOpt
        from .modules.intelligence.replay_service import ReplayService as RService
        from .modules.intelligence.anomaly_lab import AnomalyLab as ALab
        from .modules.intelligence.optimizer_suite import OptimizerSuite as OSuite
        from .modules.intelligence.meta_planner import MetaPlanner as MPlanner
        return SOpt, RService, ALab, OSuite, MPlanner
    except ImportError as e:
        logger.warning(f"Failed to import some intelligence modules: {e}")
        return None, None, None, None, None

def _import_domain_modules():
    """Lazy import domain modules to avoid circular imports."""
    try:
        from .modules.infrastructure.sensors import SensorHub as SHub
        from .modules.domain.domain_examples import (
            DroneFleet as DFleet,
            RoboticsCell as RCell,
            TradingEngine as TEngine,
            DBAnalyzer as DBAnalyzer
        )
        return SHub, DFleet, RCell, TEngine, DBAnalyzer
    except ImportError as e:
        logger.warning(f"Failed to import some domain modules: {e}")
        return None, None, None, None, None

# Control plane
from .control.api import build_app

logger = logging.getLogger(__name__)


class Registry:
    """
    Module registry for HydraMind.
    
    Manages module lifecycle and event subscriptions.
    """
    
    def __init__(self, bus: EventBus):
        """
        Initialize registry.
        
        Args:
            bus: EventBus for subscriptions
        """
        self.bus = bus
        self.mods = {}
        logger.info("Module registry initialized")
    
    def add(self, module, patterns: List[str]) -> None:
        """
        Register module with subscription patterns.
        
        Args:
            module: Module instance
            patterns: List of topic patterns to subscribe to
        """
        self.mods[module.name] = module
        
        for pattern in patterns:
            self.bus.subscribe(pattern, module)
        
        logger.info(
            f"Registered module '{module.name}' with patterns: {patterns}"
        )
    
    def all(self) -> List[Module]:
        """Get all registered modules."""
        return list(self.mods.values())
    
    def get(self, name: str) -> Optional[Module]:
        """Get module by name."""
        return self.mods.get(name)


class HydraBrain:
    """
    Main HydraMind cognitive kernel.
    
    The Brain:
    - Initializes all core infrastructure
    - Registers and starts modules
    - Coordinates lifecycle and shutdown
    - Optionally runs FastAPI control plane
    
    This is the universal core - adapt by:
    1. Creating your own modules
    2. Registering them in your subclass
    3. Configuring via YAML or environment
    """

    def _load_configuration(self, cfg_path: Union[str, Path]) -> BrainConfig:
        """Load and validate configuration with comprehensive error handling."""
        try:
            config = load_config(cfg_path)

            # Validate critical configuration values
            if not isinstance(config.ring_capacity, int) or config.ring_capacity < 1024:
                raise ConfigurationError(
                    f"Ring buffer capacity must be an integer >= 1024, got: {config.ring_capacity}",
                    details={'ring_capacity': config.ring_capacity, 'minimum': 1024}
                )

            if not isinstance(config.max_events_per_sec, int) or config.max_events_per_sec <= 0:
                raise ConfigurationError(
                    f"Max events per second must be an integer > 0, got: {config.max_events_per_sec}",
                    details={'max_events_per_sec': config.max_events_per_sec, 'minimum': 1}
                )

            # Validate server configuration if enabled
            if config.server.enabled:
                if not isinstance(config.server.port, int) or not (1 <= config.server.port <= 65535):
                    raise ConfigurationError(
                        f"Server port must be an integer between 1-65535, got: {config.server.port}",
                        details={'server_port': config.server.port}
                    )

            # Validate logging configuration
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if config.logging.level.upper() not in valid_levels:
                raise ConfigurationError(
                    f"Invalid log level '{config.logging.level}'. Must be one of: {', '.join(valid_levels)}",
                    details={'log_level': config.logging.level, 'valid_levels': list(valid_levels)}
                )

            # Validate snapshot configuration if snapshot_dir is specified
            if hasattr(config, 'snapshot_size') and config.snapshot_size is not None:
                if not isinstance(config.snapshot_size, int) or config.snapshot_size <= 0:
                    raise ConfigurationError(
                        f"Snapshot size must be a positive integer, got: {config.snapshot_size}",
                        details={'snapshot_size': config.snapshot_size}
                    )

            # Validate policy allowlist if specified
            if hasattr(config, 'policy_allowlist') and config.policy_allowlist is not None:
                if not isinstance(config.policy_allowlist, list):
                    raise ConfigurationError(
                        f"Policy allowlist must be a list of strings, got: {type(config.policy_allowlist)}",
                        details={'policy_allowlist': config.policy_allowlist}
                    )
                for pattern in config.policy_allowlist:
                    if not isinstance(pattern, str):
                        raise ConfigurationError(
                            f"Policy allowlist items must be strings, got: {type(pattern)} in {pattern}",
                            details={'policy_allowlist': config.policy_allowlist}
                        )

            return config

        except FileNotFoundError as e:
            raise ConfigurationError(
                f"Configuration file not found: {cfg_path}",
                details={'config_path': str(cfg_path), 'error': str(e)}
            ) from e
        except PermissionError as e:
            raise ConfigurationError(
                f"Permission denied reading configuration file: {cfg_path}",
                details={'config_path': str(cfg_path), 'error': str(e)}
            ) from e
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to load configuration from {cfg_path}: {e}",
                details={'config_path': str(cfg_path), 'error_type': type(e).__name__}
            ) from e

    def _format_memory(self, bytes_value: int) -> str:
        """Format memory size for logging."""
        if bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f}KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f}MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f}GB"

    def __init__(self, cfg_path: str | Path = "./hydramind.yaml"):
        """
        Initialize HydraMind Brain with comprehensive error handling.
        
        Args:
            cfg_path: Path to configuration file

        Raises:
            ConfigurationError: If configuration is invalid
            HydraMindError: If initialization fails
        """
        self._shutdown_requested = False
        self._modules: Dict[ModuleName, Module] = {}
        self._system_info = get_system_info()

        try:
            # Load configuration with validation
            self.cfg = self._load_configuration(cfg_path)
            logger.info(f"Configuration loaded from {cfg_path}")

            # Setup logging and metrics
            self.metrics = setup_logging(
                self.cfg.logging.level,
                self.cfg.logging.json,
                self.cfg.logging.file_path,
                self.cfg.logging.rotate_bytes,
                self.cfg.logging.backups
            )

            # Log system information
            logger.info("=" * 60)
            logger.info("HydraMind v1.0 - Universal Cognitive Kernel")
            logger.info("=" * 60)
            logger.info(f"System: {self._system_info['platform']}")
            logger.info(f"Python: {self._system_info['python_version']}")
            logger.info(f"CPUs: {self._system_info['cpu_count']}")
            logger.info(f"Memory: {self._format_memory(self._system_info['memory_total'])}")

            # Initialize core components
            self._initialize_core_components()

        except Exception as e:
            raise HydraMindError(
                f"Failed to initialize HydraMind Brain: {e}",
                code="BRAIN_INIT_FAILED",
                details={'config_path': str(cfg_path)}
            ) from e

    def _initialize_core_components(self) -> None:
        """Initialize core HydraMind components with comprehensive error handling."""
        try:
            # Initialize event store
            self.event_store = EventStore(self.cfg.event_db)
            logger.info(f"Event store initialized: {self.cfg.event_db}")

            # Initialize event bus
            self.bus = EventBus(self.event_store)
            logger.info("Event bus initialized")

            # Initialize execution layer
            hint = ResourceManager().recommend()
            self.exec = Exec(hint)
            logger.info(f"Execution layer initialized: {hint}")

            # Initialize policy guard
            self.policy = PolicyGuard(
                self.cfg.policy_allowlist,
                self.cfg.max_events_per_sec
            )
            logger.info("Policy guard initialized")

            # Initialize data layer
            Path(self.cfg.snapshot_dir).mkdir(exist_ok=True, parents=True)

            self.ring = RingBuffer(
                self.cfg.ring_name,
                capacity=self.cfg.ring_capacity,
                item_bytes=self.cfg.ring_item_bytes
            )
            logger.info(f"Ring buffer initialized: {self.ring.get_stats()}")

            # Use configurable snapshot size from configuration with proper validation
            snapshot_size = getattr(self.cfg, 'snapshot_size', 2_097_152)  # Default 2MB if not specified
            self.snap = MMapSnapshot(
                Path(self.cfg.snapshot_dir) / "telemetry.mmap",
                size=snapshot_size
            )
            logger.info("Memory-mapped snapshot initialized")

            self.cache = TTLCache(default_ttl=1.0)
            logger.info("TTL cache initialized")

        except Exception as e:
            raise HydraMindError(
                f"Failed to initialize core components: {e}",
                code="CORE_INIT_FAILED",
                details={'component': 'core'}
            ) from e

        # Initialize module registry
        self.registry = Registry(self.bus)
        
        # Initialize FastAPI app (if enabled and available)
        self.app = None
        if self.cfg.server.enabled:
            self.app = build_app(self)
            if self.app:
                logger.info(
                    f"FastAPI control plane ready on "
                    f"{self.cfg.server.host}:{self.cfg.server.port}"
                )
        
        # Shutdown flag
        self._shutdown_requested = False
        
        logger.info("HydraMind Brain initialized successfully")
    
    @measure_async_time
    async def start(self) -> None:
        """
        Start all HydraMind components with comprehensive error handling.
        
        Override this in subclasses to add your own modules.

        Raises:
            HydraMindError: If startup fails
        """
        logger.info("Starting HydraMind components...")
        
        try:
            # Start event bus
            self.bus.start()

            # Initialize and register modules
            await self._initialize_modules()

            # Start all modules with timeout protection
            await self._start_modules()

            logger.info(f"HydraMind started successfully with {len(self._modules)} modules")

        except Exception as e:
            logger.error(f"Failed to start HydraMind: {e}")
            # Attempt cleanup on failure
            try:
                await self._emergency_shutdown()
            except Exception as cleanup_error:
                logger.error(f"Emergency shutdown also failed: {cleanup_error}")

            raise HydraMindError(
                f"HydraMind startup failed: {e}",
                code="STARTUP_FAILED",
                details={'error': str(e)}
            ) from e
        
    async def _initialize_modules(self) -> None:
        """Initialize and register all modules based on configuration."""
        # Core modules (always enabled)
        core_modules = self._create_core_modules()

        # Domain modules (based on feature flags)
        domain_modules = self._create_domain_modules()

        # Intelligence modules (based on feature flags)
        intelligence_modules = self._create_intelligence_modules()

        # Combine all modules
        all_modules = core_modules + domain_modules + intelligence_modules

        # Register all modules
        for module, subscriptions in all_modules:
            self._register_module(module, subscriptions)

        logger.info(f"Initialized {len(all_modules)} modules for registration")

    def _create_core_modules(self) -> List[tuple]:
        """Create core modules that are always enabled."""
        # Import modules lazily to avoid circular imports
        SensorHub = _import_domain_modules()[0]
        if SensorHub is None:
            logger.warning("SensorHub module not available, skipping core module creation")
            return []

        return [
            (DAG(self.bus, self.exec, self.policy), ["dag/run"]),
            (Health(self.bus, self.exec, self.policy, interval=0.5), []),
            (SensorHub(
                self.bus, self.exec, self.policy,
                self.ring, self.snap, self.cache
            ), ["sensors/get_last", "sensors/get_snapshot"])
        ]

    def _create_domain_modules(self) -> List[tuple]:
        """Create domain-specific modules based on feature flags."""
        modules = []

        # Import modules lazily to avoid circular imports
        _, DroneFleet, RoboticsCell, TradingEngine, DBAnalyzer = _import_domain_modules()

        if self.cfg.features.drones and DroneFleet:
            modules.append((DroneFleet(self.bus, self.exec, self.policy), ["drone/command"]))

        if self.cfg.features.robots and RoboticsCell:
            modules.append((RoboticsCell(self.bus, self.exec, self.policy), ["robotics/job"]))

        if self.cfg.features.trading and TradingEngine:
            modules.append((TradingEngine(self.bus, self.exec, self.policy), ["trade/op"]))

        if self.cfg.features.db and DBAnalyzer:
            modules.append((
                DBAnalyzer(
                    self.bus, self.exec, self.policy,
                    db_url="sqlite:///hydramind_demo.db"
                ),
                ["db/query", "db/tune"]
            ))

        return modules

    def _create_intelligence_modules(self) -> List[tuple]:
        """Create intelligence modules based on feature flags."""
        modules = []

        # Import modules lazily to avoid circular imports
        SeedOptimizer, ReplayService, AnomalyLab, OptimizerSuite, MetaPlanner = _import_intelligence_modules()

        if self.cfg.features.seed and SeedOptimizer:
            modules.append((SeedOptimizer(self.bus, self.exec, self.policy), ["learn/seed/*"]))

        if self.cfg.features.replay and ReplayService:
            modules.append((ReplayService(self.bus, self.exec, self.policy), ["replay/*"]))

        if self.cfg.features.anomaly and AnomalyLab:
            modules.append((AnomalyLab(self.bus, self.exec, self.policy), ["telemetry/host", "telemetry/*"]))

        if self.cfg.features.optimizer and OptimizerSuite:
            modules.append((OptimizerSuite(self.bus, self.exec, self.policy), [
                "telemetry/host",
                "optimizer/set_goal",
                "optimizer/get_score"
            ]))

        if self.cfg.features.meta_planner and MetaPlanner:
            modules.append((MetaPlanner(self.bus, self.exec, self.policy), ["meta/*"]))

        return modules

    def _register_module(self, module: Module, subscriptions: List[str]) -> None:
        """Register a module with the registry."""
        try:
            self.registry.add(module, subscriptions)
            self._modules[module.name] = module
            logger.debug(f"Registered module '{module.name}' with {len(subscriptions)} subscriptions")
        except Exception as e:
            logger.error(f"Failed to register module '{module.name}': {e}")
            raise ModuleError(
                f"Module registration failed: {e}",
                details={'module': module.name, 'subscriptions': subscriptions}
            ) from e
        
    async def _start_modules(self) -> None:
        """Start all registered modules with timeout protection."""
        if not self._modules:
            logger.warning("No modules to start")
            return

        # Setup example DAG tasks (only if DAG module exists)
        dag_module = self._modules.get("dag")
        if dag_module:
            await self._setup_example_tasks(dag_module)

        # Start all modules with individual error handling
        started_count = 0
        failed_modules = []

        for name, module in self._modules.items():
            try:
                await retry_async(
                    lambda: module.start(),
                    max_attempts=3,
                    delay=1.0,
                    exceptions=(Exception,)
                )
                started_count += 1
                logger.debug(f"Started module '{name}'")

            except Exception as e:
                failed_modules.append((name, str(e)))
                logger.error(f"Failed to start module '{name}': {e}")

        if failed_modules:
            raise ModuleError(
                f"Failed to start {len(failed_modules)} modules: {failed_modules}",
                details={'failed_modules': failed_modules}
            )

        logger.info(f"Successfully started {started_count} modules")

        # Trigger initial DAG execution (if DAG module exists)
        if dag_module:
            await self._trigger_initial_execution()
        
        # Start demo activity loop
        asyncio.create_task(self._demo_loop())
        
        logger.info("HydraMind is now running!")
        logger.info("Press Ctrl+C to shutdown gracefully")
    
    async def _setup_example_tasks(self, dag_module: Module) -> None:
        """Setup example DAG tasks for demonstration."""
        try:
            # This would need to be implemented in the DAG module
            # For now, just log that we're setting up tasks
            logger.debug("Setting up example DAG tasks")
        except Exception as e:
            logger.warning(f"Failed to setup example tasks: {e}")

    async def _trigger_initial_execution(self) -> None:
        """Trigger initial DAG execution."""
        try:
            await self.bus.publish(Message("dag/run", {"tasks": ["sense", "plan", "act"]}))
            logger.debug("Triggered initial DAG execution")
        except Exception as e:
            logger.warning(f"Failed to trigger initial execution: {e}")
    
    async def _demo_loop(self) -> None:
        """
        Example activity loop.
        
        DELETE THIS in your implementation - just shows the event patterns.
        """
        i = 0
        while not self._shutdown_requested:
            try:
                # Example: Trigger various domain activities
                if i % 50 == 0 and self.cfg.features.drones:
                    await self.bus.publish(Message("drone/command", {
                        "drone_id": f"d-{i % 10}",
                        "action": "hold"
                    }))
                
                if i % 60 == 0 and self.cfg.features.robots:
                    await self.bus.publish(Message("robotics/job", {
                        "job_id": f"pick-{i}",
                        "type": "pick"
                    }))
                
                if i % 100 == 0 and self.cfg.features.trading:
                    await self.bus.publish(Message("trade/op", {
                        "symbol": "DEMO",
                        "buy": 100.0,
                        "sell": 100.2
                    }))
                
                if i % 200 == 0:
                    # Request sensor snapshot
                    await self.bus.publish(Message("sensors/get_last", {}))
                    
                    # Request meta planner decision
                    if self.cfg.features.meta_planner:
                        await self.bus.publish(Message("meta/choose_plan", {}))
                
                i += 1
                await asyncio.sleep(0.02)
                
            except Exception as e:
                logger.error(f"Demo loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _emergency_shutdown(self) -> None:
        """Emergency shutdown for failed startup."""
        logger.warning("Performing emergency shutdown...")

        # Stop event bus
        if hasattr(self, 'bus'):
            try:
                self.bus.stop()
                await self.bus.wait_until_stopped()
            except Exception as e:
                logger.error(f"Failed to stop event bus: {e}")

        # Stop any started modules
        for name, module in list(self._modules.items()):
            try:
                if module.state == ModuleState.RUNNING:
                    await module.stop()
            except Exception as e:
                logger.error(f"Failed to stop module '{name}': {e}")
    
    async def stop(self) -> None:
        """Stop all HydraMind components with graceful shutdown."""
        logger.info("Shutting down HydraMind...")
        
        self._shutdown_requested = True
        
        # Stop all modules
        stopped_count = 0
        for name, module in self._modules.items():
            try:
                await module.stop()
                stopped_count += 1
            except Exception as e:
                logger.error(f"Error stopping module {name}: {e}")
        
        # Stop event bus
        self.bus.stop()
        await self.bus.wait_until_stopped()
        
        # Shutdown execution pools
        self.exec.shutdown(wait=True)
        
        # Close data layer
        self.ring.close()
        self.snap.close()
        
        # Close event store
        self.event_store.close()
        
        logger.info(f"HydraMind shutdown complete ({stopped_count} modules stopped)")
    
    
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown on signals."""
        def signal_handler(sig: int, frame: Any) -> None:
            logger.info(f"Received signal {sig}, initiating shutdown...")
            self._shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main(cfg_path: str = "./hydramind.yaml") -> None:
    """
    Main entry point for HydraMind.
    
    Args:
        cfg_path: Path to configuration file
    """
    brain = HydraBrain(cfg_path)
    brain._setup_signal_handlers()
    
    try:
        await brain.start()
        
        # If FastAPI control plane is enabled, run it
        if brain.app is not None:
            try:
                import uvicorn
                
                # Run FastAPI in background
                config = uvicorn.Config(
                    brain.app,
                    host=brain.cfg.server.host,
                    port=brain.cfg.server.port,
                    log_level="info"
                )
                server = uvicorn.Server(config)
                
                # Run until shutdown
                await server.serve()
                
            except ImportError:
                logger.warning("uvicorn not installed, control plane disabled")
                # Just run indefinitely
                while not brain._shutdown_requested:
                    await asyncio.sleep(1)
        else:
            # No control plane, just run indefinitely
            while not brain._shutdown_requested:
                await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    
    finally:
        await brain.stop()


if __name__ == "__main__":
    # Entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="HydraMind Cognitive Kernel")
    parser.add_argument(
        "--config",
        default="./hydramind.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.config))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Failed to start: {e}", exc_info=True)
        sys.exit(1)
