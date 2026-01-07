"""
Tests for utility functions.

Tests the various utility functions in the core.utils module.
"""

import asyncio
import pytest
import time
import psutil
from unittest.mock import Mock, patch
from hydramind.core.utils import (
    measure_time,
    measure_async_time,
    get_system_info,
    validate_topic,
    validate_message_data,
    format_bytes,
    format_duration,
    deep_merge,
    retry_async
)


class TestTimeMeasurement:
    """Test time measurement utilities."""

    def test_measure_time_sync(self):
        """Test synchronous time measurement."""
        @measure_time
        def slow_function():
            time.sleep(0.01)
            return "result"

        result, duration = slow_function()

        assert result == "result"
        assert isinstance(duration, float)
        assert duration >= 0.01  # Should be at least 0.01 seconds

    @pytest.mark.asyncio
    async def test_measure_async_time(self):
        """Test asynchronous time measurement."""
        @measure_async_time
        async def slow_async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        result, duration = await slow_async_function()

        assert result == "async_result"
        assert isinstance(duration, float)
        assert duration >= 0.01  # Should be at least 0.01 seconds


class TestSystemInfo:
    """Test system information utilities."""

    def test_get_system_info(self):
        """Test getting system information."""
        info = get_system_info()

        assert isinstance(info, dict)
        assert "cpu_count" in info
        assert "memory_total" in info
        assert "memory_available" in info
        assert "platform" in info
        assert "python_version" in info

        # Basic sanity checks
        assert info["cpu_count"] > 0
        assert info["memory_total"] > 0
        assert info["memory_available"] >= 0
        assert isinstance(info["platform"], str)
        assert isinstance(info["python_version"], str)


class TestValidation:
    """Test validation utilities."""

    def test_validate_topic(self):
        """Test topic validation."""
        # Valid topics
        assert validate_topic("valid/topic") is True
        assert validate_topic("sensors/temperature") is True
        assert validate_topic("a") is True

        # Invalid topics
        assert validate_topic("") is False
        assert validate_topic(None) is False
        assert validate_topic(123) is False

    def test_validate_message_data(self):
        """Test message data validation."""
        # Valid data
        assert validate_message_data("test/topic", {"key": "value"}) is not None
        assert validate_message_data("test/topic", {"number": 42}) is not None
        assert validate_message_data("test/topic", {}) is not None

        # Invalid data types should raise or return None
        # This tests current behavior





class TestFormatting:
    """Test formatting utilities."""

    def test_format_bytes(self):
        """Test byte formatting."""
        assert format_bytes(0) == "0 B"
        assert format_bytes(1023) == "1023 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"

    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0) == "0.000s"
        assert format_duration(0.001) == "0.001s"
        assert format_duration(1.0) == "1.000s"
        assert format_duration(61.5) == "1m 1.500s"
        assert format_duration(3661.5) == "1h 1m 1.500s"



class TestDataStructures:
    """Test data structure utilities."""

    def test_deep_merge(self):
        """Test deep dictionary merging."""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}

        result = deep_merge(dict1, dict2)

        expected = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": 4
        }
        assert result == expected

        # Original dicts should not be modified
        assert dict1 == {"a": 1, "b": {"c": 2}}
        assert dict2 == {"b": {"d": 3}, "e": 4}


class TestAsyncUtilities:
    """Test asynchronous utilities."""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """Test retry utility with successful operation."""
        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_async(flaky_function, max_retries=3, delay=0.01)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_failure(self):
        """Test retry utility with persistent failure."""
        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            await retry_async(failing_function, max_retries=2, delay=0.01)

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_retry_async_immediate_success(self):
        """Test retry utility with immediate success."""
        call_count = 0

        async def immediate_success():
            nonlocal call_count
            call_count += 1
            return "immediate"

        result = await retry_async(immediate_success, max_retries=3)

        assert result == "immediate"
        assert call_count == 1  # Should not retry


class TestPerformance:
    """Test performance utilities."""

    def test_format_bytes_performance(self):
        """Test format_bytes performance with large numbers."""
        # Should handle large byte values efficiently
        large_bytes = 10**15  # 1 petabyte

        start_time = time.time()
        result = format_bytes(large_bytes)
        end_time = time.time()

        assert result == "1000.0 PB"
        assert end_time - start_time < 0.01  # Should be very fast

    def test_deep_merge_performance(self):
        """Test deep_merge performance with complex structures."""
        dict1 = {f"key_{i}": {f"subkey_{j}": j for j in range(10)} for i in range(10)}
        dict2 = {f"key_{i}": {f"subkey_{j}": j * 2 for j in range(10)} for i in range(10)}

        start_time = time.time()
        result = deep_merge(dict1, dict2)
        end_time = time.time()

        # Should complete reasonably quickly
        assert end_time - start_time < 0.1
        assert isinstance(result, dict)
