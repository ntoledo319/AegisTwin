"""
Twitter/X Connector for CogniLink

This module provides functionality to import data from Twitter/X data exports,
including tweets, direct messages, and follower/following information.
"""

import os
import json
import logging
import zipfile
import re
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime

logger = logging.getLogger(__name__)

class TwitterConnector(BaseConnector):
    """
    Connector for importing Twitter/X data.
    
    This class handles extraction of tweets, direct messages, and social graph
    information from Twitter/X data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Twitter connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "twitter"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Twitter/X data export file.
        
        Args:
            file_path: Path to the Twitter/X data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["tweets", "dms", "followers"])
            **kwargs: Additional arguments
            
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["tweets", "dms", "followers", "following", "profile"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_twitter_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_twitter_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_twitter_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Twitter/X data export directory.
        
        Args:
            directory_path: Path to the Twitter/X data export directory
            data_types: List of data types to extract
            
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "data", "account.js")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        # Twitter exports often have a JavaScript variable assignment at the beginning
                        content = f.read()
                        content = re.sub(r'^window\.YTD\.account\.part0\s*=\s*', '', content)
                        account_data = json.loads(content)
                        
                        if account_data and isinstance(account_data, list) and len(account_data) > 0:
                            self.user_info = account_data[0]['account']
                            yield from self._extract_profile(self.user_info)
                except Exception as e:
                    logger.error(f"Error loading Twitter profile data: {str(e)}")
        
        # Extract tweets
        if "tweets" in data_types:
            tweets_path = os.path.join(directory_path, "data", "tweets.js")
            if os.path.exists(tweets_path):
                yield from self._extract_tweets(tweets_path)
            else:
                # Try alternate path for newer exports
                tweets_path = os.path.join(directory_path, "data", "tweet.js")
                if os.path.exists(tweets_path):
                    yield from self._extract_tweets(tweets_path)
        
        # Extract direct messages
        if "dms" in data_types:
            dms_path = os.path.join(directory_path, "data", "direct-messages.js")
            if os.path.exists(dms_path):
                yield from self._extract_direct_messages(dms_path)
        
        # Extract followers
        if "followers" in data_types:
            followers_path = os.path.join(directory_path, "data", "follower.js")
            if os.path.exists(followers_path):
                yield from self._extract_followers(followers_path)
        
        # Extract following
        if "following" in data_types:
            following_path = os.path.join(directory_path, "data", "following.js")
            if os.path.exists(following_path):
                yield from self._extract_following(following_path)
    
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
                'id': f"twitter_profile_{profile_data.get('accountId', '')}",
                'username': profile_data.get('username', ''),
                'display_name': profile_data.get('accountDisplayName', ''),
                'email': profile_data.get('email', ''),
                'created_at': profile_data.get('createdAt', ''),
                'bio': profile_data.get('description', {}).get('bio', ''),
                'location': profile_data.get('description', {}).get('location', ''),
                'url': profile_data.get('description', {}).get('url', ''),
                'followers_count': profile_data.get('followersCount', 0),
                'following_count': profile_data.get('followingCount', 0),
                'tweet_count': profile_data.get('tweetCount', 0),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'twitter',
                'type': 'profile',
                'source': 'twitter_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Twitter profile: {str(e)}")
    
    def _extract_tweets(self, tweets_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract tweets from a Twitter data export.
        
        Args:
            tweets_path: Path to the tweets.js file
            
        Yields:
            Dictionaries containing normalized tweet data
        """
        try:
            with open(tweets_path, 'r', encoding='utf-8') as f:
                # Twitter exports often have a JavaScript variable assignment at the beginning
                content = f.read()
                content = re.sub(r'^window\.YTD\.tweet\.part0\s*=\s*', '', content)
                content = re.sub(r'^window\.YTD\.tweets\.part0\s*=\s*', '', content)
                tweets_data = json.loads(content)
            
            logger.info(f"Found {len(tweets_data)} tweets in Twitter export")
            
            for tweet_item in tweets_data:
                try:
                    tweet = tweet_item.get('tweet', {})
                    if not tweet:
                        continue
                    
                    # Parse tweet timestamp
                    created_at = tweet.get('created_at', '')
                    timestamp = parse_datetime(created_at) if created_at else datetime.now()
                    
                    # Get tweet content
                    full_text = tweet.get('full_text', '')
                    
                    # Check if it's a retweet
                    is_retweet = full_text.startswith('RT @')
                    original_author = None
                    if is_retweet:
                        # Extract original author from RT @username: format
                        match = re.match(r'RT @([^:]+):', full_text)
                        if match:
                            original_author = match.group(1)
                    
                    # Create normalized tweet data
                    tweet_data = {
                        'id': f"twitter_tweet_{tweet.get('id', '')}",
                        'content': full_text,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'sender': self.user_info.get('username', 'me'),
                        'is_retweet': is_retweet,
                        'original_author': original_author,
                        'retweet_count': tweet.get('retweet_count', 0),
                        'favorite_count': tweet.get('favorite_count', 0),
                        'reply_count': tweet.get('reply_count', 0),
                        'hashtags': [hashtag.get('text') for hashtag in tweet.get('entities', {}).get('hashtags', [])],
                        'urls': [url.get('expanded_url') for url in tweet.get('entities', {}).get('urls', [])],
                        'mentions': [mention.get('screen_name') for mention in tweet.get('entities', {}).get('user_mentions', [])],
                        'platform': 'twitter',
                        'type': 'tweet',
                        'source': 'twitter_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(tweet_data):
                        self.item_count += 1
                        yield tweet_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing tweet: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting tweets from Twitter export: {str(e)}")
    
    def _extract_direct_messages(self, dms_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract direct messages from a Twitter data export.
        
        Args:
            dms_path: Path to the direct-messages.js file
            
        Yields:
            Dictionaries containing normalized direct message data
        """
        try:
            with open(dms_path, 'r', encoding='utf-8') as f:
                # Twitter exports often have a JavaScript variable assignment at the beginning
                content = f.read()
                content = re.sub(r'^window\.YTD\.direct_messages\.part0\s*=\s*', '', content)
                dms_data = json.loads(content)
            
            logger.info(f"Found {len(dms_data)} direct message conversations in Twitter export")
            
            for conversation in dms_data:
                try:
                    conversation_id = conversation.get('dmConversation', {}).get('conversationId', '')
                    messages = conversation.get('dmConversation', {}).get('messages', [])
                    
                    logger.info(f"Processing {len(messages)} messages in conversation {conversation_id}")
                    
                    for message in messages:
                        try:
                            message_data = message.get('messageCreate', {})
                            if not message_data:
                                continue
                            
                            # Parse message timestamp
                            created_at = message_data.get('createdAt', '')
                            timestamp = parse_datetime(created_at) if created_at else datetime.now()
                            
                            # Get sender and recipient
                            sender_id = message_data.get('senderId', '')
                            recipient_id = message_data.get('recipientId', '')
                            
                            # Determine if the message was sent by the user
                            is_sent = sender_id == self.user_info.get('accountId', '')
                            sender = 'me' if is_sent else sender_id
                            recipient = recipient_id if is_sent else 'me'
                            
                            # Get message content
                            text = message_data.get('text', '')
                            
                            # Create normalized message data
                            dm_data = {
                                'id': f"twitter_dm_{message_data.get('id', '')}",
                                'conversation_id': conversation_id,
                                'content': text,
                                'timestamp': timestamp.isoformat() if timestamp else None,
                                'sender': sender,
                                'recipient': recipient,
                                'is_sent': is_sent,
                                'platform': 'twitter',
                                'type': 'direct_message',
                                'source': 'twitter_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(dm_data):
                                self.item_count += 1
                                yield dm_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing direct message: {str(e)}")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing conversation: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting direct messages from Twitter export: {str(e)}")
    
    def _extract_followers(self, followers_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract followers from a Twitter data export.
        
        Args:
            followers_path: Path to the follower.js file
            
        Yields:
            Dictionaries containing normalized follower data
        """
        try:
            with open(followers_path, 'r', encoding='utf-8') as f:
                # Twitter exports often have a JavaScript variable assignment at the beginning
                content = f.read()
                content = re.sub(r'^window\.YTD\.follower\.part0\s*=\s*', '', content)
                followers_data = json.loads(content)
            
            logger.info(f"Found {len(followers_data)} followers in Twitter export")
            
            for follower_item in followers_data:
                try:
                    follower = follower_item.get('follower', {})
                    if not follower:
                        continue
                    
                    # Create normalized follower data
                    follower_data = {
                        'id': f"twitter_follower_{follower.get('accountId', '')}",
                        'username': follower.get('username', ''),
                        'display_name': follower.get('displayName', ''),
                        'bio': follower.get('description', ''),
                        'follower_of': self.user_info.get('username', 'me'),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'twitter',
                        'type': 'follower',
                        'source': 'twitter_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(follower_data):
                        self.item_count += 1
                        yield follower_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing follower: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting followers from Twitter export: {str(e)}")
    
    def _extract_following(self, following_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract following from a Twitter data export.
        
        Args:
            following_path: Path to the following.js file
            
        Yields:
            Dictionaries containing normalized following data
        """
        try:
            with open(following_path, 'r', encoding='utf-8') as f:
                # Twitter exports often have a JavaScript variable assignment at the beginning
                content = f.read()
                content = re.sub(r'^window\.YTD\.following\.part0\s*=\s*', '', content)
                following_data = json.loads(content)
            
            logger.info(f"Found {len(following_data)} following in Twitter export")
            
            for following_item in following_data:
                try:
                    following = following_item.get('following', {})
                    if not following:
                        continue
                    
                    # Create normalized following data
                    following_data = {
                        'id': f"twitter_following_{following.get('accountId', '')}",
                        'username': following.get('username', ''),
                        'display_name': following.get('displayName', ''),
                        'bio': following.get('description', ''),
                        'followed_by': self.user_info.get('username', 'me'),
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'twitter',
                        'type': 'following',
                        'source': 'twitter_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(following_data):
                        self.item_count += 1
                        yield following_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing following: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting following from Twitter export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
            
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Twitter data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item