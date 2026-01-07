"""
FastAPI Web Interface Integration

Integrates the web templates and routes with the main FastAPI application
to provide a complete web UI for the Cognitive-Twin system.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

logger = logging.getLogger(__name__)

class WebIntegration:
    """Web interface integration for FastAPI"""
    
    def __init__(self, app: FastAPI, core_engine=None):
        """
        Initialize web integration.
        
        Args:
            app: FastAPI application instance
            core_engine: Core engine instance for data access
        """
        self.app = app
        self.core_engine = core_engine
        
        # Setup paths
        self.web_dir = Path(__file__).parent
        self.templates_dir = self.web_dir / "templates"
        self.static_dir = self.web_dir / "static"
        
        # Initialize templates
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        # Setup middleware
        self._setup_middleware()
        
        # Mount static files
        self._mount_static_files()
        
        # Register routes
        self._register_routes()
        
        logger.info("Web integration initialized")
    
    def _setup_middleware(self):
        """Setup middleware for the web interface"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    def _mount_static_files(self):
        """Mount static file directories"""
        if self.static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
            logger.info(f"Mounted static files from {self.static_dir}")
        else:
            logger.warning(f"Static directory not found: {self.static_dir}")
    
    def _register_routes(self):
        """Register all web routes"""
        
        @self.app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def home(request: Request):
            """Home page"""
            return self.templates.TemplateResponse(
                "index.html",
                {"request": request, "title": "Home"}
            )
        
        @self.app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard(request: Request):
            """Dashboard page"""
            try:
                # Get dashboard data
                dashboard_data = await self._get_dashboard_data()
                
                return self.templates.TemplateResponse(
                    "dashboard.html",
                    {
                        "request": request,
                        "title": "Dashboard",
                        "dashboard": dashboard_data,
                        "user": {"username": "User"}  # Default user
                    }
                )
            except Exception as e:
                logger.error(f"Error rendering dashboard: {e}")
                return await self._render_error(request, str(e))
        
        @self.app.get("/digital-twin", response_class=HTMLResponse, include_in_schema=False)
        async def digital_twin(request: Request, session_id: Optional[str] = "default"):
            """Digital twin chat page"""
            try:
                # Get twin data
                twin_data = await self._get_twin_data()
                conversation_history = await self._get_conversation_history(session_id)
                
                return self.templates.TemplateResponse(
                    "digital_twin.html",
                    {
                        "request": request,
                        "title": "Digital Twin",
                        "twin_state": twin_data,
                        "conversation_history": conversation_history,
                        "session_id": session_id
                    }
                )
            except Exception as e:
                logger.error(f"Error rendering digital twin page: {e}")
                return await self._render_error(request, str(e))
        
        @self.app.get("/data", response_class=HTMLResponse, include_in_schema=False)
        async def data_management(request: Request):
            """Data management page"""
            return self.templates.TemplateResponse(
                "data.html",
                {
                    "request": request,
                    "title": "Data Management",
                    "data_sources": await self._get_data_sources(),
                    "imported_data": await self._get_imported_data()
                }
            )
        
        @self.app.get("/analysis", response_class=HTMLResponse, include_in_schema=False)
        async def analysis(request: Request):
            """Analysis page"""
            return self.templates.TemplateResponse(
                "analysis.html",
                {
                    "request": request,
                    "title": "Analysis",
                    "analysis_types": await self._get_analysis_types(),
                    "analyses": await self._get_user_analyses()
                }
            )
        
        @self.app.get("/analysis/{analysis_id}", response_class=HTMLResponse, include_in_schema=False)
        async def analysis_result(request: Request, analysis_id: str):
            """Analysis result page"""
            try:
                analysis = await self._get_analysis(analysis_id)
                if not analysis:
                    raise HTTPException(status_code=404, detail="Analysis not found")
                
                return self.templates.TemplateResponse(
                    "analysis_result.html",
                    {
                        "request": request,
                        "title": f"Analysis: {analysis.get('name', analysis_id)}",
                        "analysis": analysis
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error rendering analysis result: {e}")
                return await self._render_error(request, str(e))
        
        @self.app.get("/knowledge-graph", response_class=HTMLResponse, include_in_schema=False)
        async def knowledge_graph(request: Request):
            """Knowledge graph page"""
            return self.templates.TemplateResponse(
                "knowledge_graph.html",
                {
                    "request": request,
                    "title": "Knowledge Graph",
                    "graph_data": await self._get_knowledge_graph_data()
                }
            )
        
        @self.app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
        async def settings(request: Request):
            """Settings page"""
            return self.templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "title": "Settings",
                    "settings": await self._get_user_settings()
                }
            )
        
        @self.app.get("/login", response_class=HTMLResponse, include_in_schema=False)
        async def login(request: Request):
            """Login page"""
            return self.templates.TemplateResponse(
                "login.html",
                {"request": request, "title": "Login"}
            )
        
        # Add API endpoints for dashboard data refresh
        @self.app.get("/api/dashboard/stats", include_in_schema=False)
        async def dashboard_stats():
            """Get dashboard statistics for AJAX refresh"""
            return await self._get_dashboard_data()
        
        # Add endpoint for real dashboard stats that aligns with actual API
        @self.app.get("/api/v1/dashboard/stats", include_in_schema=False)
        async def dashboard_stats_v1():
            """Get dashboard statistics using v1 API format"""
            return await self._get_dashboard_data()
        
        # Settings API endpoints
        @self.app.get("/api/v1/settings")
        async def get_settings():
            """Get user settings"""
            return await self._get_user_settings()
        
        @self.app.put("/api/v1/settings")
        async def update_settings(settings: Dict[str, Any]):
            """Update user settings"""
            try:
                updated_settings = await self._update_user_settings(settings)
                return JSONResponse(
                    content={"success": True, "settings": updated_settings},
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                return JSONResponse(
                    content={"error": str(e)},
                    status_code=500
                )
        
        @self.app.patch("/api/v1/settings")
        async def patch_settings(settings: Dict[str, Any]):
            """Partially update user settings"""
            try:
                updated_settings = await self._patch_user_settings(settings)
                return JSONResponse(
                    content={"success": True, "settings": updated_settings},
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Error patching settings: {e}")
                return JSONResponse(
                    content={"error": str(e)},
                    status_code=500
                )
        
        logger.info("Web routes registered")
    
    async def _render_error(self, request: Request, error: str):
        """Render error page"""
        try:
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "title": "Error",
                    "error": error
                }
            )
        except Exception:
            # Fallback to plain HTML if template fails
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head><title>Error - Cognitive-Twin</title></head>
                <body>
                    <h1>Error</h1>
                    <p>{error}</p>
                    <a href="/">Return Home</a>
                </body>
                </html>
                """,
                status_code=500
            )
    
    async def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data"""
        try:
            if self.core_engine and hasattr(self.core_engine, 'get_dashboard_data'):
                return await self.core_engine.get_dashboard_data('default_user')
            
            # Fallback data
            return {
                "data_sources_count": 3,
                "analyses_count": 7,
                "conversations_count": 42,
                "insights_count": 15,
                "recent_activities": [
                    {
                        "title": "New conversation started",
                        "icon": "comments",
                        "time_ago": "2 minutes ago"
                    },
                    {
                        "title": "Data analysis completed",
                        "icon": "chart-line",
                        "time_ago": "1 hour ago"
                    },
                    {
                        "title": "Personality profile updated",
                        "icon": "user",
                        "time_ago": "3 hours ago"
                    }
                ],
                "recent_insights": [
                    {
                        "title": "Communication Pattern",
                        "description": "You tend to be more active in the mornings",
                        "type": "info",
                        "category": "Behavior",
                        "created_at": "Today"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "data_sources_count": 0,
                "analyses_count": 0,
                "conversations_count": 0,
                "insights_count": 0,
                "recent_activities": [],
                "recent_insights": []
            }
    
    async def _get_twin_data(self) -> Dict[str, Any]:
        """Get digital twin data"""
        try:
            if self.core_engine and hasattr(self.core_engine, 'get_twin_state'):
                return await self.core_engine.get_twin_state('default_user')
            
            # Fallback data
            return {
                "name": "Your Cognitive Twin",
                "status": "Active and Learning",
                "personality_traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.6,
                    "extraversion": 0.5,
                    "agreeableness": 0.8,
                    "neuroticism": 0.3
                }
            }
        except Exception as e:
            logger.error(f"Error getting twin data: {e}")
            return {
                "name": "Your Cognitive Twin",
                "status": "Learning",
                "personality_traits": {
                    "openness": 0.5,
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.5
                }
            }
    
    async def _get_conversation_history(self, session_id: str) -> list:
        """Get conversation history"""
        try:
            if self.core_engine and hasattr(self.core_engine, 'get_conversation_history'):
                return await self.core_engine.get_conversation_history('default_user', session_id)
            
            # Fallback data
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def _get_data_sources(self) -> list:
        """Get available data sources"""
        return [
            {"name": "Email", "type": "email", "status": "available", "icon": "envelope", "description": "Import .eml, .mbox, or .json email files"},
            {"name": "Messages", "type": "messages", "status": "available", "icon": "comments", "description": "WhatsApp, Telegram, Signal exports (.json, .csv, .txt)"},
            {"name": "Calendar", "type": "calendar", "status": "available", "icon": "calendar", "description": "Calendar events from .ics or .csv files"},
            {"name": "Social Media", "type": "social", "status": "available", "icon": "share-alt", "description": "Social media data exports (.json)"}
        ]
    
    async def _get_imported_data(self) -> list:
        """Get imported data"""
        return []
    
    async def _get_analysis_types(self) -> list:
        """Get available analysis types"""
        return [
            {"name": "Communication Analysis", "type": "communication", "description": "Analyze patterns, relationships, and topics in your communication data"},
            {"name": "Personality Analysis", "type": "personality", "description": "Extract personality traits, values, and decision-making patterns"},
            {"name": "Temporal Analysis", "type": "temporal", "description": "Analyze time-based patterns and trends in your data"},
            {"name": "Network Analysis", "type": "network", "description": "Map relationships and connections between entities"},
            {"name": "Advanced NLP", "type": "nlp", "description": "Deep natural language processing including sentiment, entities, and topics"},
            {"name": "Comprehensive", "type": "comprehensive", "description": "Run all available analyses for complete insights"}
        ]
    
    async def _get_user_analyses(self) -> list:
        """Get user analyses"""
        return []
    
    async def _get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get specific analysis"""
        return None
    
    async def _get_knowledge_graph_data(self) -> Dict[str, Any]:
        """Get knowledge graph data"""
        return {
            "nodes": [],
            "links": []
        }
    
    async def _get_user_settings(self) -> Dict[str, Any]:
        """Get user settings"""
        try:
            if self.core_engine and hasattr(self.core_engine, 'get_user_settings'):
                return await self.core_engine.get_user_settings('default_user')
            
            # Default settings
            return {
                # General
                "theme": "light",
                "language": "en",
                "auto_save": True,
                "realtime": True,
                # AI & Models
                "openrouter_api_key": "",
                "default_model": "anthropic/claude-3-sonnet",
                "response_style": "balanced",
                "cost_optimization": True,
                # Data & Privacy
                "data_retention": 365,
                "auto_cleanup": True,
                "analytics": False,
                # Notifications
                "analysis_notif": True,
                "insights_notif": True,
                "system_notif": False,
                "email_notif": False,
                # Advanced
                "debug": False,
                "rate_limit": 10,
                "cache_size": 1000
            }
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return {}
    
    async def _update_user_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings (full replace)"""
        try:
            if self.core_engine and hasattr(self.core_engine, 'update_user_settings'):
                return await self.core_engine.update_user_settings('default_user', settings)
            
            # For now, just return the settings as-is
            logger.info(f"Settings updated: {list(settings.keys())}")
            return settings
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            raise
    
    async def _patch_user_settings(self, partial_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update user settings (merge with existing)"""
        try:
            current_settings = await self._get_user_settings()
            
            # Merge settings
            updated_settings = {**current_settings, **partial_settings}
            
            if self.core_engine and hasattr(self.core_engine, 'update_user_settings'):
                return await self.core_engine.update_user_settings('default_user', updated_settings)
            
            # For now, just return the merged settings
            logger.info(f"Settings patched: {list(partial_settings.keys())}")
            return updated_settings
        except Exception as e:
            logger.error(f"Error patching user settings: {e}")
            raise

def setup_web_interface(app: FastAPI, core_engine=None) -> WebIntegration:
    """
    Setup web interface integration.
    
    Args:
        app: FastAPI application
        core_engine: Core engine instance
        
    Returns:
        WebIntegration instance
    """
    web_integration = WebIntegration(app, core_engine)
    logger.info("Web interface setup complete")
    return web_integration
