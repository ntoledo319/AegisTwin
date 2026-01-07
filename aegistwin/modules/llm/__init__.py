"""
AegisTwin LLM Module

Provides LLM provider interfaces with policy-gated access and audit logging.

@ai_prompt: Use get_provider() to get an LLM provider, then call complete() or stream().
@context_boundary: aegistwin/modules/llm

## Quick Start
```python
from aegistwin.modules.llm import get_provider

provider = get_provider("mock")
response = provider.complete("Hello, world!")
```

# AI-GENERATED 2026-01-07
"""

from aegistwin.modules.llm.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from aegistwin.modules.llm.providers import (
    MockProvider,
    OpenAIProvider,
    AnthropicProvider,
    get_provider,
)

__all__ = [
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "MockProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_provider",
]
