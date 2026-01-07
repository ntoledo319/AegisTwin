"""
Utility functions for Cognitive-Twin Omega.

This module provides common utility functions used throughout the Cognitive-Twin Omega system.
"""

import os
import re
import hashlib
import json
import pickle
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set, Callable
import pandas as pd
import numpy as np
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

# Text processing utilities
def normalize_text(text: str, 
                   lowercase: bool = True, 
                   remove_urls: bool = False,
                   remove_emails: bool = False,
                   remove_phone_numbers: bool = False,
                   expand_contractions: bool = False,
                   fix_unicode: bool = True) -> str:
    """
    Normalize text with configurable options.
    
    Args:
        text: Input text to normalize
        lowercase: Convert to lowercase
        remove_urls: Remove URLs
        remove_emails: Remove email addresses
        remove_phone_numbers: Remove phone numbers
        expand_contractions: Expand contractions (e.g., "don't" -> "do not")
        fix_unicode: Fix common unicode issues
        
    Returns:
        Normalized text
    """
    if not isinstance(text, str):
        return ""
    
    # Fix unicode issues
    if fix_unicode:
        text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remove URLs
    if remove_urls:
        text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    
    # Remove email addresses
    if remove_emails:
        text = re.sub(r'\S+@\S+', ' ', text)
    
    # Remove phone numbers
    if remove_phone_numbers:
        text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', ' ', text)
    
    # Expand contractions
    if expand_contractions:
        text = expand_text_contractions(text)
    
    # Convert to lowercase
    if lowercase:
        text = text.lower()
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def expand_text_contractions(text: str) -> str:
    """
    Expand common English contractions in text.
    
    Args:
        text: Input text with contractions
        
    Returns:
        Text with expanded contractions
    """
    # Common English contractions
    contractions = {
        "ain't": "am not",
        "aren't": "are not",
        "can't": "cannot",
        "can't've": "cannot have",
        "'cause": "because",
        "could've": "could have",
        "couldn't": "could not",
        "couldn't've": "could not have",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hadn't've": "had not have",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'd've": "he would have",
        "he'll": "he will",
        "he'll've": "he will have",
        "he's": "he is",
        "how'd": "how did",
        "how'd'y": "how do you",
        "how'll": "how will",
        "how's": "how is",
        "i'd": "i would",
        "i'd've": "i would have",
        "i'll": "i will",
        "i'll've": "i will have",
        "i'm": "i am",
        "i've": "i have",
        "isn't": "is not",
        "it'd": "it would",
        "it'd've": "it would have",
        "it'll": "it will",
        "it'll've": "it will have",
        "it's": "it is",
        "let's": "let us",
        "ma'am": "madam",
        "mayn't": "may not",
        "might've": "might have",
        "mightn't": "might not",
        "mightn't've": "might not have",
        "must've": "must have",
        "mustn't": "must not",
        "mustn't've": "must not have",
        "needn't": "need not",
        "needn't've": "need not have",
        "o'clock": "of the clock",
        "oughtn't": "ought not",
        "oughtn't've": "ought not have",
        "shan't": "shall not",
        "sha'n't": "shall not",
        "shan't've": "shall not have",
        "she'd": "she would",
        "she'd've": "she would have",
        "she'll": "she will",
        "she'll've": "she will have",
        "she's": "she is",
        "should've": "should have",
        "shouldn't": "should not",
        "shouldn't've": "should not have",
        "so've": "so have",
        "so's": "so is",
        "that'd": "that would",
        "that'd've": "that would have",
        "that's": "that is",
        "there'd": "there would",
        "there'd've": "there would have",
        "there's": "there is",
        "they'd": "they would",
        "they'd've": "they would have",
        "they'll": "they will",
        "they'll've": "they will have",
        "they're": "they are",
        "they've": "they have",
        "to've": "to have",
        "wasn't": "was not",
        "we'd": "we would",
        "we'd've": "we would have",
        "we'll": "we will",
        "we'll've": "we will have",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what'll've": "what will have",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "when's": "when is",
        "when've": "when have",
        "where'd": "where did",
        "where's": "where is",
        "where've": "where have",
        "who'll": "who will",
        "who'll've": "who will have",
        "who's": "who is",
        "who've": "who have",
        "why's": "why is",
        "why've": "why have",
        "will've": "will have",
        "won't": "will not",
        "won't've": "will not have",
        "would've": "would have",
        "wouldn't": "would not",
        "wouldn't've": "would not have",
        "y'all": "you all",
        "y'all'd": "you all would",
        "y'all'd've": "you all would have",
        "y'all're": "you all are",
        "y'all've": "you all have",
        "you'd": "you would",
        "you'd've": "you would have",
        "you'll": "you will",
        "you'll've": "you will have",
        "you're": "you are",
        "you've": "you have"
    }
    
    # Sort by length (longest first) to avoid partial replacements
    sorted_contractions = sorted(contractions.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Replace contractions
    for contraction, expansion in sorted_contractions:
        text = re.sub(r'\b' + re.escape(contraction) + r'\b', expansion, text, flags=re.IGNORECASE)
    
    return text

# Hashing and deduplication utilities
def compute_text_hash(text: str, method: str = 'sha256') -> str:
    """
    Compute a hash of the given text.
    
    Args:
        text: Input text to hash
        method: Hash method (md5, sha1, sha256)
        
    Returns:
        Hexadecimal hash string
    """
    if not isinstance(text, str):
        text = str(text)
    
    text = text.encode('utf-8', errors='ignore')
    
    if method == 'md5':
        return hashlib.md5(text).hexdigest()
    elif method == 'sha1':
        return hashlib.sha1(text).hexdigest()
    else:  # default to sha256
        return hashlib.sha256(text).hexdigest()

def compute_conversation_hash(sender: str, receiver: str, timestamp: str, text: str) -> str:
    """
    Compute a hash for a conversation message.
    
    Args:
        sender: Message sender
        receiver: Message receiver
        timestamp: Message timestamp
        text: Message text
        
    Returns:
        Hexadecimal hash string
    """
    components = [
        str(sender).strip(),
        str(receiver).strip(),
        str(timestamp).strip(),
        str(text).strip()
    ]
    
    message_str = "|".join(components)
    return compute_text_hash(message_str)

def is_near_duplicate(text1: str, text2: str, threshold: float = 0.9) -> bool:
    """
    Check if two texts are near duplicates using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold (0-1)
        
    Returns:
        True if texts are near duplicates, False otherwise
    """
    # Convert to sets of words
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return text1 == text2
    
    similarity = intersection / union
    return similarity >= threshold

# Date and time utilities
def parse_date(date_str: str, 
               formats: List[str] = None, 
               default_timezone: str = 'UTC') -> Optional[datetime.datetime]:
    """
    Parse a date string using multiple possible formats.
    
    Args:
        date_str: Date string to parse
        formats: List of date formats to try
        default_timezone: Default timezone to use if not specified
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%b %d, %Y',
            '%B %d, %Y',
            '%b %d, %Y %H:%M:%S',
            '%B %d, %Y %H:%M:%S'
        ]
    
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            # Add timezone if not present
            if dt.tzinfo is None:
                import pytz
                dt = dt.replace(tzinfo=pytz.timezone(default_timezone))
            return dt
        except ValueError:
            continue
    
    # Try pandas parsing as a fallback
    try:
        dt = pd.to_datetime(date_str)
        # Add timezone if not present
        if dt.tzinfo is None:
            import pytz
            dt = dt.replace(tzinfo=pytz.timezone(default_timezone))
        return dt.to_pydatetime()
    except:
        return None

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

# File and serialization utilities
def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object for the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: Any, filepath: Union[str, Path], ensure_ascii: bool = False, indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save to
        ensure_ascii: Whether to escape non-ASCII characters
        indent: Indentation level
    """
    ensure_dir(Path(filepath).parent)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)

def load_json(filepath: Union[str, Path]) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to load from
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pickle(data: Any, filepath: Union[str, Path]) -> None:
    """
    Save data to a pickle file.
    
    Args:
        data: Data to save
        filepath: Path to save to
    """
    ensure_dir(Path(filepath).parent)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

def load_pickle(filepath: Union[str, Path]) -> Any:
    """
    Load data from a pickle file.
    
    Args:
        filepath: Path to load from
        
    Returns:
        Loaded data
    """
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def save_dataframe(df: pd.DataFrame, filepath: Union[str, Path], format: str = 'parquet') -> None:
    """
    Save a DataFrame to a file.
    
    Args:
        df: DataFrame to save
        filepath: Path to save to
        format: File format (csv, parquet, feather)
    """
    ensure_dir(Path(filepath).parent)
    
    if format == 'csv':
        df.to_csv(filepath, index=False, encoding='utf-8')
    elif format == 'parquet':
        df.to_parquet(filepath, index=False)
    elif format == 'feather':
        df.to_feather(filepath)
    else:
        raise ValueError(f"Unsupported format: {format}")

def load_dataframe(filepath: Union[str, Path], format: str = None) -> pd.DataFrame:
    """
    Load a DataFrame from a file.
    
    Args:
        filepath: Path to load from
        format: File format (csv, parquet, feather)
        
    Returns:
        Loaded DataFrame
    """
    path = Path(filepath)
    
    if format is None:
        # Infer format from extension
        format = path.suffix.lstrip('.').lower()
    
    if format == 'csv':
        return pd.read_csv(filepath, encoding='utf-8')
    elif format == 'parquet':
        return pd.read_parquet(filepath)
    elif format == 'feather':
        return pd.read_feather(filepath)
    else:
        raise ValueError(f"Unsupported format: {format}")

# Memory management utilities
def get_memory_usage() -> Dict[str, Union[float, str]]:
    """
    Get current memory usage information.
    
    Returns:
        Dictionary with memory usage information
    """
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Convert to MB
    rss_mb = memory_info.rss / (1024 * 1024)
    vms_mb = memory_info.vms / (1024 * 1024)
    
    return {
        'rss': rss_mb,
        'rss_human': f"{rss_mb:.1f} MB",
        'vms': vms_mb,
        'vms_human': f"{vms_mb:.1f} MB",
        'percent': process.memory_percent(),
        'percent_human': f"{process.memory_percent():.1f}%"
    }

def log_memory_usage(logger: logging.Logger, message: str = "Current memory usage") -> None:
    """
    Log current memory usage.
    
    Args:
        logger: Logger to use
        message: Message prefix
    """
    memory = get_memory_usage()
    logger.info(f"{message}: {memory['rss_human']} (RSS), {memory['percent_human']} of total")

# Batch processing utilities
def process_in_batches(items: List[Any], 
                       process_func: Callable[[List[Any]], List[Any]], 
                       batch_size: int = 1000, 
                       show_progress: bool = True) -> List[Any]:
    """
    Process a list of items in batches.
    
    Args:
        items: List of items to process
        process_func: Function to process a batch of items
        batch_size: Number of items per batch
        show_progress: Whether to show a progress bar
        
    Returns:
        List of processed items
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    if show_progress:
        from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            task = progress.add_task("Processing batches...", total=total_batches)
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                batch_results = process_func(batch)
                results.extend(batch_results)
                progress.update(task, advance=1)
    else:
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            batch_results = process_func(batch)
            results.extend(batch_results)
    
    return results

# Text analysis utilities
def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted URLs
    """
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|bit\.ly/[^\s<>"]+|t\.co/[^\s<>"]+|tinyurl\.com/[^\s<>"]+|goo\.gl/[^\s<>"]+|fb\.me/[^\s<>"]+|amzn\.to/[^\s<>"]+|youtu\.be/[^\s<>"]+|on\.fb\.me/[^\s<>"]+|buff\.ly/[^\s<>"]+|ow\.ly/[^\s<>"]+|is\.gd/[^\s<>"]+|su\.pr/[^\s<>"]+|tiny\.cc/[^\s<>"]+|tr\.im/[^\s<>"]+|cli\.gs/[^\s<>"]+|mee\.bo/[^\s<>"]+|wp\.me/[^\s<>"]+|bit\.do/[^\s<>"]+|trib\.al/[^\s<>"]+|adf\.ly/[^\s<>"]+|dlvr\.it/[^\s<>"]+|ift\.tt/[^\s<>"]+|fb\.com/[^\s<>"]+|j\.mp/[^\s<>"]+|spr\.ly/[^\s<>"]+|v\.gd/[^\s<>"]+|tmblr\.co/[^\s<>"]+|ping\.fm/[^\s<>"]+|post\.ly/[^\s<>"]+|just\.as/[^\s<>"]+|bkite\.com/[^\s<>"]+|snipr\.com/[^\s<>"]+|fic\.kr/[^\s<>"]+|loopt\.us/[^\s<>"]+|doiop\.com/[^\s<>"]+|twitthis\.com/[^\s<>"]+|htxt\.it/[^\s<>"]+|bacn\.me/[^\s<>"]+|shrinkify\.com/[^\s<>"]+|buzurl\.com/[^\s<>"]+|cutt\.us/[^\s<>"]+|u\.nu/[^\s<>"]+|1url\.com/[^\s<>"]+|tweez\.me/[^\s<>"]+|snipurl\.com/[^\s<>"]+|short\.ie/[^\s<>"]+|kl\.am/[^\s<>"]+|wp\.me/[^\s<>"]+|rubyurl\.com/[^\s<>"]+|om\.ly/[^\s<>"]+|linkbun\.ch/[^\s<>"]+|prettylinkpro\.com/[^\s<>"]+|bsa\.ly/[^\s<>"]+|2tu\.us/[^\s<>"]+|twiturl\.de/[^\s<>"]+|to\.ly/[^\s<>"]+|BudURL\.com/[^\s<>"]+|shrinkr\.com/[^\s<>"]+|ln-s\.net/[^\s<>"]+|tiny\.pl/[^\s<>"]+|lnk\.gd/[^\s<>"]+|xrl\.us/[^\s<>"]+|4url\.cc/[^\s<>"]+|tinyurl\.com/[^\s<>"]+|notlong\.com/[^\s<>"]+|qlnk\.net/[^\s<>"]+|twurl\.nl/[^\s<>"]+|ow\.ly/[^\s<>"]+|bit\.ly/[^\s<>"]+|a\.gd/[^\s<>"]+|t\.co/[^\s<>"]+|lnkd\.in/[^\s<>"]+|db\.tt/[^\s<>"]+|qr\.ae/[^\s<>"]+|adf\.ly/[^\s<>"]+|goo\.gl/[^\s<>"]+|bitly\.com/[^\s<>"]+|cur\.lv/[^\s<>"]+|tinyurl\.com/[^\s<>"]+|ity\.im/[^\s<>"]+|q\.gs/[^\s<>"]+|is\.gd/[^\s<>"]+|po\.st/[^\s<>"]+|bc\.vc/[^\s<>"]+|twitthis\.com/[^\s<>"]+|u\.to/[^\s<>"]+|j\.mp/[^\s<>"]+|buzurl\.com/[^\s<>"]+|cutt\.us/[^\s<>"]+|u\.bb/[^\s<>"]+|yourls\.org/[^\s<>"]+|x\.co/[^\s<>"]+|prettylinkpro\.com/[^\s<>"]+|scrnch\.me/[^\s<>"]+|filoops\.info/[^\s<>"]+|vzturl\.com/[^\s<>"]+|qr\.net/[^\s<>"]+|1url\.com/[^\s<>"]+|tweez\.me/[^\s<>"]+|v\.gd/[^\s<>"]+|tr\.im/[^\s<>"]+|link\.zip\.net/[^\s<>"]+|tinyarrows\.com/[^\s<>"]+|shrinkster\.com/'
    
    urls = re.findall(url_pattern, text)
    return urls

# Email extraction
def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted email addresses
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails

# Phone number extraction
def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted phone numbers
    """
    # This pattern covers common US phone number formats
    phone_pattern = r'(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phones = re.findall(phone_pattern, text)
    return phones

# Text statistics
def get_text_stats(text: str) -> Dict[str, Any]:
    """
    Get statistics about a text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with text statistics
    """
    if not text:
        return {
            'char_count': 0,
            'word_count': 0,
            'sentence_count': 0,
            'avg_word_length': 0,
            'avg_sentence_length': 0
        }
    
    # Character count
    char_count = len(text)
    
    # Word count
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    
    # Sentence count
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # Average word length
    avg_word_length = sum(len(word) for word in words) / max(1, word_count)
    
    # Average sentence length (in words)
    avg_sentence_length = word_count / max(1, sentence_count)
    
    return {
        'char_count': char_count,
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_word_length': avg_word_length,
        'avg_sentence_length': avg_sentence_length
    }