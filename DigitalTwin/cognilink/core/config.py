"""
Configuration System for CogniLink

This module handles loading, validating, and accessing configuration settings
for all components of the CogniLink system.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages configuration settings for the CogniLink system.
    
    This class is responsible for loading configuration files, validating settings,
    and providing access to configuration values throughout the application.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir: Directory containing configuration files. If None, uses default.
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.configs = {}
        self.load_all_configs()
        
    def load_all_configs(self) -> None:
        """Load all configuration files from the config directory."""
        config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.yaml')]
        
        for config_file in config_files:
            config_name = os.path.splitext(config_file)[0]
            file_path = os.path.join(self.config_dir, config_file)
            try:
                with open(file_path, 'r') as f:
                    self.configs[config_name] = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_file}: {str(e)}")
                self.configs[config_name] = {}
    
    def get_config(self, section: str) -> Dict[str, Any]:
        """
        Get configuration settings for a specific section.
        
        Args:
            section: The configuration section to retrieve
            
        Returns:
            Dictionary containing configuration settings for the specified section
        """
        return self.configs.get(section, {})
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            section: The configuration section
            key: The configuration key
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        section_config = self.get_config(section)
        return section_config.get(key, default)
    
    def validate_config(self, section: str, required_keys: list) -> bool:
        """
        Validate that a configuration section contains all required keys.
        
        Args:
            section: The configuration section to validate
            required_keys: List of keys that must be present
            
        Returns:
            True if all required keys are present, False otherwise
        """
        section_config = self.get_config(section)
        missing_keys = [key for key in required_keys if key not in section_config]
        
        if missing_keys:
            logger.error(f"Configuration section '{section}' is missing required keys: {missing_keys}")
            return False
        return True
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """
        Update a configuration value in memory (does not persist to file).
        
        Args:
            section: The configuration section
            key: The configuration key to update
            value: The new value
        """
        if section not in self.configs:
            self.configs[section] = {}
        self.configs[section][key] = value
        logger.debug(f"Updated config {section}.{key} = {value}")

# Global configuration instance
config_manager = None

def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """
    Get or create the global ConfigManager instance.
    
    Args:
        config_dir: Optional directory for configuration files
        
    Returns:
        The global ConfigManager instance
    """
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager(config_dir)
    return config_manager


class Config:
    """
    User-friendly configuration interface for CogniLink.
    
    This class provides a simplified interface for accessing and modifying
    configuration settings throughout the application.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the Config.
        
        Args:
            config_dir: Directory containing configuration files. If None, uses default.
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.default_config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.configs = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all configuration files."""
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Check if config files exist, if not copy defaults
        default_files = [f for f in os.listdir(self.default_config_dir) if f.endswith('.yaml')]
        for file_name in default_files:
            target_path = os.path.join(self.config_dir, file_name)
            if not os.path.exists(target_path):
                default_path = os.path.join(self.default_config_dir, file_name)
                shutil.copy(default_path, target_path)
                logger.info(f"Created default configuration file: {target_path}")
        
        # Load all config files
        config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.yaml')]
        for config_file in config_files:
            config_name = os.path.splitext(config_file)[0]
            file_path = os.path.join(self.config_dir, config_file)
            try:
                with open(file_path, 'r') as f:
                    self.configs[config_name] = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
                self.configs[config_name] = {}
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load configuration from a specific file.
        
        Args:
            file_path: Path to the configuration file
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Configuration file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Update configs with loaded values
            for section, values in config.items():
                if section not in self.configs:
                    self.configs[section] = {}
                
                if isinstance(values, dict):
                    self.configs[section].update(values)
            
            logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
    
    def save(self) -> None:
        """Save all configuration to files."""
        os.makedirs(self.config_dir, exist_ok=True)
        
        for section, config in self.configs.items():
            file_path = os.path.join(self.config_dir, f"{section}.yaml")
            try:
                with open(file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                logger.info(f"Saved configuration to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save configuration to {file_path}: {str(e)}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if section not in self.configs:
            return default
        
        return self.configs[section].get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.configs:
            self.configs[section] = {}
        
        self.configs[section][key] = value
        logger.debug(f"Set config {section}.{key} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Configuration section name
            
        Returns:
            Dictionary containing section configuration
        """
        return self.configs.get(section, {})
    
    def get_sections(self) -> List[str]:
        """
        Get all configuration section names.
        
        Returns:
            List of section names
        """
        return list(self.configs.keys())
    
    def get_connector_config(self, connector_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific connector.
        
        Args:
            connector_name: Name of the connector
            
        Returns:
            Dictionary containing connector configuration
        """
        connectors_config = self.get_section('connectors')
        connector_config = {}
        
        # Get connector-specific configuration
        for key, value in connectors_config.items():
            if key.startswith(f"{connector_name}."):
                connector_key = key[len(f"{connector_name}."):]
                connector_config[connector_key] = value
        
        # Get common connector configuration
        for key, value in connectors_config.items():
            if not key.startswith(f"{connector_name}.") and not '.' in key:
                connector_config[key] = value
        
        return connector_config
    
    def get_analysis_config(self, analysis_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific analysis module.
        
        Args:
            analysis_name: Name of the analysis module
            
        Returns:
            Dictionary containing analysis configuration
        """
        analysis_config = self.get_section('analysis')
        module_config = {}
        
        # Get module-specific configuration
        for key, value in analysis_config.items():
            if key.startswith(f"{analysis_name}."):
                module_key = key[len(f"{analysis_name}."):]
                module_config[module_key] = value
        
        # Get common analysis configuration
        for key, value in analysis_config.items():
            if not key.startswith(f"{analysis_name}.") and not '.' in key:
                module_config[key] = value
        
        return module_config
    
    def get_interface_config(self, interface_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific interface component.
        
        Args:
            interface_name: Name of the interface component
            
        Returns:
            Dictionary containing interface configuration
        """
        interface_config = self.get_section('interface')
        component_config = {}
        
        # Get component-specific configuration
        for key, value in interface_config.items():
            if key.startswith(f"{interface_name}."):
                component_key = key[len(f"{interface_name}."):]
                component_config[component_key] = value
        
        # Get common interface configuration
        for key, value in interface_config.items():
            if not key.startswith(f"{interface_name}.") and not '.' in key:
                component_config[key] = value
        
        return component_config
    
    def reset(self) -> None:
        """Reset all configuration to defaults."""
        # Clear current configs
        self.configs = {}
        
        # Copy default config files
        default_files = [f for f in os.listdir(self.default_config_dir) if f.endswith('.yaml')]
        for file_name in default_files:
            default_path = os.path.join(self.default_config_dir, file_name)
            target_path = os.path.join(self.config_dir, file_name)
            shutil.copy(default_path, target_path)
        
        # Reload configs
        self._load_configs()
        logger.info("Reset all configuration to defaults")
    
    def reset_section(self, section: str) -> None:
        """
        Reset a configuration section to defaults.
        
        Args:
            section: Section name to reset
        """
        # Check if default config exists
        default_path = os.path.join(self.default_config_dir, f"{section}.yaml")
        if not os.path.exists(default_path):
            logger.warning(f"No default configuration found for section: {section}")
            return
        
        # Copy default config
        target_path = os.path.join(self.config_dir, f"{section}.yaml")
        shutil.copy(default_path, target_path)
        
        # Reload section
        try:
            with open(target_path, 'r') as f:
                self.configs[section] = yaml.safe_load(f) or {}
            logger.info(f"Reset configuration section: {section}")
        except Exception as e:
            logger.error(f"Failed to reload configuration section {section}: {str(e)}")
            self.configs[section] = {}