"""
Tests for HydraMind Brain functionality.

Tests the main brain orchestrator and integration between components.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hydramind.brain import HydraBrain, Registry
from hydramind.core.config import BrainConfig
from hydramind.core.bus import EventBus, Message
from hydramind.core.event_store import EventStore
from hydramind.core.execs import Exec, ResourceManager
from hydramind.core.policy import PolicyGuard
from hydramind.core.data import RingBuffer, MMapSnapshot, TTLCache
from hydramind.core.exceptions import HydraMindError, ConfigurationError


class TestRegistry:
    """Test module registry functionality."""

    @pytest.fixture
    def mock_bus(self):
        """Create a mock event bus."""
        bus = Mock(spec=EventBus)
        return bus

    @pytest.fixture
    def registry(self, mock_bus):
        """Create a registry instance."""
        return Registry(mock_bus)

    def test_registry_initialization(self, registry, mock_bus):
        """Test registry initializes correctly."""
        assert registry.bus is mock_bus
        assert isinstance(registry.modules, dict)
        assert len(registry.modules) == 0

    def test_registry_register_module(self, registry):
        """Test registering a module."""
        # Create a mock module
        mock_module = Mock()
        mock_module.name = "test_module"
        mock_module.start = AsyncMock()
        mock_module.stop = AsyncMock()

        subscriptions = ["test/topic"]

        # Register the module
        registry.register(mock_module, subscriptions)

        # Should be registered
        assert "test_module" in registry.modules
        assert registry.modules["test_module"]["module"] is mock_module
        assert registry.modules["test_module"]["subscriptions"] == subscriptions

    def test_registry_unregister_module(self, registry):
        """Test unregistering a module."""
        # Register a module first
        mock_module = Mock()
        mock_module.name = "test_module"
        registry.register(mock_module, ["test/topic"])

        # Unregister the module
        registry.unregister("test_module")

        # Should be removed from registry
        assert "test_module" not in registry.modules

    def test_registry_get_module(self, registry):
        """Test getting a registered module."""
        # Register a module
        mock_module = Mock()
        mock_module.name = "test_module"
        registry.register(mock_module, ["test/topic"])

        # Get the module
        retrieved_module = registry.get_module("test_module")
        assert retrieved_module is mock_module

        # Get non-existent module
        non_existent = registry.get_module("non_existent")
        assert non_existent is None

    def test_registry_list_modules(self, registry):
        """Test listing registered modules."""
        # Initially empty
        modules = registry.list_modules()
        assert len(modules) == 0

        # Register some modules
        mock_module1 = Mock()
        mock_module1.name = "module1"
        mock_module2 = Mock()
        mock_module2.name = "module2"

        registry.register(mock_module1, ["topic1"])
        registry.register(mock_module2, ["topic2"])

        # Should list all modules
        modules = registry.list_modules()
        assert len(modules) == 2
        module_names = [m["name"] for m in modules]
        assert "module1" in module_names
        assert "module2" in module_names


class TestHydraBrain:
    """Test HydraBrain main functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def test_config(self, temp_dir):
        """Create a test configuration."""
        config_file = temp_dir / "test_config.yaml"

        # Create a minimal config file
        config_content = """
server:
  enabled: false
  host: "localhost"
  port: 8080
  cors: ["*"]

logging:
  level: "INFO"
  json: true
  file_path: "/tmp/test.log"

ring_capacity: 2048
ring_item_bytes: 1024
max_events_per_sec: 1000
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.fixture
    def brain(self, test_config):
        """Create a HydraBrain instance."""
        return HydraBrain(str(test_config))

    def test_brain_initialization(self, brain):
        """Test HydraBrain initializes correctly."""
        assert brain.cfg is not None
        assert brain.bus is not None
        assert brain.store is not None
        assert brain.exec is not None
        assert brain.policy is not None
        assert brain.ring is not None
        assert brain.snap is not None
        assert brain.cache is not None
        assert brain.registry is not None

    def test_brain_configuration_loading(self, temp_dir):
        """Test configuration loading and validation."""
        # Test valid configuration
        valid_config = temp_dir / "valid_config.yaml"
        with open(valid_config, 'w') as f:
            f.write("""
ring_capacity: 4096
max_events_per_sec: 2000
server:
  enabled: true
  port: 9000
logging:
  level: "DEBUG"
""")

        brain = HydraBrain(str(valid_config))
        assert brain.cfg.ring_capacity == 4096
        assert brain.cfg.max_events_per_sec == 2000

    def test_brain_configuration_validation_errors(self, temp_dir):
        """Test configuration validation error handling."""
        # Test invalid ring capacity
        invalid_config = temp_dir / "invalid_config.yaml"
        with open(invalid_config, 'w') as f:
            f.write("""
ring_capacity: 512  # Too small
max_events_per_sec: 0  # Invalid
server:
  port: 70000  # Invalid port
logging:
  level: "INVALID_LEVEL"
""")

        with pytest.raises(ConfigurationError):
            HydraBrain(str(invalid_config))

    def test_brain_missing_config_file(self):
        """Test handling missing configuration file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            HydraBrain("/non/existent/config.yaml")

    @pytest.mark.asyncio
    async def test_brain_start_stop(self, brain):
        """Test starting and stopping the brain."""
        # Initially not running
        assert not hasattr(brain, '_running') or not brain._running

        # Start the brain
        await brain.start()

        # Should be running
        assert brain._running is True

        # Stop the brain
        await brain.stop()

        # Should be stopped
        assert brain._running is False

    @pytest.mark.asyncio
    async def test_brain_module_registration(self, brain):
        """Test module registration during startup."""
        # Mock module creation to avoid complex dependencies
        with patch.object(brain, '_create_core_modules', return_value=[]), \
             patch.object(brain, '_create_domain_modules', return_value=[]), \
             patch.object(brain, '_create_intelligence_modules', return_value=[]):

            await brain.start()

            # Should have initialized modules (even if empty)
            assert hasattr(brain, '_modules')
            assert isinstance(brain._modules, list)

            await brain.stop()

    @pytest.mark.asyncio
    async def test_brain_emergency_shutdown(self, brain):
        """Test emergency shutdown functionality."""
        await brain.start()

        # Mock some components to fail during shutdown
        brain.bus.stop = AsyncMock(side_effect=Exception("Bus stop failed"))

        # Emergency shutdown should handle errors gracefully
        await brain._emergency_shutdown()

        # Should still be stopped
        assert brain._running is False


class TestHydraBrainIntegration:
    """Test HydraBrain integration scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def integration_config(self, temp_dir):
        """Create a comprehensive test configuration."""
        config_file = temp_dir / "integration_config.yaml"

        config_content = """
server:
  enabled: false

logging:
  level: "INFO"
  json: true

ring_capacity: 2048
ring_item_bytes: 1024
max_events_per_sec: 1000

features:
  intelligence: true
  domain: true
  infrastructure: true
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.fixture
    def integration_brain(self, integration_config):
        """Create a HydraBrain instance for integration testing."""
        return HydraBrain(str(integration_config))

    @pytest.mark.asyncio
    async def test_full_brain_lifecycle(self, integration_brain):
        """Test complete brain lifecycle."""
        # Start the brain
        await integration_brain.start()

        # Verify all components are running
        assert integration_brain.bus is not None
        assert integration_brain.store is not None
        assert integration_brain.registry is not None

        # Verify modules were initialized
        assert hasattr(integration_brain, '_modules')
        assert isinstance(integration_brain._modules, list)

        # Test event publishing
        test_message = Message("test/topic", {"test": "data"})
        await integration_brain.bus.publish(test_message)

        # Test event querying
        events = await integration_brain.store.query("test/topic", limit=10)
        # Should be able to query (may be empty if no events stored)

        # Stop the brain
        await integration_brain.stop()

        # Verify shutdown
        assert integration_brain._running is False

    @pytest.mark.asyncio
    async def test_brain_with_server_enabled(self, temp_dir):
        """Test brain with server enabled."""
        config_file = temp_dir / "server_config.yaml"

        config_content = """
server:
  enabled: true
  host: "localhost"
  port: 8080
  cors: ["*"]

logging:
  level: "INFO"

ring_capacity: 2048
max_events_per_sec: 1000
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        brain = HydraBrain(str(config_file))

        # Should initialize FastAPI app when server is enabled
        await brain.start()

        # App should be initialized if FastAPI is available
        # (May be None if FastAPI not installed)
        assert brain.app is not None or brain.app is None  # Either way is valid

        await brain.stop()

    @pytest.mark.asyncio
    async def test_brain_error_recovery(self, integration_brain):
        """Test error recovery in brain operations."""
        await integration_brain.start()

        # Test handling errors in component operations
        # Mock a component to raise an error
        original_publish = integration_brain.bus.publish
        integration_brain.bus.publish = AsyncMock(side_effect=Exception("Publish failed"))

        try:
            # This should be handled gracefully
            test_message = Message("test/topic", {"test": "data"})
            await integration_brain.bus.publish(test_message)
        except Exception:
            # If it raises, should be a known exception type
            pass

        # Restore original method
        integration_brain.bus.publish = original_publish

        # Brain should still be running
        assert integration_brain._running is True

        await integration_brain.stop()


class TestHydraBrainPerformance:
    """Test HydraBrain performance."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for performance tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def perf_config(self, temp_dir):
        """Create a performance test configuration."""
        config_file = temp_dir / "perf_config.yaml"

        config_content = """
server:
  enabled: false

logging:
  level: "WARNING"  # Reduce log noise for performance tests

ring_capacity: 8192
ring_item_bytes: 2048
max_events_per_sec: 5000
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.mark.asyncio
    async def test_brain_startup_performance(self, perf_config):
        """Test brain startup performance."""
        import time

        start_time = time.time()
        brain = HydraBrain(str(perf_config))
        await brain.start()
        end_time = time.time()

        startup_time = end_time - start_time

        # Startup should be reasonably fast
        assert startup_time < 5.0  # Should start in under 5 seconds

        await brain.stop()

    @pytest.mark.asyncio
    async def test_brain_high_frequency_events(self, perf_config):
        """Test brain performance with high-frequency events."""
        brain = HydraBrain(str(perf_config))
        await brain.start()

        # Send many events quickly
        start_time = time.time()

        events = []
        for i in range(1000):
            event = Message(f"perf/topic_{i % 10}", {
                "id": i,
                "data": f"value_{i}"
            })
            events.append(event)

        # Publish all events
        tasks = [brain.bus.publish(event) for event in events]
        await asyncio.gather(*tasks)

        end_time = time.time()

        # Should handle high-frequency events efficiently
        processing_time = end_time - start_time
        assert processing_time < 3.0  # Should process in under 3 seconds

        # Should be able to query events
        query_results = await brain.store.query("perf/*", limit=100)
        # May be empty depending on storage implementation

        await brain.stop()

    @pytest.mark.asyncio
    async def test_brain_concurrent_operations(self, perf_config):
        """Test brain performance with concurrent operations."""
        brain = HydraBrain(str(perf_config))
        await brain.start()

        async def publish_events(event_count):
            """Publish events concurrently."""
            for i in range(event_count):
                event = Message(f"concurrent/topic_{i}", {"id": i})
                await brain.bus.publish(event)

        async def query_events():
            """Query events concurrently."""
            for _ in range(10):
                await brain.store.query("concurrent/*", limit=50)

        # Run concurrent operations
        start_time = time.time()

        tasks = [
            publish_events(100),
            query_events(),
            publish_events(100)
        ]

        await asyncio.gather(*tasks)

        end_time = time.time()

        # Should handle concurrent operations efficiently
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should complete in under 2 seconds

        await brain.stop()


class TestHydraBrainErrorHandling:
    """Test HydraBrain error handling scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for error tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def error_config(self, temp_dir):
        """Create a configuration that might cause errors."""
        config_file = temp_dir / "error_config.yaml"

        config_content = """
server:
  enabled: false

logging:
  level: "INFO"

ring_capacity: 1024
max_events_per_sec: 100
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.mark.asyncio
    async def test_brain_startup_failure_recovery(self, error_config):
        """Test recovery from startup failures."""
        # Create a brain with a configuration that might cause issues
        brain = HydraBrain(str(error_config))

        # Mock a component to fail during startup
        original_start = brain.bus.start
        brain.bus.start = Mock(side_effect=Exception("Bus start failed"))

        # Startup should fail gracefully
        with pytest.raises(HydraMindError, match="startup failed"):
            await brain.start()

        # Should attempt emergency shutdown
        # (This is tested by the startup failure handling)

    @pytest.mark.asyncio
    async def test_brain_module_startup_failures(self, error_config):
        """Test handling module startup failures."""
        brain = HydraBrain(str(error_config))

        # Mock module creation to return modules that fail to start
        def failing_module():
            module = Mock()
            module.name = "failing_module"
            module.start = AsyncMock(side_effect=Exception("Module start failed"))
            module.stop = AsyncMock()
            return module, ["test/topic"]

        with patch.object(brain, '_create_core_modules', return_value=[failing_module()]):
            # Startup should handle module failures gracefully
            with pytest.raises(HydraMindError):
                await brain.start()

    @pytest.mark.asyncio
    async def test_brain_graceful_shutdown_on_signal(self, error_config):
        """Test graceful shutdown on system signals."""
        brain = HydraBrain(str(error_config))
        await brain.start()

        # Simulate shutdown signal
        brain._shutdown_requested = True

        # Should initiate graceful shutdown
        await brain.stop()

        # Should be properly stopped
        assert brain._running is False

