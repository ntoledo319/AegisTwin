"""
Tests for main entry points.

Tests the main entry point functions and CLI behavior.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hydramind.brain import main
from hydramind.core.exceptions import HydraMindError, ConfigurationError


class TestMainFunction:
    """Test main entry point function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def test_config(self, temp_dir):
        """Create a test configuration file."""
        config_file = temp_dir / "test_config.yaml"

        config_content = """
server:
  enabled: false
  host: "localhost"
  port: 8080

logging:
  level: "INFO"
  json: true

ring_capacity: 2048
ring_item_bytes: 1024
max_events_per_sec: 1000
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.mark.asyncio
    async def test_main_with_valid_config(self, test_config):
        """Test main function with valid configuration."""
        # Mock the brain's run loop to exit quickly
        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('asyncio.sleep', side_effect=asyncio.CancelledError()):

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = None  # No FastAPI app
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            mock_brain_class.return_value = mock_brain

            # Run main function briefly
            with pytest.raises(asyncio.CancelledError):
                await main(str(test_config))

            # Should have started and stopped the brain
            mock_brain.start.assert_called_once()
            mock_brain.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_server_enabled(self, test_config):
        """Test main function with server enabled."""
        # Modify config to enable server
        with open(test_config, 'r') as f:
            content = f.read()
        content = content.replace("enabled: false", "enabled: true")

        with open(test_config, 'w') as f:
            f.write(content)

        # Mock FastAPI and uvicorn
        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('uvicorn.Server') as mock_server_class, \
             patch('uvicorn.Config') as mock_config_class:

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = Mock()  # FastAPI app enabled
            mock_brain.cfg.server.host = "localhost"
            mock_brain.cfg.server.port = 8080
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            # Create mock server
            mock_server = AsyncMock()
            mock_server.serve = AsyncMock(side_effect=asyncio.CancelledError())
            mock_server_class.return_value = mock_server

            mock_brain_class.return_value = mock_brain

            # Run main function briefly
            with pytest.raises(asyncio.CancelledError):
                await main(str(test_config))

            # Should have created uvicorn server
            mock_config_class.assert_called_once()
            mock_server_class.assert_called_once()
            mock_server.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self, test_config):
        """Test main function with keyboard interrupt."""
        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('asyncio.sleep', side_effect=KeyboardInterrupt()):

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = None
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            mock_brain_class.return_value = mock_brain

            # Run main function
            await main(str(test_config))

            # Should handle keyboard interrupt gracefully
            mock_brain.start.assert_called_once()
            mock_brain.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_startup_failure(self, temp_dir):
        """Test main function with startup failure."""
        # Create config that will cause startup failure
        bad_config = temp_dir / "bad_config.yaml"
        with open(bad_config, 'w') as f:
            f.write("""
ring_capacity: -1  # Invalid
max_events_per_sec: 0  # Invalid
""")

        # Should raise ConfigurationError during brain creation
        with pytest.raises(ConfigurationError):
            await main(str(bad_config))

    @pytest.mark.asyncio
    async def test_main_with_missing_uvicorn(self, test_config):
        """Test main function when uvicorn is not available."""
        # Modify config to enable server
        with open(test_config, 'r') as f:
            content = f.read()
        content = content.replace("enabled: false", "enabled: true")

        with open(test_config, 'w') as f:
            f.write(content)

        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch.dict('sys.modules', {'uvicorn': None}):

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = Mock()  # FastAPI app enabled
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            # Mock sleep to exit quickly
            with patch('asyncio.sleep', side_effect=asyncio.CancelledError()):
                mock_brain_class.return_value = mock_brain

                # Run main function briefly
                with pytest.raises(asyncio.CancelledError):
                    await main(str(test_config))

                # Should have started and stopped brain
                mock_brain.start.assert_called_once()
                mock_brain.stop.assert_called_once()


class TestEntryPointIntegration:
    """Test entry point integration scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for integration tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def comprehensive_config(self, temp_dir):
        """Create a comprehensive test configuration."""
        config_file = temp_dir / "comprehensive_config.yaml"

        config_content = """
server:
  enabled: true
  host: "localhost"
  port: 8080
  cors: ["*"]

logging:
  level: "INFO"
  json: true
  file_path: "/tmp/hydramind.log"

ring_capacity: 4096
ring_item_bytes: 2048
max_events_per_sec: 2000

features:
  intelligence: true
  domain: true
  infrastructure: true
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.mark.asyncio
    async def test_main_with_full_configuration(self, comprehensive_config):
        """Test main function with full configuration."""
        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('uvicorn.Server') as mock_server_class, \
             patch('uvicorn.Config') as mock_config_class, \
             patch('asyncio.sleep', side_effect=asyncio.CancelledError()):

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = Mock()  # Server enabled
            mock_brain.cfg.server.host = "localhost"
            mock_brain.cfg.server.port = 8080
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            # Create mock server
            mock_server = AsyncMock()
            mock_server.serve = AsyncMock(side_effect=asyncio.CancelledError())
            mock_server_class.return_value = mock_server

            mock_brain_class.return_value = mock_brain

            # Run main function briefly
            with pytest.raises(asyncio.CancelledError):
                await main(str(comprehensive_config))

            # Should have configured uvicorn server
            mock_config_class.assert_called_once()
            config_call = mock_config_class.call_args
            assert config_call[1]['host'] == "localhost"
            assert config_call[1]['port'] == 8080

            mock_server.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_signal_handling(self, test_config):
        """Test signal handling in main function."""
        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('signal.signal') as mock_signal:

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = None
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            mock_brain_class.return_value = mock_brain

            # Mock sleep to exit quickly
            with patch('asyncio.sleep', side_effect=asyncio.CancelledError()):
                # Run main function briefly
                with pytest.raises(asyncio.CancelledError):
                    await main(str(test_config))

                # Should have set up signal handlers
                mock_signal.assert_called()

    @pytest.mark.asyncio
    async def test_main_fatal_error_handling(self, temp_dir):
        """Test fatal error handling in main function."""
        # Create config that will cause a fatal error
        fatal_config = temp_dir / "fatal_config.yaml"
        with open(fatal_config, 'w') as f:
            f.write("""
# This config will cause a fatal error during brain initialization
invalid_yaml_syntax: [
""")

        # Should handle YAML parsing errors gracefully
        with pytest.raises((HydraMindError, Exception)):
            await main(str(fatal_config))


class TestEntryPointPerformance:
    """Test entry point performance."""

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
  level: "WARNING"  # Reduce log noise

ring_capacity: 8192
ring_item_bytes: 2048
max_events_per_sec: 5000
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        return config_file

    @pytest.mark.asyncio
    async def test_main_startup_performance(self, perf_config):
        """Test main function startup performance."""
        import time

        start_time = time.time()

        with patch('hydramind.brain.HydraBrain') as mock_brain_class, \
             patch('asyncio.sleep', side_effect=asyncio.CancelledError()):

            # Create mock brain
            mock_brain = Mock()
            mock_brain.app = None
            mock_brain._shutdown_requested = False
            mock_brain.start = AsyncMock()
            mock_brain.stop = AsyncMock()
            mock_brain._setup_signal_handlers = Mock()

            mock_brain_class.return_value = mock_brain

            # Run main function briefly
            with pytest.raises(asyncio.CancelledError):
                await main(str(perf_config))

            end_time = time.time()

            startup_time = end_time - start_time

            # Startup should be reasonably fast
            assert startup_time < 2.0  # Should start in under 2 seconds


class TestEntryPointErrorScenarios:
    """Test error scenarios in entry point."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for error tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.mark.asyncio
    async def test_main_with_permission_error(self, temp_dir):
        """Test main function with permission errors."""
        # Create config in a directory with no read permission
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir()
        config_file = restricted_dir / "config.yaml"

        with open(config_file, 'w') as f:
            f.write("""
ring_capacity: 2048
max_events_per_sec: 1000
server:
  enabled: false
""")

        # Remove read permission from directory
        restricted_dir.chmod(0o000)

        try:
            # Should handle permission error
            with pytest.raises((ConfigurationError, PermissionError)):
                await main(str(config_file))
        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)

    @pytest.mark.asyncio
    async def test_main_with_invalid_yaml(self, temp_dir):
        """Test main function with invalid YAML."""
        invalid_config = temp_dir / "invalid_config.yaml"

        with open(invalid_config, 'w') as f:
            f.write("""
invalid: yaml: syntax: [
  missing: closing: bracket
""")

        # Should handle YAML parsing errors
        with pytest.raises((HydraMindError, Exception)):
            await main(str(invalid_config))

    @pytest.mark.asyncio
    async def test_main_with_missing_dependencies(self, temp_dir):
        """Test main function with missing dependencies."""
        config_file = temp_dir / "config.yaml"

        with open(config_file, 'w') as f:
            f.write("""
ring_capacity: 2048
max_events_per_sec: 1000
server:
  enabled: false
""")

        # Mock missing dependencies
        with patch.dict('sys.modules', {
            'psutil': None,
            'sqlite3': None
        }):
            # Should handle missing dependencies gracefully
            with pytest.raises((ImportError, HydraMindError)):
                await main(str(config_file))

