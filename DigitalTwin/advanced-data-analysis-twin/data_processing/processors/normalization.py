"""
Normalization processor for standardizing and cleaning data.
"""

import re
import string
import unicodedata
from typing import Dict, Any, List, Optional, Union
import asyncio
import datetime
import json

from core.logging import get_logger
from core.utils import generate_id, timestamp_now

logger = get_logger(__name__)

class NormalizationProcessor:
    """
    Processor for standardizing and cleaning data.
    
    This processor provides functionality for:
    - Text normalization (case, whitespace, punctuation)
    - Date and time normalization
    - Name and address normalization
    - Email and phone number normalization
    - JSON and structured data normalization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the normalization processor.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - language: Language code (default: "en")
                - lowercase: Whether to convert text to lowercase (default: True)
                - remove_punctuation: Whether to remove punctuation (default: False)
                - remove_whitespace: Whether to normalize whitespace (default: True)
                - date_format: Output date format (default: "ISO")
                - time_format: Output time format (default: "24h")
        """
        self.config = config or {}
        self.processor_id = generate_id("normalization_processor")
        self.language = self.config.get("language", "en")
        self.lowercase = self.config.get("lowercase", True)
        self.remove_punctuation = self.config.get("remove_punctuation", False)
        self.remove_whitespace = self.config.get("remove_whitespace", True)
        self.date_format = self.config.get("date_format", "ISO")
        self.time_format = self.config.get("time_format", "24h")
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and normalize data.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Normalized data dictionary
        """
        start_time = asyncio.get_event_loop().time()
        
        # Create a copy of the input data
        normalized_data = data.copy()
        
        # Process different data types
        for key, value in data.items():
            if isinstance(value, str):
                # Normalize text
                normalized_data[key] = await self.normalize_text(value)
            elif isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
                # Normalize list of strings
                normalized_data[key] = [await self.normalize_text(item) for item in value]
            elif key.lower() in ["date", "time", "datetime", "timestamp"]:
                # Normalize date/time
                normalized_data[key] = await self.normalize_datetime(value)
            elif key.lower() in ["name", "fullname", "full_name", "person", "person_name"]:
                # Normalize name
                normalized_data[key] = await self.normalize_name(value)
            elif key.lower() in ["address", "location", "place"]:
                # Normalize address
                normalized_data[key] = await self.normalize_address(value)
            elif key.lower() in ["email", "email_address"]:
                # Normalize email
                normalized_data[key] = await self.normalize_email(value)
            elif key.lower() in ["phone", "phone_number", "telephone", "tel"]:
                # Normalize phone number
                normalized_data[key] = await self.normalize_phone(value)
            elif isinstance(value, dict):
                # Recursively normalize nested dictionaries
                normalized_data[key] = await self.process(value)
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                # Recursively normalize list of dictionaries
                normalized_data[key] = [await self.process(item) for item in value]
        
        # Add normalization metadata
        processing_time = asyncio.get_event_loop().time() - start_time
        normalized_data["_normalization_metadata"] = {
            "processor_id": self.processor_id,
            "timestamp": timestamp_now(),
            "processing_time": processing_time
        }
        
        return normalized_data
    
    async def process_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of data items.
        
        Args:
            data_list: List of data dictionaries
            
        Returns:
            List of normalized data dictionaries
        """
        results = []
        for data in data_list:
            result = await self.process(data)
            results.append(result)
        return results
    
    async def normalize_text(self, text: str) -> str:
        """
        Normalize text by standardizing case, whitespace, and punctuation.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Convert to lowercase if configured
        if self.lowercase:
            text = text.lower()
        
        # Remove punctuation if configured
        if self.remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Normalize whitespace if configured
        if self.remove_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def normalize_datetime(self, value: Union[str, int, float, datetime.datetime]) -> str:
        """
        Normalize date and time values to a standard format.
        
        Args:
            value: Date/time value as string, timestamp, or datetime object
            
        Returns:
            Normalized date/time string
        """
        if not value:
            return ""
        
        try:
            # Convert to datetime object
            dt = None
            
            if isinstance(value, datetime.datetime):
                dt = value
            elif isinstance(value, (int, float)):
                # Assume Unix timestamp
                dt = datetime.datetime.fromtimestamp(value)
            elif isinstance(value, str):
                # Try various date formats
                formats = [
                    "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
                    "%Y-%m-%dT%H:%M:%SZ",     # ISO format
                    "%Y-%m-%d %H:%M:%S",      # SQL format
                    "%Y-%m-%d %H:%M",         # SQL format without seconds
                    "%Y-%m-%d",               # Date only
                    "%d/%m/%Y %H:%M:%S",      # European format
                    "%d/%m/%Y",               # European date only
                    "%m/%d/%Y %H:%M:%S",      # US format
                    "%m/%d/%Y",               # US date only
                    "%b %d, %Y",              # Month name format
                    "%B %d, %Y",              # Full month name format
                    "%d %b %Y",               # European with month name
                    "%d %B %Y",               # European with full month name
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
            
            if dt is None:
                return value  # Return original if parsing fails
            
            # Format according to configuration
            if self.date_format == "ISO":
                return dt.isoformat()
            elif self.date_format == "US":
                if self.time_format == "24h":
                    return dt.strftime("%m/%d/%Y %H:%M:%S")
                else:
                    return dt.strftime("%m/%d/%Y %I:%M:%S %p")
            elif self.date_format == "EU":
                if self.time_format == "24h":
                    return dt.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    return dt.strftime("%d/%m/%Y %I:%M:%S %p")
            else:
                return dt.isoformat()
                
        except Exception as e:
            logger.warning(f"Failed to normalize datetime: {value}: {str(e)}")
            return str(value)
    
    async def normalize_name(self, name: str) -> str:
        """
        Normalize person names.
        
        Args:
            name: Person name
            
        Returns:
            Normalized name
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Normalize Unicode characters
        name = unicodedata.normalize('NFKC', name)
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Normalize capitalization (Title Case)
        name = name.title()
        
        # Handle special cases for name prefixes and suffixes
        prefixes = ["Mr", "Mrs", "Ms", "Dr", "Prof"]
        suffixes = ["Jr", "Sr", "Ii", "Iii", "Iv", "Phd", "Md", "Dds", "Esq"]
        
        # Fix prefixes (ensure they have periods)
        for prefix in prefixes:
            name = re.sub(rf'\b{prefix}\b', f"{prefix}.", name)
        
        # Fix suffixes (ensure they have periods)
        for suffix in suffixes:
            name = re.sub(rf'\b{suffix}\b', f"{suffix}.", name)
        
        # Handle hyphenated names
        name = re.sub(r'(\w+)-(\w+)', lambda m: f"{m.group(1).title()}-{m.group(2).title()}", name)
        
        # Handle apostrophes in names (like O'Brien)
        name = re.sub(r"(\w+)'(\w+)", lambda m: f"{m.group(1).title()}'{m.group(2).title()}", name)
        
        # Handle special cases like "Mc" and "Mac" prefixes
        name = re.sub(r'\bMc(\w)', lambda m: f"Mc{m.group(1).upper()}", name)
        name = re.sub(r'\bMac(\w)', lambda m: f"Mac{m.group(1).upper()}", name)
        
        return name
    
    async def normalize_address(self, address: str) -> str:
        """
        Normalize addresses.
        
        Args:
            address: Address string
            
        Returns:
            Normalized address
        """
        if not address or not isinstance(address, str):
            return ""
        
        # Normalize Unicode characters
        address = unicodedata.normalize('NFKC', address)
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Normalize common abbreviations
        abbreviations = {
            r'\bSt\b': 'Street',
            r'\bRd\b': 'Road',
            r'\bAve\b': 'Avenue',
            r'\bBlvd\b': 'Boulevard',
            r'\bLn\b': 'Lane',
            r'\bDr\b': 'Drive',
            r'\bCt\b': 'Court',
            r'\bPl\b': 'Place',
            r'\bTer\b': 'Terrace',
            r'\bPt\b': 'Point',
            r'\bApt\b': 'Apartment',
            r'\bSte\b': 'Suite',
            r'\bFl\b': 'Floor',
            r'\bRm\b': 'Room',
            r'\bN\b': 'North',
            r'\bS\b': 'South',
            r'\bE\b': 'East',
            r'\bW\b': 'West',
            r'\bNE\b': 'Northeast',
            r'\bNW\b': 'Northwest',
            r'\bSE\b': 'Southeast',
            r'\bSW\b': 'Southwest'
        }
        
        for abbr, full in abbreviations.items():
            address = re.sub(abbr, full, address)
        
        # Normalize capitalization for address components
        address = ' '.join(word.capitalize() if len(word) > 1 else word for word in address.split())
        
        # Handle numeric street names
        address = re.sub(r'(\d+)(St|Nd|Rd|Th)', lambda m: f"{m.group(1)}{m.group(2).lower()}", address)
        
        # Handle postal codes
        address = re.sub(r'\b(\d{5})-?(\d{4})?\b', lambda m: f"{m.group(1)}-{m.group(2)}" if m.group(2) else m.group(1), address)
        
        return address
    
    async def normalize_email(self, email: str) -> str:
        """
        Normalize email addresses.
        
        Args:
            email: Email address
            
        Returns:
            Normalized email address
        """
        if not email or not isinstance(email, str):
            return ""
        
        # Normalize Unicode characters
        email = unicodedata.normalize('NFKC', email)
        
        # Remove extra whitespace
        email = email.strip()
        
        # Convert to lowercase
        email = email.lower()
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            logger.warning(f"Invalid email format: {email}")
            return email
        
        # Handle common email domains
        domain_mapping = {
            'gmail.com': 'gmail.com',
            'googlemail.com': 'gmail.com',
            'hotmail.com': 'hotmail.com',
            'outlook.com': 'outlook.com',
            'live.com': 'outlook.com',
            'hotmail.co.uk': 'hotmail.co.uk',
            'yahoo.com': 'yahoo.com',
            'yahoo.co.uk': 'yahoo.co.uk'
        }
        
        username, domain = email.split('@', 1)
        
        # Normalize domain
        if domain.lower() in domain_mapping:
            domain = domain_mapping[domain.lower()]
        
        # Handle Gmail username normalization (dots are ignored)
        if domain.lower() == 'gmail.com':
            username = username.replace('.', '')
        
        return f"{username}@{domain}"
    
    async def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone numbers.
        
        Args:
            phone: Phone number
            
        Returns:
            Normalized phone number
        """
        if not phone or not isinstance(phone, str):
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats based on length
        if len(digits) == 10:  # US number without country code
            return f"+1 ({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':  # US number with country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        elif len(digits) > 8:  # International number
            # Try to determine country code (simplified)
            if digits.startswith('1') and len(digits) == 11:
                # US/Canada
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
            elif digits.startswith('44') and len(digits) >= 11:
                # UK
                return f"+44 {digits[2:5]} {digits[5:8]} {digits[8:]}"
            elif digits.startswith('33') and len(digits) >= 11:
                # France
                return f"+33 {digits[2:3]} {digits[3:5]} {digits[5:7]} {digits[7:9]} {digits[9:]}"
            elif digits.startswith('49') and len(digits) >= 11:
                # Germany
                return f"+49 {digits[2:5]} {digits[5:8]} {digits[8:]}"
            else:
                # Generic international format
                return f"+{digits}"
        else:
            # Return original if we can't normalize
            return phone
    
    async def normalize_json(self, json_data: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Normalize JSON data.
        
        Args:
            json_data: JSON data as string or parsed object
            
        Returns:
            Normalized JSON data as dictionary
        """
        if isinstance(json_data, str):
            try:
                # Parse JSON string
                parsed_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {str(e)}")
                return {"error": "Invalid JSON"}
        else:
            parsed_data = json_data
        
        # Normalize the parsed data
        if isinstance(parsed_data, dict):
            return await self.process(parsed_data)
        elif isinstance(parsed_data, list):
            return {"items": await self.process_batch(parsed_data)}
        else:
            return {"value": parsed_data}