"""
Reddit Connector for CogniLink

This module provides functionality to import data from Reddit exports,
including posts, comments, messages, and profile information.
"""

import os
import json
import logging
import zipfile
import csv
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class RedditConnector(BaseConnector):
    """
    Connector for importing Reddit data.
    
    This class handles extraction of posts, comments, messages, and profile information
    from Reddit data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Reddit connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "reddit"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Reddit data export file.
        
        Args:
            file_path: Path to the Reddit data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["posts", "comments", "profile"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["posts", "comments", "profile", "messages", "subscriptions", "saved"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_reddit_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_reddit_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_reddit_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Reddit data export directory.
        
        Args:
            directory_path: Path to the Reddit data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "account", "account.csv")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            self.user_info = row
                            yield from self._extract_profile(row)
                except Exception as e:
                    logger.error(f"Error loading Reddit profile data: {str(e)}")
            
            # Try alternate location
            profile_path = os.path.join(directory_path, "profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        self.user_info = profile_data
                        yield from self._extract_profile(profile_data)
                except Exception as e:
                    logger.error(f"Error loading Reddit profile data: {str(e)}")
        
        # Extract posts
        if "posts" in data_types:
            posts_path = os.path.join(directory_path, "posts", "posts.csv")
            if os.path.exists(posts_path):
                yield from self._extract_posts_from_csv(posts_path)
            
            # Try alternate location
            posts_path = os.path.join(directory_path, "posts.json")
            if os.path.exists(posts_path):
                yield from self._extract_posts_from_json(posts_path)
        
        # Extract comments
        if "comments" in data_types:
            comments_path = os.path.join(directory_path, "comments", "comments.csv")
            if os.path.exists(comments_path):
                yield from self._extract_comments_from_csv(comments_path)
            
            # Try alternate location
            comments_path = os.path.join(directory_path, "comments.json")
            if os.path.exists(comments_path):
                yield from self._extract_comments_from_json(comments_path)
        
        # Extract messages
        if "messages" in data_types:
            messages_path = os.path.join(directory_path, "messages", "messages.csv")
            if os.path.exists(messages_path):
                yield from self._extract_messages_from_csv(messages_path)
            
            # Try alternate location
            messages_path = os.path.join(directory_path, "messages.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages_from_json(messages_path)
        
        # Extract subscriptions
        if "subscriptions" in data_types:
            subs_path = os.path.join(directory_path, "subscriptions", "subscriptions.csv")
            if os.path.exists(subs_path):
                yield from self._extract_subscriptions_from_csv(subs_path)
            
            # Try alternate location
            subs_path = os.path.join(directory_path, "subscriptions.json")
            if os.path.exists(subs_path):
                yield from self._extract_subscriptions_from_json(subs_path)
        
        # Extract saved posts/comments
        if "saved" in data_types:
            saved_path = os.path.join(directory_path, "saved", "saved.csv")
            if os.path.exists(saved_path):
                yield from self._extract_saved_from_csv(saved_path)
            
            # Try alternate location
            saved_path = os.path.join(directory_path, "saved.json")
            if os.path.exists(saved_path):
                yield from self._extract_saved_from_json(saved_path)
    
    def _extract_profile(self, profile_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information.
        
        Args:
            profile_data: User profile data
                
        Yields:
            Normalized profile data
        """
        try:
            # Handle different Reddit export formats
            username = ''
            email = ''
            created_at = ''
            
            # Format 1: CSV format
            if 'username' in profile_data:
                username = profile_data.get('username', '')
                email = profile_data.get('email', '')
                created_at = profile_data.get('created_at', '')
            
            # Format 2: JSON format
            elif 'data' in profile_data:
                user_data = profile_data.get('data', {})
                username = user_data.get('name', '')
                email = user_data.get('email', '')
                created_at = user_data.get('created_utc', '')
                if created_at:
                    try:
                        created_at = datetime.fromtimestamp(float(created_at)).isoformat()
                    except (ValueError, TypeError):
                        pass
            
            # Create normalized profile data
            profile = {
                'id': f"reddit_profile_{username}",
                'username': username,
                'email': email,
                'created_at': created_at,
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'reddit',
                'type': 'profile',
                'source': 'reddit_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Reddit profile: {str(e)}")
    
    def _extract_posts_from_csv(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from a Reddit posts CSV file.
        
        Args:
            posts_path: Path to the posts CSV file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                posts = list(reader)
            
            logger.info(f"Found {len(posts)} posts in Reddit export")
            
            for post in posts:
                try:
                    # Parse post timestamp
                    timestamp = None
                    timestamp_str = post.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"reddit_post_{post.get('id', '')}",
                        'title': post.get('title', ''),
                        'content': post.get('text', ''),
                        'subreddit': post.get('subreddit', ''),
                        'url': post.get('url', ''),
                        'permalink': post.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'score': int(post.get('score', 0)),
                        'num_comments': int(post.get('num_comments', 0)),
                        'platform': 'reddit',
                        'type': 'post',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from Reddit export: {str(e)}")
    
    def _extract_posts_from_json(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from a Reddit posts JSON file.
        
        Args:
            posts_path: Path to the posts JSON file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            # Handle different Reddit export formats
            posts_list = []
            
            # Format 1: Direct list
            if isinstance(posts_data, list):
                posts_list = posts_data
            
            # Format 2: Nested under 'data'
            elif 'data' in posts_data:
                posts_list = posts_data.get('data', [])
            
            logger.info(f"Found {len(posts_list)} posts in Reddit export")
            
            for post in posts_list:
                try:
                    # Handle nested data structure
                    if 'data' in post:
                        post = post.get('data', {})
                    
                    # Parse post timestamp
                    timestamp = None
                    timestamp_str = post.get('created_utc', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"reddit_post_{post.get('id', '')}",
                        'title': post.get('title', ''),
                        'content': post.get('selftext', ''),
                        'subreddit': post.get('subreddit', ''),
                        'url': post.get('url', ''),
                        'permalink': post.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'score': int(post.get('score', 0)),
                        'num_comments': int(post.get('num_comments', 0)),
                        'platform': 'reddit',
                        'type': 'post',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from Reddit export: {str(e)}")
    
    def _extract_comments_from_csv(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from a Reddit comments CSV file.
        
        Args:
            comments_path: Path to the comments CSV file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                comments = list(reader)
            
            logger.info(f"Found {len(comments)} comments in Reddit export")
            
            for comment in comments:
                try:
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_str = comment.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"reddit_comment_{comment.get('id', '')}",
                        'content': comment.get('body', ''),
                        'subreddit': comment.get('subreddit', ''),
                        'post_id': comment.get('link_id', '').replace('t3_', ''),
                        'parent_id': comment.get('parent_id', '').replace('t1_', '').replace('t3_', ''),
                        'permalink': comment.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'score': int(comment.get('score', 0)),
                        'platform': 'reddit',
                        'type': 'comment',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from Reddit export: {str(e)}")
    
    def _extract_comments_from_json(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from a Reddit comments JSON file.
        
        Args:
            comments_path: Path to the comments JSON file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
            
            # Handle different Reddit export formats
            comments_list = []
            
            # Format 1: Direct list
            if isinstance(comments_data, list):
                comments_list = comments_data
            
            # Format 2: Nested under 'data'
            elif 'data' in comments_data:
                comments_list = comments_data.get('data', [])
            
            logger.info(f"Found {len(comments_list)} comments in Reddit export")
            
            for comment in comments_list:
                try:
                    # Handle nested data structure
                    if 'data' in comment:
                        comment = comment.get('data', {})
                    
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_str = comment.get('created_utc', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"reddit_comment_{comment.get('id', '')}",
                        'content': comment.get('body', ''),
                        'subreddit': comment.get('subreddit', ''),
                        'post_id': comment.get('link_id', '').replace('t3_', ''),
                        'parent_id': comment.get('parent_id', '').replace('t1_', '').replace('t3_', ''),
                        'permalink': comment.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'score': int(comment.get('score', 0)),
                        'platform': 'reddit',
                        'type': 'comment',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from Reddit export: {str(e)}")
    
    def _extract_messages_from_csv(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Reddit messages CSV file.
        
        Args:
            messages_path: Path to the messages CSV file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                messages = list(reader)
            
            logger.info(f"Found {len(messages)} messages in Reddit export")
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get username from profile
                    username = ''
                    if self.user_info:
                        username = self.user_info.get('username', '')
                    
                    # Determine if the message was sent by the user
                    is_sent = message.get('author', '') == username
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"reddit_message_{message.get('id', '')}",
                        'subject': message.get('subject', ''),
                        'content': message.get('body', ''),
                        'sender': message.get('author', ''),
                        'recipient': message.get('dest', ''),
                        'is_sent': is_sent,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'message',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Reddit export: {str(e)}")
    
    def _extract_messages_from_json(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a Reddit messages JSON file.
        
        Args:
            messages_path: Path to the messages JSON file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different Reddit export formats
            messages_list = []
            
            # Format 1: Direct list
            if isinstance(messages_data, list):
                messages_list = messages_data
            
            # Format 2: Nested under 'data'
            elif 'data' in messages_data:
                messages_list = messages_data.get('data', [])
            
            logger.info(f"Found {len(messages_list)} messages in Reddit export")
            
            for message in messages_list:
                try:
                    # Handle nested data structure
                    if 'data' in message:
                        message = message.get('data', {})
                    
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('created_utc', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Get username from profile
                    username = ''
                    if self.user_info:
                        if isinstance(self.user_info, dict):
                            username = self.user_info.get('username', '')
                            if not username and 'data' in self.user_info:
                                username = self.user_info.get('data', {}).get('name', '')
                    
                    # Determine if the message was sent by the user
                    is_sent = message.get('author', '') == username
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"reddit_message_{message.get('id', '')}",
                        'subject': message.get('subject', ''),
                        'content': message.get('body', ''),
                        'sender': message.get('author', ''),
                        'recipient': message.get('dest', ''),
                        'is_sent': is_sent,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'message',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from Reddit export: {str(e)}")
    
    def _extract_subscriptions_from_csv(self, subs_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract subscriptions from a Reddit subscriptions CSV file.
        
        Args:
            subs_path: Path to the subscriptions CSV file
                
        Yields:
            Dictionaries containing normalized subscription data
        """
        try:
            with open(subs_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                subscriptions = list(reader)
            
            logger.info(f"Found {len(subscriptions)} subscriptions in Reddit export")
            
            for subscription in subscriptions:
                try:
                    # Parse subscription timestamp
                    timestamp = None
                    timestamp_str = subscription.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized subscription data
                    subscription_data = {
                        'id': f"reddit_subscription_{subscription.get('subreddit', '')}",
                        'subreddit': subscription.get('subreddit', ''),
                        'subreddit_id': subscription.get('subreddit_id', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'subscription',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(subscription_data):
                        self.item_count += 1
                        yield subscription_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit subscription: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting subscriptions from Reddit export: {str(e)}")
    
    def _extract_subscriptions_from_json(self, subs_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract subscriptions from a Reddit subscriptions JSON file.
        
        Args:
            subs_path: Path to the subscriptions JSON file
                
        Yields:
            Dictionaries containing normalized subscription data
        """
        try:
            with open(subs_path, 'r', encoding='utf-8') as f:
                subs_data = json.load(f)
            
            # Handle different Reddit export formats
            subs_list = []
            
            # Format 1: Direct list
            if isinstance(subs_data, list):
                subs_list = subs_data
            
            # Format 2: Nested under 'data'
            elif 'data' in subs_data:
                subs_list = subs_data.get('data', [])
            
            logger.info(f"Found {len(subs_list)} subscriptions in Reddit export")
            
            for subscription in subs_list:
                try:
                    # Handle nested data structure
                    if 'data' in subscription:
                        subscription = subscription.get('data', {})
                    
                    # Parse subscription timestamp
                    timestamp = None
                    timestamp_str = subscription.get('created_utc', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized subscription data
                    subscription_data = {
                        'id': f"reddit_subscription_{subscription.get('display_name', '')}",
                        'subreddit': subscription.get('display_name', ''),
                        'subreddit_id': subscription.get('name', ''),
                        'description': subscription.get('public_description', ''),
                        'subscribers': subscription.get('subscribers', 0),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'subscription',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(subscription_data):
                        self.item_count += 1
                        yield subscription_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit subscription: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting subscriptions from Reddit export: {str(e)}")
    
    def _extract_saved_from_csv(self, saved_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract saved posts/comments from a Reddit saved CSV file.
        
        Args:
            saved_path: Path to the saved CSV file
                
        Yields:
            Dictionaries containing normalized saved data
        """
        try:
            with open(saved_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                saved_items = list(reader)
            
            logger.info(f"Found {len(saved_items)} saved items in Reddit export")
            
            for item in saved_items:
                try:
                    # Parse saved timestamp
                    timestamp = None
                    timestamp_str = item.get('created_at', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Determine item type
                    item_type = 'post'
                    if 'comment' in item.get('type', ''):
                        item_type = 'comment'
                    
                    # Create normalized saved data
                    saved_data = {
                        'id': f"reddit_saved_{item.get('id', '')}",
                        'item_id': item.get('id', ''),
                        'item_type': item_type,
                        'title': item.get('title', ''),
                        'content': item.get('body', '') or item.get('text', ''),
                        'subreddit': item.get('subreddit', ''),
                        'permalink': item.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'saved',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(saved_data):
                        self.item_count += 1
                        yield saved_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit saved item: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting saved items from Reddit export: {str(e)}")
    
    def _extract_saved_from_json(self, saved_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract saved posts/comments from a Reddit saved JSON file.
        
        Args:
            saved_path: Path to the saved JSON file
                
        Yields:
            Dictionaries containing normalized saved data
        """
        try:
            with open(saved_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # Handle different Reddit export formats
            saved_list = []
            
            # Format 1: Direct list
            if isinstance(saved_data, list):
                saved_list = saved_data
            
            # Format 2: Nested under 'data'
            elif 'data' in saved_data:
                saved_list = saved_data.get('data', [])
            
            logger.info(f"Found {len(saved_list)} saved items in Reddit export")
            
            for item in saved_list:
                try:
                    # Handle nested data structure
                    if 'data' in item:
                        item = item.get('data', {})
                    
                    # Parse saved timestamp
                    timestamp = None
                    timestamp_str = item.get('created_utc', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromtimestamp(float(timestamp_str))
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Determine item type
                    item_type = 'post'
                    if item.get('name', '').startswith('t1_'):
                        item_type = 'comment'
                    
                    # Get content based on type
                    content = item.get('selftext', '') if item_type == 'post' else item.get('body', '')
                    
                    # Create normalized saved data
                    saved_data = {
                        'id': f"reddit_saved_{item.get('id', '')}",
                        'item_id': item.get('id', ''),
                        'item_type': item_type,
                        'title': item.get('title', ''),
                        'content': content,
                        'subreddit': item.get('subreddit', ''),
                        'permalink': item.get('permalink', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'reddit',
                        'type': 'saved',
                        'source': 'reddit_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(saved_data):
                        self.item_count += 1
                        yield saved_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Reddit saved item: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting saved items from Reddit export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Reddit data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item