"""
Configuration management for the integrated system.
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager for the integrated system."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from files and environment variables."""
        # Load base configuration
        self._load_yaml_config('config/base.yaml')
        
        # Load environment-specific configuration
        env = os.getenv('ENVIRONMENT', 'development')
        self._load_yaml_config(f'config/{env}.yaml')
        
        # Override with environment variables
        self._load_env_vars()
        
    def _load_yaml_config(self, path):
        """Load configuration from YAML file."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                self._merge_config(config)
                
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # Environment variables override file configuration
        for key, value in os.environ.items():
            if key.startswith('APP_'):
                # Convert APP_DATABASE_HOST to database.host
                config_key = key[4:].lower().replace('_', '.')
                self._set_nested_key(config_key, value)
                
    def _merge_config(self, config, prefix=''):
        """Merge configuration dictionary."""
        if not config:
            return
            
        for key, value in config.items():
            if isinstance(value, dict):
                self._merge_config(value, f"{prefix}{key}.")
            else:
                self._set_nested_key(f"{prefix}{key}", value)
                
    def _set_nested_key(self, key, value):
        """Set nested key in configuration."""
        keys = key.split('.')
        current = self.config
        
        # Navigate to the last level
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
            
        # Set the value
        current[keys[-1]] = value
        
    def get(self, key, default=None):
        """Get configuration value."""
        keys = key.split('.')
        current = self.config
        
        # Navigate to the requested level
        for k in keys:
            if k not in current:
                return default
            current = current[k]
            
        return current

# Create singleton instance
config = Config()