"""
Policy Enforcement Integration Tests

Tests that policies are correctly enforced.

@ai_prompt: Run with pytest tests/integration/test_policy_enforcement.py -v
@context_boundary: tests/integration/test_policy_enforcement

# AI-GENERATED 2026-01-07
"""

import json
import pytest
from pathlib import Path

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.governance.policy import Policy, PolicyEffect, PolicyEngine


class TestPolicyEnforcement:
    """Tests for policy enforcement."""
    
    def test_forbidden_action_denied(self, runtime: AegisTwinRuntime):
        """Test that forbidden actions are denied."""
        allowed = runtime.check_policy("execute", "system.shell")
        
        assert allowed is False
    
    def test_allowed_action_passes(self, runtime: AegisTwinRuntime):
        """Test that allowed actions pass."""
        allowed = runtime.check_policy("ingest", "emails")
        
        assert allowed is True
    
    def test_denial_creates_audit(self, runtime: AegisTwinRuntime):
        """Test that denial creates audit log entry."""
        runtime.run_id = "test-run"
        runtime.event_bus.start_recording()
        
        runtime.check_policy("execute", "system.shell")
        
        events = runtime.event_bus.get_event_log()
        
        # Should have policy denied and audit logged events
        event_types = [e.event_type.value for e in events]
        assert "policy.denied" in event_types
        assert "audit.logged" in event_types
    
    def test_custom_policy_respected(self, runtime: AegisTwinRuntime):
        """Test that custom policies are respected."""
        # Add custom deny policy
        runtime.policy_engine.add_policy(Policy(
            id="deny-custom-resource",
            action="access",
            resource="custom.restricted",
            effect=PolicyEffect.DENY,
            reason="Custom resource is restricted",
            priority=500,
        ))
        
        allowed = runtime.check_policy("access", "custom.restricted")
        
        assert allowed is False
    
    def test_policy_priority(self, runtime: AegisTwinRuntime):
        """Test that higher priority policies take precedence."""
        # Add allow policy with lower priority
        runtime.policy_engine.add_policy(Policy(
            id="allow-test",
            action="test",
            resource="priority.test",
            effect=PolicyEffect.ALLOW,
            reason="Allow test",
            priority=100,
        ))
        
        # Add deny policy with higher priority
        runtime.policy_engine.add_policy(Policy(
            id="deny-test",
            action="test",
            resource="priority.test",
            effect=PolicyEffect.DENY,
            reason="Deny test",
            priority=200,
        ))
        
        allowed = runtime.check_policy("test", "priority.test")
        
        # Higher priority deny should win
        assert allowed is False
    
    def test_ingest_denied_source(self, runtime: AegisTwinRuntime):
        """Test that ingestion from denied source raises error."""
        # Add deny policy for specific source
        runtime.policy_engine.add_policy(Policy(
            id="deny-untrusted-source",
            action="ingest",
            resource="untrusted",
            effect=PolicyEffect.DENY,
            reason="Untrusted source not allowed",
            priority=500,
        ))
        
        with pytest.raises(PermissionError):
            runtime.ingest({"records": []}, source="untrusted")


class TestPolicyListing:
    """Tests for policy listing."""
    
    def test_list_policies(self, runtime: AegisTwinRuntime):
        """Test listing all policies."""
        policies = runtime.policy_engine.list_policies()
        
        assert len(policies) > 0
        
        # Check structure
        for policy in policies:
            assert "id" in policy
            assert "action" in policy
            assert "resource" in policy
            assert "effect" in policy
    
    def test_add_and_remove_policy(self, runtime: AegisTwinRuntime):
        """Test adding and removing a policy."""
        initial_count = len(runtime.policy_engine.list_policies())
        
        # Add policy
        runtime.policy_engine.add_policy(Policy(
            id="test-policy-123",
            action="test",
            resource="test",
            effect=PolicyEffect.ALLOW,
            reason="Test policy",
            priority=1,
        ))
        
        assert len(runtime.policy_engine.list_policies()) == initial_count + 1
        
        # Remove policy
        removed = runtime.policy_engine.remove_policy("test-policy-123")
        
        assert removed is True
        assert len(runtime.policy_engine.list_policies()) == initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
