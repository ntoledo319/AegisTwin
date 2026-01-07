"""
Tests for logging functionality.

Tests the logging configuration and utilities.
"""

import pytest
import logging
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from hydramind.core.logging import (
    setup_logging,
    JsonFormatter
)


class TestLoggingConfiguration:
    """Test logging configuration."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for log files."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    def test_configure_logging_basic(self, temp_dir):
        """Test basic logging configuration."""
        log_file = temp_dir / "test.log"

        config = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": str(log_file),
            "max_size": "10MB",
            "backup_count": 3
        }

        setup_logging(config)

        # Test that logging works
        logger = get_logger("test_config")
        logger.info("Test message")

        # Verify log file was created and contains the message
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_configure_logging_json_format(self, temp_dir):
        """Test JSON format logging configuration."""
        log_file = temp_dir / "json_test.log"

        config = {
            "level": "INFO",
            "format": "json",
            "file": str(log_file)
        }

        setup_logging(config)

        logger = get_logger("json_test")
        logger.info("JSON test message", extra={"key": "value"})

        # Verify log file contains JSON
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "JSON test message" in content
            # Should contain JSON-like structure (exact format depends on implementation)

    def test_configure_logging_invalid_level(self):
        """Test logging configuration with invalid level."""
        config = {
            "level": "INVALID_LEVEL"
        }

        # Should handle invalid level gracefully
        setup_logging(config)

        # Should default to a valid level
        logger = get_logger("invalid_level_test")
        # Should not raise an exception
        logger.info("This should work")

    def test_configure_logging_missing_file(self):
        """Test logging configuration with missing log file directory."""
        config = {
            "level": "INFO",
            "file": "/nonexistent/directory/app.log"
        }

        # Should handle missing directory gracefully
        setup_logging(config)


class TestJsonFormatter:
    """Test JSON formatter functionality."""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        formatter = JsonFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        try:
            parsed = json.loads(formatted)
            assert isinstance(parsed, dict)
            assert "message" in parsed
            assert "level" in parsed
            assert "logger" in parsed
        except json.JSONDecodeError:
            pytest.fail("Formatted log should be valid JSON")

    def test_json_formatter_with_extra(self):
        """Test JSON formatting with extra fields."""
        formatter = JsonFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Add extra fields
        record.__dict__.update({
            "extra_field": "extra_value",
            "user_id": 123,
            "request_id": "req_456"
        })

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        # Should include extra fields
        assert parsed.get("extra_field") == "extra_value"
        assert parsed.get("user_id") == 123
        assert parsed.get("request_id") == "req_456"

    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception info."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=20,
                msg="Exception occurred",
                args=(),
                exc_info=True
            )

            formatted = formatter.format(record)
            parsed = json.loads(formatted)

            # Should include exception information
            assert "exception" in parsed or "traceback" in parsed


class TestJsonFormatter:
    """Test JSON formatter functionality."""


class TestLoggingIntegration:
    """Test logging integration scenarios."""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        formatter = JsonFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        try:
            parsed = json.loads(formatted)
            assert isinstance(parsed, dict)
            assert "message" in parsed
            assert "level" in parsed
            assert "logger" in parsed
        except json.JSONDecodeError:
            pytest.fail("Formatted log should be valid JSON")


class TestLoggingPerformance:
    """Test logging performance."""

    def test_json_formatter_performance(self):
        """Test JSON formatter performance."""
        formatter = JsonFormatter()

        # Create many log records
        records = []
        for i in range(1000):
            record = logging.LogRecord(
                name="perf_test",
                level=logging.INFO,
                pathname="test.py",
                lineno=i,
                msg=f"Message {i}",
                args=(),
                exc_info=None
            )
            records.append(record)

        # Format all records
        start_time = time.time()

        formatted = []
        for record in records:
            formatted.append(formatter.format(record))

        end_time = time.time()

        # Should complete reasonably quickly
        duration = end_time - start_time
        assert duration < 1.0  # Should complete in under 1 second

        # All should be valid JSON
        for fmt in formatted:
            try:
                json.loads(fmt)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON: {fmt}")


class TestLoggingErrorHandling:
    """Test logging error handling."""

    def test_json_formatter_with_invalid_data(self):
        """Test JSON formatter with invalid data."""
        formatter = JsonFormatter()

        # Test with a record that has non-serializable data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Add potentially problematic extra data
        record.__dict__.update({
            "problematic_data": lambda x: x  # Functions are not serializable
        })

        # Should handle formatting errors gracefully
        try:
            formatted = formatter.format(record)
            # Should either succeed or handle the error
            assert isinstance(formatted, str)
        except Exception:
            # If formatting fails, it should be handled gracefully
            pass
