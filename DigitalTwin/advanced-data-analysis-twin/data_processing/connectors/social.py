"""
Social media connector for extracting data from social media platforms.
"""

import asyncio
import json
import os
import re
import csv
import zipfile
import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from core.logging import get_logger
from core.utils import generate_id, timestamp_now, ensure_directory
from .base import DataConnectorBase

logger = get_logger(__name__)

class SocialMediaConnector(DataConnectorBase):
    """
    Connector for extracting data from social media platforms.
    
    This connector supports:
    - Twitter/X data exports
    - Facebook data exports
    - LinkedIn data exports
    - Instagram data exports
    - Reddit data exports
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the social media connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - platform: Social media platform ("twitter", "facebook", "linkedin", "instagram", "reddit")
                - source_path: Path to the data export file or directory
                - output_dir: Directory to save processed data (default: "data/social")
        """
        super().__init__(config)
        self.platform = config.get("platform", "").lower()
        self.source_path = config.get("source_path", "")
        self.output_dir = config.get("output_dir", "data/social")
        
        # Ensure output directory exists
        ensure_directory(self.output_dir)
        
        # Platform-specific handlers
        self.platform_handlers = {
            "twitter": self._extract_twitter,
            "facebook": self._extract_facebook,
            "linkedin": self._extract_linkedin,
            "instagram": self._extract_instagram,
            "reddit": self._extract_reddit,
        }
    
    async def connect(self) -> bool:
        """
        Verify that the source path exists and is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if source path exists
            if not os.path.exists(self.source_path):
                logger.error(f"Source path does not exist: {self.source_path}")
                return False
            
            # Check if platform is supported
            if self.platform not in self.platform_handlers:
                logger.error(f"Unsupported social media platform: {self.platform}")
                return False
            
            self.connected = True
            logger.info(f"Connected to {self.platform} data source: {self.source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.platform} data source: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the data source.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        self.connected = False
        return True
    
    async def extract_data(self, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract data from the social media platform.
        
        Args:
            parameters: Optional parameters for extraction:
                - content_types: List of content types to extract (posts, comments, messages, etc.)
                - start_date: Start date for filtering content (YYYY-MM-DD)
                - end_date: End date for filtering content (YYYY-MM-DD)
                - max_items: Maximum number of items to extract
        
        Returns:
            List of raw social media data dictionaries
        """
        if not self.connected:
            connected = await self.connect()
            if not connected:
                return []
        
        parameters = parameters or {}
        
        try:
            # Call platform-specific handler
            handler = self.platform_handlers.get(self.platform)
            if not handler:
                logger.error(f"No handler for platform: {self.platform}")
                return []
            
            raw_data = await handler(parameters)
            logger.info(f"Extracted {len(raw_data)} items from {self.platform}")
            return raw_data
            
        except Exception as e:
            logger.error(f"Failed to extract {self.platform} data: {str(e)}")
            return []
    
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw social media data into standardized format.
        
        Args:
            raw_data: Raw social media data from extraction
            
        Returns:
            List of standardized social media data dictionaries
        """
        transformed_items = []
        
        for raw_item in raw_data:
            try:
                # Create standardized social media item format
                item_data = {
                    "id": raw_item.get("id", generate_id("social")),
                    "source_id": f"{self.platform}_{raw_item.get('id', '')}",
                    "type": raw_item.get("type", "post"),
                    "platform": self.platform,
                    "date": raw_item.get("timestamp", ""),
                    "author": raw_item.get("author", ""),
                    "content": raw_item.get("content", ""),
                    "has_media": raw_item.get("has_media", False),
                    "media": raw_item.get("media", []),
                    "engagement": {
                        "likes": raw_item.get("likes", 0),
                        "comments": raw_item.get("comments", 0),
                        "shares": raw_item.get("shares", 0),
                    },
                    "metadata": {
                        "platform": self.platform,
                        "raw_id": raw_item.get("id", ""),
                        "content_type": raw_item.get("type", "post"),
                        "connector_id": self.connector_id,
                        "extraction_time": timestamp_now()
                    }
                }
                
                transformed_items.append(item_data)
                
            except Exception as e:
                logger.error(f"Failed to transform social media item: {str(e)}")
                continue
        
        return transformed_items
    
    async def validate_config(self) -> Dict[str, Any]:
        """
        Validate the connector configuration.
        
        Returns:
            Dictionary with validation results
        """
        # First run the base validation
        base_validation = await super().validate_config()
        if not base_validation["valid"]:
            return base_validation
        
        # Social media-specific validation
        required_fields = ["platform", "source_path"]
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "message": f"Missing required configuration fields: {', '.join(missing_fields)}"
            }
        
        # Check if platform is supported
        if self.platform not in self.platform_handlers:
            return {
                "valid": False,
                "message": f"Unsupported social media platform: {self.platform}"
            }
        
        return {
            "valid": True,
            "message": "Configuration is valid"
        }
    
    async def _extract_twitter(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Twitter/X data export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Twitter/X data dictionaries
        """
        items = []
        
        # Check if source is a file or directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Twitter source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["tweets", "direct_messages"])
        
        # Extract tweets
        if "tweets" in content_types:
            tweets = await self._extract_twitter_tweets(source_path, parameters)
            items.extend(tweets)
        
        # Extract direct messages
        if "direct_messages" in content_types:
            dms = await self._extract_twitter_dms(source_path, parameters)
            items.extend(dms)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_twitter_tweets(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tweets from Twitter data export.
        
        Args:
            source_path: Path to Twitter data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw tweet dictionaries
        """
        tweets = []
        
        # Look for tweet.js or tweets.js file
        tweet_files = list(source_path.glob("**/tweet*.js"))
        
        for tweet_file in tweet_files:
            try:
                # Read the file
                with open(tweet_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Twitter exports often start with a variable assignment
                # Remove it to get valid JSON
                if content.startswith("window.YTD.tweet"):
                    json_str = content[content.find('['):].strip()
                else:
                    json_str = content
                
                # Parse JSON
                tweet_data = json.loads(json_str)
                
                for tweet_entry in tweet_data:
                    # Twitter's export format can vary
                    if "tweet" in tweet_entry:
                        tweet = tweet_entry["tweet"]
                    else:
                        tweet = tweet_entry
                    
                    # Extract basic info
                    tweet_id = tweet.get("id", "") or tweet.get("id_str", "")
                    created_at = tweet.get("created_at", "")
                    full_text = tweet.get("full_text", "") or tweet.get("text", "")
                    
                    # Parse date
                    try:
                        # Twitter date format: "Wed Oct 10 20:19:24 +0000 2018"
                        date_obj = datetime.datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                        timestamp = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {created_at}: {str(e)}")
                        timestamp = timestamp_now()
                    
                    # Apply date filters
                    tweet_date = datetime.datetime.fromisoformat(timestamp.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if tweet_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if tweet_date > end_date:
                            continue
                    
                    # Extract media
                    media = []
                    has_media = False
                    
                    if "entities" in tweet and "media" in tweet["entities"]:
                        for media_item in tweet["entities"]["media"]:
                            media_type = media_item.get("type", "photo")
                            media_url = media_item.get("media_url_https", "") or media_item.get("media_url", "")
                            
                            if media_url:
                                has_media = True
                                media.append({
                                    "type": media_type,
                                    "url": media_url,
                                    "alt_text": media_item.get("ext_alt_text", "")
                                })
                    
                    # Extract engagement metrics
                    likes = tweet.get("favorite_count", 0)
                    retweets = tweet.get("retweet_count", 0)
                    replies = tweet.get("reply_count", 0)
                    
                    # Create tweet object
                    tweet_obj = {
                        "id": tweet_id,
                        "timestamp": timestamp,
                        "author": tweet.get("user", {}).get("screen_name", "") or "Me",
                        "content": full_text,
                        "has_media": has_media,
                        "media": media,
                        "type": "tweet",
                        "likes": likes,
                        "comments": replies,
                        "shares": retweets,
                        "in_reply_to": tweet.get("in_reply_to_status_id_str", None),
                        "is_retweet": "retweeted_status" in tweet,
                        "hashtags": [h["text"] for h in tweet.get("entities", {}).get("hashtags", [])],
                        "mentions": [m["screen_name"] for m in tweet.get("entities", {}).get("user_mentions", [])]
                    }
                    
                    tweets.append(tweet_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Twitter tweet file {tweet_file}: {str(e)}")
        
        logger.info(f"Extracted {len(tweets)} tweets from Twitter data export")
        return tweets
    
    async def _extract_twitter_dms(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract direct messages from Twitter data export.
        
        Args:
            source_path: Path to Twitter data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw direct message dictionaries
        """
        dms = []
        
        # Look for direct_messages.js file
        dm_files = list(source_path.glob("**/direct_message*.js"))
        
        for dm_file in dm_files:
            try:
                # Read the file
                with open(dm_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Twitter exports often start with a variable assignment
                # Remove it to get valid JSON
                if content.startswith("window.YTD.direct_message"):
                    json_str = content[content.find('['):].strip()
                else:
                    json_str = content
                
                # Parse JSON
                dm_data = json.loads(json_str)
                
                for dm_entry in dm_data:
                    # Twitter's export format can vary
                    if "dmConversation" in dm_entry:
                        conversation = dm_entry["dmConversation"]
                        messages = conversation.get("messages", [])
                    else:
                        messages = dm_entry.get("messages", [])
                    
                    for message in messages:
                        # Extract message data
                        message_id = message.get("id", "") or message.get("id_str", "")
                        created_at = message.get("created_at", "")
                        text = message.get("text", "")
                        sender_id = message.get("senderId", "") or message.get("sender_id", "")
                        recipient_id = message.get("recipientId", "") or message.get("recipient_id", "")
                        
                        # Parse date
                        try:
                            # Twitter date format can vary
                            date_formats = [
                                "%a %b %d %H:%M:%S %z %Y",  # Wed Oct 10 20:19:24 +0000 2018
                                "%Y-%m-%dT%H:%M:%S.%fZ"      # 2018-10-10T20:19:24.000Z
                            ]
                            
                            timestamp = None
                            for fmt in date_formats:
                                try:
                                    date_obj = datetime.datetime.strptime(created_at, fmt)
                                    timestamp = date_obj.isoformat()
                                    break
                                except ValueError:
                                    continue
                            
                            if not timestamp:
                                raise ValueError(f"Could not parse date: {created_at}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {created_at}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        message_date = datetime.datetime.fromisoformat(timestamp.split("+")[0].split("Z")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if message_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if message_date > end_date:
                                continue
                        
                        # Extract media
                        media = []
                        has_media = False
                        
                        if "mediaUrls" in message and message["mediaUrls"]:
                            has_media = True
                            for media_url in message["mediaUrls"]:
                                media.append({
                                    "type": "photo",  # Twitter DM exports don't specify media type
                                    "url": media_url,
                                    "alt_text": ""
                                })
                        
                        # Create DM object
                        dm_obj = {
                            "id": message_id,
                            "timestamp": timestamp,
                            "author": sender_id,
                            "recipient": recipient_id,
                            "content": text,
                            "has_media": has_media,
                            "media": media,
                            "type": "direct_message",
                            "likes": 0,
                            "comments": 0,
                            "shares": 0
                        }
                        
                        dms.append(dm_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Twitter DM file {dm_file}: {str(e)}")
        
        logger.info(f"Extracted {len(dms)} direct messages from Twitter data export")
        return dms
    
    async def _extract_facebook(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Facebook data export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Facebook data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Facebook source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["posts", "comments", "messages"])
        
        # Extract posts
        if "posts" in content_types:
            posts = await self._extract_facebook_posts(source_path, parameters)
            items.extend(posts)
        
        # Extract comments
        if "comments" in content_types:
            comments = await self._extract_facebook_comments(source_path, parameters)
            items.extend(comments)
        
        # Extract messages
        if "messages" in content_types:
            messages = await self._extract_facebook_messages(source_path, parameters)
            items.extend(messages)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_facebook_posts(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract posts from Facebook data export.
        
        Args:
            source_path: Path to Facebook data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw post dictionaries
        """
        posts = []
        
        # Look for posts directory or file
        posts_dir = source_path / "posts"
        posts_file = source_path / "posts/your_posts.json"
        
        if posts_file.exists():
            try:
                # Read the file
                with open(posts_file, 'r', encoding='utf-8') as f:
                    posts_data = json.load(f)
                
                # Process posts
                for post in posts_data.get("status_updates", []):
                    # Extract basic info
                    post_id = post.get("id", generate_id("fb_post"))
                    timestamp = post.get("timestamp", 0)
                    
                    # Convert timestamp to ISO format
                    try:
                        # Facebook timestamps are in seconds since epoch
                        date_obj = datetime.datetime.fromtimestamp(timestamp)
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    post_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if post_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if post_date > end_date:
                            continue
                    
                    # Extract content
                    content = post.get("data", [{}])[0].get("post", "")
                    
                    # Extract media
                    media = []
                    has_media = False
                    
                    if "attachments" in post:
                        for attachment in post["attachments"]:
                            for data in attachment.get("data", []):
                                if "media" in data:
                                    has_media = True
                                    media_item = data["media"]
                                    
                                    media_type = "photo"
                                    if "video" in media_item:
                                        media_type = "video"
                                    
                                    media_url = media_item.get("uri", "")
                                    
                                    media.append({
                                        "type": media_type,
                                        "url": media_url,
                                        "description": data.get("description", "")
                                    })
                    
                    # Create post object
                    post_obj = {
                        "id": post_id,
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Facebook exports are for the user's own data
                        "content": content,
                        "has_media": has_media,
                        "media": media,
                        "type": "post",
                        "likes": 0,  # Facebook exports don't include engagement metrics
                        "comments": 0,
                        "shares": 0
                    }
                    
                    posts.append(post_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Facebook posts file: {str(e)}")
        
        # Look for timeline posts
        timeline_file = source_path / "posts/your_posts_1.json"
        if timeline_file.exists():
            try:
                # Read the file
                with open(timeline_file, 'r', encoding='utf-8') as f:
                    timeline_data = json.load(f)
                
                # Process timeline posts
                for post in timeline_data:
                    # Extract basic info
                    post_id = post.get("timestamp", generate_id("fb_post"))
                    timestamp = post.get("timestamp", 0)
                    
                    # Convert timestamp to ISO format
                    try:
                        # Facebook timestamps are in seconds since epoch
                        date_obj = datetime.datetime.fromtimestamp(int(timestamp))
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    post_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if post_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if post_date > end_date:
                            continue
                    
                    # Extract content
                    content = post.get("data", [{}])[0].get("post", "")
                    
                    # Extract media
                    media = []
                    has_media = False
                    
                    if "attachments" in post:
                        for attachment in post["attachments"]:
                            for data in attachment.get("data", []):
                                if "media" in data:
                                    has_media = True
                                    media_item = data["media"]
                                    
                                    media_type = "photo"
                                    if "video" in media_item:
                                        media_type = "video"
                                    
                                    media_url = media_item.get("uri", "")
                                    
                                    media.append({
                                        "type": media_type,
                                        "url": media_url,
                                        "description": data.get("description", "")
                                    })
                    
                    # Create post object
                    post_obj = {
                        "id": str(post_id),
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Facebook exports are for the user's own data
                        "content": content,
                        "has_media": has_media,
                        "media": media,
                        "type": "post",
                        "likes": 0,  # Facebook exports don't include engagement metrics
                        "comments": 0,
                        "shares": 0
                    }
                    
                    posts.append(post_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Facebook timeline posts file: {str(e)}")
        
        logger.info(f"Extracted {len(posts)} posts from Facebook data export")
        return posts
    
    async def _extract_facebook_comments(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract comments from Facebook data export.
        
        Args:
            source_path: Path to Facebook data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw comment dictionaries
        """
        comments = []
        
        # Look for comments directory or file
        comments_file = source_path / "comments/comments.json"
        
        if comments_file.exists():
            try:
                # Read the file
                with open(comments_file, 'r', encoding='utf-8') as f:
                    comments_data = json.load(f)
                
                # Process comments
                for comment in comments_data.get("comments", []):
                    # Extract basic info
                    comment_id = comment.get("timestamp", generate_id("fb_comment"))
                    timestamp = comment.get("timestamp", 0)
                    
                    # Convert timestamp to ISO format
                    try:
                        # Facebook timestamps are in seconds since epoch
                        date_obj = datetime.datetime.fromtimestamp(int(timestamp))
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    comment_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if comment_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if comment_date > end_date:
                            continue
                    
                    # Extract content
                    content = comment.get("data", [{}])[0].get("comment", {}).get("comment", "")
                    
                    # Extract author
                    author = comment.get("title", "").replace("You commented on ", "")
                    
                    # Create comment object
                    comment_obj = {
                        "id": str(comment_id),
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Facebook exports are for the user's own data
                        "content": content,
                        "has_media": False,
                        "media": [],
                        "type": "comment",
                        "likes": 0,  # Facebook exports don't include engagement metrics
                        "comments": 0,
                        "shares": 0,
                        "parent_post": author
                    }
                    
                    comments.append(comment_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Facebook comments file: {str(e)}")
        
        logger.info(f"Extracted {len(comments)} comments from Facebook data export")
        return comments
    
    async def _extract_facebook_messages(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract messages from Facebook data export.
        
        Args:
            source_path: Path to Facebook data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw message dictionaries
        """
        messages = []
        
        # Look for messages directory
        messages_dir = source_path / "messages"
        
        if not messages_dir.exists() or not messages_dir.is_dir():
            logger.warning(f"Facebook messages directory not found: {messages_dir}")
            return []
        
        # Look for message files (inbox, archived_threads, etc.)
        inbox_dir = messages_dir / "inbox"
        archived_dir = messages_dir / "archived_threads"
        
        message_dirs = []
        
        if inbox_dir.exists() and inbox_dir.is_dir():
            message_dirs.append(inbox_dir)
        
        if archived_dir.exists() and archived_dir.is_dir():
            message_dirs.append(archived_dir)
        
        # Process each conversation directory
        for message_dir in message_dirs:
            for convo_dir in message_dir.iterdir():
                if not convo_dir.is_dir():
                    continue
                
                # Look for message files (message_1.json, etc.)
                message_files = list(convo_dir.glob("message_*.json"))
                
                for message_file in message_files:
                    try:
                        # Read the file
                        with open(message_file, 'r', encoding='utf-8') as f:
                            convo_data = json.load(f)
                        
                        # Extract conversation metadata
                        convo_title = convo_data.get("title", "")
                        participants = [p.get("name", "") for p in convo_data.get("participants", [])]
                        is_group = len(participants) > 2
                        
                        # Process messages
                        for message in convo_data.get("messages", []):
                            # Extract basic info
                            message_id = message.get("timestamp_ms", generate_id("fb_message"))
                            timestamp_ms = message.get("timestamp_ms", 0)
                            
                            # Convert timestamp to ISO format
                            try:
                                # Facebook timestamps are in milliseconds since epoch
                                date_obj = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
                                timestamp_iso = date_obj.isoformat()
                            except Exception as e:
                                logger.warning(f"Failed to parse date: {timestamp_ms}: {str(e)}")
                                timestamp_iso = timestamp_now()
                            
                            # Apply date filters
                            message_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                            
                            if parameters.get("start_date"):
                                start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                                if message_date < start_date:
                                    continue
                            
                            if parameters.get("end_date"):
                                end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                                if message_date > end_date:
                                    continue
                            
                            # Extract sender and content
                            sender_name = message.get("sender_name", "")
                            content = message.get("content", "")
                            
                            # Extract media
                            media = []
                            has_media = False
                            
                            # Photos
                            if "photos" in message:
                                has_media = True
                                for photo in message["photos"]:
                                    media.append({
                                        "type": "photo",
                                        "url": photo.get("uri", ""),
                                        "description": ""
                                    })
                            
                            # Videos
                            if "videos" in message:
                                has_media = True
                                for video in message["videos"]:
                                    media.append({
                                        "type": "video",
                                        "url": video.get("uri", ""),
                                        "description": ""
                                    })
                            
                            # Files
                            if "files" in message:
                                has_media = True
                                for file in message["files"]:
                                    media.append({
                                        "type": "file",
                                        "url": file.get("uri", ""),
                                        "description": ""
                                    })
                            
                            # Create message object
                            message_obj = {
                                "id": str(message_id),
                                "timestamp": timestamp_iso,
                                "author": sender_name,
                                "content": content,
                                "has_media": has_media,
                                "media": media,
                                "type": "message",
                                "likes": 0,
                                "comments": 0,
                                "shares": 0,
                                "conversation": convo_title,
                                "is_group": is_group
                            }
                            
                            messages.append(message_obj)
                    
                    except Exception as e:
                        logger.error(f"Failed to process Facebook message file {message_file}: {str(e)}")
        
        logger.info(f"Extracted {len(messages)} messages from Facebook data export")
        return messages
    
    async def _extract_linkedin(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from LinkedIn data export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw LinkedIn data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid LinkedIn source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["posts", "messages", "connections"])
        
        # Extract posts
        if "posts" in content_types:
            posts = await self._extract_linkedin_posts(source_path, parameters)
            items.extend(posts)
        
        # Extract messages
        if "messages" in content_types:
            messages = await self._extract_linkedin_messages(source_path, parameters)
            items.extend(messages)
        
        # Extract connections
        if "connections" in content_types:
            connections = await self._extract_linkedin_connections(source_path, parameters)
            items.extend(connections)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_linkedin_posts(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract posts from LinkedIn data export.
        
        Args:
            source_path: Path to LinkedIn data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw post dictionaries
        """
        posts = []
        
        # Look for posts file
        posts_file = source_path / "Posts/Posts.csv"
        
        if posts_file.exists():
            try:
                # Read the CSV file
                with open(posts_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        post_id = generate_id("li_post")
                        date_str = row.get("Date", "")
                        content = row.get("Content", "")
                        
                        # Parse date
                        try:
                            # LinkedIn date format: MM/DD/YYYY
                            date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
                            timestamp = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        post_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if post_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if post_date > end_date:
                                continue
                        
                        # Extract engagement metrics
                        likes = int(row.get("Likes", "0") or "0")
                        comments = int(row.get("Comments", "0") or "0")
                        
                        # Create post object
                        post_obj = {
                            "id": post_id,
                            "timestamp": timestamp,
                            "author": "Me",  # LinkedIn exports are for the user's own data
                            "content": content,
                            "has_media": False,  # LinkedIn exports don't include media info
                            "media": [],
                            "type": "post",
                            "likes": likes,
                            "comments": comments,
                            "shares": 0
                        }
                        
                        posts.append(post_obj)
            
            except Exception as e:
                logger.error(f"Failed to process LinkedIn posts file: {str(e)}")
        
        logger.info(f"Extracted {len(posts)} posts from LinkedIn data export")
        return posts
    
    async def _extract_linkedin_messages(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract messages from LinkedIn data export.
        
        Args:
            source_path: Path to LinkedIn data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw message dictionaries
        """
        messages = []
        
        # Look for messages directory
        messages_dir = source_path / "Messages"
        
        if not messages_dir.exists() or not messages_dir.is_dir():
            logger.warning(f"LinkedIn messages directory not found: {messages_dir}")
            return []
        
        # Process each conversation file
        for message_file in messages_dir.glob("*.csv"):
            try:
                # Extract conversation name from filename
                convo_name = message_file.stem
                
                # Read the CSV file
                with open(message_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        message_id = generate_id("li_message")
                        date_str = row.get("DATE", "") or row.get("Date", "")
                        content = row.get("CONTENT", "") or row.get("Content", "")
                        sender = row.get("FROM", "") or row.get("From", "")
                        
                        # Parse date
                        try:
                            # LinkedIn date format can vary
                            date_formats = [
                                "%m/%d/%Y, %I:%M %p",  # 01/01/2020, 12:00 PM
                                "%m/%d/%y, %I:%M %p",  # 01/01/20, 12:00 PM
                                "%B %d, %Y, %I:%M %p"  # January 1, 2020, 12:00 PM
                            ]
                            
                            timestamp = None
                            for fmt in date_formats:
                                try:
                                    date_obj = datetime.datetime.strptime(date_str, fmt)
                                    timestamp = date_obj.isoformat()
                                    break
                                except ValueError:
                                    continue
                            
                            if not timestamp:
                                raise ValueError(f"Could not parse date: {date_str}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        message_date = datetime.datetime.fromisoformat(timestamp.split("+")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if message_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if message_date > end_date:
                                continue
                        
                        # Create message object
                        message_obj = {
                            "id": message_id,
                            "timestamp": timestamp,
                            "author": sender,
                            "content": content,
                            "has_media": False,  # LinkedIn exports don't include media info
                            "media": [],
                            "type": "message",
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "conversation": convo_name
                        }
                        
                        messages.append(message_obj)
            
            except Exception as e:
                logger.error(f"Failed to process LinkedIn message file {message_file}: {str(e)}")
        
        logger.info(f"Extracted {len(messages)} messages from LinkedIn data export")
        return messages
    
    async def _extract_linkedin_connections(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract connections from LinkedIn data export.
        
        Args:
            source_path: Path to LinkedIn data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw connection dictionaries
        """
        connections = []
        
        # Look for connections file
        connections_file = source_path / "Connections/Connections.csv"
        
        if connections_file.exists():
            try:
                # Read the CSV file
                with open(connections_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        connection_id = generate_id("li_connection")
                        first_name = row.get("First Name", "")
                        last_name = row.get("Last Name", "")
                        name = f"{first_name} {last_name}".strip()
                        company = row.get("Company", "")
                        position = row.get("Position", "")
                        date_str = row.get("Connected On", "")
                        
                        # Parse date
                        try:
                            # LinkedIn date format: DD MMM YYYY
                            date_obj = datetime.datetime.strptime(date_str, "%d %b %Y")
                            timestamp = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        connection_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if connection_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if connection_date > end_date:
                                continue
                        
                        # Create connection object
                        connection_obj = {
                            "id": connection_id,
                            "timestamp": timestamp,
                            "author": name,
                            "content": f"{name} - {position} at {company}",
                            "has_media": False,
                            "media": [],
                            "type": "connection",
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "company": company,
                            "position": position
                        }
                        
                        connections.append(connection_obj)
            
            except Exception as e:
                logger.error(f"Failed to process LinkedIn connections file: {str(e)}")
        
        logger.info(f"Extracted {len(connections)} connections from LinkedIn data export")
        return connections
    
    async def _extract_instagram(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Instagram data export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Instagram data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Instagram source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["posts", "stories", "comments", "messages"])
        
        # Extract posts
        if "posts" in content_types:
            posts = await self._extract_instagram_posts(source_path, parameters)
            items.extend(posts)
        
        # Extract stories
        if "stories" in content_types:
            stories = await self._extract_instagram_stories(source_path, parameters)
            items.extend(stories)
        
        # Extract comments
        if "comments" in content_types:
            comments = await self._extract_instagram_comments(source_path, parameters)
            items.extend(comments)
        
        # Extract messages
        if "messages" in content_types:
            messages = await self._extract_instagram_messages(source_path, parameters)
            items.extend(messages)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_instagram_posts(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract posts from Instagram data export.
        
        Args:
            source_path: Path to Instagram data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw post dictionaries
        """
        posts = []
        
        # Look for posts file
        posts_file = source_path / "content/posts_1.json"
        
        if posts_file.exists():
            try:
                # Read the file
                with open(posts_file, 'r', encoding='utf-8') as f:
                    posts_data = json.load(f)
                
                # Process posts
                for post in posts_data:
                    # Extract basic info
                    post_id = post.get("media_id", generate_id("ig_post"))
                    timestamp = post.get("creation_timestamp", 0)
                    
                    # Convert timestamp to ISO format
                    try:
                        # Instagram timestamps are in seconds since epoch
                        date_obj = datetime.datetime.fromtimestamp(int(timestamp))
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    post_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if post_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if post_date > end_date:
                            continue
                    
                    # Extract content
                    caption = post.get("caption", "")
                    
                    # Extract media
                    media = []
                    has_media = False
                    
                    if "media" in post:
                        has_media = True
                        for media_item in post["media"]:
                            media_type = "photo"
                            if media_item.get("media_type") == "VIDEO":
                                media_type = "video"
                            
                            media_url = media_item.get("uri", "")
                            
                            media.append({
                                "type": media_type,
                                "url": media_url,
                                "description": ""
                            })
                    
                    # Extract engagement metrics
                    likes = len(post.get("likes", []))
                    comments = len(post.get("comments", []))
                    
                    # Create post object
                    post_obj = {
                        "id": post_id,
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Instagram exports are for the user's own data
                        "content": caption,
                        "has_media": has_media,
                        "media": media,
                        "type": "post",
                        "likes": likes,
                        "comments": comments,
                        "shares": 0,
                        "location": post.get("location", "")
                    }
                    
                    posts.append(post_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Instagram posts file: {str(e)}")
        
        logger.info(f"Extracted {len(posts)} posts from Instagram data export")
        return posts
    
    async def _extract_instagram_stories(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract stories from Instagram data export.
        
        Args:
            source_path: Path to Instagram data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw story dictionaries
        """
        stories = []
        
        # Look for stories file
        stories_file = source_path / "content/stories.json"
        
        if stories_file.exists():
            try:
                # Read the file
                with open(stories_file, 'r', encoding='utf-8') as f:
                    stories_data = json.load(f)
                
                # Process stories
                for story in stories_data.get("stories", []):
                    # Extract basic info
                    story_id = story.get("uri", "").split("/")[-1].split(".")[0]
                    if not story_id:
                        story_id = generate_id("ig_story")
                    
                    timestamp = story.get("creation_timestamp", 0)
                    
                    # Convert timestamp to ISO format
                    try:
                        # Instagram timestamps are in seconds since epoch
                        date_obj = datetime.datetime.fromtimestamp(int(timestamp))
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    story_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if story_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if story_date > end_date:
                            continue
                    
                    # Extract media
                    media_type = "photo"
                    if story.get("uri", "").endswith((".mp4", ".mov")):
                        media_type = "video"
                    
                    media = [{
                        "type": media_type,
                        "url": story.get("uri", ""),
                        "description": ""
                    }]
                    
                    # Create story object
                    story_obj = {
                        "id": story_id,
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Instagram exports are for the user's own data
                        "content": "",
                        "has_media": True,
                        "media": media,
                        "type": "story",
                        "likes": 0,
                        "comments": 0,
                        "shares": 0
                    }
                    
                    stories.append(story_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Instagram stories file: {str(e)}")
        
        logger.info(f"Extracted {len(stories)} stories from Instagram data export")
        return stories
    
    async def _extract_instagram_comments(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract comments from Instagram data export.
        
        Args:
            source_path: Path to Instagram data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw comment dictionaries
        """
        comments = []
        
        # Look for comments file
        comments_file = source_path / "comments/comments.json"
        
        if comments_file.exists():
            try:
                # Read the file
                with open(comments_file, 'r', encoding='utf-8') as f:
                    comments_data = json.load(f)
                
                # Process comments
                for comment_entry in comments_data.get("comments_media_comments", []):
                    # Extract basic info
                    comment_id = generate_id("ig_comment")
                    timestamp = comment_entry.get("created_at", "")
                    
                    # Convert timestamp to ISO format
                    try:
                        # Instagram comment timestamps are in format: YYYY-MM-DDTHH:MM:SS
                        date_obj = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        timestamp_iso = date_obj.isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {timestamp}: {str(e)}")
                        timestamp_iso = timestamp_now()
                    
                    # Apply date filters
                    comment_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if comment_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if comment_date > end_date:
                            continue
                    
                    # Extract content
                    content = comment_entry.get("string_map_data", {}).get("comment", {}).get("value", "")
                    
                    # Create comment object
                    comment_obj = {
                        "id": comment_id,
                        "timestamp": timestamp_iso,
                        "author": "Me",  # Instagram exports are for the user's own data
                        "content": content,
                        "has_media": False,
                        "media": [],
                        "type": "comment",
                        "likes": 0,
                        "comments": 0,
                        "shares": 0
                    }
                    
                    comments.append(comment_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Instagram comments file: {str(e)}")
        
        logger.info(f"Extracted {len(comments)} comments from Instagram data export")
        return comments
    
    async def _extract_instagram_messages(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract messages from Instagram data export.
        
        Args:
            source_path: Path to Instagram data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw message dictionaries
        """
        messages = []
        
        # Look for messages directory
        messages_dir = source_path / "messages/inbox"
        
        if not messages_dir.exists() or not messages_dir.is_dir():
            logger.warning(f"Instagram messages directory not found: {messages_dir}")
            return []
        
        # Process each conversation directory
        for convo_dir in messages_dir.iterdir():
            if not convo_dir.is_dir():
                continue
            
            # Look for message files (message_1.json, etc.)
            message_files = list(convo_dir.glob("message_*.json"))
            
            for message_file in message_files:
                try:
                    # Read the file
                    with open(message_file, 'r', encoding='utf-8') as f:
                        convo_data = json.load(f)
                    
                    # Extract conversation metadata
                    convo_title = convo_data.get("title", "")
                    participants = convo_data.get("participants", [])
                    is_group = len(participants) > 2
                    
                    # Process messages
                    for message in convo_data.get("messages", []):
                        # Extract basic info
                        message_id = message.get("timestamp_ms", generate_id("ig_message"))
                        timestamp_ms = message.get("timestamp_ms", 0)
                        
                        # Convert timestamp to ISO format
                        try:
                            # Instagram timestamps are in milliseconds since epoch
                            date_obj = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
                            timestamp_iso = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {timestamp_ms}: {str(e)}")
                            timestamp_iso = timestamp_now()
                        
                        # Apply date filters
                        message_date = datetime.datetime.fromisoformat(timestamp_iso.split("+")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if message_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if message_date > end_date:
                                continue
                        
                        # Extract sender and content
                        sender_name = message.get("sender_name", "")
                        content = message.get("content", "")
                        
                        # Extract media
                        media = []
                        has_media = False
                        
                        # Photos
                        if "photos" in message:
                            has_media = True
                            for photo in message["photos"]:
                                media.append({
                                    "type": "photo",
                                    "url": photo.get("uri", ""),
                                    "description": ""
                                })
                        
                        # Videos
                        if "videos" in message:
                            has_media = True
                            for video in message["videos"]:
                                media.append({
                                    "type": "video",
                                    "url": video.get("uri", ""),
                                    "description": ""
                                })
                        
                        # Create message object
                        message_obj = {
                            "id": str(message_id),
                            "timestamp": timestamp_iso,
                            "author": sender_name,
                            "content": content,
                            "has_media": has_media,
                            "media": media,
                            "type": "message",
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "conversation": convo_title,
                            "is_group": is_group
                        }
                        
                        messages.append(message_obj)
                
                except Exception as e:
                    logger.error(f"Failed to process Instagram message file {message_file}: {str(e)}")
        
        logger.info(f"Extracted {len(messages)} messages from Instagram data export")
        return messages
    
    async def _extract_reddit(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Reddit data export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Reddit data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Reddit source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["posts", "comments", "saved"])
        
        # Extract posts
        if "posts" in content_types:
            posts = await self._extract_reddit_posts(source_path, parameters)
            items.extend(posts)
        
        # Extract comments
        if "comments" in content_types:
            comments = await self._extract_reddit_comments(source_path, parameters)
            items.extend(comments)
        
        # Extract saved items
        if "saved" in content_types:
            saved = await self._extract_reddit_saved(source_path, parameters)
            items.extend(saved)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_reddit_posts(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract posts from Reddit data export.
        
        Args:
            source_path: Path to Reddit data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw post dictionaries
        """
        posts = []
        
        # Look for posts file
        posts_file = source_path / "posts.csv"
        
        if posts_file.exists():
            try:
                # Read the CSV file
                with open(posts_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        post_id = row.get("id", generate_id("reddit_post"))
                        date_str = row.get("created_utc", "")
                        title = row.get("title", "")
                        content = row.get("selftext", "")
                        subreddit = row.get("subreddit", "")
                        
                        # Parse date
                        try:
                            # Reddit timestamps are in seconds since epoch
                            date_obj = datetime.datetime.fromtimestamp(float(date_str))
                            timestamp = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        post_date = datetime.datetime.fromisoformat(timestamp.split("+")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if post_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if post_date > end_date:
                                continue
                        
                        # Extract engagement metrics
                        upvotes = int(row.get("score", "0") or "0")
                        num_comments = int(row.get("num_comments", "0") or "0")
                        
                        # Check for media
                        has_media = False
                        media = []
                        
                        url = row.get("url", "")
                        if url and any(url.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"]):
                            has_media = True
                            
                            media_type = "photo"
                            if url.endswith((".mp4", ".webm")):
                                media_type = "video"
                            
                            media.append({
                                "type": media_type,
                                "url": url,
                                "description": title
                            })
                        
                        # Create post object
                        post_obj = {
                            "id": post_id,
                            "timestamp": timestamp,
                            "author": row.get("author", "Me"),
                            "content": f"{title}\n\n{content}".strip(),
                            "has_media": has_media,
                            "media": media,
                            "type": "post",
                            "likes": upvotes,
                            "comments": num_comments,
                            "shares": 0,
                            "subreddit": subreddit,
                            "url": url
                        }
                        
                        posts.append(post_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Reddit posts file: {str(e)}")
        
        logger.info(f"Extracted {len(posts)} posts from Reddit data export")
        return posts
    
    async def _extract_reddit_comments(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract comments from Reddit data export.
        
        Args:
            source_path: Path to Reddit data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw comment dictionaries
        """
        comments = []
        
        # Look for comments file
        comments_file = source_path / "comments.csv"
        
        if comments_file.exists():
            try:
                # Read the CSV file
                with open(comments_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        comment_id = row.get("id", generate_id("reddit_comment"))
                        date_str = row.get("created_utc", "")
                        content = row.get("body", "")
                        subreddit = row.get("subreddit", "")
                        
                        # Parse date
                        try:
                            # Reddit timestamps are in seconds since epoch
                            date_obj = datetime.datetime.fromtimestamp(float(date_str))
                            timestamp = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        comment_date = datetime.datetime.fromisoformat(timestamp.split("+")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if comment_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if comment_date > end_date:
                                continue
                        
                        # Extract engagement metrics
                        upvotes = int(row.get("score", "0") or "0")
                        
                        # Create comment object
                        comment_obj = {
                            "id": comment_id,
                            "timestamp": timestamp,
                            "author": row.get("author", "Me"),
                            "content": content,
                            "has_media": False,
                            "media": [],
                            "type": "comment",
                            "likes": upvotes,
                            "comments": 0,
                            "shares": 0,
                            "subreddit": subreddit,
                            "parent_id": row.get("parent_id", ""),
                            "link_id": row.get("link_id", "")
                        }
                        
                        comments.append(comment_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Reddit comments file: {str(e)}")
        
        logger.info(f"Extracted {len(comments)} comments from Reddit data export")
        return comments
    
    async def _extract_reddit_saved(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract saved items from Reddit data export.
        
        Args:
            source_path: Path to Reddit data export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw saved item dictionaries
        """
        saved_items = []
        
        # Look for saved posts file
        saved_file = source_path / "saved.csv"
        
        if saved_file.exists():
            try:
                # Read the CSV file
                with open(saved_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.DictReader(f)
                    
                    for row in csv_reader:
                        # Extract basic info
                        item_id = row.get("id", generate_id("reddit_saved"))
                        date_str = row.get("created_utc", "")
                        title = row.get("title", "")
                        content = row.get("body", "") or row.get("selftext", "")
                        subreddit = row.get("subreddit", "")
                        item_type = "post" if "selftext" in row else "comment"
                        
                        # Parse date
                        try:
                            # Reddit timestamps are in seconds since epoch
                            date_obj = datetime.datetime.fromtimestamp(float(date_str))
                            timestamp = date_obj.isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        item_date = datetime.datetime.fromisoformat(timestamp.split("+")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if item_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if item_date > end_date:
                                continue
                        
                        # Extract engagement metrics
                        upvotes = int(row.get("score", "0") or "0")
                        num_comments = int(row.get("num_comments", "0") or "0")
                        
                        # Check for media
                        has_media = False
                        media = []
                        
                        url = row.get("url", "")
                        if url and any(url.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"]):
                            has_media = True
                            
                            media_type = "photo"
                            if url.endswith((".mp4", ".webm")):
                                media_type = "video"
                            
                            media.append({
                                "type": media_type,
                                "url": url,
                                "description": title
                            })
                        
                        # Create saved item object
                        item_obj = {
                            "id": item_id,
                            "timestamp": timestamp,
                            "author": row.get("author", ""),
                            "content": f"{title}\n\n{content}".strip() if title else content,
                            "has_media": has_media,
                            "media": media,
                            "type": f"saved_{item_type}",
                            "likes": upvotes,
                            "comments": num_comments,
                            "shares": 0,
                            "subreddit": subreddit,
                            "url": url
                        }
                        
                        saved_items.append(item_obj)
            
            except Exception as e:
                logger.error(f"Failed to process Reddit saved items file: {str(e)}")
        
        logger.info(f"Extracted {len(saved_items)} saved items from Reddit data export")
        return saved_items