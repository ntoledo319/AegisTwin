"""
Tests for the EnhancedQuantumProfileAdapter adapter.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.adapters.enhanced_quantum_profile import EnhancedQuantumProfileAdapter


class TestEnhancedQuantumProfileAdapter:
    """Tests for the EnhancedQuantumProfileAdapter adapter."""

    @pytest.fixture
    def adapter(self):
        """Create an EnhancedQuantumProfileAdapter instance for testing."""
        return EnhancedQuantumProfileAdapter()

    @pytest.fixture
    def personality_traits(self):
        """Create sample personality traits for testing."""
        return {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
            "interests": ["technology", "science", "art", "music"],
            "values": ["honesty", "creativity", "compassion"]
        }

    @pytest.fixture
    def context_factors(self):
        """Create sample context factors for testing."""
        return {
            "work": {
                "cognitive": 0.1,
                "social": -0.1,
                "structural": 0.2
            },
            "social": {
                "cognitive": -0.1,
                "social": 0.2,
                "emotional": 0.1
            },
            "creative": {
                "cognitive": 0.1,
                "creative": 0.3,
                "structural": -0.1
            }
        }

    @pytest.fixture
    def memory_data(self):
        """Create sample memory data for testing."""
        return {
            "episodic": [
                {
                    "id": "mem_001",
                    "content": "User mentioned they love hiking in the mountains",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 0.8
                },
                {
                    "id": "mem_002",
                    "content": "User expressed frustration with work deadline",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 0.7
                }
            ],
            "semantic": {
                "user_facts": {
                    "likes_hiking": True,
                    "has_dog": True,
                    "favorite_color": "blue"
                }
            }
        }

    @pytest.mark.asyncio
    async def test_create_quantum_profile_with_spidermind(self, adapter, personality_traits):
        """Test create_quantum_profile with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        adapter.quantum_engine = MagicMock()
        adapter.quantum_engine.create_consciousness_profile = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.create_consciousness_profile.return_value.set_result({
            "profile_id": "test_profile_1",
            "status": "created"
        })
        
        adapter.quantum_engine.update_quantum_dimension = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.update_quantum_dimension.return_value.set_result({
            "status": "updated"
        })
        
        adapter.quantum_engine.generate_consciousness_insights = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.generate_consciousness_insights.return_value.set_result({
            "consciousness_overview": {
                "dominant_dimensions": ["cognitive", "emotional"],
                "consciousness_stability": 0.8,
                "growth_trajectory": "ascending"
            },
            "quantum_insights": ["Strong cognitive processing capabilities", "Balanced emotional responses"],
            "dimensional_balance": 0.7,
            "coherence_score": 0.75
        })

        # Call the method
        result = await adapter.create_quantum_profile(personality_traits)

        # Verify the result
        assert "profile_id" in result
        assert "quantum_dimensions" in result
        assert len(result["quantum_dimensions"]) > 0
        assert "consciousness_overview" in result
        assert "quantum_insights" in result
        assert "dimensional_balance" in result
        assert "coherence_score" in result

        # Verify that the SpiderMind methods were called
        adapter.quantum_engine.create_consciousness_profile.assert_called_once()
        assert adapter.quantum_engine.update_quantum_dimension.call_count > 0
        adapter.quantum_engine.generate_consciousness_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_quantum_profile_fallback(self, adapter, personality_traits):
        """Test create_quantum_profile fallback implementation."""
        # Ensure SpiderMind components are not available
        adapter.quantum_engine = None
        adapter.quantum_structures = None

        # Call the method
        result = await adapter.create_quantum_profile(personality_traits)

        # Verify the result
        assert "profile_id" in result
        assert "quantum_dimensions" in result
        assert len(result["quantum_dimensions"]) > 0
        assert "consciousness_overview" in result
        assert "quantum_insights" in result
        assert "dimensional_balance" in result
        assert "coherence_score" in result

    @pytest.mark.asyncio
    async def test_model_quantum_states_with_spidermind(self, adapter, personality_traits, context_factors):
        """Test model_quantum_states with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        adapter.quantum_engine = MagicMock()
        adapter.quantum_engine.create_consciousness_profile = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.create_consciousness_profile.return_value.set_result({
            "profile_id": "test_profile_1",
            "status": "created"
        })
        
        adapter.quantum_engine.update_quantum_dimension = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.update_quantum_dimension.return_value.set_result({
            "status": "updated"
        })
        
        adapter.quantum_engine.create_quantum_state = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.create_quantum_state.return_value.set_result({
            "state_id": "test_state_1",
            "state_name": "work",
            "dimensions": {
                "cognitive": 0.9,
                "social": 0.5,
                "structural": 0.9
            },
            "probability": 0.33
        })
        
        adapter.quantum_engine.calculate_state_superposition = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.calculate_state_superposition.return_value.set_result({
            "coherence": 0.7,
            "dominant_state": "test_state_1",
            "dimensions": {
                "cognitive": 0.8,
                "social": 0.6,
                "structural": 0.7,
                "emotional": 0.6
            },
            "interference_pattern": "constructive"
        })

        # Call the method
        result = await adapter.model_quantum_states(personality_traits, context_factors)

        # Verify the result
        assert "base_dimensions" in result
        assert "quantum_states" in result
        assert len(result["quantum_states"]) > 0
        assert "superposition" in result
        assert "coherence" in result["superposition"]
        assert "dominant_state" in result["superposition"]
        assert "dimensional_values" in result["superposition"]

        # Verify that the SpiderMind methods were called
        adapter.quantum_engine.create_consciousness_profile.assert_called_once()
        assert adapter.quantum_engine.update_quantum_dimension.call_count > 0
        assert adapter.quantum_engine.create_quantum_state.call_count > 0
        adapter.quantum_engine.calculate_state_superposition.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_quantum_states_fallback(self, adapter, personality_traits, context_factors):
        """Test model_quantum_states fallback implementation."""
        # Ensure SpiderMind components are not available
        adapter.quantum_engine = None
        adapter.quantum_structures = None

        # Call the method
        result = await adapter.model_quantum_states(personality_traits, context_factors)

        # Verify the result
        assert "base_dimensions" in result
        assert "quantum_states" in result
        assert len(result["quantum_states"]) > 0
        assert "superposition" in result
        assert "coherence" in result["superposition"]
        assert "dominant_state" in result["superposition"]
        assert "dimensional_values" in result["superposition"]

    @pytest.mark.asyncio
    async def test_analyze_superposition(self, adapter):
        """Test analyze_superposition method."""
        # Create sample quantum states
        quantum_states = [
            {
                "state_id": "state_1",
                "context": "work",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.9},
                    {"name": "social", "value": 0.5},
                    {"name": "structural", "value": 0.9}
                ],
                "probability": 0.33
            },
            {
                "state_id": "state_2",
                "context": "social",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.7},
                    {"name": "social", "value": 0.8},
                    {"name": "emotional", "value": 0.7}
                ],
                "probability": 0.33
            },
            {
                "state_id": "state_3",
                "context": "creative",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.8},
                    {"name": "creative", "value": 0.9},
                    {"name": "structural", "value": 0.6}
                ],
                "probability": 0.34
            }
        ]

        # Mock the SpiderMind Omega components
        adapter.quantum_engine = MagicMock()
        adapter.quantum_engine.create_consciousness_profile = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.create_consciousness_profile.return_value.set_result({
            "profile_id": "test_profile_1",
            "status": "created"
        })
        
        adapter.quantum_engine.register_quantum_state = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.register_quantum_state.return_value.set_result({
            "state_id": "test_state_1",
            "status": "registered"
        })
        
        adapter.quantum_engine.calculate_state_superposition = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.calculate_state_superposition.return_value.set_result({
            "coherence": 0.7,
            "dominant_state": "test_state_1",
            "dimensions": {
                "cognitive": 0.8,
                "social": 0.65,
                "structural": 0.75,
                "emotional": 0.7,
                "creative": 0.9
            }
        })
        
        adapter.quantum_engine.analyze_quantum_interference = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.quantum_engine.analyze_quantum_interference.return_value.set_result({
            "pattern_type": "constructive",
            "constructive_dimensions": ["cognitive", "creative"],
            "destructive_dimensions": [],
            "neutral_dimensions": ["social", "structural", "emotional"],
            "interference_strength": 0.6,
            "state_relationships": [
                {
                    "state_1": "test_state_1",
                    "state_2": "test_state_2",
                    "compatibility": 0.7,
                    "interaction_type": "reinforcing"
                }
            ],
            "emergent_properties": ["Enhanced cognitive processing", "Creative problem-solving"]
        })

        # Call the method
        result = await adapter.analyze_superposition(quantum_states)

        # Verify the result
        assert "coherence" in result
        assert "interference_pattern" in result
        assert "dimensional_values" in result
        assert "interference_analysis" in result
        assert "constructive_dimensions" in result["interference_analysis"]
        assert "state_relationships" in result
        assert "emergent_properties" in result

        # Verify that the SpiderMind methods were called
        adapter.quantum_engine.create_consciousness_profile.assert_called_once()
        assert adapter.quantum_engine.register_quantum_state.call_count > 0
        adapter.quantum_engine.calculate_state_superposition.assert_called_once()
        adapter.quantum_engine.analyze_quantum_interference.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_superposition_fallback(self, adapter):
        """Test analyze_superposition fallback implementation."""
        # Ensure SpiderMind components are not available
        adapter.quantum_engine = None
        adapter.quantum_structures = None

        # Create sample quantum states
        quantum_states = [
            {
                "state_id": "state_1",
                "context": "work",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.9},
                    {"name": "social", "value": 0.5},
                    {"name": "structural", "value": 0.9}
                ],
                "probability": 0.33
            },
            {
                "state_id": "state_2",
                "context": "social",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.7},
                    {"name": "social", "value": 0.8},
                    {"name": "emotional", "value": 0.7}
                ],
                "probability": 0.33
            },
            {
                "state_id": "state_3",
                "context": "creative",
                "quantum_dimensions": [
                    {"name": "cognitive", "value": 0.8},
                    {"name": "creative", "value": 0.9},
                    {"name": "structural", "value": 0.6}
                ],
                "probability": 0.34
            }
        ]

        # Call the method
        result = await adapter.analyze_superposition(quantum_states)

        # Verify the result
        assert "coherence" in result
        assert "interference_pattern" in result
        assert "dimensional_values" in result
        assert "interference_analysis" in result
        assert "constructive_dimensions" in result["interference_analysis"]
        assert "state_relationships" in result

    @pytest.mark.asyncio
    async def test_map_consciousness_topology(self, adapter, personality_traits, memory_data):
        """Test map_consciousness_topology method."""
        # Mock the SpiderMind Omega components
        adapter.consciousness_mapper = MagicMock()
        adapter.consciousness_mapper.map_consciousness = MagicMock(
            return_value=asyncio.Future()
        )
        adapter.consciousness_mapper.map_consciousness.return_value.set_result({
            "topology_map": {
                "nodes": [
                    {"id": "node_1", "type": "trait", "name": "openness", "strength": 0.8, "layer": "core"},
                    {"id": "node_2", "type": "interest", "name": "technology", "strength": 0.7, "layer": "middle"}
                ],
                "edges": [
                    {"source": "node_1", "target": "node_2", "strength": 0.6, "type": "influences"}
                ]
            },
            "consciousness_layers": [
                {"name": "core", "description": "Core traits", "nodes": ["node_1"]},
                {"name": "middle", "description": "Interests", "nodes": ["node_2"]}
            ],
            "core_nodes": ["node_1"],
            "peripheral_nodes": [],
            "topology_metrics": {
                "node_count": 2,
                "edge_count": 1,
                "density": 0.5
            },
            "insights": ["Strong connection between openness and technology interest"]
        })

        # Call the method
        result = await adapter.map_consciousness_topology(personality_traits, memory_data)

        # Verify the result
        assert "topology_map" in result
        assert "nodes" in result["topology_map"]
        assert "edges" in result["topology_map"]
        assert "consciousness_layers" in result
        assert "core_nodes" in result
        assert "peripheral_nodes" in result
        assert "topology_metrics" in result
        assert "insights" in result

        # Verify that the SpiderMind method was called
        adapter.consciousness_mapper.map_consciousness.assert_called_once()

    @pytest.mark.asyncio
    async def test_map_consciousness_topology_fallback(self, adapter, personality_traits, memory_data):
        """Test map_consciousness_topology fallback implementation."""
        # Ensure SpiderMind components are not available
        adapter.consciousness_mapper = None

        # Call the method
        result = await adapter.map_consciousness_topology(personality_traits, memory_data)

        # Verify the result
        assert "topology_map" in result
        assert "nodes" in result["topology_map"]
        assert "edges" in result["topology_map"]
        assert "consciousness_layers" in result
        assert "core_nodes" in result
        assert "peripheral_nodes" in result
        assert "topology_metrics" in result
        assert "insights" in result