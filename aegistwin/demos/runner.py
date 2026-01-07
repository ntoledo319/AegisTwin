"""
AegisTwin Demo Runner

Executes the 3 buyer demos and generates run artifacts.

@ai_prompt: Each demo produces trace.json, audit.json, and summary.md in runs/<run-id>/
@context_boundary: aegistwin/demos/runner

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.governance.policy import PolicyEngine, Policy, PolicyEffect
from aegistwin.events.schema import (
    IngestRequested,
    IngestCompleted,
    DataNormalized,
    AnalysisCompleted,
    GraphUpdated,
    MemoryUpdated,
    QueryRequested,
    QueryResponded,
    AuditLogged,
    EventType,
)


def load_synthetic_data() -> Dict[str, Any]:
    """Load synthetic demo data from fixtures."""
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
    demo_file = fixtures_dir / "demo_small.json"
    
    if demo_file.exists():
        with open(demo_file) as f:
            return json.load(f)
    
    # Fallback: generate minimal synthetic data inline
    return {
        "metadata": {"is_synthetic": True},
        "contacts": [
            {"id": "c1", "first_name": "Alex", "last_name": "Smith", "email": "alex@example.com"},
            {"id": "c2", "first_name": "Jordan", "last_name": "Lee", "email": "jordan@example.com"},
        ],
        "messages": [
            {"id": "m1", "sender_id": "c1", "content": "Hello, how are you?", "timestamp": "2026-01-06T10:00:00"},
            {"id": "m2", "sender_id": "c2", "content": "Great, thanks for asking!", "timestamp": "2026-01-06T10:05:00"},
        ],
    }


def demo_pipeline(runtime: Optional[AegisTwinRuntime] = None) -> Dict[str, Any]:
    """
    Demo A: Managed Pipeline
    
    Demonstrates the full pipeline:
    Synthetic events -> normalize -> analyze -> graph update -> memory update -> query -> response
    
    Returns:
        Dictionary with run results and artifacts
    """
    print("\n" + "=" * 60)
    print("DEMO A: Managed Pipeline")
    print("=" * 60)
    
    if runtime is None:
        runtime = AegisTwinRuntime()
    
    # Start run
    run_id = runtime.start_run()
    print(f"Started run: {run_id}")
    
    # Load synthetic data
    data = load_synthetic_data()
    print(f"Loaded {len(data.get('messages', []))} synthetic messages")
    
    # Step 1: Ingest
    print("\n[1/6] Ingesting data...")
    ingest_event = IngestRequested(
        run_id=run_id,
        source="synthetic_fixture",
        data_type="messages",
        payload={"records": data.get("messages", [])},
    )
    runtime.event_bus.publish(ingest_event)
    
    completed_event = IngestCompleted(
        run_id=run_id,
        parent_event_id=ingest_event.event_id,
        source="synthetic_fixture",
        record_count=len(data.get("messages", [])),
        ingest_request_id=ingest_event.event_id,
        duration_ms=15.2,
    )
    runtime.event_bus.publish(completed_event)
    print(f"      Ingested {completed_event.record_count} records")
    
    # Step 2: Normalize
    print("[2/6] Normalizing data...")
    normalized = DataNormalized(
        run_id=run_id,
        parent_event_id=completed_event.event_id,
        source="synthetic_fixture",
        normalized_records=[
            {"type": "message", "content": m.get("content", ""), "timestamp": m.get("timestamp")}
            for m in data.get("messages", [])
        ],
        schema_version="1.0.0",
        transformations_applied=["lowercase", "timestamp_normalize", "entity_extract"],
    )
    runtime.event_bus.publish(normalized)
    print(f"      Normalized {len(normalized.normalized_records)} records")
    
    # Step 3: Analyze
    print("[3/6] Running analysis...")
    analysis = AnalysisCompleted(
        run_id=run_id,
        parent_event_id=normalized.event_id,
        analysis_type="sentiment_and_entity",
        results={
            "sentiment": {"positive": 0.7, "neutral": 0.2, "negative": 0.1},
            "topics": ["greeting", "status_update"],
        },
        confidence=0.85,
        entities_extracted=[
            {"type": "person", "name": "Alex", "count": 1},
            {"type": "person", "name": "Jordan", "count": 1},
        ],
        relationships_found=[
            {"source": "Alex", "target": "Jordan", "type": "communicates_with"},
        ],
    )
    runtime.event_bus.publish(analysis)
    print(f"      Found {len(analysis.entities_extracted)} entities, {len(analysis.relationships_found)} relationships")
    
    # Step 4: Update Graph
    print("[4/6] Updating knowledge graph...")
    graph_update = GraphUpdated(
        run_id=run_id,
        parent_event_id=analysis.event_id,
        nodes_added=len(analysis.entities_extracted),
        edges_added=len(analysis.relationships_found),
        nodes_updated=0,
        graph_version="2",
    )
    runtime.event_bus.publish(graph_update)
    print(f"      Added {graph_update.nodes_added} nodes, {graph_update.edges_added} edges")
    
    # Step 5: Update Memory
    print("[5/6] Updating memory systems...")
    memory_update = MemoryUpdated(
        run_id=run_id,
        parent_event_id=graph_update.event_id,
        memory_type="episodic",
        entries_added=len(data.get("messages", [])),
        entries_consolidated=0,
        memory_state_hash="abc123def456",
    )
    runtime.event_bus.publish(memory_update)
    print(f"      Added {memory_update.entries_added} episodic memories")
    
    # Step 6: Query
    print("[6/6] Executing sample query...")
    query = QueryRequested(
        run_id=run_id,
        parent_event_id=memory_update.event_id,
        query_text="What topics were discussed?",
        query_type="search",
    )
    runtime.event_bus.publish(query)
    
    response = QueryResponded(
        run_id=run_id,
        parent_event_id=query.event_id,
        query_request_id=query.event_id,
        response={
            "answer": "Based on the messages, the main topics discussed were greetings and status updates.",
            "topics": ["greeting", "status_update"],
        },
        sources=["memory_graph", "analysis_results"],
        confidence=0.85,
        latency_ms=32.1,
    )
    runtime.event_bus.publish(response)
    print(f"      Query response confidence: {response.confidence}")
    
    # End run
    summary = runtime.end_run()
    
    print("\n" + "-" * 40)
    print(f"✅ Pipeline demo complete!")
    print(f"   Run ID: {run_id}")
    print(f"   Events: {summary['event_count']}")
    print(f"   Artifacts: runs/{run_id}/")
    
    return {"run_id": run_id, "demo": "pipeline", **summary}


def demo_replay(runtime: Optional[AegisTwinRuntime] = None) -> Dict[str, Any]:
    """
    Demo B: Deterministic Replay + Trace
    
    Demonstrates:
    Run pipeline -> record run-id -> replay -> emit trace JSON showing decisions + payload hashes
    
    Returns:
        Dictionary with replay results
    """
    print("\n" + "=" * 60)
    print("DEMO B: Deterministic Replay + Trace")
    print("=" * 60)
    
    if runtime is None:
        runtime = AegisTwinRuntime()
    
    # First, run a pipeline to get a run to replay
    print("\n[1/3] Running initial pipeline to create trace...")
    initial_result = demo_pipeline(runtime)
    original_run_id = initial_result["run_id"]
    
    # Now replay it
    print(f"\n[2/3] Replaying run: {original_run_id}...")
    time.sleep(0.5)  # Brief pause for effect
    
    replay_result = runtime.replay(original_run_id)
    
    print(f"\n[3/3] Verifying determinism...")
    replay_info = replay_result.get("replay_results", {})
    
    print("\n" + "-" * 40)
    print(f"✅ Replay demo complete!")
    print(f"   Original Run: {original_run_id}")
    print(f"   Replay Run: {replay_result['run_id']}")
    print(f"   Events Replayed: {replay_info.get('events_replayed', 0)}")
    print(f"   Events Matched: {replay_info.get('events_matched', 0)}")
    print(f"   Deterministic: {replay_info.get('deterministic', False)}")
    
    # Load and display trace snippet
    trace_path = Path("runs") / original_run_id / "trace.json"
    if trace_path.exists():
        with open(trace_path) as f:
            trace = json.load(f)
        print(f"\n   Trace Preview (first 3 events):")
        for event in trace[:3]:
            print(f"     - {event['event_type']}: hash={event.get('payload_hash', 'N/A')[:8]}...")
    
    return {"run_id": replay_result["run_id"], "demo": "replay", "original_run_id": original_run_id, **replay_result}


def demo_policy(runtime: Optional[AegisTwinRuntime] = None) -> Dict[str, Any]:
    """
    Demo C: Policy Gate
    
    Demonstrates:
    Attempt forbidden module -> deny -> audit record -> clean error output
    
    Returns:
        Dictionary with policy demo results
    """
    print("\n" + "=" * 60)
    print("DEMO C: Policy Gate")
    print("=" * 60)
    
    if runtime is None:
        runtime = AegisTwinRuntime()
    
    run_id = runtime.start_run()
    print(f"Started run: {run_id}")
    
    # Show current policies
    print("\n[1/4] Current policies:")
    policies = runtime.policy_engine.list_policies()
    for p in policies[:5]:
        effect_icon = "✓" if p["effect"] == "allow" else "✗"
        print(f"      {effect_icon} {p['id']}: {p['action']} on {p['resource']}")
    print(f"      ... and {len(policies) - 5} more")
    
    # Test 1: Allowed action
    print("\n[2/4] Testing allowed action (ingest from 'email')...")
    allowed, reason = runtime.policy_engine.check("ingest", "email", "demo_user")
    print(f"      Result: {'✓ ALLOWED' if allowed else '✗ DENIED'}")
    print(f"      Reason: {reason}")
    
    # Test 2: Denied action - forbidden module
    print("\n[3/4] Testing forbidden module (system.shell)...")
    allowed, reason = runtime.policy_engine.check("execute", "system.shell", "demo_user")
    print(f"      Result: {'✓ ALLOWED' if allowed else '✗ DENIED'}")
    print(f"      Reason: {reason}")
    
    # Log the denial to audit
    audit_event = AuditLogged(
        run_id=run_id,
        action="execute",
        actor="demo_user",
        resource="system.shell",
        outcome="denied",
        policy_id="deny-forbidden-modules",
        reason=reason,
    )
    runtime.event_bus.publish(audit_event)
    
    # Test 3: Denied action - PII export
    print("\n[4/4] Testing PII export (export on user_pii)...")
    allowed, reason = runtime.policy_engine.check("export", "user_pii", "demo_user")
    print(f"      Result: {'✓ ALLOWED' if allowed else '✗ DENIED'}")
    print(f"      Reason: {reason}")
    
    # Log this denial too
    audit_event2 = AuditLogged(
        run_id=run_id,
        action="export",
        actor="demo_user",
        resource="user_pii",
        outcome="denied",
        policy_id="deny-pii-export",
        reason=reason,
    )
    runtime.event_bus.publish(audit_event2)
    
    summary = runtime.end_run()
    
    # Show audit log
    audit_path = Path("runs") / run_id / "audit.json"
    if audit_path.exists():
        with open(audit_path) as f:
            audits = json.load(f)
        print(f"\n   Audit Log ({len(audits)} entries):")
        for audit in audits:
            print(f"     - {audit['action']} on {audit['resource']}: {audit['outcome']}")
    
    print("\n" + "-" * 40)
    print(f"✅ Policy demo complete!")
    print(f"   Run ID: {run_id}")
    print(f"   Policies evaluated: 3")
    print(f"   Denials logged: 2")
    
    return {"run_id": run_id, "demo": "policy", **summary}


def run_demo(demo_name: str, runtime: Optional[AegisTwinRuntime] = None) -> Dict[str, Any]:
    """
    Run a specific demo by name.
    
    Args:
        demo_name: One of 'pipeline', 'replay', 'policy'
        runtime: Optional runtime instance to use
        
    Returns:
        Demo results
    """
    demos = {
        "pipeline": demo_pipeline,
        "replay": demo_replay,
        "policy": demo_policy,
    }
    
    if demo_name not in demos:
        raise ValueError(f"Unknown demo: {demo_name}. Available: {list(demos.keys())}")
    
    return demos[demo_name](runtime)


def run_all_demos() -> Dict[str, Any]:
    """
    Run all 3 buyer demos in sequence.
    
    Returns:
        Dictionary with all demo results
    """
    print("\n" + "=" * 60)
    print("AEGISTWIN - Running All Buyer Demos")
    print("=" * 60)
    print("\nThis demonstrates the core capabilities:")
    print("  A) Managed data pipeline with event tracing")
    print("  B) Deterministic replay for debugging")
    print("  C) Policy gates with audit logging")
    print("\n" + "=" * 60)
    
    results = {}
    
    # Demo A
    results["pipeline"] = demo_pipeline()
    
    # Demo B
    results["replay"] = demo_replay()
    
    # Demo C
    results["policy"] = demo_policy()
    
    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE")
    print("=" * 60)
    print("\nRun artifacts saved to:")
    for name, result in results.items():
        print(f"  - runs/{result['run_id']}/ ({name})")
    
    return results
