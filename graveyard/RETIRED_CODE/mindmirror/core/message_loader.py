"""Message loader for MindMirror."""

import json
import os
from typing import Dict, Any, List, Optional, Iterator, Tuple
from datetime import datetime
import re
from pathlib import Path
from tqdm import tqdm

from .config import config_manager
from .utils import parse_date, ensure_dir, save_pickle, load_pickle

class MessageLoader:
    """Loads and processes message data."""
    
    def __init__(self, messages_file: Optional[str] = None, cache_dir: Optional[str] = None):
        """Initialize the message loader.
        
        Args:
            messages_file: Path to the messages JSON file.
            cache_dir: Directory to store cached data.
        """
        self.messages_file = messages_file or config_manager.get_value('mindmirror', 'data.messages_file')
        self.cache_dir = cache_dir or config_manager.get_value('mindmirror', 'data.cache_dir', 'data/cache')
        ensure_dir(self.cache_dir)
        
        self.messages = None
        self.metadata = None
        self.conversations = None
        self.participants = None
        
    def load_messages(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load messages from the JSON file or cache.
        
        Args:
            force_reload: Whether to force reload from the JSON file.
            
        Returns:
            Dictionary containing messages and metadata.
        """
        cache_file = os.path.join(self.cache_dir, 'messages.pkl')
        
        # Try to load from cache first
        if not force_reload and os.path.exists(cache_file):
            try:
                data = load_pickle(cache_file)
                self.messages = data.get('messages', [])
                self.metadata = data.get('metadata', {})
                self.conversations = data.get('conversations', {})
                self.participants = data.get('participants', [])
                
                print(f"Loaded {len(self.messages)} messages from cache")
                return {
                    'messages': self.messages,
                    'metadata': self.metadata,
                    'conversations': self.conversations,
                    'participants': self.participants
                }
            except Exception as e:
                print(f"Error loading from cache: {e}")
        
        # Load from JSON file
        print(f"Loading messages from {self.messages_file}...")
        try:
            with open(self.messages_file, 'r') as f:
                data = json.load(f)
                
            self.messages = data.get('messages', [])
            
            # Extract metadata
            self.metadata = {
                'export_info': data.get('export_info', {}),
                'statistics': data.get('statistics', {})
            }
            
            # Process conversations
            self.conversations = self._process_conversations()
            
            # Extract participants
            self.participants = data.get('statistics', {}).get('participants', [])
            
            # Cache the processed data
            save_pickle({
                'messages': self.messages,
                'metadata': self.metadata,
                'conversations': self.conversations,
                'participants': self.participants
            }, cache_file)
            
            print(f"Loaded {len(self.messages)} messages")
            return {
                'messages': self.messages,
                'metadata': self.metadata,
                'conversations': self.conversations,
                'participants': self.participants
            }
        except Exception as e:
            print(f"Error loading messages: {e}")
            return {
                'messages': [],
                'metadata': {},
                'conversations': {},
                'participants': []
            }
    
    def _process_conversations(self) -> Dict[str, List[int]]:
        """Process conversations from messages.
        
        Returns:
            Dictionary mapping conversation names to lists of message indices.
        """
        conversations = {}
        
        for i, message in enumerate(self.messages):
            chat_session = message.get('chat_session', '')
            if chat_session:
                if chat_session not in conversations:
                    conversations[chat_session] = []
                conversations[chat_session].append(i)
        
        return conversations
    
    def get_conversation_messages(self, conversation_name: str) -> List[Dict[str, Any]]:
        """Get messages for a specific conversation.
        
        Args:
            conversation_name: Name of the conversation.
            
        Returns:
            List of messages in the conversation.
        """
        if not self.messages:
            self.load_messages()
            
        if conversation_name not in self.conversations:
            return []
            
        return [self.messages[i] for i in self.conversations[conversation_name]]
    
    def get_messages_by_date_range(self, start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get messages within a date range.
        
        Args:
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            
        Returns:
            List of messages within the date range.
        """
        if not self.messages:
            self.load_messages()
            
        filtered_messages = []
        
        for message in self.messages:
            message_date_str = message.get('message_date', '')
            if not message_date_str:
                continue
                
            message_date = parse_date(message_date_str)
            if not message_date:
                continue
                
            if start_date and message_date < start_date:
                continue
                
            if end_date and message_date > end_date:
                continue
                
            filtered_messages.append(message)
            
        return filtered_messages
    
    def get_messages_by_sender(self, sender_name: str) -> List[Dict[str, Any]]:
        """Get messages from a specific sender.
        
        Args:
            sender_name: Name of the sender.
            
        Returns:
            List of messages from the sender.
        """
        if not self.messages:
            self.load_messages()
            
        return [m for m in self.messages if m.get('sender_name', '') == sender_name]
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get messages of a specific type.
        
        Args:
            message_type: Type of messages to get (e.g., 'Incoming', 'Outgoing').
            
        Returns:
            List of messages of the specified type.
        """
        if not self.messages:
            self.load_messages()
            
        return [m for m in self.messages if m.get('type', '') == message_type]
    
    def search_messages(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search messages for a query string.
        
        Args:
            query: Query string to search for.
            case_sensitive: Whether to perform case-sensitive search.
            
        Returns:
            List of messages matching the query.
        """
        if not self.messages:
            self.load_messages()
            
        if not case_sensitive:
            query = query.lower()
            return [m for m in self.messages if query in m.get('text', '').lower()]
        else:
            return [m for m in self.messages if query in m.get('text', '')]
    
    def get_conversation_statistics(self, conversation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific conversation.
        
        Args:
            conversation_name: Name of the conversation.
            
        Returns:
            Dictionary of conversation statistics.
        """
        if not self.messages:
            self.load_messages()
            
        if conversation_name not in self.conversations:
            return {}
            
        messages = self.get_conversation_messages(conversation_name)
        
        # Count messages by type
        message_counts = {
            'total': len(messages),
            'incoming': len([m for m in messages if m.get('type', '') == 'Incoming']),
            'outgoing': len([m for m in messages if m.get('type', '') == 'Outgoing'])
        }
        
        # Get date range
        dates = [parse_date(m.get('message_date', '')) for m in messages]
        dates = [d for d in dates if d]
        
        date_range = {}
        if dates:
            date_range = {
                'start': min(dates),
                'end': max(dates)
            }
        
        # Count messages by sender
        sender_counts = {}
        for message in messages:
            sender = message.get('sender_name', '')
            if sender:
                sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        return {
            'message_counts': message_counts,
            'date_range': date_range,
            'sender_counts': sender_counts
        }
    
    def get_all_conversation_names(self) -> List[str]:
        """Get names of all conversations.
        
        Returns:
            List of conversation names.
        """
        if not self.messages:
            self.load_messages()
            
        return list(self.conversations.keys())
    
    def get_top_conversations(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get top conversations by message count.
        
        Args:
            top_n: Number of top conversations to return.
            
        Returns:
            List of (conversation_name, message_count) tuples.
        """
        if not self.messages:
            self.load_messages()
            
        conversation_counts = [(name, len(indices)) for name, indices in self.conversations.items()]
        return sorted(conversation_counts, key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_message_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a message by its index.
        
        Args:
            index: Index of the message.
            
        Returns:
            Message dictionary or None if index is out of range.
        """
        if not self.messages:
            self.load_messages()
            
        if 0 <= index < len(self.messages):
            return self.messages[index]
        return None
    
    def get_message_context(self, index: int, context_size: int = 5) -> List[Dict[str, Any]]:
        """Get context messages around a specific message.
        
        Args:
            index: Index of the target message.
            context_size: Number of messages to include before and after.
            
        Returns:
            List of context messages.
        """
        if not self.messages:
            self.load_messages()
            
        start_idx = max(0, index - context_size)
        end_idx = min(len(self.messages), index + context_size + 1)
        
        return self.messages[start_idx:end_idx]
    
    def get_all_participants(self) -> List[str]:
        """Get all participants from the messages.
        
        Returns:
            List of participant names.
        """
        if not self.participants:
            self.load_messages()
            
        return self.participants