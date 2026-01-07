"""
Facebook/Meta Connector for CogniLink

This module provides functionality to import data from Facebook/Meta data exports,
including posts, messages, friends, and profile information.
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

class FacebookConnector(BaseConnector):
    """
    Connector for importing Facebook/Meta data.
    
    This class handles extraction of posts, messages, friends, and profile information
    from Facebook/Meta data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Facebook connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "facebook"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Facebook/Meta data export file.
        
        Args:
            file_path: Path to the Facebook/Meta data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["posts", "messages", "friends"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["posts", "messages", "friends", "profile", "photos", "events"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_facebook_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_facebook_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_facebook_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Facebook/Meta data export directory.
        
        Args:
            directory_path: Path to the Facebook/Meta data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "profile_information", "profile_information.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data.get('profile', {})
                        yield from self._extract_profile(self.user_info)
                except Exception as e:
                    logger.error(f"Error loading Facebook profile data: {str(e)}")
        
        # Extract posts
        if "posts" in data_types:
            posts_dir = os.path.join(directory_path, "posts")
            if os.path.exists(posts_dir) and os.path.isdir(posts_dir):
                # Look for posts files
                for file_name in os.listdir(posts_dir):
                    if file_name.startswith("your_posts_") and file_name.endswith(".json"):
                        posts_path = os.path.join(posts_dir, file_name)
                        yield from self._extract_posts(posts_path)
        
        # Extract messages
        if "messages" in data_types:
            messages_dir = os.path.join(directory_path, "messages", "inbox")
            if os.path.exists(messages_dir) and os.path.isdir(messages_dir):
                # Process each conversation directory
                for convo_dir in os.listdir(messages_dir):
                    convo_path = os.path.join(messages_dir, convo_dir)
                    if os.path.isdir(convo_path):
                        # Look for message files in each conversation directory
                        for file_name in os.listdir(convo_path):
                            if file_name.startswith("message_") and file_name.endswith(".json"):
                                message_path = os.path.join(convo_path, file_name)
                                yield from self._extract_messages(message_path)
        
        # Extract friends
        if "friends" in data_types:
            friends_path = os.path.join(directory_path, "friends", "friends.json")
            if os.path.exists(friends_path):
                yield from self._extract_friends(friends_path)
        
        # Extract photos
        if "photos" in data_types:
            photos_path = os.path.join(directory_path, "photos", "your_photos.json")
            if os.path.exists(photos_path):
                yield from self._extract_photos(photos_path)
        
        # Extract events
        if "events" in data_types:
            events_path = os.path.join(directory_path, "events", "your_events.json")
            if os.path.exists(events_path):
                yield from self._extract_events(events_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Get profile fields
            profile_fields = profile_data.get('profile_v2', {})
            
            # Create normalized profile data
            profile = {
                'id': f"facebook_profile_{profile_data.get('name', {}).get('full_name', '')}",
                'name': profile_data.get('name', {}).get('full_name', ''),
                'first_name': profile_data.get('name', {}).get('first_name', ''),
                'last_name': profile_data.get('name', {}).get('last_name', ''),
                'email': next((field.get('value', '') for field in profile_fields if field.get('field_name') == 'Email'), ''),
                'birthday': next((field.get('value', '') for field in profile_fields if field.get('field_name') == 'Birthday'), ''),
                'gender': next((field.get('value', '') for field in profile_fields if field.get('field_name') == 'Gender'), ''),
                'current_city': next((field.get('value', '') for field in profile_fields if field.get('field_name') == 'Current city'), ''),
                'hometown': next((field.get('value', '') for field in profile_fields if field.get('field_name') == 'Hometown'), ''),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'facebook',
                'type': 'profile',
                'source': 'facebook_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Facebook profile: {str(e)}")
    
    def _extract_posts(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from a Facebook posts JSON file.
        
        Args:
            posts_path: Path to the posts JSON file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            posts_list = posts_data.get('status_updates', [])
            logger.info(f"Found {len(posts_list)} posts in Facebook export")
            
            for post in posts_list:
                try:
                    # Parse post timestamp
                    timestamp = None
                    timestamp_str = post.get('timestamp', 0)
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Get post content
                    content = post.get('data', [{}])[0].get('post', '')
                    
                    # Get post title
                    title = post.get('title', '')
                    
                    # Get post attachments
                    attachments = post.get('attachments', [])
                    media_items = []
                    
                    for attachment in attachments:
                        data = attachment.get('data', [])
                        for item in data:
                            if 'media' in item:
                                media_items.append({
                                    'type': item.get('media', {}).get('media_type', 'photo'),
                                    'uri': item.get('media', {}).get('uri', ''),
                                    'description': item.get('media', {}).get('description', '')
                                })
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"facebook_post_{post.get('timestamp', '')}",
                        'content': content,
                        'title': title,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'media': media_items,
                        'has_media': len(media_items) > 0,
                        'platform': 'facebook',
                        'type': 'post',
                        'source': 'facebook_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Facebook post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from Facebook export: {str(e)}")
    
    def _extract_messages(self, message_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Facebook messages JSON file.
        
        Args:
            message_path: Path to the messages JSON file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(message_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Get conversation information
            participants = messages_data.get('participants', [])
            participant_names = [p.get('name', '') for p in participants]
            conversation_title = messages_data.get('title', '')
            is_group = len(participants) > 2
            
            # Get messages
            messages = messages_data.get('messages', [])
            logger.info(f"Found {len(messages)} messages in Facebook conversation '{conversation_title or ', '.join(participant_names)}'")
            
            # Get user's name from profile or participants
            user_name = ''
            if self.user_info:
                user_name = self.user_info.get('name', {}).get('full_name', '')
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_ms = message.get('timestamp_ms', 0)
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_ms) / 1000)  # Facebook stores timestamps in milliseconds
                        except (ValueError, TypeError):
                            timestamp = datetime.now()
                    
                    # Get message content
                    content = message.get('content', '')
                    
                    # Get sender information
                    sender_name = message.get('sender_name', '')
                    
                    # Determine if the message was sent by the user
                    is_sent = sender_name == user_name
                    
                    # Handle photos, videos, and other attachments
                    photos = message.get('photos', [])
                    videos = message.get('videos', [])
                    files = message.get('files', [])
                    sticker = message.get('sticker', {})
                    
                    media_items = []
                    
                    # Add photos
                    for photo in photos:
                        media_items.append({
                            'type': 'photo',
                            'uri': photo.get('uri', ''),
                            'creation_timestamp': photo.get('creation_timestamp', 0)
                        })
                    
                    # Add videos
                    for video in videos:
                        media_items.append({
                            'type': 'video',
                            'uri': video.get('uri', ''),
                            'creation_timestamp': video.get('creation_timestamp', 0)
                        })
                    
                    # Add files
                    for file in files:
                        media_items.append({
                            'type': 'file',
                            'uri': file.get('uri', ''),
                            'creation_timestamp': file.get('creation_timestamp', 0)
                        })
                    
                    # Add sticker
                    if sticker:
                        media_items.append({
                            'type': 'sticker',
                            'uri': sticker.get('uri', '')
                        })
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"facebook_msg_{message.get('timestamp_ms', '')}",
                        'conversation_id': os.path.basename(os.path.dirname(message_path)),
                        'conversation_title': conversation_title or ', '.join(participant_names),
                        'content': content,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender': sender_name,
                        'is_sent': is_sent,
                        'is_group': is_group,
                        'group_name': conversation_title if is_group else None,
                        'media': media_items,
                        'has_media': len(media_items) > 0,
                        'platform': 'facebook',
                        'type': 'message',
                        'source': 'facebook_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Facebook message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Facebook export: {str(e)}")
    
    def _extract_friends(self, friends_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract friends from a Facebook friends JSON file.
        
        Args:
            friends_path: Path to the friends JSON file
                
        Yields:
            Dictionaries containing normalized friend data
        """
        try:
            with open(friends_path, 'r', encoding='utf-8') as f:
                friends_data = json.load(f)
            
            friends_list = friends_data.get('friends', [])
            logger.info(f"Found {len(friends_list)} friends in Facebook export")
            
            for friend in friends_list:
                try:
                    # Parse friend added timestamp
                    timestamp = None
                    timestamp_str = friend.get('timestamp', 0)
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized friend data
                    friend_data = {
                        'id': f"facebook_friend_{friend.get('name', '')}",
                        'name': friend.get('name', ''),
                        'date_added': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'facebook',
                        'type': 'friend',
                        'source': 'facebook_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(friend_data):
                        self.item_count += 1
                        yield friend_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Facebook friend: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting friends from Facebook export: {str(e)}")
    
    def _extract_photos(self, photos_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract photos from a Facebook photos JSON file.
        
        Args:
            photos_path: Path to the photos JSON file
                
        Yields:
            Dictionaries containing normalized photo data
        """
        try:
            with open(photos_path, 'r', encoding='utf-8') as f:
                photos_data = json.load(f)
            
            photos_list = photos_data.get('photos', [])
            logger.info(f"Found {len(photos_list)} photos in Facebook export")
            
            for photo in photos_list:
                try:
                    # Parse photo timestamp
                    timestamp = None
                    timestamp_str = photo.get('creation_timestamp', 0)
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized photo data
                    photo_data = {
                        'id': f"facebook_photo_{photo.get('uri', '')}",
                        'uri': photo.get('uri', ''),
                        'description': photo.get('description', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'facebook',
                        'type': 'photo',
                        'source': 'facebook_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(photo_data):
                        self.item_count += 1
                        yield photo_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Facebook photo: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting photos from Facebook export: {str(e)}")
    
    def _extract_events(self, events_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract events from a Facebook events JSON file.
        
        Args:
            events_path: Path to the events JSON file
                
        Yields:
            Dictionaries containing normalized event data
        """
        try:
            with open(events_path, 'r', encoding='utf-8') as f:
                events_data = json.load(f)
            
            events_list = events_data.get('events_joined', [])
            logger.info(f"Found {len(events_list)} events in Facebook export")
            
            for event in events_list:
                try:
                    # Parse event timestamp
                    timestamp = None
                    timestamp_str = event.get('start_timestamp', 0)
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized event data
                    event_data = {
                        'id': f"facebook_event_{event.get('name', '')}",
                        'name': event.get('name', ''),
                        'description': event.get('description', ''),
                        'start_time': timestamp.isoformat() if timestamp else None,
                        'location': event.get('place', {}).get('name', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'facebook',
                        'type': 'event',
                        'source': 'facebook_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(event_data):
                        self.item_count += 1
                        yield event_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Facebook event: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting events from Facebook export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Facebook data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item