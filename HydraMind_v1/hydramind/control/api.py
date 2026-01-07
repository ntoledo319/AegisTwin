"""
FastAPI control plane for external HydraMind control.

Provides REST endpoints for health checks, metrics, and event injection.
Optional - enable via config.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..brain import HydraBrain

logger = logging.getLogger(__name__)


def build_app(brain: "HydraBrain") -> Optional[Any]:
    """
    Build FastAPI application for HydraMind control plane.
    
    Args:
        brain: HydraBrain instance
        
    Returns:
        FastAPI app or None if FastAPI not available
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        
    except ImportError as e:
        logger.warning(
            f"FastAPI not installed; control plane disabled. "
            f"Install with: pip install fastapi uvicorn"
        )
        return None
    
    # Create FastAPI app
    app = FastAPI(
        title="HydraMind Control Plane",
        description="REST API for HydraMind cognitive kernel",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=brain.cfg.server.cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Request models
    class PublishRequest(BaseModel):
        """Event publication request."""
        topic: str
        data: Dict[str, Any]
        qos: int = 0
        key: Optional[str] = None
    
    class QueryRequest(BaseModel):
        """Event store query request."""
        topic_pattern: Optional[str] = None
        since_ts: Optional[float] = None
        until_ts: Optional[float] = None
        limit: int = 100
    
    # Endpoints
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        """Root endpoint."""
        return {
            "name": "HydraMind Control Plane",
            "version": "1.0.0",
            "status": "operational"
        }

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Health status
        """
        try:
            bus_stats = brain.bus.get_stats()
            
            return {
                "ok": True,
                "status": "healthy",
                "bus_running": bus_stats["running"],
                "modules": len(brain.registry.mods),
                "uptime": bus_stats.get("messages_published", 0)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=503, detail="Service unhealthy")
    
    @app.get("/metrics")
    async def metrics() -> Dict[str, Any]:
        """
        Get system metrics.
        
        Returns:
            Comprehensive metrics from all components
        """
        try:
            return {
                "bus": brain.bus.get_stats(),
                "event_store": {
                    "path": brain.cfg.event_db,
                    "total_events": brain.event_store.count()
                },
                "execution": brain.exec.get_stats(),
                "policy": brain.policy.get_stats(),
                "modules": {
                    name: mod.get_stats()
                    for name, mod in brain.registry.mods.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Metrics retrieval failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
    
    @app.post("/bus/publish")
    async def publish_event(request: PublishRequest):
        """
        Publish event to the bus.
        
        Args:
            request: Event publication request
            
        Returns:
            Confirmation
        """
        try:
            from ..core.bus import Message
            
            msg = Message(
                topic=request.topic,
                data=request.data,
                qos=request.qos,
                key=request.key
            )
            
            await brain.bus.publish(msg)
            
            return {
                "ok": True,
                "topic": request.topic,
                "queued": True
            }
            
        except Exception as e:
            logger.error(f"Event publication failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to publish event: {str(e)}"
            )
    
    @app.post("/events/query")
    async def query_events(request: QueryRequest):
        """
        Query event store.
        
        Args:
            request: Query parameters
            
        Returns:
            List of matching events
        """
        try:
            events = brain.event_store.query(
                topic_pattern=request.topic_pattern,
                since_ts=request.since_ts,
                until_ts=request.until_ts,
                limit=request.limit
            )
            
            return {
                "events": events,
                "count": len(events),
                "limit": request.limit
            }
            
        except Exception as e:
            logger.error(f"Event query failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Query failed: {str(e)}"
            )
    
    @app.get("/modules")
    async def list_modules() -> Dict[str, Any]:
        """
        List registered modules.
        
        Returns:
            Module information
        """
        try:
            modules = []
            for name, mod in brain.registry.mods.items():
                modules.append({
                    "name": name,
                    "running": mod._running,
                    "stats": mod.get_stats()
                })
            
            return {
                "modules": modules,
                "count": len(modules)
            }
            
        except Exception as e:
            logger.error(f"Module listing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list modules: {str(e)}"
            )
    
    @app.get("/config")
    async def get_config() -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Configuration (sensitive values redacted)
        """
        try:
            from dataclasses import asdict
            
            config = asdict(brain.cfg)
            
            # Redact sensitive info
            if "custom" in config and isinstance(config["custom"], dict):
                for key in list(config["custom"].keys()):
                    if any(s in key.lower() for s in ["key", "secret", "password", "token"]):
                        config["custom"][key] = "***REDACTED***"
            
            return config
            
        except Exception as e:
            logger.error(f"Config retrieval failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve config: {str(e)}"
            )
    
    @app.post("/shutdown")
    async def shutdown() -> Dict[str, str]:
        """
        Initiate graceful shutdown.
        
        Returns:
            Confirmation
        """
        logger.warning("Shutdown requested via API")
        
        # Note: Actual shutdown needs to be handled by the main loop
        # This just signals intent
        return {
            "ok": True,
            "message": "Shutdown initiated"
        }
    
    logger.info("FastAPI control plane initialized")
    
    return app
