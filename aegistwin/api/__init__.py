"""
AegisTwin API Module

FastAPI control plane for health, demo, query, and replay endpoints.

@ai_prompt: Run with `uvicorn aegistwin.api:app` for the REST API.
@context_boundary: aegistwin/api
"""

from aegistwin.api.main import app, create_app

__all__ = ["app", "create_app"]
