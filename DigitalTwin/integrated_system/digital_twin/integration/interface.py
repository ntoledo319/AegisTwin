"""
Digital twin interface module.

This module provides the main interface for interacting with the digital twin,
coordinating between the cognitive twin and external systems.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class DigitalTwinInterface:
    """Interface for interacting with the digital twin."""
    
    def __init__(self, cognitive_twin=None):
        """
        Initialize the digital twin interface.
        
        Args:
            cognitive_twin: Cognitive twin instance
        """
        self.cognitive_twin = cognitive_twin
        self.session_data = {}
        self.interaction_history = []
        self.max_history_length = 100
        self.initialized = False
        self.interface_path = "data/interface_data.json"
    
    async def initialize(self):
        """Initialize the digital twin interface."""
        logger.info("Initializing digital twin interface")
        
        # Initialize cognitive twin if provided
        if self.cognitive_twin:
            await self.cognitive_twin.initialize()
        
        # Try to load interface data from file
        if await self._load_interface_data():
            logger.info("Loaded interface data from file")
        else:
            logger.info("Starting with empty interface data")
        
        self.initialized = True
        logger.info("Digital twin interface initialized")
    
    async def _load_interface_data(self) -> bool:
        """
        Load interface data from file.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.interface_path):
                with open(self.interface_path, 'r') as f:
                    interface_data = json.load(f)
                
                # Load interaction history
                if 'interaction_history' in interface_data:
                    self.interaction_history = interface_data['interaction_history']
                
                # Load session data
                if 'session_data' in interface_data:
                    self.session_data = interface_data['session_data']
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading interface data: {str(e)}")
            return False
    
    async def _save_interface_data(self):
        """Save interface data to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.interface_path), exist_ok=True)
            
            # Create interface data
            interface_data = {
                'interaction_history': self.interaction_history[-self.max_history_length:],
                'session_data': self.session_data,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.interface_path, 'w') as f:
                json.dump(interface_data, f, indent=2)
            
            logger.info("Saved interface data to file")
            return True
        except Exception as e:
            logger.error(f"Error saving interface data: {str(e)}")
            return False
    
    async def interact(self, input_data: Any, input_type: str = 'message', 
                      session_id: str = 'default') -> Dict[str, Any]:
        """
        Interact with the digital twin.
        
        Args:
            input_data: Input data
            input_type: Type of input (message, event, feedback, etc.)
            session_id: Session identifier
            
        Returns:
            Dictionary containing the response
        """
        logger.info(f"Processing {input_type} interaction in session {session_id}")
        
        if not self.initialized:
            await self.initialize()
        
        # Create interaction record
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'input_type': input_type,
            'input_data': input_data if isinstance(input_data, (str, int, float, bool)) else "complex_data"
        }
        
        # Update session data
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'interaction_count': 0
            }
        
        self.session_data[session_id]['last_active'] = datetime.now().isoformat()
        self.session_data[session_id]['interaction_count'] += 1
        
        # Process with cognitive twin if available
        response = None
        if self.cognitive_twin:
            response = await self.cognitive_twin.process_input(input_data, input_type)
        else:
            response = {'error': "Cognitive twin not available"}
        
        # Add response to interaction record
        interaction['response'] = response if isinstance(response, (str, int, float, bool)) else "complex_data"
        
        # Add to interaction history
        self.interaction_history.append(interaction)
        
        # Save interface data
        await self._save_interface_data()
        
        return response
    
    async def get_session_data(self, session_id: str = 'default') -> Dict[str, Any]:
        """
        Get data for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session data
        """
        logger.info(f"Getting data for session {session_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if session_id in self.session_data:
            return self.session_data[session_id]
        else:
            return {'error': f"Session {session_id} not found"}
    
    async def get_twin_state(self) -> Dict[str, Any]:
        """
        Get the current state of the digital twin.
        
        Returns:
            Dictionary containing the twin state
        """
        logger.info("Getting digital twin state")
        
        if not self.initialized:
            await self.initialize()
        
        # Get cognitive state if available
        cognitive_state = {}
        if self.cognitive_twin:
            cognitive_state = await self.cognitive_twin.get_cognitive_state()
        
        # Get interface state
        interface_state = {
            'active_sessions': len(self.session_data),
            'total_interactions': sum(session['interaction_count'] for session in self.session_data.values()),
            'last_interaction': self.interaction_history[-1]['timestamp'] if self.interaction_history else None
        }
        
        # Combine states
        state = {
            'cognitive': cognitive_state,
            'interface': interface_state
        }
        
        return state
    
    async def create_session(self, session_id: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new interaction session.
        
        Args:
            session_id: Session identifier (optional, will be generated if not provided)
            metadata: Additional session metadata
            
        Returns:
            Dictionary containing session information
        """
        logger.info("Creating new interaction session")
        
        if not self.initialized:
            await self.initialize()
        
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Check if session already exists
        if session_id in self.session_data:
            return {'error': f"Session {session_id} already exists"}
        
        # Create session data
        self.session_data[session_id] = {
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'interaction_count': 0
        }
        
        # Add metadata if provided
        if metadata:
            self.session_data[session_id]['metadata'] = metadata
        
        # Save interface data
        await self._save_interface_data()
        
        return {
            'session_id': session_id,
            'created_at': self.session_data[session_id]['created_at']
        }
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End an interaction session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session summary
        """
        logger.info(f"Ending session {session_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if session_id not in self.session_data:
            return {'error': f"Session {session_id} not found"}
        
        # Get session data
        session_data = self.session_data[session_id].copy()
        
        # Add end timestamp
        session_data['ended_at'] = datetime.now().isoformat()
        
        # Calculate duration
        try:
            start_time = datetime.fromisoformat(session_data['created_at'])
            end_time = datetime.fromisoformat(session_data['ended_at'])
            duration = (end_time - start_time).total_seconds()
            session_data['duration_seconds'] = duration
        except:
            session_data['duration_seconds'] = 0
        
        # Remove session from active sessions
        del self.session_data[session_id]
        
        # Save interface data
        await self._save_interface_data()
        
        return {
            'session_id': session_id,
            'summary': session_data
        }
    
    async def maintenance(self):
        """Perform maintenance tasks."""
        logger.info("Performing digital twin interface maintenance")
        
        if not self.initialized:
            await self.initialize()
        
        # Perform cognitive twin maintenance if available
        if self.cognitive_twin:
            await self.cognitive_twin.maintenance()
        
        # Clean up old sessions
        now = datetime.now()
        for session_id, session_data in list(self.session_data.items()):
            try:
                last_active = datetime.fromisoformat(session_data['last_active'])
                days_inactive = (now - last_active).days
                
                # End sessions inactive for more than 7 days
                if days_inactive > 7:
                    await self.end_session(session_id)
            except:
                pass
        
        # Trim interaction history if needed
        if len(self.interaction_history) > self.max_history_length:
            self.interaction_history = self.interaction_history[-self.max_history_length:]
        
        # Save interface data
        await self._save_interface_data()
        
        logger.info("Digital twin interface maintenance complete")