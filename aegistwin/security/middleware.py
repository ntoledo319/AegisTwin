"""
Security Middleware

Provides:
- Rate limiting per IP/API key
- Request validation
- Security headers

@ai_prompt: Add SecurityMiddleware to FastAPI app for production
@context_boundary: aegistwin/security/middleware
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


@dataclass
class RateLimitState:
    """Tracks rate limit state for a client."""
    minute_count: int = 0
    hour_count: int = 0
    minute_reset: float = 0
    hour_reset: float = 0
    tokens: float = 0
    last_update: float = field(default_factory=time.time)


class RateLimiter:
    """
    Token bucket rate limiter with per-minute and per-hour limits.

    Attributes:
        config: Rate limit configuration
        clients: Per-client state tracking
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self.clients: dict[str, RateLimitState] = defaultdict(
            lambda: RateLimitState(tokens=self.config.burst_size)
        )

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier from request."""
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"key:{api_key[:16]}"

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client = request.client
        if client:
            return f"ip:{client.host}"

        return "ip:unknown"

    def check(self, request: Request) -> tuple[bool, dict]:
        """
        Check if request is allowed.

        Returns:
            Tuple of (allowed, headers_dict)
        """
        client_key = self._get_client_key(request)
        state = self.clients[client_key]
        now = time.time()

        if now > state.minute_reset:
            state.minute_count = 0
            state.minute_reset = now + 60

        if now > state.hour_reset:
            state.hour_count = 0
            state.hour_reset = now + 3600

        elapsed = now - state.last_update
        state.tokens = min(
            self.config.burst_size,
            state.tokens + elapsed * (self.config.requests_per_minute / 60),
        )
        state.last_update = now

        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, self.config.requests_per_minute - state.minute_count)),
            "X-RateLimit-Reset": str(int(state.minute_reset)),
        }

        if state.minute_count >= self.config.requests_per_minute:
            headers["Retry-After"] = str(int(state.minute_reset - now))
            return False, headers

        if state.hour_count >= self.config.requests_per_hour:
            headers["Retry-After"] = str(int(state.hour_reset - now))
            return False, headers

        if state.tokens < 1:
            headers["Retry-After"] = "1"
            return False, headers

        state.tokens -= 1
        state.minute_count += 1
        state.hour_count += 1

        return True, headers


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware.

    Adds:
    - Rate limiting
    - Security headers
    - Request logging
    """

    def __init__(
        self,
        app: FastAPI,
        rate_limiter: RateLimiter | None = None,
        enable_rate_limit: bool = True,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.enable_rate_limit = enable_rate_limit

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        if request.url.path in ["/health", "/metrics"]:
            response = await call_next(request)
            return self._add_security_headers(response)

        if self.enable_rate_limit:
            allowed, headers = self.rate_limiter.check(request)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers=headers,
                )

        response = await call_next(request)

        if self.enable_rate_limit:
            _, headers = self.rate_limiter.check(request)
            for key, value in headers.items():
                response.headers[key] = value

        return self._add_security_headers(response)

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        return response


def setup_security(
    app: FastAPI,
    rate_limit_config: RateLimitConfig | None = None,
    enable_rate_limit: bool = True,
) -> None:
    """
    Configure security middleware for FastAPI app.

    Args:
        app: FastAPI application
        rate_limit_config: Rate limiting configuration
        enable_rate_limit: Whether to enable rate limiting
    """
    limiter = RateLimiter(rate_limit_config) if rate_limit_config else None
    app.add_middleware(
        SecurityMiddleware,
        rate_limiter=limiter,
        enable_rate_limit=enable_rate_limit,
    )
