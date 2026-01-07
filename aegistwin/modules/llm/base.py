"""
AegisTwin LLM Base Classes

Abstract base class and data models for LLM providers.

@ai_prompt: Inherit from LLMProvider to create new provider implementations.
@context_boundary: aegistwin/modules/llm/base

# AI-GENERATED 2026-01-07
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """
    Request model for LLM completion.

    Attributes:
        prompt: The input prompt text
        model: Model identifier (e.g., 'gpt-4o-mini', 'claude-3-haiku')
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0 to 2.0)
        stop: Stop sequences
        messages: Alternative chat-style messages format
        metadata: Additional provider-specific parameters
    """
    prompt: str | None = None
    messages: list[dict[str, str]] | None = None
    model: str = "default"
    max_tokens: int = 1000
    temperature: float = 0.7
    stop: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_messages(self) -> list[dict[str, str]]:
        """Convert prompt to messages format if needed."""
        if self.messages:
            return self.messages
        if self.prompt:
            return [{"role": "user", "content": self.prompt}]
        return []


class LLMResponse(BaseModel):
    """
    Response model from LLM completion.

    Attributes:
        content: The generated text content
        model: Model that generated the response
        provider: Provider name (openai, anthropic, mock)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        finish_reason: Why generation stopped (stop, length, etc.)
        raw_response: Original provider response (optional)
    """
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    raw_response: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implement this class to add new LLM provider support.

    Attributes:
        name: Provider name identifier
        default_model: Default model to use

    ## Non-Negotiables
    - All requests must be logged for audit
    - API keys must never be logged
    - Errors must be handled gracefully
    """

    name: str = "base"
    default_model: str = "default"

    @abstractmethod
    def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: Input text prompt
            model: Model to use (defaults to provider default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a completion for the given prompt.

        Args:
            prompt: Input text prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            String chunks as they are generated
        """
        pass

    def complete_request(self, request: LLMRequest) -> LLMResponse:
        """
        Complete using a structured request object.

        Args:
            request: LLMRequest with all parameters

        Returns:
            LLMResponse with generated content
        """
        prompt = request.prompt
        if not prompt and request.messages:
            # Convert messages to prompt
            prompt = "\n".join(
                f"{m['role']}: {m['content']}"
                for m in request.messages
            )

        return self.complete(
            prompt=prompt or "",
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            **request.metadata
        )

    def is_available(self) -> bool:
        """
        Check if the provider is available (has credentials, etc.).

        Returns:
            True if provider can be used
        """
        return True


class LLMError(Exception):
    """Base exception for LLM errors."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        status_code: int | None = None,
        response: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.response = response


class RateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(LLMError):
    """Raised when authentication fails."""
    pass
