"""
Web routes for the web interface.

This module provides web routes for the web interface,
enabling interaction with the integrated system through a web browser.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WebRoutes:
    """Web routes for the web interface."""
    
    def __init__(self, app=None, core_engine=None):
        """
        Initialize the web routes.
        
        Args:
            app: Web application instance
            core_engine: Core engine instance
        """
        self.app = app
        self.core_engine = core_engine
        self.initialized = False
    
    async def initialize(self):
        """Initialize the web routes."""
        logger.info("Initializing web routes")
        
        if not self.app:
            logger.warning("No app provided for web routes")
            return
        
        # Register routes
        self._register_routes()
        
        self.initialized = True
        logger.info("Web routes initialized")
    
    def _register_routes(self):
        """Register web routes with the app."""
        app = self.app
        
        # Home page
        @app.route('/', methods=['GET'])
        async def home():
            """Home page."""
            logger.info("Web: Home page")
            
            return await app.render_template('index.html', title="Integrated System")
        
        # Dashboard page
        @app.route('/dashboard', methods=['GET'])
        async def dashboard():
            """Dashboard page."""
            logger.info("Web: Dashboard page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get user data
                user_id = app.session.get('user_id', 'default')
                user = await self.core_engine.get_user(user_id)
                
                # Get dashboard data
                dashboard_data = await self.core_engine.get_dashboard_data(user_id)
                
                return await app.render_template(
                    'dashboard.html',
                    title="Dashboard",
                    user=user,
                    dashboard=dashboard_data
                )
            except Exception as e:
                logger.error(f"Error rendering dashboard: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Data page
        @app.route('/data', methods=['GET'])
        async def data():
            """Data page."""
            logger.info("Web: Data page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get data sources
                sources = await self.core_engine.get_data_sources()
                
                # Get imported data
                user_id = app.session.get('user_id', 'default')
                imported_data = await self.core_engine.get_imported_data(user_id)
                
                return await app.render_template(
                    'data.html',
                    title="Data Management",
                    sources=sources,
                    imported_data=imported_data
                )
            except Exception as e:
                logger.error(f"Error rendering data page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Analysis page
        @app.route('/analysis', methods=['GET'])
        async def analysis():
            """Analysis page."""
            logger.info("Web: Analysis page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get analysis types
                analysis_types = await self.core_engine.get_analysis_types()
                
                # Get user's analyses
                user_id = app.session.get('user_id', 'default')
                analyses = await self.core_engine.get_user_analyses(user_id)
                
                return await app.render_template(
                    'analysis.html',
                    title="Analysis",
                    analysis_types=analysis_types,
                    analyses=analyses
                )
            except Exception as e:
                logger.error(f"Error rendering analysis page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Analysis result page
        @app.route('/analysis/<analysis_id>', methods=['GET'])
        async def analysis_result(analysis_id):
            """Analysis result page."""
            logger.info(f"Web: Analysis result page for {analysis_id}")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get analysis
                analysis = await self.core_engine.get_analysis(analysis_id)
                
                if not analysis:
                    return await app.render_template('error.html', error='Analysis not found')
                
                return await app.render_template(
                    'analysis_result.html',
                    title=f"Analysis: {analysis.get('name', analysis_id)}",
                    analysis=analysis
                )
            except Exception as e:
                logger.error(f"Error rendering analysis result page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Digital twin page
        @app.route('/digital-twin', methods=['GET'])
        async def digital_twin():
            """Digital twin page."""
            logger.info("Web: Digital twin page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get digital twin state
                user_id = app.session.get('user_id', 'default')
                twin_state = await self.core_engine.get_twin_state(user_id)
                
                # Get conversation history
                session_id = app.request.args.get('session_id', 'default')
                conversation_history = await self.core_engine.get_conversation_history(user_id, session_id)
                
                return await app.render_template(
                    'digital_twin.html',
                    title="Digital Twin",
                    twin_state=twin_state,
                    conversation_history=conversation_history,
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"Error rendering digital twin page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Knowledge graph page
        @app.route('/knowledge-graph', methods=['GET'])
        async def knowledge_graph():
            """Knowledge graph page."""
            logger.info("Web: Knowledge graph page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get knowledge graph data
                user_id = app.session.get('user_id', 'default')
                graph_data = await self.core_engine.get_knowledge_graph(user_id)
                
                return await app.render_template(
                    'knowledge_graph.html',
                    title="Knowledge Graph",
                    graph_data=graph_data
                )
            except Exception as e:
                logger.error(f"Error rendering knowledge graph page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Settings page
        @app.route('/settings', methods=['GET'])
        async def settings():
            """Settings page."""
            logger.info("Web: Settings page")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get user settings
                user_id = app.session.get('user_id', 'default')
                user_settings = await self.core_engine.get_user_settings(user_id)
                
                return await app.render_template(
                    'settings.html',
                    title="Settings",
                    settings=user_settings
                )
            except Exception as e:
                logger.error(f"Error rendering settings page: {str(e)}")
                return await app.render_template('error.html', error=str(e))
        
        # Login page
        @app.route('/login', methods=['GET'])
        async def login():
            """Login page."""
            logger.info("Web: Login page")
            
            return await app.render_template('login.html', title="Login")
        
        # Login form submission
        @app.route('/login', methods=['POST'])
        async def login_post():
            """Login form submission."""
            logger.info("Web: Login form submission")
            
            if not self.core_engine:
                return await app.render_template('error.html', error='Core engine not available')
            
            try:
                # Get form data
                form_data = await app.request.form()
                username = form_data.get('username')
                password = form_data.get('password')
                
                # Authenticate user
                auth_result = await self.core_engine.authenticate_user(username, password)
                
                if auth_result.get('success'):
                    # Set session
                    app.session['user_id'] = auth_result.get('user_id')
                    app.session['username'] = username
                    
                    # Redirect to dashboard
                    return app.redirect('/dashboard')
                else:
                    # Show error
                    return await app.render_template(
                        'login.html',
                        title="Login",
                        error=auth_result.get('error', 'Authentication failed')
                    )
            except Exception as e:
                logger.error(f"Error processing login: {str(e)}")
                return await app.render_template('login.html', title="Login", error=str(e))
        
        # Logout
        @app.route('/logout', methods=['GET'])
        async def logout():
            """Logout."""
            logger.info("Web: Logout")
            
            # Clear session
            app.session.clear()
            
            # Redirect to login
            return app.redirect('/login')
        
        logger.info("Web routes registered")