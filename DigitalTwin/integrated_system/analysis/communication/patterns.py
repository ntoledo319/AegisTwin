"""
Communication pattern analysis module.

This module provides functionality for analyzing patterns in communication data,
including frequency, timing, and style patterns.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """Analyzer for communication patterns."""
    
    def __init__(self):
        """Initialize the pattern analyzer."""
        self.patterns = {}
        
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze communication patterns in messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of pattern analysis results
        """
        logger.info(f"Analyzing patterns in {len(messages)} messages")
        
        if not messages:
            return {"patterns": {}, "error": "No messages to analyze"}
        
        # Convert to DataFrame for easier analysis
        try:
            df = pd.DataFrame(messages)
            
            # Ensure timestamp column exists
            if 'timestamp' not in df.columns:
                return {"patterns": {}, "error": "Messages missing timestamp field"}
            
            # Convert timestamps to datetime objects if they're not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Analyze various patterns
            frequency_patterns = self._analyze_frequency(df)
            timing_patterns = self._analyze_timing(df)
            style_patterns = self._analyze_style(df)
            response_patterns = self._analyze_response_patterns(df)
            
            # Combine all patterns
            all_patterns = {
                "frequency": frequency_patterns,
                "timing": timing_patterns,
                "style": style_patterns,
                "response": response_patterns
            }
            
            # Store patterns
            self.patterns = all_patterns
            
            return {"patterns": all_patterns}
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return {"patterns": {}, "error": str(e)}
    
    def _analyze_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze frequency patterns in communication.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of frequency patterns
        """
        # Calculate messages per day
        df['date'] = df['timestamp'].dt.date
        messages_per_day = df.groupby('date').size()
        
        # Calculate average, min, max messages per day
        avg_messages_per_day = messages_per_day.mean()
        max_messages_per_day = messages_per_day.max()
        min_messages_per_day = messages_per_day.min()
        
        # Calculate messages by day of week
        df['day_of_week'] = df['timestamp'].dt.day_name()
        messages_by_day = df.groupby('day_of_week').size().to_dict()
        
        # Calculate messages by hour of day
        df['hour'] = df['timestamp'].dt.hour
        messages_by_hour = df.groupby('hour').size().to_dict()
        
        # Calculate active days percentage
        total_days = (df['date'].max() - df['date'].min()).days + 1
        active_days = len(messages_per_day)
        active_days_percentage = (active_days / total_days) * 100 if total_days > 0 else 0
        
        return {
            "avg_messages_per_day": float(avg_messages_per_day),
            "max_messages_per_day": int(max_messages_per_day),
            "min_messages_per_day": int(min_messages_per_day),
            "messages_by_day_of_week": messages_by_day,
            "messages_by_hour": messages_by_hour,
            "active_days_percentage": float(active_days_percentage)
        }
    
    def _analyze_timing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze timing patterns in communication.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of timing patterns
        """
        # Calculate response times if conversation_id and sender fields exist
        response_times = []
        
        if 'conversation_id' in df.columns and 'sender' in df.columns:
            # Sort by conversation and timestamp
            df = df.sort_values(['conversation_id', 'timestamp'])
            
            # Group by conversation
            for conversation_id, group in df.groupby('conversation_id'):
                prev_sender = None
                prev_time = None
                
                for _, row in group.iterrows():
                    current_sender = row['sender']
                    current_time = row['timestamp']
                    
                    # If sender changed, calculate response time
                    if prev_sender is not None and current_sender != prev_sender:
                        response_time = (current_time - prev_time).total_seconds()
                        response_times.append(response_time)
                    
                    prev_sender = current_sender
                    prev_time = current_time
        
        # Calculate response time statistics
        if response_times:
            avg_response_time = np.mean(response_times)
            median_response_time = np.median(response_times)
            min_response_time = np.min(response_times)
            max_response_time = np.max(response_times)
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = None
        
        # Calculate time between messages
        df = df.sort_values('timestamp')
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
        
        # Remove first row which has NaN time diff
        time_diffs = df['time_diff'].dropna().tolist()
        
        if time_diffs:
            avg_time_between_messages = np.mean(time_diffs)
            median_time_between_messages = np.median(time_diffs)
        else:
            avg_time_between_messages = median_time_between_messages = None
        
        return {
            "avg_response_time_seconds": float(avg_response_time) if avg_response_time is not None else None,
            "median_response_time_seconds": float(median_response_time) if median_response_time is not None else None,
            "min_response_time_seconds": float(min_response_time) if min_response_time is not None else None,
            "max_response_time_seconds": float(max_response_time) if max_response_time is not None else None,
            "avg_time_between_messages_seconds": float(avg_time_between_messages) if avg_time_between_messages is not None else None,
            "median_time_between_messages_seconds": float(median_time_between_messages) if median_time_between_messages is not None else None
        }
    
    def _analyze_style(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze communication style patterns.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of style patterns
        """
        style_patterns = {}
        
        # Check if content field exists
        if 'content' not in df.columns:
            return {"error": "Messages missing content field"}
        
        # Calculate average message length
        df['message_length'] = df['content'].apply(lambda x: len(str(x)) if x else 0)
        avg_message_length = df['message_length'].mean()
        max_message_length = df['message_length'].max()
        min_message_length = df['message_length'].min()
        
        # Calculate emoji usage if possible
        emoji_count = 0
        try:
            import emoji
            df['emoji_count'] = df['content'].apply(lambda x: sum(c in emoji.EMOJI_DATA for c in str(x)) if x else 0)
            emoji_count = df['emoji_count'].sum()
            messages_with_emoji = (df['emoji_count'] > 0).sum()
            emoji_percentage = (messages_with_emoji / len(df)) * 100 if len(df) > 0 else 0
        except ImportError:
            emoji_percentage = None
        
        # Calculate question frequency
        df['has_question'] = df['content'].apply(lambda x: '?' in str(x) if x else False)
        question_count = df['has_question'].sum()
        question_percentage = (question_count / len(df)) * 100 if len(df) > 0 else 0
        
        # Calculate exclamation frequency
        df['has_exclamation'] = df['content'].apply(lambda x: '!' in str(x) if x else False)
        exclamation_count = df['has_exclamation'].sum()
        exclamation_percentage = (exclamation_count / len(df)) * 100 if len(df) > 0 else 0
        
        return {
            "avg_message_length": float(avg_message_length),
            "max_message_length": int(max_message_length),
            "min_message_length": int(min_message_length),
            "emoji_percentage": float(emoji_percentage) if emoji_percentage is not None else None,
            "question_percentage": float(question_percentage),
            "exclamation_percentage": float(exclamation_percentage)
        }
    
    def _analyze_response_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze response patterns in communication.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of response patterns
        """
        # Check if necessary fields exist
        if not all(field in df.columns for field in ['conversation_id', 'sender', 'timestamp']):
            return {"error": "Messages missing required fields for response pattern analysis"}
        
        # Sort by conversation and timestamp
        df = df.sort_values(['conversation_id', 'timestamp'])
        
        # Initialize counters
        conversation_starters = {}
        conversation_enders = {}
        response_rates = {}
        
        # Analyze each conversation
        for conversation_id, group in df.groupby('conversation_id'):
            # Get first and last sender
            first_sender = group.iloc[0]['sender']
            last_sender = group.iloc[-1]['sender']
            
            # Update conversation starters
            if first_sender in conversation_starters:
                conversation_starters[first_sender] += 1
            else:
                conversation_starters[first_sender] = 1
            
            # Update conversation enders
            if last_sender in conversation_enders:
                conversation_enders[last_sender] += 1
            else:
                conversation_enders[last_sender] = 1
            
            # Calculate response rates
            senders = group['sender'].unique()
            for sender in senders:
                # Get messages by this sender
                sender_messages = group[group['sender'] == sender]
                
                # Get messages by other senders
                other_messages = group[group['sender'] != sender]
                
                # Count how many of this sender's messages got responses
                responses_received = 0
                
                for _, msg in sender_messages.iterrows():
                    # Find messages that came after this one
                    later_messages = other_messages[other_messages['timestamp'] > msg['timestamp']]
                    
                    # If there's at least one later message, count it as a response
                    if len(later_messages) > 0:
                        responses_received += 1
                
                # Calculate response rate
                response_rate = responses_received / len(sender_messages) if len(sender_messages) > 0 else 0
                
                # Update response rates
                if sender in response_rates:
                    response_rates[sender].append(response_rate)
                else:
                    response_rates[sender] = [response_rate]
        
        # Calculate average response rates
        avg_response_rates = {sender: np.mean(rates) for sender, rates in response_rates.items()}
        
        return {
            "conversation_starters": conversation_starters,
            "conversation_enders": conversation_enders,
            "avg_response_rates": avg_response_rates
        }