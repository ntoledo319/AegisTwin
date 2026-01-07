"""
Basic SDK Usage Example

Demonstrates the simplest way to use AegisTwin as an SDK in your application.
"""

from aegistwin import AegisTwin

def main():
    # Initialize AegisTwin
    twin = AegisTwin()
    
    # Ingest some data
    data = {
        "records": [
            {"id": 1, "text": "First record", "timestamp": "2024-01-01T10:00:00Z"},
            {"id": 2, "text": "Second record", "timestamp": "2024-01-01T11:00:00Z"},
        ]
    }
    
    run_id = twin.ingest(data, source="example_app")
    print(f"✅ Data ingested - Run ID: {run_id}")
    
    # Query the system
    result = twin.query("What records were ingested?")
    print(f"✅ Query result: {result['answer']}")
    
    # End the run
    summary = twin.runtime.end_run()
    print(f"✅ Run completed: {summary['event_count']} events")

if __name__ == "__main__":
    main()
