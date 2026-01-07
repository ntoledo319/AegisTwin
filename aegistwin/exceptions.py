"""
AegisTwin Exceptions

Custom exception classes for AegisTwin.

@ai_prompt: Use these exceptions for error handling in AegisTwin.
@context_boundary: aegistwin/exceptions

# AI-GENERATED 2026-01-06
"""


class AegisTwinError(Exception):
    """Base exception for all AegisTwin errors."""
    pass


class PolicyDeniedError(AegisTwinError):
    """Raised when an action is denied by policy."""

    def __init__(self, action: str, resource: str, reason: str, policy_id: str = None):
        self.action = action
        self.resource = resource
        self.reason = reason
        self.policy_id = policy_id
        super().__init__(f"Policy denied: {action} on {resource} - {reason}")


class ReplayError(AegisTwinError):
    """Raised when replay fails or diverges."""

    def __init__(self, run_id: str, message: str, divergences: list = None):
        self.run_id = run_id
        self.divergences = divergences or []
        super().__init__(f"Replay error for {run_id}: {message}")


class ConfigurationError(AegisTwinError):
    """Raised when configuration is invalid."""
    pass


class ConnectorError(AegisTwinError):
    """Raised when a connector operation fails."""

    def __init__(self, connector_name: str, message: str):
        self.connector_name = connector_name
        super().__init__(f"Connector '{connector_name}' error: {message}")


class PipelineError(AegisTwinError):
    """Raised when pipeline processing fails."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(f"Pipeline error at {stage}: {message}")


class EventError(AegisTwinError):
    """Raised when event processing fails."""
    pass


class StorageError(AegisTwinError):
    """Raised when storage operations fail."""
    pass
