# Configuration Guide

This guide provides comprehensive configuration options for HydraMind v1, including YAML configuration, environment variables, and runtime settings.

---

## 📋 Configuration Overview

HydraMind uses a hierarchical configuration system:
1. **Default values** - Built-in sensible defaults
2. **YAML configuration** - `hydramind.yaml` file
3. **Environment variables** - Runtime overrides
4. **Runtime parameters** - Command-line arguments

---

## 🏗️ Complete Configuration Reference

### hydramind.yaml Structure

```yaml
# HydraMind v1 Configuration
# Copy this file and customize for your use case

# FastAPI Control Plane (REST API)
server:
  enabled: false              # Set true to enable HTTP control plane
  host: 0.0.0.0              # Listen address
  port: 8765                 # HTTP port
  cors: ["*"]                # CORS origins (* = allow all)

# Logging Configuration
logging:
  level: INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL
  json: true                 # Use JSON format for structured logs
  file_path: ./logs/hydramind.log
  rotate_bytes: 15000000     # 15MB before rotation
  backups: 5                 # Keep 5 backup files

# Feature Flags - Enable/disable modules
features:
  # Intelligence modules (keep these)
  seed: true                 # Adaptive learning rate optimizer
  replay: true               # Priority replay buffer
  anomaly: true              # Anomaly detection (EWMA + Z-score)
  optimizer: true            # Bottleneck detection & goal scoring
  meta_planner: true         # Strategy selection

  # Example domain modules (DELETE these, add your own)
  drones: false              # Example: Drone swarm coordinator
  robots: false              # Example: Robotics cell
  trading: false             # Example: Trading engine
  db: false                  # Example: Database analyzer

  # Add your custom features here:
  # my_smart_home: true
  # my_vehicle_fleet: true
  # my_game_ai: true

# Event Storage (SQLite)
event_db: ./brain_events.sqlite

# Data Layer (Shared Memory & Snapshots)
snapshot_dir: ./snapshots
snapshot_size: 2097152       # Size of memory-mapped snapshot (bytes, default: 2MB)
ring_name: hydra_ring        # Shared memory name (must be unique)
ring_capacity: 16384         # Number of items in ring buffer
ring_item_bytes: 2048        # Max bytes per item

# Security & Rate Limiting
policy_allowlist: null       # null = allow all topics
                             # or list: ["safe/*", "public/*"]
max_events_per_sec: 50000    # Global rate limit

# Your custom configuration
custom:
  # Example:
  # camera_device: /dev/video0
  # lidar_port: /dev/ttyUSB0
  # api_key: ${API_KEY}  # Can reference env vars
  # neural_net_path: ./models/latest.pth
```

---

## ⚙️ Environment Variable Overrides

All configuration values can be overridden using environment variables with the `BRAIN_` prefix:

```bash
# Server configuration
export BRAIN_SERVER_ENABLED=true
export BRAIN_SERVER_HOST=0.0.0.0
export BRAIN_SERVER_PORT=8765

# Logging configuration
export BRAIN_LOGGING_LEVEL=DEBUG
export BRAIN_LOGGING_JSON=true
export BRAIN_LOGGING_FILE_PATH=./logs/hydramind.log

# Feature flags
export BRAIN_FEATURES_SEED=true
export BRAIN_FEATURES_ANOMALY=true
export BRAIN_FEATURES_OPTIMIZER=true

# Data layer
export BRAIN_RING_CAPACITY=32768
export BRAIN_SNAPSHOT_DIR=./data/snapshots

# Security
export BRAIN_POLICY_ALLOWLIST="safe/*,public/*"
export BRAIN_MAX_EVENTS_PER_SEC=100000

# Custom configuration
export BRAIN_CUSTOM_CAMERA_DEVICE=/dev/video0
export BRAIN_CUSTOM_MODEL_PATH=./models/v1.pth
```

### Environment Variable Format

**Simple values:**
```bash
export BRAIN_SERVER_ENABLED=true
export BRAIN_SERVER_PORT=8765
export BRAIN_LOGGING_LEVEL=INFO
```

**Nested values:**
```bash
export BRAIN_FEATURES_SEED=true
export BRAIN_FEATURES_ANOMALY=true
```

**Lists:**
```bash
export BRAIN_SERVER_CORS="https://app.example.com,https://admin.example.com"
export BRAIN_POLICY_ALLOWLIST="safe/*,public/*"
```

---

## 🚀 Runtime Configuration

### Command-Line Arguments

```bash
# Run with custom config file
python -m hydramind --config ./myproject.yaml

# Override specific settings
python -m hydramind --config ./config.yaml --server-port 9000

# Enable debug logging
python -m hydramind --logging-level DEBUG

# Dry run (validate config without starting)
python -m hydramind --config ./config.yaml --dry-run

# Show help
python -m hydramind --help
```

### Runtime Configuration API

Configure modules at runtime via the EventBus:

```python
# Configure learning rate
await bus.publish(Message("learn/seed/config", {
    "learner_id": "model_v1",
    "lr": 0.001,
    "floor": 0.00001,
    "ceil": 0.02
}))

# Set optimization goals
await bus.publish(Message("optimizer/set_goal", {
    "name": "latency",
    "target": 10.0,
    "weight": 2.0,
    "direction": "min"
}))
```

---

## 📊 Configuration Sections

### Server Configuration

Controls the FastAPI control plane:

```yaml
server:
  enabled: true              # Enable REST API server
  host: "0.0.0.0"           # Bind address (0.0.0.0 for all interfaces)
  port: 8765                # Port number
  cors:                     # CORS allowed origins
    - "https://myapp.com"
    - "https://admin.myapp.com"
```

**Environment Overrides:**
```bash
export BRAIN_SERVER_ENABLED=true
export BRAIN_SERVER_HOST=0.0.0.0
export BRAIN_SERVER_PORT=8765
export BRAIN_SERVER_CORS="https://myapp.com,https://admin.myapp.com"
```

### Logging Configuration

Controls logging behavior and output:

```yaml
logging:
  level: "INFO"             # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  json: true               # Use JSON format for structured logs
  file_path: "./logs/hydramind.log"  # Log file location
  rotate_bytes: 15000000   # Rotate when file reaches 15MB
  backups: 5               # Keep 5 backup files
```

**Environment Overrides:**
```bash
export BRAIN_LOGGING_LEVEL=DEBUG
export BRAIN_LOGGING_JSON=true
export BRAIN_LOGGING_FILE_PATH=./logs/debug.log
```

### Feature Flags

Enable or disable specific modules and capabilities:

```yaml
features:
  # Intelligence modules
  seed: true               # Adaptive learning rate optimization
  replay: true             # Experience replay buffer
  anomaly: true            # Real-time anomaly detection
  optimizer: true          # System optimization
  meta_planner: true       # Strategy selection

  # Domain examples (disable for production)
  drones: false
  robots: false
  trading: false
  db: false

  # Custom features
  my_smart_home: true
  autonomous_vehicles: true
```

**Environment Overrides:**
```bash
export BRAIN_FEATURES_SEED=true
export BRAIN_FEATURES_ANOMALY=true
export BRAIN_FEATURES_MY_SMART_HOME=true
```

### Data Layer Configuration

Controls data storage and processing:

```yaml
# Event storage
event_db: "./brain_events.sqlite"

# Shared memory and snapshots
snapshot_dir: "./snapshots"
snapshot_size: 2097152           # Size of memory-mapped snapshot (bytes, default: 2MB)
ring_name: "hydra_ring"           # Must be unique per system
ring_capacity: 16384              # Number of items in ring buffer
ring_item_bytes: 2048             # Max size per item (bytes)
```

**Environment Overrides:**
```bash
export BRAIN_EVENT_DB=./data/events.db
export BRAIN_SNAPSHOT_DIR=./data/snapshots
export BRAIN_SNAPSHOT_SIZE=4194304    # 4MB snapshot
export BRAIN_RING_CAPACITY=32768
```

### Security Configuration

Controls access and rate limiting:

```yaml
policy_allowlist: null           # null = allow all topics
                                 # or: ["safe/*", "public/*"]
max_events_per_sec: 50000        # Global rate limit
```

**Environment Overrides:**
```bash
export BRAIN_POLICY_ALLOWLIST="safe/*,public/*"
export BRAIN_MAX_EVENTS_PER_SEC=100000
```

---

## 🎨 Configuration Examples

### Development Configuration

```yaml
# development.yaml
server:
  enabled: true
  host: "127.0.0.1"
  port: 8765

logging:
  level: "DEBUG"
  json: true
  file_path: "./logs/development.log"

features:
  seed: true
  replay: true
  anomaly: true
  optimizer: true
  meta_planner: true

  # Keep examples for testing
  drones: true
  robots: true

# Development settings
custom:
  debug_mode: true
  hot_reload: true
  mock_sensors: true
```

### Production Configuration

```yaml
# production.yaml
server:
  enabled: true
  host: "0.0.0.0"
  port: 8765
  cors: ["https://myapp.com"]

logging:
  level: "INFO"
  json: true
  file_path: "/var/log/hydramind/production.log"
  rotate_bytes: 100000000  # 100MB
  backups: 10

features:
  seed: true
  replay: true
  anomaly: true
  optimizer: true
  meta_planner: true

  # Disable examples in production
  drones: false
  robots: false
  trading: false
  db: false

  # Enable production modules
  smart_home: true
  security_system: true

# Production settings
custom:
  data_dir: "/var/lib/hydramind"
  backup_dir: "/var/backups/hydramind"
  sensor_timeout: 30.0
  alert_webhook: "https://alerts.mycompany.com/hydramind"
```

### Edge Device Configuration

```yaml
# edge-device.yaml
server:
  enabled: false  # No web interface on edge devices

logging:
  level: "WARNING"
  json: true
  file_path: "./hydramind.log"

features:
  seed: true
  anomaly: true
  # Minimal features for edge deployment

ring_capacity: 4096      # Smaller for memory-constrained devices
ring_item_bytes: 512     # Smaller items

# Edge-specific settings
custom:
  sensor_polling_rate: 1.0  # Hz
  battery_monitoring: true
  offline_mode: true
  sync_interval: 300.0  # 5 minutes
```

---

## 🔧 Advanced Configuration

### Module-Specific Configuration

Configure individual modules:

```yaml
# Module configuration in custom section
custom:
  # Temperature monitor settings
  temperature_monitor:
    target_temp: 22.0
    tolerance: 2.0
    polling_interval: 5.0

  # Security system settings
  security_system:
    motion_zones: ["living_room", "kitchen", "bedroom"]
    alert_delay: 30.0
    camera_resolution: "1080p"

  # Database analyzer settings
  db_analyzer:
    connection_string: "postgresql://user:pass@localhost/analytics"
    query_timeout: 30.0
    slow_query_threshold: 1000  # ms
```

### Environment Variable Expansion

Use environment variables in configuration:

```yaml
custom:
  api_key: "${API_KEY}"           # Expands to env var
  data_dir: "${HYDRAMIND_DATA_DIR:-./data}"  # With default
  model_path: "${MODELS_DIR}/latest.pth"
```

### Configuration Validation

HydraMind validates configuration at startup:

```bash
# Validate configuration without starting
python -m hydramind --config config.yaml --dry-run

# Expected output:
# ✓ Configuration loaded successfully
# ✓ All modules configured
# ✓ No validation errors
```

---

## 📈 Performance Tuning

### Memory Configuration

```yaml
# For high-throughput scenarios
ring_capacity: 65536         # Increase for more buffering
ring_item_bytes: 4096        # Larger items for complex data

# For memory-constrained environments
ring_capacity: 4096          # Reduce for limited memory
ring_item_bytes: 256         # Smaller items
```

### CPU Configuration

```yaml
# For CPU-intensive workloads
features:
  optimizer: true
  meta_planner: true

custom:
  thread_pool_size: 16       # More threads for parallel processing
  process_pool_size: 8       # More processes for isolation
```

### Network Configuration

```yaml
# For high-frequency network operations
max_events_per_sec: 100000   # Higher rate limit

# For bandwidth-constrained environments
max_events_per_sec: 1000     # Lower rate limit
```

---

## 🔒 Security Configuration

### Secure Production Setup

```yaml
# production-secure.yaml
server:
  enabled: true
  host: "127.0.0.1"          # Localhost only
  port: 8765
  cors: []                   # No CORS for security

logging:
  level: "INFO"
  json: true
  file_path: "/var/log/hydramind/secure.log"

features:
  anomaly: true              # Enable anomaly detection
  optimizer: true            # Enable optimization

# Restrict to safe topics only
policy_allowlist:
  - "sensor/*"
  - "control/*"
  - "health/*"

# High security settings
custom:
  encryption_enabled: true
  audit_all_events: true
  require_authentication: true
```

### Development Security

```yaml
# development-secure.yaml
server:
  enabled: true
  host: "127.0.0.1"
  port: 8765

logging:
  level: "DEBUG"
  json: true

# Allow all topics for development
policy_allowlist: null

features:
  # Enable all for testing
  seed: true
  replay: true
  anomaly: true
  optimizer: true
  meta_planner: true

  # Keep examples for learning
  drones: true
  robots: true
```

---

## 🚨 Configuration Troubleshooting

### Common Configuration Issues

**Module not starting:**
```yaml
# Problem: Module fails to initialize
features:
  my_module: true  # Make sure feature flag is enabled

custom:
  my_module:
    required_setting: "value"  # Provide required configuration
```

**Performance issues:**
```yaml
# Problem: High memory usage
ring_capacity: 8192          # Reduce from default 16384
ring_item_bytes: 1024        # Reduce from default 2048

# Problem: Slow event processing
max_events_per_sec: 10000    # Reduce rate limit if needed
```

**Security issues:**
```yaml
# Problem: Unauthorized access
policy_allowlist:
  - "safe/*"
  - "internal/*"

# Problem: Rate limiting too strict
max_events_per_sec: 1000     # Increase if legitimate traffic is blocked
```

### Configuration Validation

```bash
# Check configuration syntax
python -c "
from hydramind.core.config import load_config
try:
    config = load_config('config.yaml')
    print('✓ Configuration syntax is valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"

# Test configuration with HydraMind
python -m hydramind --config config.yaml --dry-run

# Validate specific settings
python -c "
from hydramind.core.config import load_config
config = load_config('config.yaml')
print(f'Ring capacity: {config.ring_capacity}')
print(f'Features enabled: {[k for k, v in config.features.__dict__.items() if v]}')
"
```

### Configuration Migration

When upgrading HydraMind versions:

```bash
# Backup current configuration
cp hydramind.yaml hydramind.yaml.backup

# Check for deprecated settings
python -m hydramind --config hydramind.yaml --validate

# Update configuration based on warnings
# nano hydramind.yaml

# Test updated configuration
python -m hydramind --config hydramind.yaml --dry-run
```

---

## 📚 Related Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[INSTALL.md](INSTALL.md)** - Installation and setup instructions
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 10-minute tutorial
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[API/](API/)** - REST API documentation
- **[EVENTS.md](EVENTS.md)** - Event topics and message formats

---

## 🔄 Version Compatibility

| HydraMind Version | Config Format Version | Migration Required |
|-------------------|----------------------|-------------------|
| **1.0.0** | 1.0 | ✅ New installation |
| **< 1.0.0** | - | ✅ Full reinstall recommended |

**Configuration format is stable** - No breaking changes expected in patch releases.

---

**Configuration is the foundation of your HydraMind deployment. Take time to understand and customize it for your specific use case.**
