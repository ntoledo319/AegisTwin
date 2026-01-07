"""
Web Interface Module for Cognitive-Twin Integrated System.

This module provides comprehensive web interface capabilities for the integrated system,
including HTTP routes, template rendering, static file serving, and session management.
The web interface serves as the primary user interaction layer for the Cognitive-Twin platform.

Usage:
    from integrated_system.web import WebInterface
    from core.engine import Engine
    
    engine = Engine()
    web_interface = WebInterface(core_engine=engine)
    await web_interface.initialize()
    await web_interface.start(host="0.0.0.0", port=8080)

Example:
    >>> web_interface = WebInterface()
    >>> success = await web_interface.initialize()
    >>> if success:
    ...     await web_interface.start()

Dependencies:
    - aiohttp: Async HTTP framework for web server capabilities
    - aiohttp_jinja2: Template rendering support
    - jinja2: Template engine for dynamic content generation

# VOCAB: RouteManager - Manages HTTP routes and endpoint mappings
# VOCAB: SessionMiddleware - Handles user session state across requests
# @context_boundary: Web Interface Layer
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import os
try:
    from aiohttp import web
    import aiohttp_jinja2
    import jinja2
except ImportError:
    web = None
    aiohttp_jinja2 = None
    jinja2 = None
from .routes import RouteManager

logger = logging.getLogger(__name__)

class WebInterface:
    """
    Web Interface for Cognitive-Twin Integrated System.
    
    Provides HTTP-based access to the Cognitive-Twin platform through a web interface.
    Handles route management, template rendering, static file serving, and user sessions.
    
    This class manages the complete web application lifecycle including initialization,
    startup, request handling, and graceful shutdown.
    
    Attributes:
        core_engine: Reference to the main system engine
        app: aiohttp web application instance
        route_manager: Handles HTTP route configuration
        initialized: Flag indicating initialization status
        server: Server instance information for shutdown
        
    Features:
        - Async HTTP request handling
        - Jinja2 template rendering
        - Static file serving
        - Session middleware
        - Graceful startup/shutdown
        
    Error Handling:
        Gracefully handles missing dependencies and initialization failures.
        Falls back to degraded mode when web framework is unavailable.
    """
    
    def __init__(self, core_engine: Optional[Any] = None) -> None:
        """
        Initialize the web interface with optional core engine.
        
        Args:
            core_engine: Optional core engine instance for system integration.
                        If None, web interface will operate in standalone mode.
                        
        Note:
            The core engine provides access to data processing, analysis,
            and digital twin capabilities. Without it, the web interface
            will have limited functionality.
        """
        self.core_engine = core_engine
        self.app = None
        self.route_manager = None
        self.initialized = False
        self.server = None
    
    async def initialize(self) -> bool:
        """
        Initialize the web interface with all required components.
        
        Sets up the aiohttp web application, configures Jinja2 templating,
        establishes static file serving, and initializes route management.
        
        Returns:
            bool: True if initialization successful, False if failed
            
        Raises:
            ImportError: When required web dependencies are not available
            
        Note:
            This method is idempotent - calling it multiple times is safe.
            If dependencies are missing, the method logs errors and returns False.
        """
        logger.info("Initializing web interface")
        
        try:
            # Import web framework
            import aiohttp
            from aiohttp import web
            import aiohttp_jinja2
            import jinja2
            
            # Create app
            self.app = web.Application()
            
            # Set up Jinja2 templates
            template_path = os.path.join(os.path.dirname(__file__), 'templates')
            aiohttp_jinja2.setup(
                self.app,
                loader=jinja2.FileSystemLoader(template_path)
            )
            
            # Set up static files
            static_path = os.path.join(os.path.dirname(__file__), 'static')
            self.app.router.add_static('/static', static_path)
            
            # Set up session middleware
            self.app.middlewares.append(self._session_middleware)
            
            # Set up routes
            self.route_manager = RouteManager(self.app, self.core_engine)
            await self.route_manager.initialize()
            
            self.initialized = True
            logger.info("Web interface initialized")
            return True
        except ImportError as e:
            logger.error(f"Error initializing web interface: {str(e)}")
            logger.error("Web framework not available. Please install aiohttp and aiohttp_jinja2.")
            return False
        except Exception as e:
            logger.error(f"Error initializing web interface: {str(e)}")
            return False
    
    async def _session_middleware(self, request, handler):
        """Session middleware."""
        # Create session if it doesn't exist
        if not hasattr(request, 'session'):
            request.session = {}
        
        # Process request
        response = await handler(request)
        
        return response
    
    async def start(self, host='0.0.0.0', port=8080):
        """
        Start the web interface.
        
        Args:
            host: Host to listen on
            port: Port to listen on
            
        Returns:
            True if started successfully, False otherwise
        """
        logger.info(f"Starting web interface on {host}:{port}")
        
        if not self.initialized:
            success = await self.initialize()
            if not success:
                logger.error("Failed to initialize web interface")
                return False
        
        try:
            from aiohttp import web
            
            # Start server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, host, port)
            await site.start()
            
            self.server = {
                'runner': runner,
                'site': site
            }
            
            logger.info(f"Web interface started on http://{host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Error starting web interface: {str(e)}")
            return False
    
    async def stop(self):
        """Stop the web interface."""
        logger.info("Stopping web interface")
        
        if self.server:
            try:
                await self.server['runner'].cleanup()
                logger.info("Web interface stopped")
                return True
            except Exception as e:
                logger.error(f"Error stopping web interface: {str(e)}")
                return False
        
        return True