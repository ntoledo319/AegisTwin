"""
Routes module for the web interface.

This module provides routes for the web interface,
including API routes and web routes.
"""

import logging
from typing import Dict, List, Any, Optional
from .api import APIRoutes
from .web import WebRoutes

logger = logging.getLogger(__name__)

class RouteManager:
    """Manager for web routes."""
    
    def __init__(self, app=None, core_engine=None):
        """
        Initialize the route manager.
        
        Args:
            app: Web application instance
            core_engine: Core engine instance
        """
        self.app = app
        self.core_engine = core_engine
        self.api_routes = APIRoutes(app, core_engine)
        self.web_routes = WebRoutes(app, core_engine)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the route manager."""
        logger.info("Initializing route manager")
        
        # Initialize routes
        await self.api_routes.initialize()
        await self.web_routes.initialize()
        
        self.initialized = True
        logger.info("Route manager initialized")