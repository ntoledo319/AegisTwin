"""
AegisTwin LLM Providers

Concrete implementations for various LLM providers.

@ai_prompt: Use get_provider("openai") or get_provider("mock") to get an instance.
@context_boundary: aegistwin/modules/llm/providers

# AI-GENERATED 2026-01-07
"""

import os
import time
from collections.abc import Iterator

import httpx

from aegistwin.modules.llm.base import (
    AuthenticationError,
    LLMError,
    LLMProvider,
    LLMResponse,
    RateLimitError,
)


class MockProvider(LLMProvider):
    """
    Mock LLM provider for testing.

    Returns deterministic responses without making API calls.
    """

    name = "mock"
    default_model = "mock-v1"

    def __init__(self, response_prefix: str = "Mock response to:"):
        """
        Initialize mock provider.

        Args:
            response_prefix: Prefix for mock responses
        """
        self.response_prefix = response_prefix
        self._call_count = 0

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a mock completion."""
        self._call_count += 1

        # Simulate latency
        latency = 50 + (len(prompt) * 0.5)

        # Generate deterministic response
        response_text = f"{self.response_prefix} {prompt[:100]}"
        if len(prompt) > 100:
            response_text += "..."

        # Add some variety based on call count
        response_text += f"\n\n[Mock call #{self._call_count}]"

        return LLMResponse(
            content=response_text,
            model=model or self.default_model,
            provider=self.name,
            input_tokens=len(prompt.split()),
            output_tokens=len(response_text.split()),
            latency_ms=latency,
            finish_reason="stop",
        )

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Stream a mock completion word by word."""
        response = self.complete(prompt, model, max_tokens, temperature, **kwargs)

        for word in response.content.split():
            yield word + " "
            time.sleep(0.01)  # Simulate streaming delay


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider.

    Uses httpx for API calls (no SDK dependency).
    Requires OPENAI_API_KEY environment variable.
    """

    name = "openai"
    default_model = "gpt-4o-mini"
    base_url = "https://api.openai.com/v1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate completion via OpenAI API."""
        if not self.is_available():
            raise AuthenticationError(
                "OpenAI API key not configured",
                provider=self.name
            )

        start_time = time.perf_counter()

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add optional parameters
        if "stop" in kwargs:
            payload["stop"] = kwargs["stop"]

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code == 429:
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider=self.name,
                        status_code=429,
                    )

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid API key",
                        provider=self.name,
                        status_code=401,
                    )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as e:
            raise LLMError(
                f"HTTP error: {str(e)}",
                provider=self.name,
            ) from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider=self.name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Stream completion via OpenAI API."""
        if not self.is_available():
            raise AuthenticationError(
                "OpenAI API key not configured",
                provider=self.name
            )

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        with httpx.Client() as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        import json
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude API provider.

    Uses httpx for API calls (no SDK dependency).
    Requires ANTHROPIC_API_KEY environment variable.
    """

    name = "anthropic"
    default_model = "claude-3-haiku-20240307"
    base_url = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate completion via Anthropic API."""
        if not self.is_available():
            raise AuthenticationError(
                "Anthropic API key not configured",
                provider=self.name
            )

        start_time = time.perf_counter()

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/messages",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code == 429:
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider=self.name,
                        status_code=429,
                    )

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid API key",
                        provider=self.name,
                        status_code=401,
                    )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPError as e:
            raise LLMError(
                f"HTTP error: {str(e)}",
                provider=self.name,
            ) from e

        latency_ms = (time.perf_counter() - start_time) * 1000

        content = data["content"][0]["text"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data["model"],
            provider=self.name,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            latency_ms=latency_ms,
            finish_reason=data.get("stop_reason", "stop"),
            raw_response=data,
        )

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Stream completion via Anthropic API."""
        if not self.is_available():
            raise AuthenticationError(
                "Anthropic API key not configured",
                provider=self.name
            )

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        with httpx.Client() as client:
            with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=self._get_headers(),
                json=payload,
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        import json
                        data = json.loads(line[6:])
                        if data["type"] == "content_block_delta":
                            yield data["delta"].get("text", "")


# Provider registry
_PROVIDERS: dict[str, type] = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(name: str = "mock", **kwargs) -> LLMProvider:
    """
    Get an LLM provider by name.

    Args:
        name: Provider name (mock, openai, anthropic)
        **kwargs: Provider-specific initialization arguments

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider name is unknown
    """
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider: {name}. "
            f"Available: {list(_PROVIDERS.keys())}"
        )

    return _PROVIDERS[name](**kwargs)


def register_provider(name: str, provider_class: type) -> None:
    """
    Register a custom LLM provider.

    Args:
        name: Provider name
        provider_class: LLMProvider subclass
    """
    _PROVIDERS[name] = provider_class
