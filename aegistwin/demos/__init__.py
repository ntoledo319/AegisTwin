"""
AegisTwin Demos Module

Provides the 3 buyer demos that demonstrate core capabilities.

@ai_prompt: Run all demos with `make demo` or `python -m aegistwin demo`
@context_boundary: aegistwin/demos

## Demo A: Managed Pipeline
Synthetic events -> normalize -> analyze -> graph update -> memory update -> query -> response

## Demo B: Deterministic Replay + Trace
Run pipeline -> record run-id -> replay -> emit trace JSON showing decisions + payload hashes

## Demo C: Policy Gate
Attempt forbidden module -> deny -> audit record -> clean error output

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

from aegistwin.demos.runner import run_demo, run_all_demos

__all__ = ["run_demo", "run_all_demos"]
