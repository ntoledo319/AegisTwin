"""
Main entry point for the Advanced Data Analysis & Digital Twin System.
"""

import os
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv
from api import app
from core.db import db_manager

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

async def startup():
    """
    Startup tasks for the application.
    """
    logger.info("Starting Advanced Data Analysis & Digital Twin System...")
    
    # Initialize database connections
    await db_manager.initialize()
    
    logger.info("System startup complete")

async def shutdown():
    """
    Shutdown tasks for the application.
    """
    logger.info("Shutting down Advanced Data Analysis & Digital Twin System...")
    
    # Close database connections
    await db_manager.shutdown()
    
    logger.info("System shutdown complete")

@app.on_event("startup")
async def app_startup():
    """
    FastAPI startup event handler.
    """
    await startup()

@app.on_event("shutdown")
async def app_shutdown():
    """
    FastAPI shutdown event handler.
    """
    await shutdown()

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