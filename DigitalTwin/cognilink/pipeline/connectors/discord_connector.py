"""
Discord Connector for CogniLink

This module provides functionality to import data from Discord exports,
including messages, channels, servers, and user information.
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

class DiscordConnector(BaseConnector):
    """
    Connector for importing Discord data.
    
    This class handles extraction of messages, channels, servers, and user information
    from Discord data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Discord connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "discord"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Discord data export file.
        
        Args:
            file_path: Path to the Discord data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["messages", "servers", "profile"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["messages", "servers", "profile", "channels", "relationships"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_discord_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_discord_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_discord_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Discord data export directory.
        
        Args:
            directory_path: Path to the Discord data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "account", "user.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Discord profile data: {str(e)}")
        
        # Extract servers
        if "servers" in data_types:
            servers_path = os.path.join(directory_path, "servers", "index.json")
            if os.path.exists(servers_path):
                yield from self._extract_servers(servers_path)
        
        # Extract channels
        if "channels" in data_types:
            channels_path = os.path.join(directory_path, "servers")
            if os.path.exists(channels_path) and os.path.isdir(channels_path):
                for server_dir in os.listdir(channels_path):
                    server_path = os.path.join(channels_path, server_dir)
                    if os.path.isdir(server_path):
                        channels_file = os.path.join(server_path, "channels.json")
                        if os.path.exists(channels_file):
                            yield from self._extract_channels(channels_file, server_dir)
        
        # Extract direct messages
        if "messages" in data_types:
            # Extract direct messages
            dm_path = os.path.join(directory_path, "messages", "index.json")
            if os.path.exists(dm_path):
                yield from self._extract_direct_messages(dm_path, directory_path)
            
            # Extract server messages
            servers_path = os.path.join(directory_path, "servers")
            if os.path.exists(servers_path) and os.path.isdir(servers_path):
                for server_dir in os.listdir(servers_path):
                    server_path = os.path.join(servers_path, server_dir)
                    if os.path.isdir(server_path):
                        channels_dir = os.path.join(server_path, "channels")
                        if os.path.exists(channels_dir) and os.path.isdir(channels_dir):
                            for channel_dir in os.listdir(channels_dir):
                                channel_path = os.path.join(channels_dir, channel_dir)
                                if os.path.isdir(channel_path):
                                    messages_file = os.path.join(channel_path, "messages.csv")
                                    if os.path.exists(messages_file):
                                        yield from self._extract_server_messages(messages_file, server_dir, channel_dir)
        
        # Extract relationships (friends, blocked users)
        if "relationships" in data_types:
            relationships_path = os.path.join(directory_path, "relationships.json")
            if os.path.exists(relationships_path):
                yield from self._extract_relationships(relationships_path)
    
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
                'id': f"discord_profile_{profile_data.get('id', '')}",
                'username': profile_data.get('username', ''),
                'discriminator': profile_data.get('discriminator', ''),
                'email': profile_data.get('email', ''),
                'phone': profile_data.get('phone', ''),
                'verified': profile_data.get('verified', False),
                'mfa_enabled': profile_data.get('mfa_enabled', False),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'discord',
                'type': 'profile',
                'source': 'discord_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Discord profile: {str(e)}")
    
    def _extract_servers(self, servers_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract servers from a Discord servers index.json file.
        
        Args:
            servers_path: Path to the servers index.json file
                
        Yields:
            Dictionaries containing normalized server data
        """
        try:
            with open(servers_path, 'r', encoding='utf-8') as f:
                servers_data = json.load(f)
            
            logger.info(f"Found {len(servers_data)} servers in Discord export")
            
            for server in servers_data:
                try:
                    # Create normalized server data
                    server_data = {
                        'id': f"discord_server_{server.get('id', '')}",
                        'name': server.get('name', ''),
                        'server_id': server.get('id', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'discord',
                        'type': 'server',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(server_data):
                        self.item_count += 1
                        yield server_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord server: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting servers from Discord export: {str(e)}")
    
    def _extract_channels(self, channels_path: str, server_id: str) -> Iterator[Dict[str, Any]]:
        """
        Extract channels from a Discord server's channels.json file.
        
        Args:
            channels_path: Path to the channels.json file
            server_id: ID of the server
                
        Yields:
            Dictionaries containing normalized channel data
        """
        try:
            with open(channels_path, 'r', encoding='utf-8') as f:
                channels_data = json.load(f)
            
            logger.info(f"Found {len(channels_data)} channels in Discord server {server_id}")
            
            for channel in channels_data:
                try:
                    # Create normalized channel data
                    channel_data = {
                        'id': f"discord_channel_{channel.get('id', '')}",
                        'name': channel.get('name', ''),
                        'channel_id': channel.get('id', ''),
                        'server_id': server_id,
                        'type': channel.get('type', 0),  # 0 = text, 2 = voice, 4 = category
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'discord',
                        'data_type': 'channel',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(channel_data):
                        self.item_count += 1
                        yield channel_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord channel: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting channels from Discord export: {str(e)}")
    
    def _extract_direct_messages(self, dm_index_path: str, base_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract direct messages from Discord export.
        
        Args:
            dm_index_path: Path to the direct messages index.json file
            base_path: Base path of the Discord export
                
        Yields:
            Dictionaries containing normalized direct message data
        """
        try:
            with open(dm_index_path, 'r', encoding='utf-8') as f:
                dm_index = json.load(f)
            
            logger.info(f"Found {len(dm_index)} direct message channels in Discord export")
            
            for dm_channel in dm_index:
                try:
                    channel_id = dm_channel.get('id', '')
                    channel_name = dm_channel.get('name', '')
                    
                    # Process messages in this DM channel
                    messages_file = os.path.join(base_path, "messages", channel_id, "messages.csv")
                    if os.path.exists(messages_file):
                        yield from self._extract_dm_messages(messages_file, channel_id, channel_name)
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord DM channel: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting direct messages from Discord export: {str(e)}")
    
    def _extract_dm_messages(self, messages_file: str, channel_id: str, channel_name: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Discord direct message CSV file.
        
        Args:
            messages_file: Path to the messages.csv file
            channel_id: ID of the DM channel
            channel_name: Name of the DM channel
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                messages = list(reader)
            
            logger.info(f"Found {len(messages)} messages in Discord DM channel {channel_name}")
            
            # Get user's ID from profile
            user_id = ''
            if self.user_info:
                user_id = self.user_info.get('id', '')
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('Timestamp', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get sender information
                    sender_id = message.get('Author ID', '')
                    sender_name = message.get('Author', '')
                    
                    # Determine if the message was sent by the user
                    is_sent = sender_id == user_id
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"discord_message_{message.get('ID', '')}",
                        'content': message.get('Contents', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender_id': sender_id,
                        'sender_name': sender_name,
                        'channel_id': channel_id,
                        'channel_name': channel_name,
                        'is_sent': is_sent,
                        'attachments': message.get('Attachments', ''),
                        'platform': 'discord',
                        'type': 'direct_message',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord DM message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Discord DM channel: {str(e)}")
    
    def _extract_server_messages(self, messages_file: str, server_id: str, channel_id: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Discord server channel CSV file.
        
        Args:
            messages_file: Path to the messages.csv file
            server_id: ID of the server
            channel_id: ID of the channel
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                messages = list(reader)
            
            logger.info(f"Found {len(messages)} messages in Discord server channel {server_id}/{channel_id}")
            
            # Get user's ID from profile
            user_id = ''
            if self.user_info:
                user_id = self.user_info.get('id', '')
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('Timestamp', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get sender information
                    sender_id = message.get('Author ID', '')
                    sender_name = message.get('Author', '')
                    
                    # Determine if the message was sent by the user
                    is_sent = sender_id == user_id
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"discord_message_{message.get('ID', '')}",
                        'content': message.get('Contents', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender_id': sender_id,
                        'sender_name': sender_name,
                        'server_id': server_id,
                        'channel_id': channel_id,
                        'is_sent': is_sent,
                        'attachments': message.get('Attachments', ''),
                        'platform': 'discord',
                        'type': 'server_message',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord server message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Discord server channel: {str(e)}")
    
    def _extract_relationships(self, relationships_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract relationships from a Discord relationships.json file.
        
        Args:
            relationships_path: Path to the relationships.json file
                
        Yields:
            Dictionaries containing normalized relationship data
        """
        try:
            with open(relationships_path, 'r', encoding='utf-8') as f:
                relationships_data = json.load(f)
            
            # Process friends
            friends = relationships_data.get('friends', [])
            logger.info(f"Found {len(friends)} friends in Discord export")
            
            for friend in friends:
                try:
                    # Create normalized friend data
                    friend_data = {
                        'id': f"discord_friend_{friend.get('id', '')}",
                        'username': friend.get('name', ''),
                        'discriminator': friend.get('discriminator', ''),
                        'user_id': friend.get('id', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'discord',
                        'type': 'friend',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(friend_data):
                        self.item_count += 1
                        yield friend_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord friend: {str(e)}")
            
            # Process blocked users
            blocked = relationships_data.get('blocked', [])
            logger.info(f"Found {len(blocked)} blocked users in Discord export")
            
            for blocked_user in blocked:
                try:
                    # Create normalized blocked user data
                    blocked_data = {
                        'id': f"discord_blocked_{blocked_user.get('id', '')}",
                        'username': blocked_user.get('name', ''),
                        'discriminator': blocked_user.get('discriminator', ''),
                        'user_id': blocked_user.get('id', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'discord',
                        'type': 'blocked_user',
                        'source': 'discord_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(blocked_data):
                        self.item_count += 1
                        yield blocked_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Discord blocked user: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting relationships from Discord export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Discord data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item