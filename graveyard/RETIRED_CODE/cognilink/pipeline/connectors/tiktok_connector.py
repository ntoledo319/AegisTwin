"""
TikTok Connector for CogniLink

This module provides functionality to import data from TikTok exports,
including videos, comments, messages, and profile information.
"""

import os
import json
import logging
import zipfile
import re
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import csv

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class TikTokConnector(BaseConnector):
    """
    Connector for importing TikTok data.
    
    This class handles extraction of videos, comments, messages, and profile information
    from TikTok data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the TikTok connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "tiktok"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a TikTok data export file.
        
        Args:
            file_path: Path to the TikTok data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["videos", "comments", "profile"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["videos", "comments", "profile", "messages", "followers", "following", "activity"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_tiktok_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_tiktok_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_tiktok_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a TikTok data export directory.
        
        Args:
            directory_path: Path to the TikTok data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "user_data.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading TikTok profile data: {str(e)}")
            
            # Try alternate location
            profile_path = os.path.join(directory_path, "Profile", "Profile Information.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading TikTok profile data: {str(e)}")
        
        # Extract videos
        if "videos" in data_types:
            videos_path = os.path.join(directory_path, "Video", "Videos.json")
            if os.path.exists(videos_path):
                yield from self._extract_videos(videos_path)
            
            # Try alternate location
            videos_path = os.path.join(directory_path, "videos.json")
            if os.path.exists(videos_path):
                yield from self._extract_videos(videos_path)
        
        # Extract comments
        if "comments" in data_types:
            comments_path = os.path.join(directory_path, "Comment", "Comments.json")
            if os.path.exists(comments_path):
                yield from self._extract_comments(comments_path)
            
            # Try alternate location
            comments_path = os.path.join(directory_path, "comments.json")
            if os.path.exists(comments_path):
                yield from self._extract_comments(comments_path)
        
        # Extract direct messages
        if "messages" in data_types:
            messages_path = os.path.join(directory_path, "Direct Messages", "Chat History.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages(messages_path)
            
            # Try alternate location
            messages_path = os.path.join(directory_path, "chat_history.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages(messages_path)
        
        # Extract followers
        if "followers" in data_types:
            followers_path = os.path.join(directory_path, "Follower List", "Followers.json")
            if os.path.exists(followers_path):
                yield from self._extract_followers(followers_path)
            
            # Try alternate location
            followers_path = os.path.join(directory_path, "followers.json")
            if os.path.exists(followers_path):
                yield from self._extract_followers(followers_path)
        
        # Extract following
        if "following" in data_types:
            following_path = os.path.join(directory_path, "Following List", "Following.json")
            if os.path.exists(following_path):
                yield from self._extract_following(following_path)
            
            # Try alternate location
            following_path = os.path.join(directory_path, "following.json")
            if os.path.exists(following_path):
                yield from self._extract_following(following_path)
        
        # Extract activity
        if "activity" in data_types:
            activity_path = os.path.join(directory_path, "Activity", "Like List.json")
            if os.path.exists(activity_path):
                yield from self._extract_likes(activity_path)
            
            # Try alternate location
            activity_path = os.path.join(directory_path, "like_list.json")
            if os.path.exists(activity_path):
                yield from self._extract_likes(activity_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Handle different TikTok export formats
            username = ''
            display_name = ''
            bio = ''
            
            # Format 1: Profile Information.json
            if 'Profile Information' in profile_data:
                profile_info = profile_data['Profile Information']
                username = profile_info.get('Profile Information', {}).get('Username', '')
                display_name = profile_info.get('Profile Information', {}).get('Display Name', '')
                bio = profile_info.get('Profile Information', {}).get('Bio', '')
            
            # Format 2: user_data.json
            elif 'user' in profile_data:
                user_info = profile_data['user']
                username = user_info.get('username', '')
                display_name = user_info.get('nickname', '')
                bio = user_info.get('signature', '')
            
            # Create normalized profile data
            profile = {
                'id': f"tiktok_profile_{username}",
                'username': username,
                'display_name': display_name,
                'bio': bio,
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'tiktok',
                'type': 'profile',
                'source': 'tiktok_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing TikTok profile: {str(e)}")
    
    def _extract_videos(self, videos_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract videos from a TikTok videos JSON file.
        
        Args:
            videos_path: Path to the videos JSON file
                
        Yields:
            Dictionaries containing normalized video data
        """
        try:
            with open(videos_path, 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
            
            # Handle different TikTok export formats
            videos_list = []
            
            # Format 1: Videos.json
            if 'Videos' in videos_data:
                videos_list = videos_data['Videos']
            
            # Format 2: videos.json
            elif 'videos' in videos_data:
                videos_list = videos_data['videos']
            
            # Format 3: Direct list
            elif isinstance(videos_data, list):
                videos_list = videos_data
            
            logger.info(f"Found {len(videos_list)} videos in TikTok export")
            
            for video in videos_list:
                try:
                    # Parse video timestamp
                    timestamp = None
                    timestamp_str = ''
                    
                    # Format 1: "Date Created: 2021-01-01 12:00:00"
                    if 'Date Created' in video:
                        timestamp_str = video['Date Created']
                    
                    # Format 2: "create_time": "2021-01-01 12:00:00"
                    elif 'create_time' in video:
                        timestamp_str = video['create_time']
                    
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get video content
                    caption = ''
                    
                    # Format 1: "Caption"
                    if 'Caption' in video:
                        caption = video['Caption']
                    
                    # Format 2: "desc"
                    elif 'desc' in video:
                        caption = video['desc']
                    
                    # Get video URL
                    video_url = ''
                    
                    # Format 1: "Video Link"
                    if 'Video Link' in video:
                        video_url = video['Video Link']
                    
                    # Format 2: "share_url"
                    elif 'share_url' in video:
                        video_url = video['share_url']
                    
                    # Get video statistics
                    likes = 0
                    comments = 0
                    shares = 0
                    views = 0
                    
                    # Format 1: Individual fields
                    if 'Likes' in video:
                        likes = int(video.get('Likes', 0))
                    if 'Comments' in video:
                        comments = int(video.get('Comments', 0))
                    if 'Shares' in video:
                        shares = int(video.get('Shares', 0))
                    if 'Views' in video:
                        views = int(video.get('Views', 0))
                    
                    # Format 2: "statistics" object
                    elif 'statistics' in video:
                        stats = video['statistics']
                        likes = int(stats.get('digg_count', 0))
                        comments = int(stats.get('comment_count', 0))
                        shares = int(stats.get('share_count', 0))
                        views = int(stats.get('play_count', 0))
                    
                    # Create normalized video data
                    video_data = {
                        'id': f"tiktok_video_{video.get('id', '') or video.get('Video ID', '')}",
                        'caption': caption,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'video_url': video_url,
                        'likes': likes,
                        'comments': comments,
                        'shares': shares,
                        'views': views,
                        'platform': 'tiktok',
                        'type': 'video',
                        'source': 'tiktok_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(video_data):
                        self.item_count += 1
                        yield video_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok video: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting videos from TikTok export: {str(e)}")
    
    def _extract_comments(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from a TikTok comments JSON file.
        
        Args:
            comments_path: Path to the comments JSON file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
            
            # Handle different TikTok export formats
            comments_list = []
            
            # Format 1: Comments.json
            if 'Comments' in comments_data:
                comments_list = comments_data['Comments']
            
            # Format 2: comments.json
            elif 'comments' in comments_data:
                comments_list = comments_data['comments']
            
            # Format 3: Direct list
            elif isinstance(comments_data, list):
                comments_list = comments_data
            
            logger.info(f"Found {len(comments_list)} comments in TikTok export")
            
            for comment in comments_list:
                try:
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_str = ''
                    
                    # Format 1: "Date Created: 2021-01-01 12:00:00"
                    if 'Date Created' in comment:
                        timestamp_str = comment['Date Created']
                    
                    # Format 2: "create_time": "2021-01-01 12:00:00"
                    elif 'create_time' in comment:
                        timestamp_str = comment['create_time']
                    
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get comment content
                    content = ''
                    
                    # Format 1: "Comment"
                    if 'Comment' in comment:
                        content = comment['Comment']
                    
                    # Format 2: "text"
                    elif 'text' in comment:
                        content = comment['text']
                    
                    # Get video ID
                    video_id = ''
                    
                    # Format 1: "Video ID"
                    if 'Video ID' in comment:
                        video_id = comment['Video ID']
                    
                    # Format 2: "aweme_id"
                    elif 'aweme_id' in comment:
                        video_id = comment['aweme_id']
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"tiktok_comment_{comment.get('id', '') or comment.get('Comment ID', '')}",
                        'content': content,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'video_id': video_id,
                        'platform': 'tiktok',
                        'type': 'comment',
                        'source': 'tiktok_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from TikTok export: {str(e)}")
    
    def _extract_messages(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a TikTok messages JSON file.
        
        Args:
            messages_path: Path to the messages JSON file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different TikTok export formats
            conversations = []
            
            # Format 1: Chat History.json
            if 'Direct Messages' in messages_data:
                conversations = messages_data['Direct Messages']
            
            # Format 2: chat_history.json
            elif 'chat_history' in messages_data:
                conversations = messages_data['chat_history']
            
            logger.info(f"Found {len(conversations)} conversations in TikTok export")
            
            # Get user's username from profile
            username = ''
            if self.user_info:
                if 'Profile Information' in self.user_info:
                    username = self.user_info['Profile Information'].get('Profile Information', {}).get('Username', '')
                elif 'user' in self.user_info:
                    username = self.user_info['user'].get('username', '')
            
            for conversation in conversations:
                try:
                    # Get conversation information
                    conversation_id = ''
                    conversation_name = ''
                    
                    # Format 1: "Conversation ID" and "Conversation Name"
                    if 'Conversation ID' in conversation:
                        conversation_id = conversation['Conversation ID']
                        conversation_name = conversation.get('Conversation Name', '')
                    
                    # Format 2: "conversation_id" and "conversation_title"
                    elif 'conversation_id' in conversation:
                        conversation_id = conversation['conversation_id']
                        conversation_name = conversation.get('conversation_title', '')
                    
                    # Get messages
                    messages = []
                    
                    # Format 1: "Messages"
                    if 'Messages' in conversation:
                        messages = conversation['Messages']
                    
                    # Format 2: "messages"
                    elif 'messages' in conversation:
                        messages = conversation['messages']
                    
                    logger.info(f"Processing {len(messages)} messages in TikTok conversation '{conversation_name}'")
                    
                    for message in messages:
                        try:
                            # Parse message timestamp
                            timestamp = None
                            timestamp_str = ''
                            
                            # Format 1: "Date Sent: 2021-01-01 12:00:00"
                            if 'Date Sent' in message:
                                timestamp_str = message['Date Sent']
                            
                            # Format 2: "create_time": "2021-01-01 12:00:00"
                            elif 'create_time' in message:
                                timestamp_str = message['create_time']
                            
                            if timestamp_str:
                                timestamp = parse_datetime(timestamp_str)
                            
                            # Get message content
                            content = ''
                            
                            # Format 1: "Content"
                            if 'Content' in message:
                                content = message['Content']
                            
                            # Format 2: "text"
                            elif 'text' in message:
                                content = message['text']
                            
                            # Get sender information
                            sender = ''
                            
                            # Format 1: "Sender"
                            if 'Sender' in message:
                                sender = message['Sender']
                            
                            # Format 2: "sender"
                            elif 'sender' in message:
                                sender = message['sender']
                            
                            # Determine if the message was sent by the user
                            is_sent = sender == username
                            
                            # Create normalized message data
                            message_data = {
                                'id': f"tiktok_msg_{conversation_id}_{message.get('id', '') or message.get('Message ID', '')}",
                                'conversation_id': conversation_id,
                                'conversation_name': conversation_name,
                                'content': content,
                                'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                'sender': sender,
                                'is_sent': is_sent,
                                'platform': 'tiktok',
                                'type': 'message',
                                'source': 'tiktok_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(message_data):
                                self.item_count += 1
                                yield message_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing TikTok message: {str(e)}")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok conversation: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from TikTok export: {str(e)}")
    
    def _extract_followers(self, followers_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract followers from a TikTok followers JSON file.
        
        Args:
            followers_path: Path to the followers JSON file
                
        Yields:
            Dictionaries containing normalized follower data
        """
        try:
            with open(followers_path, 'r', encoding='utf-8') as f:
                followers_data = json.load(f)
            
            # Handle different TikTok export formats
            followers_list = []
            
            # Format 1: Followers.json
            if 'Follower List' in followers_data:
                followers_list = followers_data['Follower List']
            
            # Format 2: followers.json
            elif 'followers' in followers_data:
                followers_list = followers_data['followers']
            
            # Format 3: Direct list
            elif isinstance(followers_data, list):
                followers_list = followers_data
            
            logger.info(f"Found {len(followers_list)} followers in TikTok export")
            
            for follower in followers_list:
                try:
                    # Get follower information
                    username = ''
                    
                    # Format 1: "Username"
                    if 'Username' in follower:
                        username = follower['Username']
                    
                    # Format 2: "username"
                    elif 'username' in follower:
                        username = follower['username']
                    
                    # Create normalized follower data
                    follower_data = {
                        'id': f"tiktok_follower_{username}",
                        'username': username,
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'tiktok',
                        'type': 'follower',
                        'source': 'tiktok_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(follower_data):
                        self.item_count += 1
                        yield follower_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok follower: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting followers from TikTok export: {str(e)}")
    
    def _extract_following(self, following_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract following from a TikTok following JSON file.
        
        Args:
            following_path: Path to the following JSON file
                
        Yields:
            Dictionaries containing normalized following data
        """
        try:
            with open(following_path, 'r', encoding='utf-8') as f:
                following_data = json.load(f)
            
            # Handle different TikTok export formats
            following_list = []
            
            # Format 1: Following.json
            if 'Following List' in following_data:
                following_list = following_data['Following List']
            
            # Format 2: following.json
            elif 'following' in following_data:
                following_list = following_data['following']
            
            # Format 3: Direct list
            elif isinstance(following_data, list):
                following_list = following_data
            
            logger.info(f"Found {len(following_list)} following in TikTok export")
            
            for following in following_list:
                try:
                    # Get following information
                    username = ''
                    
                    # Format 1: "Username"
                    if 'Username' in following:
                        username = following['Username']
                    
                    # Format 2: "username"
                    elif 'username' in following:
                        username = following['username']
                    
                    # Create normalized following data
                    following_data = {
                        'id': f"tiktok_following_{username}",
                        'username': username,
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'tiktok',
                        'type': 'following',
                        'source': 'tiktok_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(following_data):
                        self.item_count += 1
                        yield following_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok following: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting following from TikTok export: {str(e)}")
    
    def _extract_likes(self, likes_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract likes from a TikTok likes JSON file.
        
        Args:
            likes_path: Path to the likes JSON file
                
        Yields:
            Dictionaries containing normalized like data
        """
        try:
            with open(likes_path, 'r', encoding='utf-8') as f:
                likes_data = json.load(f)
            
            # Handle different TikTok export formats
            likes_list = []
            
            # Format 1: Like List.json
            if 'Like List' in likes_data:
                likes_list = likes_data['Like List']
            
            # Format 2: like_list.json
            elif 'like_list' in likes_data:
                likes_list = likes_data['like_list']
            
            # Format 3: Direct list
            elif isinstance(likes_data, list):
                likes_list = likes_data
            
            logger.info(f"Found {len(likes_list)} likes in TikTok export")
            
            for like in likes_list:
                try:
                    # Parse like timestamp
                    timestamp = None
                    timestamp_str = ''
                    
                    # Format 1: "Date: 2021-01-01 12:00:00"
                    if 'Date' in like:
                        timestamp_str = like['Date']
                    
                    # Format 2: "create_time": "2021-01-01 12:00:00"
                    elif 'create_time' in like:
                        timestamp_str = like['create_time']
                    
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get video information
                    video_id = ''
                    
                    # Format 1: "Video ID"
                    if 'Video ID' in like:
                        video_id = like['Video ID']
                    
                    # Format 2: "aweme_id"
                    elif 'aweme_id' in like:
                        video_id = like['aweme_id']
                    
                    # Create normalized like data
                    like_data = {
                        'id': f"tiktok_like_{video_id}",
                        'video_id': video_id,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'tiktok',
                        'type': 'like',
                        'source': 'tiktok_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(like_data):
                        self.item_count += 1
                        yield like_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing TikTok like: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting likes from TikTok export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for TikTok data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item