"""
HydraMind Exception Hierarchy

Standardized exception classes for consistent error handling across HydraMind.
Provides specific exceptions for different types of failures and conditions.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, Union


logger = logging.getLogger(__name__)


# =============================================================================
# BASE EXCEPTIONS
# =============================================================================

class HydraMindError(Exception):
    """Base exception for all HydraMind errors"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

        # Log the error
        logger.error(
            f"HydraMind Error [{self.code}]: {message}",
            extra={
                'error_code': self.code,
                'error_details': self.details,
                'error_cause': str(cause) if cause else None
            }
        )


class HydraMindWarning(UserWarning):
    """Base warning for HydraMind conditions"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

        logger.warning(
            f"HydraMind Warning [{self.code}]: {message}",
            extra={
                'warning_code': self.code,
                'warning_details': self.details
            }
        )


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================

class ConfigurationError(HydraMindError):
    """Configuration-related errors"""
    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed"""
    pass


class ConfigFileError(ConfigurationError):
    """Configuration file not found or invalid"""
    pass


class EnvironmentError(ConfigurationError):
    """Environment variable configuration error"""
    pass


# =============================================================================
# MODULE ERRORS
# =============================================================================

class ModuleError(HydraMindError):
    """Module-related errors"""
    pass


class ModuleNotFoundError(ModuleError):
    """Requested module not found"""

    def __init__(self, module_name: str, available_modules: Optional[list] = None):
        message = f"Module '{module_name}' not found"
        if available_modules:
            message += f". Available modules: {', '.join(available_modules)}"

        super().__init__(
            message=message,
            code="MODULE_NOT_FOUND",
            details={'module_name': module_name, 'available_modules': available_modules}
        )
        self.module_name = module_name


class ModuleInitializationError(ModuleError):
    """Module failed to initialize"""
    pass


class ModuleLifecycleError(ModuleError):
    """Module lifecycle operation failed"""
    pass


class ModuleDependencyError(ModuleError):
    """Module dependency resolution failed"""
    pass


# =============================================================================
# EVENT SYSTEM ERRORS
# =============================================================================

class EventSystemError(HydraMindError):
    """Event bus and messaging errors"""
    pass


class EventBusError(EventSystemError):
    """Event bus operation failed"""
    pass


class EventSubscriptionError(EventBusError):
    """Event subscription failed"""
    pass


class EventPublishError(EventBusError):
    """Event publishing failed"""
    pass


class EventQueueError(EventBusError):
    """Event queue operation failed"""
    pass


class MessageValidationError(EventBusError):
    """Event message validation failed"""

    def __init__(
        self,
        topic: str,
        data: Any,
        validation_errors: list
    ):
        message = f"Message validation failed for topic '{topic}'"
        super().__init__(
            message=message,
            code="MESSAGE_VALIDATION_FAILED",
            details={
                'topic': topic,
                'validation_errors': validation_errors,
                'data_type': type(data).__name__
            }
        )
        self.topic = topic
        self.validation_errors = validation_errors


# =============================================================================
# DATA LAYER ERRORS
# =============================================================================

class DataLayerError(HydraMindError):
    """Data storage and caching errors"""
    pass


class StorageError(DataLayerError):
    """Storage operation failed"""
    pass


class RingBufferError(DataLayerError):
    """Ring buffer operation failed"""
    pass


class CacheError(DataLayerError):
    """Cache operation failed"""
    pass


class PersistenceError(StorageError):
    """Data persistence operation failed"""
    pass


# =============================================================================
# EXECUTION ERRORS
# =============================================================================

class ExecutionError(HydraMindError):
    """Execution and resource management errors"""
    pass


class ResourceError(ExecutionError):
    """Resource allocation or management failed"""
    pass


class ThreadPoolError(ExecutionError):
    """Thread pool operation failed"""
    pass


class ProcessPoolError(ExecutionError):
    """Process pool operation failed"""
    pass


class TimeoutError(ExecutionError):
    """Operation timed out"""
    pass


# =============================================================================
# NETWORK/COMMUNICATION ERRORS
# =============================================================================

class NetworkError(HydraMindError):
    """Network and communication errors"""
    pass


class ConnectionError(NetworkError):
    """Connection failed or lost"""
    pass


class ProtocolError(NetworkError):
    """Communication protocol error"""
    pass


class SerializationError(NetworkError):
    """Data serialization/deserialization failed"""
    pass


# =============================================================================
# SYSTEM ERRORS
# =============================================================================

class SystemError(HydraMindError):
    """System-level errors"""
    pass


class ResourceExhaustionError(SystemError):
    """System resource exhausted"""
    pass


class SystemHealthError(SystemError):
    """System health check failed"""
    pass


class SecurityError(SystemError):
    """Security policy violation"""
    pass


# =============================================================================
# LEARNING/OPTIMIZATION ERRORS
# =============================================================================

class LearningError(HydraMindError):
    """Learning and optimization errors"""
    pass


class OptimizationError(LearningError):
    """Optimization operation failed"""
    pass


class ModelError(LearningError):
    """Model operation failed"""
    pass


class TrainingError(LearningError):
    """Training operation failed"""
    pass


class PredictionError(LearningError):
    """Prediction operation failed"""
    pass


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def handle_exception(
    exception: Exception,
    context: Optional[str] = None,
    reraise: bool = True
) -> Optional[HydraMindError]:
    """
    Handle and potentially convert exceptions to HydraMind exceptions.

    Args:
        exception: The original exception
        context: Additional context about where the error occurred
        reraise: Whether to re-raise the converted exception

    Returns:
        Converted HydraMind exception if applicable, None otherwise

    Raises:
        HydraMindError: If reraise=True and conversion is possible
    """
    # Convert common exception types
    if isinstance(exception, KeyError):
        hydra_error = ConfigurationError(
            f"Missing required configuration key: {exception.args[0] if exception.args else 'unknown'}",
            details={'key': str(exception)}
        )
    elif isinstance(exception, FileNotFoundError):
        hydra_error = ConfigFileError(
            f"Configuration file not found: {exception.filename}",
            details={'filename': exception.filename}
        )
    elif isinstance(exception, PermissionError):
        hydra_error = SecurityError(
            f"Permission denied: {exception.filename}",
            details={'filename': exception.filename}
        )
    elif isinstance(exception, TimeoutError):
        hydra_error = TimeoutError(
            f"Operation timed out: {str(exception)}",
            details={'original_error': str(exception)}
        )
    elif isinstance(exception, MemoryError):
        hydra_error = ResourceExhaustionError(
            "Insufficient memory for operation",
            details={'memory_error': str(exception)}
        )
    else:
        # Return original exception if no specific conversion
        return None

    if context:
        hydra_error.details['context'] = context

    if reraise:
        raise hydra_error

    return hydra_error


def create_error_context(
    operation: str,
    component: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create standardized error context for logging.

    Args:
        operation: The operation being performed
        component: The component where error occurred
        **kwargs: Additional context data

    Returns:
        Error context dictionary
    """
    return {
        'operation': operation,
        'component': component,
        'timestamp': __import__('time').time(),
        **kwargs
    }


# =============================================================================
# EXCEPTION REGISTRY
# =============================================================================

# Registry of exception types for programmatic handling
EXCEPTION_REGISTRY = {
    'configuration': ConfigurationError,
    'module': ModuleError,
    'event': EventSystemError,
    'data': DataLayerError,
    'execution': ExecutionError,
    'network': NetworkError,
    'system': SystemError,
    'learning': LearningError
}


def get_exception_type(category: str) -> type:
    """
    Get exception type by category.

    Args:
        category: Exception category

    Returns:
        Corresponding exception class

    Raises:
        KeyError: If category not found
    """
    return EXCEPTION_REGISTRY[category]
