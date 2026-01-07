"""
Helper functions and mocks for tests.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock

class MockDataPipeline:
    """Mock implementation of DataPipeline for testing."""
    
    def __init__(self):
        self.initialize = AsyncMock()
        self.shutdown = AsyncMock()
        self.process = AsyncMock(return_value={
            "status": "success",
            "processed_data": {"source": "test", "data": "test data"},
            "message": "Data processed successfully"
        })
        
    async def process(self, data_source, data):
        """Process data from a specific source."""
        return {
            "status": "success",
            "processed_data": {"source": data_source, "data": data},
            "message": "Data processed successfully"
        }

class MockCommunicationAnalyzer:
    """Mock implementation of CommunicationAnalyzer for testing."""
    
    def __init__(self):
        pass
        
    async def analyze(self, data):
        """Analyze communication data."""
        return {
            "patterns": [
                {"type": "time_pattern", "description": "Most active between 9am-11am", "confidence": 0.85},
                {"type": "response_pattern", "description": "Quick responses to specific contacts", "confidence": 0.78}
            ],
            "relationships": [
                {"contact": "contact1@example.com", "strength": 0.92, "type": "professional"},
                {"contact": "contact2@example.com", "strength": 0.87, "type": "personal"}
            ]
        }
        
    async def analyze_user(self, user_id, user_data):
        """Analyze communication data for a specific user."""
        return {
            "patterns": [
                {"type": "time_pattern", "description": "Most active between 9am-11am", "confidence": 0.85},
                {"type": "response_pattern", "description": "Quick responses to specific contacts", "confidence": 0.78}
            ],
            "relationships": [
                {"contact": "contact1@example.com", "strength": 0.92, "type": "professional"},
                {"contact": "contact2@example.com", "strength": 0.87, "type": "personal"}
            ]
        }

class MockAdvancedAnalyzer:
    """Mock implementation of AdvancedAnalyzer for testing."""
    
    def __init__(self):
        pass
        
    async def analyze(self, data):
        """Analyze data using advanced techniques."""
        return {
            "topics": [
                {"name": "work", "prevalence": 0.45, "sentiment": 0.2},
                {"name": "family", "prevalence": 0.25, "sentiment": 0.8}
            ],
            "entities": [
                {"name": "Project X", "type": "project", "mentions": 42},
                {"name": "Company Y", "type": "organization", "mentions": 27}
            ]
        }
        
    async def analyze_user(self, user_id, user_data):
        """Analyze data for a specific user using advanced techniques."""
        return {
            "topics": [
                {"name": "work", "prevalence": 0.45, "sentiment": 0.2},
                {"name": "family", "prevalence": 0.25, "sentiment": 0.8}
            ],
            "entities": [
                {"name": "Project X", "type": "project", "mentions": 42},
                {"name": "Company Y", "type": "organization", "mentions": 27}
            ]
        }

class MockCognitiveAnalyzer:
    """Mock implementation of CognitiveAnalyzer for testing."""
    
    def __init__(self):
        pass
        
    async def analyze(self, data):
        """Analyze data using cognitive techniques."""
        return {
            "personality": {
                "openness": 0.75,
                "conscientiousness": 0.82,
                "extraversion": 0.45,
                "agreeableness": 0.68,
                "neuroticism": 0.32
            },
            "values": {
                "achievement": 0.85,
                "benevolence": 0.72,
                "self_direction": 0.78,
                "security": 0.65
            }
        }
        
    async def analyze_user(self, user_id, user_data):
        """Analyze data for a specific user using cognitive techniques."""
        return {
            "personality": {
                "openness": 0.75,
                "conscientiousness": 0.82,
                "extraversion": 0.45,
                "agreeableness": 0.68,
                "neuroticism": 0.32
            },
            "values": {
                "achievement": 0.85,
                "benevolence": 0.72,
                "self_direction": 0.78,
                "security": 0.65
            }
        }

class MockKnowledgeGraphBuilder:
    """Mock implementation of KnowledgeGraphBuilder for testing."""
    
    def __init__(self):
        pass
        
    async def update_graph(self, data, analysis_results):
        """Update the knowledge graph with new data."""
        return {
            "success": True,
            "nodes_added": 5,
            "relationships_added": 8,
            "message": "Graph updated successfully"
        }

class MockCognitiveTwin:
    """Mock implementation of CognitiveTwin for testing."""
    
    def __init__(self):
        self.initialized = False
        
    async def initialize(self):
        """Initialize the cognitive twin."""
        self.initialized = True
        return True
        
    async def shutdown(self):
        """Shutdown the cognitive twin."""
        self.initialized = False
        return True
        
    async def update(self, data, analysis_results):
        """Update the cognitive twin with new data."""
        return {
            "success": True,
            "personality_updated": True,
            "memory_updated": True,
            "message": "Cognitive twin updated successfully"
        }