"""
Utility Functions for CogniLink

This module provides common utility functions used throughout the CogniLink system.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the logging system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger.info(f"Logging configured with level {log_level}")

def normalize_email(email: str) -> str:
    """
    Normalize an email address for consistent comparison.
    
    Args:
        email: Email address to normalize
        
    Returns:
        Normalized email address (lowercase, no whitespace)
    """
    if not email:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = email.lower().strip()
    
    # Remove any "mailto:" prefix
    if normalized.startswith("mailto:"):
        normalized = normalized[7:]
    
    return normalized

def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number for consistent comparison.
    
    Args:
        phone: Phone number to normalize
        
    Returns:
        Normalized phone number (digits only)
    """
    if not phone:
        return ""
    
    # Keep only digits
    digits_only = re.sub(r'\D', '', phone)
    
    # If it's a long number with country code, standardize format
    if len(digits_only) > 10:
        # Remove leading 1 for US/Canada numbers if present
        if digits_only.startswith('1') and len(digits_only) == 11:
            digits_only = digits_only[1:]
    
    return digits_only

def generate_message_id(message_data: Dict[str, Any]) -> str:
    """
    Generate a unique ID for a message based on its content.
    
    Args:
        message_data: Dictionary containing message data
        
    Returns:
        Unique hash ID for the message
    """
    # Create a string with key message components
    id_components = []
    
    # Add sender if available
    if 'sender' in message_data:
        id_components.append(str(message_data['sender']))
    
    # Add recipients if available
    if 'recipients' in message_data:
        if isinstance(message_data['recipients'], list):
            id_components.append(','.join(sorted(str(r) for r in message_data['recipients'])))
        else:
            id_components.append(str(message_data['recipients']))
    
    # Add timestamp if available
    if 'timestamp' in message_data:
        id_components.append(str(message_data['timestamp']))
    
    # Add subject if available
    if 'subject' in message_data:
        id_components.append(str(message_data['subject']))
    
    # Add first 100 chars of content if available
    if 'content' in message_data and message_data['content']:
        id_components.append(str(message_data['content'])[:100])
    
    # Join components and hash
    message_string = '|'.join(id_components)
    return hashlib.md5(message_string.encode('utf-8')).hexdigest()

def parse_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse a datetime string in various formats.
    
    Args:
        date_string: String representation of a date/time
        
    Returns:
        Datetime object or None if parsing fails
    """
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO format with microseconds and timezone
        '%Y-%m-%dT%H:%M:%S%z',     # ISO format with timezone
        '%Y-%m-%dT%H:%M:%S.%f',    # ISO format with microseconds
        '%Y-%m-%dT%H:%M:%S',       # ISO format
        '%Y-%m-%d %H:%M:%S',       # Common datetime format
        '%Y-%m-%d',                # Date only
        '%m/%d/%Y %H:%M:%S',       # US format with time
        '%m/%d/%Y',                # US date format
        '%d/%m/%Y %H:%M:%S',       # European format with time
        '%d/%m/%Y',                # European date format
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            # Add UTC timezone if not specified
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    logger.warning(f"Could not parse datetime string: {date_string}")
    return None

def safe_json_serialize(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable types.
    
    Args:
        obj: Object to make JSON-serializable
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

def save_json(data: Any, filepath: str, pretty: bool = True) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save the file
        pretty: Whether to format the JSON for readability
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, default=safe_json_serialize, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, default=safe_json_serialize, ensure_ascii=False)
    
    logger.debug(f"Data saved to {filepath}")

def load_json(filepath: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.debug(f"Data loaded from {filepath}")
    return data

def extract_domains(email_list: List[str]) -> Dict[str, int]:
    """
    Extract and count domains from a list of email addresses.
    
    Args:
        email_list: List of email addresses
        
    Returns:
        Dictionary mapping domains to their frequency
    """
    domains = {}
    for email in email_list:
        try:
            domain = email.split('@')[1].lower()
            domains[domain] = domains.get(domain, 0) + 1
        except (IndexError, AttributeError):
            continue
    
    return domains

def group_by_time_period(timestamps: List[datetime], period: str = 'day') -> Dict[str, int]:
    """
    Group timestamps by a specified time period.
    
    Args:
        timestamps: List of datetime objects
        period: Time period for grouping ('hour', 'day', 'week', 'month', 'year')
        
    Returns:
        Dictionary mapping period keys to counts
    """
    result = {}
    
    for dt in timestamps:
        if period == 'hour':
            key = dt.strftime('%Y-%m-%d %H:00')
        elif period == 'day':
            key = dt.strftime('%Y-%m-%d')
        elif period == 'week':
            # ISO week format: YYYY-Www
            key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
        elif period == 'month':
            key = dt.strftime('%Y-%m')
        elif period == 'year':
            key = dt.strftime('%Y')
        else:
            raise ValueError(f"Unknown period: {period}")
        
        result[key] = result.get(key, 0) + 1
    
    return result