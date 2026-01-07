"""
AegisTwin OPA Policy Example

Demonstrates Open Policy Agent integration for policy-as-code.

Usage:
    # With embedded policy (no OPA server needed)
    python examples/07_opa_policies.py
    
    # With external OPA server
    docker run -p 8181:8181 openpolicyagent/opa run --server
    OPA_URL=http://localhost:8181 python examples/07_opa_policies.py

@ai_prompt: Shows Rego policy evaluation with OPAEvaluator.
@context_boundary: examples/07_opa_policies

# AI-GENERATED 2026-01-07
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegistwin.governance.opa import OPAEvaluator, load_rego_policy


def demo_embedded_policy():
    """Demonstrate embedded Rego policy evaluation."""
    print("=" * 50)
    print("Demo 1: Embedded Rego Policy")
    print("=" * 50)
    
    # Get policy path
    policy_path = Path(__file__).parent.parent / "aegistwin/governance/policies/default.rego"
    
    if not policy_path.exists():
        print(f"⚠️  Policy file not found: {policy_path}")
        print("   Creating inline policy for demo...")
        
        # Use inline policy for demo
        inline_policy = '''
package aegistwin.authz

default allow = false

allow {
    input.action == "query"
}

allow {
    input.action == "ingest"
    not startswith(input.resource, "system.")
}

deny[reason] {
    input.resource == "system.shell"
    reason := "Shell access is forbidden"
}
'''
        # Write to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".rego", delete=False
        ) as f:
            f.write(inline_policy)
            policy_path = f.name
    
    print(f"\n📋 Loading policy from: {policy_path}")
    
    evaluator = OPAEvaluator(policy_path=str(policy_path))
    
    # Test cases
    test_cases = [
        ("query", "memory_graph", "user"),
        ("ingest", "emails", "system"),
        ("execute", "system.shell", "user"),
        ("export", "user_pii_data", "user"),
        ("analyze", "documents", "admin"),
    ]
    
    print("\n🔍 Policy Evaluation Results:\n")
    
    for action, resource, actor in test_cases:
        allowed, reason = evaluator.check(action, resource, actor)
        status = "✓ ALLOW" if allowed else "✗ DENY"
        print(f"  {status}: {action} on {resource} by {actor}")
        print(f"          Reason: {reason}\n")


def demo_external_opa():
    """Demonstrate external OPA server integration."""
    print("\n" + "=" * 50)
    print("Demo 2: External OPA Server")
    print("=" * 50)
    
    opa_url = os.getenv("OPA_URL")
    
    if not opa_url:
        print("\n⚠️  OPA_URL not set. Skipping external OPA demo.")
        print("   To test with external OPA:")
        print("   1. docker run -p 8181:8181 openpolicyagent/opa run --server")
        print("   2. OPA_URL=http://localhost:8181 python examples/07_opa_policies.py")
        return
    
    print(f"\n🔌 Connecting to OPA at: {opa_url}")
    
    evaluator = OPAEvaluator(opa_url=opa_url)
    
    # Test a simple query
    allowed, reason = evaluator.check("query", "test_resource", "user")
    
    status = "✓ ALLOW" if allowed else "✗ DENY"
    print(f"\n  {status}: query on test_resource by user")
    print(f"          Reason: {reason}")


def demo_policy_content():
    """Show the default policy content."""
    print("\n" + "=" * 50)
    print("Default Rego Policy")
    print("=" * 50)
    
    policy_path = Path(__file__).parent.parent / "aegistwin/governance/policies/default.rego"
    
    if policy_path.exists():
        content = load_rego_policy(str(policy_path))
        print(f"\n📄 {policy_path}:\n")
        print("-" * 40)
        # Print first 50 lines
        lines = content.split("\n")[:50]
        for line in lines:
            print(f"  {line}")
        if len(content.split("\n")) > 50:
            print("  ...")
        print("-" * 40)
    else:
        print(f"\n⚠️  Policy file not found: {policy_path}")


def main():
    """Main entry point."""
    print("\n🔐 AegisTwin OPA Policy Integration Example\n")
    
    demo_embedded_policy()
    demo_external_opa()
    demo_policy_content()
    
    print("\n" + "=" * 50)
    print("✅ OPA Policy Example Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
