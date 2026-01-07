"""
AegisTwin Policy Engine

Provides configurable policy enforcement for access control and governance.
Policies can allow, deny, or require approval for actions on resources.

@ai_prompt: Define policies in YAML or programmatically. Check before every action.
@context_boundary: aegistwin/governance/policy

## Policy Structure
```yaml
policies:
  - id: deny-external-export
    action: export
    resource: "*"
    effect: deny
    reason: "External exports are not permitted"
```

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import fnmatch


class PolicyEffect(str, Enum):
    """Effect of a policy when matched."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class Policy:
    """
    A single policy rule.
    
    Attributes:
        id: Unique identifier for the policy
        action: Action pattern to match (supports wildcards)
        resource: Resource pattern to match (supports wildcards)
        effect: What happens when policy matches
        actor: Optional actor pattern (who is performing the action)
        reason: Human-readable reason for the policy
        priority: Higher priority policies are evaluated first
    """
    id: str
    action: str
    resource: str
    effect: PolicyEffect
    actor: str = "*"
    reason: str = ""
    priority: int = 0
    
    def matches(self, action: str, resource: str, actor: str = "*") -> bool:
        """Check if this policy matches the given action/resource/actor."""
        action_match = fnmatch.fnmatch(action, self.action)
        resource_match = fnmatch.fnmatch(resource, self.resource)
        actor_match = self.actor == "*" or fnmatch.fnmatch(actor, self.actor)
        return action_match and resource_match and actor_match


class PolicyEngine:
    """
    Engine for evaluating policies and enforcing access control.
    
    Policies are evaluated in priority order. The first matching policy
    determines the outcome. If no policy matches, the default is to allow.
    
    Supports optional OPA evaluator for enterprise policy-as-code.
    
    ## Non-Negotiables
    - All policy denials are logged
    - Forbidden modules are never allowed regardless of policy
    
    @ai_prompt: Initialize with default policies, then add custom ones.
    """
    
    # Modules that are NEVER allowed (hardcoded security)
    FORBIDDEN_MODULES = [
        "system.shell",
        "system.exec",
        "network.external",
        "data.export_pii",
    ]
    
    def __init__(self):
        self._policies: List[Policy] = []
        self._opa_evaluator: Optional[Any] = None
        self._load_default_policies()
    
    def set_opa_evaluator(self, evaluator: Any) -> None:
        """
        Set an OPA evaluator for policy-as-code support.
        
        When set, OPA is used as the primary policy engine,
        with built-in policies as fallback.
        
        Args:
            evaluator: OPAEvaluator instance
        """
        self._opa_evaluator = evaluator
    
    def _load_default_policies(self) -> None:
        """Load default security policies."""
        defaults = [
            # Deny forbidden modules
            Policy(
                id="deny-forbidden-modules",
                action="*",
                resource="system.*",
                effect=PolicyEffect.DENY,
                reason="System modules are restricted",
                priority=1000,
            ),
            # Deny PII export
            Policy(
                id="deny-pii-export",
                action="export",
                resource="*pii*",
                effect=PolicyEffect.DENY,
                reason="PII export is not permitted",
                priority=999,
            ),
            # Deny external network
            Policy(
                id="deny-external-network",
                action="*",
                resource="network.external",
                effect=PolicyEffect.DENY,
                reason="External network access is restricted",
                priority=998,
            ),
            # Allow ingest by default
            Policy(
                id="allow-ingest",
                action="ingest",
                resource="*",
                effect=PolicyEffect.ALLOW,
                reason="Ingestion is allowed",
                priority=100,
            ),
            # Allow query by default
            Policy(
                id="allow-query",
                action="query",
                resource="*",
                effect=PolicyEffect.ALLOW,
                reason="Queries are allowed",
                priority=100,
            ),
            # Allow analysis by default
            Policy(
                id="allow-analysis",
                action="analyze",
                resource="*",
                effect=PolicyEffect.ALLOW,
                reason="Analysis is allowed",
                priority=100,
            ),
        ]
        
        for policy in defaults:
            self.add_policy(policy)
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies.append(policy)
        # Keep sorted by priority (descending)
        self._policies.sort(key=lambda p: p.priority, reverse=True)
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID."""
        original_len = len(self._policies)
        self._policies = [p for p in self._policies if p.id != policy_id]
        return len(self._policies) < original_len
    
    def check(self, action: str, resource: str, actor: str = "system") -> Tuple[bool, str]:
        """
        Check if an action is allowed.
        
        Args:
            action: The action being performed
            resource: The resource being accessed
            actor: Who is performing the action
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check hardcoded forbidden list first
        if resource in self.FORBIDDEN_MODULES:
            return False, f"Module '{resource}' is forbidden"
        
        # Try OPA evaluator if available
        if self._opa_evaluator is not None:
            try:
                allowed, reason = self._opa_evaluator.check(action, resource, actor)
                return allowed, reason
            except Exception as e:
                # Fall back to built-in policies on OPA error
                pass
        
        # Evaluate policies in priority order
        for policy in self._policies:
            if policy.matches(action, resource, actor):
                if policy.effect == PolicyEffect.ALLOW:
                    return True, policy.reason
                elif policy.effect == PolicyEffect.DENY:
                    return False, policy.reason
                elif policy.effect == PolicyEffect.REQUIRE_APPROVAL:
                    # For now, treat as deny (approval workflow not implemented)
                    return False, f"Requires approval: {policy.reason}"
        
        # Default: allow if no policy matches
        return True, "No matching policy - default allow"
    
    def get_denying_policy_id(self, action: str, resource: str) -> Optional[str]:
        """Get the ID of the policy that would deny an action."""
        for policy in self._policies:
            if policy.matches(action, resource) and policy.effect == PolicyEffect.DENY:
                return policy.id
        return None
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies."""
        return [
            {
                "id": p.id,
                "action": p.action,
                "resource": p.resource,
                "effect": p.effect.value,
                "reason": p.reason,
                "priority": p.priority,
            }
            for p in self._policies
        ]
