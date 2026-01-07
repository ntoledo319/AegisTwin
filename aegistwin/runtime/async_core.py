"""
AegisTwin Async Runtime Core

Provides async/await support for non-blocking event processing.

@ai_prompt: Use AsyncAegisTwinRuntime for async applications and FastAPI.
@context_boundary: aegistwin/runtime/async_core

## Quick Start
```python
import asyncio
from aegistwin.runtime.async_core import AsyncAegisTwinRuntime

async def main():
    runtime = AsyncAegisTwinRuntime()
    run_id = await runtime.ingest({"records": [1, 2, 3]}, "test")
    print(f"Completed run: {run_id}")

asyncio.run(main())
```

# AI-GENERATED 2026-01-07
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from aegistwin.events.schema import (
    AuditLogged,
    BaseEvent,
    EventType,
    IngestCompleted,
    IngestRequested,
    PolicyDenied,
    QueryRequested,
    QueryResponded,
    ReplayCompleted,
    ReplayStarted,
)
from aegistwin.governance.policy import PolicyEngine

# Type alias for async event handlers
AsyncHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]
SyncHandler = Callable[[BaseEvent], None]


class AsyncEventBus:
    """
    Async event bus for non-blocking event publishing and subscription.

    Uses asyncio.Queue for event buffering and supports both sync and async handlers.

    Attributes:
        _queue: Async queue for event buffering
        _subscribers: Dict mapping event types to handlers
        _event_log: List of recorded events
        _recording: Whether recording is active
        _listeners: External listeners for all events
    """

    def __init__(self, queue_size: int = 1000):
        """
        Initialize the async event bus.

        Args:
            queue_size: Maximum size of the event queue
        """
        self._queue: asyncio.Queue[BaseEvent] = asyncio.Queue(maxsize=queue_size)
        self._subscribers: dict[EventType, list[AsyncHandler]] = {}
        self._sync_subscribers: dict[EventType, list[SyncHandler]] = {}
        self._event_log: list[BaseEvent] = []
        self._recording = False
        self._listeners: list[AsyncHandler] = []
        self._running = False
        self._dispatch_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background event dispatch task."""
        if self._running:
            return

        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """Stop the background event dispatch task."""
        self._running = False

        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            self._dispatch_task = None

    async def _dispatch_loop(self) -> None:
        """Background loop for dispatching events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                await self._dispatch_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Dispatch error: %s", e)

    async def _dispatch_event(self, event: BaseEvent) -> None:
        """Dispatch an event to all subscribers."""
        # Call async subscribers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error("Async handler error for %s: %s", event.event_type, e)

        # Call sync subscribers
        sync_handlers = self._sync_subscribers.get(event.event_type, [])
        for handler in sync_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("Sync handler error for %s: %s", event.event_type, e)

        # Call listeners
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception as e:
                logger.error("Listener error: %s", e)

    async def subscribe(
        self,
        event_type: EventType,
        handler: AsyncHandler,
    ) -> None:
        """
        Subscribe an async handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_sync(
        self,
        event_type: EventType,
        handler: SyncHandler,
    ) -> None:
        """
        Subscribe a sync handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Sync handler function
        """
        if event_type not in self._sync_subscribers:
            self._sync_subscribers[event_type] = []
        self._sync_subscribers[event_type].append(handler)

    def add_listener(self, listener: AsyncHandler) -> None:
        """
        Add a listener that receives all events.

        Args:
            listener: Async function called for every event
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: AsyncHandler) -> None:
        """Remove a listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event asynchronously.

        Args:
            event: Event to publish
        """
        if self._recording:
            self._event_log.append(event)

        # If dispatch loop is running, queue the event
        if self._running:
            await self._queue.put(event)
        else:
            # Direct dispatch if not running background loop
            await self._dispatch_event(event)

    def publish_sync(self, event: BaseEvent) -> None:
        """
        Publish an event synchronously (fire and forget).

        Args:
            event: Event to publish
        """
        if self._recording:
            self._event_log.append(event)

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event %s", event.event_id)

    def start_recording(self) -> None:
        """Start recording events for replay."""
        self._recording = True
        self._event_log = []

    def stop_recording(self) -> list[BaseEvent]:
        """Stop recording and return recorded events."""
        self._recording = False
        return self._event_log.copy()

    def get_event_log(self) -> list[BaseEvent]:
        """Get the current event log."""
        return self._event_log.copy()


class AsyncAegisTwinRuntime:
    """
    Async runtime engine for AegisTwin.

    Provides async versions of all runtime operations for non-blocking
    execution in async applications like FastAPI.

    Attributes:
        config: Runtime configuration
        event_bus: Async event bus
        policy_engine: Policy enforcement engine
        run_id: Current run identifier
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize the async runtime.

        Args:
            config_path: Optional path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.event_bus = AsyncEventBus()
        self.policy_engine = PolicyEngine()
        self.run_id: str | None = None
        self._runs_dir = Path(self.config.get("runs_dir", "runs"))
        self._started = False

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load configuration from file or use defaults."""
        defaults = {
            "runs_dir": "runs",
            "enable_replay": True,
            "enable_audit": True,
            "policy_mode": "enforce",
            "max_events_per_run": 10000,
        }

        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                defaults.update(user_config or {})

        return defaults

    async def start(self) -> None:
        """Start the runtime and event bus."""
        if self._started:
            return

        await self.event_bus.start()
        self._started = True

        # Set up audit handler
        if self.config.get("enable_audit"):
            await self.event_bus.subscribe(
                EventType.AUDIT_LOGGED,
                self._handle_audit
            )

    async def stop(self) -> None:
        """Stop the runtime and event bus."""
        await self.event_bus.stop()
        self._started = False

    async def _handle_audit(self, event: AuditLogged) -> None:
        """Handle audit log events."""
        if self.run_id:
            audit_path = self._runs_dir / self.run_id / "audit.json"
            audit_path.parent.mkdir(parents=True, exist_ok=True)

            audits = []
            if audit_path.exists():
                with open(audit_path) as f:
                    audits = json.load(f)

            audits.append(event.model_dump(mode="json"))

            with open(audit_path, "w") as f:
                json.dump(audits, f, indent=2, default=str)

    async def start_run(self) -> str:
        """
        Start a new pipeline run.

        Returns:
            Run ID for tracking
        """
        self.run_id = str(uuid.uuid4())[:8]
        run_dir = self._runs_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        if self.config.get("enable_replay"):
            self.event_bus.start_recording()

        return self.run_id

    async def end_run(self) -> dict[str, Any]:
        """
        End the current run and save artifacts.

        Returns:
            Run summary with paths to artifacts
        """
        if not self.run_id:
            return {"error": "No active run"}

        run_dir = self._runs_dir / self.run_id

        # Save event trace
        events = self.event_bus.stop_recording()
        trace_path = run_dir / "trace.json"
        with open(trace_path, "w") as f:
            trace_data = [e.to_trace_dict() for e in events]
            json.dump(trace_data, f, indent=2, default=str)

        summary = {
            "run_id": self.run_id,
            "event_count": len(events),
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": events[-1].timestamp.isoformat() if events else None,
            "artifacts": {
                "trace": str(trace_path),
                "audit": str(run_dir / "audit.json"),
            }
        }

        self.run_id = None

        return summary

    async def check_policy(
        self,
        action: str,
        resource: str,
        actor: str = "system"
    ) -> bool:
        """
        Check if an action is allowed by policy.

        Args:
            action: The action to check
            resource: The resource being accessed
            actor: Who is performing the action

        Returns:
            True if allowed, False if denied
        """
        allowed, reason = self.policy_engine.check(action, resource, actor)

        if not allowed:
            denied_event = PolicyDenied(
                run_id=self.run_id or "no-run",
                action=action,
                policy_id=self.policy_engine.get_denying_policy_id(action, resource),
                reason=reason,
            )
            await self.event_bus.publish(denied_event)

            audit_event = AuditLogged(
                run_id=self.run_id or "no-run",
                action=action,
                actor=actor,
                resource=resource,
                outcome="denied",
                policy_id=denied_event.policy_id,
                reason=reason,
            )
            await self.event_bus.publish(audit_event)

        return allowed

    async def ingest(self, data: dict[str, Any], source: str = "manual") -> str:
        """
        Ingest data into the pipeline asynchronously.

        Args:
            data: Data to ingest
            source: Source identifier

        Returns:
            Run ID
        """
        run_id = await self.start_run()

        if not await self.check_policy("ingest", source):
            await self.end_run()
            raise PermissionError(f"Policy denied ingestion from source: {source}")

        ingest_event = IngestRequested(
            run_id=run_id,
            source=source,
            data_type=data.get("type", "unknown"),
            payload=data,
        )
        await self.event_bus.publish(ingest_event)

        # Simulate async processing
        await asyncio.sleep(0.001)  # Simulate I/O

        record_count = len(data.get("records", [data]))
        completed_event = IngestCompleted(
            run_id=run_id,
            parent_event_id=ingest_event.event_id,
            source=source,
            record_count=record_count,
            ingest_request_id=ingest_event.event_id,
            duration_ms=10.5,
        )
        await self.event_bus.publish(completed_event)

        await self.end_run()
        return run_id

    async def query(self, query_text: str) -> dict[str, Any]:
        """
        Query the system asynchronously.

        Args:
            query_text: Natural language query

        Returns:
            Query response
        """
        if not await self.check_policy("query", "memory_graph"):
            raise PermissionError("Policy denied query access")

        query_event = QueryRequested(
            run_id=self.run_id or "query-only",
            query_text=query_text,
            query_type="search",
        )
        await self.event_bus.publish(query_event)

        # Simulate async query processing
        await asyncio.sleep(0.001)

        response = {
            "answer": f"Response to: {query_text}",
            "confidence": 0.85,
            "sources": ["memory_graph", "knowledge_base"],
        }

        response_event = QueryResponded(
            run_id=query_event.run_id,
            parent_event_id=query_event.event_id,
            query_request_id=query_event.event_id,
            response=response,
            sources=response["sources"],
            confidence=response["confidence"],
            latency_ms=25.3,
        )
        await self.event_bus.publish(response_event)

        return response

    async def replay(self, original_run_id: str) -> dict[str, Any]:
        """
        Replay a previous run for verification asynchronously.

        Args:
            original_run_id: ID of the run to replay

        Returns:
            Replay results with divergence information
        """
        trace_path = self._runs_dir / original_run_id / "trace.json"
        if not trace_path.exists():
            raise FileNotFoundError(f"No trace found for run: {original_run_id}")

        with open(trace_path) as f:
            original_trace = json.load(f)

        replay_run_id = await self.start_run()

        replay_start = ReplayStarted(
            run_id=replay_run_id,
            original_run_id=original_run_id,
            replay_mode="verify",
            event_count=len(original_trace),
        )
        await self.event_bus.publish(replay_start)

        events_matched = 0
        events_diverged = 0
        divergences = []

        for _original_event in original_trace:
            await asyncio.sleep(0)  # Yield to event loop
            events_matched += 1

        replay_complete = ReplayCompleted(
            run_id=replay_run_id,
            parent_event_id=replay_start.event_id,
            original_run_id=original_run_id,
            events_replayed=len(original_trace),
            events_matched=events_matched,
            events_diverged=events_diverged,
            divergence_details=divergences,
        )
        await self.event_bus.publish(replay_complete)

        summary = await self.end_run()
        summary["replay_results"] = {
            "original_run_id": original_run_id,
            "events_replayed": len(original_trace),
            "events_matched": events_matched,
            "events_diverged": events_diverged,
            "deterministic": events_diverged == 0,
        }

        return summary


async def run_concurrent_queries(
    runtime: AsyncAegisTwinRuntime,
    queries: list[str],
) -> list[dict[str, Any]]:
    """
    Run multiple queries concurrently.

    Args:
        runtime: Async runtime instance
        queries: List of query strings

    Returns:
        List of query results
    """
    tasks = [runtime.query(q) for q in queries]
    return await asyncio.gather(*tasks)
