"""
Redis-Backed Event Bus

Provides distributed event bus using Redis Streams for horizontal scaling.

@ai_prompt: Use RedisEventBus instead of EventBus for production deployments
@context_boundary: aegistwin/runtime/redis_bus
"""

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aegistwin.events.schema import BaseEvent, EventType

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    stream_name: str = "aegistwin:events"
    consumer_group: str = "aegistwin-workers"
    max_stream_length: int = 10000


class RedisEventBus:
    """
    Distributed event bus using Redis Streams.

    Features:
    - Horizontal scaling with consumer groups
    - Event persistence in Redis
    - Automatic stream trimming
    - Reconnection handling

    Attributes:
        config: Redis configuration
        client: Redis client instance
    """

    def __init__(self, config: RedisConfig | None = None):
        if not HAS_REDIS:
            raise RuntimeError("redis package not installed. Install with: pip install redis")

        self.config = config or RedisConfig()
        self._client: aioredis.Redis | None = None
        self._handlers: dict[EventType, list[Callable]] = {}
        self._running = False
        self._consumer_task: asyncio.Task | None = None
        self._consumer_name = f"consumer-{id(self)}"

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = aioredis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            password=self.config.password,
            decode_responses=True,
        )

        try:
            await self._client.xgroup_create(
                self.config.stream_name,
                self.config.consumer_group,
                id="0",
                mkstream=True,
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.close()
            self._client = None

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async callable to handle events
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: BaseEvent) -> str:
        """
        Publish an event to Redis Stream.

        Args:
            event: Event to publish

        Returns:
            Redis message ID
        """
        if not self._client:
            raise RuntimeError("Not connected to Redis")

        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "run_id": event.run_id or "",
            "payload": json.dumps(event.model_dump(mode="json")),
        }

        msg_id = await self._client.xadd(
            self.config.stream_name,
            event_data,
            maxlen=self.config.max_stream_length,
        )

        return msg_id

    async def start_consuming(self) -> None:
        """Start consuming events from Redis Stream."""
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_loop())

    async def _consume_loop(self) -> None:
        """Main consumer loop."""
        while self._running and self._client:
            try:
                messages = await self._client.xreadgroup(
                    groupname=self.config.consumer_group,
                    consumername=self._consumer_name,
                    streams={self.config.stream_name: ">"},
                    count=10,
                    block=1000,
                )

                for _stream, stream_messages in messages:
                    for msg_id, data in stream_messages:
                        await self._handle_message(msg_id, data)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def _handle_message(self, msg_id: str, data: dict) -> None:
        """Process a single message from the stream."""
        try:
            event_type = EventType(data["event_type"])
            handlers = self._handlers.get(event_type, [])

            payload = json.loads(data["payload"])

            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)

            await self._client.xack(
                self.config.stream_name,
                self.config.consumer_group,
                msg_id,
            )

        except Exception:
            pass

    async def get_stream_info(self) -> dict[str, Any]:
        """Get information about the event stream."""
        if not self._client:
            return {}

        info = await self._client.xinfo_stream(self.config.stream_name)
        return {
            "length": info.get("length", 0),
            "first_entry": info.get("first-entry"),
            "last_entry": info.get("last-entry"),
            "consumer_groups": info.get("groups", 0),
        }


class RedisEventBusFactory:
    """Factory for creating Redis event bus instances."""

    _instance: RedisEventBus | None = None

    @classmethod
    async def get_instance(cls, config: RedisConfig | None = None) -> RedisEventBus:
        """Get or create singleton Redis event bus."""
        if cls._instance is None:
            cls._instance = RedisEventBus(config)
            await cls._instance.connect()
        return cls._instance

    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown the singleton instance."""
        if cls._instance:
            await cls._instance.disconnect()
            cls._instance = None
