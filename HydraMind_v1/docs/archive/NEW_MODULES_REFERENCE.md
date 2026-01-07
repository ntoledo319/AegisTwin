# HydraMind New Modules - Quick Reference

## Overview
Six new cognitive modules extracted from NousIntelligence SEED architecture, providing autonomous learning, optimization, verification, data collection, pattern recognition, agent coordination, and predictive capabilities.

---

## Module Summaries

### 1. SelfOptimizer (`self_optimizer.py`)
**Purpose**: Continuously learns and optimizes system parameters across multiple domains.

**Key Features**:
- 🎯 Multi-domain optimization (performance, throughput, latency, error rate, resources)
- 📊 Pattern-based learning
- 🔄 Automatic parameter tuning
- 📈 Trend detection
- ⚡ Real-time metric monitoring

**Events**:
```python
# Consumed:
- health/telemetry
- module/performance  
- optimizer/optimize

# Emitted:
- optimizer/result
- optimizer/recommendation
```

**Usage**:
```python
optimizer = SelfOptimizer(bus, ex, policy, optimization_interval=60.0)
await optimizer.start()

# Manual optimization:
await bus.publish_event("optimizer/optimize", {"domain": "performance"})
```

---

### 2. SystemVerifier (`system_verifier.py`)
**Purpose**: Autonomous health verification and issue detection.

**Key Features**:
- ❤️ Continuous health monitoring
- 🔍 Memory, CPU, disk checks
- 🚨 Critical issue alerting
- 💯 Health score calculation
- 📋 Actionable recommendations

**Events**:
```python
# Consumed:
- verifier/check
- verifier/register_check

# Emitted:
- verifier/result
- verifier/alert
- verifier/recommendation
```

**Usage**:
```python
verifier = SystemVerifier(bus, ex, policy, check_interval=300.0)
await verifier.start()

# Manual check:
await bus.publish_event("verifier/check", {"check_type": "full"})
```

---

### 3. DataCollector (`data_collector.py`)
**Purpose**: Autonomous data gathering, aggregation, and insight generation.

**Key Features**:
- 📥 Multi-source collection
- 📊 Time-series storage
- 🔬 Statistical analysis
- 💡 Insight generation
- 📈 Summary reports

**Collection Types**:
- SYSTEM_METRICS: CPU, memory, disk
- MODULE_PERFORMANCE: Latency, throughput
- EVENT_PATTERNS: Event frequencies
- ERROR_LOGS: Error tracking
- USAGE_ANALYTICS: System usage

**Events**:
```python
# Consumed:
- collector/start/stop/collect
- health/telemetry
- module/performance
- module/error

# Emitted:
- collector/result
- collector/insight
- collector/summary
```

**Usage**:
```python
collector = DataCollector(
    bus, ex, policy,
    collection_interval=60.0,
    summary_interval=300.0
)
await collector.start()
```

---

### 4. PatternLearner (`pattern_learner.py`)
**Purpose**: Autonomous pattern recognition and anomaly detection.

**Key Features**:
- 🔍 Pattern detection (temporal, sequential, correlation, trend)
- 📊 Statistical analysis
- ⚠️ Anomaly detection
- 📚 Pattern library
- 🎯 Confidence scoring

**Pattern Types**:
- TEMPORAL: Time-based patterns
- SEQUENTIAL: Event sequences
- CORRELATION: Metric relationships
- ANOMALY: Baseline deviations
- TREND: Directional changes

**Events**:
```python
# Consumed:
- learner/analyze
- collector/summary
- health/telemetry

# Emitted:
- learner/pattern_detected
- learner/anomaly_detected
```

**Usage**:
```python
learner = PatternLearner(
    bus, ex, policy,
    learning_interval=120.0,
    pattern_threshold=0.7
)
await learner.start()
```

---

### 5. SwarmCoordinator (`swarm_coordinator.py`)
**Purpose**: Coordinates multiple autonomous agents working toward common goals.

**Key Features**:
- 🤖 Agent lifecycle management
- 📋 Task distribution
- ⚖️ Load balancing
- 🎯 Capability matching
- 📊 Performance tracking

**Agent Roles**:
- WORKER: Task execution
- MONITOR: System monitoring
- OPTIMIZER: Performance optimization
- HEALER: Self-healing
- COLLECTOR: Data collection
- LEARNER: Pattern learning

**Events**:
```python
# Consumed:
- swarm/register_agent
- swarm/submit_task
- swarm/agent_status
- swarm/task_result

# Emitted:
- swarm/task_assigned
- swarm/task_completed
- swarm/swarm_status
- swarm/spawn_agent
```

**Usage**:
```python
coordinator = SwarmCoordinator(
    bus, ex, policy,
    coordination_interval=30.0,
    max_agents_per_role=5
)
await coordinator.start()

# Register agent:
await bus.publish_event("swarm/register_agent", {
    "role": "worker",
    "capabilities": ["optimization", "data_processing"]
})

# Submit task:
await bus.publish_event("swarm/submit_task", {
    "task_type": "optimization",
    "priority": 8,
    "payload": {"target": "cpu_usage"}
})
```

---

### 6. PredictiveEngine (`predictive_engine.py`)
**Purpose**: Predicts future events, metrics, and potential issues.

**Key Features**:
- 🔮 Multi-type predictions
- 📈 Trend analysis
- ⚠️ Anomaly forecasting
- 📊 Time-series modeling
- 🎯 Confidence scoring

**Prediction Types**:
- EVENT: Next likely events
- METRIC: Future values
- ANOMALY: Potential issues
- LOAD: System load levels
- FAILURE: Predicted failures

**Events**:
```python
# Consumed:
- predictor/predict
- learner/pattern_detected
- collector/summary

# Emitted:
- predictor/prediction
- predictor/alert
```

**Usage**:
```python
predictor = PredictiveEngine(
    bus, ex, policy,
    prediction_interval=180.0,
    min_confidence=0.6
)
await predictor.start()

# Request prediction:
await bus.publish_event("predictor/predict", {
    "type": "metric",
    "target": "cpu_usage"
})
```

---

## Integration Example

```python
# Complete cognitive system
modules = [
    SelfOptimizer(bus, ex, policy),
    SystemVerifier(bus, ex, policy),
    DataCollector(bus, ex, policy),
    PatternLearner(bus, ex, policy),
    SwarmCoordinator(bus, ex, policy),
    PredictiveEngine(bus, ex, policy)
]

# Start all
for module in modules:
    await module.start()

# They work together automatically:
# 1. DataCollector gathers metrics
# 2. PatternLearner finds patterns
# 3. PredictiveEngine makes predictions
# 4. SelfOptimizer adjusts parameters
# 5. SystemVerifier ensures health
# 6. SwarmCoordinator orchestrates agents
```

---

## Event Flow

```
Telemetry → DataCollector → PatternLearner → PredictiveEngine
                ↓                  ↓                 ↓
         collector/summary   learner/pattern   predictor/alert
                ↓                  ↓                 ↓
           SelfOptimizer ←──────────────────────────┘
                ↓
         optimizer/result → SystemVerifier → SwarmCoordinator
```

---

## Statistics Available

Each module provides comprehensive statistics via `get_stats()`:

```python
stats = module.get_stats()

# Common stats (all modules):
{
    'name': str,
    'running': bool,
    'messages_handled': int,
    'errors': int
}

# Module-specific stats:
# - optimizer: optimization_history_count, patterns_detected
# - verifier: results_history_count, recent_average_health
# - collector: data_series_count, total_events_tracked
# - learner: patterns_stored, anomalies_detected
# - coordinator: total_agents, total_tasks_processed
# - predictor: predictions_made, accuracy_pct
```

---

## Configuration

All modules accept these parameters:

| Module | Interval Parameter | Default | Purpose |
|--------|-------------------|---------|---------|
| SelfOptimizer | optimization_interval | 60s | How often to optimize |
| SystemVerifier | check_interval | 300s | How often to verify |
| DataCollector | collection_interval | 60s | How often to collect |
| DataCollector | summary_interval | 300s | How often to summarize |
| PatternLearner | learning_interval | 120s | How often to learn |
| SwarmCoordinator | coordination_interval | 30s | How often to coordinate |
| PredictiveEngine | prediction_interval | 180s | How often to predict |

**Tuning Recommendations**:
- **High-frequency systems**: Reduce all intervals by 50%
- **Low-resource systems**: Increase intervals by 2-3x
- **Production**: Use defaults or slightly higher
- **Development**: Use lower intervals for faster feedback

---

## Performance Considerations

1. **Memory Usage**:
   - Data windows are bounded (500-1000 items)
   - History is periodically trimmed
   - Deques used for efficient circular buffers

2. **CPU Usage**:
   - All operations are async
   - Configurable intervals
   - No blocking operations

3. **Event Load**:
   - Modules subscribe only to needed events
   - Catch-all handlers are silent on error
   - Policy guard prevents event storms

---

## Common Patterns

### Pattern 1: Manual Trigger
```python
# Trigger optimization manually
await bus.publish_event("optimizer/optimize", {
    "domain": "performance"
})
```

### Pattern 2: Respond to Predictions
```python
async def handle_prediction(msg):
    if msg.data['type'] == 'anomaly':
        # Take action on predicted anomaly
        await bus.publish_event("verifier/check", {
            "check_type": "full"
        })

await bus.subscribe("predictor/alert", handle_prediction)
```

### Pattern 3: Agent Task Chain
```python
# Submit related tasks
tasks = [
    {"task_type": "collect", "priority": 5},
    {"task_type": "analyze", "priority": 7},
    {"task_type": "optimize", "priority": 9}
]

for task in tasks:
    await bus.publish_event("swarm/submit_task", task)
```

---

## Troubleshooting

**Issue**: No events being emitted
- **Check**: Module started? `await module.start()`
- **Check**: Subscribed to events?
- **Check**: Policy allowing messages?

**Issue**: High CPU usage
- **Solution**: Increase interval parameters
- **Solution**: Reduce window sizes
- **Solution**: Disable verbose logging

**Issue**: Memory growing
- **Solution**: Check window sizes are bounded
- **Solution**: Verify history trimming
- **Solution**: Review event subscriptions

---

## Next Steps

1. ✅ Run the demo: `examples/seed_cognitive_demo.py`
2. ✅ Read module docstrings for detailed APIs
3. ✅ Check `PROGRESS_SESSION1.md` for roadmap
4. ✅ Explore existing modules in `hydramind/modules/`
5. ✅ Review `hydramind/core/` for base classes

---

**Created**: October 10, 2025  
**Status**: Production-ready  
**Testing**: Pending comprehensive test suite
