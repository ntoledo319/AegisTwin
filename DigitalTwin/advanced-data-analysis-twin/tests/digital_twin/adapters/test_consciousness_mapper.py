"""
Unit tests for the Enhanced ConsciousnessMapper adapter.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from digital_twin.adapters.consciousness_mapper import EnhancedConsciousnessMapperAdapter


@pytest.fixture
def consciousness_mapper_adapter():
    """Create an Enhanced ConsciousnessMapper adapter for testing."""
    return EnhancedConsciousnessMapperAdapter()


@pytest.fixture
def sample_consciousness_data():
    """Create sample consciousness data for testing."""
    # Create timestamps
    now = datetime.now()
    data = []
    
    # Generate 10 data points
    for i in range(10):
        timestamp = (now - timedelta(days=10-i)).isoformat()
        
        # Create a data point with dimensions
        data_point = {
            "timestamp": timestamp,
            "dimensions": {
                "happiness": 0.5 + (i * 0.05),
                "energy": 0.6 - (i * 0.02),
                "focus": 0.7 + (0.1 * ((i % 5) / 5)),
                "creativity": 0.4 + (i * 0.03),
                "anxiety": 0.3 - (i * 0.01)
            },
            "patterns": [
                f"pattern_{i % 3}",
                f"pattern_{(i+1) % 4}"
            ],
            "transitions": [
                f"transition_{i-1}_{i}" if i > 0 else ""
            ]
        }
        
        data.append(data_point)
    
    return data


@pytest.fixture
def sample_personality_data():
    """Create sample personality data for testing."""
    return {
        "traits": {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
            "creativity": 0.8,
            "resilience": 0.7,
            "adaptability": 0.6,
            "empathy": 0.9,
            "curiosity": 0.8
        },
        "states": [
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "dimensions": {
                    "mood": 0.7,
                    "energy": 0.6,
                    "focus": 0.5
                },
                "patterns": ["morning_routine", "work_focus"],
                "transitions": ["sleep_to_wake"]
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "dimensions": {
                    "mood": 0.6,
                    "energy": 0.5,
                    "focus": 0.7
                },
                "patterns": ["problem_solving", "creative_flow"],
                "transitions": ["work_to_rest"]
            },
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "dimensions": {
                    "mood": 0.8,
                    "energy": 0.7,
                    "focus": 0.6
                },
                "patterns": ["social_engagement", "relaxation"],
                "transitions": ["work_to_play"]
            }
        ]
    }


@pytest.mark.asyncio
async def test_map_consciousness_topology(consciousness_mapper_adapter, sample_consciousness_data):
    """Test map_consciousness_topology method."""
    # Call the method
    result = await consciousness_mapper_adapter.map_consciousness_topology(sample_consciousness_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "map_id" in result
    assert "regions" in result
    assert "transitions" in result
    assert "dominant_topologies" in result
    assert "metrics" in result
    assert "insights" in result
    
    # Check that regions were created
    assert len(result["regions"]) > 0
    
    # Check that each region has the expected fields
    for region in result["regions"]:
        assert "region_id" in region
        assert "topology_type" in region
        assert "dimensions" in region
        assert "stability" in region
        assert "accessibility" in region
        assert "neighboring_regions" in region
        
    # Check that transitions were created
    assert "direct_transitions" in result["transitions"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_analyze_consciousness_structure(consciousness_mapper_adapter, sample_personality_data):
    """Test analyze_consciousness_structure method."""
    # Call the method
    result = await consciousness_mapper_adapter.analyze_consciousness_structure(sample_personality_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "analysis_id" in result
    assert "layers" in result
    assert "core_elements" in result
    assert "peripheral_elements" in result
    assert "structural_metrics" in result
    assert "insights" in result
    
    # Check that layers were created
    assert len(result["layers"]) > 0
    
    # Check that core elements were identified
    assert len(result["core_elements"]) > 0
    
    # Check that peripheral elements were identified
    assert len(result["peripheral_elements"]) > 0
    
    # Check that structural metrics were calculated
    assert "coherence" in result["structural_metrics"]
    assert "complexity" in result["structural_metrics"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_detect_emergent_properties(consciousness_mapper_adapter, sample_consciousness_data):
    """Test detect_emergent_properties method."""
    # Call the method
    result = await consciousness_mapper_adapter.detect_emergent_properties(sample_consciousness_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that emergent properties were detected
    assert len(result) > 0
    
    # Check that each property has the expected fields
    for property in result:
        assert "property_id" in property
        assert "name" in property
        assert "description" in property
        assert "emergence_level" in property
        assert "contributing_elements" in property
        assert "observed_effects" in property
        assert "stability" in property


@pytest.mark.asyncio
async def test_generate_navigation_guide(consciousness_mapper_adapter):
    """Test generate_navigation_guide method."""
    # Create a sample topology map
    topology_map = {
        "regions": [
            {
                "region_id": "region_1",
                "topology_type": "linear",
                "dimensions": {"happiness": 0.8, "energy": 0.7},
                "stability": 0.8,
                "accessibility": 0.7,
                "neighboring_regions": ["region_2", "region_3"],
                "characteristic_patterns": ["pattern_1"],
                "entry_triggers": ["trigger_1"],
                "exit_conditions": ["condition_1"]
            },
            {
                "region_id": "region_2",
                "topology_type": "cyclical",
                "dimensions": {"happiness": 0.6, "energy": 0.5},
                "stability": 0.6,
                "accessibility": 0.8,
                "neighboring_regions": ["region_1", "region_3"],
                "characteristic_patterns": ["pattern_2"],
                "entry_triggers": ["trigger_2"],
                "exit_conditions": ["condition_2"]
            },
            {
                "region_id": "region_3",
                "topology_type": "chaotic",
                "dimensions": {"happiness": 0.4, "energy": 0.3},
                "stability": 0.2,
                "accessibility": 0.5,
                "neighboring_regions": ["region_1", "region_2"],
                "characteristic_patterns": ["pattern_3"],
                "entry_triggers": ["trigger_3"],
                "exit_conditions": ["condition_3"]
            }
        ],
        "transitions": {
            "direct_transitions": {
                "region_1->region_2": 5,
                "region_2->region_1": 3,
                "region_1->region_3": 2,
                "region_3->region_1": 1,
                "region_2->region_3": 4,
                "region_3->region_2": 2
            }
        }
    }
    
    # Call the method
    result = await consciousness_mapper_adapter.generate_navigation_guide(topology_map)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "guide_id" in result
    assert "optimal_paths" in result
    assert "stability_anchors" in result
    assert "growth_trajectories" in result
    assert "warning_zones" in result
    assert "recommendations" in result
    
    # Check that stability anchors were identified (region_1 has high stability)
    assert "region_1" in result["stability_anchors"]
    
    # Check that warning zones were identified (region_3 has low stability and chaotic topology)
    warning_region_ids = [zone.get("region_id", "") for zone in result["warning_zones"]]
    assert "region_3" in warning_region_ids
    
    # Check that recommendations were generated
    assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_convert_personality_to_consciousness_states(consciousness_mapper_adapter, sample_personality_data):
    """Test _convert_personality_to_consciousness_states method."""
    # Call the method
    result = consciousness_mapper_adapter._convert_personality_to_consciousness_states(sample_personality_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that states were created
    assert len(result) == len(sample_personality_data["states"])
    
    # Check that each state has the expected fields
    for state in result:
        assert "timestamp" in state
        assert "dimensions" in state
        assert "patterns" in state
        assert "transitions" in state


@pytest.mark.asyncio
async def test_basic_consciousness_mapping(consciousness_mapper_adapter, sample_consciousness_data):
    """Test _basic_consciousness_mapping method."""
    # Call the method
    result = consciousness_mapper_adapter._basic_consciousness_mapping(sample_consciousness_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "map_id" in result
    assert "regions" in result
    assert "transitions" in result
    assert "dominant_topologies" in result
    assert "metrics" in result
    assert "insights" in result
    
    # Check that regions were created
    assert len(result["regions"]) > 0
    
    # Check that transitions were created
    assert "direct_transitions" in result["transitions"]
    assert len(result["transitions"]["direct_transitions"]) > 0
    
    # Check that metrics were calculated
    assert "region_count" in result["metrics"]
    assert "transition_count" in result["metrics"]
    assert "connectivity_density" in result["metrics"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_basic_structure_analysis(consciousness_mapper_adapter, sample_personality_data):
    """Test _basic_structure_analysis method."""
    # Call the method
    result = consciousness_mapper_adapter._basic_structure_analysis(sample_personality_data)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "analysis_id" in result
    assert "layers" in result
    assert "core_elements" in result
    assert "peripheral_elements" in result
    assert "structural_metrics" in result
    assert "insights" in result
    
    # Check that layers were created
    assert len(result["layers"]) > 0
    
    # Check that core elements were identified
    assert len(result["core_elements"]) > 0
    
    # Check that peripheral elements were identified
    assert len(result["peripheral_elements"]) > 0
    
    # Check that structural metrics were calculated
    assert "coherence" in result["structural_metrics"]
    assert "complexity" in result["structural_metrics"]
    
    # Check that insights were generated
    assert len(result["insights"]) > 0


@pytest.mark.asyncio
async def test_basic_emergent_property_detection(consciousness_mapper_adapter, sample_consciousness_data):
    """Test _basic_emergent_property_detection method."""
    # Call the method
    result = consciousness_mapper_adapter._basic_emergent_property_detection(sample_consciousness_data)
    
    # Check the result structure
    assert isinstance(result, list)
    
    # Check that emergent properties were detected
    assert len(result) > 0
    
    # Check that each property has the expected fields
    for property in result:
        assert "property_id" in property
        assert "name" in property
        assert "description" in property
        assert "emergence_level" in property
        assert "contributing_elements" in property
        assert "observed_effects" in property
        assert "stability" in property


@pytest.mark.asyncio
async def test_basic_navigation_guide(consciousness_mapper_adapter):
    """Test _basic_navigation_guide method."""
    # Create a sample topology map
    topology_map = {
        "regions": [
            {
                "region_id": "region_1",
                "topology_type": "linear",
                "dimensions": {"happiness": 0.8, "energy": 0.7},
                "stability": 0.8,
                "accessibility": 0.7,
                "neighboring_regions": ["region_2", "region_3"],
                "characteristic_patterns": ["pattern_1"],
                "entry_triggers": ["trigger_1"],
                "exit_conditions": ["condition_1"]
            },
            {
                "region_id": "region_2",
                "topology_type": "cyclical",
                "dimensions": {"happiness": 0.6, "energy": 0.5},
                "stability": 0.6,
                "accessibility": 0.8,
                "neighboring_regions": ["region_1", "region_3"],
                "characteristic_patterns": ["pattern_2"],
                "entry_triggers": ["trigger_2"],
                "exit_conditions": ["condition_2"]
            },
            {
                "region_id": "region_3",
                "topology_type": "chaotic",
                "dimensions": {"happiness": 0.4, "energy": 0.3},
                "stability": 0.2,
                "accessibility": 0.5,
                "neighboring_regions": ["region_1", "region_2"],
                "characteristic_patterns": ["pattern_3"],
                "entry_triggers": ["trigger_3"],
                "exit_conditions": ["condition_3"]
            }
        ]
    }
    
    # Call the method
    result = consciousness_mapper_adapter._basic_navigation_guide(topology_map)
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "guide_id" in result
    assert "optimal_paths" in result
    assert "stability_anchors" in result
    assert "growth_trajectories" in result
    assert "warning_zones" in result
    assert "recommendations" in result
    
    # Check that stability anchors were identified (region_1 has high stability)
    assert "region_1" in result["stability_anchors"]
    
    # Check that warning zones were identified (region_3 has low stability and chaotic topology)
    warning_region_ids = [zone.get("region_id", "") for zone in result["warning_zones"]]
    assert "region_3" in warning_region_ids
    
    # Check that recommendations were generated
    assert len(result["recommendations"]) > 0