"""
Configuration system for HydraMind.

Supports YAML files, environment variable overrides, and runtime configuration.
Designed to be extended for any domain-specific needs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """FastAPI control plane configuration."""
    host: str = "0.0.0.0"
    port: int = 8765
    enabled: bool = False  # Control plane off by default
    cors: List[str] = field(default_factory=lambda: ["*"])
    
    def __post_init__(self):
        """Validate server configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}")


@dataclass
class LoggingConfig:
    """Logging and metrics configuration."""
    level: str = "INFO"
    json: bool = True
    file_path: str = "./logs/hydramind.log"
    rotate_bytes: int = 10_000_000
    backups: int = 5
    metrics_enabled: bool = True
    
    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            logger.warning(f"Invalid log level '{self.level}', defaulting to INFO")
            self.level = "INFO"


@dataclass
class FeatureFlags:
    """Feature toggles for optional modules and capabilities."""
    seed: bool = True
    tuner: bool = True
    replay: bool = True
    db: bool = True
    trading: bool = True
    robots: bool = True
    drones: bool = True
    anomaly: bool = True
    optimizer: bool = True
    meta_planner: bool = True


@dataclass
class BrainConfig:
    """Main configuration for HydraMind cognitive kernel."""
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # Event storage
    event_db: str = "./brain_events.sqlite"
    
    # Data layer
    snapshot_dir: str = "./snapshots"
    ring_name: str = "hydra_ring"
    ring_capacity: int = 16384
    ring_item_bytes: int = 2048
    
    # Security
    policy_allowlist: Optional[List[str]] = None
    max_events_per_sec: int = 50000
    
    # Custom configuration (for user extensions)
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.ring_capacity < 1024:
            raise ValueError("ring_capacity must be at least 1024")
        if self.ring_item_bytes < 256:
            raise ValueError("ring_item_bytes must be at least 256")


def _apply_dict(dc: Any, data: Dict[str, Any]) -> None:
    """Recursively apply dictionary data to dataclass."""
    for k, v in data.items():
        if hasattr(dc, k):
            cur = getattr(dc, k)
            if isinstance(cur, (ServerConfig, LoggingConfig, FeatureFlags)):
                if isinstance(v, dict):
                    _apply_dict(cur, v)
            elif k == "custom" and isinstance(v, dict):
                # Merge custom config
                cur.update(v)
            else:
                try:
                    setattr(dc, k, v)
                except Exception as e:
                    logger.warning(f"Failed to set config {k}: {e}")


def _env_bool(v: str) -> bool:
    """Parse environment variable as boolean."""
    return v.lower() in ("1", "true", "yes", "on", "enabled")


def load_config(path: str | Path = "./hydramind.yaml") -> BrainConfig:
    """
    Load configuration from YAML file with environment variable overrides.
    
    Environment variables follow the pattern: BRAIN_<SECTION>_<KEY>
    Examples:
        BRAIN_LOGGING_LEVEL=DEBUG
        BRAIN_FEATURES_ANOMALY=false
        BRAIN_SERVER_PORT=9000
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Loaded and validated BrainConfig
    """
    cfg = BrainConfig()
    p = Path(path)
    
    # Load YAML if exists
    if p.exists():
        try:
            data = yaml.safe_load(p.read_text()) or {}
            _apply_dict(cfg, data)
            logger.info(f"Loaded configuration from {path}")
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            logger.info("Using default configuration")
    else:
        logger.info(f"Config file {path} not found, using defaults")
    
    # Environment variable overrides
    prefix = "BRAIN_"
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
            
        parts = key[len(prefix):].lower().split("_")
        
        try:
            if parts[0] in ("server", "logging", "features"):
                target = getattr(cfg, parts[0])
                attr = "_".join(parts[1:])
            else:
                target = cfg
                attr = "_".join(parts)
            
            if not hasattr(target, attr):
                # Might be custom config
                if parts[0] == "custom":
                    cfg.custom[attr] = val
                continue
                
            cur = getattr(target, attr)
            
            # Type conversion
            if isinstance(cur, bool):
                setattr(target, attr, _env_bool(val))
            elif isinstance(cur, int):
                setattr(target, attr, int(val))
            elif isinstance(cur, float):
                setattr(target, attr, float(val))
            elif isinstance(cur, list):
                # Parse comma-separated lists
                setattr(target, attr, [v.strip() for v in val.split(",")])
            else:
                setattr(target, attr, val)
                
            logger.debug(f"Applied env override: {key}={val}")
            
        except Exception as e:
            logger.warning(f"Failed to apply env override {key}: {e}")
    
    return cfg


def save_config(cfg: BrainConfig, path: str | Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        cfg: Configuration to save
        path: Output path
    """
    from dataclasses import asdict
    
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict, handling nested dataclasses
    def convert(obj):  # type: ignore
        """Convert dataclasses to dict for YAML serialization."""
        if hasattr(obj, '__dataclass_fields__'):
            return {k: convert(v) for k, v in asdict(obj).items()}
        return obj
    
    data = convert(cfg)
    
    with open(p, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved configuration to {path}")
