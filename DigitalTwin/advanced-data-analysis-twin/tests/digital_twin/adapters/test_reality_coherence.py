"""
Tests for the RealityCoherenceValidator adapter.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from digital_twin.adapters.reality_coherence import RealityCoherenceValidator


class TestRealityCoherenceValidator:
    """Tests for the RealityCoherenceValidator adapter."""

    @pytest.fixture
    def validator(self):
        """Create a RealityCoherenceValidator instance for testing."""
        return RealityCoherenceValidator()

    @pytest.fixture
    def digital_twin_state(self):
        """Create a sample digital twin state for testing."""
        return {
            "personality": {
                "traits": {
                    "openness": 0.8,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.9,
                    "neuroticism": 0.3
                },
                "interests": ["technology", "science", "art", "music"],
                "values": ["honesty", "creativity", "compassion"]
            },
            "memory": {
                "episodic": [
                    {
                        "id": "mem_001",
                        "content": "User mentioned they love hiking in the mountains",
                        "timestamp": datetime.now().isoformat(),
                        "importance": 0.8
                    }
                ],
                "semantic": {
                    "user_facts": {
                        "likes_hiking": True,
                        "has_dog": True,
                        "favorite_color": "blue"
                    }
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    @pytest.fixture
    def reality_context(self):
        """Create a sample reality context for testing."""
        return {
            "observed_behaviors": {
                "hiking_frequency": "weekly",
                "pet_ownership": True,
                "color_preferences": ["blue", "green"]
            },
            "external_data": {
                "location_data": {
                    "frequently_visited": ["mountain trails", "dog parks", "art galleries"]
                },
                "social_media": {
                    "interests": ["hiking", "dogs", "photography", "art"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    @pytest.mark.asyncio
    async def test_validate_coherence_with_spidermind(self, validator, digital_twin_state, reality_context):
        """Test validate_coherence with SpiderMind Omega components."""
        # Mock the SpiderMind Omega components
        validator.reality_coherence = MagicMock()
        validator.reality_coherence.validate_consciousness_coherence = MagicMock(
            return_value=asyncio.Future()
        )
        validator.reality_coherence.validate_consciousness_coherence.return_value.set_result({
            "coherence_level": 3,
            "coherence_score": 0.85,
            "validation_metrics": [
                {
                    "metric_id": "test_metric_1",
                    "constraint_type": "cognitive",
                    "coherence_score": 0.9,
                    "confidence": 0.8
                }
            ],
            "insights": ["Digital twin model is well-aligned with reality"],
            "recommendations": []
        })

        # Call the method
        result = await validator.validate_coherence(digital_twin_state, reality_context)

        # Verify the result
        assert result["coherence_score"] > 0.8
        assert "insights" in result
        assert "recommendations" in result
        assert len(result["validation_metrics"]) > 0

        # Verify that the SpiderMind method was called
        validator.reality_coherence.validate_consciousness_coherence.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_coherence_fallback(self, validator, digital_twin_state, reality_context):
        """Test validate_coherence fallback implementation."""
        # Ensure SpiderMind components are not available
        validator.reality_coherence = None
        validator.coherence_validator = None
        validator.reality_structures = None

        # Call the method
        result = await validator.validate_coherence(digital_twin_state, reality_context)

        # Verify the result
        assert "coherence_score" in result
        assert "insights" in result
        assert "recommendations" in result
        assert "validation_metrics" in result

    @pytest.mark.asyncio
    async def test_establish_reality_anchor(self, validator):
        """Test establish_reality_anchor method."""
        # Mock the SpiderMind Omega components
        validator.reality_coherence = MagicMock()
        validator.reality_coherence.establish_reality_anchor = MagicMock(
            return_value=asyncio.Future()
        )
        validator.reality_coherence.establish_reality_anchor.return_value.set_result({
            "anchor_id": "test_anchor_1",
            "status": "established"
        })

        # Mock the reality_structures module
        class MockRealityConstraint:
            COGNITIVE = "cognitive"
        
        validator.reality_structures = MagicMock()
        validator.reality_structures.RealityConstraint = MockRealityConstraint

        # Call the method
        result = await validator.establish_reality_anchor(
            "test_anchor_1",
            "cognitive",
            {"fact": "User is a software engineer"},
            0.9
        )

        # Verify the result
        assert result["anchor_id"] == "test_anchor_1"
        assert result["status"] == "established"

        # Verify that the SpiderMind method was called
        validator.reality_coherence.establish_reality_anchor.assert_called_once()

    @pytest.mark.asyncio
    async def test_establish_reality_anchor_fallback(self, validator):
        """Test establish_reality_anchor fallback implementation."""
        # Ensure SpiderMind components are not available
        validator.reality_coherence = None
        validator.reality_structures = None

        # Call the method
        result = await validator.establish_reality_anchor(
            "test_anchor_1",
            "cognitive",
            {"fact": "User is a software engineer"},
            0.9
        )

        # Verify the result
        assert result["anchor_id"] == "test_anchor_1"
        assert result["status"] == "established"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_generate_coherence_insights(self, validator, digital_twin_state, reality_context):
        """Test generate_coherence_insights method."""
        # Mock the SpiderMind Omega components
        validator.reality_coherence = MagicMock()
        validator.reality_coherence.validate_consciousness_coherence = MagicMock(
            return_value=asyncio.Future()
        )
        validator.reality_coherence.validate_consciousness_coherence.return_value.set_result({
            "coherence_level": 3,
            "coherence_score": 0.85,
            "insights": ["Digital twin model is well-aligned with reality"]
        })

        # Call the method
        result = await validator.generate_coherence_insights(digital_twin_state, reality_context)

        # Verify the result
        assert len(result) > 0
        assert isinstance(result[0], str)

        # Verify that the SpiderMind method was called
        validator.reality_coherence.validate_consciousness_coherence.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_coherence_insights_fallback(self, validator, digital_twin_state, reality_context):
        """Test generate_coherence_insights fallback implementation."""
        # Ensure SpiderMind components are not available
        validator.reality_coherence = None

        # Call the method
        result = await validator.generate_coherence_insights(digital_twin_state, reality_context)

        # Verify the result
        assert len(result) > 0
        assert isinstance(result[0], str)