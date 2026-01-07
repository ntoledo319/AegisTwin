"""
AegisTwin WebSocket Client Example

Demonstrates connecting to the WebSocket event stream.

Usage:
    # Start server first:
    uvicorn aegistwin.api.main:app --reload
    
    # Then run client:
    python examples/06_websocket_client.py

@ai_prompt: Use websockets library to connect to /ws/events endpoint.
@context_boundary: examples/06_websocket_client

# AI-GENERATED 2026-01-07
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    sys.exit(1)


async def listen_to_events(
    url: str = "ws://localhost:8000/ws/events",
    event_types: list = None,
    duration: int = 60,
):
    """
    Connect to WebSocket and listen for events.
    
    Args:
        url: WebSocket URL to connect to
        event_types: Optional list of event types to filter
        duration: How long to listen (seconds)
    """
    # Add event type filter to URL if specified
    if event_types:
        url += f"?event_types={','.join(event_types)}"
    
    print(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print("✓ Connected!")
            
            # Receive connection confirmation
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"  Filters: {data.get('filters', {})}")
            print("\nListening for events (Ctrl+C to stop)...\n")
            
            # Set up timeout
            end_time = asyncio.get_event_loop().time() + duration
            
            while asyncio.get_event_loop().time() < end_time:
                try:
                    msg = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=5.0
                    )
                    
                    data = json.loads(msg)
                    
                    # Handle ping
                    if data.get("type") == "ping":
                        await websocket.send("pong")
                        continue
                    
                    # Print event
                    event_type = data.get("event_type", "unknown")
                    event_id = data.get("event_id", "?")[:8]
                    run_id = data.get("run_id", "?")
                    timestamp = data.get("timestamp", "")[:19]
                    
                    print(f"📨 [{timestamp}] {event_type}")
                    print(f"   run_id: {run_id}, event_id: {event_id}")
                    
                    # Print additional fields based on event type
                    if "source" in data:
                        print(f"   source: {data['source']}")
                    if "record_count" in data:
                        print(f"   records: {data['record_count']}")
                    if "outcome" in data:
                        print(f"   outcome: {data['outcome']}")
                    
                    print()
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    await websocket.send("ping")
                    pong = await websocket.recv()
                    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
        print("   Start with: uvicorn aegistwin.api.main:app --reload")


async def listen_to_run(run_id: str, url: str = "ws://localhost:8000"):
    """
    Listen to events from a specific run.
    
    Args:
        run_id: Run ID to filter by
        url: Base WebSocket URL
    """
    full_url = f"{url}/ws/events/{run_id}"
    await listen_to_events(full_url)


async def subscribe_to_types(
    url: str = "ws://localhost:8000/ws/events",
    event_types: list = None,
):
    """
    Connect and dynamically subscribe to event types.
    
    Args:
        url: WebSocket URL
        event_types: Event types to subscribe to
    """
    async with websockets.connect(url) as websocket:
        # Wait for connection confirmation
        await websocket.recv()
        
        # Send subscription request
        subscribe_msg = {
            "type": "subscribe",
            "event_types": event_types or ["ingest.completed", "query.responded"],
        }
        await websocket.send(json.dumps(subscribe_msg))
        
        # Wait for confirmation
        response = await websocket.recv()
        print(f"Subscribed: {response}")
        
        # Listen for events
        while True:
            msg = await websocket.recv()
            print(f"Event: {msg[:100]}...")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AegisTwin WebSocket Client Example"
    )
    parser.add_argument(
        "--url",
        default="ws://localhost:8000/ws/events",
        help="WebSocket URL to connect to",
    )
    parser.add_argument(
        "--types",
        nargs="*",
        help="Event types to filter (e.g., ingest.completed query.responded)",
    )
    parser.add_argument(
        "--run-id",
        help="Filter to specific run ID",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="How long to listen (seconds)",
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("AegisTwin WebSocket Client")
    print("=" * 50)
    
    if args.run_id:
        asyncio.run(listen_to_run(args.run_id))
    else:
        asyncio.run(listen_to_events(
            url=args.url,
            event_types=args.types,
            duration=args.duration,
        ))


if __name__ == "__main__":
    main()
