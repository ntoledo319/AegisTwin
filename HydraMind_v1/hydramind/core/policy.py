"""
Policy engine for rate limiting and topic filtering.

Provides security and backpressure control for the event bus.
"""

from __future__ import annotations
import time
import logging
from typing import Iterable, Optional, Set
from .bus import Message

logger = logging.getLogger(__name__)


class PolicyGuard:
    """
    Policy enforcement for event bus messages.
    
    Features:
    - Topic allowlisting for security
    - Rate limiting to prevent overload
    - Per-topic and global rate tracking
    """
    
    def __init__(
        self,
        allowed: Optional[Iterable[str]] = None,
        max_per_sec: int = 50000
    ):
        """
        Initialize policy guard.
        
        Args:
            allowed: Allowed topics (None = allow all)
            max_per_sec: Maximum messages per second (global limit)
        """
        self.allowed: Optional[Set[str]] = set(allowed) if allowed else None
        self.max_per_sec = max_per_sec
        
        # Rate limiting state
        self._ticks = 0
        self._window_start = time.time()
        self._violations = 0
        
        if self.allowed:
            logger.info(f"Policy guard initialized with {len(self.allowed)} allowed topics")
        else:
            logger.info("Policy guard initialized (all topics allowed)")
    
    def verify(self, msg: Message) -> bool:
        """
        Verify if message is allowed.
        
        Checks:
        1. Topic allowlist (if configured)
        2. Rate limiting
        
        Args:
            msg: Message to verify
            
        Returns:
            True if message is allowed
        """
        # Check allowlist
        if self.allowed and msg.topic not in self.allowed:
            logger.warning(f"Topic '{msg.topic}' not in allowlist")
            self._violations += 1
            return False
        
        # Check rate limit
        now = time.time()
        
        # Reset window if > 1 second elapsed
        if now - self._window_start > 1.0:
            self._window_start = now
            self._ticks = 0
        
        self._ticks += 1
        
        if self._ticks > self.max_per_sec:
            if self._ticks == self.max_per_sec + 1:  # Log only once per window
                logger.warning(
                    f"Rate limit exceeded: {self._ticks} msg/sec "
                    f"(max {self.max_per_sec})"
                )
            self._violations += 1
            return False
        
        return True
    
    def add_allowed_topic(self, topic: str) -> None:
        """
        Add topic to allowlist.
        
        Args:
            topic: Topic to allow
        """
        if self.allowed is None:
            self.allowed = set()
        
        self.allowed.add(topic)
        logger.debug(f"Added '{topic}' to allowlist")
    
    def remove_allowed_topic(self, topic: str) -> bool:
        """
        Remove topic from allowlist.
        
        Args:
            topic: Topic to remove
            
        Returns:
            True if topic was in allowlist
        """
        if self.allowed and topic in self.allowed:
            self.allowed.remove(topic)
            logger.debug(f"Removed '{topic}' from allowlist")
            return True
        return False
    
    def is_allowed(self, topic: str) -> bool:
        """
        Check if topic is in allowlist.
        
        Args:
            topic: Topic to check
            
        Returns:
            True if allowed (or no allowlist configured)
        """
        if self.allowed is None:
            return True
        return topic in self.allowed
    
    def get_stats(self) -> dict:
        """Get policy statistics."""
        return {
            "allowlist_enabled": self.allowed is not None,
            "allowed_topics": len(self.allowed) if self.allowed else None,
            "max_per_sec": self.max_per_sec,
            "current_rate": self._ticks / max(0.01, time.time() - self._window_start),
            "violations": self._violations
        }
    
    def reset_stats(self) -> None:
        """Reset violation counter."""
        self._violations = 0
        logger.debug("Policy stats reset")
