"""
AegisTwin CLI

Command-line interface for AegisTwin operations.

Usage:
    aegistwin demo [pipeline|replay|policy]
    aegistwin ingest <file>
    aegistwin query <query>
    aegistwin replay <run-id>

@ai_prompt: Run `aegistwin demo` to see the system in action.
@context_boundary: aegistwin/cli

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

import argparse
import json
import sys
from pathlib import Path


def cmd_demo(args):
    """Run a demonstration."""
    from aegistwin.demos import run_all_demos, run_demo

    if args.demo_name == "all":
        run_all_demos()
        print("\n✅ All demos completed. Results in: runs/")
        return 0
    else:
        result = run_demo(args.demo_name)
        print(f"\n✅ Demo '{args.demo_name}' completed.")
        print(f"   Run ID: {result.get('run_id', 'N/A')}")
        return 0


def cmd_ingest(args):
    """Ingest data from a file."""
    from aegistwin import AegisTwin

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1

    with open(file_path) as f:
        data = json.load(f)

    twin = AegisTwin()
    run_id = twin.ingest(data, source=file_path.stem)
    print(f"✅ Ingested data from {file_path}")
    print(f"   Run ID: {run_id}")
    return 0


def cmd_query(args):
    """Query the system."""
    from aegistwin import AegisTwin

    twin = AegisTwin()
    result = twin.query(args.query)
    print(json.dumps(result, indent=2))
    return 0


def cmd_replay(args):
    """Replay a previous run."""
    from aegistwin import AegisTwinRuntime

    runtime = AegisTwinRuntime()
    try:
        result = runtime.replay(args.run_id)
        print(f"✅ Replay completed for run: {args.run_id}")
        print(f"   Deterministic: {result['replay_results']['deterministic']}")
        print(f"   Events matched: {result['replay_results']['events_matched']}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1


def cmd_scan(args):
    """Run PII scanner."""
    import subprocess
    result = subprocess.run([sys.executable, "tools/pii_scan.py"], cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="aegistwin",
        description="AegisTwin - Event-driven agent runtime + governance + deterministic replay + local memory graph",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a demonstration")
    demo_parser.add_argument(
        "demo_name",
        nargs="?",
        default="all",
        choices=["pipeline", "replay", "policy", "all"],
        help="Demo to run (default: all)"
    )
    demo_parser.set_defaults(func=cmd_demo)

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data from a file")
    ingest_parser.add_argument("file", help="JSON file to ingest")
    ingest_parser.set_defaults(func=cmd_ingest)

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the system")
    query_parser.add_argument("query", help="Natural language query")
    query_parser.set_defaults(func=cmd_query)

    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a previous run")
    replay_parser.add_argument("run_id", help="Run ID to replay")
    replay_parser.set_defaults(func=cmd_replay)

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Run PII scanner")
    scan_parser.set_defaults(func=cmd_scan)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
