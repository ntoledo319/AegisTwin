"""
High-performance event bus with wildcard subscriptions and persistent storage.

The EventBus is the nervous system of HydraMind - all modules communicate through it.
Supports wildcards, QoS levels, and automatic event persistence.
"""

from __future__ import annotations
import asyncio
import logging
import fnmatch
from dataclasses import dataclass
from typing import Dict, List, Protocol, Optional
from .event_store import EventStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Message:
    """
    Event message passed through the bus.
    
    Attributes:
        topic: Event topic (supports wildcard patterns in subscriptions)
        data: Event payload (must be JSON-serializable dict)
        qos: Quality of service (0=fire-and-forget, 1=at-least-once)
        key: Optional key for deduplication/grouping
    """
    topic: str
    data: dict
    qos: int = 0
    key: Optional[str] = None
    
    def __post_init__(self):
        """Validate message."""
        if not isinstance(self.data, dict):
            raise TypeError("Message data must be a dict")
        if self.qos not in (0, 1):
            raise ValueError("QoS must be 0 or 1")


class Subscriber(Protocol):
    """Protocol for event subscribers."""
    
    async def on_message(self, msg: Message) -> None:
        """
        Handle incoming message.
        
        Args:
            msg: Event message
        """
        ...


class EventBus:
    """
    Asynchronous event bus with wildcard routing and persistence.
    
    Features:
    - Wildcard subscriptions (e.g., "sensor/*", "robot/arm/*")
    - Persistent event log via EventStore
    - Async dispatch with error isolation
    - Queue-based delivery for backpressure handling
    - Metrics and monitoring
    """
    
    def __init__(
        self,
        event_store: EventStore,
        max_queue: int = 500_000
    ):
        """
        Initialize event bus.
        
        Args:
            event_store: EventStore instance for persistence
            max_queue: Maximum queued messages before blocking
        """
        self.event_store = event_store
        self._subs: Dict[str, List[Subscriber]] = {}
        self._queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=max_queue)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Metrics
        self._messages_published = 0
        self._messages_dispatched = 0
        self._dispatch_errors = 0
        
        logger.info(f"EventBus initialized (max_queue={max_queue})")
    
    def subscribe(self, pattern: str, subscriber: Subscriber) -> None:
        """
        Subscribe to events matching pattern.
        
        Patterns support wildcards:
        - "*" matches any single level
        - "**" matches any number of levels
        
        Examples:
            - "sensor/*" matches "sensor/temp", "sensor/humidity"
            - "robot/*/status" matches "robot/arm1/status", "robot/gripper/status"
            - "telemetry/**" matches all sub-topics of telemetry
        
        Args:
            pattern: Topic pattern (supports wildcards)
            subscriber: Subscriber instance
        """
        self._subs.setdefault(pattern, []).append(subscriber)
        logger.debug(f"Subscribed {subscriber} to pattern '{pattern}'")
    
    def unsubscribe(self, pattern: str, subscriber: Subscriber) -> bool:
        """
        Unsubscribe from pattern.
        
        Args:
            pattern: Topic pattern
            subscriber: Subscriber instance
            
        Returns:
            True if subscriber was found and removed
        """
        if pattern in self._subs:
            try:
                self._subs[pattern].remove(subscriber)
                logger.debug(f"Unsubscribed {subscriber} from pattern '{pattern}'")
                
                # Clean up empty pattern lists
                if not self._subs[pattern]:
                    del self._subs[pattern]
                
                return True
            except ValueError:
                pass
        
        return False
    
    async def publish(self, msg: Message) -> None:
        """
        Publish message to the bus.
        
        Message will be:
        1. Persisted to EventStore
        2. Queued for dispatch
        3. Delivered to all matching subscribers
        
        Args:
            msg: Message to publish
            
        Raises:
            asyncio.QueueFull: If queue is full (shouldn't happen with high max_queue)
        """
        try:
            await self._queue.put(msg)
            self._messages_published += 1
            
        except asyncio.QueueFull:
            logger.error(f"Event queue full! Dropping message: {msg.topic}")
            raise
    
    async def _dispatch(self, msg: Message) -> None:
        """
        Dispatch message to all matching subscribers.
        
        Args:
            msg: Message to dispatch
        """
        dispatched = 0
        
        for pattern, subscribers in self._subs.items():
            # Check if topic matches pattern
            if fnmatch.fnmatch(msg.topic, pattern):
                for sub in subscribers:
                    try:
                        # Fire and forget - don't block on subscriber processing
                        asyncio.create_task(
                            self._safe_deliver(sub, msg)
                        )
                        dispatched += 1
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to create dispatch task for {sub}: {e}"
                        )
                        self._dispatch_errors += 1
        
        if dispatched > 0:
            self._messages_dispatched += dispatched
            logger.debug(f"Dispatched '{msg.topic}' to {dispatched} subscribers")
        else:
            logger.debug(f"No subscribers for '{msg.topic}'")
    
    async def _safe_deliver(self, sub: Subscriber, msg: Message) -> None:
        """
        Safely deliver message to subscriber with error isolation.
        
        Args:
            sub: Subscriber
            msg: Message
        """
        try:
            await sub.on_message(msg)
            
        except Exception as e:
            logger.error(
                f"Subscriber {sub} failed to handle message '{msg.topic}': {e}",
                exc_info=True
            )
            self._dispatch_errors += 1
    
    async def run(self) -> None:
        """
        Run the event bus dispatcher.
        
        This should be called as a background task.
        Processes queued messages and dispatches to subscribers.
        """
        self._running = True
        logger.info("EventBus started")
        
        try:
            while self._running:
                try:
                    # Wait for message with timeout to allow shutdown
                    msg = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=0.1
                    )
                    
                    # Persist event
                    try:
                        self.event_store.persist(
                            msg.topic,
                            msg.data,
                            msg.qos,
                            msg.key
                        )
                    except Exception as e:
                        logger.error(f"Failed to persist event: {e}")
                        # Continue anyway - don't block event flow
                    
                    # Dispatch to subscribers
                    await self._dispatch(msg)
                    
                except asyncio.TimeoutError:
                    # No message - continue loop
                    continue
                
                except Exception as e:
                    logger.error(f"Error in event bus loop: {e}", exc_info=True)
                    await asyncio.sleep(0.01)  # Brief pause before retry
        
        finally:
            logger.info("EventBus stopped")
    
    def start(self) -> asyncio.Task:
        """
        Start the event bus as a background task.
        
        Returns:
            Task handle
        """
        if self._task is not None and not self._task.done():
            logger.warning("EventBus already running")
            return self._task
        
        self._task = asyncio.create_task(self.run())
        return self._task
    
    def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
    
    async def wait_until_stopped(self) -> None:
        """Wait for event bus to stop."""
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> dict:
        """Get event bus statistics."""
        return {
            "running": self._running,
            "messages_published": self._messages_published,
            "messages_dispatched": self._messages_dispatched,
            "dispatch_errors": self._dispatch_errors,
            "queue_size": self._queue.qsize(),
            "queue_max": self._queue.maxsize,
            "subscribers": sum(len(subs) for subs in self._subs.values()),
            "patterns": len(self._subs)
        }
