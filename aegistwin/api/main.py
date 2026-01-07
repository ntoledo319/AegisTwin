"""
AegisTwin FastAPI Application

REST API for AegisTwin operations including health checks, demos, queries, and replay.

@ai_prompt: Mount this app or run standalone with uvicorn.
@context_boundary: aegistwin/api/main

# AI-GENERATED 2026-01-06
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aegistwin.runtime.core import AegisTwinRuntime
from aegistwin.demos import run_demo, run_all_demos


class IngestRequest(BaseModel):
    """Request body for ingestion."""
    data: Dict[str, Any]
    source: str = "api"


class QueryRequest(BaseModel):
    """Request body for queries."""
    query: str
    context: Optional[Dict[str, Any]] = None


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
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint with API info."""
        return {
            "name": "AegisTwin",
            "tagline": "Event-driven agent runtime + governance + deterministic replay + local memory graph",
            "docs": "/docs",
        }
    
    @app.post("/demo/{demo_name}")
    async def run_demo_endpoint(demo_name: str) -> Dict[str, Any]:
        """Run a demo by name."""
        try:
            if demo_name == "all":
                result = run_all_demos()
            else:
                result = run_demo(demo_name)
            return {"status": "success", "result": result}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ingest")
    async def ingest_data(request: IngestRequest) -> Dict[str, Any]:
        """Ingest data into the system."""
        try:
            run_id = runtime.ingest(request.data, request.source)
            return {"status": "success", "run_id": run_id}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/query")
    async def query_system(request: QueryRequest) -> Dict[str, Any]:
        """Query the system."""
        try:
            result = runtime.query(request.query)
            return {"status": "success", "result": result}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/replay")
    async def replay_run(request: ReplayRequest) -> Dict[str, Any]:
        """Replay a previous run."""
        try:
            result = runtime.replay(request.run_id)
            return {"status": "success", "result": result}
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/policies")
    async def list_policies() -> Dict[str, Any]:
        """List all policies."""
        return {"policies": runtime.policy_engine.list_policies()}
    
    return app


# Create default app instance
app = create_app()
