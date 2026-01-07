"""
API routes for the web interface.

This module provides API routes for the web interface,
enabling interaction with the integrated system through HTTP requests.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class APIRoutes:
    """API routes for the web interface."""
    
    def __init__(self, app=None, core_engine=None):
        """
        Initialize the API routes.
        
        Args:
            app: Web application instance
            core_engine: Core engine instance
        """
        self.app = app
        self.core_engine = core_engine
        self.initialized = False
    
    async def initialize(self):
        """Initialize the API routes."""
        logger.info("Initializing API routes")
        
        if not self.app:
            logger.warning("No app provided for API routes")
            return
        
        # Register routes
        self._register_routes()
        
        self.initialized = True
        logger.info("API routes initialized")
    
    def _register_routes(self):
        """Register API routes with the app."""
        app = self.app
        
        # User routes
        @app.route('/api/users', methods=['GET'])
        async def get_users():
            """Get all users."""
            logger.info("API: Get users")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                users = await self.core_engine.get_users()
                return {'users': users}, 200
            except Exception as e:
                logger.error(f"Error getting users: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/users/<user_id>', methods=['GET'])
        async def get_user(user_id):
            """Get a specific user."""
            logger.info(f"API: Get user {user_id}")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                user = await self.core_engine.get_user(user_id)
                if user:
                    return user, 200
                else:
                    return {'error': 'User not found'}, 404
            except Exception as e:
                logger.error(f"Error getting user: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/users', methods=['POST'])
        async def create_user():
            """Create a new user."""
            logger.info("API: Create user")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                data = await app.request.json()
                user = await self.core_engine.create_user(data)
                return user, 201
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                return {'error': str(e)}, 500
        
        # Data routes
        @app.route('/api/data/sources', methods=['GET'])
        async def get_data_sources():
            """Get all data sources."""
            logger.info("API: Get data sources")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                sources = await self.core_engine.get_data_sources()
                return {'sources': sources}, 200
            except Exception as e:
                logger.error(f"Error getting data sources: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/data/import', methods=['POST'])
        async def import_data():
            """Import data from a source."""
            logger.info("API: Import data")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                data = await app.request.json()
                source = data.get('source')
                options = data.get('options', {})
                
                result = await self.core_engine.import_data(source, options)
                return result, 200
            except Exception as e:
                logger.error(f"Error importing data: {str(e)}")
                return {'error': str(e)}, 500
        
        # Analysis routes
        @app.route('/api/analysis', methods=['POST'])
        async def analyze_data():
            """Analyze data."""
            logger.info("API: Analyze data")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                data = await app.request.json()
                analysis_type = data.get('type', 'comprehensive')
                data_id = data.get('data_id')
                options = data.get('options', {})
                
                result = await self.core_engine.analyze(data_id, analysis_type, options)
                return result, 200
            except Exception as e:
                logger.error(f"Error analyzing data: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/analysis/<analysis_id>', methods=['GET'])
        async def get_analysis(analysis_id):
            """Get analysis results."""
            logger.info(f"API: Get analysis {analysis_id}")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                analysis = await self.core_engine.get_analysis(analysis_id)
                if analysis:
                    return analysis, 200
                else:
                    return {'error': 'Analysis not found'}, 404
            except Exception as e:
                logger.error(f"Error getting analysis: {str(e)}")
                return {'error': str(e)}, 500
        
        # Digital twin routes
        @app.route('/api/digital-twin/interact', methods=['POST'])
        async def interact_with_twin():
            """Interact with the digital twin."""
            logger.info("API: Interact with digital twin")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                data = await app.request.json()
                input_data = data.get('input')
                input_type = data.get('type', 'message')
                session_id = data.get('session_id', 'default')
                
                result = await self.core_engine.interact_with_twin(input_data, input_type, session_id)
                return result, 200
            except Exception as e:
                logger.error(f"Error interacting with digital twin: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/digital-twin/sessions', methods=['GET'])
        async def get_twin_sessions():
            """Get digital twin sessions."""
            logger.info("API: Get digital twin sessions")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                sessions = await self.core_engine.get_twin_sessions()
                return {'sessions': sessions}, 200
            except Exception as e:
                logger.error(f"Error getting digital twin sessions: {str(e)}")
                return {'error': str(e)}, 500
        
        # Visualization routes
        @app.route('/api/visualization', methods=['POST'])
        async def create_visualization():
            """Create a visualization."""
            logger.info("API: Create visualization")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                data = await app.request.json()
                viz_type = data.get('type', 'auto')
                viz_data = data.get('data')
                options = data.get('options', {})
                
                result = await self.core_engine.create_visualization(viz_data, viz_type, options)
                return result, 200
            except Exception as e:
                logger.error(f"Error creating visualization: {str(e)}")
                return {'error': str(e)}, 500
        
        # Knowledge graph routes
        @app.route('/api/knowledge-graph/entities', methods=['GET'])
        async def get_entities():
            """Get knowledge graph entities."""
            logger.info("API: Get knowledge graph entities")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                filters = app.request.args.get('filters', {})
                limit = int(app.request.args.get('limit', 10))
                
                entities = await self.core_engine.query_entities(filters, limit)
                return {'entities': entities}, 200
            except Exception as e:
                logger.error(f"Error getting knowledge graph entities: {str(e)}")
                return {'error': str(e)}, 500
        
        @app.route('/api/knowledge-graph/relationships', methods=['GET'])
        async def get_relationships():
            """Get knowledge graph relationships."""
            logger.info("API: Get knowledge graph relationships")
            
            if not self.core_engine:
                return {'error': 'Core engine not available'}, 500
            
            try:
                filters = app.request.args.get('filters', {})
                limit = int(app.request.args.get('limit', 10))
                
                relationships = await self.core_engine.query_relationships(filters, limit)
                return {'relationships': relationships}, 200
            except Exception as e:
                logger.error(f"Error getting knowledge graph relationships: {str(e)}")
                return {'error': str(e)}, 500
        
        logger.info("API routes registered")