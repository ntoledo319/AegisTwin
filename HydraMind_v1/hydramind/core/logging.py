"""
Structured logging and metrics system for HydraMind.

Provides JSON logging, file rotation, and metrics collection.
"""

from __future__ import annotations
import logging
import logging.handlers
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        payload = {
            "ts": time.time(),
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        
        # Add exception info if present (but sanitize for security)
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            # Remove potentially sensitive information from exception traces
            # Keep only the essential error information
            lines = exc_text.split('\n')
            sanitized_lines = []
            for line in lines[:5]:  # Only include first few lines
                if not any(sensitive in line.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                    sanitized_lines.append(line)
            payload["exc_info"] = '\n'.join(sanitized_lines) if sanitized_lines else "Exception details omitted for security"
        
        # Add extra fields
        if hasattr(record, 'extra'):
            payload.update(record.extra)
            
        return json.dumps(payload, ensure_ascii=False)


class MetricsLogger:
    """
    Lightweight metrics collector that piggybacks on logging.
    
    For production systems, consider integrating with Prometheus, StatsD, etc.
    """
    
    def __init__(self, logger: logging.Logger):
        self.log = logger
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
    
    def gauge(self, name: str, value: float, **labels: Any) -> None:
        """Record a gauge metric (point-in-time value)."""
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self._gauges[key] = value
        self.log.info(
            "metric",
            extra={
                "metric_type": "gauge",
                "metric_name": name,
                "value": value,
                "labels": labels
            }
        )
    
    def counter(self, name: str, inc: float = 1.0, **labels: Any) -> None:
        """Increment a counter metric."""
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        self._counters[key] = self._counters.get(key, 0.0) + inc
        self.log.info(
            "metric",
            extra={
                "metric_type": "counter",
                "metric_name": name,
                "increment": inc,
                "total": self._counters[key],
                "labels": labels
            }
        )
    
    def histogram(self, name: str, value: float, **labels: Any) -> None:
        """Record a histogram value (for aggregation)."""
        self.log.info(
            "metric",
            extra={
                "metric_type": "histogram",
                "metric_name": name,
                "value": value,
                "labels": labels
            }
        )
    
    def get_counter(self, name: str, **labels: Any) -> float:
        """Get current counter value."""
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, **labels: Any) -> Optional[float]:
        """Get current gauge value."""
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        return self._gauges.get(key)


def setup_logging(
    level: str = "INFO",
    json_mode: bool = True,
    file_path: str = "./logs/hydramind.log",
    rotate_bytes: int = 10_000_000,
    backups: int = 5
) -> MetricsLogger:
    """
    Configure logging system with console and file handlers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_mode: Use JSON formatting for structured logs
        file_path: Path to log file
        rotate_bytes: Max bytes before rotation
        backups: Number of backup files to keep
        
    Returns:
        MetricsLogger instance for metrics collection
    """
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(root.level)
    
    if json_mode:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    
    root.addHandler(console_handler)
    
    # File handler with rotation
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=rotate_bytes,
            backupCount=backups,
            encoding="utf-8"
        )
        file_handler.setLevel(root.level)
        
        if json_mode:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
        
        root.addHandler(file_handler)
        
    except Exception as e:
        root.warning(f"Failed to setup file logging: {e}")
    
    # Create metrics logger
    metrics_logger = logging.getLogger("metrics")
    return MetricsLogger(metrics_logger)
