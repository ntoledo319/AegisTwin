"""
Configuration management for Cognitive-Twin Omega.

This module handles loading, validating, and accessing configuration settings
for the Cognitive-Twin Omega system.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict containing configuration settings
        
    Raises:
        ConfigurationError: If the configuration file cannot be loaded or is invalid
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate the configuration
        validate_config(config)
        
        # Expand paths
        config = expand_paths(config)
        
        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_path}: {str(e)}")

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration structure and required settings.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigurationError: If the configuration is invalid
    """
    # Check for required top-level sections
    required_sections = ['project', 'paths', 'data_sources', 'preprocessing', 'nlp']
    for section in required_sections:
        if section not in config:
            raise ConfigurationError(f"Missing required configuration section: {section}")
    
    # Check for required paths
    required_paths = ['raw', 'interim', 'processed', 'models', 'logs']
    for path_key in required_paths:
        if path_key not in config['paths']:
            raise ConfigurationError(f"Missing required path configuration: {path_key}")
    
    # Check for at least one enabled data source
    data_sources = config.get('data_sources', {})
    if not any(source.get('enabled', False) for source in data_sources.values()):
        logger.warning("No data sources are enabled in the configuration")

def expand_paths(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand relative paths in the configuration to absolute paths.
    
    Args:
        config: Configuration dictionary with paths to expand
        
    Returns:
        Configuration with expanded paths
    """
    # Create a deep copy to avoid modifying the original
    expanded = config.copy()
    
    # Get the base directory (where the config file is located)
    base_dir = os.getcwd()
    
    # Expand paths in the paths section
    if 'paths' in expanded:
        for key, path in expanded['paths'].items():
            if not os.path.isabs(path):
                expanded['paths'][key] = os.path.abspath(os.path.join(base_dir, path))
    
    # Expand paths in data sources
    if 'data_sources' in expanded:
        for source_type, source_config in expanded['data_sources'].items():
            if isinstance(source_config, dict) and 'formats' in source_config:
                for i, format_config in enumerate(source_config['formats']):
                    if 'path' in format_config and not os.path.isabs(format_config['path']):
                        expanded['data_sources'][source_type]['formats'][i]['path'] = \
                            os.path.abspath(os.path.join(base_dir, format_config['path']))
    
    return expanded

def load_auxiliary_config(config: Dict[str, Any], config_key: str, default_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load an auxiliary configuration file referenced in the main config.
    
    Args:
        config: Main configuration dictionary
        config_key: Key path to the auxiliary config file (dot notation)
        default_path: Default path to use if not found in config
        
    Returns:
        Auxiliary configuration dictionary
        
    Raises:
        ConfigurationError: If the auxiliary configuration cannot be loaded
    """
    # Navigate the config dictionary using the key path
    current = config
    key_parts = config_key.split('.')
    
    for part in key_parts[:-1]:
        if part not in current:
            if default_path:
                return load_config(default_path)
            raise ConfigurationError(f"Configuration key not found: {config_key}")
        current = current[part]
    
    last_key = key_parts[-1]
    if last_key not in current:
        if default_path:
            return load_config(default_path)
        raise ConfigurationError(f"Configuration key not found: {config_key}")
    
    aux_path = current[last_key]
    return load_config(aux_path)

def get_enabled_data_sources(config: Dict[str, Any]) -> List[str]:
    """
    Get a list of enabled data sources from the configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of enabled data source names
    """
    enabled_sources = []
    for source_name, source_config in config.get('data_sources', {}).items():
        if source_config.get('enabled', False):
            enabled_sources.append(source_name)
    return enabled_sources

def get_pipeline_components(config: Dict[str, Any], pipeline_key: str) -> List[str]:
    """
    Get the list of enabled pipeline components for a specific pipeline.
    
    Args:
        config: Configuration dictionary
        pipeline_key: Key for the pipeline configuration
        
    Returns:
        List of enabled component names
    """
    # Navigate to the pipeline configuration
    pipeline_parts = pipeline_key.split('.')
    current = config
    
    for part in pipeline_parts:
        if part not in current:
            return []
        current = current[part]
    
    # If it's a list, return it directly
    if isinstance(current, list):
        return current
    
    # If it's a dict with enabled flags, return enabled components
    if isinstance(current, dict):
        return [name for name, enabled in current.items() if enabled]
    
    return []

def get_model_path(config: Dict[str, Any], model_name: str) -> str:
    """
    Get the path for a specific model.
    
    Args:
        config: Configuration dictionary
        model_name: Name of the model
        
    Returns:
        Path to the model
    """
    models_dir = config['paths']['models']
    return os.path.join(models_dir, model_name)

def get_output_path(config: Dict[str, Any], output_name: str) -> str:
    """
    Get the path for a specific output file.
    
    Args:
        config: Configuration dictionary
        output_name: Name of the output
        
    Returns:
        Path to the output file
    """
    processed_dir = config['paths']['processed']
    return os.path.join(processed_dir, output_name)