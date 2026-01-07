"""
Telegram Connector for CogniLink

This module provides functionality to import data from Telegram exports,
including messages, media, contacts, and channel information.
"""

import os
import json
import logging
import zipfile
import re
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import html

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class TelegramConnector(BaseConnector):
    """
    Connector for importing Telegram data.
    
    This class handles extraction of messages, media, contacts, and channel information
    from Telegram data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Telegram connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "telegram"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Telegram data export file.
        
        Args:
            file_path: Path to the Telegram data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["messages", "contacts", "channels"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["messages", "contacts", "channels", "profile"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_telegram_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_telegram_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_telegram_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Telegram data export directory.
        
        Args:
            directory_path: Path to the Telegram data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "personal_information.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data.get('personal_information', {})
                        yield from self._extract_profile(self.user_info)
                except Exception as e:
                    logger.error(f"Error loading Telegram profile data: {str(e)}")
        
        # Extract contacts
        if "contacts" in data_types:
            contacts_path = os.path.join(directory_path, "contacts.json")
            if os.path.exists(contacts_path):
                yield from self._extract_contacts(contacts_path)
        
        # Extract messages from chats
        if "messages" in data_types:
            chats_dir = os.path.join(directory_path, "chats")
            if os.path.exists(chats_dir) and os.path.isdir(chats_dir):
                # Process each chat directory
                for chat_dir in os.listdir(chats_dir):
                    chat_path = os.path.join(chats_dir, chat_dir)
                    if os.path.isdir(chat_path):
                        # Look for result.json in each chat directory
                        result_path = os.path.join(chat_path, "result.json")
                        if os.path.exists(result_path):
                            yield from self._extract_messages(result_path)
        
        # Extract channel information
        if "channels" in data_types:
            channels_path = os.path.join(directory_path, "channels.json")
            if os.path.exists(channels_path):
                yield from self._extract_channels(channels_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Create normalized profile data
            profile = {
                'id': f"telegram_profile_{profile_data.get('user_id', '')}",
                'username': profile_data.get('username', ''),
                'first_name': profile_data.get('first_name', ''),
                'last_name': profile_data.get('last_name', ''),
                'phone_number': profile_data.get('phone_number', ''),
                'bio': profile_data.get('bio', ''),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'telegram',
                'type': 'profile',
                'source': 'telegram_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Telegram profile: {str(e)}")
    
    def _extract_contacts(self, contacts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from a Telegram contacts.json file.
        
        Args:
            contacts_path: Path to the contacts.json file
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            with open(contacts_path, 'r', encoding='utf-8') as f:
                contacts_data = json.load(f)
            
            contacts_list = contacts_data.get('contacts', {}).get('list', [])
            logger.info(f"Found {len(contacts_list)} contacts in Telegram export")
            
            for contact in contacts_list:
                try:
                    # Create normalized contact data
                    contact_data = {
                        'id': f"telegram_contact_{contact.get('user_id', '')}",
                        'first_name': contact.get('first_name', ''),
                        'last_name': contact.get('last_name', ''),
                        'phone_number': contact.get('phone_number', ''),
                        'date_added': contact.get('date', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'telegram',
                        'type': 'contact',
                        'source': 'telegram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact_data):
                        self.item_count += 1
                        yield contact_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Telegram contact: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting contacts from Telegram export: {str(e)}")
    
    def _extract_messages(self, result_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Telegram chat result.json file.
        
        Args:
            result_path: Path to the result.json file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            # Get chat information
            chat_name = chat_data.get('name', os.path.basename(os.path.dirname(result_path)))
            chat_type = chat_data.get('type', 'private')
            is_group = chat_type in ['group', 'supergroup']
            
            # Get messages
            messages = chat_data.get('messages', [])
            logger.info(f"Found {len(messages)} messages in Telegram chat '{chat_name}'")
            
            for message in messages:
                try:
                    # Skip service messages if configured to do so
                    if message.get('type') == 'service' and not self.config.get('include_service_messages', True):
                        continue
                    
                    # Parse message timestamp
                    date_str = message.get('date', '')
                    timestamp = None
                    if date_str:
                        try:
                            # Telegram uses format like "2021-01-01T12:00:00"
                            timestamp = datetime.fromisoformat(date_str)
                        except ValueError:
                            timestamp = parse_datetime(date_str)
                    
                    # Get message content
                    content = ''
                    media_type = None
                    
                    # Handle different message types
                    if message.get('type') == 'message':
                        content = message.get('text', '')
                        
                        # Handle formatted text
                        if isinstance(content, list):
                            text_parts = []
                            for part in content:
                                if isinstance(part, str):
                                    text_parts.append(part)
                                elif isinstance(part, dict):
                                    if 'text' in part:
                                        text_parts.append(part['text'])
                            content = ''.join(text_parts)
                    
                    elif message.get('type') == 'service':
                        content = message.get('action', '')
                        if isinstance(content, dict):
                            action_type = content.get('type', '')
                            if action_type == 'invite_members':
                                members = content.get('members', [])
                                member_names = [m.get('name', '') for m in members]
                                content = f"invited {', '.join(member_names)}"
                            elif action_type == 'create_group':
                                content = f"created group {content.get('title', '')}"
                    
                    # Handle media
                    if 'photo' in message:
                        media_type = 'photo'
                        if not content:
                            content = '[Photo]'
                    elif 'video' in message:
                        media_type = 'video'
                        if not content:
                            content = '[Video]'
                    elif 'voice_message' in message:
                        media_type = 'voice'
                        if not content:
                            content = '[Voice Message]'
                    elif 'file' in message:
                        media_type = 'file'
                        if not content:
                            content = f"[File: {message.get('file', {}).get('filename', 'unknown')}]"
                    
                    # Get sender information
                    from_id = message.get('from_id', '')
                    sender_name = message.get('from', 'Unknown')
                    
                    # Determine if the message was sent by the user
                    is_sent = False
                    if self.user_info:
                        user_id = self.user_info.get('user_id', '')
                        is_sent = from_id == f"user{user_id}"
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"telegram_msg_{message.get('id', '')}",
                        'chat_name': chat_name,
                        'chat_type': chat_type,
                        'content': html.unescape(content) if isinstance(content, str) else str(content),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender': 'me' if is_sent else sender_name,
                        'sender_id': from_id,
                        'is_sent': is_sent,
                        'is_group': is_group,
                        'group_name': chat_name if is_group else None,
                        'media_type': media_type,
                        'has_media': media_type is not None,
                        'platform': 'telegram',
                        'type': 'message' if message.get('type') != 'service' else 'service_message',
                        'source': 'telegram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Telegram message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Telegram export: {str(e)}")
    
    def _extract_channels(self, channels_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract channel information from a Telegram channels.json file.
        
        Args:
            channels_path: Path to the channels.json file
                
        Yields:
            Dictionaries containing normalized channel data
        """
        try:
            with open(channels_path, 'r', encoding='utf-8') as f:
                channels_data = json.load(f)
            
            channels_list = channels_data.get('channels', {}).get('list', [])
            logger.info(f"Found {len(channels_list)} channels in Telegram export")
            
            for channel in channels_list:
                try:
                    # Create normalized channel data
                    channel_data = {
                        'id': f"telegram_channel_{channel.get('id', '')}",
                        'name': channel.get('name', ''),
                        'description': channel.get('description', ''),
                        'member_count': channel.get('member_count', 0),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'telegram',
                        'type': 'channel',
                        'source': 'telegram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(channel_data):
                        self.item_count += 1
                        yield channel_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Telegram channel: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting channels from Telegram export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Telegram data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item