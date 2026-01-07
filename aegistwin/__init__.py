"""
AegisTwin - Event-driven agent runtime + governance + deterministic replay + local memory graph.

This package provides a unified wrapper around HydraMind runtime, Cognitive-Twin connectors,
and memory systems to create an acquirer-ready IP asset for intelligent agent orchestration.

@ai_prompt: Import from aegistwin for the unified API. Use aegistwin.run() for demos.
@context_boundary: aegistwin (top-level package)

## Core Features
- **Event-driven Runtime**: Built on HydraMind's event bus architecture
- **Governance & Policy**: Configurable policy gates with audit logging
- **Deterministic Replay**: Record and replay agent decisions for debugging
- **Local Memory Graph**: Episodic, semantic, and procedural memory systems

## Quick Start
```python
from aegistwin import AegisTwin

twin = AegisTwin()
twin.run_demo()
```

# AI-GENERATED 2026-01-06
# HUMAN-VALIDATED [pending]
"""

__version__ = "0.1.0"
__author__ = "AegisTwin Team"
__license__ = "MIT"

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.governance.policy import PolicyEngine
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
    ReplayStarted,
    ReplayCompleted,
)

__all__ = [
    # Core
    "AegisTwinRuntime",
    "PolicyEngine",
    # Events
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


class AegisTwin:
    """
    Main entry point for AegisTwin functionality.
    
    Provides a simplified interface for common operations including
    running demos, processing data, and querying the memory graph.
    
    @ai_prompt: Use this class for high-level operations. For fine-grained
    control, use AegisTwinRuntime directly.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize AegisTwin with optional configuration.
        
        Args:
            config_path: Path to YAML configuration file. If None, uses defaults.
        """
        self._runtime = None
        self._config_path = config_path
    
    @property
    def runtime(self) -> AegisTwinRuntime:
        """Lazy-load the runtime."""
        if self._runtime is None:
            self._runtime = AegisTwinRuntime(config_path=self._config_path)
        return self._runtime
    
    def run_demo(self, demo_name: str = "pipeline") -> dict:
        """
        Run a demonstration scenario.
        
        Args:
            demo_name: One of 'pipeline', 'replay', or 'policy'
            
        Returns:
            Dictionary containing demo results and artifacts
        """
        from aegistwin.demos import run_demo
        return run_demo(demo_name, self.runtime)
    
    def ingest(self, data: dict, source: str = "manual") -> str:
        """
        Ingest data into the system.
        
        Args:
            data: Data to ingest
            source: Source identifier
            
        Returns:
            Run ID for tracking
        """
        return self.runtime.ingest(data, source)
    
    def query(self, query: str) -> dict:
        """
        Query the memory graph.
        
        Args:
            query: Natural language query
            
        Returns:
            Query response with results
        """
        return self.runtime.query(query)
