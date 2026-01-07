"""
Main entry point for the Integrated Data Analysis & Cognitive Twin System.
"""

import os
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import config
from core.db import db_manager
from core.engine import Engine
from api.endpoints import router as api_router
from web.fastapi_integration import setup_web_interface

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cognitive-Twin: Advanced Data Analysis & Digital Twin System",
    description="A sophisticated platform for personal data analysis, cognitive modeling, and AI-powered digital twin interaction.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Setup web interface
web_integration = setup_web_interface(app)

# Create engine instance
engine = None

@app.on_event("startup")
async def startup():
    """
    Startup tasks for the application.
    """
    global engine
    
    logger.info("Starting Cognitive-Twin System...")
    
    # Initialize database connections
    await db_manager.initialize()
    
    # Initialize core engine
    engine = Engine()
    await engine.initialize()
    
    # Connect engine to web integration
    web_integration.core_engine = engine
    
    logger.info("Cognitive-Twin system startup complete")

@app.on_event("shutdown")
async def shutdown():
    """
    Shutdown tasks for the application.
    """
    logger.info("Shutting down Cognitive-Twin System...")
    
    # Close database connections
    await db_manager.shutdown()
    
    # Shutdown engine
    if engine:
        await engine.shutdown()
    
    logger.info("Cognitive-Twin system shutdown complete")

# Note: Root endpoint is now handled by web integration

def run_server():
    """
    Run the FastAPI server.
    """
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )

if __name__ == "__main__":
    run_server()