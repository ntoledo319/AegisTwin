"""
Rate limiting middleware for the API.
"""

from fastapi import Request, HTTPException
import time
from typing import Dict, Tuple, Optional, Callable
import asyncio
from datetime import datetime, timedelta

# Simple in-memory rate limiter
# In production, this should use Redis or another distributed cache
class RateLimiter:
    def __init__(self, limit: int, window: int):
        """
        Initialize a rate limiter.
        
        Parameters:
        - limit: Maximum number of requests allowed in the window
        - window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests: Dict[str, list] = {}
        self.last_cleanup = time.time()
    
    async def cleanup(self):
        """
        Clean up expired request records.
        """
        now = time.time()
        # Only clean up every minute to avoid excessive processing
        if now - self.last_cleanup < 60:
            return
        
        self.last_cleanup = now
        cutoff = now - self.window
        
        for key in list(self.requests.keys()):
            # Filter out timestamps older than the window
            self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]
            # Remove empty entries
            if not self.requests[key]:
                del self.requests[key]
    
    async def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        Check if a key is rate limited.
        
        Parameters:
        - key: The key to check (usually IP address or user ID)
        
        Returns:
        - Tuple of (is_limited, retry_after)
        """
        await self.cleanup()
        
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove timestamps outside the current window
        self.requests[key] = [ts for ts in self.requests[key] if ts > now - self.window]
        
        # Check if the number of requests exceeds the limit
        if len(self.requests[key]) >= self.limit:
            oldest = min(self.requests[key])
            retry_after = int(oldest + self.window - now) + 1
            return True, retry_after
        
        # Add the current timestamp
        self.requests[key].append(now)
        return False, 0

# Create rate limiters with different limits
# In production, these would be configurable
api_limiter = RateLimiter(limit=100, window=60)  # 100 requests per minute
auth_limiter = RateLimiter(limit=10, window=60)  # 10 auth requests per minute

async def rate_limit_middleware(request: Request, limiter: RateLimiter = api_limiter):
    """
    Rate limiting middleware.
    
    Parameters:
    - request: FastAPI request object
    - limiter: Rate limiter to use
    
    Raises:
    - HTTPException: If rate limit is exceeded
    """
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # Check if the request is rate limited
    is_limited, retry_after = await limiter.is_rate_limited(client_ip)
    
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": str(retry_after)}
        )

# Rate limit dependency for routes
async def rate_limit(request: Request):
    """
    Rate limiting dependency for routes.
    
    Parameters:
    - request: FastAPI request object
    
    Raises:
    - HTTPException: If rate limit is exceeded
    """
    await rate_limit_middleware(request)

# Rate limit dependency for authentication routes
async def auth_rate_limit(request: Request):
    """
    Rate limiting dependency for authentication routes.
    
    Parameters:
    - request: FastAPI request object
    
    Raises:
    - HTTPException: If rate limit is exceeded
    """
    await rate_limit_middleware(request, auth_limiter)

# Create a rate limiter factory for custom limits
def create_rate_limiter(limit: int, window: int) -> Callable:
    """
    Create a custom rate limiter dependency.
    
    Parameters:
    - limit: Maximum number of requests allowed in the window
    - window: Time window in seconds
    
    Returns:
    - Rate limiting dependency function
    """
    limiter = RateLimiter(limit=limit, window=window)
    
    async def custom_rate_limit(request: Request):
        await rate_limit_middleware(request, limiter)
    
    return custom_rate_limit