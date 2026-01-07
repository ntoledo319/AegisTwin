"""
Zero-copy data layer for high-performance sensor/telemetry streaming.

Provides:
- RingBuffer: Shared-memory circular buffer for inter-process communication
- MMapSnapshot: Memory-mapped file snapshots for instant state persistence
- TTLCache: Fast in-memory cache with automatic expiration
"""

from __future__ import annotations
import os
import mmap
import time
import logging
from pathlib import Path
from multiprocessing import shared_memory
from typing import Optional, Any, Tuple, List
import numpy as np

from .exceptions import RingBufferError

logger = logging.getLogger(__name__)


class RingBuffer:
    """
    Lock-free ring buffer using shared memory for IPC.
    
    Perfect for high-frequency sensor data streaming between processes.
    Uses numpy for zero-copy byte manipulation.
    """
    
    def __init__(
        self,
        name: str,
        capacity: int = 16384,
        item_bytes: int = 2048
    ):
        """
        Initialize ring buffer.
        
        Args:
            name: Shared memory name (must be unique per system)
            capacity: Number of items the buffer can hold
            item_bytes: Maximum bytes per item
        """
        self.name = name
        self.capacity = capacity
        self.item_bytes = item_bytes
        total_bytes = capacity * item_bytes
        
        try:
            # Try to create new shared memory
            self.shm = shared_memory.SharedMemory(
                name=name,
                create=True,
                size=total_bytes
            )
            self.owner = True
            logger.info(f"Created ring buffer '{name}': {capacity} items x {item_bytes} bytes")

        except FileExistsError:
            # Attach to existing shared memory
            try:
                self.shm = shared_memory.SharedMemory(
                    name=name,
                    create=False
                )
                self.owner = False
                logger.info(f"Attached to existing ring buffer '{name}'")
            except Exception as attach_error:
                logger.error(f"Failed to attach to existing ring buffer '{name}': {attach_error}")
                raise RingBufferError(
                    f"Failed to attach to existing ring buffer: {attach_error}",
                    details={'name': name, 'error': str(attach_error)}
                ) from attach_error

        except (OSError, PermissionError) as e:
            logger.error(f"Permission or OS error creating ring buffer '{name}': {e}")
            raise RingBufferError(
                f"Permission or OS error creating ring buffer: {e}",
                details={'name': name, 'error': str(e)}
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error creating ring buffer '{name}': {e}")
            raise RingBufferError(
                f"Failed to create ring buffer: {e}",
                details={'name': name, 'error_type': type(e).__name__}
            ) from e
        
        # Create numpy view of shared memory
        self.buf = np.ndarray(
            (capacity, item_bytes),
            dtype=np.uint8,
            buffer=self.shm.buf
        )
        
        self.head_writes = 0
    
    def write_bytes(self, data: bytes) -> None:
        """
        Write bytes to ring buffer (overwrites oldest if full).
        
        Args:
            data: Bytes to write (must be <= item_bytes)
            
        Raises:
            ValueError: If data is too large
        """
        if len(data) > self.item_bytes:
            raise ValueError(
                f"Data size {len(data)} exceeds item_bytes {self.item_bytes}"
            )
        
        try:
            slot = self.head_writes % self.capacity
            # Use numpy's efficient copy instead of fill + copy
            np.copyto(self.buf[slot], np.frombuffer(data.ljust(self.item_bytes, b'\x00'), dtype=np.uint8))
            self.head_writes += 1
            
        except Exception as e:
            logger.error(f"Failed to write to ring buffer: {e}")
            raise
    
    def read_snapshot(
        self,
        tail: int,
        max_items: int = 256
    ) -> Tuple[List[bytes], int]:
        """
        Read items from ring buffer starting at tail position.
        
        Args:
            tail: Starting read position
            max_items: Maximum items to read
            
        Returns:
            Tuple of (items list, new tail position)
        """
        items = []
        writes = self.head_writes
        
        try:
            while tail < writes and len(items) < max_items:
                slot = tail % self.capacity
                raw = bytes(self.buf[slot]).rstrip(b"\x00")

                if raw:  # Skip empty slots
                    items.append(raw)

                tail += 1
            
            return items, tail
            
        except Exception as e:
            logger.error(f"Failed to read from ring buffer: {e}")
            return items, tail
    
    def get_stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "name": self.name,
            "capacity": self.capacity,
            "item_bytes": self.item_bytes,
            "total_bytes": self.capacity * self.item_bytes,
            "total_writes": self.head_writes,
            "utilization": min(1.0, self.head_writes / self.capacity),
            "owner": self.owner
        }
    
    def close(self) -> None:
        """Close shared memory (unlinks if owner)."""
        try:
            self.shm.close()
            
            if self.owner:
                try:
                    self.shm.unlink()
                    logger.info(f"Unlinked ring buffer '{self.name}'")
                except FileNotFoundError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to unlink ring buffer: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to close ring buffer: {e}")


class MMapSnapshot:
    """
    Memory-mapped file for instant state snapshots.
    
    Changes are immediately visible to all processes mapping the same file.
    Perfect for checkpointing and state sharing.
    """
    
    def __init__(self, path: Path, size: int = 2_097_152):
        """
        Initialize memory-mapped snapshot file.
        
        Args:
            path: File path
            size: File size in bytes
        """
        self.path = path
        self.size = size
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create/open file
            fd = os.open(str(path), os.O_CREAT | os.O_RDWR)
            os.ftruncate(fd, size)
            
            # Create memory mapping
            self.mm = mmap.mmap(fd, size, access=mmap.ACCESS_WRITE)
            os.close(fd)
            
            logger.info(f"Created mmap snapshot: {path} ({size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to create mmap snapshot: {e}")
            raise
    
    def write_json(self, data: bytes) -> None:
        """
        Write JSON bytes to snapshot.
        
        Args:
            data: JSON bytes to write
            
        Raises:
            ValueError: If data is too large
        """
        if len(data) >= self.size:
            raise ValueError(
                f"Snapshot data {len(data)} exceeds size {self.size}"
            )
        
        try:
            self.mm.seek(0)
            self.mm.write(data)
            self.mm.write(b"\n")  # Delimiter
            self.mm.flush()
            
        except Exception as e:
            logger.error(f"Failed to write snapshot: {e}")
            raise
    
    def read_bytes(self) -> bytes:
        """Read bytes from snapshot until newline."""
        try:
            self.mm.seek(0)
            return self.mm.readline().rstrip(b"\n")
            
        except Exception as e:
            logger.error(f"Failed to read snapshot: {e}")
            return b""
    
    def close(self) -> None:
        """Close memory mapping."""
        try:
            self.mm.close()
            logger.info(f"Closed mmap snapshot: {self.path}")
            
        except Exception as e:
            logger.error(f"Failed to close mmap snapshot: {e}")


class TTLCache:
    """
    Simple in-memory cache with time-to-live expiration.
    
    Perfect for caching sensor readings, API responses, etc.
    Not thread-safe - use separate instance per thread if needed.
    """
    
    def __init__(self, default_ttl: float = 1.0):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.store: dict = {}
        logger.debug(f"Created TTL cache with default TTL={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        entry = self.store.get(key)
        
        if entry is None:
            return None
        
        expiry, value = entry
        
        if time.time() > expiry:
            # Expired - remove it
            del self.store[key]
            return None
        
        return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None
    ) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self.store[key] = (expiry, value)
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed
        """
        if key in self.store:
            del self.store[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.store.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired = [k for k, (exp, _) in self.store.items() if now > exp]
        
        for key in expired:
            del self.store[key]
        
        return len(expired)
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        now = time.time()
        expired = sum(1 for exp, _ in self.store.values() if now > exp)
        
        return {
            "size": len(self.store),
            "expired": expired,
            "active": len(self.store) - expired,
            "default_ttl": self.default_ttl
        }
