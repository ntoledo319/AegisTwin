"""
Policy Enforcement Example

Shows how to configure custom policies to control agent behavior.
"""

from aegistwin import AegisTwinRuntime
from aegistwin.governance.policy import Policy

def main():
    # Initialize runtime
    runtime = AegisTwinRuntime()
    
    # Define a custom policy
    deny_export_policy = Policy(
        policy_id="deny_export",
        name="Deny Data Export",
        description="Prevents exporting data to external systems",
        deny_actions=["export", "send_external"],
        deny_resources=["*"],
    )
    
    # Add policy to engine
    runtime.policy_engine.add_policy(deny_export_policy)
    
    # Try to perform a denied action
    print("Attempting to export data...")
    allowed = runtime.check_policy(
        action="export",
        resource="user_data",
        actor="example_app"
    )
    
    if allowed:
        print("✅ Export allowed")
    else:
        print("❌ Export denied by policy")
    
    # Perform an allowed action
    print("\nAttempting to ingest data...")
    allowed = runtime.check_policy(
        action="ingest",
        resource="user_data",
        actor="example_app"
    )
    
    if allowed:
        print("✅ Ingest allowed")
        run_id = runtime.start_run()
        data = {"records": [{"id": 1, "text": "Test"}]}
        runtime.ingest(data, source="example_app")
        summary = runtime.end_run()
        print(f"✅ Ingested {summary['event_count']} events")

if __name__ == "__main__":
    main()
