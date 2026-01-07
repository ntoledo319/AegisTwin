"""
AegisTwin Governance Module

Provides policy enforcement, audit logging, and access control.

@ai_prompt: Use PolicyEngine to check permissions before actions.
@context_boundary: aegistwin/governance
"""

from aegistwin.governance.policy import PolicyEngine, Policy

__all__ = ["PolicyEngine", "Policy"]
