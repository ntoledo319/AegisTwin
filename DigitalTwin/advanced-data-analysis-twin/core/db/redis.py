"""
Redis client for caching and real-time features in the Advanced Data Analysis & Digital Twin System.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Redis client for caching and real-time features.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, password: Optional[str] = None, db: int = 0):
        """
        Initialize the Redis client.
        
        Parameters:
        - host: Redis host
        - port: Redis port
        - password: Redis password
        - db: Redis database number
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.password = password or os.getenv("REDIS_PASSWORD", None)
        self.db = db
        self.client = None
    
    async def connect(self) -> None:
        """
        Connect to Redis.
        
        Raises:
        - RedisError: If connection fails
        """
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True
            )
            # Ping the server to check connection
            self.client.ping()
            logger.info(f"Connected to Redis: {self.host}:{self.port}, db: {self.db}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from Redis.
        """
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    async def set(self, key: str, value: Union[str, Dict[str, Any], List[Any]], expire: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Parameters:
        - key: Redis key
        - value: Value to store (string or JSON-serializable object)
        - expire: Expiration time in seconds
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            # Convert dict/list to JSON string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
        except RedisError as e:
            logger.error(f"Failed to set Redis key {key}: {e}")
            raise
    
    async def get(self, key: str, as_json: bool = False) -> Optional[Union[str, Dict[str, Any], List[Any]]]:
        """
        Get a value from Redis.
        
        Parameters:
        - key: Redis key
        - as_json: Whether to parse the value as JSON
        
        Returns:
        - Value if key exists, None otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            value = self.client.get(key)
            
            if value is None:
                return None
            
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Redis value as JSON: {value}")
                    return value
            
            return value
        except RedisError as e:
            logger.error(f"Failed to get Redis key {key}: {e}")
            raise
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Parameters:
        - key: Redis key
        
        Returns:
        - True if key was deleted, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Failed to delete Redis key {key}: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Parameters:
        - key: Redis key
        
        Returns:
        - True if key exists, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Failed to check if Redis key {key} exists: {e}")
            raise
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Parameters:
        - key: Redis key
        - seconds: Expiration time in seconds
        
        Returns:
        - True if successful, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return bool(self.client.expire(key, seconds))
        except RedisError as e:
            logger.error(f"Failed to set expiration for Redis key {key}: {e}")
            raise
    
    async def ttl(self, key: str) -> int:
        """
        Get the remaining time to live for a key.
        
        Parameters:
        - key: Redis key
        
        Returns:
        - Remaining time in seconds, -1 if no expiration, -2 if key doesn't exist
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Failed to get TTL for Redis key {key}: {e}")
            raise
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a key's value.
        
        Parameters:
        - key: Redis key
        - amount: Amount to increment
        
        Returns:
        - New value
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Failed to increment Redis key {key}: {e}")
            raise
    
    async def hash_set(self, key: str, field: str, value: Union[str, Dict[str, Any], List[Any]]) -> bool:
        """
        Set a field in a Redis hash.
        
        Parameters:
        - key: Redis key
        - field: Hash field
        - value: Value to store (string or JSON-serializable object)
        
        Returns:
        - True if field is new, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            # Convert dict/list to JSON string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            return bool(self.client.hset(key, field, value))
        except RedisError as e:
            logger.error(f"Failed to set field {field} in Redis hash {key}: {e}")
            raise
    
    async def hash_get(self, key: str, field: str, as_json: bool = False) -> Optional[Union[str, Dict[str, Any], List[Any]]]:
        """
        Get a field from a Redis hash.
        
        Parameters:
        - key: Redis key
        - field: Hash field
        - as_json: Whether to parse the value as JSON
        
        Returns:
        - Value if field exists, None otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            value = self.client.hget(key, field)
            
            if value is None:
                return None
            
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Redis hash value as JSON: {value}")
                    return value
            
            return value
        except RedisError as e:
            logger.error(f"Failed to get field {field} from Redis hash {key}: {e}")
            raise
    
    async def hash_delete(self, key: str, field: str) -> bool:
        """
        Delete a field from a Redis hash.
        
        Parameters:
        - key: Redis key
        - field: Hash field
        
        Returns:
        - True if field was deleted, False otherwise
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            return bool(self.client.hdel(key, field))
        except RedisError as e:
            logger.error(f"Failed to delete field {field} from Redis hash {key}: {e}")
            raise
    
    async def hash_get_all(self, key: str, as_json: bool = False) -> Dict[str, Any]:
        """
        Get all fields and values from a Redis hash.
        
        Parameters:
        - key: Redis key
        - as_json: Whether to parse values as JSON
        
        Returns:
        - Dictionary of fields and values
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            result = self.client.hgetall(key)
            
            if as_json:
                for field, value in result.items():
                    try:
                        result[field] = json.loads(value)
                    except json.JSONDecodeError:
                        # Keep as string if not valid JSON
                        pass
            
            return result
        except RedisError as e:
            logger.error(f"Failed to get all fields from Redis hash {key}: {e}")
            raise
    
    async def publish(self, channel: str, message: Union[str, Dict[str, Any], List[Any]]) -> int:
        """
        Publish a message to a Redis channel.
        
        Parameters:
        - channel: Redis channel
        - message: Message to publish (string or JSON-serializable object)
        
        Returns:
        - Number of clients that received the message
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            # Convert dict/list to JSON string
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            return self.client.publish(channel, message)
        except RedisError as e:
            logger.error(f"Failed to publish message to Redis channel {channel}: {e}")
            raise
    
    def create_subscriber(self, channels: List[str]):
        """
        Create a Redis subscriber for channels.
        
        Parameters:
        - channels: List of channels to subscribe to
        
        Returns:
        - Redis pubsub object
        
        Raises:
        - ValueError: If not connected to Redis
        - RedisError: If operation fails
        """
        if not self.client:
            raise ValueError("Not connected to Redis")
        
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except RedisError as e:
            logger.error(f"Failed to create Redis subscriber for channels {channels}: {e}")
            raise

# Singleton instance
redis_client = RedisClient()