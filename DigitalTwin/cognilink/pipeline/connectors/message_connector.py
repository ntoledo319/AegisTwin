"""
Message Connector for CogniLink

This module provides functionality to import message data from various sources
including chat exports, messaging platform APIs, and message dump files.
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Iterator, Union
from datetime import datetime
import re

from cognilink.core.utils import normalize_phone, normalize_email, generate_message_id, parse_datetime

logger = logging.getLogger(__name__)

class MessageConnector:
    """
    Connector for importing message data from various sources.
    
    This class handles the extraction and normalization of message data
    from different messaging platforms and formats.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the message connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        self.config = config or {}
        self.message_count = 0
        self.error_count = 0
        self.platform_handlers = {
            'whatsapp': self._process_whatsapp_message,
            'telegram': self._process_telegram_message,
            'signal': self._process_signal_message,
            'imessage': self._process_imessage,
            'facebook': self._process_facebook_message,
            'discord': self._process_discord_message,
            'slack': self._process_slack_message,
            'generic': self._process_generic_message
        }
    
    def extract_from_json(self, json_path: str, platform: str = 'generic') -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            platform: Messaging platform format ('whatsapp', 'telegram', etc.)
            
        Yields:
            Dictionaries containing normalized message data
        """
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            messages = []
            
            # WhatsApp format
            if platform == 'whatsapp' and isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            
            # Telegram format
            elif platform == 'telegram' and isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            
            # Signal format
            elif platform == 'signal' and isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            
            # Facebook format
            elif platform == 'facebook' and isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            
            # Discord format
            elif platform == 'discord' and isinstance(data, list):
                messages = data
            
            # Slack format
            elif platform == 'slack' and isinstance(data, list):
                messages = data
            
            # Generic format - try to detect structure
            elif isinstance(data, list):
                messages = data
            elif isinstance(data, dict) and any(k in data for k in ['messages', 'chats', 'conversations']):
                for key in ['messages', 'chats', 'conversations']:
                    if key in data:
                        messages = data[key]
                        break
            else:
                logger.error(f"Unrecognized JSON format in {json_path}")
                return
            
            logger.info(f"Processing {len(messages)} messages from JSON file as {platform} format")
            
            # Process messages based on platform
            handler = self.platform_handlers.get(platform.lower(), self._process_generic_message)
            
            for message_data in messages:
                try:
                    normalized_data = handler(message_data)
                    if normalized_data:
                        self.message_count += 1
                        yield normalized_data
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing message from JSON: {str(e)}")
            
            logger.info(f"Completed JSON processing: {self.message_count} messages extracted, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Failed to process JSON file {json_path}: {str(e)}")
    
    def extract_from_csv(self, csv_path: str, platform: str = 'generic', 
                        mapping: Dict[str, str] = None) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            platform: Messaging platform format
            mapping: Dictionary mapping CSV column names to message fields
            
        Yields:
            Dictionaries containing normalized message data
        """
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return
        
        # Default field mappings if none provided
        default_mappings = {
            'sender': ['sender', 'from', 'author', 'user', 'name'],
            'recipient': ['recipient', 'to', 'receiver'],
            'content': ['content', 'text', 'message', 'body'],
            'timestamp': ['timestamp', 'date', 'time', 'datetime'],
            'platform': ['platform', 'source', 'app'],
            'conversation_id': ['conversation_id', 'chat_id', 'thread_id']
        }
        
        field_mapping = mapping or default_mappings
        
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                # Try to detect dialect
                sample = f.read(1024)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                
                reader = csv.DictReader(f, dialect=dialect)
                headers = reader.fieldnames
                
                if not headers:
                    logger.error(f"No headers found in CSV file: {csv_path}")
                    return
                
                # Create field mapping from headers
                field_map = {}
                for field, possible_names in field_mapping.items():
                    for name in possible_names:
                        if name in headers:
                            field_map[field] = name
                            break
                
                logger.info(f"Processing messages from CSV file with mapping: {field_map}")
                
                for row in reader:
                    try:
                        message_data = {}
                        
                        # Map fields using the mapping
                        for field, csv_field in field_map.items():
                            if csv_field in row:
                                message_data[field] = row[csv_field]
                        
                        # Include all other fields as extras
                        for header in headers:
                            if header not in field_map.values():
                                message_data[header] = row[header]
                        
                        # Process based on platform
                        normalized_data = self._process_generic_message(message_data)
                        if normalized_data:
                            self.message_count += 1
                            yield normalized_data
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error processing message from CSV: {str(e)}")
                
                logger.info(f"Completed CSV processing: {self.message_count} messages extracted, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Failed to process CSV file {csv_path}: {str(e)}")
    
    def extract_from_text(self, text_path: str, platform: str = 'generic',
                         pattern: str = None) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a text file using regex patterns.
        
        Args:
            text_path: Path to the text file
            platform: Messaging platform format
            pattern: Regex pattern for extracting message components
            
        Yields:
            Dictionaries containing normalized message data
        """
        if not os.path.exists(text_path):
            logger.error(f"Text file not found: {text_path}")
            return
        
        # Default patterns for common platforms
        default_patterns = {
            'whatsapp': r'^\[?(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?(?:\s[AP]M)?)\]?\s-\s([^:]+):\s(.+)$',
            'telegram': r'^\[?(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?(?:\s[AP]M)?)\]?\s([^:]+):\s(.+)$',
            'generic': r'^\[?(\d{1,4}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?(?:\s[AP]M)?)\]?\s([^:]+):\s(.+)$'
        }
        
        # Use provided pattern or default for platform
        regex_pattern = pattern or default_patterns.get(platform.lower(), default_patterns['generic'])
        
        try:
            with open(text_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Split into lines
            lines = content.split('\n')
            
            # Compile regex
            message_pattern = re.compile(regex_pattern)
            
            # Process lines
            current_message = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts a new message
                match = message_pattern.match(line)
                
                if match:
                    # If we have a previous message, yield it
                    if current_message:
                        try:
                            normalized_data = self._process_generic_message(current_message)
                            if normalized_data:
                                self.message_count += 1
                                yield normalized_data
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing message from text: {str(e)}")
                    
                    # Start new message
                    timestamp_str, sender, content = match.groups()
                    
                    current_message = {
                        'timestamp': timestamp_str,
                        'sender': sender.strip(),
                        'content': content.strip(),
                        'platform': platform
                    }
                elif current_message:
                    # Continuation of previous message
                    current_message['content'] += f"\n{line}"
            
            # Don't forget the last message
            if current_message:
                try:
                    normalized_data = self._process_generic_message(current_message)
                    if normalized_data:
                        self.message_count += 1
                        yield normalized_data
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing message from text: {str(e)}")
            
            logger.info(f"Completed text file processing: {self.message_count} messages extracted, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Failed to process text file {text_path}: {str(e)}")
    
    def _process_generic_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a generic message into a normalized format.
        
        Args:
            message_data: Raw message data
            
        Returns:
            Normalized message data dictionary
        """
        normalized = {}
        
        # Map common field names
        field_mappings = {
            'sender': ['sender', 'from', 'author', 'user', 'name', 'from_name'],
            'sender_id': ['sender_id', 'from_id', 'author_id', 'user_id'],
            'recipient': ['recipient', 'to', 'receiver', 'to_name'],
            'recipient_id': ['recipient_id', 'to_id', 'receiver_id'],
            'content': ['content', 'text', 'message', 'body'],
            'timestamp': ['timestamp', 'date', 'time', 'datetime'],
            'platform': ['platform', 'source', 'app'],
            'conversation_id': ['conversation_id', 'chat_id', 'thread_id']
        }
        
        # Extract fields using mappings
        for target_field, source_fields in field_mappings.items():
            for field in source_fields:
                if field in message_data:
                    normalized[target_field] = message_data[field]
                    break
        
        # Ensure required fields have defaults
        normalized.setdefault('sender', 'Unknown')
        normalized.setdefault('content', '')
        normalized.setdefault('platform', 'unknown')
        
        # Process timestamp
        if 'timestamp' in normalized:
            timestamp = normalized['timestamp']
            if isinstance(timestamp, (int, float)):
                # Assume Unix timestamp
                date = datetime.fromtimestamp(timestamp)
                normalized['timestamp'] = date.isoformat()
            else:
                date = parse_datetime(str(timestamp))
                normalized['timestamp'] = date.isoformat() if date else None
        else:
            normalized['timestamp'] = None
        
        # Normalize identifiers
        if '@' in normalized.get('sender', ''):
            normalized['sender'] = normalize_email(normalized['sender'])
        elif normalized.get('sender', '').replace('+', '').replace('-', '').replace(' ', '').isdigit():
            normalized['sender'] = normalize_phone(normalized['sender'])
        
        if '@' in normalized.get('recipient', ''):
            normalized['recipient'] = normalize_email(normalized['recipient'])
        elif normalized.get('recipient', '').replace('+', '').replace('-', '').replace(' ', '').isdigit():
            normalized['recipient'] = normalize_phone(normalized['recipient'])
        
        # Generate ID if not present
        normalized['id'] = message_data.get('id') or generate_message_id(normalized)
        
        # Include any additional fields from original data
        for key, value in message_data.items():
            if key not in normalized and key not in [item for sublist in field_mappings.values() for item in sublist]:
                normalized[key] = value
        
        return normalized
    
    def _process_whatsapp_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a WhatsApp message into a normalized format.
        
        Args:
            message_data: Raw WhatsApp message data
            
        Returns:
            Normalized message data dictionary
        """
        # WhatsApp-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'whatsapp'
        
        # Handle WhatsApp-specific fields
        if 'type' in message_data:
            normalized['message_type'] = message_data['type']
        
        if 'from' in message_data and isinstance(message_data['from'], str):
            normalized['sender'] = normalize_phone(message_data['from'])
        
        return normalized
    
    def _process_telegram_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Telegram message into a normalized format.
        
        Args:
            message_data: Raw Telegram message data
            
        Returns:
            Normalized message data dictionary
        """
        # Telegram-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'telegram'
        
        # Handle Telegram-specific fields
        if 'from_id' in message_data:
            normalized['sender_id'] = message_data['from_id']
        
        if 'text' in message_data and isinstance(message_data['text'], list):
            # Telegram exports can have text as a list of text elements and entities
            text_parts = []
            for item in message_data['text']:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            normalized['content'] = ''.join(text_parts)
        
        return normalized
    
    def _process_signal_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Signal message into a normalized format.
        
        Args:
            message_data: Raw Signal message data
            
        Returns:
            Normalized message data dictionary
        """
        # Signal-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'signal'
        
        # Handle Signal-specific fields
        if 'source' in message_data:
            normalized['sender'] = normalize_phone(message_data['source'])
        
        if 'conversationId' in message_data:
            normalized['conversation_id'] = message_data['conversationId']
        
        return normalized
    
    def _process_imessage(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an iMessage into a normalized format.
        
        Args:
            message_data: Raw iMessage data
            
        Returns:
            Normalized message data dictionary
        """
        # iMessage-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'imessage'
        
        # Handle iMessage-specific fields
        if 'is_from_me' in message_data:
            normalized['is_from_me'] = bool(message_data['is_from_me'])
        
        if 'service' in message_data:
            normalized['service'] = message_data['service']
        
        return normalized
    
    def _process_facebook_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Facebook message into a normalized format.
        
        Args:
            message_data: Raw Facebook message data
            
        Returns:
            Normalized message data dictionary
        """
        # Facebook-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'facebook'
        
        # Handle Facebook-specific fields
        if 'sender_name' in message_data:
            normalized['sender'] = message_data['sender_name']
        
        if 'content' in message_data:
            normalized['content'] = message_data['content']
        
        if 'timestamp_ms' in message_data:
            timestamp = int(message_data['timestamp_ms']) / 1000  # Convert to seconds
            normalized['timestamp'] = datetime.fromtimestamp(timestamp).isoformat()
        
        return normalized
    
    def _process_discord_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Discord message into a normalized format.
        
        Args:
            message_data: Raw Discord message data
            
        Returns:
            Normalized message data dictionary
        """
        # Discord-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'discord'
        
        # Handle Discord-specific fields
        if 'author' in message_data and isinstance(message_data['author'], dict):
            if 'username' in message_data['author']:
                normalized['sender'] = message_data['author']['username']
            if 'id' in message_data['author']:
                normalized['sender_id'] = message_data['author']['id']
        
        if 'channel_id' in message_data:
            normalized['conversation_id'] = message_data['channel_id']
        
        return normalized
    
    def _process_slack_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Slack message into a normalized format.
        
        Args:
            message_data: Raw Slack message data
            
        Returns:
            Normalized message data dictionary
        """
        # Slack-specific processing
        normalized = self._process_generic_message(message_data)
        normalized['platform'] = 'slack'
        
        # Handle Slack-specific fields
        if 'user' in message_data:
            normalized['sender_id'] = message_data['user']
        
        if 'channel' in message_data:
            normalized['conversation_id'] = message_data['channel']
        
        if 'ts' in message_data:
            try:
                timestamp = float(message_data['ts'])
                normalized['timestamp'] = datetime.fromtimestamp(timestamp).isoformat()
            except (ValueError, TypeError):
                pass
        
        return normalized