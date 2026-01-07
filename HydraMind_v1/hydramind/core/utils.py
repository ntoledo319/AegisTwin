"""
HydraMind Utility Functions

Common utility functions used throughout the HydraMind system.
Provides consistent implementations for frequent operations.
"""

from __future__ import annotations
import asyncio
import functools
import hashlib
import inspect
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Awaitable
from contextlib import asynccontextmanager, contextmanager

from .constants import (
    DEFAULT_CONFIG, PERFORMANCE, LIMITS,
    validate_topic, validate_message_size,
    JSONData, Topic, Timestamp
)
from .exceptions import HydraMindError, handle_exception


logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


# =============================================================================
# ASYNC UTILITIES
# =============================================================================

async def async_timeout(timeout: float, coro: Awaitable[T]) -> T:
    """
    Run coroutine with timeout.

    Args:
        timeout: Maximum time to wait in seconds
        coro: Coroutine to run

    Returns:
        Coroutine result

    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    return await asyncio.wait_for(coro, timeout=timeout)


@asynccontextmanager
async def async_context_timeout(timeout: float):
    """
    Async context manager with timeout.

    Usage:
        async with async_context_timeout(30.0):
            await long_operation()
    """
    try:
        yield
    except asyncio.TimeoutError:
        raise HydraMindError(
            f"Operation timed out after {timeout}s",
            code="TIMEOUT",
            details={'timeout': timeout}
        )


def run_async(coro: Awaitable[T], timeout: Optional[float] = None) -> T:
    """
    Run async coroutine in sync context.

    Args:
        coro: Coroutine to run
        timeout: Optional timeout in seconds

    Returns:
        Coroutine result
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a task
            task = asyncio.create_task(coro)
            if timeout:
                return loop.run_until_complete(async_timeout(timeout, task))
            return loop.run_until_complete(task)
        else:
            # Create new loop if none running
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


# =============================================================================
# RETRY UTILITIES
# =============================================================================

async def retry_async(
    func: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> T:
    """
    Retry async function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
        exceptions: Exception types to catch
        on_retry: Optional callback for retry attempts

    Returns:
        Function result

    Raises:
        Last exception if all attempts fail
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt < max_attempts - 1:
                wait_time = delay * (backoff ** attempt)

                if on_retry:
                    on_retry(e, attempt + 1)

                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {e}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_attempts} attempts failed")

    raise last_exception


def retry_sync(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> T:
    """
    Retry sync function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Backoff multiplier
        exceptions: Exception types to catch
        on_retry: Optional callback for retry attempts

    Returns:
        Function result

    Raises:
        Last exception if all attempts fail
    """
    import time

    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e

            if attempt < max_attempts - 1:
                wait_time = delay * (backoff ** attempt)

                if on_retry:
                    on_retry(e, attempt + 1)

                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {e}"
                )
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_attempts} attempts failed")

    raise last_exception


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_json_data(data: Any) -> JSONData:
    """
    Validate and convert data to JSON-serializable format.

    Args:
        data: Data to validate

    Returns:
        Validated JSON data

    Raises:
        HydraMindError: If data is not JSON-serializable
    """
    try:
        # Test JSON serialization
        json.dumps(data)
        return data
    except (TypeError, ValueError) as e:
        raise HydraMindError(
            f"Data is not JSON-serializable: {e}",
            code="INVALID_JSON_DATA",
            details={'data_type': type(data).__name__}
        )


def validate_message_data(topic: str, data: Any) -> JSONData:
    """
    Validate message data for event publishing.

    Args:
        topic: Event topic
        data: Message data

    Returns:
        Validated message data

    Raises:
        HydraMindError: If validation fails
    """
    if not validate_topic(topic):
        raise HydraMindError(
            f"Invalid topic format: {topic}",
            code="INVALID_TOPIC",
            details={'topic': topic}
        )

    if not validate_message_size(data):
        raise HydraMindError(
            "Message size exceeds limit",
            code="MESSAGE_TOO_LARGE",
            details={'topic': topic, 'data_size': len(str(data))}
        )

    return validate_json_data(data)


# =============================================================================
# ID AND HASH UTILITIES
# =============================================================================

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID
        length: Length of random part (excluding prefix)

    Returns:
        Unique identifier string
    """
    random_part = str(uuid.uuid4()).replace('-', '')[:length]
    return f"{prefix}{random_part}"


def generate_message_id() -> str:
    """Generate unique message ID."""
    return generate_id("msg_", 12)


def generate_request_id() -> str:
    """Generate unique request ID."""
    return generate_id("req_", 12)


def hash_data(data: Any) -> str:
    """
    Generate hash of data for deduplication.

    Args:
        data: Data to hash

    Returns:
        SHA256 hash string
    """
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()[:16]


# =============================================================================
# PATH AND FILE UTILITIES
# =============================================================================

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path

    Returns:
        Path object

    Raises:
        HydraMindError: If directory cannot be created
    """
    path = Path(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except (OSError, PermissionError) as e:
        raise HydraMindError(
            f"Cannot create directory {path}: {e}",
            code="DIRECTORY_ERROR",
            details={'path': str(path)}
        )


def safe_filename(name: str) -> str:
    """
    Convert string to safe filename.

    Args:
        name: Original name

    Returns:
        Safe filename
    """
    import re
    # Replace unsafe characters with underscores
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove multiple underscores and trailing/leading underscores
    safe = re.sub(r'_+', '_', safe).strip('_')
    return safe


# =============================================================================
# PERFORMANCE UTILITIES
# =============================================================================

def measure_time(func: F) -> F:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to measure

    Returns:
        Wrapped function with timing
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.debug(
                f"{func.__name__} executed in {execution_time:.4f}s",
                extra={
                    'function': func.__name__,
                    'execution_time': execution_time,
                    'module': func.__module__
                }
            )

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f}s: {e}",
                extra={
                    'function': func.__name__,
                    'execution_time': execution_time,
                    'error': str(e)
                }
            )
            raise

    return wrapper  # type: ignore


def measure_async_time(func: F) -> F:
    """
    Decorator to measure async function execution time.

    Args:
        func: Async function to measure

    Returns:
        Wrapped function with timing
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.debug(
                f"{func.__name__} executed in {execution_time:.4f}s",
                extra={
                    'function': func.__name__,
                    'execution_time': execution_time,
                    'module': func.__module__
                }
            )

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.4f}s: {e}",
                extra={
                    'function': func.__name__,
                    'execution_time': execution_time,
                    'error': str(e)
                }
            )
            raise

    return wrapper  # type: ignore


# =============================================================================
# DICT AND DATA UTILITIES
# =============================================================================

def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        update: Dictionary to merge in

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(
    d: Dict[str, Any],
    prefix: str = "",
    separator: str = "."
) -> Dict[str, Any]:
    """
    Flatten nested dictionary.

    Args:
        d: Dictionary to flatten
        prefix: Key prefix
        separator: Key separator

    Returns:
        Flattened dictionary
    """
    items = []

    for key, value in d.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))

    return dict(items)


def filter_dict(
    d: Dict[str, Any],
    keys: List[str],
    include: bool = True
) -> Dict[str, Any]:
    """
    Filter dictionary by keys.

    Args:
        d: Dictionary to filter
        keys: Keys to include/exclude
        include: If True, include only these keys; if False, exclude them

    Returns:
        Filtered dictionary
    """
    if include:
        return {k: v for k, v in d.items() if k in keys}
    else:
        return {k: v for k, v in d.items() if k not in keys}


# =============================================================================
# TYPE CHECKING UTILITIES
# =============================================================================

def is_coroutine_function(func: Any) -> bool:
    """
    Check if function is a coroutine function.

    Args:
        func: Function to check

    Returns:
        True if coroutine function
    """
    return inspect.iscoroutinefunction(func)


def get_function_signature(func: Callable) -> str:
    """
    Get string representation of function signature.

    Args:
        func: Function to inspect

    Returns:
        Function signature string
    """
    try:
        sig = inspect.signature(func)
        return f"{func.__name__}{sig}"
    except (ValueError, TypeError):
        return f"{func.__name__}(...)"


# =============================================================================
# SYSTEM INFORMATION UTILITIES
# =============================================================================

def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.

    Returns:
        System information dictionary
    """
    import platform
    import psutil

    try:
        cpu_count = psutil.cpu_count(logical=True) or 1
        memory = psutil.virtual_memory()

        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': cpu_count,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_percent': memory.percent,
            'pid': __import__('os').getpid()
        }
    except Exception as e:
        logger.warning(f"Could not get full system info: {e}")
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'error': str(e)
        }


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes in human-readable format.

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 30m 45s")
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours}h {minutes}m {seconds:.0f}s"
