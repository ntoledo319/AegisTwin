"""
Analysis package for the integrated system.

This package provides comprehensive analysis capabilities, including:
- Communication analysis: patterns, relationships, and topics
- Advanced analysis: NLP, temporal, and network analysis
- Cognitive analysis: personality, values, decision-making, and memory
"""

import logging
from typing import Dict, List, Any, Optional
from .communication import CommunicationAnalyzer
from .advanced import AdvancedAnalyzer
from .cognitive import CognitiveAnalyzer

logger = logging.getLogger(__name__)

class AnalysisManager:
    """Manager for all analysis components."""
    
    def __init__(self):
        """Initialize the analysis manager."""
        self.communication_analyzer = CommunicationAnalyzer()
        self.advanced_analyzer = AdvancedAnalyzer()
        self.cognitive_analyzer = CognitiveAnalyzer()
        self.analysis_results = {}
    
    async def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Analyze data using all available analyzers.
        
        Args:
            data: Data to analyze
            
        Returns:
            Dictionary of analysis results
        """
        logger.info("Starting comprehensive analysis")
        
        # Analyze communication patterns
        communication_results = await self.communication_analyzer.analyze(data)
        
        # Analyze with advanced techniques
        advanced_results = await self.advanced_analyzer.analyze(data, communication_results)
        
        # Analyze with cognitive techniques
        cognitive_results = await self.cognitive_analyzer.analyze(data, communication_results, advanced_results)
        
        # Combine results
        results = {
            "communication": communication_results,
            "advanced": advanced_results,
            "cognitive": cognitive_results
        }
        
        # Store results
        self.analysis_results = results
        
        logger.info("Comprehensive analysis complete")
        return results
    
    async def generate_insights(self, data: Any) -> List[Dict[str, Any]]:
        """
        Generate insights from all analysis components.
        
        Args:
            data: Data for analysis
            
        Returns:
            List of insights
        """
        logger.info("Generating comprehensive insights")
        
        # Analyze data if not already analyzed
        if not self.analysis_results:
            await self.analyze(data)
        
        insights = []
        
        # Generate communication insights
        communication_insights = await self.communication_analyzer.generate_insights(data)
        for insight in communication_insights:
            insight['source'] = 'communication'
        insights.extend(communication_insights)
        
        # Generate advanced insights
        advanced_insights = await self.advanced_analyzer.generate_insights(data)
        for insight in advanced_insights:
            insight['source'] = 'advanced'
        insights.extend(advanced_insights)
        
        # Generate cognitive insights
        cognitive_insights = await self.cognitive_analyzer.generate_insights(data)
        for insight in cognitive_insights:
            insight['source'] = 'cognitive'
        insights.extend(cognitive_insights)
        
        # Sort insights by score (higher is more important)
        sorted_insights = sorted(insights, key=lambda x: x.get('score', 0), reverse=True)
        
        # Limit to top insights to avoid overwhelming the user
        top_insights = sorted_insights[:20]
        
        logger.info(f"Generated {len(top_insights)} top insights from {len(sorted_insights)} total")
        return top_insights