"""
Memory analysis module for cognitive analysis.

This module provides functionality for analyzing memory patterns and processes
based on communication data and behavior patterns.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import re

logger = logging.getLogger(__name__)

class MemoryAnalyzer:
    """Analyzer for memory patterns and processes."""
    
    def __init__(self):
        """Initialize the memory analyzer."""
        self.nlp_available = False
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for memory analysis")
        
        # Initialize memory patterns dictionary
        self.memory_patterns = {}
    
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze memory patterns based on messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of memory analysis results
        """
        logger.info(f"Analyzing memory patterns from {len(messages)} messages")
        
        if not messages:
            return {"error": "No messages to analyze"}
        
        try:
            # Sort messages by timestamp if available
            if 'timestamp' in messages[0]:
                messages = sorted(messages, key=lambda x: x.get('timestamp', 0))
            
            # Extract text content and metadata from messages
            texts = []
            timestamps = []
            senders = []
            
            for message in messages:
                if 'content' in message and message['content']:
                    texts.append(str(message['content']))
                elif 'text' in message and message['text']:
                    texts.append(str(message['text']))
                else:
                    texts.append("")
                
                if 'timestamp' in message:
                    timestamps.append(message['timestamp'])
                else:
                    timestamps.append(None)
                
                if 'sender' in message:
                    senders.append(message['sender'])
                else:
                    senders.append(None)
            
            # Create a DataFrame for easier analysis
            df = pd.DataFrame({
                'text': texts,
                'timestamp': timestamps,
                'sender': senders
            })
            
            # Analyze recall patterns
            recall_patterns = await self._analyze_recall_patterns(df)
            
            # Analyze reference patterns
            reference_patterns = await self._analyze_reference_patterns(df)
            
            # Analyze memory consistency
            memory_consistency = await self._analyze_memory_consistency(df)
            
            # Analyze memory decay
            memory_decay = await self._analyze_memory_decay(df)
            
            # Store memory patterns
            self.memory_patterns = {
                "recall_patterns": recall_patterns,
                "reference_patterns": reference_patterns,
                "memory_consistency": memory_consistency,
                "memory_decay": memory_decay
            }
            
            return {
                "recall_patterns": recall_patterns,
                "reference_patterns": reference_patterns,
                "memory_consistency": memory_consistency,
                "memory_decay": memory_decay
            }
                
        except Exception as e:
            logger.error(f"Error analyzing memory patterns: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_recall_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze recall patterns from messages.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of recall pattern analysis results
        """
        # Look for explicit recall indicators
        recall_indicators = [
            'remember', 'recall', 'recollect', 'reminisce', 'remind', 'memory',
            'memorable', 'unforgettable', 'mind', 'think of', 'bring to mind',
            'come to mind', 'spring to mind', 'pop into head', 'forget', 'forgot',
            'forgotten', 'slip my mind', 'can\'t remember', 'don\'t remember',
            'didn\'t remember', 'escape me', 'blank', 'lost track'
        ]
        
        # Count recall indicators in each message
        df['recall_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in recall_indicators)
        )
        
        # Calculate total recall indicators
        total_recall_indicators = df['recall_count'].sum()
        
        # Calculate recall frequency (per message)
        recall_frequency = total_recall_indicators / len(df) if len(df) > 0 else 0
        
        # Identify messages with recall indicators
        recall_messages = df[df['recall_count'] > 0]
        
        # Analyze recall types
        positive_recall_indicators = [
            'remember', 'recall', 'recollect', 'reminisce', 'remind', 'memory',
            'memorable', 'unforgettable', 'mind', 'think of', 'bring to mind',
            'come to mind', 'spring to mind', 'pop into head'
        ]
        
        negative_recall_indicators = [
            'forget', 'forgot', 'forgotten', 'slip my mind', 'can\'t remember',
            'don\'t remember', 'didn\'t remember', 'escape me', 'blank', 'lost track'
        ]
        
        # Count positive and negative recall indicators
        positive_recall_count = sum(
            sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text.lower())) for word in positive_recall_indicators)
            for text in df['text']
        )
        
        negative_recall_count = sum(
            sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text.lower())) for word in negative_recall_indicators)
            for text in df['text']
        )
        
        # Calculate recall ratio (positive vs negative)
        total_specific_recalls = positive_recall_count + negative_recall_count
        positive_recall_ratio = positive_recall_count / total_specific_recalls if total_specific_recalls > 0 else 0.5
        
        # Determine recall tendency
        recall_tendency = None
        if positive_recall_ratio > 0.7:
            recall_tendency = 'Strong Recall'
        elif positive_recall_ratio > 0.5:
            recall_tendency = 'Moderate Recall'
        elif positive_recall_ratio > 0.3:
            recall_tendency = 'Moderate Forgetfulness'
        else:
            recall_tendency = 'Significant Forgetfulness'
        
        return {
            'recall_frequency': float(recall_frequency),
            'total_recall_indicators': int(total_recall_indicators),
            'positive_recall_count': int(positive_recall_count),
            'negative_recall_count': int(negative_recall_count),
            'positive_recall_ratio': float(positive_recall_ratio),
            'recall_tendency': recall_tendency
        }
    
    async def _analyze_reference_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze reference patterns from messages.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of reference pattern analysis results
        """
        # Look for time reference indicators
        past_indicators = [
            'yesterday', 'last week', 'last month', 'last year', 'previously', 'before',
            'earlier', 'ago', 'in the past', 'used to', 'once', 'formerly', 'back then',
            'back in', 'when I was', 'had been', 'had', 'did', 'was', 'were'
        ]
        
        present_indicators = [
            'today', 'now', 'currently', 'presently', 'at this moment', 'at present',
            'right now', 'at the moment', 'am', 'is', 'are', 'have', 'has', 'do', 'does'
        ]
        
        future_indicators = [
            'tomorrow', 'next week', 'next month', 'next year', 'soon', 'in the future',
            'upcoming', 'coming', 'will', 'going to', 'plan to', 'intend to', 'expect to',
            'hope to', 'shall', 'would', 'could', 'might', 'may'
        ]
        
        # Count time reference indicators in each message
        df['past_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in past_indicators)
        )
        
        df['present_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in present_indicators)
        )
        
        df['future_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in future_indicators)
        )
        
        # Calculate total time reference indicators
        total_past = df['past_count'].sum()
        total_present = df['present_count'].sum()
        total_future = df['future_count'].sum()
        total_time_references = total_past + total_present + total_future
        
        # Calculate time reference ratios
        past_ratio = total_past / total_time_references if total_time_references > 0 else 0
        present_ratio = total_present / total_time_references if total_time_references > 0 else 0
        future_ratio = total_future / total_time_references if total_time_references > 0 else 0
        
        # Determine time orientation
        time_orientation = None
        max_ratio = max(past_ratio, present_ratio, future_ratio)
        if max_ratio == past_ratio:
            time_orientation = 'Past-Oriented'
        elif max_ratio == present_ratio:
            time_orientation = 'Present-Oriented'
        else:
            time_orientation = 'Future-Oriented'
        
        # Look for personal reference indicators
        first_person_indicators = [
            'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'
        ]
        
        second_person_indicators = [
            'you', 'your', 'yours', 'yourself', 'yourselves'
        ]
        
        third_person_indicators = [
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'
        ]
        
        # Count personal reference indicators in each message
        df['first_person_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in first_person_indicators)
        )
        
        df['second_person_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in second_person_indicators)
        )
        
        df['third_person_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in third_person_indicators)
        )
        
        # Calculate total personal reference indicators
        total_first_person = df['first_person_count'].sum()
        total_second_person = df['second_person_count'].sum()
        total_third_person = df['third_person_count'].sum()
        total_personal_references = total_first_person + total_second_person + total_third_person
        
        # Calculate personal reference ratios
        first_person_ratio = total_first_person / total_personal_references if total_personal_references > 0 else 0
        second_person_ratio = total_second_person / total_personal_references if total_personal_references > 0 else 0
        third_person_ratio = total_third_person / total_personal_references if total_personal_references > 0 else 0
        
        # Determine personal reference orientation
        personal_reference_orientation = None
        max_personal_ratio = max(first_person_ratio, second_person_ratio, third_person_ratio)
        if max_personal_ratio == first_person_ratio:
            personal_reference_orientation = 'Self-Focused'
        elif max_personal_ratio == second_person_ratio:
            personal_reference_orientation = 'Other-Focused'
        else:
            personal_reference_orientation = 'External-Focused'
        
        return {
            'time_references': {
                'past': int(total_past),
                'present': int(total_present),
                'future': int(total_future),
                'past_ratio': float(past_ratio),
                'present_ratio': float(present_ratio),
                'future_ratio': float(future_ratio),
                'time_orientation': time_orientation
            },
            'personal_references': {
                'first_person': int(total_first_person),
                'second_person': int(total_second_person),
                'third_person': int(total_third_person),
                'first_person_ratio': float(first_person_ratio),
                'second_person_ratio': float(second_person_ratio),
                'third_person_ratio': float(third_person_ratio),
                'personal_reference_orientation': personal_reference_orientation
            }
        }
    
    async def _analyze_memory_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze memory consistency from messages.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of memory consistency analysis results
        """
        # Look for contradiction indicators
        contradiction_indicators = [
            'actually', 'in fact', 'contrary', 'opposite', 'instead', 'rather',
            'but', 'however', 'nevertheless', 'nonetheless', 'though', 'although',
            'even though', 'despite', 'in spite of', 'regardless', 'notwithstanding',
            'on the other hand', 'conversely', 'on the contrary', 'in contrast'
        ]
        
        # Count contradiction indicators in each message
        df['contradiction_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in contradiction_indicators)
        )
        
        # Calculate total contradiction indicators
        total_contradiction_indicators = df['contradiction_count'].sum()
        
        # Calculate contradiction frequency (per message)
        contradiction_frequency = total_contradiction_indicators / len(df) if len(df) > 0 else 0
        
        # Look for correction indicators
        correction_indicators = [
            'correction', 'correct', 'incorrectly', 'mistakenly', 'erroneously',
            'wrongly', 'inaccurately', 'meant to say', 'should have said',
            'misspoke', 'misstated', 'misremembered', 'confused', 'mixed up',
            'error', 'mistake', 'wrong', 'incorrect', 'inaccurate', 'not right'
        ]
        
        # Count correction indicators in each message
        df['correction_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in correction_indicators)
        )
        
        # Calculate total correction indicators
        total_correction_indicators = df['correction_count'].sum()
        
        # Calculate correction frequency (per message)
        correction_frequency = total_correction_indicators / len(df) if len(df) > 0 else 0
        
        # Look for uncertainty indicators
        uncertainty_indicators = [
            'maybe', 'perhaps', 'possibly', 'probably', 'likely', 'unlikely',
            'might', 'may', 'could', 'not sure', 'uncertain', 'unsure', 'doubt',
            'questionable', 'ambiguous', 'unclear', 'vague', 'confused', 'puzzled',
            'perplexed', 'bewildered', 'think', 'guess', 'suppose', 'assume', 'presume'
        ]
        
        # Count uncertainty indicators in each message
        df['uncertainty_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in uncertainty_indicators)
        )
        
        # Calculate total uncertainty indicators
        total_uncertainty_indicators = df['uncertainty_count'].sum()
        
        # Calculate uncertainty frequency (per message)
        uncertainty_frequency = total_uncertainty_indicators / len(df) if len(df) > 0 else 0
        
        # Calculate consistency score
        # Lower values of contradiction, correction, and uncertainty indicate higher consistency
        consistency_factors = [
            1 - min(1, contradiction_frequency * 5),  # Scale to 0-1 range
            1 - min(1, correction_frequency * 10),    # Scale to 0-1 range
            1 - min(1, uncertainty_frequency * 3)     # Scale to 0-1 range
        ]
        
        consistency_score = sum(consistency_factors) / len(consistency_factors)
        
        # Determine consistency level
        consistency_level = None
        if consistency_score > 0.8:
            consistency_level = 'High'
        elif consistency_score > 0.6:
            consistency_level = 'Moderate'
        else:
            consistency_level = 'Low'
        
        return {
            'contradiction_frequency': float(contradiction_frequency),
            'correction_frequency': float(correction_frequency),
            'uncertainty_frequency': float(uncertainty_frequency),
            'consistency_score': float(consistency_score),
            'consistency_level': consistency_level
        }
    
    async def _analyze_memory_decay(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze memory decay from messages.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of memory decay analysis results
        """
        # Check if timestamps are available
        if 'timestamp' not in df.columns or df['timestamp'].isna().all():
            return {"error": "No timestamp data available for memory decay analysis"}
        
        # Convert timestamps to datetime if they're not already
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Look for specific date/time references
        date_references = []
        
        # Regular expressions for date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{1,2}(st|nd|rd|th)?\s+(of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\b',  # 1st of January
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(st|nd|rd|th)?\b',  # January 1st
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # Day of week
            r'\b(yesterday|today|tomorrow)\b'  # Relative day
        ]
        
        # Find date references in each message
        for i, row in df.iterrows():
            text = row['text'].lower()
            timestamp = row['timestamp']
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    date_references.append({
                        'message_index': i,
                        'timestamp': timestamp,
                        'reference': matches[0] if isinstance(matches[0], str) else matches[0][0],
                        'pattern': pattern
                    })
        
        # Calculate time intervals between messages
        if len(df) > 1:
            df['time_diff'] = df['timestamp'].diff()
            avg_time_between_messages = df['time_diff'].mean().total_seconds()
        else:
            avg_time_between_messages = None
        
        # Look for references to previous messages
        reference_indicators = [
            'as I said', 'as mentioned', 'as stated', 'as noted', 'as discussed',
            'as we talked about', 'as we discussed', 'earlier I said', 'previously I said',
            'I told you', 'I mentioned', 'I said', 'I noted', 'I stated', 'I pointed out',
            'you said', 'you mentioned', 'you noted', 'you stated', 'you pointed out'
        ]
        
        # Count reference indicators in each message
        df['reference_count'] = df['text'].apply(
            lambda x: sum(len(re.findall(r'\b' + re.escape(word) + r'\b', x.lower())) for word in reference_indicators)
        )
        
        # Calculate total reference indicators
        total_reference_indicators = df['reference_count'].sum()
        
        # Calculate reference frequency (per message)
        reference_frequency = total_reference_indicators / len(df) if len(df) > 0 else 0
        
        # Calculate memory decay indicators
        
        # 1. Look for increasing uncertainty over time
        if len(df) > 10:  # Need enough messages for meaningful analysis
            # Split into quarters
            quarter_size = len(df) // 4
            quarters = [
                df.iloc[:quarter_size],
                df.iloc[quarter_size:2*quarter_size],
                df.iloc[2*quarter_size:3*quarter_size],
                df.iloc[3*quarter_size:]
            ]
            
            # Calculate uncertainty frequency for each quarter
            uncertainty_by_quarter = [
                quarter['uncertainty_count'].sum() / len(quarter) if len(quarter) > 0 else 0
                for quarter in quarters
            ]
            
            # Check if uncertainty increases over time
            uncertainty_trend = 'Increasing' if uncertainty_by_quarter[3] > uncertainty_by_quarter[0] else 'Stable or Decreasing'
        else:
            uncertainty_trend = 'Insufficient Data'
        
        # 2. Calculate memory retention score
        # Higher values of reference frequency indicate better memory retention
        retention_factors = [
            min(1, reference_frequency * 5)  # Scale to 0-1 range
        ]
        
        if uncertainty_trend != 'Insufficient Data':
            # Add uncertainty trend factor
            retention_factors.append(0.3 if uncertainty_trend == 'Stable or Decreasing' else 0.0)
        
        retention_score = sum(retention_factors) / len(retention_factors) if retention_factors else 0.5
        
        # Determine memory retention level
        retention_level = None
        if retention_score > 0.7:
            retention_level = 'High'
        elif retention_score > 0.4:
            retention_level = 'Moderate'
        else:
            retention_level = 'Low'
        
        return {
            'date_references_count': len(date_references),
            'avg_time_between_messages_seconds': float(avg_time_between_messages) if avg_time_between_messages is not None else None,
            'reference_frequency': float(reference_frequency),
            'uncertainty_trend': uncertainty_trend,
            'retention_score': float(retention_score),
            'retention_level': retention_level
        }
    
    def get_memory_patterns(self) -> Dict[str, Any]:
        """
        Get the current memory pattern analysis results.
        
        Returns:
            Dictionary of memory pattern analysis results
        """
        return self.memory_patterns