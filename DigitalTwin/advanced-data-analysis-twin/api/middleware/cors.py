"""
CORS middleware configuration for the API.
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os
from typing import List

def setup_cors(app: FastAPI):
    """
    Set up CORS middleware for the FastAPI application.
    
    Parameters:
    - app: FastAPI application instance
    """
    # Get allowed origins from environment variable or use default
    allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    
    # Parse allowed origins
    if allowed_origins_str == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

def get_cors_config():
    """
    Get the CORS configuration.
    
    Returns:
    - Dictionary with CORS configuration
    """
    # Get allowed origins from environment variable or use default
    allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    
    # Parse allowed origins
    if allowed_origins_str == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }