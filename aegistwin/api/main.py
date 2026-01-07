"""
AegisTwin FastAPI Application

REST API for AegisTwin operations including health checks, demos, queries, and replay.

@ai_prompt: Mount this app or run standalone with uvicorn.
@context_boundary: aegistwin/api/main

# AI-GENERATED 2026-01-06
"""

from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from aegistwin.api.websocket import (
    handle_websocket_connection,
)
from aegistwin.api.websocket import (
    manager as ws_manager,
)
from aegistwin.demos import run_all_demos, run_demo
from aegistwin.observability.metrics import generate_prometheus_metrics
from aegistwin.runtime.core import AegisTwinRuntime


class IngestRequest(BaseModel):
    """Request body for ingestion."""
    data: dict[str, Any]
    source: str = "api"


class QueryRequest(BaseModel):
    """Request body for queries."""
    query: str
    context: dict[str, Any] | None = None


class ReplayRequest(BaseModel):
    """Request body for replay."""
    run_id: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="AegisTwin API",
        description="Event-driven agent runtime + governance + deterministic replay + local memory graph",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Shared runtime instance
    runtime = AegisTwinRuntime()

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with API info."""
        return {
            "name": "AegisTwin",
            "tagline": "Event-driven agent runtime + governance + deterministic replay + local memory graph",
            "docs": "/docs",
        }

    @app.post("/demo/{demo_name}")
    async def run_demo_endpoint(demo_name: str) -> dict[str, Any]:
        """Run a demo by name."""
        try:
            if demo_name == "all":
                result = run_all_demos()
            else:
                result = run_demo(demo_name)
            return {"status": "success", "result": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/ingest")
    async def ingest_data(request: IngestRequest) -> dict[str, Any]:
        """Ingest data into the system."""
        try:
            run_id = runtime.ingest(request.data, request.source)
            return {"status": "success", "run_id": run_id}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/query")
    async def query_system(request: QueryRequest) -> dict[str, Any]:
        """Query the system."""
        try:
            result = runtime.query(request.query)
            return {"status": "success", "result": result}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/replay")
    async def replay_run(request: ReplayRequest) -> dict[str, Any]:
        """Replay a previous run."""
        try:
            result = runtime.replay(request.run_id)
            return {"status": "success", "result": result}
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.get("/policies")
    async def list_policies() -> dict[str, Any]:
        """List all policies."""
        return {"policies": runtime.policy_engine.list_policies()}

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        """Prometheus metrics endpoint."""
        return generate_prometheus_metrics()

    @app.websocket("/ws/events")
    async def websocket_events(
        websocket: WebSocket,
        event_types: str | None = Query(None, description="Comma-separated event types"),
    ):
        """
        WebSocket endpoint for real-time event streaming.

        Query params:
            event_types: Comma-separated list of event types to filter
        """
        types_list = event_types.split(",") if event_types else None
        await handle_websocket_connection(websocket, types_list)

    @app.websocket("/ws/events/{run_id}")
    async def websocket_events_for_run(
        websocket: WebSocket,
        run_id: str,
    ):
        """WebSocket endpoint for events from a specific run."""
        await handle_websocket_connection(websocket, run_id=run_id)

    @app.get("/ws/info")
    async def websocket_info() -> dict[str, Any]:
        """Get information about active WebSocket connections."""
        return ws_manager.get_connection_info()

    return app


# Create default app instance
app = create_app()
