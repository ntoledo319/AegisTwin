"""
Unit tests for the VoidAnalyzer adapter.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from digital_twin.adapters.void_analyzer import VoidAnalyzerAdapter


@pytest.fixture
def void_analyzer_adapter():
    """Create a VoidAnalyzer adapter for testing."""
    return VoidAnalyzerAdapter()


@pytest.fixture
def sample_user_data():
    """Create sample user data for testing."""
    # Create timestamps
    now = datetime.now()
    timestamps = [
        (now - timedelta(days=20)).isoformat(),
        (now - timedelta(days=15)).isoformat(),
        (now - timedelta(days=10)).isoformat(),
        (now - timedelta(days=5)).isoformat(),
        now.isoformat(),
    ]
    
    # Create sample data with a gap between days 15 and 10
    return {
        "communication": [
            {"timestamp": timestamps[0], "message_count": 10, "response_time": 30},
            {"timestamp": timestamps[1], "message_count": 15, "response_time": 25},
            # Gap here
            {"timestamp": timestamps[3], "message_count": 20, "response_time": 20},
            {"timestamp": timestamps[4], "message_count": 18, "response_time": 15},
        ],
        "activity": [
            {"timestamp": timestamps[0], "activity_level": 0.3, "duration": 45},
            {"timestamp": timestamps[1], "activity_level": 0.5, "duration": 60},
            {"timestamp": timestamps[2], "activity_level": 0.2, "duration": 30},
            {"timestamp": timestamps[3], "activity_level": 0.8, "duration": 90},
            {"timestamp": timestamps[4], "activity_level": 0.7, "duration": 75},
        ],
        "mood": [
            {"timestamp": timestamps[0], "happiness": 0.6, "energy": 0.4},
            {"timestamp": timestamps[1], "happiness": 0.7, "energy": 0.6},
            # Gap here
            {"timestamp": timestamps[3], "happiness": 0.8, "energy": 0.7},
            {"timestamp": timestamps[4], "happiness": 0.9, "energy": 0.8},
        ],
        # Missing "social" category
    }


@pytest.fixture
def sample_user_profile():
    """Create sample user profile for testing."""
    return {
        "personality": {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
        },
        "preferences": {
            "music": 0.8,
            "movies": 0.7,
        },
        # Missing "demographics" section
        "interests": {
            "technology": 0.9,
            "science": 0.8,
            "art": 0.6,
        },
    }


@pytest.mark.asyncio
async def test_analyze_understanding_gaps(void_analyzer_adapter, sample_user_data):
    """Test analyze_understanding_gaps method."""
    # Call the method
    result = await void_analyzer_adapter.analyze_understanding_gaps(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "detected_voids" in result
    assert "insights" in result
    assert "recommendations" in result
    
    # Check that voids were detected
    assert len(result["detected_voids"]) > 0
    
    # Check that insights were generated
    assert len(result["insights"]) > 0
    
    # Check that recommendations were generated
    assert len(result["recommendations"]) > 0
    
    # Check that at least one temporal void was detected (due to the gap)
    temporal_voids = [v for v in result["detected_voids"] if v["type"] == "temporal"]
    assert len(temporal_voids) > 0
    
    # Check that a missing category void was detected (for "social")
    awareness_voids = [v for v in result["detected_voids"] if v["type"] == "awareness"]
    assert len(awareness_voids) > 0


@pytest.mark.asyncio
async def test_detect_knowledge_gaps(void_analyzer_adapter, sample_user_profile):
    """Test detect_knowledge_gaps method."""
    # Call the method
    result = await void_analyzer_adapter.detect_knowledge_gaps(sample_user_profile)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that gaps were detected
    assert len(result) > 0
    
    # Check that each gap has the expected fields
    for gap in result:
        assert "id" in gap
        assert "type" in gap
        assert "severity" in gap
        assert "confidence" in gap
        assert "affected_dimensions" in gap
        assert "potential_causes" in gap
        assert "recovery_suggestions" in gap
    
    # Check that a gap for missing "demographics" was detected
    demographics_gaps = [g for g in result if "demographics" in g.get("affected_dimensions", [])]
    assert len(demographics_gaps) > 0


@pytest.mark.asyncio
async def test_generate_void_recovery_recommendations(void_analyzer_adapter):
    """Test generate_void_recovery_recommendations method."""
    # Create sample gaps
    gaps = [
        {
            "id": "gap1",
            "type": "temporal",
            "severity": 0.7,
            "confidence": 0.8,
            "discovered_at": datetime.now().isoformat(),
            "time_span": {
                "start_time": (datetime.now() - timedelta(days=10)).isoformat(),
                "end_time": (datetime.now() - timedelta(days=5)).isoformat()
            },
            "affected_dimensions": ["communication"],
            "potential_causes": ["Data collection gap"],
            "recovery_suggestions": ["Collect additional data"]
        },
        {
            "id": "gap2",
            "type": "awareness",
            "severity": 0.6,
            "confidence": 0.9,
            "discovered_at": datetime.now().isoformat(),
            "time_span": {
                "start_time": "",
                "end_time": ""
            },
            "affected_dimensions": ["social"],
            "potential_causes": ["No data collected"],
            "recovery_suggestions": ["Start collecting social data"]
        }
    ]
    
    # Call the method
    result = await void_analyzer_adapter.generate_void_recovery_recommendations(gaps)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "recovery_plans" in result
    assert "summary" in result
    assert "recommendations" in result
    
    # Check that recovery plans were generated
    assert len(result["recovery_plans"]) > 0
    
    # Check that recommendations were generated
    assert len(result["recommendations"]) > 0
    
    # Check that the summary has the expected fields
    assert "plan_count" in result["summary"]
    assert "average_success_probability" in result["summary"]
    assert "average_duration" in result["summary"]
    
    # Check that the plan count matches the number of input gaps
    assert result["summary"]["plan_count"] == len(gaps)


@pytest.mark.asyncio
async def test_convert_user_data_to_consciousness_states(void_analyzer_adapter, sample_user_data):
    """Test _convert_user_data_to_consciousness_states method."""
    # Call the method
    result = void_analyzer_adapter._convert_user_data_to_consciousness_states(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that states were created for each data point
    expected_count = sum(len(data_points) for data_points in sample_user_data.values())
    assert len(result) == expected_count
    
    # Check that each state has the expected fields
    for state in result:
        assert "timestamp" in state
        assert "category" in state
        assert "data" in state
        assert "dimensions" in state
        assert isinstance(state["dimensions"], dict)


@pytest.mark.asyncio
async def test_basic_void_analysis(void_analyzer_adapter, sample_user_data):
    """Test _basic_void_analysis method."""
    # Call the method
    result = void_analyzer_adapter._basic_void_analysis(sample_user_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "detected_voids" in result
    assert "insights" in result
    assert "recommendations" in result
    
    # Check that voids were detected
    assert len(result["detected_voids"]) > 0
    
    # Check that insights were generated
    assert len(result["insights"]) > 0
    
    # Check that recommendations were generated
    assert len(result["recommendations"]) > 0