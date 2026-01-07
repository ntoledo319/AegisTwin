"""
Tests for the SpiderMind Omega adapters.

This module contains tests for the adapter classes that integrate with SpiderMind Omega.
"""

import pytest
from typing import Dict, Any
import asyncio
import os
import sys

# Import the adapters
from digital_twin.adapters import BehavioralPatternAnalyzer, QuantumProfileAdapter, SpiderMindCompatibilityLayer


class TestBehavioralPatternAnalyzer:
    """
    Tests for the BehavioralPatternAnalyzer class.
    """

    def test_initialization(self):
        """
        Test that the BehavioralPatternAnalyzer initializes correctly.
        """
        analyzer = BehavioralPatternAnalyzer()
        assert analyzer is not None

    @pytest.mark.asyncio
    async def test_analyze_patterns(self):
        """
        Test analyzing patterns.
        """
        analyzer = BehavioralPatternAnalyzer()
        
        # Sample traits
        traits = {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.75,
            "neuroticism": 0.4,
            "formality": 0.6,
            "verbosity": 0.7,
            "emotionality": 0.5,
            "assertiveness": 0.6,
            "analytical_thinking": 0.8
        }
        
        # Analyze patterns
        patterns = await analyzer.analyze_patterns(traits)
        
        # Check patterns
        assert patterns is not None
        assert isinstance(patterns, dict)
        
        # Even if PatternHydra is not available, the fallback should provide results
        assert len(patterns) > 0


class TestQuantumProfileAdapter:
    """
    Tests for the QuantumProfileAdapter class.
    """

    def test_initialization(self):
        """
        Test that the QuantumProfileAdapter initializes correctly.
        """
        adapter = QuantumProfileAdapter()
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_create_quantum_profile(self):
        """
        Test creating a quantum profile.
        """
        adapter = QuantumProfileAdapter()
        
        # Sample personality traits
        traits = {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.75,
            "neuroticism": 0.4,
            "formality": 0.6,
            "verbosity": 0.7,
            "emotionality": 0.5,
            "assertiveness": 0.6,
            "analytical_thinking": 0.8
        }
        
        # Create quantum profile
        profile = await adapter.create_quantum_profile(traits)
        
        # Check profile
        assert profile is not None
        assert isinstance(profile, dict)
        
        # Check profile structure
        assert "dimensions" in profile
        assert "traits" in profile
        assert "quantum_attributes" in profile
        assert "quantum_profile" in profile
        
        # Check dimensions
        dimensions = profile["dimensions"]
        assert "openness" in dimensions
        assert "conscientiousness" in dimensions
        assert "extraversion" in dimensions
        assert "agreeableness" in dimensions
        assert "neuroticism" in dimensions
        
        # Check quantum attributes
        quantum_attributes = profile["quantum_attributes"]
        assert "coherence_level" in quantum_attributes
        assert "quantum_state" in quantum_attributes
        assert "temporal_stability" in quantum_attributes

    @pytest.mark.asyncio
    async def test_update_quantum_profile(self):
        """
        Test updating a quantum profile.
        """
        adapter = QuantumProfileAdapter()
        
        # Sample personality traits
        traits = {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.75,
            "neuroticism": 0.4
        }
        
        # Create quantum profile
        profile = await adapter.create_quantum_profile(traits)
        
        # New traits
        new_traits = {
            "openness": 0.7,
            "conscientiousness": 0.8,
            "analytical_thinking": 0.9
        }
        
        # Update profile
        updated_profile = await adapter.update_quantum_profile(profile, new_traits)
        
        # Check updated profile
        assert updated_profile is not None
        assert isinstance(updated_profile, dict)
        
        # Check that dimensions have been updated
        dimensions = updated_profile["dimensions"]
        assert dimensions["openness"] != traits["openness"]
        assert dimensions["conscientiousness"] != traits["conscientiousness"]
        
        # Check that new traits have been added
        assert "analytical_thinking" in updated_profile["traits"]

    @pytest.mark.asyncio
    async def test_analyze_quantum_patterns(self):
        """
        Test analyzing quantum patterns.
        """
        adapter = QuantumProfileAdapter()
        
        # Sample personality traits
        traits = {
            "openness": 0.8,
            "conscientiousness": 0.6,
            "extraversion": 0.7,
            "agreeableness": 0.75,
            "neuroticism": 0.4
        }
        
        # Create quantum profile
        profile = await adapter.create_quantum_profile(traits)
        
        # Analyze patterns
        patterns = await adapter.analyze_quantum_patterns(profile)
        
        # Check patterns
        assert patterns is not None
        assert isinstance(patterns, dict)
        
        # Even if QuantumProfile is not available, the fallback should provide results
        assert len(patterns) > 0


class TestSpiderMindCompatibilityLayer:
    """
    Tests for the SpiderMindCompatibilityLayer class.
    """

    def test_initialization(self):
        """
        Test that the SpiderMindCompatibilityLayer initializes correctly.
        """
        layer = SpiderMindCompatibilityLayer()
        assert layer is not None
        assert hasattr(layer, "spidermind_components")

    def test_get_component(self):
        """
        Test getting a component.
        """
        layer = SpiderMindCompatibilityLayer()
        
        # Try to get components
        pattern_hydra = layer.get_component("pattern_hydra")
        quantum_engine = layer.get_component("quantum_consciousness_engine")
        
        # Components may or may not be available depending on SpiderMind Omega installation
        # But the method should not raise an exception
        assert True

    @pytest.mark.asyncio
    async def test_analyze_patterns(self):
        """
        Test analyzing patterns.
        """
        layer = SpiderMindCompatibilityLayer()
        
        # Sample data
        data = {
            "personality": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.75,
                "neuroticism": 0.4
            },
            "behavior": {
                "activity_level": 0.7,
                "social_engagement": 0.6,
                "learning_preference": "visual",
                "decision_style": "analytical"
            }
        }
        
        # Analyze patterns
        patterns = await layer.analyze_patterns(data)
        
        # Check patterns
        assert patterns is not None
        assert isinstance(patterns, dict)
        
        # Even if PatternHydra is not available, the fallback should provide results
        assert len(patterns) > 0

    @pytest.mark.asyncio
    async def test_create_quantum_profile(self):
        """
        Test creating a quantum profile.
        """
        layer = SpiderMindCompatibilityLayer()
        
        # Sample personality data
        personality_data = {
            "dimensions": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.75,
                "neuroticism": 0.4
            },
            "traits": {
                "formality": 0.6,
                "verbosity": 0.7,
                "emotionality": 0.5,
                "assertiveness": 0.6,
                "analytical_thinking": 0.8
            }
        }
        
        # Create quantum profile
        profile = await layer.create_quantum_profile(personality_data)
        
        # Check profile
        assert profile is not None
        assert isinstance(profile, dict)
        
        # Even if QuantumConsciousnessEngine is not available, the fallback should provide results
        assert len(profile) > 0

    @pytest.mark.asyncio
    async def test_predict_future_state(self):
        """
        Test predicting future state.
        """
        layer = SpiderMindCompatibilityLayer()
        
        # Sample profile
        profile = {
            "dimensions": {
                "openness": 0.8,
                "conscientiousness": 0.6,
                "extraversion": 0.7,
                "agreeableness": 0.75,
                "neuroticism": 0.4
            },
            "traits": {
                "formality": 0.6,
                "verbosity": 0.7,
                "emotionality": 0.5,
                "assertiveness": 0.6,
                "analytical_thinking": 0.8
            }
        }
        
        # Predict future state
        prediction = await layer.predict_future_state(profile, 30)
        
        # Check prediction
        assert prediction is not None
        assert isinstance(prediction, dict)
        
        # Even if FuturePredictor is not available, the fallback should provide results
        assert len(prediction) > 0

    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns(self):
        """
        Test analyzing temporal patterns.
        """
        layer = SpiderMindCompatibilityLayer()
        
        # Sample temporal data
        data = {
            "start_time": "2025-01-01T00:00:00",
            "end_time": "2025-09-26T00:00:00",
            "resolution": "day",
            "data_points": [
                {"date": "2025-01-15", "value": 0.7},
                {"date": "2025-02-15", "value": 0.8},
                {"date": "2025-03-15", "value": 0.6},
                {"date": "2025-04-15", "value": 0.9},
                {"date": "2025-05-15", "value": 0.7},
                {"date": "2025-06-15", "value": 0.8},
                {"date": "2025-07-15", "value": 0.7},
                {"date": "2025-08-15", "value": 0.6},
                {"date": "2025-09-15", "value": 0.8}
            ]
        }
        
        # Analyze temporal patterns
        patterns = await layer.analyze_temporal_patterns(data)
        
        # Check patterns
        assert patterns is not None
        assert isinstance(patterns, dict)
        
        # Even if TimeWeaver is not available, the fallback should provide results
        assert len(patterns) > 0