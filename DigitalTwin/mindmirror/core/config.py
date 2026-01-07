"""Configuration management for MindMirror."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration for MindMirror."""
    
    def __init__(self, config_dir: str = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                        Defaults to 'config' in project root.
        """
        if config_dir is None:
            # Default to 'config' directory in project root
            self.config_dir = Path(__file__).parents[2] / 'config'
        else:
            self.config_dir = Path(config_dir)
            
        self.configs: Dict[str, Any] = {}
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """Load all YAML configuration files from the config directory."""
        if not self.config_dir.exists():
            os.makedirs(self.config_dir)
            
        for config_file in self.config_dir.glob('*.yaml'):
            config_name = config_file.stem
            with open(config_file, 'r') as f:
                self.configs[config_name] = yaml.safe_load(f)
    
    def get_config(self, name: str) -> Dict[str, Any]:
        """Get a specific configuration by name.
        
        Args:
            name: Name of the configuration to retrieve.
            
        Returns:
            The configuration dictionary.
            
        Raises:
            KeyError: If the configuration does not exist.
        """
        if name not in self.configs:
            raise KeyError(f"Configuration '{name}' not found")
        return self.configs[name]
    
    def get_value(self, config_name: str, path: str, default: Any = None) -> Any:
        """Get a specific configuration value using dot notation path.
        
        Args:
            config_name: Name of the configuration.
            path: Dot-separated path to the configuration value.
            default: Default value to return if path does not exist.
            
        Returns:
            The configuration value or default if not found.
        """
        try:
            config = self.get_config(config_name)
        except KeyError:
            return default
            
        parts = path.split('.')
        
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
                
        return config
    
    def update_config(self, name: str, updates: Dict[str, Any]) -> None:
        """Update a configuration and save it to disk.
        
        Args:
            name: Name of the configuration to update.
            updates: Dictionary of updates to apply.
            
        Raises:
            KeyError: If the configuration does not exist.
        """
        if name not in self.configs:
            raise KeyError(f"Configuration '{name}' not found")
            
        # Update in memory
        self.configs[name].update(updates)
        
        # Write to disk
        config_path = self.config_dir / f"{name}.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(self.configs[name], f, default_flow_style=False)

# Global instance
config_manager = ConfigManager()