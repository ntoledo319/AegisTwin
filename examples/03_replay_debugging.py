"""
Replay & Debugging Example

Demonstrates how to record and replay agent runs for debugging.
"""

from aegistwin import AegisTwinRuntime

def main():
    runtime = AegisTwinRuntime()
    
    # Run 1: Original execution
    print("=== Running Original Execution ===")
    run_id = runtime.start_run()
    
    data = {
        "records": [
            {"id": 1, "text": "Alpha", "priority": "high"},
            {"id": 2, "text": "Beta", "priority": "medium"},
            {"id": 3, "text": "Gamma", "priority": "low"},
        ]
    }
    
    runtime.ingest(data, source="debug_example")
    summary = runtime.end_run()
    
    print(f"✅ Original run: {run_id}")
    print(f"   Events: {summary['event_count']}")
    print(f"   Trace saved to: {summary['artifacts']['trace']}")
    
    # Run 2: Replay the original
    print("\n=== Replaying Original Execution ===")
    replay_summary = runtime.replay(run_id)
    
    print(f"✅ Replay run: {replay_summary['run_id']}")
    print(f"   Events replayed: {replay_summary['replay_results']['events_replayed']}")
    print(f"   Events matched: {replay_summary['replay_results']['events_matched']}")
    print(f"   Deterministic: {replay_summary['replay_results']['deterministic']}")
    
    if replay_summary['replay_results']['deterministic']:
        print("\n🎯 Replay was 100% deterministic!")
    else:
        print("\n⚠️  Replay diverged from original")

if __name__ == "__main__":
    main()
