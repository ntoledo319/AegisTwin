"""
Main FastAPI application for the Advanced Data Analysis & Digital Twin System.
This module sets up the API gateway that handles all external requests.
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List

# Import routes
from .routes import analysis, data, twin, visualization, digital_twin

# Setup logging
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Advanced Data Analysis & Digital Twin API",
    description="API for the Advanced Data Analysis & Digital Twin System",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "healthy", "version": app.version}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Advanced Data Analysis & Digital Twin API",
        "version": app.version,
        "documentation": "/docs",
    }

# Include routers
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(twin.router, prefix="/api/twin", tags=["Digital Twin"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["Visualization"])
app.include_router(digital_twin.router, prefix="/api", tags=["Digital Twin Components"])

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("API starting up")
    # Initialize services, connections, etc.

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("API shutting down")
    # Close connections, cleanup, etc.