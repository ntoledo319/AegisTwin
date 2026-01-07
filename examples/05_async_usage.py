"""
AegisTwin Async Usage Example

Demonstrates async ingestion, concurrent queries, and event stream processing.

Usage:
    python examples/05_async_usage.py

@ai_prompt: Use AsyncAegisTwinRuntime for async applications.
@context_boundary: examples/05_async_usage

# AI-GENERATED 2026-01-07
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from aegistwin.runtime.async_core import AsyncAegisTwinRuntime, run_concurrent_queries


async def example_basic_async():
    """Basic async ingestion example."""
    print("=" * 50)
    print("Example 1: Basic Async Ingestion")
    print("=" * 50)
    
    runtime = AsyncAegisTwinRuntime()
    await runtime.start()
    
    try:
        # Async ingestion
        run_id = await runtime.ingest(
            data={"records": [{"id": 1}, {"id": 2}, {"id": 3}]},
            source="async_example"
        )
        print(f"✓ Async ingestion complete: run_id={run_id}")
        
    finally:
        await runtime.stop()


async def example_concurrent_queries():
    """Concurrent query execution example."""
    print("\n" + "=" * 50)
    print("Example 2: Concurrent Queries")
    print("=" * 50)
    
    runtime = AsyncAegisTwinRuntime()
    await runtime.start()
    
    try:
        queries = [
            "What emails were received today?",
            "Show calendar events for this week",
            "Find messages from the team",
            "List recent activities",
        ]
        
        print(f"Executing {len(queries)} queries concurrently...")
        
        results = await run_concurrent_queries(runtime, queries)
        
        for i, (query, result) in enumerate(zip(queries, results)):
            print(f"  [{i+1}] Query: {query[:40]}...")
            print(f"      Answer: {result['answer'][:50]}...")
        
        print(f"✓ All {len(queries)} queries completed concurrently")
        
    finally:
        await runtime.stop()


async def example_event_streaming():
    """Event streaming with listener example."""
    print("\n" + "=" * 50)
    print("Example 3: Event Streaming")
    print("=" * 50)
    
    runtime = AsyncAegisTwinRuntime()
    events_received = []
    
    async def event_listener(event):
        """Listener that receives all events."""
        events_received.append(event)
        print(f"  📨 Event: {event.event_type.value} (run={event.run_id})")
    
    # Add listener before starting
    runtime.event_bus.add_listener(event_listener)
    
    await runtime.start()
    
    try:
        print("Ingesting data with event streaming...")
        
        run_id = await runtime.ingest(
            data={"records": [{"type": "test", "value": i} for i in range(3)]},
            source="streaming_example"
        )
        
        # Small delay to ensure all events are processed
        await asyncio.sleep(0.1)
        
        print(f"✓ Received {len(events_received)} events during ingestion")
        
    finally:
        runtime.event_bus.remove_listener(event_listener)
        await runtime.stop()


async def example_batch_processing():
    """Batch processing with async runtime."""
    print("\n" + "=" * 50)
    print("Example 4: Batch Processing")
    print("=" * 50)
    
    runtime = AsyncAegisTwinRuntime()
    await runtime.start()
    
    try:
        # Process multiple data sources concurrently
        sources = ["emails", "calendar", "messages", "notes"]
        
        async def process_source(source: str) -> str:
            data = {"records": [{"source": source, "id": i} for i in range(5)]}
            return await runtime.ingest(data, source)
        
        print(f"Processing {len(sources)} sources concurrently...")
        
        tasks = [process_source(s) for s in sources]
        run_ids = await asyncio.gather(*tasks)
        
        for source, run_id in zip(sources, run_ids):
            print(f"  ✓ {source}: {run_id}")
        
        print(f"✓ Batch processing complete: {len(run_ids)} runs")
        
    finally:
        await runtime.stop()


async def main():
    """Run all async examples."""
    print("\n🚀 AegisTwin Async Usage Examples\n")
    
    await example_basic_async()
    await example_concurrent_queries()
    await example_event_streaming()
    await example_batch_processing()
    
    print("\n" + "=" * 50)
    print("✅ All async examples completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
