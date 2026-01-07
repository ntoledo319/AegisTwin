"""
AegisTwin Configuration

Centralized configuration management for AegisTwin.

@ai_prompt: Use Config.load() to load configuration from file or environment.
@context_boundary: aegistwin/config

# AI-GENERATED 2026-01-06
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class Config:
    """
    AegisTwin configuration.
    
    Can be loaded from:
    - YAML file (aegistwin.yaml)
    - Environment variables (AEGISTWIN_*)
    - Programmatic defaults
    """
    
    # Runtime settings
    runs_dir: str = "runs"
    enable_replay: bool = True
    enable_audit: bool = True
    max_events_per_run: int = 10000
    
    # Policy settings
    policy_mode: str = "enforce"  # enforce, warn, disabled
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Storage settings
    graph_storage: Optional[str] = None
    memory_storage: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file and environment.
        
        Priority (highest to lowest):
        1. Environment variables (AEGISTWIN_*)
        2. Config file (if provided)
        3. Defaults
        """
        config = cls()
        
        # Load from file if provided
        if config_path:
            path = Path(config_path)
            if path.exists():
                config = cls._load_from_file(path)
        else:
            # Try default locations
            for default_path in ["aegistwin.yaml", "config.yaml", ".aegistwin.yaml"]:
                if Path(default_path).exists():
                    config = cls._load_from_file(Path(default_path))
                    break
        
        # Override with environment variables
        config = cls._apply_env_overrides(config)
        
        return config
    
    @classmethod
    def _load_from_file(cls, path: Path) -> "Config":
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            runs_dir=data.get("runs_dir", "runs"),
            enable_replay=data.get("enable_replay", True),
            enable_audit=data.get("enable_audit", True),
            max_events_per_run=data.get("max_events_per_run", 10000),
            policy_mode=data.get("policy_mode", "enforce"),
            api_host=data.get("api_host", "0.0.0.0"),
            api_port=data.get("api_port", 8000),
            graph_storage=data.get("graph_storage"),
            memory_storage=data.get("memory_storage"),
            log_level=data.get("log_level", "INFO"),
        )
    
    @classmethod
    def _apply_env_overrides(cls, config: "Config") -> "Config":
        """Apply environment variable overrides."""
        env_map = {
            "AEGISTWIN_RUNS_DIR": ("runs_dir", str),
            "AEGISTWIN_ENABLE_REPLAY": ("enable_replay", lambda x: x.lower() == "true"),
            "AEGISTWIN_ENABLE_AUDIT": ("enable_audit", lambda x: x.lower() == "true"),
            "AEGISTWIN_MAX_EVENTS": ("max_events_per_run", int),
            "AEGISTWIN_POLICY_MODE": ("policy_mode", str),
            "AEGISTWIN_API_HOST": ("api_host", str),
            "AEGISTWIN_API_PORT": ("api_port", int),
            "AEGISTWIN_LOG_LEVEL": ("log_level", str),
        }
        
        for env_var, (attr, converter) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                setattr(config, attr, converter(value))
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runs_dir": self.runs_dir,
            "enable_replay": self.enable_replay,
            "enable_audit": self.enable_audit,
            "max_events_per_run": self.max_events_per_run,
            "policy_mode": self.policy_mode,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "graph_storage": self.graph_storage,
            "memory_storage": self.memory_storage,
            "log_level": self.log_level,
        }
    
    def save(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
