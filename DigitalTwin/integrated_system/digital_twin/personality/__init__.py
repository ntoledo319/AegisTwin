"""
Personality module for the digital twin.

This module provides personality modeling capabilities for the digital twin,
including trait analysis, behavior generation, and personality adaptation.
"""

import logging
from typing import Dict, List, Any, Optional
from .engine import PersonalityEngine
from .model import PersonalityModel

logger = logging.getLogger(__name__)

class PersonalityManager:
    """Manager for digital twin personality components."""
    
    def __init__(self):
        """Initialize the personality manager."""
        self.engine = PersonalityEngine()
        self.model = PersonalityModel()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the personality manager."""
        logger.info("Initializing personality manager")
        
        # Initialize engine
        await self.engine.initialize()
        
        # Initialize model
        await self.model.initialize()
        
        self.initialized = True
        logger.info("Personality manager initialized")
    
    async def analyze_personality(self, data: Any) -> Dict[str, Any]:
        """
        Analyze personality from data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Dictionary of personality analysis results
        """
        logger.info("Analyzing personality from data")
        
        if not self.initialized:
            await self.initialize()
        
        # Use engine to analyze personality
        personality_traits = await self.engine.analyze_personality(data)
        
        # Update model with new traits
        await self.model.update(traits=personality_traits, data=data)
        
        return {
            'traits': self.model.traits,
            'facets': self.model.facets,
            'values': self.model.values,
            'interests': self.model.interests
        }
    
    async def generate_response(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate personality-driven response.
        
        Args:
            input_data: Input data to respond to
            context: Additional context (optional)
            
        Returns:
            Dictionary containing response and metadata
        """
        logger.info("Generating personality-driven response")
        
        if not self.initialized:
            await self.initialize()
        
        # Use engine to generate response
        response = await self.engine.generate_response(input_data, context)
        
        return response
    
    async def adapt_personality(self, feedback: Any) -> Dict[str, Any]:
        """
        Adapt personality based on feedback.
        
        Args:
            feedback: Feedback data
            
        Returns:
            Dictionary of adaptation results
        """
        logger.info("Adapting personality based on feedback")
        
        if not self.initialized:
            await self.initialize()
        
        # Use engine to adapt personality
        adaptation_results = await self.engine.adapt_personality(feedback)
        
        # Update model with adaptation results
        await self.model.update(traits=adaptation_results.get('traits'))
        
        return {
            'previous_traits': adaptation_results.get('previous_traits'),
            'current_traits': self.model.traits,
            'changes': adaptation_results.get('changes')
        }
    
    async def get_personality_profile(self) -> Dict[str, Any]:
        """
        Get the current personality profile.
        
        Returns:
            Dictionary containing the personality profile
        """
        logger.info("Getting personality profile")
        
        if not self.initialized:
            await self.initialize()
        
        return {
            'traits': self.model.traits,
            'facets': self.model.facets,
            'values': self.model.values,
            'interests': self.model.interests,
            'communication_style': self.engine.communication_style,
            'decision_style': self.engine.decision_style,
            'interaction_style': self.engine.interaction_style
        }