"""
Slack Connector for CogniLink

This module provides functionality to import data from Slack exports,
including messages, channels, users, and workspace information.
"""

import os
import json
import logging
import zipfile
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import re

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class SlackConnector(BaseConnector):
    """
    Connector for importing Slack data.
    
    This class handles extraction of messages, channels, users, and workspace information
    from Slack data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Slack connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "slack"
        self.user_info = {}
        self.users_map = {}  # Map of user IDs to user info
        self.channels_map = {}  # Map of channel IDs to channel info
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Slack data export file.
        
        Args:
            file_path: Path to the Slack data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["messages", "channels", "users"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["messages", "channels", "users", "workspace"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_slack_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_slack_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_slack_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Slack data export directory.
        
        Args:
            directory_path: Path to the Slack data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load users information for reference
        users_path = os.path.join(directory_path, "users.json")
        if os.path.exists(users_path):
            try:
                with open(users_path, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    # Create a map of user IDs to user info
                    self.users_map = {user.get('id', ''): user for user in users_data}
                    
                    # Try to identify the current user
                    for user in users_data:
                        if user.get('is_primary_owner', False) or user.get('is_owner', False):
                            self.user_info = user
                            break
            except Exception as e:
                logger.error(f"Error loading Slack users data: {str(e)}")
        
        # Load channels information for reference
        channels_path = os.path.join(directory_path, "channels.json")
        if os.path.exists(channels_path):
            try:
                with open(channels_path, 'r', encoding='utf-8') as f:
                    channels_data = json.load(f)
                    # Create a map of channel IDs to channel info
                    self.channels_map = {channel.get('id', ''): channel for channel in channels_data}
            except Exception as e:
                logger.error(f"Error loading Slack channels data: {str(e)}")
        
        # Extract workspace information
        if "workspace" in data_types:
            workspace_path = os.path.join(directory_path, "integration_logs.json")
            if os.path.exists(workspace_path):
                yield from self._extract_workspace_info(workspace_path)
        
        # Extract users
        if "users" in data_types and self.users_map:
            yield from self._extract_users(self.users_map.values())
        
        # Extract channels
        if "channels" in data_types and self.channels_map:
            yield from self._extract_channels(self.channels_map.values())
        
        # Extract messages from channels
        if "messages" in data_types:
            # Process each channel directory
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    # Check if this is a channel directory (contains JSON files with messages)
                    has_messages = False
                    for file in os.listdir(item_path):
                        if file.endswith('.json') and not file in ['integration_logs.json', 'users.json', 'channels.json']:
                            has_messages = True
                            break
                    
                    if has_messages:
                        # This is a channel directory, process messages
                        channel_id = None
                        channel_name = item
                        
                        # Try to find channel ID from the channels map
                        for cid, channel in self.channels_map.items():
                            if channel.get('name', '') == channel_name:
                                channel_id = cid
                                break
                        
                        yield from self._extract_messages(item_path, channel_id, channel_name)
    
    def _extract_workspace_info(self, workspace_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract workspace information from a Slack integration_logs.json file.
        
        Args:
            workspace_path: Path to the integration_logs.json file
                
        Yields:
            Normalized workspace data
        """
        try:
            with open(workspace_path, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
            
            # Try to extract workspace name and domain
            workspace_name = ''
            workspace_domain = ''
            
            if workspace_data and len(workspace_data) > 0:
                # Look for entries that might contain workspace info
                for entry in workspace_data:
                    if 'workspace_name' in entry:
                        workspace_name = entry.get('workspace_name', '')
                    if 'workspace_domain' in entry:
                        workspace_domain = entry.get('workspace_domain', '')
                    
                    # If we found both, break
                    if workspace_name and workspace_domain:
                        break
            
            # Create normalized workspace data
            workspace = {
                'id': f"slack_workspace_{workspace_domain}",
                'name': workspace_name,
                'domain': workspace_domain,
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'slack',
                'type': 'workspace',
                'source': 'slack_export'
            }
            
            # Apply filters
            if self._apply_filters(workspace):
                self.item_count += 1
                yield workspace
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Slack workspace info: {str(e)}")
    
    def _extract_users(self, users: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """
        Extract users from Slack users data.
        
        Args:
            users: List of user data dictionaries
                
        Yields:
            Dictionaries containing normalized user data
        """
        logger.info(f"Found {len(users)} users in Slack export")
        
        for user in users:
            try:
                # Get user profile
                profile = user.get('profile', {})
                
                # Create normalized user data
                user_data = {
                    'id': f"slack_user_{user.get('id', '')}",
                    'user_id': user.get('id', ''),
                    'name': user.get('name', ''),
                    'real_name': profile.get('real_name', ''),
                    'display_name': profile.get('display_name', ''),
                    'email': profile.get('email', ''),
                    'title': profile.get('title', ''),
                    'phone': profile.get('phone', ''),
                    'is_admin': user.get('is_admin', False),
                    'is_owner': user.get('is_owner', False),
                    'is_primary_owner': user.get('is_primary_owner', False),
                    'is_bot': user.get('is_bot', False),
                    'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                    'platform': 'slack',
                    'type': 'user',
                    'source': 'slack_export'
                }
                
                # Apply filters
                if self._apply_filters(user_data):
                    self.item_count += 1
                    yield user_data
            
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing Slack user: {str(e)}")
    
    def _extract_channels(self, channels: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """
        Extract channels from Slack channels data.
        
        Args:
            channels: List of channel data dictionaries
                
        Yields:
            Dictionaries containing normalized channel data
        """
        logger.info(f"Found {len(channels)} channels in Slack export")
        
        for channel in channels:
            try:
                # Create normalized channel data
                channel_data = {
                    'id': f"slack_channel_{channel.get('id', '')}",
                    'channel_id': channel.get('id', ''),
                    'name': channel.get('name', ''),
                    'topic': channel.get('topic', {}).get('value', ''),
                    'purpose': channel.get('purpose', {}).get('value', ''),
                    'is_private': channel.get('is_private', False),
                    'is_archived': channel.get('is_archived', False),
                    'created': self._convert_slack_timestamp(channel.get('created', 0)),
                    'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                    'platform': 'slack',
                    'type': 'channel',
                    'source': 'slack_export'
                }
                
                # Apply filters
                if self._apply_filters(channel_data):
                    self.item_count += 1
                    yield channel_data
            
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing Slack channel: {str(e)}")
    
    def _extract_messages(self, channel_path: str, channel_id: str, channel_name: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Slack channel directory.
        
        Args:
            channel_path: Path to the channel directory
            channel_id: ID of the channel
            channel_name: Name of the channel
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            # Process each JSON file in the channel directory (each file contains messages for a day)
            message_files = [f for f in os.listdir(channel_path) if f.endswith('.json')]
            message_files.sort()  # Sort to process in chronological order
            
            total_messages = 0
            
            for message_file in message_files:
                file_path = os.path.join(channel_path, message_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                    
                    total_messages += len(messages)
                    
                    for message in messages:
                        try:
                            # Skip messages without text or subtype "channel_join", etc.
                            if 'subtype' in message and message['subtype'] in ['channel_join', 'channel_leave', 'channel_archive', 'channel_unarchive']:
                                continue
                            
                            # Parse message timestamp
                            timestamp = self._convert_slack_timestamp(message.get('ts', ''))
                            
                            # Get sender information
                            sender_id = message.get('user', '')
                            sender_name = 'Unknown'
                            
                            if sender_id in self.users_map:
                                user = self.users_map[sender_id]
                                profile = user.get('profile', {})
                                sender_name = profile.get('display_name', '') or user.get('name', '')
                            
                            # Determine if the message was sent by the current user
                            is_sent = False
                            if self.user_info:
                                is_sent = sender_id == self.user_info.get('id', '')
                            
                            # Get message content
                            content = message.get('text', '')
                            
                            # Handle message attachments
                            attachments = []
                            if 'attachments' in message:
                                for attachment in message['attachments']:
                                    if 'fallback' in attachment:
                                        attachments.append(attachment['fallback'])
                            
                            # Handle message files
                            files = []
                            if 'files' in message:
                                for file in message['files']:
                                    files.append({
                                        'id': file.get('id', ''),
                                        'name': file.get('name', ''),
                                        'type': file.get('filetype', ''),
                                        'url': file.get('url_private', '')
                                    })
                            
                            # Handle message reactions
                            reactions = []
                            if 'reactions' in message:
                                for reaction in message['reactions']:
                                    reactions.append({
                                        'name': reaction.get('name', ''),
                                        'count': reaction.get('count', 0),
                                        'users': reaction.get('users', [])
                                    })
                            
                            # Create normalized message data
                            message_data = {
                                'id': f"slack_message_{message.get('ts', '').replace('.', '_')}",
                                'content': content,
                                'timestamp': timestamp,
                                'sender_id': sender_id,
                                'sender_name': sender_name,
                                'channel_id': channel_id,
                                'channel_name': channel_name,
                                'is_sent': is_sent,
                                'attachments': attachments,
                                'files': files,
                                'reactions': reactions,
                                'thread_ts': message.get('thread_ts', ''),
                                'is_thread_reply': 'thread_ts' in message and message.get('thread_ts', '') != message.get('ts', ''),
                                'platform': 'slack',
                                'type': 'message',
                                'source': 'slack_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(message_data):
                                self.item_count += 1
                                yield message_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing Slack message: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error processing Slack message file {file_path}: {str(e)}")
            
            logger.info(f"Processed {total_messages} messages from Slack channel {channel_name}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Slack channel {channel_name}: {str(e)}")
    
    def _convert_slack_timestamp(self, ts: str) -> str:
        """
        Convert a Slack timestamp to an ISO format datetime string.
        
        Args:
            ts: Slack timestamp (e.g., "1234567890.123456")
                
        Returns:
            ISO format datetime string
        """
        try:
            if not ts:
                return datetime.now().isoformat()
            
            # Slack timestamps are in the format "1234567890.123456"
            # The part before the dot is Unix time in seconds
            timestamp = float(ts.split('.')[0])
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat()
        except (ValueError, TypeError):
            return datetime.now().isoformat()
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Slack data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item