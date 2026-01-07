"""
Caching System for CogniLink

This module provides caching functionality to improve performance
for repeated operations.
"""

import os
import json
import pickle
import hashlib
import time
import logging
from typing import Any, Dict, Optional, Callable, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

class Cache:
    """
    Cache implementation for storing and retrieving data.
    
    This class provides methods for caching data to improve performance
    for repeated operations.
    """
    
    def __init__(self, cache_dir: str = None, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory for storing cache files
            max_size: Maximum number of items to store in memory cache
            ttl: Time to live for cache items in seconds (default: 1 hour)
        """
        from cognilink.core.config import Config
        config = Config()
        
        self.cache_dir = cache_dir or config.get('paths', 'cache_dir', 'cache')
        self.max_size = max_size
        self.ttl = ttl
        self.memory_cache = {}
        self.access_times = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _generate_key(self, key_data: Any) -> str:
        """
        Generate a cache key from the provided data.
        
        Args:
            key_data: Data to generate key from
            
        Returns:
            String key
        """
        if isinstance(key_data, str):
            return hashlib.md5(key_data.encode('utf-8')).hexdigest()
        else:
            return hashlib.md5(str(key_data).encode('utf-8')).hexdigest()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            # Check if item has expired
            if time.time() - self.access_times[cache_key]['created'] > self.ttl:
                # Remove expired item
                del self.memory_cache[cache_key]
                del self.access_times[cache_key]
            else:
                # Update access time
                self.access_times[cache_key]['accessed'] = time.time()
                return self.memory_cache[cache_key]
        
        # Check file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.cache")
        if os.path.exists(cache_file):
            # Check if file has expired
            if time.time() - os.path.getmtime(cache_file) > self.ttl:
                # Remove expired file
                os.remove(cache_file)
                return default
            
            try:
                with open(cache_file, 'rb') as f:
                    value = pickle.load(f)
                
                # Add to memory cache
                self._add_to_memory_cache(cache_key, value)
                return value
            except Exception as e:
                logger.error(f"Error loading cache file {cache_file}: {str(e)}")
                return default
        
        return default
    
    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom time to live in seconds
        """
        cache_key = self._generate_key(key)
        
        # Add to memory cache
        self._add_to_memory_cache(cache_key, value)
        
        # Save to file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.cache")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.error(f"Error saving cache file {cache_file}: {str(e)}")
    
    def _add_to_memory_cache(self, cache_key: str, value: Any) -> None:
        """
        Add a value to the memory cache.
        
        Args:
            cache_key: Cache key
            value: Value to cache
        """
        # Check if cache is full
        if len(self.memory_cache) >= self.max_size:
            # Remove least recently accessed item
            oldest_key = min(self.access_times, key=lambda k: self.access_times[k]['accessed'])
            del self.memory_cache[oldest_key]
            del self.access_times[oldest_key]
        
        # Add new item
        self.memory_cache[cache_key] = value
        self.access_times[cache_key] = {
            'created': time.time(),
            'accessed': time.time()
        }
    
    def delete(self, key: Any) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        cache_key = self._generate_key(key)
        
        # Remove from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            del self.access_times[cache_key]
        
        # Remove from file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.cache")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        # Clear memory cache
        self.memory_cache = {}
        self.access_times = {}
        
        # Clear file cache
        for file_name in os.listdir(self.cache_dir):
            if file_name.endswith('.cache'):
                os.remove(os.path.join(self.cache_dir, file_name))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        # Count file cache items
        file_count = len([f for f in os.listdir(self.cache_dir) if f.endswith('.cache')])
        
        return {
            'memory_items': len(self.memory_cache),
            'file_items': file_count,
            'max_size': self.max_size,
            'ttl': self.ttl,
            'cache_dir': self.cache_dir
        }


# Cache decorator
def cached(ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live for cache items in seconds
        key_func: Function to generate cache key from function arguments
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache = Cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key is function name + args + kwargs
                cache_key = (func.__name__, args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


# Global cache instance
_cache_instance = None

def get_cache() -> Cache:
    """
    Get the global cache instance.
    
    Returns:
        Global cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance