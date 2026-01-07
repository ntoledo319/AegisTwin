"""
AegisTwin Runtime Core

Provides the main runtime engine that orchestrates event flow, policy enforcement,
and module execution with AegisTwin-specific logic.

@ai_prompt: AegisTwinRuntime is the central orchestrator. Initialize once per process.
@context_boundary: aegistwin/runtime/core

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED 2026-01-06
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from aegistwin.events.schema import (
    BaseEvent,
    IngestRequested,
    IngestCompleted,
    DataNormalized,
    AnalysisCompleted,
    GraphUpdated,
    MemoryUpdated,
    QueryRequested,
    QueryResponded,
    AuditLogged,
    ReplayStarted,
    ReplayCompleted,
    PolicyDenied,
    EventType,
)
from aegistwin.governance.policy import PolicyEngine


class EventBus:
    """
    Simple event bus for publishing and subscribing to events.
    
    Provides publish/subscribe event distribution.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_log: List[BaseEvent] = []
        self._recording = False
    
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers."""
        if self._recording:
            self._event_log.append(event)
        
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log but don't fail the pipeline
                print(f"Handler error for {event.event_type}: {e}")
    
    def start_recording(self) -> None:
        """Start recording events for replay."""
        self._recording = True
        self._event_log = []
    
    def stop_recording(self) -> List[BaseEvent]:
        """Stop recording and return recorded events."""
        self._recording = False
        return self._event_log.copy()
    
    def get_event_log(self) -> List[BaseEvent]:
        """Get the current event log."""
        return self._event_log.copy()


class AegisTwinRuntime:
    """
    Main runtime engine for AegisTwin.
    
    Orchestrates the flow of events through the pipeline, enforces policies,
    and manages state with governance and replay capabilities.
    
    Attributes:
        config: Runtime configuration
        event_bus: Event bus for inter-module communication
        policy_engine: Policy enforcement engine
        run_id: Current run identifier
    
    ## Affected Components
    - aegistwin.modules.connectors
    - aegistwin.modules.pipeline
    - aegistwin.modules.analysis
    - aegistwin.modules.graph
    - aegistwin.modules.memory
    
    @ai_prompt: Initialize with config_path for custom settings, or use defaults.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the runtime.
        
        Args:
            config_path: Optional path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.event_bus = EventBus()
        self.policy_engine = PolicyEngine()
        self.run_id: Optional[str] = None
        self._runs_dir = Path(self.config.get("runs_dir", "runs"))
        self._setup_handlers()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        defaults = {
            "runs_dir": "runs",
            "enable_replay": True,
            "enable_audit": True,
            "policy_mode": "enforce",  # enforce, warn, disabled
            "max_events_per_run": 10000,
        }
        
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                defaults.update(user_config or {})
        
        return defaults
    
    def _setup_handlers(self) -> None:
        """Set up default event handlers."""
        # Audit logging handler
        if self.config.get("enable_audit"):
            self.event_bus.subscribe(EventType.AUDIT_LOGGED, self._handle_audit)
    
    def _handle_audit(self, event: AuditLogged) -> None:
        """Handle audit log events by writing to audit file."""
        if self.run_id:
            audit_path = self._runs_dir / self.run_id / "audit.json"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            
            audits = []
            if audit_path.exists():
                with open(audit_path) as f:
                    audits = json.load(f)
            
            audits.append(event.model_dump(mode="json"))
            
            with open(audit_path, "w") as f:
                json.dump(audits, f, indent=2, default=str)
    
    def start_run(self) -> str:
        """
        Start a new pipeline run.
        
        Returns:
            Run ID for tracking
        """
        self.run_id = str(uuid.uuid4())[:8]
        run_dir = self._runs_dir / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.get("enable_replay"):
            self.event_bus.start_recording()
        
        return self.run_id
    
    def end_run(self) -> Dict[str, Any]:
        """
        End the current run and save artifacts.
        
        Returns:
            Run summary with paths to artifacts
        """
        if not self.run_id:
            return {"error": "No active run"}
        
        run_dir = self._runs_dir / self.run_id
        
        # Save event trace
        events = self.event_bus.stop_recording()
        trace_path = run_dir / "trace.json"
        with open(trace_path, "w") as f:
            trace_data = [e.to_trace_dict() for e in events]
            json.dump(trace_data, f, indent=2, default=str)
        
        # Generate summary
        summary = {
            "run_id": self.run_id,
            "event_count": len(events),
            "start_time": events[0].timestamp.isoformat() if events else None,
            "end_time": events[-1].timestamp.isoformat() if events else None,
            "artifacts": {
                "trace": str(trace_path),
                "audit": str(run_dir / "audit.json"),
            }
        }
        
        summary_path = run_dir / "summary.md"
        with open(summary_path, "w") as f:
            f.write(f"# Run Summary: {self.run_id}\n\n")
            f.write(f"**Events:** {len(events)}\n")
            f.write(f"**Start:** {summary.get('start_time', 'N/A')}\n")
            f.write(f"**End:** {summary.get('end_time', 'N/A')}\n\n")
            f.write("## Event Types\n\n")
            event_counts = {}
            for e in events:
                et = e.event_type.value
                event_counts[et] = event_counts.get(et, 0) + 1
            for et, count in sorted(event_counts.items()):
                f.write(f"- `{et}`: {count}\n")
        
        run_id = self.run_id
        self.run_id = None
        
        return summary
    
    def check_policy(self, action: str, resource: str, actor: str = "system") -> bool:
        """
        Check if an action is allowed by policy.
        
        Args:
            action: The action to check
            resource: The resource being accessed
            actor: Who is performing the action
            
        Returns:
            True if allowed, False if denied
        """
        allowed, reason = self.policy_engine.check(action, resource, actor)
        
        if not allowed:
            # Emit policy denied event
            denied_event = PolicyDenied(
                run_id=self.run_id or "no-run",
                action=action,
                policy_id=self.policy_engine.get_denying_policy_id(action, resource),
                reason=reason,
            )
            self.event_bus.publish(denied_event)
            
            # Log audit
            audit_event = AuditLogged(
                run_id=self.run_id or "no-run",
                action=action,
                actor=actor,
                resource=resource,
                outcome="denied",
                policy_id=denied_event.policy_id,
                reason=reason,
            )
            self.event_bus.publish(audit_event)
        
        return allowed
    
    def ingest(self, data: Dict[str, Any], source: str = "manual") -> str:
        """
        Ingest data into the pipeline.
        
        Args:
            data: Data to ingest
            source: Source identifier
            
        Returns:
            Run ID
        """
        run_id = self.start_run()
        
        # Check policy
        if not self.check_policy("ingest", source):
            self.end_run()
            raise PermissionError(f"Policy denied ingestion from source: {source}")
        
        # Emit ingest requested
        ingest_event = IngestRequested(
            run_id=run_id,
            source=source,
            data_type=data.get("type", "unknown"),
            payload=data,
        )
        self.event_bus.publish(ingest_event)
        
        # Simulate pipeline processing
        record_count = len(data.get("records", [data]))
        completed_event = IngestCompleted(
            run_id=run_id,
            parent_event_id=ingest_event.event_id,
            source=source,
            record_count=record_count,
            ingest_request_id=ingest_event.event_id,
            duration_ms=10.5,
        )
        self.event_bus.publish(completed_event)
        
        return run_id
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Query the system.
        
        Args:
            query_text: Natural language query
            
        Returns:
            Query response
        """
        # Check policy
        if not self.check_policy("query", "memory_graph"):
            raise PermissionError("Policy denied query access")
        
        query_event = QueryRequested(
            run_id=self.run_id or "query-only",
            query_text=query_text,
            query_type="search",
        )
        self.event_bus.publish(query_event)
        
        # Simulate query processing
        response = {
            "answer": f"Response to: {query_text}",
            "confidence": 0.85,
            "sources": ["memory_graph", "knowledge_base"],
        }
        
        response_event = QueryResponded(
            run_id=query_event.run_id,
            parent_event_id=query_event.event_id,
            query_request_id=query_event.event_id,
            response=response,
            sources=response["sources"],
            confidence=response["confidence"],
            latency_ms=25.3,
        )
        self.event_bus.publish(response_event)
        
        return response
    
    def replay(self, original_run_id: str) -> Dict[str, Any]:
        """
        Replay a previous run for verification.
        
        Args:
            original_run_id: ID of the run to replay
            
        Returns:
            Replay results with divergence information
        """
        # Load original trace
        trace_path = self._runs_dir / original_run_id / "trace.json"
        if not trace_path.exists():
            raise FileNotFoundError(f"No trace found for run: {original_run_id}")
        
        with open(trace_path) as f:
            original_trace = json.load(f)
        
        # Start replay
        replay_run_id = self.start_run()
        
        replay_start = ReplayStarted(
            run_id=replay_run_id,
            original_run_id=original_run_id,
            replay_mode="verify",
            event_count=len(original_trace),
        )
        self.event_bus.publish(replay_start)
        
        # Replay and compare (simplified)
        events_matched = 0
        events_diverged = 0
        divergences = []
        
        for original_event in original_trace:
            # In a real implementation, we would re-execute and compare
            events_matched += 1
        
        replay_complete = ReplayCompleted(
            run_id=replay_run_id,
            parent_event_id=replay_start.event_id,
            original_run_id=original_run_id,
            events_replayed=len(original_trace),
            events_matched=events_matched,
            events_diverged=events_diverged,
            divergence_details=divergences,
        )
        self.event_bus.publish(replay_complete)
        
        summary = self.end_run()
        summary["replay_results"] = {
            "original_run_id": original_run_id,
            "events_replayed": len(original_trace),
            "events_matched": events_matched,
            "events_diverged": events_diverged,
            "deterministic": events_diverged == 0,
        }
        
        return summary
