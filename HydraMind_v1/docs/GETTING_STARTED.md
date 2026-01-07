# Getting Started - 10-Minute Tutorial

Welcome to HydraMind v1! This guide will get you up and running with your first intelligent system in just 10 minutes.

---

## ⏱️ What You'll Build

By the end of this tutorial, you'll have:
- ✅ HydraMind installed and running
- ✅ A custom module that processes sensor data
- ✅ Real-time event processing and responses
- ✅ A working intelligent system foundation

---

## 🚀 Step 1: Installation (2 minutes)

### Quick Install

```bash
# Install HydraMind
pip install hydramind

# Verify installation
python -c "import hydramind; print('✅ HydraMind installed!')"
```

### Start HydraMind

```bash
# Run with default configuration
python -m hydramind

# You should see startup logs like:
# HydraMind v1.0 - Universal Cognitive Kernel
# Event store initialized: ./brain_events.sqlite
# Event bus initialized
# Module registry initialized
# HydraMind is now running!
```

**🎉 Congratulations! HydraMind is running!**

---

## 🏗️ Step 2: Create Your First Module (3 minutes)

Let's create a simple temperature monitoring module.

### Create Module File

```bash
# Create your project directory
mkdir my-smart-home
cd my-smart-home

# Create modules directory
mkdir modules

# Create your first module
cat > modules/temperature_monitor.py << 'EOF'
from hydramind.core.module import Module
from hydramind.core.bus import Message

class TemperatureMonitor(Module):
    name = "temperature_monitor"

    def __init__(self, bus, ex, policy, target_temp=22.0):
        super().__init__(bus, ex, policy)
        self.target_temp = target_temp
        self.log.info(f"Temperature monitor initialized (target: {target_temp}°C)")

    async def _handle_message(self, msg: Message):
        """Process temperature readings"""
        if msg.topic == "sensor/temperature":
            current_temp = msg.data["value"]

            self.log.info(f"Temperature reading: {current_temp}°C")

            # Check if temperature is too high
            if current_temp > self.target_temp + 2:
                await self.emit("hvac/command", {
                    "action": "cool",
                    "target": self.target_temp,
                    "reason": "temperature_too_high"
                })
                self.log.warning(f"Temperature too high: {current_temp}°C")

            # Check if temperature is too low
            elif current_temp < self.target_temp - 2:
                await self.emit("hvac/command", {
                    "action": "heat",
                    "target": self.target_temp,
                    "reason": "temperature_too_low"
                })
                self.log.warning(f"Temperature too low: {current_temp}°C")
EOF
```

### Create Your Brain

```bash
# Create your brain file
cat > brain.py << 'EOF'
from hydramind.brain import HydraBrain
from modules.temperature_monitor import TemperatureMonitor

class SmartHomeBrain(HydraBrain):
    async def start(self):
        # Create and register your temperature monitor
        temp_monitor = TemperatureMonitor(
            self.bus, self.exec, self.policy,
            target_temp=22.0  # 22°C target temperature
        )

        # Subscribe to temperature sensor events
        self.registry.add(temp_monitor, ["sensor/temperature"])

        # Call parent to start core modules
        await super().start()

# Run your smart home
if __name__ == "__main__":
    import asyncio
    brain = SmartHomeBrain()
    asyncio.run(brain.start())
EOF
```

### Configure HydraMind

```bash
# Create configuration file
cat > hydramind.yaml << 'EOF'
# Smart Home Configuration
server:
  enabled: true
  host: 0.0.0.0
  port: 8765

features:
  # Enable intelligence modules
  seed: true
  replay: true
  anomaly: true
  optimizer: true

  # Disable example modules for cleaner output
  drones: false
  robots: false
  trading: false
  db: false

# Custom configuration for your modules
custom:
  target_temperature: 22.0
  sensor_polling_interval: 5.0
EOF
```

---

## 🧪 Step 3: Test Your Module (3 minutes)

### Start Your System

```bash
# Run your smart home brain
python brain.py
```

You should see:
```
HydraMind v1.0 - Universal Cognitive Kernel
System: [your system info]
Temperature monitor initialized (target: 22.0°C)
Module 'temperature_monitor' started successfully
HydraMind is now running!
```

### Test with Sample Data

Open another terminal and send test temperature readings:

```bash
# Send a normal temperature reading
curl -X POST http://localhost:8765/bus/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sensor/temperature",
    "data": {"value": 23.5, "unit": "C", "sensor_id": "living_room"}
  }'

# Send a high temperature reading
curl -X POST http://localhost:8765/bus/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sensor/temperature",
    "data": {"value": 26.0, "unit": "C", "sensor_id": "living_room"}
  }'

# Send a low temperature reading
curl -X POST http://localhost:8765/bus/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "sensor/temperature",
    "data": {"value": 18.0, "unit": "C", "sensor_id": "living_room"}
  }'
```

### Check the Results

You should see in your brain terminal:
```
Temperature reading: 23.5°C
Temperature reading: 26.0°C
Temperature too high: 26.0°C
hvac/command emitted: {"action": "cool", "target": 22.0}
Temperature reading: 18.0°C
Temperature too low: 18.0°C
hvac/command emitted: {"action": "heat", "target": 22.0}
```

**🎉 Excellent! Your intelligent temperature monitoring system is working!**

---

## 📊 Step 4: Monitor Your System (2 minutes)

### Check System Health

```bash
# Check overall health
curl http://localhost:8765/health

# Check available modules
curl http://localhost:8765/modules

# Check system metrics
curl http://localhost:8765/metrics
```

### View Logs

```bash
# Check recent logs
tail -f logs/hydramind.log

# You should see your temperature monitoring activity
```

### Query Event History

```bash
# Query recent temperature events
curl -X POST http://localhost:8765/events/query \
  -H "Content-Type: application/json" \
  -d '{
    "topic_pattern": "sensor/temperature",
    "limit": 10
  }'

# Query HVAC commands
curl -X POST http://localhost:8765/events/query \
  -H "Content-Type: application/json" \
  -d '{
    "topic_pattern": "hvac/command",
    "limit": 10
  }'
```

---

## 🎓 What You've Learned

In just 10 minutes, you've built:

### ✅ **Core Concepts**
- **Modules** - Self-contained units of functionality
- **EventBus** - Communication between modules
- **Message handling** - Processing and responding to events
- **Configuration** - Customizing behavior

### ✅ **Intelligence Features**
- **Real-time processing** - Immediate response to sensor data
- **Decision making** - Automated HVAC control based on temperature
- **Logging and monitoring** - Complete observability
- **Error handling** - Robust operation with graceful failures

### ✅ **Production Features**
- **Health monitoring** - System status and performance metrics
- **API access** - Programmatic control and monitoring
- **Persistent storage** - Event history and audit trails
- **Scalable architecture** - Ready for additional modules

---

## 🚀 Next Steps

### Add More Intelligence

```python
# Add occupancy detection
class OccupancyMonitor(Module):
    name = "occupancy_monitor"

    async def _handle_message(self, msg: Message):
        if msg.topic == "sensor/motion":
            # Detect occupancy patterns
            await self.emit("hvac/adjust", {"mode": "eco"})

# Add energy optimization
class EnergyOptimizer(Module):
    name = "energy_optimizer"

    async def _handle_message(self, msg: Message):
        if msg.topic == "energy/usage":
            # Optimize based on usage patterns
            pass
```

### Connect Real Hardware

```python
# Add real sensor integration
import serial

class RealSensorHub(Module):
    name = "real_sensors"

    async def start(self):
        await super().start()
        self.serial = serial.Serial('/dev/ttyUSB0', 9600)

    async def _handle_message(self, msg: Message):
        if msg.topic == "sensor/poll":
            # Read from real sensors
            data = self.serial.readline()
            temp = parse_temperature(data)
            await self.emit("sensor/temperature", {"value": temp})
```

### Deploy to Production

```bash
# Use production configuration
cp production.yaml hydramind.yaml

# Run as service
sudo systemctl enable hydramind
sudo systemctl start hydramind

# Monitor with external tools
curl http://your-server:8765/health
```

---

## 🔧 Troubleshooting

### Common Issues

**Module not responding:**
```bash
# Check module registration
curl http://localhost:8765/modules

# Check event bus status
curl http://localhost:8765/metrics
```

**Configuration issues:**
```bash
# Test configuration
python -m hydramind --config hydramind.yaml --dry-run

# Check logs for errors
tail -f logs/hydramind.log
```

**Performance issues:**
```bash
# Check system resources
curl http://localhost:8765/metrics

# Monitor memory usage
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

---

## 📚 Advanced Learning

### Study the Modules

```bash
# Explore available modules
python -c "
from hydramind.modules import get_modules_by_category
intelligence = get_modules_by_category('intelligence')
print('Intelligence modules:', intelligence)
"

# Study a specific module
python -c "
from hydramind.modules.intelligence.seed_optimizer import SeedOptimizer
help(SeedOptimizer)
"
```

### Read the Documentation

- **[FEATURES.md](FEATURES.md)** - Complete feature breakdown
- **[API/](API/)** - REST API documentation
- **[EVENTS.md](EVENTS.md)** - Event topics and formats
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design deep dive

### Join the Community

- **GitHub Issues** - Ask questions, report bugs
- **GitHub Discussions** - Community conversations
- **Discord** - Real-time chat and support

---

## 🎯 What You've Accomplished

In **10 minutes**, you've:

1. ✅ **Installed HydraMind** and got it running
2. ✅ **Created a custom module** that processes real sensor data
3. ✅ **Built an intelligent system** that makes automated decisions
4. ✅ **Connected to monitoring** and can see real-time operation
5. ✅ **Learned the fundamentals** to build much more complex systems

**You're now ready to build production intelligent systems with HydraMind!** 🚀

The foundation you've built can scale to:
- Smart homes with dozens of sensors
- Drone swarms with coordinated flight
- Factory automation with predictive maintenance
- Any intelligent system you can imagine

**Welcome to the future of intelligent systems!**
