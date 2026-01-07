"""
Example domain modules demonstrating HydraMind patterns.

These are TEMPLATES - delete and replace with your actual domain logic!
"""

from __future__ import annotations
import asyncio
import time
from ...core.module import Module
from ...core.bus import Message


class DroneFleet(Module):
    """
    Example drone swarm coordinator.
    
    This is a TEMPLATE - replace with your actual drone control logic:
    - Real drone communication (MAVLink, etc)
    - Formation flying algorithms
    - Path planning and collision avoidance
    - Mission management
    
    Shows: Simple request-response pattern
    """
    
    name = "drone_fleet"
    
    async def on_message(self, msg: Message) -> None:
        """Handle drone commands."""
        if msg.topic == "drone/command":
            drone_id = msg.data.get("drone_id")
            action = msg.data.get("action")
            
            # EXAMPLE: Simulate command processing
            await asyncio.sleep(0.01)
            
            # EXAMPLE: Acknowledge command
            await self.emit("drone/ack", {
                "drone_id": drone_id,
                "action": action,
                "ok": True,
                "ts": time.time()
            })
            
            self.log.debug(f"Drone {drone_id} executed: {action}")


class RoboticsCell(Module):
    """
    Example manufacturing robotics cell.
    
    This is a TEMPLATE - replace with your actual robotics control:
    - Robot arm control (ROS, custom protocols)
    - Computer vision integration
    - Pick-and-place operations
    - Quality inspection
    
    Shows: Job-based task execution
    """
    
    name = "robotics"
    
    async def on_message(self, msg: Message) -> None:
        """Handle robotics jobs."""
        if msg.topic == "robotics/job":
            job_id = msg.data.get("job_id")
            job_type = msg.data.get("type", "pick")
            
            # EXAMPLE: Simulate job execution
            await asyncio.sleep(0.02)
            
            # EXAMPLE: Report completion
            await self.emit("robotics/done", {
                "job_id": job_id,
                "type": job_type,
                "status": "completed",
                "ts": time.time()
            })
            
            self.log.debug(f"Job {job_id} completed: {job_type}")


class TradingEngine(Module):
    """
    Example trading/finance engine.
    
    This is a TEMPLATE - replace with your actual trading logic:
    - Market data processing
    - Strategy execution
    - Risk management
    - Order routing
    
    Shows: Stateless computation
    """
    
    name = "trading"
    
    async def on_message(self, msg: Message) -> None:
        """Handle trading operations."""
        if msg.topic == "trade/op":
            buy = msg.data.get("buy")
            sell = msg.data.get("sell")
            symbol = msg.data.get("symbol", "UNKNOWN")
            
            # EXAMPLE: Calculate P&L
            pnl = 0.0
            if buy is not None and sell is not None:
                pnl = float(sell) - float(buy)
            
            # EXAMPLE: Emit result
            await self.emit("trade/done", {
                "symbol": symbol,
                "buy": buy,
                "sell": sell,
                "pnl": pnl,
                "ts": time.time()
            })
            
            self.log.debug(f"Trade {symbol}: P&L={pnl:.2f}")


class DBAnalyzer(Module):
    """
    Example database query analyzer.
    
    This is a TEMPLATE - replace with your actual DB logic:
    - Query optimization
    - Index recommendations
    - Performance monitoring
    - Data analytics
    
    Shows: Thread-pool execution for I/O-bound operations
    """
    
    name = "db_analyzer"
    
    def __init__(self, bus, ex, policy, db_url: str = "sqlite:///example.db"):
        """
        Initialize DB analyzer.
        
        Args:
            bus: EventBus
            ex: Execution layer
            policy: Policy guard
            db_url: Database connection URL
        """
        super().__init__(bus, ex, policy)
        self.db_url = db_url
    
    async def on_message(self, msg: Message) -> None:
        """Handle database operations."""
        if msg.topic == "db/query":
            query = msg.data.get("sql", "SELECT 1")
            
            # EXAMPLE: Execute query in thread pool (I/O-bound)
            t0 = time.perf_counter()
            
            try:
                # This is where you'd do: pd.read_sql_query(query, engine)
                # For now, just simulate
                await asyncio.sleep(0.01)
                result_rows = 42  # Example
                
                dt = (time.perf_counter() - t0) * 1000.0
                
                await self.emit("db/result", {
                    "query": query[:100],  # Truncate for safety
                    "ms": dt,
                    "rows": result_rows,
                    "ts": time.time()
                })
                
            except Exception as e:
                self.log.error(f"Query failed: {e}")
                await self.emit("db/error", {
                    "query": query[:100],
                    "error": str(e)
                })
        
        elif msg.topic == "db/tune":
            # EXAMPLE: Trigger tuning optimization
            await self.emit("tuner/search", msg.data)


# Add more domain modules here for your use case:
# - SmartHome(Module) - home automation
# - VehicleFleet(Module) - autonomous vehicles
# - GameAI(Module) - NPC behaviors
# - NetworkMonitor(Module) - infrastructure monitoring
# - etc.
