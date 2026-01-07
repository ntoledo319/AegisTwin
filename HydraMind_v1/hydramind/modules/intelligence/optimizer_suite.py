"""
Bottleneck detection and goal-based optimization scoring.

Analyzes system metrics to identify performance bottlenecks and
recommend optimization actions.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any, List
from ...core.module import Module
from ...core.bus import Message


@dataclass
class Goal:
    """
    Optimization goal with target and direction.
    
    Attributes:
        name: Goal name (matches metric key)
        target: Target value
        weight: Importance weight (higher = more important)
        direction: "min" or "max"
    """
    name: str
    target: float
    weight: float = 1.0
    direction: str = "min"  # or "max"
    
    def __post_init__(self):
        """Validate goal."""
        if self.direction not in ("min", "max"):
            raise ValueError("Direction must be 'min' or 'max'")
        if self.weight < 0:
            raise ValueError("Weight must be non-negative")


class OptimizerSuite(Module):
    """
    System optimization analyzer.
    
    Features:
    - Goal-based scoring (how far from optimal?)
    - Bottleneck detection (what's limiting performance?)
    - Action recommendations (what to do about it?)
    
    Protocol:
        Input events:
            - telemetry/host: System telemetry
            - optimizer/set_goal: Configure optimization goal
        
        Output events:
            - optimizer/recommendation: Optimization recommendations
            - optimizer/score: Current optimization score
    
    Example:
        # Configure custom goal
        await bus.publish(Message("optimizer/set_goal", {
            "name": "latency",
            "target": 10.0,
            "weight": 2.0,
            "direction": "min"
        }))
        
        # Telemetry automatically analyzed
        await bus.publish(Message("telemetry/host", {
            "cpu": 92.0,
            "mem": 85.0,
            "latency": 45.0
        }))
        
        # Receives recommendations
        # -> optimizer/recommendation: {
        #     "issues": ["cpu", "latency"],
        #     "actions": [{"type": "scale_threads", "delta": 2}],
        #     "score": 67.5
        # }
    """
    
    name = "optimizer"
    
    def __init__(
        self,
        bus,
        ex,
        policy,
        cpu_threshold: float = 90.0,
        mem_threshold: float = 92.0
    ):
        """
        Initialize optimizer suite.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            cpu_threshold: CPU bottleneck threshold (%)
            mem_threshold: Memory bottleneck threshold (%)
        """
        super().__init__(bus, ex, policy)
        
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        
        # Default goals
        self.goals: Dict[str, Goal] = {
            "cpu": Goal("cpu", target=85.0, weight=1.0, direction="min"),
            "mem": Goal("mem", target=90.0, weight=0.8, direction="min"),
        }
        
        self._recommendations_made = 0
        self._last_metrics: Dict[str, float] = {}
        
        self.log.info(
            f"OptimizerSuite initialized: "
            f"cpu_threshold={cpu_threshold}, mem_threshold={mem_threshold}"
        )
    
    def score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate optimization score.
        
        Lower score = better (closer to goals).
        
        Args:
            metrics: Current metrics
            
        Returns:
            Weighted penalty score
        """
        total_score = 0.0
        
        for goal in self.goals.values():
            value = metrics.get(goal.name)
            if value is None:
                continue
            
            # Calculate error from target
            if goal.direction == "min":
                error = max(0.0, value - goal.target)
            else:  # max
                error = max(0.0, goal.target - value)
            
            # Weighted penalty
            total_score += goal.weight * error
        
        return total_score
    
    def detect_bottlenecks(self, metrics: Dict[str, float]) -> List[str]:
        """
        Detect system bottlenecks.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of bottleneck names
        """
        bottlenecks = []
        
        # CPU bottleneck
        cpu = metrics.get("cpu", 0.0)
        if cpu > self.cpu_threshold:
            bottlenecks.append("cpu")
        
        # Memory bottleneck
        mem = metrics.get("mem", 0.0)
        if mem > self.mem_threshold:
            bottlenecks.append("mem")
        
        # Check custom goals
        for goal in self.goals.values():
            if goal.name in ("cpu", "mem"):
                continue  # Already checked
            
            value = metrics.get(goal.name)
            if value is None:
                continue
            
            # Check if significantly worse than target
            if goal.direction == "min":
                if value > goal.target * 1.2:  # 20% over target
                    bottlenecks.append(goal.name)
            else:  # max
                if value < goal.target * 0.8:  # 20% under target
                    bottlenecks.append(goal.name)
        
        return bottlenecks
    
    def recommend_actions(
        self,
        bottlenecks: List[str],
        metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Generate action recommendations.
        
        Args:
            bottlenecks: Detected bottlenecks
            metrics: Current metrics
            
        Returns:
            List of action recommendations
        """
        actions = []
        
        for bottleneck in bottlenecks:
            if bottleneck == "cpu":
                # High CPU - suggest scaling threads or reducing load
                cpu = metrics.get("cpu", 0.0)
                if cpu > 95:
                    actions.append({
                        "type": "critical",
                        "target": "cpu",
                        "action": "reduce_load",
                        "reason": f"CPU at {cpu:.1f}% (critical)"
                    })
                else:
                    actions.append({
                        "type": "scale_threads",
                        "target": "cpu",
                        "delta": -2,
                        "reason": f"CPU at {cpu:.1f}% (reduce threads)"
                    })
            
            elif bottleneck == "mem":
                # High memory - suggest GC or scaling
                mem = metrics.get("mem", 0.0)
                if mem > 95:
                    actions.append({
                        "type": "critical",
                        "target": "mem",
                        "action": "force_gc",
                        "reason": f"Memory at {mem:.1f}% (critical)"
                    })
                else:
                    actions.append({
                        "type": "gc_hint",
                        "target": "mem",
                        "reason": f"Memory at {mem:.1f}% (suggest GC)"
                    })
            
            else:
                # Custom bottleneck
                actions.append({
                    "type": "investigate",
                    "target": bottleneck,
                    "reason": f"Metric '{bottleneck}' exceeds target"
                })
        
        return actions
    
    async def on_message(self, msg: Message) -> None:
        """Handle optimizer events."""
        
        if msg.topic == "telemetry/host":
            await self._analyze_telemetry(msg)
        
        elif msg.topic == "optimizer/set_goal":
            await self._set_goal(msg)
        
        elif msg.topic == "optimizer/get_score":
            await self._report_score()
    
    async def _analyze_telemetry(self, msg: Message) -> None:
        """Analyze telemetry for optimization opportunities."""
        metrics = {
            "cpu": float(msg.data.get("cpu", 0.0)),
            "mem": float(msg.data.get("mem", 0.0))
        }
        
        # Include custom metrics
        for key, value in msg.data.items():
            if key not in ("cpu", "mem", "ts") and isinstance(value, (int, float)):
                metrics[key] = float(value)
        
        self._last_metrics = metrics
        
        # Calculate score
        score = self.score(metrics)
        
        # Detect bottlenecks
        bottlenecks = self.detect_bottlenecks(metrics)
        
        # Generate recommendations if bottlenecks found
        if bottlenecks:
            actions = self.recommend_actions(bottlenecks, metrics)
            self._recommendations_made += 1
            
            self.log.info(
                f"Optimization needed: score={score:.2f}, "
                f"bottlenecks={bottlenecks}"
            )
            
            await self.emit("optimizer/recommendation", {
                "issues": bottlenecks,
                "actions": actions,
                "score": score,
                "metrics": metrics,
                "ts": time.time()
            })
        
        # Always emit score for monitoring
        await self.emit("optimizer/score", {
            "score": score,
            "metrics": metrics,
            "ts": time.time()
        })
    
    async def _set_goal(self, msg: Message) -> None:
        """Configure optimization goal."""
        try:
            goal = Goal(
                name=msg.data["name"],
                target=float(msg.data["target"]),
                weight=float(msg.data.get("weight", 1.0)),
                direction=msg.data.get("direction", "min")
            )
            
            self.goals[goal.name] = goal
            
            self.log.info(
                f"Set goal '{goal.name}': target={goal.target}, "
                f"weight={goal.weight}, direction={goal.direction}"
            )
            
            await self.emit("optimizer/goal_set", {
                "name": goal.name,
                "target": goal.target,
                "weight": goal.weight,
                "direction": goal.direction
            })
        
        except Exception as e:
            self.log.error(f"Failed to set goal: {e}")
    
    async def _report_score(self) -> None:
        """Report current optimization score."""
        if self._last_metrics:
            score = self.score(self._last_metrics)
            await self.emit("optimizer/score", {
                "score": score,
                "metrics": self._last_metrics,
                "ts": time.time()
            })
    
    def get_stats(self) -> dict:
        """Get optimizer statistics."""
        stats = super().get_stats()
        
        goal_stats = {
            name: {
                "target": goal.target,
                "weight": goal.weight,
                "direction": goal.direction
            }
            for name, goal in self.goals.items()
        }
        
        stats.update({
            "cpu_threshold": self.cpu_threshold,
            "mem_threshold": self.mem_threshold,
            "goals": len(self.goals),
            "recommendations_made": self._recommendations_made,
            "current_score": self.score(self._last_metrics) if self._last_metrics else None,
            "goal_config": goal_stats
        })
        
        return stats
