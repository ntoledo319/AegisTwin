"""Utility functions for MindMirror."""

import hashlib
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import pickle
import numpy as np
from collections import Counter

def generate_id(text: str) -> str:
    """Generate a deterministic ID from text.
    
    Args:
        text: Input text to hash.
        
    Returns:
        A SHA-256 hash of the normalized text.
    """
    # Normalize text
    normalized = unicodedata.normalize('NFKD', text.lower().strip())
    # Generate hash
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def normalize_text(text: str) -> str:
    """Normalize text for consistent processing.
    
    Args:
        text: Input text.
        
    Returns:
        Normalized text with consistent whitespace and punctuation.
    """
    if not text:
        return ""
        
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
        
    # Convert to lowercase
    text = text.lower()
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """Extract named entities from text using regex patterns.
    
    Args:
        text: Input text.
        
    Returns:
        List of extracted entities with type and text.
    """
    entities = []
    
    # Extract email addresses
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    for match in email_pattern.finditer(text):
        entities.append({
            'text': match.group(0),
            'type': 'EMAIL',
            'start': match.start(),
            'end': match.end()
        })
    
    # Extract URLs
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!.~\'*,;:=+$/?[\]@#&]*)*')
    for match in url_pattern.finditer(text):
        entities.append({
            'text': match.group(0),
            'type': 'URL',
            'start': match.start(),
            'end': match.end()
        })
    
    # Extract phone numbers
    phone_pattern = re.compile(r'(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}')
    for match in phone_pattern.finditer(text):
        entities.append({
            'text': match.group(0),
            'type': 'PHONE',
            'start': match.start(),
            'end': match.end()
        })
    
    # Extract dates
    date_pattern = re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b')
    for match in date_pattern.finditer(text):
        entities.append({
            'text': match.group(0),
            'type': 'DATE',
            'start': match.start(),
            'end': match.end()
        })
    
    # Extract times
    time_pattern = re.compile(r'\b(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s*[ap]\.?m\.?)?)\b')
    for match in time_pattern.finditer(text):
        entities.append({
            'text': match.group(0),
            'type': 'TIME',
            'start': match.start(),
            'end': match.end()
        })
    
    return entities

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity.
    
    Args:
        text1: First text.
        text2: Second text.
        
    Returns:
        Similarity score between 0 and 1.
    """
    # Tokenize texts
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0.0
        
    return intersection / union

def parse_date(date_string: str) -> Optional[datetime]:
    """Parse a date string into a datetime object.
    
    Args:
        date_string: String representation of a date.
        
    Returns:
        Datetime object or None if parsing fails.
    """
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f%z',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
            
    return None

def serialize_datetime(obj: Any) -> Any:
    """JSON serializer for datetime objects.
    
    Args:
        obj: Object to serialize.
        
    Returns:
        Serialized object.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_json_dumps(data: Any) -> str:
    """Safely convert data to JSON string.
    
    Args:
        data: Data to convert.
        
    Returns:
        JSON string.
    """
    return json.dumps(data, default=serialize_datetime)

def ensure_dir(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists.
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

def save_pickle(obj: Any, filepath: str) -> None:
    """Save an object to a pickle file.
    
    Args:
        obj: Object to save.
        filepath: Path to save the object to.
    """
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f)

def load_pickle(filepath: str) -> Any:
    """Load an object from a pickle file.
    
    Args:
        filepath: Path to load the object from.
        
    Returns:
        Loaded object.
    """
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def extract_keywords(text: str, top_n: int = 10) -> List[Tuple[str, int]]:
    """Extract keywords from text.
    
    Args:
        text: Input text.
        top_n: Number of top keywords to return.
        
    Returns:
        List of (keyword, count) tuples.
    """
    # Tokenize and clean
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'it', 'for',
        'with', 'as', 'was', 'on', 'are', 'be', 'this', 'by', 'from', 'at',
        'an', 'but', 'not', 'or', 'have', 'had', 'has', 'you', 'your', 'we',
        'our', 'they', 'their', 'he', 'she', 'his', 'her', 'my', 'i', 'me',
        'who', 'what', 'where', 'when', 'why', 'how', 'which', 'would', 'could',
        'should', 'will', 'can', 'do', 'does', 'did', 'been', 'being', 'am',
        'just', 'so', 'very', 'really', 'like', 'get', 'got', 'going', 'know',
        'think', 'see', 'go', 'im', 'dont', 'thats', 'its', 'yeah', 'okay'
    }
    
    filtered_words = [word for word in words if word not in stop_words]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Return top N keywords
    return word_counts.most_common(top_n)

def detect_emotion(text: str) -> Dict[str, float]:
    """Detect emotions in text using lexicon-based approach.
    
    Args:
        text: Input text.
        
    Returns:
        Dictionary mapping emotions to scores.
    """
    # Simple emotion lexicon
    emotion_lexicon = {
        'joy': ['happy', 'joy', 'delighted', 'glad', 'pleased', 'excited', 'love', 'wonderful', 'amazing', 'awesome', 'great', 'excellent', 'fantastic', 'terrific', 'yay', 'woohoo', 'haha', 'lol', 'lmao', 'hehe'],
        'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'gloomy', 'disappointed', 'sorry', 'regret', 'miss', 'lonely', 'alone', 'crying', 'tear', 'tears', 'upset', 'heartbroken', 'grief', 'sigh'],
        'anger': ['angry', 'mad', 'furious', 'rage', 'hate', 'annoyed', 'irritated', 'frustrated', 'pissed', 'damn', 'fuck', 'shit', 'wtf', 'ugh', 'grr', 'argh'],
        'fear': ['afraid', 'scared', 'frightened', 'terrified', 'anxious', 'nervous', 'worried', 'concerned', 'panic', 'dread', 'horror', 'terror', 'yikes', 'omg'],
        'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'wow', 'whoa', 'omg', 'oh', 'what', 'huh', 'unexpected', 'sudden'],
        'disgust': ['disgusted', 'gross', 'yuck', 'ew', 'nasty', 'sick', 'revolting', 'repulsive', 'distasteful', 'unpleasant', 'awful', 'terrible', 'horrible']
    }
    
    # Normalize text
    normalized_text = normalize_text(text)
    words = re.findall(r'\b[a-zA-Z]+\b', normalized_text)
    
    # Initialize emotion scores
    emotion_scores = {emotion: 0.0 for emotion in emotion_lexicon}
    
    # Count emotion words
    for word in words:
        for emotion, emotion_words in emotion_lexicon.items():
            if word in emotion_words:
                emotion_scores[emotion] += 1.0
    
    # Normalize scores
    total_score = sum(emotion_scores.values())
    if total_score > 0:
        for emotion in emotion_scores:
            emotion_scores[emotion] /= total_score
    
    return emotion_scores

def get_message_context(messages: List[Dict[str, Any]], message_index: int, window_size: int = 5) -> List[Dict[str, Any]]:
    """Get context messages around a specific message.
    
    Args:
        messages: List of messages.
        message_index: Index of the target message.
        window_size: Number of messages to include before and after.
        
    Returns:
        List of context messages.
    """
    start_idx = max(0, message_index - window_size)
    end_idx = min(len(messages), message_index + window_size + 1)
    
    return messages[start_idx:end_idx]

def calculate_response_time(messages: List[Dict[str, Any]]) -> Dict[str, timedelta]:
    """Calculate average response time for each participant.
    
    Args:
        messages: List of messages.
        
    Returns:
        Dictionary mapping participants to average response times.
    """
    response_times = {}
    last_message = {}
    
    for i, message in enumerate(messages):
        sender = message.get('sender_name', '')
        timestamp = parse_date(message.get('message_date', ''))
        
        if not sender or not timestamp:
            continue
            
        # Check if this is a response to someone else
        for other_sender, (other_time, _) in last_message.items():
            if other_sender != sender:
                response_time = timestamp - other_time
                
                # Only count if response time is reasonable (less than a day)
                if timedelta(0) < response_time < timedelta(days=1):
                    if sender not in response_times:
                        response_times[sender] = []
                        
                    response_times[sender].append(response_time)
        
        # Update last message for this sender
        last_message[sender] = (timestamp, i)
    
    # Calculate averages
    avg_response_times = {}
    for sender, times in response_times.items():
        if times:
            avg_response_times[sender] = sum(times, timedelta(0)) / len(times)
    
    return avg_response_times