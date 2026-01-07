# Event Topics and Message Formats

This document defines all event topics, message formats, and communication patterns used in HydraMind v1. Understanding these events is essential for building custom modules and integrating with the system.

---

## 📡 Event System Overview

HydraMind uses a **topic-based publish-subscribe** messaging system where modules communicate by publishing events to specific topics and subscribing to topics of interest.

### Topic Naming Convention

```
[domain]/[category]/[action]
```

Examples:
- `sensor/temperature` - Temperature sensor reading
- `hvac/command` - HVAC control command
- `learn/seed/config` - Learning configuration
- `anomaly/cpu` - CPU anomaly detection

### Message Structure

```python
@dataclass
class Message:
    topic: str              # Event topic (e.g., "sensor/temperature")
    data: Dict[str, Any]    # Event payload (JSON-serializable)
    qos: int = 0           # Quality of service (0=fire-and-forget, 1=at-least-once)
    key: Optional[str] = None  # Deduplication/grouping key
    timestamp: float = 0.0  # Unix timestamp
```

---

## 🎯 Core Event Topics

### System Events

#### Lifecycle Events
```json
{
  "topic": "system/startup",
  "data": {
    "version": "1.0.0",
    "modules": ["module1", "module2"],
    "config_hash": "sha256:...",
    "startup_time": 1.23
  }
}
```

```json
{
  "topic": "system/shutdown",
  "data": {
    "reason": "graceful" | "error" | "signal",
    "uptime": 3600.0,
    "modules_stopped": 8,
    "errors": []
  }
}
```

#### Health Events
```json
{
  "topic": "health/telemetry",
  "data": {
    "module": "temperature_monitor",
    "health": {
      "state": "running",
      "uptime": 1800.0,
      "message_count": 150,
      "error_count": 0,
      "memory_usage": 52428800,
      "cpu_usage": 2.5,
      "health_score": 0.95
    },
    "timestamp": 1640995200.0
  }
}
```

### Configuration Events

#### Module Configuration
```json
{
  "topic": "config/module/update",
  "data": {
    "module": "temperature_monitor",
    "config": {
      "target_temp": 22.0,
      "tolerance": 2.0,
      "polling_interval": 5.0
    },
    "restart_required": false
  }
}
```

---

## 🧠 Intelligence Module Events

### 1. SEED Optimizer Events

#### Configuration
```json
{
  "topic": "learn/seed/config",
  "data": {
    "learner_id": "model_v1",
    "lr": 0.001,
    "floor": 0.00001,
    "ceil": 0.02,
    "ema_alpha": 0.2
  }
}
```

#### Metrics Reporting
```json
{
  "topic": "learn/seed/metrics",
  "data": {
    "learner_id": "model_v1",
    "loss": 0.523,
    "accuracy": 0.89,
    "epoch": 150
  }
}
```

#### Learning Rate Updates
```json
{
  "topic": "learn/seed/update",
  "data": {
    "learner_id": "model_v1",
    "lr": 0.00105,
    "trend": -0.02,
    "confidence": 0.85
  }
}
```

### 2. Anomaly Detection Events

#### Telemetry Input
```json
{
  "topic": "telemetry/host",
  "data": {
    "cpu": 85.2,
    "mem": 67.3,
    "disk": 45.1,
    "network": 120.5,
    "ts": 1640995200.0
  }
}
```

#### Anomaly Detection
```json
{
  "topic": "anomaly/cpu",
  "data": {
    "value": 95.2,
    "z_score": 4.2,
    "mean": 35.0,
    "threshold": 3.0,
    "confidence": 0.99,
    "ts": 1640995200.0
  }
}
```

### 3. Pattern Learning Events

#### Pattern Detection
```json
{
  "topic": "learner/pattern/detected",
  "data": {
    "pattern_type": "temporal",
    "pattern_id": "daily_cpu_spike",
    "confidence": 0.87,
    "description": "CPU usage spikes daily at 9 AM",
    "data_points": 30
  }
}
```

#### Pattern Updates
```json
{
  "topic": "learner/pattern/update",
  "data": {
    "pattern_id": "daily_cpu_spike",
    "strength": 0.92,
    "frequency": "daily",
    "next_occurrence": 1641081600.0
  }
}
```

### 4. Swarm Coordination Events

#### Agent Management
```json
{
  "topic": "swarm/agent/spawn",
  "data": {
    "agent_id": "worker_001",
    "role": "worker",
    "capabilities": ["data_processing", "file_io"],
    "resources": {"cpu": 1, "memory": 512}
  }
}
```

#### Task Distribution
```json
{
  "topic": "swarm/task/assign",
  "data": {
    "task_id": "process_batch_123",
    "agent_id": "worker_001",
    "task_type": "data_processing",
    "priority": 5,
    "deadline": 1640995260.0
  }
}
```

### 5. Predictive Engine Events

#### Prediction Requests
```json
{
  "topic": "predictor/request",
  "data": {
    "prediction_type": "event",
    "target_topic": "system/load",
    "horizon": 3600,
    "confidence_threshold": 0.8
  }
}
```

#### Prediction Results
```json
{
  "topic": "predictor/result",
  "data": {
    "prediction_id": "pred_001",
    "prediction_type": "event",
    "predicted_events": [
      {
        "topic": "system/load",
        "probability": 0.85,
        "timestamp": 1640998800.0,
        "confidence": 0.82
      }
    ],
    "model_used": "lstm_v2",
    "features_used": ["cpu", "memory", "network"]
  }
}
```

---

## 🏭 Domain-Specific Events

### Smart Home Events

#### Sensor Readings
```json
{
  "topic": "sensor/temperature",
  "data": {
    "value": 23.5,
    "unit": "C",
    "sensor_id": "living_room_thermometer",
    "location": "living_room",
    "accuracy": 0.1
  }
}
```

#### HVAC Control
```json
{
  "topic": "hvac/command",
  "data": {
    "action": "cool" | "heat" | "off",
    "target": 22.0,
    "mode": "auto" | "manual",
    "zone": "living_room",
    "reason": "temperature_too_high"
  }
}
```

#### Lighting Control
```json
{
  "topic": "lighting/command",
  "data": {
    "action": "on" | "off" | "dim",
    "brightness": 80,
    "color_temp": 3000,
    "room": "living_room",
    "scene": "movie_night"
  }
}
```

### Autonomous Vehicle Events

#### Sensor Fusion
```json
{
  "topic": "sensor/fusion",
  "data": {
    "position": {"x": 10.5, "y": 20.3, "z": 0.0},
    "velocity": {"x": 5.2, "y": 0.1, "z": 0.0},
    "orientation": {"yaw": 45.0, "pitch": 2.1, "roll": 0.5},
    "confidence": 0.95,
    "sources": ["lidar", "camera", "imu"]
  }
}
```

#### Motion Planning
```json
{
  "topic": "planning/trajectory",
  "data": {
    "trajectory_id": "traj_001",
    "waypoints": [
      {"x": 10.0, "y": 20.0, "speed": 5.0},
      {"x": 15.0, "y": 25.0, "speed": 3.0}
    ],
    "constraints": {
      "max_speed": 10.0,
      "max_acceleration": 2.0,
      "obstacle_avoidance": true
    }
  }
}
```

### Industrial IoT Events

#### Production Monitoring
```json
{
  "topic": "production/status",
  "data": {
    "line_id": "assembly_line_1",
    "status": "running" | "stopped" | "maintenance",
    "throughput": 150,  // units per hour
    "quality_rate": 0.98,
    "downtime_minutes": 15
  }
}
```

#### Predictive Maintenance
```json
{
  "topic": "maintenance/prediction",
  "data": {
    "equipment_id": "motor_001",
    "component": "bearing",
    "time_to_failure": 7200,  // seconds
    "confidence": 0.89,
    "recommended_action": "schedule_maintenance",
    "priority": "high"
  }
}
```

---

## 🎛️ Control Plane Events

### REST API Integration

#### Health Check Events
```json
{
  "topic": "api/health_check",
  "data": {
    "endpoint": "/health",
    "method": "GET",
    "status_code": 200,
    "response_time": 0.023,
    "user_agent": "curl/7.68.0"
  }
}
```

#### Event Injection
```json
{
  "topic": "api/event_inject",
  "data": {
    "source": "api",
    "original_topic": "sensor/temperature",
    "injected_data": {
      "value": 25.0,
      "unit": "C",
      "sensor_id": "external_api"
    },
    "reason": "testing"
  }
}
```

---

## 📊 Module Communication Patterns

### Request-Response Pattern

#### Requester → Responder
```python
# Request
await bus.publish(Message("compute/fibonacci", {
    "n": 10,
    "request_id": "req_001"
}))

# Response
async def on_message(self, msg: Message):
    if msg.topic == "compute/fibonacci":
        n = msg.data["n"]
        result = fibonacci(n)
        await self.emit(f"compute/fibonacci/{msg.data['request_id']}", {
            "result": result
        })
```

### Broadcast Pattern

#### One-to-Many Communication
```python
# Broadcast to all subscribers
await bus.publish(Message("alert/security", {
    "level": "high",
    "message": "Unauthorized access detected",
    "location": "server_room"
}))

# Multiple modules can respond
async def on_message(self, msg: Message):
    if msg.topic == "alert/security":
        # Log the alert
        # Send notification
        # Trigger response actions
```

### Streaming Pattern

#### Continuous Data Flow
```python
# High-frequency sensor streaming
async def sensor_stream(self):
    while self.running:
        data = await self.sensor.read()
        await self.emit("sensor/stream", data)
        await asyncio.sleep(0.01)  # 100Hz

# Batch processing of stream
async def on_message(self, msg: Message):
    if msg.topic == "sensor/stream":
        self.batch.append(msg.data)
        if len(self.batch) >= 100:
            await self.process_batch(self.batch)
            self.batch.clear()
```

---

## 🔧 Module-Specific Event Topics

### Temperature Monitor Module

#### Input Events
```json
{
  "topic": "sensor/temperature",
  "data": {
    "value": 24.5,
    "unit": "C",
    "sensor_id": "living_room",
    "accuracy": 0.1
  }
}
```

#### Output Events
```json
{
  "topic": "hvac/command",
  "data": {
    "action": "cool",
    "target": 22.0,
    "zone": "living_room",
    "reason": "temperature_too_high"
  }
}
```

### Security System Module

#### Motion Detection
```json
{
  "topic": "sensor/motion",
  "data": {
    "detected": true,
    "zone": "living_room",
    "confidence": 0.95,
    "camera_id": "cam_001"
  }
}
```

#### Alert Generation
```json
{
  "topic": "alert/security",
  "data": {
    "level": "medium",
    "type": "motion_detected",
    "zone": "living_room",
    "camera_id": "cam_001",
    "image_url": "https://storage/camera/cam_001/snapshot.jpg"
  }
}
```

### Database Analyzer Module

#### Query Monitoring
```json
{
  "topic": "db/query",
  "data": {
    "query_id": "q_001",
    "sql": "SELECT * FROM users WHERE active = true",
    "execution_time": 150.5,
    "rows_returned": 1250,
    "database": "analytics"
  }
}
```

#### Optimization Recommendations
```json
{
  "topic": "db/optimization",
  "data": {
    "query_id": "q_001",
    "issue": "missing_index",
    "recommendation": "CREATE INDEX idx_users_active ON users(active)",
    "expected_improvement": 0.85,
    "impact": "high"
  }
}
```

---

## 📈 Event Categories Summary

### System Management
- `system/*` - System lifecycle and configuration
- `health/*` - Health monitoring and telemetry
- `config/*` - Configuration updates and management

### Intelligence & Learning
- `learn/*` - Learning configuration and metrics
- `predictor/*` - Prediction requests and results
- `optimizer/*` - Optimization goals and recommendations
- `anomaly/*` - Anomaly detection and alerts

### Coordination & Agents
- `swarm/*` - Multi-agent coordination
- `task/*` - Task assignment and management
- `agent/*` - Agent lifecycle and status

### Domain-Specific
- `sensor/*` - Sensor readings and data
- `actuator/*` - Actuator control commands
- `hvac/*` - Heating/cooling system control
- `lighting/*` - Lighting system control
- `security/*` - Security system events

### Infrastructure
- `db/*` - Database operations and optimization
- `api/*` - API usage and monitoring
- `network/*` - Network connectivity and performance

---

## 🔄 Event Processing Guidelines

### Best Practices

#### Topic Design
- **Hierarchical naming** - Use `/` separators for organization
- **Consistent patterns** - Follow established naming conventions
- **Version in topics** - Include version numbers for breaking changes
- **Avoid ambiguity** - Make topic purposes clear from names

#### Message Design
- **Structured data** - Use consistent field names and types
- **Required fields** - Include all necessary information
- **Optional fields** - Clearly mark optional vs required
- **Timestamps** - Include when events occurred
- **Context** - Provide sufficient context for processing

#### Error Handling
```python
async def on_message(self, msg: Message):
    try:
        # Process message
        await self.process_event(msg)
    except Exception as e:
        # Log error with context
        self.log.error(f"Failed to process {msg.topic}: {e}")

        # Emit error event for monitoring
        await self.emit("error/processing", {
            "original_topic": msg.topic,
            "error": str(e),
            "module": self.name
        })
```

### Performance Considerations

#### High-Frequency Events
```python
# For events > 100Hz, use streaming pattern
async def high_frequency_handler(self):
    batch = []
    while self.running:
        # Collect events in batches
        if len(batch) >= 100:
            await self.process_batch(batch)
            batch.clear()

        # Wait for next batch or timeout
        try:
            msg = await asyncio.wait_for(self.event_queue.get(), timeout=0.01)
            batch.append(msg)
        except asyncio.TimeoutError:
            pass
```

#### Large Data Events
```python
# For large payloads, use references
await self.emit("data/large_dataset", {
    "dataset_id": "ds_001",
    "size": 1048576,  # 1MB
    "format": "parquet",
    "location": "/data/datasets/ds_001.parquet"
})

# Process large data separately
async def on_message(self, msg: Message):
    if msg.topic == "data/large_dataset":
        dataset_id = msg.data["dataset_id"]
        await self.process_large_dataset(dataset_id)
```

---

## 🎛️ Event Testing & Debugging

### Event Injection via API

```bash
# Inject test events
curl -X POST http://localhost:8765/bus/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sensor/temperature",
    "data": {"value": 25.0, "unit": "C"}
  }'

# Query event history
curl -X POST http://localhost:8765/events/query \
  -H "Content-Type: application/json" \
  -d '{
    "topic_pattern": "sensor/*",
    "limit": 10,
    "since": 1640995200
  }'
```

### Module Event Monitoring

```python
class EventMonitor(Module):
    name = "event_monitor"

    async def _handle_message(self, msg: Message):
        """Monitor all events for debugging"""
        self.log.debug(f"Event: {msg.topic} -> {msg.data}")

        # Track event statistics
        self.event_counts[msg.topic] = self.event_counts.get(msg.topic, 0) + 1
```

### Event Flow Visualization

```python
# Visualize event flow
def visualize_event_flow():
    """Create a diagram of event relationships"""
    events = {
        "sensor/temperature": ["hvac/command", "analytics/temperature"],
        "sensor/motion": ["security/alert", "lighting/command"],
        "hvac/command": ["energy/usage", "comfort/score"],
        "learn/seed/metrics": ["learn/seed/update"],
        "anomaly/*": ["alert/system", "optimizer/adjust"]
    }

    # Generate visualization (Mermaid, Graphviz, etc.)
```

---

## 📋 Event Reference Table

| Topic Pattern | Purpose | Example Payload |
|---------------|---------|-----------------|
| `system/startup` | System initialization | `{"version": "1.0.0", "modules": [...], "startup_time": 1.23}` |
| `system/shutdown` | System shutdown | `{"reason": "graceful", "uptime": 3600.0}` |
| `health/telemetry` | Health monitoring | `{"module": "temp_monitor", "health_score": 0.95}` |
| `sensor/temperature` | Temperature readings | `{"value": 23.5, "unit": "C", "sensor_id": "living_room"}` |
| `hvac/command` | HVAC control | `{"action": "cool", "target": 22.0, "zone": "living_room"}` |
| `learn/seed/config` | Learning configuration | `{"learner_id": "model_v1", "lr": 0.001}` |
| `learn/seed/metrics` | Learning metrics | `{"learner_id": "model_v1", "loss": 0.523}` |
| `anomaly/cpu` | CPU anomaly detection | `{"value": 95.2, "z_score": 4.2, "threshold": 3.0}` |
| `swarm/agent/spawn` | Agent creation | `{"agent_id": "worker_001", "role": "worker"}` |
| `predictor/result` | Prediction results | `{"prediction_id": "pred_001", "probability": 0.85}` |

---

## 🔧 Custom Event Topics

### Creating New Event Topics

When adding new modules, follow these guidelines:

#### 1. Topic Hierarchy
```
[domain]/[subsystem]/[action]
```

Examples:
- `robotics/arm/move` - Robot arm movement command
- `trading/portfolio/update` - Portfolio position changes
- `iot/device/status` - IoT device connectivity status

#### 2. Message Format Standards
```python
# Standard fields to include
{
  "topic": "custom/event",
  "data": {
    # Required fields
    "timestamp": 1640995200.0,
    "source": "module_name",

    # Domain-specific fields
    "custom_field": "value",
    "another_field": 42
  },

  # Optional fields
  "qos": 1,
  "key": "unique_identifier"
}
```

#### 3. Event Documentation
```python
# Document new events in this file
"""
## Custom Module Events

### Module Name Events

#### Input Events
- `custom/input` - Description of input event

#### Output Events
- `custom/output` - Description of output event
"""
```

---

## 🚨 Event Error Handling

### Error Event Topics

#### Module Errors
```json
{
  "topic": "error/module",
  "data": {
    "module": "temperature_monitor",
    "error": "Connection timeout",
    "context": {"sensor_id": "living_room"},
    "timestamp": 1640995200.0,
    "severity": "high"
  }
}
```

#### Processing Errors
```json
{
  "topic": "error/processing",
  "data": {
    "original_topic": "sensor/temperature",
    "error": "Invalid temperature value: -300",
    "module": "temperature_monitor",
    "recovery_action": "using_default_value"
  }
}
```

### Error Recovery Patterns

```python
async def on_message(self, msg: Message):
    try:
        # Process message
        result = await self.process_data(msg.data)

        # Emit success confirmation
        await self.emit("processing/success", {
            "original_topic": msg.topic,
            "result_summary": "processed_successfully"
        })

    except ValidationError as e:
        # Emit validation error
        await self.emit("error/validation", {
            "original_topic": msg.topic,
            "error": str(e),
            "field": e.field_name
        })

    except ProcessingError as e:
        # Emit processing error
        await self.emit("error/processing", {
            "original_topic": msg.topic,
            "error": str(e),
            "retry_count": self.retry_count
        })
```

---

## 📊 Event Metrics & Monitoring

### Event Statistics Events

#### Throughput Monitoring
```json
{
  "topic": "metrics/events_per_second",
  "data": {
    "topic_pattern": "sensor/*",
    "events_per_second": 150.5,
    "peak_rate": 200.0,
    "average_latency": 0.023,
    "error_rate": 0.001
  }
}
```

#### Module Performance
```json
{
  "topic": "metrics/module_performance",
  "data": {
    "module": "temperature_monitor",
    "messages_processed": 1500,
    "average_processing_time": 0.015,
    "memory_usage": 52428800,
    "error_count": 2
  }
}
```

### Event Pattern Analysis

#### Event Correlation
```json
{
  "topic": "analytics/event_correlation",
  "data": {
    "correlation_id": "corr_001",
    "events": ["sensor/temperature", "hvac/command"],
    "correlation_strength": 0.85,
    "pattern": "temperature_above_threshold → hvac_cooling",
    "confidence": 0.92
  }
}
```

---

**This comprehensive event documentation ensures that all communication patterns in HydraMind v1 are well-defined, documented, and maintainable.**
