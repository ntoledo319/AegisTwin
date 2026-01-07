"""
AegisTwin Runtime Module

Thin adapter over HydraMind runtime providing event-driven agent execution.

@ai_prompt: Use AegisTwinRuntime for pipeline execution. It wraps HydraMind.
@context_boundary: aegistwin/runtime
"""

from aegistwin.runtime.core import AegisTwinRuntime

__all__ = ["AegisTwinRuntime"]
