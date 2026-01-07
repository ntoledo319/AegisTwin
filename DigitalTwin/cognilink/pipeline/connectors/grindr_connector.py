"""
Grindr Connector for CogniLink

This module provides functionality to import data from Grindr exports,
including profile information, chats, messages, and app usage.
"""

import os
import json
import logging
import zipfile
import csv
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import re

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class GrindrConnector(BaseConnector):
    """
    Connector for importing Grindr data.
    
    This class handles extraction of profile information, chats, messages,
    and app usage from Grindr data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Grindr connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "grindr"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Grindr data export file.
        
        Args:
            file_path: Path to the Grindr data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["profile", "chats", "messages"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["profile", "chats", "messages", "blocks", "favorites", "usage"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_grindr_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_grindr_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_grindr_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Grindr data export directory.
        
        Args:
            directory_path: Path to the Grindr data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, look for profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Grindr profile data: {str(e)}")
            
            # Try alternate location
            profile_path = os.path.join(directory_path, "account", "profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Grindr profile data: {str(e)}")
        
        # Extract chats
        if "chats" in data_types:
            chats_path = os.path.join(directory_path, "chats.json")
            if os.path.exists(chats_path):
                yield from self._extract_chats(chats_path)
            
            # Try alternate location
            chats_path = os.path.join(directory_path, "messages", "chats.json")
            if os.path.exists(chats_path):
                yield from self._extract_chats(chats_path)
        
        # Extract messages
        if "messages" in data_types:
            messages_dir = os.path.join(directory_path, "messages")
            if os.path.exists(messages_dir) and os.path.isdir(messages_dir):
                for file_name in os.listdir(messages_dir):
                    if file_name.endswith('.json') and file_name != 'chats.json':
                        messages_path = os.path.join(messages_dir, file_name)
                        yield from self._extract_messages(messages_path)
        
        # Extract blocks
        if "blocks" in data_types:
            blocks_path = os.path.join(directory_path, "blocks.json")
            if os.path.exists(blocks_path):
                yield from self._extract_blocks(blocks_path)
            
            # Try alternate location
            blocks_path = os.path.join(directory_path, "connections", "blocks.json")
            if os.path.exists(blocks_path):
                yield from self._extract_blocks(blocks_path)
        
        # Extract favorites
        if "favorites" in data_types:
            favorites_path = os.path.join(directory_path, "favorites.json")
            if os.path.exists(favorites_path):
                yield from self._extract_favorites(favorites_path)
            
            # Try alternate location
            favorites_path = os.path.join(directory_path, "connections", "favorites.json")
            if os.path.exists(favorites_path):
                yield from self._extract_favorites(favorites_path)
        
        # Extract app usage
        if "usage" in data_types:
            usage_path = os.path.join(directory_path, "app_usage.json")
            if os.path.exists(usage_path):
                yield from self._extract_usage(usage_path)
            
            # Try alternate location
            usage_path = os.path.join(directory_path, "activity", "app_usage.json")
            if os.path.exists(usage_path):
                yield from self._extract_usage(usage_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Handle different Grindr export formats
            display_name = ''
            age = 0
            email = ''
            
            # Format 1: Flat structure
            if 'displayName' in profile_data:
                display_name = profile_data.get('displayName', '')
                age = profile_data.get('age', 0)
                email = profile_data.get('email', '')
            
            # Format 2: Nested under 'profile'
            elif 'profile' in profile_data:
                profile = profile_data.get('profile', {})
                display_name = profile.get('displayName', '')
                age = profile.get('age', 0)
                email = profile_data.get('email', '')
            
            # Create normalized profile data
            profile = {
                'id': f"grindr_profile_{generate_message_id({'name': display_name})}",
                'display_name': display_name,
                'age': age,
                'email': email,
                'about': profile_data.get('about', '') or profile_data.get('headline', ''),
                'height': profile_data.get('height', ''),
                'weight': profile_data.get('weight', ''),
                'body_type': profile_data.get('bodyType', ''),
                'ethnicity': profile_data.get('ethnicity', ''),
                'position': profile_data.get('position', ''),
                'hiv_status': profile_data.get('hivStatus', ''),
                'last_tested': profile_data.get('lastTested', ''),
                'looking_for': profile_data.get('lookingFor', []),
                'tribes': profile_data.get('tribes', []),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'grindr',
                'type': 'profile',
                'source': 'grindr_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Grindr profile: {str(e)}")
    
    def _extract_chats(self, chats_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract chats from a Grindr chats.json file.
        
        Args:
            chats_path: Path to the chats.json file
                
        Yields:
            Dictionaries containing normalized chat data
        """
        try:
            with open(chats_path, 'r', encoding='utf-8') as f:
                chats_data = json.load(f)
            
            # Handle different Grindr export formats
            chats_list = []
            
            # Format 1: Direct list
            if isinstance(chats_data, list):
                chats_list = chats_data
            
            # Format 2: Nested under 'chats'
            elif 'chats' in chats_data:
                chats_list = chats_data.get('chats', [])
            
            logger.info(f"Found {len(chats_list)} chats in Grindr export")
            
            for chat in chats_list:
                try:
                    # Parse chat timestamps
                    created_timestamp = None
                    last_message_timestamp = None
                    
                    created_at = chat.get('createdAt', '') or chat.get('created_at', '')
                    last_message_at = chat.get('lastMessageAt', '') or chat.get('last_message_at', '')
                    
                    if created_at:
                        created_timestamp = parse_datetime(created_at)
                    
                    if last_message_at:
                        last_message_timestamp = parse_datetime(last_message_at)
                    
                    # Create normalized chat data
                    chat_data = {
                        'id': f"grindr_chat_{chat.get('id', '') or generate_message_id(chat)}",
                        'chat_id': chat.get('id', ''),
                        'display_name': chat.get('displayName', '') or chat.get('name', ''),
                        'created_at': created_timestamp.isoformat() if created_timestamp else None,
                        'last_message_at': last_message_timestamp.isoformat() if last_message_timestamp else None,
                        'unread_count': chat.get('unreadCount', 0),
                        'timestamp': created_timestamp.isoformat() if created_timestamp else datetime.now().isoformat(),
                        'platform': 'grindr',
                        'type': 'chat',
                        'source': 'grindr_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(chat_data):
                        self.item_count += 1
                        yield chat_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Grindr chat: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting chats from Grindr export: {str(e)}")
    
    def _extract_messages(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Grindr messages JSON file.
        
        Args:
            messages_path: Path to the messages JSON file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different Grindr export formats
            messages_list = []
            chat_id = ''
            
            # Try to extract chat ID from filename
            filename = os.path.basename(messages_path)
            chat_id_match = re.match(r'chat_([a-zA-Z0-9-]+)\.json', filename)
            if chat_id_match:
                chat_id = chat_id_match.group(1)
            
            # Format 1: Direct list
            if isinstance(messages_data, list):
                messages_list = messages_data
            
            # Format 2: Nested under 'messages'
            elif 'messages' in messages_data:
                messages_list = messages_data.get('messages', [])
                if 'chatId' in messages_data:
                    chat_id = messages_data.get('chatId', '')
            
            logger.info(f"Found {len(messages_list)} messages in chat {chat_id}")
            
            for message in messages_list:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('sentAt', '') or message.get('sent_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Determine if the message was sent by the user
                    is_sent = message.get('isFromMe', False) or message.get('is_from_me', False)
                    
                    # Get message content
                    content = message.get('body', '') or message.get('content', '')
                    
                    # Get message type
                    message_type = message.get('type', 'text')
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"grindr_message_{message.get('id', '') or generate_message_id(message)}",
                        'message_id': message.get('id', ''),
                        'chat_id': chat_id or message.get('chatId', ''),
                        'content': content,
                        'message_type': message_type,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'is_sent': is_sent,
                        'is_read': message.get('isRead', True) or message.get('is_read', True),
                        'platform': 'grindr',
                        'type': 'message',
                        'source': 'grindr_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Grindr message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Grindr export: {str(e)}")
    
    def _extract_blocks(self, blocks_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract blocks from a Grindr blocks.json file.
        
        Args:
            blocks_path: Path to the blocks.json file
                
        Yields:
            Dictionaries containing normalized block data
        """
        try:
            with open(blocks_path, 'r', encoding='utf-8') as f:
                blocks_data = json.load(f)
            
            # Handle different Grindr export formats
            blocks_list = []
            
            # Format 1: Direct list
            if isinstance(blocks_data, list):
                blocks_list = blocks_data
            
            # Format 2: Nested under 'blocks'
            elif 'blocks' in blocks_data:
                blocks_list = blocks_data.get('blocks', [])
            
            logger.info(f"Found {len(blocks_list)} blocks in Grindr export")
            
            for block in blocks_list:
                try:
                    # Parse block timestamp
                    timestamp = None
                    timestamp_str = block.get('blockedAt', '') or block.get('blocked_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized block data
                    block_data = {
                        'id': f"grindr_block_{block.get('id', '') or generate_message_id(block)}",
                        'block_id': block.get('id', ''),
                        'profile_id': block.get('profileId', '') or block.get('profile_id', ''),
                        'display_name': block.get('displayName', '') or block.get('name', ''),
                        'blocked_at': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'grindr',
                        'type': 'block',
                        'source': 'grindr_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(block_data):
                        self.item_count += 1
                        yield block_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Grindr block: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting blocks from Grindr export: {str(e)}")
    
    def _extract_favorites(self, favorites_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract favorites from a Grindr favorites.json file.
        
        Args:
            favorites_path: Path to the favorites.json file
                
        Yields:
            Dictionaries containing normalized favorite data
        """
        try:
            with open(favorites_path, 'r', encoding='utf-8') as f:
                favorites_data = json.load(f)
            
            # Handle different Grindr export formats
            favorites_list = []
            
            # Format 1: Direct list
            if isinstance(favorites_data, list):
                favorites_list = favorites_data
            
            # Format 2: Nested under 'favorites'
            elif 'favorites' in favorites_data:
                favorites_list = favorites_data.get('favorites', [])
            
            logger.info(f"Found {len(favorites_list)} favorites in Grindr export")
            
            for favorite in favorites_list:
                try:
                    # Parse favorite timestamp
                    timestamp = None
                    timestamp_str = favorite.get('favoritedAt', '') or favorite.get('favorited_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized favorite data
                    favorite_data = {
                        'id': f"grindr_favorite_{favorite.get('id', '') or generate_message_id(favorite)}",
                        'favorite_id': favorite.get('id', ''),
                        'profile_id': favorite.get('profileId', '') or favorite.get('profile_id', ''),
                        'display_name': favorite.get('displayName', '') or favorite.get('name', ''),
                        'favorited_at': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'grindr',
                        'type': 'favorite',
                        'source': 'grindr_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(favorite_data):
                        self.item_count += 1
                        yield favorite_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Grindr favorite: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting favorites from Grindr export: {str(e)}")
    
    def _extract_usage(self, usage_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract app usage from a Grindr app_usage.json file.
        
        Args:
            usage_path: Path to the app_usage.json file
                
        Yields:
            Dictionaries containing normalized app usage data
        """
        try:
            with open(usage_path, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
            
            # Handle different Grindr export formats
            usage_list = []
            
            # Format 1: Direct list
            if isinstance(usage_data, list):
                usage_list = usage_data
            
            # Format 2: Nested under 'app_usage'
            elif 'app_usage' in usage_data:
                usage_list = usage_data.get('app_usage', [])
            
            # Format 3: Nested under 'sessions'
            elif 'sessions' in usage_data:
                usage_list = usage_data.get('sessions', [])
            
            logger.info(f"Found {len(usage_list)} app usage sessions in Grindr export")
            
            for session in usage_list:
                try:
                    # Parse session timestamps
                    start_time = None
                    end_time = None
                    
                    start_time_str = session.get('startTime', '') or session.get('started_at', '')
                    end_time_str = session.get('endTime', '') or session.get('ended_at', '')
                    
                    if start_time_str:
                        start_time = parse_datetime(start_time_str)
                    
                    if end_time_str:
                        end_time = parse_datetime(end_time_str)
                    
                    # Calculate duration in seconds
                    duration = 0
                    if start_time and end_time:
                        duration = (end_time - start_time).total_seconds()
                    elif session.get('durationSeconds', 0):
                        duration = session.get('durationSeconds', 0)
                    
                    # Create normalized app usage data
                    usage_data = {
                        'id': f"grindr_session_{generate_message_id(session)}",
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None,
                        'duration_seconds': duration,
                        'actions': session.get('actions', []),
                        'taps_sent': session.get('tapsSent', 0),
                        'messages_sent': session.get('messagesSent', 0),
                        'profiles_viewed': session.get('profilesViewed', 0),
                        'timestamp': start_time.isoformat() if start_time else datetime.now().isoformat(),
                        'platform': 'grindr',
                        'type': 'app_usage',
                        'source': 'grindr_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(usage_data):
                        self.item_count += 1
                        yield usage_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Grindr app usage session: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting app usage from Grindr export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Grindr data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item