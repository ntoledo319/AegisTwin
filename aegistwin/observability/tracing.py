"""
AegisTwin OpenTelemetry Tracing

Provides distributed tracing capabilities using OpenTelemetry SDK.

@ai_prompt: Initialize tracing once at startup with init_tracing().
@context_boundary: aegistwin/observability/tracing

## Environment Variables
- OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint
- OTEL_SERVICE_NAME: Service name for traces
- OTEL_TRACES_EXPORTER: Exporter type (otlp, console, none)

# AI-GENERATED 2026-01-07
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

# Try importing OpenTelemetry, provide stubs if not available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None
    TracerProvider = None
    Span = None

# Try importing OTLP exporter
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    OTLPSpanExporter = None


@dataclass
class TracingConfig:
    """
    Configuration for OpenTelemetry tracing.
    
    Attributes:
        service_name: Name of the service for trace identification
        otlp_endpoint: OTLP collector endpoint (optional)
        console_export: Whether to export to console (for debugging)
        enabled: Whether tracing is enabled
    """
    service_name: str = "aegistwin"
    otlp_endpoint: Optional[str] = None
    console_export: bool = False
    enabled: bool = True
    
    @classmethod
    def from_env(cls) -> "TracingConfig":
        """Create config from environment variables."""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "aegistwin"),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            console_export=os.getenv("OTEL_TRACES_EXPORTER", "").lower() == "console",
            enabled=os.getenv("OTEL_TRACES_EXPORTER", "").lower() != "none",
        )


# Global state
_tracer_provider: Optional["TracerProvider"] = None
_initialized: bool = False


def init_tracing(
    service_name: str = "aegistwin",
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
    config: Optional[TracingConfig] = None,
) -> bool:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint (optional)
        console_export: Whether to export to console
        config: Optional TracingConfig object (overrides other params)
        
    Returns:
        True if tracing was initialized, False if unavailable
    """
    global _tracer_provider, _initialized
    
    if _initialized:
        return True
    
    if not OTEL_AVAILABLE:
        print("Warning: OpenTelemetry not available. Install with 'pip install opentelemetry-api opentelemetry-sdk'")
        return False
    
    # Use config if provided
    if config:
        service_name = config.service_name
        otlp_endpoint = config.otlp_endpoint
        console_export = config.console_export
        if not config.enabled:
            _initialized = True
            return False
    
    # Check environment for overrides
    env_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if env_endpoint:
        otlp_endpoint = env_endpoint
    
    env_service = os.getenv("OTEL_SERVICE_NAME")
    if env_service:
        service_name = env_service
    
    if os.getenv("OTEL_TRACES_EXPORTER", "").lower() == "console":
        console_export = True
    
    # Create resource with service info
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "0.1.0",
    })
    
    # Create provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Add exporters
    if console_export:
        _tracer_provider.add_span_processor(
            SimpleSpanProcessor(ConsoleSpanExporter())
        )
    
    if otlp_endpoint and OTLP_AVAILABLE:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    
    # Set global provider
    trace.set_tracer_provider(_tracer_provider)
    
    _initialized = True
    return True


def shutdown_tracing() -> None:
    """Shutdown tracing and flush pending spans."""
    global _tracer_provider, _initialized
    
    if _tracer_provider and hasattr(_tracer_provider, 'shutdown'):
        _tracer_provider.shutdown()
    
    _tracer_provider = None
    _initialized = False


def get_tracer(name: str = "aegistwin") -> Union["trace.Tracer", "NoOpTracer"]:
    """
    Get a tracer instance.
    
    Args:
        name: Name for the tracer (usually module name)
        
    Returns:
        OpenTelemetry Tracer or NoOpTracer if not available
    """
    if not OTEL_AVAILABLE or not _initialized:
        return NoOpTracer()
    
    return trace.get_tracer(name)


class NoOpSpan:
    """No-op span for when tracing is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    
    def set_status(self, status: Any) -> None:
        pass
    
    def record_exception(self, exception: Exception) -> None:
        pass
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        pass


class NoOpTracer:
    """No-op tracer for when OpenTelemetry is not available."""
    
    def start_as_current_span(self, name: str, **kwargs) -> NoOpSpan:
        return NoOpSpan()
    
    def start_span(self, name: str, **kwargs) -> NoOpSpan:
        return NoOpSpan()


F = TypeVar('F', bound=Callable[..., Any])


def trace_event(span_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator to trace a function as a span.
    
    Args:
        span_name: Optional name for the span (defaults to function name)
        
    Returns:
        Decorated function
        
    Example:
        @trace_event("process_data")
        def my_function(data):
            return process(data)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__ or "aegistwin")
            name = span_name or func.__name__
            
            with tracer.start_as_current_span(name) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if hasattr(span, 'record_exception'):
                        span.record_exception(e)
                    if hasattr(span, 'set_status') and OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    
    return decorator


@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating a trace span.
    
    Args:
        name: Name of the span
        attributes: Optional attributes to add to the span
        
    Example:
        with trace_span("my_operation", {"key": "value"}):
            do_something()
    """
    tracer = get_tracer("aegistwin")
    
    with tracer.start_as_current_span(name) as span:
        if attributes and hasattr(span, 'set_attribute'):
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def add_event_attributes(span: Any, event: Any) -> None:
    """
    Add standard AegisTwin event attributes to a span.
    
    Args:
        span: OpenTelemetry span
        event: AegisTwin event object
    """
    if not hasattr(span, 'set_attribute'):
        return
    
    if hasattr(event, 'event_type'):
        span.set_attribute("aegistwin.event.type", str(event.event_type.value))
    if hasattr(event, 'event_id'):
        span.set_attribute("aegistwin.event.id", event.event_id)
    if hasattr(event, 'run_id'):
        span.set_attribute("aegistwin.event.run_id", event.run_id)
    if hasattr(event, 'parent_event_id') and event.parent_event_id:
        span.set_attribute("aegistwin.event.parent_id", event.parent_event_id)


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers for propagation.
    
    Args:
        headers: Headers dictionary to inject into
        
    Returns:
        Headers with trace context
    """
    if not OTEL_AVAILABLE:
        return headers
    
    propagator = TraceContextTextMapPropagator()
    propagator.inject(headers)
    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[Any]:
    """
    Extract trace context from headers.
    
    Args:
        headers: Headers dictionary to extract from
        
    Returns:
        Extracted context or None
    """
    if not OTEL_AVAILABLE:
        return None
    
    propagator = TraceContextTextMapPropagator()
    return propagator.extract(headers)
