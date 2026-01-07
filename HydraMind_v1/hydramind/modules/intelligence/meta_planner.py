"""
Meta-learning planner using Upper Confidence Bound (UCB) bandit algorithm.

Selects between multiple strategies/experiments and learns which ones
perform best over time.
"""

from __future__ import annotations
import math
import time
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List
from ...core.module import Module
from ...core.bus import Message


@dataclass
class Arm:
    """
    Bandit arm representing a strategy/plan.
    
    Attributes:
        id: Arm identifier
        pulls: Number of times selected
        reward_sum: Cumulative reward
        metadata: Optional metadata about this arm
    """
    id: str
    pulls: int = 0
    reward_sum: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def mean_reward(self) -> float:
        """Calculate mean reward."""
        return self.reward_sum / max(1, self.pulls)


class UCB:
    """
    Upper Confidence Bound (UCB1) bandit algorithm.
    
    Balances exploration vs exploitation by:
    - Selecting arms with high estimated reward (exploitation)
    - Adding bonus for under-explored arms (exploration)
    """
    
    def __init__(self, exploration_factor: float = math.sqrt(2)):
        """
        Initialize UCB selector.
        
        Args:
            exploration_factor: Controls exploration vs exploitation balance
        """
        self.exploration_factor = exploration_factor
    
    def select(self, arms: Dict[str, Arm]) -> str:
        """
        Select arm using UCB1 algorithm.
        
        Args:
            arms: Available arms
            
        Returns:
            Selected arm ID
        """
        if not arms:
            raise ValueError("No arms available")
        
        total_pulls = sum(arm.pulls for arm in arms.values())
        
        # Force exploration of unplayed arms
        for arm_id, arm in arms.items():
            if arm.pulls == 0:
                return arm_id
        
        # UCB selection
        best_id = None
        best_score = float('-inf')
        
        for arm_id, arm in arms.items():
            # Mean reward + exploration bonus
            exploitation = arm.mean_reward
            exploration = self.exploration_factor * math.sqrt(
                math.log(total_pulls + 1) / (arm.pulls + 1e-9)
            )
            
            ucb_score = exploitation + exploration
            
            if ucb_score > best_score:
                best_id = arm_id
                best_score = ucb_score
        
        return best_id


class MetaPlanner(Module):
    """
    Experiment manager and strategy selector using bandit algorithms.
    
    Automatically learns which strategies/plans work best and selects
    them more often. Useful for:
    - A/B testing different approaches
    - Adaptive algorithm selection
    - Hyperparameter optimization
    - Strategy evolution
    
    Protocol:
        Input events:
            - meta/choose_plan: Request strategy selection
            - meta/feedback: Provide reward for selected strategy
            - meta/add_arm: Add new strategy
            - meta/remove_arm: Remove strategy
        
        Output events:
            - meta/plan: Selected strategy
            - meta/updated: Arm stats updated
    
    Example:
        # Add strategies
        await bus.publish(Message("meta/add_arm", {
            "arm_id": "greedy_v1",
            "metadata": {"algorithm": "greedy", "version": 1}
        }))
        
        await bus.publish(Message("meta/add_arm", {
            "arm_id": "epsilon_v1",
            "metadata": {"algorithm": "epsilon", "version": 1}
        }))
        
        # Request strategy selection
        await bus.publish(Message("meta/choose_plan", {}))
        
        # -> meta/plan: {"choice": "greedy_v1", ...}
        
        # Provide feedback after execution
        await bus.publish(Message("meta/feedback", {
            "arm": "greedy_v1",
            "reward": 0.85  # Normalized reward (0-1 or any scale)
        }))
    """
    
    name = "meta_planner"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        exploration_factor: float = math.sqrt(2),
        default_arms: int = 3
    ):
        """
        Initialize meta planner.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            exploration_factor: UCB exploration parameter
            default_arms: Number of default arms to create
        """
        super().__init__(bus, ex, policy)
        
        self.ucb = UCB(exploration_factor)
        self.arms: Dict[str, Arm] = {}
        
        # Create default arms
        for i in range(default_arms):
            arm_id = f"plan_{i}"
            self.arms[arm_id] = Arm(
                id=arm_id,
                metadata={"default": True, "index": i}
            )
        
        self._selections_made = 0
        self._total_reward = 0.0
        
        self.log.info(
            f"MetaPlanner initialized: exploration_factor={exploration_factor}, "
            f"default_arms={default_arms}"
        )
    
    async def on_message(self, msg: Message) -> None:
        """Handle meta planner events."""
        
        if msg.topic == "meta/choose_plan":
            await self._choose_plan(msg)
        
        elif msg.topic == "meta/feedback":
            await self._handle_feedback(msg)
        
        elif msg.topic == "meta/add_arm":
            await self._add_arm(msg)
        
        elif msg.topic == "meta/remove_arm":
            await self._remove_arm(msg)
        
        elif msg.topic == "meta/get_stats":
            await self._report_stats()
    
    async def _choose_plan(self, msg: Message) -> None:
        """Select strategy using UCB."""
        if not self.arms:
            self.log.warning("No arms available for selection")
            return
        
        try:
            choice = self.ucb.select(self.arms)
            arm = self.arms[choice]
            
            self._selections_made += 1
            
            self.log.debug(
                f"Selected arm '{choice}': "
                f"pulls={arm.pulls}, mean_reward={arm.mean_reward:.3f}"
            )
            
            await self.emit("meta/plan", {
                "choice": choice,
                "pulls": arm.pulls,
                "mean_reward": arm.mean_reward,
                "metadata": arm.metadata,
                "ts": time.time()
            })
        
        except Exception as e:
            self.log.error(f"Failed to choose plan: {e}")
    
    async def _handle_feedback(self, msg: Message) -> None:
        """Process reward feedback."""
        arm_id = msg.data.get("arm")
        reward = msg.data.get("reward")
        
        if not arm_id or reward is None:
            self.log.warning("Feedback missing arm or reward")
            return
        
        if arm_id not in self.arms:
            self.log.warning(f"Unknown arm '{arm_id}'")
            return
        
        try:
            reward = float(reward)
            arm = self.arms[arm_id]
            
            # Update arm statistics
            arm.pulls += 1
            arm.reward_sum += reward
            self._total_reward += reward
            
            self.log.debug(
                f"Feedback for arm '{arm_id}': reward={reward:.3f}, "
                f"pulls={arm.pulls}, mean={arm.mean_reward:.3f}"
            )
            
            await self.emit("meta/updated", {
                "arm": arm_id,
                "pulls": arm.pulls,
                "reward_sum": arm.reward_sum,
                "mean_reward": arm.mean_reward,
                "ts": time.time()
            })
        
        except Exception as e:
            self.log.error(f"Failed to process feedback: {e}")
    
    async def _add_arm(self, msg: Message) -> None:
        """Add new arm/strategy."""
        arm_id = msg.data.get("arm_id")
        metadata = msg.data.get("metadata", {})
        
        if not arm_id:
            self.log.warning("Add arm missing arm_id")
            return
        
        if arm_id in self.arms:
            self.log.warning(f"Arm '{arm_id}' already exists")
            return
        
        self.arms[arm_id] = Arm(id=arm_id, metadata=metadata)
        
        self.log.info(f"Added arm '{arm_id}' with metadata: {metadata}")
        
        await self.emit("meta/arm_added", {
            "arm": arm_id,
            "metadata": metadata,
            "ts": time.time()
        })
    
    async def _remove_arm(self, msg: Message) -> None:
        """Remove arm/strategy."""
        arm_id = msg.data.get("arm_id")
        
        if not arm_id:
            self.log.warning("Remove arm missing arm_id")
            return
        
        if arm_id not in self.arms:
            self.log.warning(f"Arm '{arm_id}' does not exist")
            return
        
        del self.arms[arm_id]
        
        self.log.info(f"Removed arm '{arm_id}'")
        
        await self.emit("meta/arm_removed", {
            "arm": arm_id,
            "ts": time.time()
        })
    
    async def _report_stats(self) -> None:
        """Report meta planner statistics."""
        arm_stats = {
            arm_id: {
                "pulls": arm.pulls,
                "reward_sum": arm.reward_sum,
                "mean_reward": arm.mean_reward,
                "metadata": arm.metadata
            }
            for arm_id, arm in self.arms.items()
        }
        
        # Find best arm
        best_arm = max(
            self.arms.items(),
            key=lambda x: x[1].mean_reward,
            default=(None, None)
        )[0]
        
        await self.emit("meta/stats", {
            "arms": len(self.arms),
            "selections": self._selections_made,
            "total_reward": self._total_reward,
            "best_arm": best_arm,
            "arm_stats": arm_stats,
            "ts": time.time()
        })
    
    def get_stats(self) -> dict:
        """Get meta planner statistics."""
        stats = super().get_stats()
        
        arm_stats = {}
        for arm_id, arm in self.arms.items():
            arm_stats[arm_id] = {
                "pulls": arm.pulls,
                "reward_sum": arm.reward_sum,
                "mean_reward": arm.mean_reward
            }
        
        # Calculate best arm
        best_arm = None
        best_reward = float('-inf')
        for arm_id, arm in self.arms.items():
            if arm.pulls > 0 and arm.mean_reward > best_reward:
                best_arm = arm_id
                best_reward = arm.mean_reward
        
        stats.update({
            "exploration_factor": self.ucb.exploration_factor,
            "arms": len(self.arms),
            "selections": self._selections_made,
            "total_reward": self._total_reward,
            "best_arm": best_arm,
            "best_mean_reward": best_reward if best_arm else None,
            "arm_stats": arm_stats
        })
        
        return stats
