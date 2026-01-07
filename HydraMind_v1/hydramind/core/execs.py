"""
Adaptive execution layer with thread and process pools.

Provides intelligent resource management and execution strategies based on:
- CPU/memory availability
- Task characteristics (I/O-bound vs CPU-bound)
- System load
"""

from __future__ import annotations
import psutil
import asyncio
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Callable, Optional, Any, TypeVar
import functools

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ResourceHint:
    """
    Resource recommendations based on system state.
    
    Attributes:
        threads: Recommended thread pool size
        processes: Recommended process pool size
        cpu_pct: Current CPU usage percentage
        mem_pct: Current memory usage percentage
        available_memory_gb: Available memory in GB
    """
    threads: int
    processes: int
    cpu_pct: float
    mem_pct: float
    available_memory_gb: float
    
    def __str__(self) -> str:
        return (
            f"ResourceHint(threads={self.threads}, processes={self.processes}, "
            f"cpu={self.cpu_pct:.1f}%, mem={self.mem_pct:.1f}%, "
            f"available={self.available_memory_gb:.1f}GB)"
        )


class ResourceManager:
    """
    Analyzes system resources and provides execution recommendations.
    
    Helps determine optimal pool sizes based on current system state.
    """
    
    def __init__(self) -> None:
        """Initialize resource manager."""
        self._cpu_count = psutil.cpu_count(logical=True) or 2
        logger.info(f"ResourceManager initialized (CPUs={self._cpu_count})")
    
    def recommend(self, load_factor: float = 0.75) -> ResourceHint:
        """
        Get resource recommendations based on current system state.
        
        Args:
            load_factor: Fraction of resources to use (0.0-1.0)
            
        Returns:
            ResourceHint with recommendations
        """
        try:
            # CPU info
            cpu_pct = psutil.cpu_percent(interval=0.1)
            
            # Memory info
            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            available_gb = mem.available / (1024 ** 3)
            
            # Thread pool sizing
            # I/O-bound tasks can use more threads than CPUs
            threads = max(2, int(self._cpu_count * 2 * load_factor))
            
            # Process pool sizing
            # CPU-bound tasks should not exceed CPU count
            # Also consider available memory (rough estimate: 512MB per process)
            max_procs_by_mem = max(1, int(available_gb / 0.5))
            max_procs_by_cpu = max(1, int(self._cpu_count * load_factor))
            processes = min(max_procs_by_mem, max_procs_by_cpu)
            
            hint = ResourceHint(
                threads=threads,
                processes=processes,
                cpu_pct=cpu_pct,
                mem_pct=mem_pct,
                available_memory_gb=available_gb
            )
            
            logger.debug(f"Resource recommendation: {hint}")
            return hint
            
        except Exception as e:
            logger.error(f"Failed to get resource recommendations: {e}")
            # Fallback to conservative defaults
            return ResourceHint(
                threads=4,
                processes=2,
                cpu_pct=0.0,
                mem_pct=0.0,
                available_memory_gb=0.0
            )
    
    def should_scale_up(self, current_threads: int) -> bool:
        """
        Check if we should scale up thread pool.
        
        Args:
            current_threads: Current thread pool size
            
        Returns:
            True if scaling up is recommended
        """
        try:
            cpu_pct = psutil.cpu_percent(interval=0.1)
            mem_pct = psutil.virtual_memory().percent
            
            # Scale up if CPU usage is high but we have memory
            if cpu_pct > 80 and mem_pct < 80:
                return current_threads < self._cpu_count * 4
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check scaling: {e}")
            return False


class Exec:
    """
    Adaptive execution layer with thread and process pools.
    
    Provides async wrappers for running blocking functions in pools.
    Automatically selects appropriate pool based on task characteristics.
    
    Tiers:
        0: Async/lightweight - no pool needed
        1: I/O-bound - thread pool
        2+: CPU-bound - process pool
    """
    
    def __init__(self, hint: ResourceHint):
        """
        Initialize execution pools.
        
        Args:
            hint: Resource recommendations
        """
        self.hint = hint
        
        try:
            self.tpool = ThreadPoolExecutor(
                max_workers=hint.threads,
                thread_name_prefix="hydra_worker"
            )
            logger.info(f"Thread pool initialized: {hint.threads} workers")
            
        except Exception as e:
            logger.error(f"Failed to create thread pool: {e}")
            self.tpool = ThreadPoolExecutor(max_workers=4)
        
        try:
            self.ppool = ProcessPoolExecutor(
                max_workers=hint.processes
            )
            logger.info(f"Process pool initialized: {hint.processes} workers")
            
        except Exception as e:
            logger.error(f"Failed to create process pool: {e}")
            self.ppool = None
    
    async def thread(
        self,
        fn: Callable[..., T],
        *args: Any,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> T:
        """
        Run function in thread pool.
        
        Best for I/O-bound operations (file I/O, network, database).
        
        Args:
            fn: Function to execute
            *args: Positional arguments
            timeout: Optional timeout in seconds
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
            Exception: Any exception raised by function
        """
        try:
            loop = asyncio.get_running_loop()
            
            # Wrap function with args
            wrapped = functools.partial(fn, *args, **kwargs)
            
            # Submit to thread pool
            future = loop.run_in_executor(self.tpool, wrapped)
            
            if timeout:
                return await asyncio.wait_for(future, timeout)
            else:
                return await future
                
        except Exception as e:
            logger.error(f"Thread execution failed: {e}", exc_info=True)
            raise
    
    async def process(
        self,
        fn: Callable[..., T],
        *args: Any,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> T:
        """
        Run function in process pool.
        
        Best for CPU-bound operations (computation, data processing).
        Note: Function and arguments must be picklable.
        
        Args:
            fn: Function to execute (must be picklable)
            *args: Positional arguments (must be picklable)
            timeout: Optional timeout in seconds
            **kwargs: Keyword arguments (must be picklable)
            
        Returns:
            Function result
            
        Raises:
            RuntimeError: If process pool not available
            asyncio.TimeoutError: If timeout exceeded
            Exception: Any exception raised by function
        """
        if self.ppool is None:
            raise RuntimeError("Process pool not available")
        
        try:
            loop = asyncio.get_running_loop()
            
            # Wrap function with args
            wrapped = functools.partial(fn, *args, **kwargs)
            
            # Submit to process pool
            future = loop.run_in_executor(self.ppool, wrapped)
            
            if timeout:
                return await asyncio.wait_for(future, timeout)
            else:
                return await future
                
        except Exception as e:
            logger.error(f"Process execution failed: {e}", exc_info=True)
            raise
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown execution pools.
        
        Args:
            wait: Wait for pending tasks to complete
        """
        try:
            logger.info("Shutting down thread pool...")
            self.tpool.shutdown(wait=wait)
            
            if self.ppool:
                logger.info("Shutting down process pool...")
                self.ppool.shutdown(wait=wait)
            
            logger.info("Execution pools shut down")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_stats(self) -> dict:
        """Get execution pool statistics."""
        return {
            "thread_workers": self.hint.threads,
            "process_workers": self.hint.processes,
            "process_pool_available": self.ppool is not None,
            "cpu_pct": self.hint.cpu_pct,
            "mem_pct": self.hint.mem_pct,
            "available_memory_gb": self.hint.available_memory_gb
        }


async def run_with_retry(
    coro_fn: Callable[..., Any],
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Run async function with exponential backoff retry.
    
    Args:
        coro_fn: Async function to execute
        max_retries: Maximum retry attempts
        retry_delay: Initial delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result
        
    Raises:
        Exception: Last exception if all retries fail
    """
    last_exception = None
    delay = retry_delay
    
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn(*args, **kwargs)
            
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception
