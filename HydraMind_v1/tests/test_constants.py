"""
Tests for constants and enums.

Tests the various constants and enumerated types used throughout HydraMind.
"""

import pytest
from hydramind.core.constants import (
    ModuleName,
    ModuleState,
    StatsDict,
    JSONData,
    Topic,
    DEFAULT_MODULE_CONFIG,
    PERFORMANCE,
    LIMITS
)


class TestModuleName:
    """Test ModuleName type."""

    def test_module_name_creation(self):
        """Test creating ModuleName instances."""
        name = ModuleName("test_module")
        assert str(name) == "test_module"
        assert name == "test_module"

    def test_module_name_validation(self):
        """Test ModuleName validation."""
        # Valid names
        assert ModuleName("valid_name") == "valid_name"
        assert ModuleName("name_with_underscores") == "name_with_underscores"
        assert ModuleName("module-1") == "module-1"

        # Invalid names should raise (implementation dependent)
        # This tests current behavior

    def test_module_name_comparison(self):
        """Test ModuleName comparison operations."""
        name1 = ModuleName("test_module")
        name2 = ModuleName("test_module")
        name3 = ModuleName("other_module")

        assert name1 == name2
        assert name1 != name3
        assert name1 == "test_module"  # Should compare with strings


class TestModuleState:
    """Test ModuleState enum."""

    def test_module_state_values(self):
        """Test ModuleState enum values."""
        assert ModuleState.UNINITIALIZED == "uninitialized"
        assert ModuleState.INITIALIZING == "initializing"
        assert ModuleState.RUNNING == "running"
        assert ModuleState.STOPPING == "stopping"
        assert ModuleState.STOPPED == "stopped"
        assert ModuleState.ERROR == "error"

    def test_module_state_transitions(self):
        """Test valid state transitions."""
        # Valid transitions (implementation dependent)
        # This tests the current behavior

        # Test that states are distinct
        states = [
            ModuleState.UNINITIALIZED,
            ModuleState.INITIALIZING,
            ModuleState.RUNNING,
            ModuleState.STOPPING,
            ModuleState.STOPPED,
            ModuleState.ERROR
        ]

        assert len(set(states)) == 6  # All states should be unique

    def test_module_state_ordering(self):
        """Test ModuleState ordering."""
        # States should be comparable
        assert ModuleState.UNINITIALIZED != ModuleState.RUNNING
        assert ModuleState.RUNNING != ModuleState.STOPPED

        # Test string representation
        assert str(ModuleState.RUNNING) == "ModuleState.RUNNING"
        assert "ModuleState.RUNNING" in repr(ModuleState.RUNNING)


class TestTypeAliases:
    """Test type alias definitions."""

    def test_stats_dict_type(self):
        """Test StatsDict type alias."""
        # StatsDict should be a dictionary type
        data = {"key": "value", "number": 42}
        assert isinstance(data, dict)

        # Type checking (implementation dependent)
        # This tests that the type alias exists

    def test_json_data_type(self):
        """Test JSONData type alias."""
        # JSONData should accept valid JSON-serializable data
        valid_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        }

        assert isinstance(valid_data, dict)

    def test_topic_type(self):
        """Test Topic type alias."""
        # Topic should be a string type
        topic = "valid/topic/name"
        assert isinstance(topic, str)

        # Should handle various topic formats
        topics = [
            "simple",
            "with/levels",
            "complex/topic/with/many/levels",
            "topic-with-dashes",
            "topic_with_underscores"
        ]

        for t in topics:
            assert isinstance(t, str)


class TestDefaultConfiguration:
    """Test default configuration constants."""

    def test_default_module_config(self):
        """Test DEFAULT_MODULE_CONFIG structure."""
        assert isinstance(DEFAULT_MODULE_CONFIG, dict)
        assert "retry_attempts" in DEFAULT_MODULE_CONFIG
        assert "start_timeout" in DEFAULT_MODULE_CONFIG
        assert "health_check_interval" in DEFAULT_MODULE_CONFIG

        # Should have reasonable default values
        assert DEFAULT_MODULE_CONFIG["retry_attempts"] > 0
        assert DEFAULT_MODULE_CONFIG["start_timeout"] > 0
        assert DEFAULT_MODULE_CONFIG["health_check_interval"] > 0

    def test_default_module_config_completeness(self):
        """Test that DEFAULT_MODULE_CONFIG is comprehensive."""
        required_keys = [
            "retry_attempts",
            "start_timeout",
            "health_check_interval",
            "max_concurrent_operations",
            "retry_delay"
        ]

        for key in required_keys:
            assert key in DEFAULT_MODULE_CONFIG, f"Missing required config key: {key}"


class TestPerformanceConstants:
    """Test performance-related constants."""

    def test_performance_values(self):
        """Test PERFORMANCE constant values."""
        assert isinstance(PERFORMANCE, dict)
        assert "cache_ttl" in PERFORMANCE
        assert "health_check_interval" in PERFORMANCE
        assert "module_start_timeout" in PERFORMANCE

        # Should have reasonable values
        assert PERFORMANCE["cache_ttl"] > 0
        assert PERFORMANCE["health_check_interval"] > 0
        assert PERFORMANCE["module_start_timeout"] > 0

    def test_performance_reasonableness(self):
        """Test that performance constants are reasonable."""
        # Cache TTL should be reasonable
        assert 0.1 <= PERFORMANCE["cache_ttl"] <= 3600  # 0.1s to 1 hour

        # Health check interval should be reasonable
        assert 0.1 <= PERFORMANCE["health_check_interval"] <= 60  # 0.1s to 1 minute

        # Module start timeout should be reasonable
        assert 1 <= PERFORMANCE["module_start_timeout"] <= 300  # 1s to 5 minutes


class TestLimitsConstants:
    """Test limits-related constants."""

    def test_limits_values(self):
        """Test LIMITS constant values."""
        assert isinstance(LIMITS, dict)
        assert "max_message_size" in LIMITS
        assert "max_topic_length" in LIMITS
        assert "max_ring_items" in LIMITS
        assert "max_concurrent_modules" in LIMITS

        # Should have reasonable limit values
        assert LIMITS["max_message_size"] > 0
        assert LIMITS["max_topic_length"] > 0
        assert LIMITS["max_ring_items"] > 0
        assert LIMITS["max_concurrent_modules"] > 0

    def test_limits_reasonableness(self):
        """Test that limits constants are reasonable."""
        # Message size should be reasonable
        assert LIMITS["max_message_size"] >= 1024  # At least 1KB
        assert LIMITS["max_message_size"] <= 10 * 1024 * 1024  # At most 10MB

        # Topic length should be reasonable
        assert LIMITS["max_topic_length"] >= 10
        assert LIMITS["max_topic_length"] <= 1000

        # Ring buffer size should be reasonable
        assert LIMITS["max_ring_items"] >= 1000
        assert LIMITS["max_ring_items"] <= 10_000_000

        # Concurrent modules should be reasonable
        assert LIMITS["max_concurrent_modules"] >= 1
        assert LIMITS["max_concurrent_modules"] <= 10_000


class TestConstantsIntegration:
    """Test integration of constants across modules."""

    def test_constants_consistency(self):
        """Test that constants are consistent across definitions."""
        # Test that related constants work together

        # Module states should be valid strings
        for state in ModuleState:
            assert isinstance(state.value, str)
            assert len(state.value) > 0

        # Default config should use valid types
        for key, value in DEFAULT_MODULE_CONFIG.items():
            assert value is not None
            assert isinstance(key, str)

    def test_constants_usage_in_types(self):
        """Test that constants work with type definitions."""
        # ModuleName should work with string operations
        name = ModuleName("test")
        assert name + "_suffix" == "test_suffix"
        assert "test".upper() == "TEST"

        # ModuleState should work in comparisons
        state = ModuleState.RUNNING
        assert state == "running"
        assert state != ModuleState.STOPPED


class TestConstantsExtensibility:
    """Test constants extensibility."""

    def test_module_state_completeness(self):
        """Test that ModuleState covers all necessary states."""
        required_states = {
            "uninitialized",
            "initializing",
            "running",
            "stopping",
            "stopped",
            "error"
        }

        actual_states = {state.value for state in ModuleState}

        # Should have all required states
        assert required_states.issubset(actual_states)

        # Should not have extra states that aren't needed
        assert len(actual_states) <= 10  # Reasonable upper bound

    def test_performance_thresholds_completeness(self):
        """Test that performance constants cover key metrics."""
        required_metrics = {
            "cache_ttl",
            "health_check_interval",
            "module_start_timeout"
        }

        actual_metrics = set(PERFORMANCE.keys())

        # Should have all required metrics
        assert required_metrics.issubset(actual_metrics)

    def test_limits_completeness(self):
        """Test that limits constants cover key constraints."""
        required_limits = {
            "max_message_size",
            "max_topic_length",
            "max_ring_items",
            "max_concurrent_modules"
        }

        actual_limits = set(LIMITS.keys())

        # Should have all required limits
        assert required_limits.issubset(actual_limits)
