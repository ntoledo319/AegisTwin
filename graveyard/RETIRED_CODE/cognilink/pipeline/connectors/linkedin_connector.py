"""
LinkedIn Connector for CogniLink

This module provides functionality to import data from LinkedIn exports,
including profile information, connections, messages, and activity.
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

class LinkedInConnector(BaseConnector):
    """
    Connector for importing LinkedIn data.
    
    This class handles extraction of profile information, connections, messages,
    and activity from LinkedIn data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LinkedIn connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "linkedin"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a LinkedIn data export file.
        
        Args:
            file_path: Path to the LinkedIn data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["profile", "connections", "messages"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["profile", "connections", "messages", "posts", "reactions", "comments", "jobs"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_linkedin_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_linkedin_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_linkedin_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a LinkedIn data export directory.
        
        Args:
            directory_path: Path to the LinkedIn data export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            profile_path = os.path.join(directory_path, "Profile.csv")
            if os.path.exists(profile_path):
                yield from self._extract_profile_from_csv(profile_path)
            
            # Try alternate location
            profile_path = os.path.join(directory_path, "profile", "profile.json")
            if os.path.exists(profile_path):
                yield from self._extract_profile_from_json(profile_path)
        
        # Extract connections
        if "connections" in data_types:
            connections_path = os.path.join(directory_path, "Connections.csv")
            if os.path.exists(connections_path):
                yield from self._extract_connections_from_csv(connections_path)
            
            # Try alternate location
            connections_path = os.path.join(directory_path, "connections", "connections.json")
            if os.path.exists(connections_path):
                yield from self._extract_connections_from_json(connections_path)
        
        # Extract messages
        if "messages" in data_types:
            messages_dir = os.path.join(directory_path, "messages")
            if os.path.exists(messages_dir) and os.path.isdir(messages_dir):
                for file_name in os.listdir(messages_dir):
                    if file_name.endswith(".csv"):
                        messages_path = os.path.join(messages_dir, file_name)
                        yield from self._extract_messages_from_csv(messages_path)
            
            # Try alternate location
            messages_path = os.path.join(directory_path, "messages", "messages.json")
            if os.path.exists(messages_path):
                yield from self._extract_messages_from_json(messages_path)
        
        # Extract posts
        if "posts" in data_types:
            posts_path = os.path.join(directory_path, "Posts.csv")
            if os.path.exists(posts_path):
                yield from self._extract_posts_from_csv(posts_path)
            
            # Try alternate location
            posts_path = os.path.join(directory_path, "shares", "shares.json")
            if os.path.exists(posts_path):
                yield from self._extract_posts_from_json(posts_path)
        
        # Extract reactions
        if "reactions" in data_types:
            reactions_path = os.path.join(directory_path, "Reactions.csv")
            if os.path.exists(reactions_path):
                yield from self._extract_reactions_from_csv(reactions_path)
            
            # Try alternate location
            reactions_path = os.path.join(directory_path, "reactions", "reactions.json")
            if os.path.exists(reactions_path):
                yield from self._extract_reactions_from_json(reactions_path)
        
        # Extract comments
        if "comments" in data_types:
            comments_path = os.path.join(directory_path, "Comments.csv")
            if os.path.exists(comments_path):
                yield from self._extract_comments_from_csv(comments_path)
            
            # Try alternate location
            comments_path = os.path.join(directory_path, "comments", "comments.json")
            if os.path.exists(comments_path):
                yield from self._extract_comments_from_json(comments_path)
        
        # Extract job applications
        if "jobs" in data_types:
            jobs_path = os.path.join(directory_path, "Job Applications.csv")
            if os.path.exists(jobs_path):
                yield from self._extract_jobs_from_csv(jobs_path)
            
            # Try alternate location
            jobs_path = os.path.join(directory_path, "job_applications", "job_applications.json")
            if os.path.exists(jobs_path):
                yield from self._extract_jobs_from_json(jobs_path)
    
    def _extract_profile_from_csv(self, profile_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract profile information from a LinkedIn Profile.csv file.
        
        Args:
            profile_path: Path to the Profile.csv file
                
        Yields:
            Normalized profile data
        """
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                profile_data = next(reader, {})
            
            # Store user info for later use
            self.user_info = profile_data
            
            # Create normalized profile data
            profile = {
                'id': f"linkedin_profile_{profile_data.get('First Name', '')}_{profile_data.get('Last Name', '')}",
                'first_name': profile_data.get('First Name', ''),
                'last_name': profile_data.get('Last Name', ''),
                'headline': profile_data.get('Headline', ''),
                'email': profile_data.get('Email Address', ''),
                'location': profile_data.get('Location', ''),
                'industry': profile_data.get('Industry', ''),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'linkedin',
                'type': 'profile',
                'source': 'linkedin_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing LinkedIn profile: {str(e)}")
    
    def _extract_profile_from_json(self, profile_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract profile information from a LinkedIn profile.json file.
        
        Args:
            profile_path: Path to the profile.json file
                
        Yields:
            Normalized profile data
        """
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Store user info for later use
            self.user_info = profile_data
            
            # Handle different LinkedIn export formats
            profile_info = {}
            
            # Format 1: Direct object
            if 'firstName' in profile_data:
                profile_info = profile_data
            
            # Format 2: Nested under 'profile'
            elif 'profile' in profile_data:
                profile_info = profile_data.get('profile', {})
            
            # Create normalized profile data
            profile = {
                'id': f"linkedin_profile_{profile_info.get('firstName', '')}_{profile_info.get('lastName', '')}",
                'first_name': profile_info.get('firstName', ''),
                'last_name': profile_info.get('lastName', ''),
                'headline': profile_info.get('headline', ''),
                'email': profile_info.get('emailAddress', ''),
                'location': profile_info.get('locationName', ''),
                'industry': profile_info.get('industryName', ''),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'linkedin',
                'type': 'profile',
                'source': 'linkedin_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing LinkedIn profile: {str(e)}")
    
    def _extract_connections_from_csv(self, connections_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract connections from a LinkedIn Connections.csv file.
        
        Args:
            connections_path: Path to the Connections.csv file
                
        Yields:
            Dictionaries containing normalized connection data
        """
        try:
            with open(connections_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                connections = list(reader)
            
            logger.info(f"Found {len(connections)} connections in LinkedIn export")
            
            for connection in connections:
                try:
                    # Parse connection timestamp
                    timestamp = None
                    timestamp_str = connection.get('Connected On', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized connection data
                    connection_data = {
                        'id': f"linkedin_connection_{connection.get('First Name', '')}_{connection.get('Last Name', '')}",
                        'first_name': connection.get('First Name', ''),
                        'last_name': connection.get('Last Name', ''),
                        'email': connection.get('Email Address', ''),
                        'company': connection.get('Company', ''),
                        'position': connection.get('Position', ''),
                        'connected_on': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'connection',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(connection_data):
                        self.item_count += 1
                        yield connection_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn connection: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting connections from LinkedIn export: {str(e)}")
    
    def _extract_connections_from_json(self, connections_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract connections from a LinkedIn connections.json file.
        
        Args:
            connections_path: Path to the connections.json file
                
        Yields:
            Dictionaries containing normalized connection data
        """
        try:
            with open(connections_path, 'r', encoding='utf-8') as f:
                connections_data = json.load(f)
            
            # Handle different LinkedIn export formats
            connections_list = []
            
            # Format 1: Direct list
            if isinstance(connections_data, list):
                connections_list = connections_data
            
            # Format 2: Nested under 'connections'
            elif 'connections' in connections_data:
                connections_list = connections_data.get('connections', [])
            
            logger.info(f"Found {len(connections_list)} connections in LinkedIn export")
            
            for connection in connections_list:
                try:
                    # Parse connection timestamp
                    timestamp = None
                    timestamp_str = connection.get('connectedAt', '') or connection.get('connectionDate', '')
                    if timestamp_str:
                        try:
                            if isinstance(timestamp_str, int):
                                timestamp = datetime.fromtimestamp(timestamp_str / 1000)  # LinkedIn stores timestamps in milliseconds
                            else:
                                timestamp = parse_datetime(timestamp_str)
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized connection data
                    connection_data = {
                        'id': f"linkedin_connection_{connection.get('firstName', '')}_{connection.get('lastName', '')}",
                        'first_name': connection.get('firstName', ''),
                        'last_name': connection.get('lastName', ''),
                        'email': connection.get('emailAddress', ''),
                        'company': connection.get('companyName', ''),
                        'position': connection.get('position', ''),
                        'connected_on': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'connection',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(connection_data):
                        self.item_count += 1
                        yield connection_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn connection: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting connections from LinkedIn export: {str(e)}")
    
    def _extract_messages_from_csv(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a LinkedIn messages CSV file.
        
        Args:
            messages_path: Path to the messages CSV file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                messages = list(reader)
            
            logger.info(f"Found {len(messages)} messages in LinkedIn export")
            
            # Get conversation name from filename
            conversation_name = os.path.basename(messages_path).replace('.csv', '')
            
            for message in messages:
                try:
                    # Parse message timestamp
                    timestamp = None
                    timestamp_str = message.get('DATE', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Get sender and determine if the message was sent by the user
                    sender = message.get('FROM', '')
                    is_sent = False
                    
                    if self.user_info:
                        user_name = f"{self.user_info.get('First Name', '')} {self.user_info.get('Last Name', '')}"
                        is_sent = sender == user_name
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"linkedin_message_{generate_message_id(message)}",
                        'conversation_name': conversation_name,
                        'content': message.get('CONTENT', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender': sender,
                        'is_sent': is_sent,
                        'platform': 'linkedin',
                        'type': 'message',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn message: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from LinkedIn export: {str(e)}")
    
    def _extract_messages_from_json(self, messages_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from a LinkedIn messages.json file.
        
        Args:
            messages_path: Path to the messages.json file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            # Handle different LinkedIn export formats
            conversations = []
            
            # Format 1: Direct list of conversations
            if isinstance(messages_data, list):
                conversations = messages_data
            
            # Format 2: Nested under 'conversations'
            elif 'conversations' in messages_data:
                conversations = messages_data.get('conversations', [])
            
            logger.info(f"Found {len(conversations)} conversations in LinkedIn export")
            
            # Get user's name from profile
            user_name = ''
            if self.user_info:
                if 'firstName' in self.user_info and 'lastName' in self.user_info:
                    user_name = f"{self.user_info.get('firstName', '')} {self.user_info.get('lastName', '')}"
                elif 'profile' in self.user_info:
                    profile = self.user_info.get('profile', {})
                    user_name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}"
            
            for conversation in conversations:
                try:
                    # Get conversation information
                    conversation_id = conversation.get('conversationId', '')
                    conversation_name = conversation.get('conversationName', '')
                    
                    # Get messages
                    messages = conversation.get('messages', [])
                    
                    logger.info(f"Processing {len(messages)} messages in LinkedIn conversation '{conversation_name}'")
                    
                    for message in messages:
                        try:
                            # Parse message timestamp
                            timestamp = None
                            timestamp_ms = message.get('createdAt', 0)
                            if timestamp_ms:
                                try:
                                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000)  # LinkedIn stores timestamps in milliseconds
                                except (ValueError, TypeError):
                                    timestamp = None
                            
                            # Get sender information
                            sender = message.get('senderName', '')
                            
                            # Determine if the message was sent by the user
                            is_sent = sender == user_name
                            
                            # Get message content
                            content = ''
                            if 'text' in message:
                                content = message.get('text', '')
                            elif 'messageBody' in message:
                                content = message.get('messageBody', '')
                            
                            # Create normalized message data
                            message_data = {
                                'id': f"linkedin_message_{message.get('messageId', '')}",
                                'conversation_id': conversation_id,
                                'conversation_name': conversation_name,
                                'content': content,
                                'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                'sender': sender,
                                'is_sent': is_sent,
                                'platform': 'linkedin',
                                'type': 'message',
                                'source': 'linkedin_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(message_data):
                                self.item_count += 1
                                yield message_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing LinkedIn message: {str(e)}")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn conversation: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting messages from LinkedIn export: {str(e)}")
    
    def _extract_posts_from_csv(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from a LinkedIn Posts.csv file.
        
        Args:
            posts_path: Path to the Posts.csv file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                posts = list(reader)
            
            logger.info(f"Found {len(posts)} posts in LinkedIn export")
            
            for post in posts:
                try:
                    # Parse post timestamp
                    timestamp = None
                    timestamp_str = post.get('Date', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"linkedin_post_{generate_message_id(post)}",
                        'content': post.get('Content', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'visibility': post.get('Visibility', ''),
                        'platform': 'linkedin',
                        'type': 'post',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from LinkedIn export: {str(e)}")
    
    def _extract_posts_from_json(self, posts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract posts from a LinkedIn shares.json file.
        
        Args:
            posts_path: Path to the shares.json file
                
        Yields:
            Dictionaries containing normalized post data
        """
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            # Handle different LinkedIn export formats
            posts_list = []
            
            # Format 1: Direct list
            if isinstance(posts_data, list):
                posts_list = posts_data
            
            # Format 2: Nested under 'shares'
            elif 'shares' in posts_data:
                posts_list = posts_data.get('shares', [])
            
            logger.info(f"Found {len(posts_list)} posts in LinkedIn export")
            
            for post in posts_list:
                try:
                    # Parse post timestamp
                    timestamp = None
                    timestamp_ms = post.get('createdAt', 0)
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)  # LinkedIn stores timestamps in milliseconds
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Get post content
                    content = ''
                    if 'text' in post:
                        content = post.get('text', '')
                    elif 'commentary' in post:
                        content = post.get('commentary', '')
                    
                    # Create normalized post data
                    post_data = {
                        'id': f"linkedin_post_{post.get('shareId', '')}",
                        'content': content,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'visibility': post.get('visibility', ''),
                        'platform': 'linkedin',
                        'type': 'post',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(post_data):
                        self.item_count += 1
                        yield post_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn post: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting posts from LinkedIn export: {str(e)}")
    
    def _extract_reactions_from_csv(self, reactions_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract reactions from a LinkedIn Reactions.csv file.
        
        Args:
            reactions_path: Path to the Reactions.csv file
                
        Yields:
            Dictionaries containing normalized reaction data
        """
        try:
            with open(reactions_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                reactions = list(reader)
            
            logger.info(f"Found {len(reactions)} reactions in LinkedIn export")
            
            for reaction in reactions:
                try:
                    # Parse reaction timestamp
                    timestamp = None
                    timestamp_str = reaction.get('Date', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized reaction data
                    reaction_data = {
                        'id': f"linkedin_reaction_{generate_message_id(reaction)}",
                        'content': reaction.get('Content', ''),
                        'reaction_type': reaction.get('Reaction Type', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'reaction',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(reaction_data):
                        self.item_count += 1
                        yield reaction_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn reaction: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting reactions from LinkedIn export: {str(e)}")
    
    def _extract_reactions_from_json(self, reactions_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract reactions from a LinkedIn reactions.json file.
        
        Args:
            reactions_path: Path to the reactions.json file
                
        Yields:
            Dictionaries containing normalized reaction data
        """
        try:
            with open(reactions_path, 'r', encoding='utf-8') as f:
                reactions_data = json.load(f)
            
            # Handle different LinkedIn export formats
            reactions_list = []
            
            # Format 1: Direct list
            if isinstance(reactions_data, list):
                reactions_list = reactions_data
            
            # Format 2: Nested under 'reactions'
            elif 'reactions' in reactions_data:
                reactions_list = reactions_data.get('reactions', [])
            
            logger.info(f"Found {len(reactions_list)} reactions in LinkedIn export")
            
            for reaction in reactions_list:
                try:
                    # Parse reaction timestamp
                    timestamp = None
                    timestamp_ms = reaction.get('createdAt', 0)
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)  # LinkedIn stores timestamps in milliseconds
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized reaction data
                    reaction_data = {
                        'id': f"linkedin_reaction_{reaction.get('reactionId', '')}",
                        'content': reaction.get('content', ''),
                        'reaction_type': reaction.get('reactionType', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'reaction',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(reaction_data):
                        self.item_count += 1
                        yield reaction_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn reaction: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting reactions from LinkedIn export: {str(e)}")
    
    def _extract_comments_from_csv(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from a LinkedIn Comments.csv file.
        
        Args:
            comments_path: Path to the Comments.csv file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                comments = list(reader)
            
            logger.info(f"Found {len(comments)} comments in LinkedIn export")
            
            for comment in comments:
                try:
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_str = comment.get('Date', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"linkedin_comment_{generate_message_id(comment)}",
                        'content': comment.get('Comment', ''),
                        'post_content': comment.get('Post Content', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'comment',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from LinkedIn export: {str(e)}")
    
    def _extract_comments_from_json(self, comments_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract comments from a LinkedIn comments.json file.
        
        Args:
            comments_path: Path to the comments.json file
                
        Yields:
            Dictionaries containing normalized comment data
        """
        try:
            with open(comments_path, 'r', encoding='utf-8') as f:
                comments_data = json.load(f)
            
            # Handle different LinkedIn export formats
            comments_list = []
            
            # Format 1: Direct list
            if isinstance(comments_data, list):
                comments_list = comments_data
            
            # Format 2: Nested under 'comments'
            elif 'comments' in comments_data:
                comments_list = comments_data.get('comments', [])
            
            logger.info(f"Found {len(comments_list)} comments in LinkedIn export")
            
            for comment in comments_list:
                try:
                    # Parse comment timestamp
                    timestamp = None
                    timestamp_ms = comment.get('createdAt', 0)
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)  # LinkedIn stores timestamps in milliseconds
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized comment data
                    comment_data = {
                        'id': f"linkedin_comment_{comment.get('commentId', '')}",
                        'content': comment.get('text', '') or comment.get('commentText', ''),
                        'post_id': comment.get('postId', ''),
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'comment',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(comment_data):
                        self.item_count += 1
                        yield comment_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn comment: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting comments from LinkedIn export: {str(e)}")
    
    def _extract_jobs_from_csv(self, jobs_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract job applications from a LinkedIn Job Applications.csv file.
        
        Args:
            jobs_path: Path to the Job Applications.csv file
                
        Yields:
            Dictionaries containing normalized job application data
        """
        try:
            with open(jobs_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                jobs = list(reader)
            
            logger.info(f"Found {len(jobs)} job applications in LinkedIn export")
            
            for job in jobs:
                try:
                    # Parse job application timestamp
                    timestamp = None
                    timestamp_str = job.get('Application Date', '')
                    if timestamp_str:
                        timestamp = parse_datetime(timestamp_str)
                    
                    # Create normalized job application data
                    job_data = {
                        'id': f"linkedin_job_{generate_message_id(job)}",
                        'company_name': job.get('Company Name', ''),
                        'job_title': job.get('Job Title', ''),
                        'application_date': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'job_application',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(job_data):
                        self.item_count += 1
                        yield job_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn job application: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting job applications from LinkedIn export: {str(e)}")
    
    def _extract_jobs_from_json(self, jobs_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract job applications from a LinkedIn job_applications.json file.
        
        Args:
            jobs_path: Path to the job_applications.json file
                
        Yields:
            Dictionaries containing normalized job application data
        """
        try:
            with open(jobs_path, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
            
            # Handle different LinkedIn export formats
            jobs_list = []
            
            # Format 1: Direct list
            if isinstance(jobs_data, list):
                jobs_list = jobs_data
            
            # Format 2: Nested under 'jobApplications'
            elif 'jobApplications' in jobs_data:
                jobs_list = jobs_data.get('jobApplications', [])
            
            logger.info(f"Found {len(jobs_list)} job applications in LinkedIn export")
            
            for job in jobs_list:
                try:
                    # Parse job application timestamp
                    timestamp = None
                    timestamp_ms = job.get('appliedAt', 0)
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)  # LinkedIn stores timestamps in milliseconds
                        except (ValueError, TypeError):
                            timestamp = None
                    
                    # Create normalized job application data
                    job_data = {
                        'id': f"linkedin_job_{job.get('applicationId', '')}",
                        'company_name': job.get('companyName', ''),
                        'job_title': job.get('jobTitle', ''),
                        'application_date': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'linkedin',
                        'type': 'job_application',
                        'source': 'linkedin_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(job_data):
                        self.item_count += 1
                        yield job_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing LinkedIn job application: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting job applications from LinkedIn export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for LinkedIn data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item