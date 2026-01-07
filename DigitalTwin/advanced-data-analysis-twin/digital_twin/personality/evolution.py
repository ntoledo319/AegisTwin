"""
Personality Evolution Engine for the Digital Twin.

This module provides functionality for evolving personality traits over time
based on new data.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PersonalityEvolutionEngine:
    """
    Engine for evolving personality traits over time.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the evolution engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.stability_factors = self.config.get("stability_factors", {})
        logger.info("Personality Evolution Engine initialized")

    async def evolve_traits(self, existing_traits: Dict[str, Any], new_traits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evolve existing traits with new traits.

        Args:
            existing_traits: Existing personality traits
            new_traits: New personality traits

        Returns:
            Updated personality traits
        """
        evolved_traits = existing_traits.copy()

        for trait_name, new_value in new_traits.items():
            # If trait doesn't exist in existing traits, add it
            if trait_name not in evolved_traits:
                evolved_traits[trait_name] = new_value
                continue

            # Get existing value
            existing_value = evolved_traits[trait_name]

            # Get stability factor for this trait (how resistant it is to change)
            stability_factor = self.stability_factors.get(trait_name, 0.5)

            # Calculate effective learning rate based on stability factor
            effective_learning_rate = self.learning_rate * (1.0 - stability_factor)

            # Evolve the trait value
            evolved_value = self._evolve_trait_value(existing_value, new_value, effective_learning_rate)

            # Update the trait
            evolved_traits[trait_name] = evolved_value

        logger.debug(f"Evolved {len(new_traits)} traits")
        return evolved_traits

    def _evolve_trait_value(self, existing_value: float, new_value: float, learning_rate: float) -> float:
        """
        Evolve a single trait value.

        Args:
            existing_value: Existing trait value
            new_value: New trait value
            learning_rate: Learning rate for evolution

        Returns:
            Evolved trait value
        """
        # Simple weighted average evolution
        evolved_value = existing_value * (1.0 - learning_rate) + new_value * learning_rate

        # Ensure value is between 0.0 and 1.0
        return max(0.0, min(1.0, evolved_value))

    def set_learning_rate(self, learning_rate: float) -> None:
        """
        Set the learning rate for trait evolution.

        Args:
            learning_rate: New learning rate (0.0 to 1.0)
        """
        self.learning_rate = max(0.0, min(1.0, learning_rate))
        logger.info(f"Learning rate set to {self.learning_rate}")

    def set_stability_factor(self, trait_name: str, stability_factor: float) -> None:
        """
        Set the stability factor for a specific trait.

        Args:
            trait_name: Name of the trait
            stability_factor: Stability factor (0.0 to 1.0)
        """
        self.stability_factors[trait_name] = max(0.0, min(1.0, stability_factor))
        logger.debug(f"Stability factor for {trait_name} set to {stability_factor}")