"""
AegisTwin Events Module

Defines the event contract for the AegisTwin system using Pydantic models.
All inter-module communication uses these typed events.

@ai_prompt: All events inherit from BaseEvent. Use event.emit() to publish.
@context_boundary: aegistwin/events
"""

from aegistwin.events.schema import (
    AnalysisCompleted,
    AuditLogged,
    BaseEvent,
    DataNormalized,
    GraphUpdated,
    IngestCompleted,
    IngestRequested,
    MemoryUpdated,
    QueryRequested,
    QueryResponded,
    ReplayCompleted,
    ReplayStarted,
)

__all__ = [
    "BaseEvent",
    "IngestRequested",
    "IngestCompleted",
    "DataNormalized",
    "AnalysisCompleted",
    "GraphUpdated",
    "MemoryUpdated",
    "QueryRequested",
    "QueryResponded",
    "AuditLogged",
    "ReplayStarted",
    "ReplayCompleted",
]
