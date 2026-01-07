"""
AegisTwin Runtime Module

Core runtime module providing event-driven agent execution.

@ai_prompt: Use AegisTwinRuntime for pipeline execution.
@context_boundary: aegistwin/runtime
"""

from aegistwin.runtime.core import AegisTwinRuntime, EventBus
from aegistwin.runtime.async_core import AsyncAegisTwinRuntime, AsyncEventBus

__all__ = [
    "AegisTwinRuntime",
    "EventBus",
    "AsyncAegisTwinRuntime",
    "AsyncEventBus",
]
