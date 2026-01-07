"""
Instagram Connector for CogniLink

This module provides functionality to import data from Instagram exports,
including posts, direct messages, profile information, and activity.
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

class InstagramConnector(BaseConnector):
    """
    Connector for importing Instagram data.
    
    This class handles extraction of posts, direct messages, profile information,
    and activity from Instagram data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Instagram connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "instagram"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from an Instagram data export file.
        
        Args:
            file_path: Path to the Instagram data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["posts", "messages", "profile"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["posts", "messages", "profile", "comments", "followers", "following", "stories"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_instagram_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_instagram_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_instagram_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process an Instagram data export directory.
        
        Args:
            directory_path: Path to the Instagram data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "personal_information", "personal_information.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Instagram profile data: {str(e)}")
        
        # Extract posts
        if "posts" in data_types:
            posts_path = os.path.join(directory_path, "content", "posts_1.json")
            if os.path.exists(posts_path):
                yield from self._extract_posts(posts_path)
            else:
                # Try alternate location
                posts_dir = os.path.join(directory_path, "posts")
                if os.path.exists(posts_dir) and os.path.isdir(posts_dir):
                    for file_name in os.listdir(posts_dir):
                        if file_name.endswith(".json"):
                            posts_path = os.path.join(posts_dir, file_name)
                            yield from self._extract_posts(posts_path)
        
        # Extract direct messages
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
        
        # Extract comments
        if "comments" in data_types:
            comments_path = os.path.join(directory_path, "comments", "comments.json")
            if os.path.exists(comments_path):
                yield from self._extract_comments(comments_path)
        
        # Extract followers
        if "followers" in data_types:
            followers_path = os.path.join(directory_path, "followers_and_following", "followers.json")
            if os.path.exists(followers_path):
                yield from self._extract_followers(followers_path)
        
        # Extract following
        if "following" in data_types:
            following_path = os.path.join(directory_path, "followers_and_following", "following.json")
            if os.path.exists(following_path):
                yield from self._extract_following(following_path)
        
        # Extract stories
        if "stories" in data_types:
            stories_path = os.path.join(directory_path, "content", "stories.json")
            if os.path.exists(stories_path):
                yield from self._extract_stories(stories_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Get profile information
            profile_info = profile_data.get('profile_user', [{}])[0]
            
            # Create normalized profile data
            profile = {
                'id': f"instagram_profile_{profile_info.get('username', '')}",
                'username': profile_info.get('username', ''),
                'name': profile_info.get('name', ''),
                'biography': profile_info.get('biography', ''),
                'website': profile_info.get('external_url', ''),
                'email': profile_info.get('email', ''),
                'phone_number': profile_info.get('phone_number', ''),
                'gender': profile_info.get('gender', ''),
                'private_account': profile_info.get('is_private', False),
                'business_account': profile_info.get('is_business_account', False),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'instagram',
                'type': 'profile',
                'source': 'instagram_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Instagram profile: {str(e)}")
    
    def _extract_posts(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from an Instagram posts JSON file.
        
        Args:
            posts_path: Path to the posts JSON file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            # Handle different Instagram export formats
            posts_list = []
            if isinstance(posts_data, dict) and 'media' in posts_data:
                posts_list = posts_data.get('media', [])
            elif isinstance(posts_data, list):
                posts_list = posts_data
            
            logger.info(f"Found {len(posts_list)} posts in Instagram export")
            
            for post in posts_list:
                try:
                    # Parse post timestamp
                    timestamp = None
                    timestamp_str = post.get('taken_at', '') or post.get('creation_timestamp', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Get post content
                    caption = ''
                    if 'caption' in post:
                        if isinstance(post['caption'], str):
                            caption = post['caption']
                        elif isinstance(post['caption'], dict):
                            caption = post['caption'].get('text', '')
                    
                    # Get post location
                    location = None
                    if 'location' in post:
                        if isinstance(post['location'], dict):
                            location = {
                                'name': post['location'].get('name', ''),
                                'latitude': post['location'].get('latitude', 0),
                                'longitude': post['location'].get('longitude', 0)
                            }
                    
                    # Get media items
                    media_items = []
                    
                    # Handle different media formats
                    if 'media' in post:
                        for media in post['media']:
                            media_items.append({
                                'type': media.get('media_type', 'image'),
                                'uri': media.get('uri', ''),
                                'creation_timestamp': media.get('creation_timestamp', '')
                            })
                    elif 'image_versions2' in post:
                        media_items.append({
                            'type': 'image',
                            'uri': post.get('image_versions2', {}).get('candidates', [{}])[0].get('url', ''),
                            'creation_timestamp': timestamp_str
                        })
                    elif 'carousel_media' in post:
                        for media in post['carousel_media']:
                            media_items.append({
                                'type': 'image' if 'image_versions2' in media else 'video',
                                'uri': media.get('image_versions2', {}).get('candidates', [{}])[0].get('url', '') or 
                                       media.get('video_versions', [{}])[0].get('url', ''),
                                'creation_timestamp': timestamp_str
                            })
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"instagram_post_{post.get('id', '')}",
                        'caption': caption,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'location': location,
                        'likes_count': post.get('like_count', 0),
                        'comments_count': post.get('comment_count', 0),
                        'media': media_items,
                        'has_media': len(media_items) > 0,
                        'is_video': any(item['type'] == 'video' for item in media_items),
                        'platform': 'instagram',
                        'type': 'post',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from Instagram export: {str(e)}")
    
    def _extract_messages(self, message_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from an Instagram messages JSON file.
        
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
            logger.info(f"Found {len(messages)} messages in Instagram conversation '{conversation_title or ', '.join(participant_names)}'")
            
            # Get user's name from profile or participants
            user_name = ''
            if self.user_info:
                user_name = self.user_info.get('profile_user', [{}])[0].get('username', '')
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('timestamp_ms', 0)
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str) / 1000)  # Instagram stores timestamps in milliseconds
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
                    share = message.get('share', {})
                    
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
                    
                    # Add shared content
                    if share:
                        media_items.append({
                            'type': 'share',
                            'uri': share.get('link', ''),
                            'share_text': share.get('share_text', '')
                        })
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"instagram_msg_{message.get('timestamp_ms', '')}",
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
                        'platform': 'instagram',
                        'type': 'message',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Instagram export: {str(e)}")
    
    def _extract_comments(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from an Instagram comments JSON file.
        
        Args:
            comments_path: Path to the comments JSON file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
            
            # Handle different Instagram export formats
            comments_list = []
            if isinstance(comments_data, dict) and 'comments_media_comments' in comments_data:
                comments_list = comments_data.get('comments_media_comments', [])
            elif isinstance(comments_data, list):
                comments_list = comments_data
            
            logger.info(f"Found {len(comments_list)} comments in Instagram export")
            
            for comment in comments_list:
                try:
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_str = comment.get('created_at', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"instagram_comment_{comment.get('id', '')}",
                        'content': comment.get('text', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'post_id': comment.get('media_id', ''),
                        'platform': 'instagram',
                        'type': 'comment',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from Instagram export: {str(e)}")
    
    def _extract_followers(self, followers_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract followers from an Instagram followers JSON file.
        
        Args:
            followers_path: Path to the followers JSON file
                
        Yields:
            Dictionaries containing normalized follower data
        """
        try:
            with open(followers_path, 'r', encoding='utf-8') as f:
                followers_data = json.load(f)
            
            # Handle different Instagram export formats
            followers_list = []
            if isinstance(followers_data, dict) and 'relationships_followers' in followers_data:
                followers_list = followers_data.get('relationships_followers', [])
            elif isinstance(followers_data, list):
                followers_list = followers_data
            
            logger.info(f"Found {len(followers_list)} followers in Instagram export")
            
            for follower in followers_list:
                try:
                    # Create normalized follower data
                    follower_data = {
                        'id': f"instagram_follower_{follower.get('string_list_data', [{}])[0].get('value', '')}",
                        'username': follower.get('string_list_data', [{}])[0].get('value', ''),
                        'name': follower.get('string_list_data', [{}])[0].get('href', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'instagram',
                        'type': 'follower',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(follower_data):
                        self.item_count += 1
                        yield follower_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram follower: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting followers from Instagram export: {str(e)}")
    
    def _extract_following(self, following_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract following from an Instagram following JSON file.
        
        Args:
            following_path: Path to the following JSON file
                
        Yields:
            Dictionaries containing normalized following data
        """
        try:
            with open(following_path, 'r', encoding='utf-8') as f:
                following_data = json.load(f)
            
            # Handle different Instagram export formats
            following_list = []
            if isinstance(following_data, dict) and 'relationships_following' in following_data:
                following_list = following_data.get('relationships_following', [])
            elif isinstance(following_data, list):
                following_list = following_data
            
            logger.info(f"Found {len(following_list)} following in Instagram export")
            
            for following in following_list:
                try:
                    # Create normalized following data
                    following_data = {
                        'id': f"instagram_following_{following.get('string_list_data', [{}])[0].get('value', '')}",
                        'username': following.get('string_list_data', [{}])[0].get('value', ''),
                        'name': following.get('string_list_data', [{}])[0].get('href', ''),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'instagram',
                        'type': 'following',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(following_data):
                        self.item_count += 1
                        yield following_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram following: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting following from Instagram export: {str(e)}")
    
    def _extract_stories(self, stories_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract stories from an Instagram stories JSON file.
        
        Args:
            stories_path: Path to the stories JSON file
                
        Yields:
            Dictionaries containing normalized story data
        """
        try:
            with open(stories_path, 'r', encoding='utf-8') as f:
                stories_data = json.load(f)
            
            # Handle different Instagram export formats
            stories_list = []
            if isinstance(stories_data, dict) and 'ig_stories' in stories_data:
                stories_list = stories_data.get('ig_stories', [])
            elif isinstance(stories_data, list):
                stories_list = stories_data
            
            logger.info(f"Found {len(stories_list)} stories in Instagram export")
            
            for story in stories_list:
                try:
                    # Parse story timestamp
                    timestamp = None
                    timestamp_str = story.get('creation_timestamp', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = parse_datetime(timestamp_str)
                    
                    # Get media items
                    media_items = []
                    
                    if 'uri' in story:
                        media_items.append({
                            'type': 'image' if story.get('media_type', '') == 'photo' else 'video',
                            'uri': story.get('uri', ''),
                            'creation_timestamp': timestamp_str
                        })
                    
                    # Create normalized story data
                    story_data = {
                        'id': f"instagram_story_{story.get('id', '')}",
                        'caption': story.get('caption', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'media': media_items,
                        'has_media': len(media_items) > 0,
                        'is_video': any(item['type'] == 'video' for item in media_items),
                        'platform': 'instagram',
                        'type': 'story',
                        'source': 'instagram_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(story_data):
                        self.item_count += 1
                        yield story_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Instagram story: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting stories from Instagram export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Instagram data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item