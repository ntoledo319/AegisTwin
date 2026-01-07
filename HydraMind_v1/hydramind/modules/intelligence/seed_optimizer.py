"""
Adaptive learning rate optimizer using EWMA trend tracking.

Automatically adjusts learning rates based on loss trends to accelerate
convergence while avoiding divergence.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from ...core.module import Module
from ...core.bus import Message


@dataclass
class SeedState:
    """
    State for a single learner.
    
    Attributes:
        lr: Current learning rate
        floor: Minimum learning rate
        ceil: Maximum learning rate
        trend: EWMA of loss deltas (negative = improving)
    """
    lr: float = 1e-3
    floor: float = 1e-5
    ceil: float = 2e-2
    trend: float = 0.0


class SeedOptimizer(Module):
    """
    Adaptive learning rate optimizer.
    
    Monitors loss metrics and adjusts learning rates using EWMA trend analysis:
    - Increasing LR when loss is decreasing (improving)
    - Decreasing LR when loss is increasing (diverging)
    
    Protocol:
        Input events:
            - learn/seed/config: Configure learner (lr, floor, ceil)
            - learn/seed/metrics: Report loss for adjustment
        
        Output events:
            - learn/seed/ack: Acknowledge configuration
            - learn/seed/update: New LR recommendation
    
    Example:
        # Configure learner
        await bus.publish(Message("learn/seed/config", {
            "learner_id": "model_v1",
            "lr": 0.001,
            "floor": 0.00001,
            "ceil": 0.02
        }))
        
        # Report loss
        await bus.publish(Message("learn/seed/metrics", {
            "learner_id": "model_v1",
            "loss": 0.523
        }))
        
        # Receive update
        # -> learn/seed/update: {"learner_id": "model_v1", "lr": 0.00105, "trend": -0.02}
    """
    
    name = "seed"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        ema_alpha: float = 0.2,
        lr_down: float = 0.95,
        lr_up: float = 1.05
    ):
        """
        Initialize seed optimizer.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            ema_alpha: EWMA smoothing factor (0-1)
            lr_down: LR multiplier when diverging
            lr_up: LR multiplier when converging
        """
        super().__init__(bus, ex, policy)
        self.ema_alpha = ema_alpha
        self.lr_down = lr_down
        self.lr_up = lr_up
        self.state: Dict[str, SeedState] = {}
        
        self.log.info(
            f"SeedOptimizer initialized: alpha={ema_alpha}, "
            f"lr_down={lr_down}, lr_up={lr_up}"
        )
    
    def _get_state(self, learner_id: str) -> SeedState:
        """Get or create state for learner."""
        if learner_id not in self.state:
            self.state[learner_id] = SeedState()
            self.log.debug(f"Created state for learner '{learner_id}'")
        return self.state[learner_id]
    
    async def on_message(self, msg: Message) -> None:
        """Handle seed optimizer events."""
        
        if msg.topic == "learn/seed/config":
            await self._handle_config(msg)
        
        elif msg.topic == "learn/seed/metrics":
            await self._handle_metrics(msg)
    
    async def _handle_config(self, msg: Message) -> None:
        """Configure learner parameters."""
        learner_id = msg.data.get("learner_id")
        if not learner_id:
            self.log.warning("Config missing learner_id")
            return
        
        state = self._get_state(learner_id)
        
        # Update parameters
        if "lr" in msg.data:
            state.lr = float(msg.data["lr"])
        if "floor" in msg.data:
            state.floor = float(msg.data["floor"])
        if "ceil" in msg.data:
            state.ceil = float(msg.data["ceil"])
        
        self.log.info(
            f"Configured learner '{learner_id}': "
            f"lr={state.lr}, floor={state.floor}, ceil={state.ceil}"
        )
        
        await self.emit("learn/seed/ack", {
            "learner_id": learner_id,
            "lr": state.lr,
            "floor": state.floor,
            "ceil": state.ceil
        })
    
    async def _handle_metrics(self, msg: Message) -> None:
        """Process loss metrics and adjust learning rate."""
        learner_id = msg.data.get("learner_id")
        loss = msg.data.get("loss")
        
        if not learner_id or loss is None:
            self.log.warning("Metrics missing learner_id or loss")
            return
        
        loss = float(loss)
        state = self._get_state(learner_id)
        
        # Calculate loss delta (negative = improving)
        delta = -loss
        
        # Update trend using EWMA
        state.trend = (
            self.ema_alpha * delta +
            (1 - self.ema_alpha) * state.trend
        )
        
        # Adjust learning rate based on trend
        if state.trend > 0:
            # Loss decreasing - increase LR
            state.lr = min(state.ceil, state.lr * self.lr_up)
        else:
            # Loss increasing - decrease LR
            state.lr = max(state.floor, state.lr * self.lr_down)
        
        self.log.debug(
            f"Learner '{learner_id}': loss={loss:.4f}, "
            f"trend={state.trend:.4f}, lr={state.lr:.6f}"
        )
        
        await self.emit("learn/seed/update", {
            "learner_id": learner_id,
            "lr": state.lr,
            "trend": state.trend,
            "loss": loss
        })
    
    def get_stats(self) -> dict:
        """Get optimizer statistics."""
        stats = super().get_stats()
        stats.update({
            "learners": len(self.state),
            "ema_alpha": self.ema_alpha,
            "lr_down": self.lr_down,
            "lr_up": self.lr_up
        })
        return stats
