"""
Personality Trait Extractor for the Digital Twin.

This module provides the base class for extracting personality traits from
different types of user data.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PersonalityTraitExtractor(ABC):
    """
    Base class for extracting personality traits from user data.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the trait extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logger.debug(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    async def extract_traits(self, data: Any) -> Dict[str, Any]:
        """
        Extract personality traits from data.

        Args:
            data: User data

        Returns:
            Dictionary of extracted traits
        """
        pass

    def _normalize_trait_value(self, value: float) -> float:
        """
        Normalize a trait value to be between 0.0 and 1.0.

        Args:
            value: Raw trait value

        Returns:
            Normalized trait value
        """
        return max(0.0, min(1.0, value))

    def _combine_trait_values(self, values: List[float], weights: List[float] = None) -> float:
        """
        Combine multiple trait values into a single value.

        Args:
            values: List of trait values
            weights: List of weights for each value (optional)

        Returns:
            Combined trait value
        """
        if not values:
            return 0.5  # Default value

        if weights is None:
            weights = [1.0] * len(values)
        elif len(weights) != len(values):
            raise ValueError("Number of weights must match number of values")

        weighted_sum = sum(value * weight for value, weight in zip(values, weights))
        weight_sum = sum(weights)

        if weight_sum == 0:
            return 0.5  # Default value

        return self._normalize_trait_value(weighted_sum / weight_sum)