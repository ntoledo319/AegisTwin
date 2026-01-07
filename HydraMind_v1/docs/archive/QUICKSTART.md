# HydraMind Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Install

```bash
cd HydraMind_v1
pip install -r requirements.txt
```

### Step 2: Run the Demo

```bash
# Run with example modules
python -m hydramind

# You should see:
# ============================================================
# HydraMind v1.0 - Universal Cognitive Kernel
# ============================================================
# ... initialization logs ...
# HydraMind is now running!
# Press Ctrl+C to shutdown gracefully
```

### Step 3: Enable Control Plane (Optional)

```bash
# Install FastAPI
pip install fastapi uvicorn

# Edit hydramind.yaml
# Change: server.enabled: true

# Run again
python -m hydramind

# Visit: http://localhost:8765/health
```

### Step 4: Create Your First Module

Create `myproject/modules/hello.py`:

```python
from hydramind.core.module import Module
from hydramind.core.bus import Message
import time

class HelloModule(Module):
    name = "hello"
    
    async def on_message(self, msg: Message):
        if msg.topic == "hello/world":
            name = msg.data.get("name", "World")
            
            self.log.info(f"Hello, {name}!")
            
            await self.emit("hello/response", {
                "message": f"Hello, {name}!",
                "ts": time.time()
            })
```

Create `myproject/brain.py`:

```python
from hydramind.brain import HydraBrain
from myproject.modules.hello import HelloModule

class MyBrain(HydraBrain):
    async def start(self):
        # Add your module
        hello = HelloModule(self.bus, self.exec, self.policy)
        self.registry.add(hello, ["hello/world"])
        
        # Important: call parent start
        await super().start()
        
        # Test it
        await self.bus.publish(Message("hello/world", {"name": "HydraMind"}))

if __name__ == "__main__":
    import asyncio
    from hydramind.core.bus import Message
    
    brain = MyBrain()
    brain._setup_signal_handlers()
    
    try:
        asyncio.run(brain.start())
        
        # Keep running
        while not brain._shutdown_requested:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
```

Run it:

```bash
python myproject/brain.py
```

You should see:
```
[INFO] Module.hello | Hello, HydraMind!
```

### Step 5: Build Your System

Now delete the example modules and build your actual system:

1. **Delete examples**: Remove drone/robot/trading modules from `hydramind/modules/domain_examples.py`
2. **Create your modules**: Add your domain logic in `myproject/modules/`
3. **Configure**: Edit `hydramind.yaml` with your settings
4. **Register modules**: Wire them up in your `MyBrain` class
5. **Run**: `python myproject/brain.py`

---

## 📚 Next Steps

- Read the [main README](README.md) for comprehensive documentation
- Study the intelligence modules (seed_optimizer, replay, anomaly, etc)
- Check out the sensor hub pattern for high-frequency data
- Explore the DAG executor for task orchestration
- Enable the FastAPI control plane for external control

---

## 🎯 Common Use Cases

### Smart Home
- Subscribe to: `sensor/*`
- Emit to: `device/control/*`
- Use: AnomalyLab for unusual patterns

### Drone Swarm
- Subscribe to: `drone/*/position`
- Emit to: `drone/*/command`
- Use: MetaPlanner for formation strategies

### Trading System
- Subscribe to: `market/tick`
- Emit to: `order/place`
- Use: ReplayBuffer for strategy training

### Robotics
- Subscribe to: `vision/*`, `sensor/*`
- Emit to: `actuator/*`, `motion/*`
- Use: DAG for multi-step tasks

---

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'hydramind'"**
- Run from the HydraMind_v1 directory
- Or install: `pip install -e .`

**"FileExistsError" on ring buffer**
- Shared memory name collision
- Change `ring_name` in config
- Or reboot to clear shared memory

**High CPU usage**
- Reduce telemetry interval in sensors.py
- Disable demo_loop in your implementation
- Check for infinite loops in modules

**Events not arriving**
- Check subscriptions match topics
- Verify policy allowlist if configured
- Check logs for policy rejections

---

## 💡 Tips

- **Start simple**: Get one module working first
- **Use logging**: `self.log.info()` is your friend
- **Monitor metrics**: Use `/metrics` endpoint
- **Test patterns**: Emit test events via control plane
- **Read the code**: The core is well-documented

---

**Happy building! 🚀**

*HydraMind - Built once, adapted infinitely*
