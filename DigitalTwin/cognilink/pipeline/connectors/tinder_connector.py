"""
Tinder Connector for CogniLink

This module provides functionality to import data from Tinder data exports,
including matches, messages, and profile information.
"""

import os
import json
import logging
import zipfile
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime

logger = logging.getLogger(__name__)

class TinderConnector(BaseConnector):
    """
    Connector for importing Tinder data.
    
    This class handles extraction of matches, messages, and profile information
    from Tinder data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Tinder connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "tinder"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Tinder data export file.
        
        Args:
            file_path: Path to the Tinder data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["matches", "messages", "profile"])
            **kwargs: Additional arguments
            
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["matches", "messages", "profile", "usage", "swipes"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_tinder_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_tinder_directory(file_path, data_types)
        
        # Handle single JSON file (might be a specific export type)
        elif file_path.endswith('.json'):
            file_name = os.path.basename(file_path).lower()
            
            if "profile" in data_types and "profile" in file_name:
                yield from self._extract_profile(file_path)
            
            elif "matches" in data_types and "matches" in file_name:
                yield from self._extract_matches(file_path)
            
            elif "messages" in data_types and "messages" in file_name:
                yield from self._extract_messages(file_path)
            
            elif "usage" in data_types and "usage" in file_name:
                yield from self._extract_usage(file_path)
            
            elif "swipes" in data_types and "swipes" in file_name:
                yield from self._extract_swipes(file_path)
            
            else:
                logger.warning(f"Unrecognized Tinder JSON file: {file_path}")
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_tinder_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Tinder data export directory.
        
        Args:
            directory_path: Path to the Tinder data export directory
            data_types: List of data types to extract
            
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_paths = [
                os.path.join(directory_path, "data", "Profile.json"),
                os.path.join(directory_path, "Profile.json"),
                os.path.join(directory_path, "profile.json")
            ]
            
            for profile_path in profile_paths:
                if os.path.exists(profile_path):
                    yield from self._extract_profile(profile_path)
                    break
        
        # Extract matches
        if "matches" in data_types:
            matches_paths = [
                os.path.join(directory_path, "data", "Matches.json"),
                os.path.join(directory_path, "Matches.json"),
                os.path.join(directory_path, "matches.json")
            ]
            
            for matches_path in matches_paths:
                if os.path.exists(matches_path):
                    yield from self._extract_matches(matches_path)
                    break
        
        # Extract messages
        if "messages" in data_types:
            messages_paths = [
                os.path.join(directory_path, "data", "Messages.json"),
                os.path.join(directory_path, "Messages.json"),
                os.path.join(directory_path, "messages.json")
            ]
            
            for messages_path in messages_paths:
                if os.path.exists(messages_path):
                    yield from self._extract_messages(messages_path)
                    break
        
        # Extract usage data
        if "usage" in data_types:
            usage_paths = [
                os.path.join(directory_path, "data", "Usage.json"),
                os.path.join(directory_path, "Usage.json"),
                os.path.join(directory_path, "usage.json"),
                os.path.join(directory_path, "data", "AppUsage.json"),
                os.path.join(directory_path, "AppUsage.json"),
                os.path.join(directory_path, "app_usage.json")
            ]
            
            for usage_path in usage_paths:
                if os.path.exists(usage_path):
                    yield from self._extract_usage(usage_path)
                    break
        
        # Extract swipe data
        if "swipes" in data_types:
            swipes_paths = [
                os.path.join(directory_path, "data", "Swipes.json"),
                os.path.join(directory_path, "Swipes.json"),
                os.path.join(directory_path, "swipes.json"),
                os.path.join(directory_path, "data", "SwipeActivity.json"),
                os.path.join(directory_path, "SwipeActivity.json"),
                os.path.join(directory_path, "swipe_activity.json")
            ]
            
            for swipes_path in swipes_paths:
                if os.path.exists(swipes_path):
                    yield from self._extract_swipes(swipes_path)
                    break
    
    def _extract_profile(self, profile_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information from a Tinder profile JSON file.
        
        Args:
            profile_path: Path to the profile JSON file
            
        Yields:
            Normalized profile data
        """
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Store user info for later use
            self.user_info = profile_data
            
            # Handle different profile formats
            user_data = profile_data.get('user', profile_data)
            
            # Extract basic profile information
            user_id = user_data.get('_id', user_data.get('id', ''))
            name = user_data.get('name', '')
            bio = user_data.get('bio', '')
            birth_date = user_data.get('birth_date', user_data.get('birthDate', ''))
            gender = user_data.get('gender', '')
            email = user_data.get('email', '')
            phone_number = user_data.get('phone_number', '')
            
            # Parse birth date
            birth_timestamp = None
            if birth_date:
                birth_timestamp = parse_datetime(birth_date)
            
            # Extract photos
            photos = []
            if 'photos' in user_data:
                for photo in user_data['photos']:
                    url = photo.get('url', '')
                    if url:
                        photos.append(url)
            
            # Create normalized profile data
            profile = {
                'id': f"tinder_profile_{user_id}",
                'user_id': user_id,
                'name': name,
                'bio': bio,
                'birth_date': birth_timestamp.isoformat() if birth_timestamp else None,
                'gender': gender,
                'email': email,
                'phone_number': phone_number,
                'photo_count': len(photos),
                'photos': photos,
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'tinder',
                'type': 'profile',
                'source': 'tinder_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
            
            # Extract preferences if available
            if 'user_interests' in profile_data or 'user_interests' in user_data:
                interests_data = profile_data.get('user_interests', user_data.get('user_interests', {}))
                
                interests = []
                if 'selected_interests' in interests_data:
                    interests = interests_data['selected_interests']
                
                # Create normalized interests data
                interests_item = {
                    'id': f"tinder_interests_{user_id}",
                    'user_id': user_id,
                    'interests': interests,
                    'timestamp': datetime.now().isoformat(),
                    'platform': 'tinder',
                    'type': 'interests',
                    'source': 'tinder_export'
                }
                
                # Apply filters
                if self._apply_filters(interests_item):
                    self.item_count += 1
                    yield interests_item
            
            # Extract discovery settings if available
            if 'discovery_settings' in profile_data or 'discovery_settings' in user_data:
                settings_data = profile_data.get('discovery_settings', user_data.get('discovery_settings', {}))
                
                # Create normalized settings data
                settings_item = {
                    'id': f"tinder_settings_{user_id}",
                    'user_id': user_id,
                    'age_min': settings_data.get('age_min', 18),
                    'age_max': settings_data.get('age_max', 100),
                    'distance_max': settings_data.get('distance_max', 100),
                    'gender_filter': settings_data.get('gender_filter', 'all'),
                    'timestamp': datetime.now().isoformat(),
                    'platform': 'tinder',
                    'type': 'settings',
                    'source': 'tinder_export'
                }
                
                # Apply filters
                if self._apply_filters(settings_item):
                    self.item_count += 1
                    yield settings_item
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Tinder profile: {str(e)}")
    
    def _extract_matches(self, matches_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract matches from a Tinder matches JSON file.
        
        Args:
            matches_path: Path to the matches JSON file
            
        Yields:
            Dictionaries containing normalized match data
        """
        try:
            with open(matches_path, 'r', encoding='utf-8') as f:
                matches_data = json.load(f)
            
            # Handle different formats
            matches = matches_data.get('matches', matches_data)
            
            logger.info(f"Found {len(matches)} matches in {matches_path}")
            
            for match in matches:
                try:
                    match_id = match.get('_id', match.get('id', ''))
                    person_id = match.get('person', {}).get('_id', match.get('person_id', ''))
                    person_name = match.get('person', {}).get('name', match.get('person_name', ''))
                    match_date = match.get('created_date', match.get('match_date', ''))
                    
                    # Parse match date
                    timestamp = parse_datetime(match_date) if match_date else datetime.now()
                    
                    # Extract person photos
                    photos = []
                    if 'person' in match and 'photos' in match['person']:
                        for photo in match['person']['photos']:
                            url = photo.get('url', '')
                            if url:
                                photos.append(url)
                    
                    # Create normalized match data
                    match_data = {
                        'id': f"tinder_match_{match_id}",
                        'match_id': match_id,
                        'person_id': person_id,
                        'person_name': person_name,
                        'match_date': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'photo_count': len(photos),
                        'photos': photos,
                        'platform': 'tinder',
                        'type': 'match',
                        'source': 'tinder_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(match_data):
                        self.item_count += 1
                        yield match_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing match: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting matches from {matches_path}: {str(e)}")
    
    def _extract_messages(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Tinder messages JSON file.
        
        Args:
            messages_path: Path to the messages JSON file
            
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different formats
            if 'messages' in messages_data:
                # Format with all messages in one list
                messages = messages_data['messages']
                logger.info(f"Found {len(messages)} messages in {messages_path}")
                
                for message in messages:
                    try:
                        message_id = message.get('_id', message.get('id', ''))
                        match_id = message.get('match_id', '')
                        sender_id = message.get('from', message.get('sender_id', ''))
                        receiver_id = message.get('to', message.get('receiver_id', ''))
                        message_date = message.get('sent_date', message.get('timestamp', ''))
                        content = message.get('message', message.get('content', ''))
                        
                        # Parse message date
                        timestamp = parse_datetime(message_date) if message_date else datetime.now()
                        
                        # Determine if the message was sent by the user
                        is_sent = sender_id == self.user_info.get('_id', self.user_info.get('id', ''))
                        sender = 'me' if is_sent else sender_id
                        recipient = receiver_id if is_sent else 'me'
                        
                        # Create normalized message data
                        message_data = {
                            'id': f"tinder_message_{message_id}",
                            'message_id': message_id,
                            'match_id': match_id,
                            'sender': sender,
                            'recipient': recipient,
                            'content': content,
                            'sent_date': timestamp.isoformat() if timestamp else None,
                            'timestamp': timestamp.isoformat() if timestamp else None,
                            'is_sent': is_sent,
                            'platform': 'tinder',
                            'type': 'message',
                            'source': 'tinder_export'
                        }
                        
                        # Apply filters
                        if self._apply_filters(message_data):
                            self.item_count += 1
                            yield message_data
                    
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error processing message: {str(e)}")
            
            elif 'matches' in messages_data:
                # Format with messages grouped by match
                matches = messages_data['matches']
                logger.info(f"Found {len(matches)} matches with messages in {messages_path}")
                
                for match in matches:
                    match_id = match.get('_id', match.get('id', ''))
                    person_id = match.get('person', {}).get('_id', match.get('person_id', ''))
                    person_name = match.get('person', {}).get('name', match.get('person_name', ''))
                    
                    messages = match.get('messages', [])
                    logger.info(f"Found {len(messages)} messages in match with {person_name}")
                    
                    for message in messages:
                        try:
                            message_id = message.get('_id', message.get('id', ''))
                            sender_id = message.get('from', message.get('sender_id', ''))
                            message_date = message.get('sent_date', message.get('timestamp', ''))
                            content = message.get('message', message.get('content', ''))
                            
                            # Parse message date
                            timestamp = parse_datetime(message_date) if message_date else datetime.now()
                            
                            # Determine if the message was sent by the user
                            is_sent = sender_id == self.user_info.get('_id', self.user_info.get('id', ''))
                            sender = 'me' if is_sent else person_id
                            recipient = person_id if is_sent else 'me'
                            
                            # Create normalized message data
                            message_data = {
                                'id': f"tinder_message_{message_id}",
                                'message_id': message_id,
                                'match_id': match_id,
                                'sender': sender,
                                'recipient': recipient,
                                'sender_name': 'me' if is_sent else person_name,
                                'recipient_name': person_name if is_sent else 'me',
                                'content': content,
                                'sent_date': timestamp.isoformat() if timestamp else None,
                                'timestamp': timestamp.isoformat() if timestamp else None,
                                'is_sent': is_sent,
                                'platform': 'tinder',
                                'type': 'message',
                                'source': 'tinder_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(message_data):
                                self.item_count += 1
                                yield message_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing message: {str(e)}")
            
            else:
                logger.warning(f"Unrecognized messages format in {messages_path}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from {messages_path}: {str(e)}")
    
    def _extract_usage(self, usage_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract usage data from a Tinder usage JSON file.
        
        Args:
            usage_path: Path to the usage JSON file
            
        Yields:
            Dictionaries containing normalized usage data
        """
        try:
            with open(usage_path, 'r', encoding='utf-8') as f:
                usage_data = json.load(f)
            
            # Handle different formats
            app_opens = usage_data.get('app_opens', usage_data.get('app_open_events', []))
            
            logger.info(f"Found {len(app_opens)} app open events in {usage_path}")
            
            for i, event in enumerate(app_opens):
                try:
                    event_date = event.get('date', event.get('timestamp', ''))
                    
                    # Parse event date
                    timestamp = parse_datetime(event_date) if event_date else datetime.now()
                    
                    # Create normalized usage data
                    usage_item = {
                        'id': f"tinder_app_open_{i}",
                        'event_type': 'app_open',
                        'event_date': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'tinder',
                        'type': 'usage',
                        'source': 'tinder_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(usage_item):
                        self.item_count += 1
                        yield usage_item
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing app open event: {str(e)}")
            
            # Extract other usage metrics if available
            if 'usage_metrics' in usage_data:
                metrics = usage_data['usage_metrics']
                
                for metric_name, metric_value in metrics.items():
                    try:
                        # Create normalized metric data
                        metric_item = {
                            'id': f"tinder_metric_{metric_name}",
                            'metric_name': metric_name,
                            'metric_value': metric_value,
                            'timestamp': datetime.now().isoformat(),
                            'platform': 'tinder',
                            'type': 'metric',
                            'source': 'tinder_export'
                        }
                        
                        # Apply filters
                        if self._apply_filters(metric_item):
                            self.item_count += 1
                            yield metric_item
                    
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error processing usage metric: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting usage data from {usage_path}: {str(e)}")
    
    def _extract_swipes(self, swipes_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract swipe data from a Tinder swipes JSON file.
        
        Args:
            swipes_path: Path to the swipes JSON file
            
        Yields:
            Dictionaries containing normalized swipe data
        """
        try:
            with open(swipes_path, 'r', encoding='utf-8') as f:
                swipes_data = json.load(f)
            
            # Handle different formats
            swipes = swipes_data.get('swipes', swipes_data.get('swipe_activity', swipes_data))
            
            logger.info(f"Found {len(swipes)} swipe events in {swipes_path}")
            
            for i, swipe in enumerate(swipes):
                try:
                    swipe_date = swipe.get('date', swipe.get('timestamp', ''))
                    direction = swipe.get('direction', swipe.get('swipe_direction', ''))
                    person_id = swipe.get('person_id', swipe.get('user_id', ''))
                    
                    # Parse swipe date
                    timestamp = parse_datetime(swipe_date) if swipe_date else datetime.now()
                    
                    # Create normalized swipe data
                    swipe_data = {
                        'id': f"tinder_swipe_{i}",
                        'direction': direction,
                        'person_id': person_id,
                        'swipe_date': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'tinder',
                        'type': 'swipe',
                        'source': 'tinder_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(swipe_data):
                        self.item_count += 1
                        yield swipe_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing swipe: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting swipes from {swipes_path}: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
            
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Tinder data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item