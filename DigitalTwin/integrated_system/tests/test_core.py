"""
Tests for the core components of the integrated system.
"""

import os
import sys
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config
from core.engine import Engine
from tests.test_helpers import (
    MockDataPipeline,
    MockCommunicationAnalyzer,
    MockAdvancedAnalyzer,
    MockCognitiveAnalyzer,
    MockKnowledgeGraphBuilder,
    MockCognitiveTwin
)

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def engine():
    """Create an instance of the Engine for testing."""
    # Create engine instance
    engine_instance = Engine()
    
    # Replace components with mocks
    engine_instance.data_pipeline = MockDataPipeline()
    engine_instance.communication_analyzer = MockCommunicationAnalyzer()
    engine_instance.advanced_analyzer = MockAdvancedAnalyzer()
    engine_instance.cognitive_analyzer = MockCognitiveAnalyzer()
    engine_instance.knowledge_graph_builder = MockKnowledgeGraphBuilder()
    engine_instance.cognitive_twin = MockCognitiveTwin()
    
    yield engine_instance
    
    # No need to call shutdown as we're using mocks

@pytest.mark.asyncio
async def test_config_loading():
    """Test that configuration is loaded correctly."""
    # Check that config is a singleton instance
    assert config is not None
    
    # Check that some basic configuration values are loaded
    assert config.get("app.name") is not None
    assert config.get("server.host") is not None
    assert config.get("server.port") is not None
    
    # Check that environment-specific configuration is loaded
    assert config.get("app.environment") is not None

@pytest.mark.asyncio
async def test_engine_initialization(engine):
    """Test that the engine initializes correctly."""
    # Check that engine is initialized
    assert engine is not None
    
    # The engine should have these attributes even if they're not fully implemented yet
    # Check that the attributes exist, even if they're None
    assert hasattr(engine, "data_pipeline") is True
    assert hasattr(engine, "communication_analyzer") is True
    assert hasattr(engine, "advanced_analyzer") is True
    assert hasattr(engine, "cognitive_analyzer") is True
    assert hasattr(engine, "knowledge_graph_builder") is True
    assert hasattr(engine, "cognitive_twin") is True

@pytest.mark.asyncio
async def test_process_data(engine):
    """Test that the engine can process data."""
    # Process some test data
    result = await engine.process_data("test", "Test data")
    
    # Check that the result has the expected structure
    assert result is not None
    assert "status" in result
    assert result["status"] == "success"
    assert "processed_data" in result
    assert "analysis_results" in result
    assert "knowledge_graph_updated" in result
    assert "cognitive_twin_updated" in result

@pytest.mark.asyncio
async def test_analyze_data(engine):
    """Test that the engine can analyze data."""
    # Analyze data for a test user
    result = await engine.analyze_data("test_user")
    
    # Check that the result has the expected structure
    assert result is not None
    assert "communication" in result
    assert "patterns" in result["communication"]
    assert "relationships" in result["communication"]
    assert "advanced" in result
    assert "topics" in result["advanced"]
    assert "entities" in result["advanced"]
    assert "cognitive" in result
    assert "personality" in result["cognitive"]
    assert "values" in result["cognitive"]

@pytest.mark.asyncio
async def test_generate_insights(engine):
    """Test that the engine can generate insights."""
    # Generate insights for a test user
    insights = await engine.generate_insights("test_user")
    
    # Check that insights have the expected structure
    assert insights is not None
    assert len(insights) > 0
    assert "id" in insights[0]
    assert "title" in insights[0]
    assert "description" in insights[0]
    assert "category" in insights[0]
    assert "score" in insights[0]