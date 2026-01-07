"""
Sensor data hub with ring buffer integration.

Demonstrates high-frequency data acquisition pattern using shared memory
and caching. This is an EXAMPLE - adapt for your sensors/telemetry.
"""

from __future__ import annotations
import asyncio
import psutil
import time
import json
from ...core.module import Module
from ...core.bus import Message
from ...core.data import RingBuffer, MMapSnapshot, TTLCache


class SensorHub(Module):
    """
    Example sensor hub for telemetry acquisition.
    
    Features:
    - High-frequency data production to ring buffer
    - Memory-mapped snapshots for instant state access
    - TTL cache for recent readings
    - Async consumption and event emission
    
    This is a TEMPLATE - replace with your actual sensor integration:
    - IoT device readings
    - Camera frames
    - LiDAR point clouds
    - Network metrics
    - Industrial sensors
    - etc.
    """
    
    name = "sensors"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        ring: RingBuffer,
        snap: MMapSnapshot,
        cache: TTLCache,
        produce_interval: float = 0.05,
        consume_interval: float = 0.01
    ):
        """
        Initialize sensor hub.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            ring: Ring buffer for high-frequency data
            snap: Memory-mapped snapshot file
            cache: TTL cache for recent readings
            produce_interval: Data production interval (seconds)
            consume_interval: Data consumption interval (seconds)
        """
        super().__init__(bus, ex, policy)
        self.ring = ring
        self.snap = snap
        self.cache = cache
        self.produce_interval = produce_interval
        self.consume_interval = consume_interval
        
        self.tail = 0  # Read position in ring buffer
        self._produce_task = None
        self._consume_task = None
        
        self.log.info(
            f"SensorHub initialized: "
            f"produce={produce_interval}s, consume={consume_interval}s"
        )
    
    async def start(self) -> None:
        """Start sensor acquisition loops."""
        await super().start()
        self._produce_task = asyncio.create_task(self._produce_loop())
        self._consume_task = asyncio.create_task(self._consume_loop())
    
    async def stop(self) -> None:
        """Stop sensor acquisition."""
        if self._produce_task and not self._produce_task.done():
            self._produce_task.cancel()
            try:
                await self._produce_task
            except asyncio.CancelledError:
                pass
        
        if self._consume_task and not self._consume_task.done():
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
    
    async def _produce_loop(self) -> None:
        """
        Producer: Acquire sensor data and write to ring buffer.
        
        REPLACE THIS with your actual sensor reading logic!
        """
        while self._running:
            try:
                # EXAMPLE: Read system metrics
                # REPLACE with: camera.read(), lidar.scan(), sensor.read(), etc.
                payload = {
                    "cpu": psutil.cpu_percent(interval=0.01),
                    "mem": psutil.virtual_memory().percent,
                    "ts": time.time(),
                    "source": "system"
                }
                
                # Write to ring buffer (shared memory, zero-copy)
                data_bytes = json.dumps(payload).encode("utf-8")
                self.ring.write_bytes(data_bytes)
                
                # Update snapshot (memory-mapped, instant persistence)
                snap_data = {
                    "ts": time.time(),
                    "latest": payload
                }
                self.snap.write_json(json.dumps(snap_data).encode("utf-8"))
                
                await asyncio.sleep(self.produce_interval)
                
            except Exception as e:
                self.log.error(f"Producer error: {e}")
                await asyncio.sleep(self.produce_interval)
    
    async def _consume_loop(self) -> None:
        """
        Consumer: Read from ring buffer and emit events.
        """
        while self._running:
            try:
                # Read new items from ring buffer
                items, self.tail = self.ring.read_snapshot(self.tail, max_items=256)
                
                for raw_bytes in items:
                    try:
                        # Decode sensor reading
                        obj = json.loads(raw_bytes.decode("utf-8"))
                        
                        # Cache recent reading
                        self.cache.set("telemetry/last", obj, ttl=1.0)
                        
                        # Emit to event bus for processing
                        await self.emit("telemetry/host", obj)
                        
                    except json.JSONDecodeError as e:
                        self.log.warning(f"Invalid JSON in ring buffer: {e}")
                    except Exception as e:
                        self.log.error(f"Consumer processing error: {e}")
                
                await asyncio.sleep(self.consume_interval)
                
            except Exception as e:
                self.log.error(f"Consumer error: {e}")
                await asyncio.sleep(self.consume_interval)
    
    async def on_message(self, msg: Message) -> None:
        """Handle sensor queries."""
        if msg.topic == "sensors/get_last":
            # Retrieve cached last reading
            value = self.cache.get("telemetry/last")
            
            await self.emit("sensors/last", {
                "value": value,
                "cached": value is not None,
                "ts": time.time()
            })
        
        elif msg.topic == "sensors/get_snapshot":
            # Read from memory-mapped snapshot
            try:
                snap_bytes = self.snap.read_bytes()
                snap_data = json.loads(snap_bytes.decode("utf-8"))
                
                await self.emit("sensors/snapshot", snap_data)
                
            except Exception as e:
                self.log.error(f"Failed to read snapshot: {e}")
    
    def get_stats(self) -> dict:
        """Get sensor hub statistics."""
        stats = super().get_stats()
        stats.update({
            "ring_buffer": self.ring.get_stats(),
            "cache": self.cache.get_stats(),
            "tail_position": self.tail,
            "produce_interval": self.produce_interval,
            "consume_interval": self.consume_interval
        })
        return stats
