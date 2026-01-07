# Example HydraMind Projects

This directory contains example implementations showing how to build systems with HydraMind.

## Structure

```
examples/
├── simple_sensor/          # Basic sensor processing
├── smart_home/            # Home automation example
└── custom_template/       # Blank template to copy
```

## Getting Started

1. Copy a template:
```bash
cp -r examples/custom_template/ myproject/
cd myproject/
```

2. Customize the modules in `modules/`

3. Update `config.yaml` with your settings

4. Run:
```bash
python brain.py
```

## Examples Overview

### simple_sensor/
Basic pattern for reading sensor data and processing it.
- Single sensor module
- Data validation
- Simple analytics

### smart_home/
Home automation with multiple sensors and actuators.
- Temperature/humidity sensors
- Light control
- Automation rules
- Energy tracking

### custom_template/
Blank project template ready to customize.
- Starter module structure
- Configuration template
- Brain boilerplate

## Creating Your Own

1. **Define your domain**: What sensors/actuators/APIs?
2. **Design event topics**: `sensor/*`, `control/*`, etc.
3. **Build modules**: One per major subsystem
4. **Wire them up**: Register in brain.py
5. **Test**: Start simple, add complexity

## Tips

- Start with one module and test it
- Use the control plane (`/bus/publish`) to test event flows
- Monitor metrics to debug issues
- Check logs for policy rejections
- Read the core module code for patterns

---

*These are just starting points - the possibilities are infinite!*
