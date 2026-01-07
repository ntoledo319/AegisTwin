"""
Tests for AegisTwin policy engine.

@context_boundary: tests/policy
"""

import pytest

from aegistwin.governance.policy import PolicyEngine, Policy, PolicyEffect


class TestPolicy:
    """Tests for Policy class."""
    
    def test_policy_matches_exact(self):
        """Test exact action/resource matching."""
        policy = Policy(
            id="test",
            action="ingest",
            resource="email",
            effect=PolicyEffect.ALLOW,
        )
        
        assert policy.matches("ingest", "email")
        assert not policy.matches("export", "email")
        assert not policy.matches("ingest", "calendar")
    
    def test_policy_matches_wildcard(self):
        """Test wildcard matching."""
        policy = Policy(
            id="test",
            action="*",
            resource="system.*",
            effect=PolicyEffect.DENY,
        )
        
        assert policy.matches("execute", "system.shell")
        assert policy.matches("read", "system.config")
        assert not policy.matches("execute", "data.export")
    
    def test_policy_matches_pattern(self):
        """Test pattern matching."""
        policy = Policy(
            id="test",
            action="export",
            resource="*pii*",
            effect=PolicyEffect.DENY,
        )
        
        assert policy.matches("export", "user_pii")
        assert policy.matches("export", "pii_data")
        assert not policy.matches("export", "public_data")


class TestPolicyEngine:
    """Tests for PolicyEngine class."""
    
    def test_default_policies_loaded(self):
        """Test that default policies are loaded."""
        engine = PolicyEngine()
        policies = engine.list_policies()
        
        assert len(policies) > 0
        policy_ids = [p["id"] for p in policies]
        assert "deny-forbidden-modules" in policy_ids
        assert "deny-pii-export" in policy_ids
    
    def test_forbidden_modules_denied(self):
        """Test that forbidden modules are always denied."""
        engine = PolicyEngine()
        
        allowed, reason = engine.check("execute", "system.shell")
        assert not allowed
        assert "forbidden" in reason.lower()
    
    def test_ingest_allowed_by_default(self):
        """Test that ingest is allowed by default."""
        engine = PolicyEngine()
        
        allowed, reason = engine.check("ingest", "email")
        assert allowed
    
    def test_query_allowed_by_default(self):
        """Test that query is allowed by default."""
        engine = PolicyEngine()
        
        allowed, reason = engine.check("query", "memory_graph")
        assert allowed
    
    def test_pii_export_denied(self):
        """Test that PII export is denied."""
        engine = PolicyEngine()
        
        allowed, reason = engine.check("export", "user_pii")
        assert not allowed
    
    def test_add_custom_policy(self):
        """Test adding a custom policy."""
        engine = PolicyEngine()
        
        engine.add_policy(Policy(
            id="custom-deny",
            action="delete",
            resource="*",
            effect=PolicyEffect.DENY,
            reason="Deletion not allowed",
            priority=500,
        ))
        
        allowed, reason = engine.check("delete", "data")
        assert not allowed
        assert "Deletion not allowed" in reason
    
    def test_remove_policy(self):
        """Test removing a policy."""
        engine = PolicyEngine()
        
        engine.add_policy(Policy(
            id="temp-policy",
            action="temp",
            resource="*",
            effect=PolicyEffect.DENY,
        ))
        
        removed = engine.remove_policy("temp-policy")
        assert removed
        
        # Should not be in list anymore
        policy_ids = [p["id"] for p in engine.list_policies()]
        assert "temp-policy" not in policy_ids
    
    def test_policy_priority(self):
        """Test that higher priority policies are evaluated first."""
        engine = PolicyEngine()
        
        # Add allow policy with lower priority
        engine.add_policy(Policy(
            id="allow-test",
            action="test",
            resource="*",
            effect=PolicyEffect.ALLOW,
            priority=100,
        ))
        
        # Add deny policy with higher priority
        engine.add_policy(Policy(
            id="deny-test",
            action="test",
            resource="*",
            effect=PolicyEffect.DENY,
            priority=200,
        ))
        
        # Higher priority deny should win
        allowed, _ = engine.check("test", "resource")
        assert not allowed
    
    def test_get_denying_policy_id(self):
        """Test getting the ID of denying policy."""
        engine = PolicyEngine()
        
        policy_id = engine.get_denying_policy_id("export", "user_pii")
        assert policy_id == "deny-pii-export"
    
    def test_default_allow_when_no_match(self):
        """Test that unmatched actions are allowed by default."""
        engine = PolicyEngine()
        
        # Remove all policies
        for p in engine.list_policies():
            engine.remove_policy(p["id"])
        
        allowed, reason = engine.check("random_action", "random_resource")
        assert allowed
        assert "default" in reason.lower()
