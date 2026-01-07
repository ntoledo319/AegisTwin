"""
Tests for the PersonalityEngine.

This module contains tests for the PersonalityEngine class and its components.
"""

import pytest
from typing import Dict, Any
import asyncio

# Import the PersonalityEngine
from digital_twin import PersonalityEngine


class TestPersonalityEngine:
    """
    Tests for the PersonalityEngine class.
    """

    def test_initialization(self, personality_engine):
        """
        Test that the PersonalityEngine initializes correctly.
        """
        assert personality_engine is not None
        assert isinstance(personality_engine, PersonalityEngine)
        assert personality_engine.trait_extractors is not None
        assert personality_engine.evolution_engine is not None
        assert personality_engine.alignment_module is not None
        assert personality_engine.pattern_analyzer is not None

    def test_trait_extractors_initialization(self, personality_engine):
        """
        Test that the trait extractors are initialized correctly.
        """
        extractors = personality_engine.trait_extractors
        assert extractors is not None
        assert "text" in extractors
        assert "communication" in extractors
        assert "activity" in extractors
        assert "social" in extractors
        assert "consumption" in extractors

    @pytest.mark.asyncio
    async def test_extract_traits(self, personality_engine, sample_user_data):
        """
        Test extracting traits from user data.
        """
        traits = await personality_engine.extract_traits(sample_user_data)
        
        # Check that traits were extracted
        assert traits is not None
        assert isinstance(traits, dict)
        assert len(traits) > 0
        
        # Check for specific traits
        assert "openness" in traits
        assert "conscientiousness" in traits
        assert "extraversion" in traits
        assert "agreeableness" in traits
        assert "neuroticism" in traits
        
        # Check trait values are in the expected range
        for trait, value in traits.items():
            assert 0.0 <= value <= 1.0

    @pytest.mark.asyncio
    async def test_create_personality_profile(self, personality_engine, sample_user_data):
        """
        Test creating a personality profile.
        """
        # Extract traits
        traits = await personality_engine.extract_traits(sample_user_data)
        
        # Create profile
        user_id = "test_user_123"
        profile = await personality_engine.create_personality_profile(user_id, traits)
        
        # Check profile structure
        assert profile is not None
        assert isinstance(profile, dict)
        assert "user_id" in profile
        assert profile["user_id"] == user_id
        assert "traits" in profile
        assert "dimensions" in profile
        assert "patterns" in profile
        assert "created_at" in profile
        assert "updated_at" in profile
        assert "version" in profile
        
        # Check dimensions
        dimensions = profile["dimensions"]
        assert "openness" in dimensions
        assert "conscientiousness" in dimensions
        assert "extraversion" in dimensions
        assert "agreeableness" in dimensions
        assert "neuroticism" in dimensions
        
        # Check dimension values are in the expected range
        for dimension, value in dimensions.items():
            assert 0.0 <= value <= 1.0

    @pytest.mark.asyncio
    async def test_update_personality_profile(self, personality_engine, sample_user_data):
        """
        Test updating a personality profile.
        """
        # Extract traits
        traits = await personality_engine.extract_traits(sample_user_data)
        
        # Create profile
        user_id = "test_user_123"
        profile = await personality_engine.create_personality_profile(user_id, traits)
        
        # Create new data
        new_data = {
            "text": {
                "content": "I prefer structured environments and planning ahead. I enjoy organizing and categorizing things."
            }
        }
        
        # Extract new traits
        new_traits = await personality_engine.extract_traits(new_data)
        
        # Update profile
        updated_profile = await personality_engine.update_personality_profile(profile, new_data)
        
        # Check updated profile
        assert updated_profile is not None
        assert isinstance(updated_profile, dict)
        assert "user_id" in updated_profile
        assert updated_profile["user_id"] == user_id
        assert "traits" in updated_profile
        assert "dimensions" in updated_profile
        assert "patterns" in updated_profile
        assert "created_at" in updated_profile
        assert "updated_at" in updated_profile
        assert "version" in updated_profile
        
        # Check that version has increased
        assert updated_profile["version"] > profile["version"]
        
        # Check that update time has changed
        assert updated_profile["updated_at"] != profile["updated_at"]

    @pytest.mark.asyncio
    async def test_align_response(self, personality_engine, sample_user_data):
        """
        Test aligning a response with a personality profile.
        """
        # Extract traits
        traits = await personality_engine.extract_traits(sample_user_data)
        
        # Create profile
        user_id = "test_user_123"
        profile = await personality_engine.create_personality_profile(user_id, traits)
        
        # Create a response
        response = "Here is some information about hiking trails in the Rocky Mountains."
        
        # Create context
        context = {
            "current_topic": "hiking",
            "conversation_state": "exploration"
        }
        
        # Align response
        aligned_response = await personality_engine.align_response(profile, response, context)
        
        # Check aligned response
        assert aligned_response is not None
        assert isinstance(aligned_response, str)
        assert len(aligned_response) > 0