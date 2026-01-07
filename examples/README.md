# AegisTwin Examples

This directory contains examples demonstrating how to use AegisTwin in different scenarios.

## Running Examples

```bash
# Install AegisTwin first
pip install -e .

# Run any example
python examples/01_basic_sdk_usage.py
python examples/02_policy_enforcement.py
python examples/03_replay_debugging.py
```

## Examples

### 1. Basic SDK Usage (`01_basic_sdk_usage.py`)
The simplest way to use AegisTwin as an SDK. Shows:
- Initializing AegisTwin
- Ingesting data
- Querying the system
- Handling run completion

### 2. Policy Enforcement (`02_policy_enforcement.py`)
How to configure custom policies to control agent behavior. Shows:
- Creating custom policies
- Adding policies to the engine
- Testing policy enforcement
- Handling denied actions

### 3. Replay & Debugging (`03_replay_debugging.py`)
Recording and replaying agent runs for debugging. Shows:
- Recording events during execution
- Replaying previous runs
- Verifying deterministic behavior
- Accessing trace artifacts

## Next Steps

- See the [Embedding Guide](../docs/13_EMBEDDING_GUIDE.md) for integration patterns
- Check the [API documentation](../docs/10_ARCHITECTURE.md) for advanced usage
- Run the full demos with `make demo`
