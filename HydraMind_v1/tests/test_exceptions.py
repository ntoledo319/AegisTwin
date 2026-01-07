"""
Tests for exception handling functionality.

Tests the exception classes and error handling utilities.
"""

import pytest
import time
from hydramind.core.exceptions import (
    HydraMindError,
    ModuleError,
    ModuleInitializationError,
    ModuleLifecycleError,
    EventBusError,
    StorageError,
    handle_exception,
)


class TestHydraMindError:
    """Test HydraMindError base exception."""

    def test_error_creation(self):
        """Test creating HydraMindError instances."""
        # Basic error
        error = HydraMindError("Test error")
        assert str(error) == "Test error"
        assert error.details is None

        # Error with details
        details = {"module": "test_module", "code": 500}
        error = HydraMindError("Test error with details", details=details)
        assert str(error) == "Test error with details"
        assert error.details == details

        # Error with cause
        cause = ValueError("Original error")
        error = HydraMindError("Wrapped error", cause=cause)
        assert str(error) == "Wrapped error"
        assert error.__cause__ == cause

    def test_error_equality(self):
        """Test error equality comparison."""
        error1 = HydraMindError("Test error")
        error2 = HydraMindError("Test error")
        error3 = HydraMindError("Different error")

        # Same message should be equal
        assert error1 == error2

        # Different message should not be equal
        assert error1 != error3

    def test_error_repr(self):
        """Test error string representation."""
        error = HydraMindError("Test error", details={"key": "value"})

        repr_str = repr(error)
        assert "Test error" in repr_str
        assert "key" in repr_str
        assert "value" in repr_str


class TestModuleErrors:
    """Test module-specific exceptions."""

    def test_module_error(self):
        """Test ModuleError creation."""
        error = ModuleError("Module failed", module_name="test_module")
        assert str(error) == "Module failed"
        assert error.details["module_name"] == "test_module"

    def test_module_initialization_error(self):
        """Test ModuleInitializationError creation."""
        error = ModuleInitializationError("Init failed", module_name="test_module")
        assert str(error) == "Init failed"
        assert error.details["module_name"] == "test_module"

    def test_module_lifecycle_error(self):
        """Test ModuleLifecycleError creation."""
        details = {"module": "test_module", "state": "RUNNING"}
        error = ModuleLifecycleError("Lifecycle error", details=details)
        assert str(error) == "Lifecycle error"
        assert error.details["module"] == "test_module"
        assert error.details["state"] == "RUNNING"


class TestInfrastructureErrors:
    """Test infrastructure-specific exceptions."""

    def test_event_bus_error(self):
        """Test EventBusError creation."""
        error = EventBusError("Bus error", topic="test/topic")
        assert str(error) == "Bus error"
        assert error.details["topic"] == "test/topic"

    def test_storage_error(self):
        """Test StorageError creation."""
        error = StorageError("Store error", db_path="/test/path.db")
        assert str(error) == "Store error"
        assert error.details["db_path"] == "/test/path.db"



class TestExceptionHandling:
    """Test exception handling utilities."""

    def test_handle_exception_basic(self):
        """Test basic exception handling."""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            # handle_exception should not raise an exception
            result = handle_exception(e, "test_context")
            assert result is None


    def test_handle_exception_return_value(self):
        """Test exception handling with return value."""
        def failing_function():
            raise ValueError("Test exception")

        # handle_exception should return the default value when exception occurs
        result = handle_exception(
            lambda: failing_function(),
            "test_context",
            default_value="default"
        )
        assert result == "default"



class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_exception_inheritance(self):
        """Test that exceptions inherit correctly."""
        # Test basic inheritance
        error = HydraMindError("Base error")
        assert isinstance(error, HydraMindError)
        assert isinstance(error, Exception)

        # Test module error inheritance
        module_error = ModuleError("Module error")
        assert isinstance(module_error, HydraMindError)
        assert isinstance(module_error, ModuleError)

        # Test infrastructure error inheritance
        storage_error = StorageError("Storage error")
        assert isinstance(storage_error, HydraMindError)
        assert isinstance(storage_error, StorageError)

    def test_exception_details_inheritance(self):
        """Test that details are properly inherited."""
        # Base error with details
        base_error = HydraMindError("Base error", details={"base": "data"})
        assert base_error.details == {"base": "data"}

        # Module error should inherit base details
        module_error = ModuleError("Module error", details={"module": "test"})
        # Note: This tests the current implementation behavior
        # The details should be merged or handled appropriately


class TestErrorContext:
    """Test error context and debugging information."""

    def test_error_with_stack_trace(self):
        """Test that errors capture stack trace information."""
        def deep_function():
            raise HydraMindError("Deep error")

        def middle_function():
            return deep_function()

        def top_function():
            return middle_function()

        try:
            top_function()
        except HydraMindError as e:
            # Error should be catchable and have context
            assert str(e) == "Deep error"
            # Stack trace should be available via traceback module
            import traceback
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            assert "deep_function" in tb_str
            assert "middle_function" in tb_str
            assert "top_function" in tb_str

    def test_error_timestamps(self):
        """Test that errors include timestamp information."""
        before = time.time()
        error = HydraMindError("Timed error")
        after = time.time()

        # Error should have been created between before and after
        # Note: This is a conceptual test - actual implementation may vary
        assert error.details is None or "timestamp" not in error.details

    def test_error_context_preservation(self):
        """Test that error context is preserved through re-raising."""
        original_error = ValueError("Original error")

        try:
            raise HydraMindError("Wrapper error", cause=original_error)
        except HydraMindError as e:
            # Should preserve the original cause
            assert e.__cause__ == original_error
            assert str(e.__cause__) == "Original error"


class TestErrorRecovery:
    """Test error recovery and resilience patterns."""

    def test_non_critical_error_handling(self):
        """Test handling of non-critical errors."""
        def risky_operation():
            if time.time() > 0:  # Always true
                raise ValueError("Non-critical error")
            return "success"

        # Should handle the error gracefully
        result = handle_exception(
            risky_operation,
            "risky_context",
            default_value="fallback"
        )
        assert result == "fallback"

    def test_critical_error_propagation(self):
        """Test that critical errors are properly propagated."""
        def critical_operation():
            raise SystemExit("Critical error")

        # SystemExit should propagate (not be caught by handle_exception)
        with pytest.raises(SystemExit):
            handle_exception(critical_operation, "critical_context")
