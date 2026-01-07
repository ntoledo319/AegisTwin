"""
Priority-based experience replay buffer.

Stores and samples experiences for reinforcement learning, with priority-based
sampling to focus on important experiences.
"""

from __future__ import annotations
import heapq
import time
import logging
from typing import Dict, List, Tuple, Any
from ...core.module import Module
from ...core.bus import Message


class ReplayService(Module):
    """
    Priority replay buffer for experience replay.
    
    Stores experiences with priorities and samples high-priority items
    for training. Uses a max-heap to efficiently track top experiences.
    
    Protocol:
        Input events:
            - replay/store: Store experience with priority
            - replay/sample: Sample top-K experiences
        
        Output events:
            - replay/samples: Return sampled experiences
    
    Example:
        # Store important experience
        await bus.publish(Message("replay/store", {
            "topic": "training_data",
            "data": {"state": [...], "action": 2, "reward": 1.5},
            "priority": 1.5  # Higher = more important
        }))
        
        # Sample for training
        await bus.publish(Message("replay/sample", {
            "topic": "training_data",
            "k": 64
        }))
        
        # Receive samples
        # -> replay/samples: {"topic": "training_data", "items": [...]}
    """
    
    name = "replay"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        capacity: int = 200_000
    ):
        """
        Initialize replay buffer.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            capacity: Maximum experiences per topic
        """
        super().__init__(bus, ex, policy)
        self.capacity = capacity
        
        # Separate buffer per topic
        # Each buffer is a max-heap: [(-priority, {"ts": ..., "data": ...})]
        self.buffers: Dict[str, List[Tuple[float, dict]]] = {}
        
        self._total_stored = 0
        self._total_sampled = 0
        
        self.log.info(f"ReplayService initialized: capacity={capacity}")
    
    def _get_buffer(self, topic: str) -> List[Tuple[float, dict]]:
        """Get or create buffer for topic."""
        if topic not in self.buffers:
            self.buffers[topic] = []
            self.log.debug(f"Created replay buffer for topic '{topic}'")
        return self.buffers[topic]
    
    async def on_message(self, msg: Message) -> None:
        """Handle replay service events."""
        
        if msg.topic == "replay/store":
            await self._handle_store(msg)
        
        elif msg.topic == "replay/sample":
            await self._handle_sample(msg)
        
        elif msg.topic == "replay/clear":
            await self._handle_clear(msg)
    
    async def _handle_store(self, msg: Message) -> None:
        """Store experience in replay buffer."""
        topic = msg.data.get("topic")
        data = msg.data.get("data")
        priority = float(msg.data.get("priority", 0.0))
        
        if not topic or data is None:
            self.log.warning("Store missing topic or data")
            return
        
        buffer = self._get_buffer(topic)
        
        # Create experience item
        item = {
            "ts": time.time(),
            "data": data
        }
        
        # Store with negative priority (max-heap)
        heapq.heappush(buffer, (-priority, item))
        self._total_stored += 1
        
        # Enforce capacity limit
        if len(buffer) > self.capacity:
            heapq.heappop(buffer)  # Remove lowest priority
        
        self.log.debug(
            f"Stored experience in '{topic}': "
            f"priority={priority:.3f}, buffer_size={len(buffer)}"
        )
    
    async def _handle_sample(self, msg: Message) -> None:
        """Sample top-K experiences from buffer."""
        topic = msg.data.get("topic")
        k = int(msg.data.get("k", 64))
        
        if not topic:
            self.log.warning("Sample missing topic")
            return
        
        buffer = self._get_buffer(topic)
        
        if not buffer:
            self.log.debug(f"No experiences in buffer '{topic}'")
            await self.emit("replay/samples", {
                "topic": topic,
                "items": [],
                "requested": k,
                "available": 0
            })
            return
        
        # Sample top-K items (without removing from buffer)
        # Create a copy of heap to preserve original
        buffer_copy = list(buffer)
        heapq.heapify(buffer_copy)
        
        items = []
        for _ in range(min(k, len(buffer_copy))):
            neg_priority, item = heapq.heappop(buffer_copy)
            items.append(item)
        
        self._total_sampled += len(items)
        
        self.log.debug(
            f"Sampled {len(items)}/{k} experiences from '{topic}'"
        )
        
        await self.emit("replay/samples", {
            "topic": topic,
            "items": items,
            "requested": k,
            "available": len(buffer)
        })
    
    async def _handle_clear(self, msg: Message) -> None:
        """Clear replay buffer for topic."""
        topic = msg.data.get("topic")
        
        if not topic:
            self.log.warning("Clear missing topic")
            return
        
        if topic == "*":
            # Clear all buffers
            count = sum(len(buf) for buf in self.buffers.values())
            self.buffers.clear()
            self.log.info(f"Cleared all replay buffers ({count} experiences)")
        
        elif topic in self.buffers:
            count = len(self.buffers[topic])
            del self.buffers[topic]
            self.log.info(f"Cleared buffer '{topic}' ({count} experiences)")
        
        else:
            self.log.debug(f"Buffer '{topic}' does not exist")
    
    def get_stats(self) -> dict:
        """Get replay buffer statistics."""
        stats = super().get_stats()
        
        buffer_stats = {
            topic: len(buf)
            for topic, buf in self.buffers.items()
        }
        
        stats.update({
            "capacity": self.capacity,
            "topics": len(self.buffers),
            "total_experiences": sum(buffer_stats.values()),
            "total_stored": self._total_stored,
            "total_sampled": self._total_sampled,
            "buffers": buffer_stats
        })
        
        return stats
