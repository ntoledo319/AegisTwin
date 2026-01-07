"""
Hinge Connector for CogniLink

This module provides functionality to import data from Hinge exports,
including profile information, matches, messages, and app usage.
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

class HingeConnector(BaseConnector):
    """
    Connector for importing Hinge data.
    
    This class handles extraction of profile information, matches, messages,
    and app usage from Hinge data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Hinge connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "hinge"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Hinge data export file.
        
        Args:
            file_path: Path to the Hinge data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["profile", "matches", "messages"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["profile", "matches", "messages", "usage"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_hinge_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_hinge_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_hinge_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Hinge data export directory.
        
        Args:
            directory_path: Path to the Hinge data export directory
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
                    logger.error(f"Error loading Hinge profile data: {str(e)}")
            
            # Try alternate location
            profile_path = os.path.join(directory_path, "account", "profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Hinge profile data: {str(e)}")
        
        # Extract matches
        if "matches" in data_types:
            matches_path = os.path.join(directory_path, "matches.json")
            if os.path.exists(matches_path):
                yield from self._extract_matches(matches_path)
            
            # Try alternate location
            matches_path = os.path.join(directory_path, "connections", "matches.json")
            if os.path.exists(matches_path):
                yield from self._extract_matches(matches_path)
        
        # Extract messages
        if "messages" in data_types:
            messages_path = os.path.join(directory_path, "messages.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages(messages_path)
            
            # Try alternate location
            messages_path = os.path.join(directory_path, "connections", "messages.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages(messages_path)
        
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
            # Create normalized profile data
            profile = {
                'id': f"hinge_profile_{generate_message_id(profile_data)}",
                'name': profile_data.get('name', ''),
                'gender': profile_data.get('gender', ''),
                'birth_date': profile_data.get('birth_date', ''),
                'email': profile_data.get('email', ''),
                'phone': profile_data.get('phone_number', ''),
                'location': profile_data.get('location', {}).get('city', ''),
                'preferences': profile_data.get('preferences', {}),
                'prompts': profile_data.get('prompts', []),
                'vitals': profile_data.get('vitals', {}),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'hinge',
                'type': 'profile',
                'source': 'hinge_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Hinge profile: {str(e)}")
    
    def _extract_matches(self, matches_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract matches from a Hinge matches.json file.
        
        Args:
            matches_path: Path to the matches.json file
                
        Yields:
            Dictionaries containing normalized match data
        """
        try:
            with open(matches_path, 'r', encoding='utf-8') as f:
                matches_data = json.load(f)
            
            # Handle different Hinge export formats
            matches_list = []
            
            # Format 1: Direct list
            if isinstance(matches_data, list):
                matches_list = matches_data
            
            # Format 2: Nested under 'matches'
            elif 'matches' in matches_data:
                matches_list = matches_data.get('matches', [])
            
            logger.info(f"Found {len(matches_list)} matches in Hinge export")
            
            for match in matches_list:
                try:
                    # Parse match timestamp
                    timestamp = None
                    timestamp_str = match.get('match_date', '') or match.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized match data
                    match_data = {
                        'id': f"hinge_match_{match.get('id', '') or generate_message_id(match)}",
                        'match_id': match.get('id', ''),
                        'name': match.get('name', ''),
                        'age': match.get('age', 0),
                        'gender': match.get('gender', ''),
                        'location': match.get('location', {}).get('city', ''),
                        'match_date': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'prompts': match.get('prompts', []),
                        'vitals': match.get('vitals', {}),
                        'platform': 'hinge',
                        'type': 'match',
                        'source': 'hinge_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(match_data):
                        self.item_count += 1
                        yield match_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Hinge match: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting matches from Hinge export: {str(e)}")
    
    def _extract_messages(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Hinge messages.json file.
        
        Args:
            messages_path: Path to the messages.json file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different Hinge export formats
            conversations = []
            
            # Format 1: Direct list of conversations
            if isinstance(messages_data, list):
                conversations = messages_data
            
            # Format 2: Nested under 'conversations'
            elif 'conversations' in messages_data:
                conversations = messages_data.get('conversations', [])
            
            logger.info(f"Found {len(conversations)} conversations in Hinge export")
            
            for conversation in conversations:
                try:
                    # Get match information
                    match_id = conversation.get('match_id', '')
                    match_name = conversation.get('match_name', '')
                    
                    # Get messages
                    messages = conversation.get('messages', [])
                    
                    logger.info(f"Processing {len(messages)} messages with {match_name}")
                    
                    for message in messages:
                        try:
                            # Parse message timestamp
                            timestamp = None
                            timestamp_str = message.get('sent_date', '') or message.get('created_at', '')
                            if timestamp_str:
                                timestamp = parse_datetime(timestamp_str)
                            
                            # Determine if the message was sent by the user
                            is_sent = message.get('is_from_user', False) or message.get('sender_type', '') == 'user'
                            
                            # Create normalized message data
                            message_data = {
                                'id': f"hinge_message_{message.get('id', '') or generate_message_id(message)}",
                                'message_id': message.get('id', ''),
                                'match_id': match_id,
                                'match_name': match_name,
                                'content': message.get('text', '') or message.get('content', ''),
                                'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                'is_sent': is_sent,
                                'platform': 'hinge',
                                'type': 'message',
                                'source': 'hinge_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(message_data):
                                self.item_count += 1
                                yield message_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing Hinge message: {str(e)}")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Hinge conversation: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Hinge export: {str(e)}")
    
    def _extract_usage(self, usage_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract app usage from a Hinge app_usage.json file.
        
        Args:
            usage_path: Path to the app_usage.json file
                
        Yields:
            Dictionaries containing normalized app usage data
        """
        try:
            with open(usage_path, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
            
            # Handle different Hinge export formats
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
            
            logger.info(f"Found {len(usage_list)} app usage sessions in Hinge export")
            
            for session in usage_list:
                try:
                    # Parse session timestamps
                    start_time = None
                    end_time = None
                    
                    start_time_str = session.get('start_time', '') or session.get('started_at', '')
                    end_time_str = session.get('end_time', '') or session.get('ended_at', '')
                    
                    if start_time_str:
                        start_time = parse_datetime(start_time_str)
                    
                    if end_time_str:
                        end_time = parse_datetime(end_time_str)
                    
                    # Calculate duration in seconds
                    duration = 0
                    if start_time and end_time:
                        duration = (end_time - start_time).total_seconds()
                    elif session.get('duration_seconds', 0):
                        duration = session.get('duration_seconds', 0)
                    
                    # Create normalized app usage data
                    usage_data = {
                        'id': f"hinge_session_{generate_message_id(session)}",
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None,
                        'duration_seconds': duration,
                        'actions': session.get('actions', []),
                        'likes_sent': session.get('likes_sent', 0),
                        'passes': session.get('passes', 0),
                        'matches': session.get('matches', 0),
                        'messages_sent': session.get('messages_sent', 0),
                        'timestamp': start_time.isoformat() if start_time else datetime.now().isoformat(),
                        'platform': 'hinge',
                        'type': 'app_usage',
                        'source': 'hinge_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(usage_data):
                        self.item_count += 1
                        yield usage_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Hinge app usage session: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting app usage from Hinge export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Hinge data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item