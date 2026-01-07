"""
Core module for the Advanced Data Analysis & Digital Twin System.
"""

from .config import settings, get_settings, initialize_directories
from .logging import get_logger
from .utils import (
    generate_id,
    timestamp_now,
    hash_content,
    ensure_directory,
    load_json_file,
    save_json_file,
    chunk_text,
    format_duration,
    deep_merge,
    truncate_string,
)

# Initialize required directories
initialize_directories()

__all__ = [
    "settings",
    "get_settings",
    "get_logger",
    "generate_id",
    "timestamp_now",
    "hash_content",
    "ensure_directory",
    "load_json_file",
    "save_json_file",
    "chunk_text",
    "format_duration",
    "deep_merge",
    "truncate_string",
]