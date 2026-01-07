"""
Tests for core module functionality.

Tests the base Module class and its lifecycle management.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from hydramind.core.module import Module, ModuleState, ModuleHealth
from hydramind.core.bus import EventBus, Message
from hydramind.core.execs import Exec
from hydramind.core.policy import PolicyGuard
from hydramind.core.exceptions import ModuleLifecycleError


class MockModule(Module):
    """Test implementation of Module for testing."""

    name = "test_module"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_called = False
        self.stop_called = False
        self.message_count = 0
        self._running = False

    async def _initialize(self):
        """Test initialization."""
        self.start_called = True

    async def _cleanup(self):
        """Test cleanup."""
        self.stop_called = True

    async def _handle_message(self, msg: Message):
        """Test message handling."""
        self.message_count += 1


class TestModuleBase:
    """Base test class for module tests."""

    @pytest.fixture
    def test_module(self, event_bus, exec_engine, policy_guard):
        """Create a test module instance."""
        return MockModule(event_bus, exec_engine, policy_guard)


class TestModuleLifecycle(TestModuleBase):
    """Test module lifecycle management."""

    @pytest.mark.asyncio
    async def test_module_initialization(self, test_module):
        """Test that module initializes correctly."""
        assert test_module.state == ModuleState.UNINITIALIZED
        assert test_module.name == "test_module"
        assert test_module._start_time is None
        assert test_module._stop_time is None

    @pytest.mark.asyncio
    async def test_module_start(self, test_module):
        """Test module start lifecycle."""
        await test_module.start()

        assert test_module.state == ModuleState.RUNNING
        assert test_module.start_called
        assert test_module._start_time is not None

    @pytest.mark.asyncio
    async def test_module_start_already_started(self, test_module):
        """Test that starting an already started module raises error."""
        await test_module.start()

        with pytest.raises(ModuleLifecycleError):
            await test_module.start()

    @pytest.mark.asyncio
    async def test_module_stop(self, test_module):
        """Test module stop lifecycle."""
        await test_module.start()
        await test_module.stop()

        assert test_module.state == ModuleState.STOPPED
        assert test_module.stop_called
        assert test_module._stop_time is not None

    @pytest.mark.asyncio
    async def test_module_stop_already_stopped(self, test_module):
        """Test that stopping an already stopped module is safe."""
        # Should not raise an error
        await test_module.stop()
        assert test_module.state == ModuleState.STOPPED


class TestModuleMessaging(TestModuleBase):
    """Test module messaging functionality."""

    @pytest.mark.asyncio
    async def test_module_message_handling(self, test_module):
        """Test that module handles messages correctly."""
        await test_module.start()

        # Create a test message
        msg = Message("test/topic", {"key": "value"})

        # Handle the message
        await test_module.on_message(msg)

        assert test_module.message_count == 1
        assert test_module._message_count == 1

    @pytest.mark.asyncio
    async def test_module_emit(self, test_module):
        """Test that module can emit messages."""
        await test_module.start()

        # Mock the bus publish method
        test_module.bus.publish = AsyncMock()

        # Emit a message
        result = await test_module.emit("test/topic", {"key": "value"})

        assert result is True
        test_module.bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_module_emit_validation(self, test_module):
        """Test input validation in emit method."""
        await test_module.start()

        # Test invalid topic
        with pytest.raises(ValueError, match="Topic must be a non-empty string"):
            await test_module.emit("", {"key": "value"})

        # Test invalid data type
        with pytest.raises(ValueError, match="Data must be a dictionary"):
            await test_module.emit("test/topic", "invalid_data")

        # Test invalid QoS
        with pytest.raises(ValueError, match="QoS must be 0 or 1"):
            await test_module.emit("test/topic", {"key": "value"}, qos=2)

        # Test invalid key type
        with pytest.raises(ValueError, match="Key must be a string or None"):
            await test_module.emit("test/topic", {"key": "value"}, key=123)


class TestModuleHealth(TestModuleBase):
    """Test module health monitoring."""

    @pytest.mark.asyncio
    async def test_module_health(self, test_module):
        """Test module health reporting."""
        await test_module.start()

        health = test_module.get_health()

        assert isinstance(health, ModuleHealth)
        assert health.state == ModuleState.RUNNING
        assert health.uptime >= 0
        assert health.message_count == 0
        assert health.error_count == 0
        assert 0.0 <= health.health_score <= 1.0

    @pytest.mark.asyncio
    async def test_module_stats(self, test_module):
        """Test module statistics."""
        await test_module.start()

        stats = test_module.get_stats()

        assert isinstance(stats, dict)
        assert stats["name"] == "test_module"
        assert "messages_handled" in stats
        assert "errors" in stats


class TestModuleErrors(TestModuleBase):
    """Test module error handling."""

    @pytest.mark.asyncio
    async def test_module_message_error_handling(self, test_module):
        """Test that message errors are handled gracefully."""
        await test_module.start()

        # Create a module that raises an error
        class ErrorModule(Module):
            name = "error_module"

            async def _handle_message(self, msg: Message):
                raise ValueError("Test error")

        error_module = ErrorModule(test_module.bus, test_module.exec, test_module.policy)
        await error_module.start()

        # Send a message that will cause an error
        msg = Message("test/topic", {"key": "value"})
        await error_module.on_message(msg)

        # Check that error was counted
        assert error_module._error_count == 1
        assert error_module._last_error == "Test error"


if __name__ == "__main__":
    pytest.main([__file__])
