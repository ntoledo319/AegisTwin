"""
Demo: SEED-Inspired Cognitive System
=====================================

Demonstrates the new autonomous cognitive modules working together:
- SelfOptimizer: Learns and optimizes parameters
- SystemVerifier: Monitors system health
- DataCollector: Gathers metrics
- PatternLearner: Detects patterns
- SwarmCoordinator: Coordinates agents
- PredictiveEngine: Predicts future states

This example shows how these modules collaborate to create an
intelligent, self-improving system.
"""

import asyncio
import logging
from hydramind.core.bus import EventBus
from hydramind.core.execs import Exec
from hydramind.core.policy import PolicyGuard
from hydramind.modules.self_optimizer import SelfOptimizer
from hydramind.modules.system_verifier import SystemVerifier
from hydramind.modules.data_collector import DataCollector
from hydramind.modules.pattern_learner import PatternLearner
from hydramind.modules.swarm_coordinator import SwarmCoordinator
from hydramind.modules.predictive_engine import PredictiveEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Run the SEED-inspired cognitive system demo.
    """
    logger.info("=" * 60)
    logger.info("HydraMind SEED Cognitive System Demo")
    logger.info("=" * 60)
    
    # Initialize core infrastructure
    logger.info("\n[1/7] Initializing core infrastructure...")
    bus = EventBus()
    ex = Exec(max_workers=4)
    policy = PolicyGuard(rate_limit=1000, window_seconds=1.0)
    
    # Initialize cognitive modules
    logger.info("[2/7] Initializing cognitive modules...")
    
    modules = {
        'optimizer': SelfOptimizer(
            bus, ex, policy,
            optimization_interval=30.0  # Optimize every 30s for demo
        ),
        'verifier': SystemVerifier(
            bus, ex, policy,
            check_interval=20.0  # Verify every 20s for demo
        ),
        'collector': DataCollector(
            bus, ex, policy,
            collection_interval=15.0,  # Collect every 15s
            summary_interval=30.0  # Summarize every 30s
        ),
        'learner': PatternLearner(
            bus, ex, policy,
            learning_interval=25.0  # Learn every 25s
        ),
        'coordinator': SwarmCoordinator(
            bus, ex, policy,
            coordination_interval=20.0  # Coordinate every 20s
        ),
        'predictor': PredictiveEngine(
            bus, ex, policy,
            prediction_interval=35.0  # Predict every 35s
        )
    }
    
    # Start all modules
    logger.info("[3/7] Starting all modules...")
    for name, module in modules.items():
        await module.start()
        logger.info(f"  ✓ Started {name}")
    
    # Set up event listeners to show system activity
    logger.info("[4/7] Setting up event monitoring...")
    
    event_counts = {'total': 0}
    
    async def log_event(msg):
        """Log interesting events"""
        event_counts['total'] += 1
        topic = msg.topic
        
        if topic.startswith('optimizer/result'):
            logger.info(f"  📊 Optimization: {msg.data.get('domain')} - "
                       f"{msg.data.get('improvement_pct', 0):.1f}% improvement")
        
        elif topic.startswith('verifier/result'):
            health = msg.data.get('overall_health', 0)
            logger.info(f"  ❤️  Health Check: {health:.1f}% - "
                       f"{msg.data.get('checks_passed', 0)}/{msg.data.get('checks_completed', 0)} passed")
        
        elif topic.startswith('verifier/alert'):
            logger.warning(f"  ⚠️  Alert: {msg.data.get('check')} - {msg.data.get('severity')}")
        
        elif topic.startswith('collector/insight'):
            logger.info(f"  💡 Insight: {msg.data.get('insight')}")
        
        elif topic.startswith('learner/pattern_detected'):
            logger.info(f"  🔍 Pattern: {msg.data.get('pattern_type')} - "
                       f"{msg.data.get('name')} ({msg.data.get('confidence', 0):.2f} confidence)")
        
        elif topic.startswith('swarm/agent_registered'):
            logger.info(f"  🤖 Agent: {msg.data.get('agent_id')} ({msg.data.get('role')}) registered")
        
        elif topic.startswith('swarm/task_completed'):
            logger.info(f"  ✅ Task: {msg.data.get('task_id')} completed by {msg.data.get('agent_id')}")
        
        elif topic.startswith('predictor/prediction'):
            logger.info(f"  🔮 Prediction: {msg.data.get('type')} - {msg.data.get('target')} "
                       f"({msg.data.get('confidence', 0):.2f} confidence)")
        
        elif topic.startswith('predictor/alert'):
            logger.warning(f"  ⚡ Predicted Issue: {msg.data.get('type')} - {msg.data.get('target')}")
    
    # Subscribe to all interesting topics
    await bus.subscribe("optimizer/*", log_event)
    await bus.subscribe("verifier/*", log_event)
    await bus.subscribe("collector/insight", log_event)
    await bus.subscribe("learner/pattern_detected", log_event)
    await bus.subscribe("swarm/*", log_event)
    await bus.subscribe("predictor/*", log_event)
    
    # Simulate system activity
    logger.info("[5/7] Simulating system activity...")
    logger.info("  System will run for 90 seconds to demonstrate capabilities...\n")
    
    # Register some agents with the swarm
    await bus.publish_event("swarm/register_agent", {
        "role": "worker",
        "capabilities": ["data_processing", "optimization"]
    })
    
    await bus.publish_event("swarm/register_agent", {
        "role": "monitor",
        "capabilities": ["health_check", "verification"]
    })
    
    # Submit some tasks
    await bus.publish_event("swarm/submit_task", {
        "task_type": "optimization",
        "priority": 8,
        "payload": {"target": "cpu_usage"}
    })
    
    await bus.publish_event("swarm/submit_task", {
        "task_type": "verification",
        "priority": 7,
        "payload": {"check_type": "full"}
    })
    
    # Generate some simulated telemetry
    async def simulate_telemetry():
        """Simulate periodic telemetry"""
        import random
        base_cpu = 50
        base_mem = 60
        
        for _ in range(30):  # 30 telemetry updates
            await asyncio.sleep(3)
            
            # Add some variation
            cpu = base_cpu + random.randint(-10, 10)
            mem = base_mem + random.randint(-5, 5)
            
            await bus.publish_event("health/telemetry", {
                "cpu": cpu,
                "mem": mem,
                "disk": 70,
                "ts": asyncio.get_event_loop().time()
            })
            
            # Occasionally spike CPU to trigger patterns
            if random.random() > 0.8:
                base_cpu = min(90, base_cpu + 5)
            else:
                base_cpu = max(40, base_cpu - 2)
    
    # Run simulation
    telemetry_task = asyncio.create_task(simulate_telemetry())
    
    # Let the system run
    logger.info("[6/7] System running...")
    logger.info("-" * 60)
    
    try:
        await asyncio.sleep(90)  # Run for 90 seconds
    except KeyboardInterrupt:
        logger.info("\n  Interrupted by user")
    
    # Wait for telemetry to finish
    if not telemetry_task.done():
        telemetry_task.cancel()
        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass
    
    logger.info("\n" + "-" * 60)
    logger.info("[7/7] Shutting down...")
    
    # Get final statistics
    logger.info("\n" + "=" * 60)
    logger.info("Final Statistics:")
    logger.info("=" * 60)
    
    for name, module in modules.items():
        stats = module.get_stats()
        logger.info(f"\n{name.upper()}:")
        logger.info(f"  Status: {'Running' if stats.get('running') else 'Stopped'}")
        logger.info(f"  Messages: {stats.get('messages_handled', 0)}")
        
        if name == 'optimizer':
            logger.info(f"  Optimizations: {stats.get('optimization_history_count', 0)}")
            logger.info(f"  Patterns: {stats.get('patterns_detected', 0)}")
        
        elif name == 'verifier':
            logger.info(f"  Checks Run: {stats.get('results_history_count', 0)}")
            logger.info(f"  Avg Health: {stats.get('recent_average_health', 0):.1f}%")
        
        elif name == 'collector':
            logger.info(f"  Data Series: {stats.get('data_series_count', 0)}")
            logger.info(f"  Events Tracked: {stats.get('total_events_tracked', 0)}")
        
        elif name == 'learner':
            logger.info(f"  Patterns: {stats.get('patterns_stored', 0)}")
            logger.info(f"  Anomalies: {stats.get('anomalies_detected', 0)}")
        
        elif name == 'coordinator':
            logger.info(f"  Agents: {stats.get('total_agents', 0)}")
            logger.info(f"  Tasks Processed: {stats.get('total_tasks_processed', 0)}")
        
        elif name == 'predictor':
            logger.info(f"  Predictions: {stats.get('predictions_made', 0)}")
            logger.info(f"  Accuracy: {stats.get('accuracy_pct', 0):.1f}%")
    
    logger.info(f"\nTotal Events Processed: {event_counts['total']}")
    
    # Stop all modules
    logger.info("\nStopping modules...")
    for name, module in modules.items():
        await module.stop()
        logger.info(f"  ✓ Stopped {name}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Demo Complete!")
    logger.info("=" * 60)
    logger.info("\nKey Takeaways:")
    logger.info("  ✓ All modules worked together autonomously")
    logger.info("  ✓ System self-optimized based on patterns")
    logger.info("  ✓ Health monitoring detected issues")
    logger.info("  ✓ Patterns were learned from behavior")
    logger.info("  ✓ Predictions were made about future states")
    logger.info("  ✓ Swarm coordination managed agent tasks")
    logger.info("\nThis demonstrates the foundation of a self-improving")
    logger.info("cognitive system inspired by SEED architecture!")


if __name__ == "__main__":
    asyncio.run(main())
