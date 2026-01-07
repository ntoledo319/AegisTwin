"""
Unit tests for the EntanglementMatrix adapter.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from digital_twin.adapters.entanglement_matrix import EntanglementMatrixAdapter


@pytest.fixture
def entanglement_matrix_adapter():
    """Create an EntanglementMatrix adapter for testing."""
    return EntanglementMatrixAdapter()


@pytest.fixture
def sample_user_data():
    """Create sample user data for testing."""
    # Create timestamps
    now = datetime.now()
    timestamps = [
        (now - timedelta(days=10)).isoformat(),
        (now - timedelta(days=8)).isoformat(),
        (now - timedelta(days=6)).isoformat(),
        (now - timedelta(days=4)).isoformat(),
        (now - timedelta(days=2)).isoformat(),
        now.isoformat(),
    ]
    
    # Create sample data
    return {
        "communication": [
            {"timestamp": timestamps[0], "message_count": 10, "response_time": 30},
            {"timestamp": timestamps[1], "message_count": 15, "response_time": 25},
            {"timestamp": timestamps[2], "message_count": 5, "response_time": 40},
            {"timestamp": timestamps[3], "message_count": 20, "response_time": 20},
            {"timestamp": timestamps[4], "message_count": 12, "response_time": 35},
            {"timestamp": timestamps[5], "message_count": 18, "response_time": 15},
        ],
        "activity": [
            {"timestamp": timestamps[0], "activity_level": 0.3, "duration": 45},
            {"timestamp": timestamps[1], "activity_level": 0.5, "duration": 60},
            {"timestamp": timestamps[2], "activity_level": 0.2, "duration": 30},
            {"timestamp": timestamps[3], "activity_level": 0.8, "duration": 90},
            {"timestamp": timestamps[4], "activity_level": 0.4, "duration": 50},
            {"timestamp": timestamps[5], "activity_level": 0.7, "duration": 75},
        ],
        "mood": [
            {"timestamp": timestamps[0], "happiness": 0.6, "energy": 0.4},
            {"timestamp": timestamps[1], "happiness": 0.7, "energy": 0.6},
            {"timestamp": timestamps[2], "happiness": 0.5, "energy": 0.3},
            {"timestamp": timestamps[3], "happiness": 0.8, "energy": 0.7},
            {"timestamp": timestamps[4], "happiness": 0.6, "energy": 0.5},
            {"timestamp": timestamps[5], "happiness": 0.9, "energy": 0.8},
        ],
    }


@pytest.fixture
def sample_personality_dimensions():
    """Create sample personality dimensions for testing."""
    return {
        "openness": 0.8,
        "conscientiousness": 0.6,
        "extraversion": 0.7,
        "agreeableness": 0.9,
        "neuroticism": 0.3,
    }


@pytest.mark.asyncio
async def test_analyze_entanglements(entanglement_matrix_adapter, sample_user_data):
    """Test analyze_entanglements method."""
    # Call the method
    result = await entanglement_matrix_adapter.analyze_entanglements(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "network_density" in result
    assert "entanglement_count" in result
    assert "node_count" in result
    assert "insights" in result
    
    # Check that the network density is reasonable
    assert 0 <= result["network_density"] <= 1
    
    # Check that the node count matches the number of categories
    assert result["node_count"] == len(sample_user_data)


@pytest.mark.asyncio
async def test_detect_relationship_patterns(entanglement_matrix_adapter, sample_user_data):
    """Test detect_relationship_patterns method."""
    # Call the method
    result = await entanglement_matrix_adapter.detect_relationship_patterns(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that each pattern has the expected fields
    for pattern in result:
        assert "pattern_id" in pattern
        assert "source" in pattern
        assert "target" in pattern
        assert "relationship_type" in pattern
        assert "strength" in pattern
        assert "description" in pattern
        
        # Check that the strength is reasonable
        assert 0 <= pattern["strength"] <= 1
        
        # Check that source and target are from the original data
        assert pattern["source"] in sample_user_data or pattern["source"].replace("entity_", "") in sample_user_data
        assert pattern["target"] in sample_user_data or pattern["target"].replace("entity_", "") in sample_user_data


@pytest.mark.asyncio
async def test_visualize_entanglement_network(entanglement_matrix_adapter, sample_user_data):
    """Test visualize_entanglement_network method."""
    # Call the method
    result = await entanglement_matrix_adapter.visualize_entanglement_network(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "nodes" in result
    assert "links" in result
    assert "metadata" in result
    
    # Check that nodes and links are lists
    assert isinstance(result["nodes"], list)
    assert isinstance(result["links"], list)
    
    # Check that each node has the expected fields
    for node in result["nodes"]:
        assert "id" in node
        assert "label" in node
        assert "type" in node
        assert "influence" in node
        
        # Check that the influence is reasonable
        assert 0 <= node["influence"] <= 1
    
    # Check that each link has the expected fields
    for link in result["links"]:
        assert "source" in link
        assert "target" in link
        assert "type" in link
        assert "strength" in link
        
        # Check that the strength is reasonable
        assert 0 <= link["strength"] <= 1


@pytest.mark.asyncio
async def test_analyze_dimension_entanglements(entanglement_matrix_adapter, sample_personality_dimensions):
    """Test analyze_dimension_entanglements method."""
    # Call the method
    result = await entanglement_matrix_adapter.analyze_dimension_entanglements(sample_personality_dimensions)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "dimension_pairs" in result
    assert "metrics" in result
    assert "insights" in result
    
    # Check that dimension_pairs is a list
    assert isinstance(result["dimension_pairs"], list)
    
    # Check that each dimension pair has the expected fields
    for pair in result["dimension_pairs"]:
        assert "dimensions" in pair
        assert "entanglement_type" in pair
        assert "strength" in pair
        assert "description" in pair
        
        # Check that the strength is reasonable
        assert 0 <= pair["strength"] <= 1
        
        # Check that dimensions are from the original data
        assert pair["dimensions"][0] in sample_personality_dimensions
        assert pair["dimensions"][1] in sample_personality_dimensions
    
    # Check that metrics has the expected fields
    assert "average_entanglement_strength" in result["metrics"]
    assert "maximum_entanglement_strength" in result["metrics"]
    assert "minimum_entanglement_strength" in result["metrics"]
    assert "entanglement_count" in result["metrics"]
    
    # Check that insights is a list
    assert isinstance(result["insights"], list)


@pytest.mark.asyncio
async def test_strength_description(entanglement_matrix_adapter):
    """Test _strength_description method."""
    # Test different strength values
    assert entanglement_matrix_adapter._strength_description(0.95) == "extremely strong"
    assert entanglement_matrix_adapter._strength_description(0.8) == "strong"
    assert entanglement_matrix_adapter._strength_description(0.5) == "moderate"
    assert entanglement_matrix_adapter._strength_description(0.2) == "weak"
    assert entanglement_matrix_adapter._strength_description(0.05) == "very weak"


@pytest.mark.asyncio
async def test_convert_to_consciousness_data(entanglement_matrix_adapter, sample_user_data):
    """Test _convert_to_consciousness_data method."""
    # Call the method
    result = entanglement_matrix_adapter._convert_to_consciousness_data(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    
    # Check that each category is converted to an entity
    for category in sample_user_data:
        entity_id = f"entity_{category}"
        assert entity_id in result
        assert isinstance(result[entity_id], list)
        assert len(result[entity_id]) == len(sample_user_data[category])
        
        # Check that each data point is converted to a consciousness state
        for i, state in enumerate(result[entity_id]):
            assert "timestamp" in state
            assert "values" in state
            assert "metadata" in state
            assert "source" in state["metadata"]
            assert state["metadata"]["source"] == category


@pytest.mark.asyncio
async def test_basic_entanglement_analysis(entanglement_matrix_adapter, sample_user_data):
    """Test _basic_entanglement_analysis method."""
    # Call the method
    result = entanglement_matrix_adapter._basic_entanglement_analysis(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "network_density" in result
    assert "entanglement_count" in result
    assert "node_count" in result
    assert "insights" in result
    
    # Check that the network density is reasonable
    assert 0 <= result["network_density"] <= 1
    
    # Check that the node count matches the number of categories
    assert result["node_count"] == len(sample_user_data)


@pytest.mark.asyncio
async def test_basic_relationship_pattern_detection(entanglement_matrix_adapter, sample_user_data):
    """Test _basic_relationship_pattern_detection method."""
    # Call the method
    result = entanglement_matrix_adapter._basic_relationship_pattern_detection(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that each pattern has the expected fields
    for pattern in result:
        assert "pattern_id" in pattern
        assert "source" in pattern
        assert "target" in pattern
        assert "relationship_type" in pattern
        assert "strength" in pattern
        assert "description" in pattern
        
        # Check that the strength is reasonable
        assert 0 <= pattern["strength"] <= 1
        
        # Check that source and target are from the original data
        assert pattern["source"] in sample_user_data
        assert pattern["target"] in sample_user_data


@pytest.mark.asyncio
async def test_basic_dimension_entanglement_analysis(entanglement_matrix_adapter, sample_personality_dimensions):
    """Test _basic_dimension_entanglement_analysis method."""
    # Call the method
    result = entanglement_matrix_adapter._basic_dimension_entanglement_analysis(sample_personality_dimensions)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "dimension_pairs" in result
    assert "metrics" in result
    assert "insights" in result
    
    # Check that dimension_pairs is a list
    assert isinstance(result["dimension_pairs"], list)
    
    # Check that metrics has the expected fields
    assert "average_entanglement_strength" in result["metrics"]
    assert "maximum_entanglement_strength" in result["metrics"]
    assert "minimum_entanglement_strength" in result["metrics"]
    assert "entanglement_count" in result["metrics"]