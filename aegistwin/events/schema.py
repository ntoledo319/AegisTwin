"""
AegisTwin Event Schema

Pydantic models defining the event contract for the AegisTwin system.
These events drive the entire pipeline from ingestion to query response.

@ai_prompt: Create new events by inheriting from BaseEvent. All events
are immutable and serializable to JSON.

@context_boundary: aegistwin/events/schema

## Event Flow
```
IngestRequested -> IngestCompleted -> DataNormalized -> AnalysisCompleted
                                                              |
                                                              v
QueryResponded <- QueryRequested <- MemoryUpdated <- GraphUpdated
```

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class EventType(str, Enum):
    """Enumeration of all event types in the system."""
    INGEST_REQUESTED = "ingest.requested"
    INGEST_COMPLETED = "ingest.completed"
    DATA_NORMALIZED = "data.normalized"
    ANALYSIS_COMPLETED = "analysis.completed"
    GRAPH_UPDATED = "graph.updated"
    MEMORY_UPDATED = "memory.updated"
    QUERY_REQUESTED = "query.requested"
    QUERY_RESPONDED = "query.responded"
    AUDIT_LOGGED = "audit.logged"
    REPLAY_STARTED = "replay.started"
    REPLAY_COMPLETED = "replay.completed"
    POLICY_DENIED = "policy.denied"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"


class BaseEvent(BaseModel):
    """
    Base class for all AegisTwin events.

    Provides common fields for event identification, timing, and tracing.
    All events are immutable after creation.

    Attributes:
        event_id: Unique identifier for this event instance
        event_type: Type of event from EventType enum
        timestamp: When the event was created
        run_id: ID of the pipeline run this event belongs to
        parent_event_id: ID of the event that triggered this one
        metadata: Additional context data
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_event_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @computed_field
    @property
    def payload_hash(self) -> str:
        """Compute deterministic hash of event payload for replay verification."""
        # Exclude volatile fields from hash
        data = self.model_dump(exclude={"event_id", "timestamp", "payload_hash"})
        serialized = str(sorted(data.items()))
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def to_trace_dict(self) -> dict[str, Any]:
        """Convert event to trace-friendly dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "run_id": self.run_id,
            "parent_event_id": self.parent_event_id,
            "payload_hash": self.payload_hash,
        }


class IngestRequested(BaseEvent):
    """
    Event emitted when data ingestion is requested.

    Attributes:
        source: Source of the data (e.g., 'email', 'calendar', 'messages')
        data_type: Type of data being ingested
        payload: The actual data to ingest
        connector_id: ID of the connector handling this request
    """
    event_type: EventType = EventType.INGEST_REQUESTED
    source: str
    data_type: str
    payload: dict[str, Any]
    connector_id: str | None = None


class IngestCompleted(BaseEvent):
    """
    Event emitted when data ingestion completes successfully.

    Attributes:
        source: Source of the ingested data
        record_count: Number of records ingested
        ingest_request_id: ID of the original IngestRequested event
        duration_ms: Time taken to complete ingestion
    """
    event_type: EventType = EventType.INGEST_COMPLETED
    source: str
    record_count: int
    ingest_request_id: str
    duration_ms: float


class DataNormalized(BaseEvent):
    """
    Event emitted when ingested data has been normalized.

    Attributes:
        source: Original data source
        normalized_records: List of normalized data records
        schema_version: Version of the normalization schema used
        transformations_applied: List of transformations applied
    """
    event_type: EventType = EventType.DATA_NORMALIZED
    source: str
    normalized_records: list[dict[str, Any]]
    schema_version: str = "1.0.0"
    transformations_applied: list[str] = Field(default_factory=list)


class AnalysisCompleted(BaseEvent):
    """
    Event emitted when analysis of normalized data completes.

    Attributes:
        analysis_type: Type of analysis performed
        results: Analysis results
        confidence: Confidence score (0.0 to 1.0)
        entities_extracted: Named entities found
        relationships_found: Relationships between entities
    """
    event_type: EventType = EventType.ANALYSIS_COMPLETED
    analysis_type: str
    results: dict[str, Any]
    confidence: float = 1.0
    entities_extracted: list[dict[str, Any]] = Field(default_factory=list)
    relationships_found: list[dict[str, Any]] = Field(default_factory=list)


class GraphUpdated(BaseEvent):
    """
    Event emitted when the knowledge graph is updated.

    Attributes:
        nodes_added: Number of nodes added
        edges_added: Number of edges added
        nodes_updated: Number of nodes updated
        graph_version: Current version of the graph
    """
    event_type: EventType = EventType.GRAPH_UPDATED
    nodes_added: int = 0
    edges_added: int = 0
    nodes_updated: int = 0
    graph_version: str = "1"


class MemoryUpdated(BaseEvent):
    """
    Event emitted when memory systems are updated.

    Attributes:
        memory_type: Type of memory updated (episodic, semantic, procedural)
        entries_added: Number of memory entries added
        entries_consolidated: Number of entries consolidated
        memory_state_hash: Hash of current memory state
    """
    event_type: EventType = EventType.MEMORY_UPDATED
    memory_type: str
    entries_added: int = 0
    entries_consolidated: int = 0
    memory_state_hash: str | None = None


class QueryRequested(BaseEvent):
    """
    Event emitted when a query is submitted.

    Attributes:
        query_text: The natural language query
        query_type: Type of query (search, inference, aggregation)
        context: Additional context for the query
        requester_id: ID of the requesting entity
    """
    event_type: EventType = EventType.QUERY_REQUESTED
    query_text: str
    query_type: str = "search"
    context: dict[str, Any] = Field(default_factory=dict)
    requester_id: str | None = None


class QueryResponded(BaseEvent):
    """
    Event emitted when a query response is ready.

    Attributes:
        query_request_id: ID of the original QueryRequested event
        response: The query response
        sources: Sources used to generate the response
        confidence: Confidence in the response
        latency_ms: Query processing time
    """
    event_type: EventType = EventType.QUERY_RESPONDED
    query_request_id: str
    response: dict[str, Any]
    sources: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    latency_ms: float = 0.0


class AuditLogged(BaseEvent):
    """
    Event emitted for audit logging purposes.

    Attributes:
        action: The action being audited
        actor: Who performed the action
        resource: What resource was affected
        outcome: Result of the action (success, denied, error)
        policy_id: ID of the policy that was evaluated
        reason: Explanation for the outcome
    """
    event_type: EventType = EventType.AUDIT_LOGGED
    action: str
    actor: str
    resource: str
    outcome: str
    policy_id: str | None = None
    reason: str | None = None


class ReplayStarted(BaseEvent):
    """
    Event emitted when a replay session begins.

    Attributes:
        original_run_id: ID of the run being replayed
        replay_mode: Mode of replay (verify, debug, compare)
        event_count: Number of events to replay
    """
    event_type: EventType = EventType.REPLAY_STARTED
    original_run_id: str
    replay_mode: str = "verify"
    event_count: int = 0


class ReplayCompleted(BaseEvent):
    """
    Event emitted when a replay session completes.

    Attributes:
        original_run_id: ID of the run that was replayed
        events_replayed: Number of events replayed
        events_matched: Number of events that matched original
        events_diverged: Number of events that diverged
        divergence_details: Details about any divergences
    """
    event_type: EventType = EventType.REPLAY_COMPLETED
    original_run_id: str
    events_replayed: int = 0
    events_matched: int = 0
    events_diverged: int = 0
    divergence_details: list[dict[str, Any]] = Field(default_factory=list)


class PolicyDenied(BaseEvent):
    """
    Event emitted when a policy denies an action.

    Attributes:
        action: The action that was denied
        policy_id: ID of the denying policy
        reason: Why the action was denied
        suggested_action: Suggested alternative action
    """
    event_type: EventType = EventType.POLICY_DENIED
    action: str
    policy_id: str
    reason: str
    suggested_action: str | None = None


class LLMRequestEvent(BaseEvent):
    """
    Event emitted when an LLM request is made.

    Attributes:
        provider: LLM provider name (openai, anthropic, mock)
        model: Model identifier
        prompt_preview: First 200 chars of prompt (for audit, no PII)
        max_tokens: Maximum tokens requested
        temperature: Sampling temperature
    """
    event_type: EventType = EventType.LLM_REQUEST
    provider: str
    model: str
    prompt_preview: str = ""
    max_tokens: int = 1000
    temperature: float = 0.7


class LLMResponseEvent(BaseEvent):
    """
    Event emitted when an LLM response is received.

    Attributes:
        provider: LLM provider name
        model: Model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        finish_reason: Why generation stopped
        request_event_id: ID of the corresponding request event
    """
    event_type: EventType = EventType.LLM_RESPONSE
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    request_event_id: str | None = None
