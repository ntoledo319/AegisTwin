"""
Personality Engine for the Digital Twin.

This module provides the core functionality for modeling and evolving the user's
personality based on their data.
"""

import datetime
import logging
from typing import Dict, Any, List, Optional

from .traits import PersonalityTraitExtractor
from .evolution import PersonalityEvolutionEngine
from .alignment import PersonalityAlignmentModule
from ..adapters.pattern_hydra import BehavioralPatternAnalyzer

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """
    Engine for modeling and evolving user personality.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the personality engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.trait_extractors = self._initialize_trait_extractors()
        self.evolution_engine = PersonalityEvolutionEngine(config)
        self.alignment_module = PersonalityAlignmentModule(config)
        self.pattern_analyzer = BehavioralPatternAnalyzer(config)
        logger.info("Personality Engine initialized")

    def _initialize_trait_extractors(self) -> Dict[str, PersonalityTraitExtractor]:
        """
        Initialize trait extractors for different data types.

        Returns:
            Dictionary of trait extractors
        """
        from .extractors.textual import TextualTraitExtractor
        from .extractors.communication import CommunicationTraitExtractor
        from .extractors.activity import ActivityTraitExtractor
        from .extractors.social import SocialTraitExtractor
        from .extractors.consumption import ConsumptionTraitExtractor

        return {
            "text": TextualTraitExtractor(),
            "communication": CommunicationTraitExtractor(),
            "activity": ActivityTraitExtractor(),
            "social": SocialTraitExtractor(),
            "consumption": ConsumptionTraitExtractor(),
        }

    async def extract_traits(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from user data.

        Args:
            user_data: User data dictionary

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        for data_type, extractor in self.trait_extractors.items():
            if data_type in user_data:
                logger.debug(f"Extracting traits from {data_type} data")
                data_traits = await extractor.extract_traits(user_data[data_type])
                traits.update(data_traits)

        return traits

    async def create_personality_profile(self, user_id: str, traits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a personality profile from extracted traits.

        Args:
            user_id: User ID
            traits: Extracted traits

        Returns:
            Personality profile dictionary
        """
        # Create basic profile
        profile = {
            "user_id": user_id,
            "traits": traits,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "version": 1,
        }

        # Add derived personality dimensions
        profile["dimensions"] = {
            "openness": self._calculate_openness(traits),
            "conscientiousness": self._calculate_conscientiousness(traits),
            "extraversion": self._calculate_extraversion(traits),
            "agreeableness": self._calculate_agreeableness(traits),
            "neuroticism": self._calculate_neuroticism(traits),
        }

        # Add behavioral patterns
        profile["patterns"] = await self.pattern_analyzer.analyze_patterns(traits)

        # Add communication style
        profile["communication_style"] = {
            "formality": self._calculate_formality(traits),
            "verbosity": self._calculate_verbosity(traits),
            "emotionality": self._calculate_emotionality(traits),
            "assertiveness": self._calculate_assertiveness(traits),
            "humor": self._calculate_humor(traits),
        }

        logger.info(f"Created personality profile for user {user_id}")
        return profile

    async def update_personality_profile(self, profile: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a personality profile with new data.

        Args:
            profile: Existing personality profile
            new_data: New user data

        Returns:
            Updated personality profile
        """
        # Extract traits from new data
        new_traits = await self.extract_traits(new_data)

        # Evolve existing traits with new traits
        updated_traits = await self.evolution_engine.evolve_traits(profile["traits"], new_traits)

        # Update profile
        updated_profile = profile.copy()
        updated_profile["traits"] = updated_traits
        updated_profile["updated_at"] = datetime.datetime.now().isoformat()
        updated_profile["version"] += 1

        # Update derived dimensions
        updated_profile["dimensions"] = {
            "openness": self._calculate_openness(updated_traits),
            "conscientiousness": self._calculate_conscientiousness(updated_traits),
            "extraversion": self._calculate_extraversion(updated_traits),
            "agreeableness": self._calculate_agreeableness(updated_traits),
            "neuroticism": self._calculate_neuroticism(updated_traits),
        }

        # Update behavioral patterns
        updated_profile["patterns"] = await self.pattern_analyzer.analyze_patterns(updated_traits)

        # Update communication style
        updated_profile["communication_style"] = {
            "formality": self._calculate_formality(updated_traits),
            "verbosity": self._calculate_verbosity(updated_traits),
            "emotionality": self._calculate_emotionality(updated_traits),
            "assertiveness": self._calculate_assertiveness(updated_traits),
            "humor": self._calculate_humor(updated_traits),
        }

        logger.info(f"Updated personality profile for user {profile['user_id']}")
        return updated_profile

    async def align_response(self, profile: Dict[str, Any], response: str, context: Dict[str, Any]) -> str:
        """
        Align a response with the personality profile.

        Args:
            profile: Personality profile
            response: Original response
            context: Conversation context

        Returns:
            Aligned response
        """
        return await self.alignment_module.align_response(profile, response, context)

    def _calculate_openness(self, traits: Dict[str, Any]) -> float:
        """
        Calculate openness score from traits.

        Args:
            traits: Personality traits

        Returns:
            Openness score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        # In a real implementation, this would use a more sophisticated algorithm
        openness_traits = [
            traits.get("curiosity", 0.5),
            traits.get("creativity", 0.5),
            traits.get("open_mindedness", 0.5),
            traits.get("adventurousness", 0.5),
            traits.get("artistic_interest", 0.5),
        ]
        return sum(openness_traits) / len(openness_traits)

    def _calculate_conscientiousness(self, traits: Dict[str, Any]) -> float:
        """
        Calculate conscientiousness score from traits.

        Args:
            traits: Personality traits

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        conscientiousness_traits = [
            traits.get("organization", 0.5),
            traits.get("diligence", 0.5),
            traits.get("perfectionism", 0.5),
            traits.get("prudence", 0.5),
            traits.get("reliability", 0.5),
        ]
        return sum(conscientiousness_traits) / len(conscientiousness_traits)

    def _calculate_extraversion(self, traits: Dict[str, Any]) -> float:
        """
        Calculate extraversion score from traits.

        Args:
            traits: Personality traits

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        extraversion_traits = [
            traits.get("sociability", 0.5),
            traits.get("assertiveness", 0.5),
            traits.get("energy_level", 0.5),
            traits.get("excitement_seeking", 0.5),
            traits.get("cheerfulness", 0.5),
        ]
        return sum(extraversion_traits) / len(extraversion_traits)

    def _calculate_agreeableness(self, traits: Dict[str, Any]) -> float:
        """
        Calculate agreeableness score from traits.

        Args:
            traits: Personality traits

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        agreeableness_traits = [
            traits.get("trust", 0.5),
            traits.get("altruism", 0.5),
            traits.get("cooperation", 0.5),
            traits.get("modesty", 0.5),
            traits.get("sympathy", 0.5),
        ]
        return sum(agreeableness_traits) / len(agreeableness_traits)

    def _calculate_neuroticism(self, traits: Dict[str, Any]) -> float:
        """
        Calculate neuroticism score from traits.

        Args:
            traits: Personality traits

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        neuroticism_traits = [
            traits.get("anxiety", 0.5),
            traits.get("depression", 0.5),
            traits.get("emotional_volatility", 0.5),
            traits.get("vulnerability", 0.5),
            traits.get("self_consciousness", 0.5),
        ]
        return sum(neuroticism_traits) / len(neuroticism_traits)

    def _calculate_formality(self, traits: Dict[str, Any]) -> float:
        """
        Calculate formality score from traits.

        Args:
            traits: Personality traits

        Returns:
            Formality score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        formality_traits = [
            traits.get("conscientiousness", 0.5),
            traits.get("professionalism", 0.5),
            traits.get("seriousness", 0.5),
        ]
        return sum(formality_traits) / len(formality_traits)

    def _calculate_verbosity(self, traits: Dict[str, Any]) -> float:
        """
        Calculate verbosity score from traits.

        Args:
            traits: Personality traits

        Returns:
            Verbosity score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        verbosity_traits = [
            traits.get("extraversion", 0.5),
            traits.get("openness", 0.5),
            traits.get("talkativeness", 0.5),
        ]
        return sum(verbosity_traits) / len(verbosity_traits)

    def _calculate_emotionality(self, traits: Dict[str, Any]) -> float:
        """
        Calculate emotionality score from traits.

        Args:
            traits: Personality traits

        Returns:
            Emotionality score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        emotionality_traits = [
            traits.get("neuroticism", 0.5),
            traits.get("emotional_expressiveness", 0.5),
            traits.get("empathy", 0.5),
        ]
        return sum(emotionality_traits) / len(emotionality_traits)

    def _calculate_assertiveness(self, traits: Dict[str, Any]) -> float:
        """
        Calculate assertiveness score from traits.

        Args:
            traits: Personality traits

        Returns:
            Assertiveness score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        assertiveness_traits = [
            traits.get("extraversion", 0.5),
            traits.get("confidence", 0.5),
            traits.get("dominance", 0.5),
        ]
        return sum(assertiveness_traits) / len(assertiveness_traits)

    def _calculate_humor(self, traits: Dict[str, Any]) -> float:
        """
        Calculate humor score from traits.

        Args:
            traits: Personality traits

        Returns:
            Humor score (0.0 to 1.0)
        """
        # This is a placeholder implementation
        humor_traits = [
            traits.get("playfulness", 0.5),
            traits.get("creativity", 0.5),
            traits.get("cheerfulness", 0.5),
        ]
        return sum(humor_traits) / len(humor_traits)