"""
AegisTwin LLM Integration Example

Demonstrates policy-gated LLM calls with audit trail.

Usage:
    # With mock provider (no API key needed)
    python examples/04_llm_integration.py
    
    # With OpenAI
    OPENAI_API_KEY=sk-... python examples/04_llm_integration.py --provider openai

@ai_prompt: Shows policy checks before LLM calls with full audit logging.
@context_boundary: examples/04_llm_integration

# AI-GENERATED 2026-01-07
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegistwin import AegisTwinRuntime
from aegistwin.events.schema import (
    LLMRequestEvent,
    LLMResponseEvent,
    AuditLogged,
    EventType,
)
from aegistwin.modules.llm import get_provider, LLMProvider
from aegistwin.governance.policy import Policy, PolicyEffect


def setup_llm_policies(runtime: AegisTwinRuntime) -> None:
    """Add LLM-specific policies to the runtime."""
    # Allow LLM queries by default
    runtime.policy_engine.add_policy(Policy(
        id="allow-llm-query",
        action="llm.query",
        resource="*",
        effect=PolicyEffect.ALLOW,
        reason="LLM queries are allowed",
        priority=100,
    ))
    
    # Deny external LLM if needed (can be enabled)
    # runtime.policy_engine.add_policy(Policy(
    #     id="deny-external-llm",
    #     action="llm.query",
    #     resource="llm.external",
    #     effect=PolicyEffect.DENY,
    #     reason="External LLM access is restricted",
    #     priority=200,
    # ))


def run_llm_with_audit(
    runtime: AegisTwinRuntime,
    provider: LLMProvider,
    prompt: str,
) -> Optional[str]:
    """
    Run an LLM query with policy check and audit logging.
    
    Args:
        runtime: AegisTwin runtime instance
        provider: LLM provider to use
        prompt: The prompt to send
        
    Returns:
        LLM response text or None if denied
    """
    run_id = runtime.start_run()
    
    # Determine resource based on provider
    resource = "llm.mock" if provider.name == "mock" else "llm.external"
    
    # Policy check
    print(f"\n📋 Policy Check: llm.query on {resource}")
    allowed = runtime.check_policy("llm.query", resource)
    
    if not allowed:
        print("  ❌ Policy DENIED")
        runtime.end_run()
        return None
    
    print("  ✓ Policy ALLOWED")
    
    # Emit LLM request event
    request_event = LLMRequestEvent(
        run_id=run_id,
        provider=provider.name,
        model=provider.default_model,
        prompt_preview=prompt[:200],
        max_tokens=500,
        temperature=0.7,
    )
    runtime.event_bus.publish(request_event)
    print(f"\n📤 LLM Request Event: {request_event.event_id[:8]}")
    
    # Make LLM call
    print(f"\n🤖 Calling {provider.name} ({provider.default_model})...")
    response = provider.complete(prompt, max_tokens=500)
    
    # Emit LLM response event
    response_event = LLMResponseEvent(
        run_id=run_id,
        parent_event_id=request_event.event_id,
        provider=provider.name,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_ms=response.latency_ms,
        finish_reason=response.finish_reason,
        request_event_id=request_event.event_id,
    )
    runtime.event_bus.publish(response_event)
    print(f"📥 LLM Response Event: {response_event.event_id[:8]}")
    
    # Emit audit log
    audit_event = AuditLogged(
        run_id=run_id,
        action="llm.query",
        actor="user",
        resource=resource,
        outcome="success",
        reason=f"LLM query completed: {response.output_tokens} tokens",
    )
    runtime.event_bus.publish(audit_event)
    print(f"📝 Audit Log: {audit_event.event_id[:8]}")
    
    # End run
    summary = runtime.end_run()
    print(f"\n✓ Run complete: {summary['run_id']} ({summary['event_count']} events)")
    
    return response.content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AegisTwin LLM Integration Example"
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "anthropic"],
        default="mock",
        help="LLM provider to use (default: mock)",
    )
    parser.add_argument(
        "--prompt",
        default="Explain what a digital twin is in 2 sentences.",
        help="Prompt to send to the LLM",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AegisTwin LLM Integration Example")
    print("=" * 60)
    
    # Initialize runtime
    runtime = AegisTwinRuntime()
    setup_llm_policies(runtime)
    
    # Get provider
    print(f"\n🔧 Provider: {args.provider}")
    provider = get_provider(args.provider)
    
    if not provider.is_available():
        print(f"⚠️  Provider {args.provider} is not available (missing API key)")
        print("   Falling back to mock provider")
        provider = get_provider("mock")
    
    # Run LLM query
    print(f"\n📝 Prompt: {args.prompt}")
    
    response = run_llm_with_audit(runtime, provider, args.prompt)
    
    if response:
        print("\n" + "-" * 40)
        print("📄 Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
    
    # Show audit trail
    print("\n📊 Audit Trail:")
    for policy in runtime.policy_engine.list_policies()[:5]:
        print(f"  - {policy['id']}: {policy['effect']}")
    
    print("\n" + "=" * 60)
    print("✅ LLM Integration Example Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
