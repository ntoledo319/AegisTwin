"""
Configuration management for the Digital Twin.

This module provides functionality for loading, validating, and accessing
configuration settings for the Digital Twin components.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class DigitalTwinConfig:
    """
    Configuration manager for Digital Twin components.
    """

    _instance = None

    def __new__(cls):
        """
        Singleton pattern to ensure only one config instance exists.
        """
        if cls._instance is None:
            cls._instance = super(DigitalTwinConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the configuration manager.
        """
        if self._initialized:
            return

        self.config = {}
        self.config_path = os.environ.get("DIGITAL_TWIN_CONFIG_PATH", "config/digital_twin.yaml")
        self.load_config()
        self._initialized = True
        logger.info("Digital Twin configuration initialized")

    def load_config(self) -> None:
        """
        Load configuration from file.
        """
        try:
            # Try to load from YAML file
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            logger.warning("Using default configuration")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "personality_engine": {
                "learning_rate": 0.1,
                "stability_factors": {
                    "openness": 0.5,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.6,
                    "neuroticism": 0.5
                },
                "alignment_strength": 0.7
            },
            "memory_system": {
                "episodic_memory_dir": "data/memories/episodic",
                "semantic_memory_dir": "data/memories/semantic",
                "procedural_memory_dir": "data/memories/procedural",
                "index_dir": "data/memories/index",
                "consolidation_interval": 86400,  # 24 hours in seconds
                "importance_threshold": 0.5
            },
            "conversation_engine": {
                "max_context_history": 10,
                "max_topics_history": 5,
                "max_entities_history": 20,
                "max_intents_history": 5,
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "nlp": {
                "nlp_provider": "spacy",
                "nlp_model": "en_core_web_sm"
            },
            "spidermind_integration": {
                "pattern_hydra_enabled": True,
                "quantum_profile_enabled": True
            },
            "api": {
                "rate_limit": 100,  # requests per minute
                "timeout": 30,  # seconds
                "max_request_size": 10485760  # 10 MB
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/digital_twin.log"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if "." in key:
            # Handle nested keys
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            # Handle top-level keys
            return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Configuration value
        """
        if "." in key:
            # Handle nested keys
            parts = key.split(".")
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            # Handle top-level keys
            self.config[key] = value

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save to YAML file
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
                
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Section name

        Returns:
            Section dictionary
        """
        return self.config.get(section, {})

    def validate(self) -> bool:
        """
        Validate the configuration.

        Returns:
            True if valid, False otherwise
        """
        # This is a placeholder for configuration validation
        # In a real implementation, this would check for required values,
        # value types, ranges, etc.
        return True


# Create a singleton instance
config = DigitalTwinConfig()


def get_config() -> DigitalTwinConfig:
    """
    Get the configuration instance.

    Returns:
        Configuration instance
    """
    return config