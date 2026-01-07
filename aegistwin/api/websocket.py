"""
AegisTwin WebSocket Handlers

Real-time event streaming via WebSocket for dashboards and monitoring.

@ai_prompt: Use ConnectionManager for WebSocket connection management.
@context_boundary: aegistwin/api/websocket

# AI-GENERATED 2026-01-07
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from aegistwin.events.schema import BaseEvent, EventType


def event_to_json(event: BaseEvent) -> str:
    """
    Serialize an event to JSON for WebSocket transmission.

    Args:
        event: AegisTwin event to serialize

    Returns:
        JSON string representation
    """
    data = {
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "timestamp": event.timestamp.isoformat(),
        "run_id": event.run_id,
        "parent_event_id": event.parent_event_id,
        "payload_hash": event.payload_hash,
    }

    # Add event-specific fields
    event_dict = event.model_dump(mode="json")
    for key, value in event_dict.items():
        if key not in data and key != "metadata":
            data[key] = value

    return json.dumps(data, default=str)


class ConnectionManager:
    """
    Manages WebSocket connections and event broadcasting.

    Supports:
    - Multiple concurrent connections
    - Filtered subscriptions by event type
    - Run-specific subscriptions
    - Automatic cleanup on disconnect

    Attributes:
        active_connections: Set of active WebSocket connections
        subscriptions: Dict mapping connection to event type filters
        run_subscriptions: Dict mapping connection to run ID filters
    """

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.subscriptions: dict[WebSocket, set[EventType]] = {}
        self.run_subscriptions: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        event_types: list[str] | None = None,
        run_id: str | None = None,
    ) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection to accept
            event_types: Optional list of event types to subscribe to
            run_id: Optional run ID to filter events
        """
        await websocket.accept()

        async with self._lock:
            self.active_connections.add(websocket)

            # Set up event type filter
            if event_types:
                self.subscriptions[websocket] = {
                    EventType(et) for et in event_types
                    if et in [e.value for e in EventType]
                }
            else:
                self.subscriptions[websocket] = set()  # Empty = all events

            # Set up run filter
            if run_id:
                self.run_subscriptions[websocket] = {run_id}
            else:
                self.run_subscriptions[websocket] = set()  # Empty = all runs

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            self.active_connections.discard(websocket)
            self.subscriptions.pop(websocket, None)
            self.run_subscriptions.pop(websocket, None)

    def _should_send(self, websocket: WebSocket, event: BaseEvent) -> bool:
        """
        Check if an event should be sent to a connection.

        Args:
            websocket: Target connection
            event: Event to check

        Returns:
            True if event matches subscription filters
        """
        # Check event type filter
        type_filter = self.subscriptions.get(websocket, set())
        if type_filter and event.event_type not in type_filter:
            return False

        # Check run filter
        run_filter = self.run_subscriptions.get(websocket, set())
        if run_filter and event.run_id not in run_filter:
            return False

        return True

    async def send_event(self, websocket: WebSocket, event: BaseEvent) -> bool:
        """
        Send an event to a specific connection.

        Args:
            websocket: Target connection
            event: Event to send

        Returns:
            True if sent successfully
        """
        try:
            if self._should_send(websocket, event):
                await websocket.send_text(event_to_json(event))
                return True
        except Exception:
            # Connection likely closed
            await self.disconnect(websocket)
        return False

    async def broadcast(self, event: BaseEvent) -> int:
        """
        Broadcast an event to all matching connections.

        Args:
            event: Event to broadcast

        Returns:
            Number of connections that received the event
        """
        sent_count = 0

        # Copy to avoid modification during iteration
        connections = list(self.active_connections)

        for websocket in connections:
            if await self.send_event(websocket, event):
                sent_count += 1

        return sent_count

    async def send_json(self, websocket: WebSocket, data: dict[str, Any]) -> bool:
        """
        Send arbitrary JSON data to a connection.

        Args:
            websocket: Target connection
            data: Data to send

        Returns:
            True if sent successfully
        """
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            await self.disconnect(websocket)
            return False

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self.active_connections)

    def get_connection_info(self) -> dict[str, Any]:
        """Get information about current connections."""
        return {
            "total_connections": self.connection_count,
            "connections": [
                {
                    "event_filters": [
                        et.value for et in self.subscriptions.get(ws, set())
                    ],
                    "run_filters": list(self.run_subscriptions.get(ws, set())),
                }
                for ws in self.active_connections
            ],
        }


# Global connection manager instance
manager = ConnectionManager()


async def websocket_event_handler(event: BaseEvent) -> None:
    """
    Event handler for broadcasting events to WebSocket clients.

    This should be registered with the AsyncEventBus.

    Args:
        event: Event to broadcast
    """
    await manager.broadcast(event)


async def handle_websocket_connection(
    websocket: WebSocket,
    event_types: list[str] | None = None,
    run_id: str | None = None,
) -> None:
    """
    Handle a WebSocket connection lifecycle.

    Args:
        websocket: WebSocket connection
        event_types: Optional event type filter
        run_id: Optional run ID filter
    """
    await manager.connect(websocket, event_types, run_id)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "filters": {
                "event_types": event_types or "all",
                "run_id": run_id or "all",
            },
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (or keepalive)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")

                # Handle subscription updates
                elif data.startswith("{"):
                    msg = json.loads(data)
                    if msg.get("type") == "subscribe":
                        # Update filters
                        if "event_types" in msg:
                            async with manager._lock:
                                manager.subscriptions[websocket] = {
                                    EventType(et) for et in msg["event_types"]
                                }
                        if "run_id" in msg:
                            async with manager._lock:
                                manager.run_subscriptions[websocket] = {msg["run_id"]}

                        await websocket.send_json({"type": "subscribed"})

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
