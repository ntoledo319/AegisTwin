"""
Cognitive-Twin Omega - Data Preprocessing System

This module provides comprehensive data preprocessing capabilities for Cognitive-Twin Omega,
enabling the system to clean, normalize, deduplicate, and prepare data for analysis.
"""

import logging
import re
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from collections import defaultdict

import pandas as pd
import numpy as np
from tqdm import tqdm
from rapidfuzz import fuzz
import yaml

from cognitive_twin.core.utils import (
    ensure_dir, normalize_text, compute_text_hash, 
    is_near_duplicate, parse_date
)

# Initialize logger
logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Manages the preprocessing of data for Cognitive-Twin Omega.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data preprocessor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.raw_dir = Path(config['paths']['raw'])
        self.interim_dir = Path(config['paths']['interim'])
        self.processed_dir = Path(config['paths']['processed'])
        
        # Ensure directories exist
        ensure_dir(self.raw_dir)
        ensure_dir(self.interim_dir)
        ensure_dir(self.processed_dir)
        
        # Load preprocessing configuration
        self.preprocess_config = config.get('preprocessing', {})
        
        # Load identity mapping
        self.identity_mapping = self._load_identity_mapping()
        
        # Initialize stats
        self.stats = {
            'total_items': 0,
            'processed_items': 0,
            'duplicates_removed': 0,
            'spam_filtered': 0,
            'normalized_items': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def _load_identity_mapping(self) -> Dict[str, str]:
        """
        Load identity mapping from aliases configuration.
        
        Returns:
            Dictionary mapping aliases to canonical names
        """
        identity_mapping = {}
        
        try:
            # Get the path to the aliases file
            aliases_file = self.config.get('relationship_modeling', {}).get('identity', {}).get('canonical_mapping_file')
            if not aliases_file:
                logger.warning("No aliases file specified in configuration")
                return identity_mapping
            
            # Load the aliases file
            with open(aliases_file, 'r') as f:
                aliases_data = yaml.safe_load(f)
            
            # Extract canonical mappings
            if 'canonical' in aliases_data:
                for alias, canonical in aliases_data['canonical'].items():
                    identity_mapping[alias.lower()] = canonical
            
            logger.info(f"Loaded {len(identity_mapping)} identity mappings")
            
        except Exception as e:
            logger.error(f"Error loading identity mapping: {str(e)}", exc_info=True)
        
        return identity_mapping
    
    def process_all(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all data sources.
        
        Args:
            data_sources: Dictionary of data sources
            
        Returns:
            Dictionary of processed data
        """
        logger.info("Processing all data sources")
        
        processed_data = {}
        
        # Process each data source
        for source_type, source_data in data_sources.items():
            logger.info(f"Processing {source_type} data")
            
            try:
                if source_type == 'text_messages':
                    processed_data[source_type] = self.process_text_messages(source_data)
                elif source_type == 'emails':
                    processed_data[source_type] = self.process_emails(source_data)
                elif source_type == 'documents':
                    processed_data[source_type] = self.process_documents(source_data)
                elif source_type == 'social_media':
                    processed_data[source_type] = self.process_social_media(source_data)
                elif source_type == 'calendar':
                    processed_data[source_type] = self.process_calendar(source_data)
                elif source_type == 'location':
                    processed_data[source_type] = self.process_location(source_data)
                elif source_type == 'photos':
                    processed_data[source_type] = self.process_photos(source_data)
                else:
                    logger.warning(f"No processor implemented for data source type: {source_type}")
            except Exception as e:
                logger.error(f"Error processing {source_type} data: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
        
        logger.info(f"Processed {self.stats['processed_items']}/{self.stats['total_items']} items")
        logger.info(f"Removed {self.stats['duplicates_removed']} duplicates and {self.stats['spam_filtered']} spam items")
        logger.info(f"Normalized {self.stats['normalized_items']} items")
        logger.info(f"Encountered {self.stats['errors']} errors and {self.stats['warnings']} warnings")
        
        return processed_data
    
    def process_text_messages(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process text messages.
        
        Args:
            data: DataFrame of text messages
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing {len(data)} text messages")
        self.stats['total_items'] += len(data)
        
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # 1. Normalize text content
        df = self._normalize_text_content(df, 'content')
        
        # 2. Normalize sender/conversation names
        df = self._normalize_identities(df)
        
        # 3. Remove duplicates
        df = self._remove_duplicates(df)
        
        # 4. Filter spam
        df = self._filter_spam(df)
        
        # 5. Identify subject's messages
        df = self._identify_subject_messages(df)
        
        # 6. Add additional metadata
        df = self._add_text_message_metadata(df)
        
        # Save processed data
        processed_path = self.processed_dir / 'text_messages.parquet'
        df.to_parquet(processed_path, index=False)
        logger.info(f"Saved processed text messages to {processed_path}")
        
        self.stats['processed_items'] += len(df)
        return df
    
    def _normalize_text_content(self, df: pd.DataFrame, content_column: str) -> pd.DataFrame:
        """
        Normalize text content in a DataFrame.
        
        Args:
            df: DataFrame to process
            content_column: Name of the column containing text content
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Normalizing text content in {content_column} column")
        
        # Get text normalization config
        text_norm_config = self.preprocess_config.get('text_normalization', {})
        
        # Apply normalization
        df['content_original'] = df[content_column]
        df[content_column] = df[content_column].apply(
            lambda x: normalize_text(
                x,
                lowercase=text_norm_config.get('lowercase', True),
                remove_urls=text_norm_config.get('remove_urls', False),
                remove_emails=text_norm_config.get('remove_emails', False),
                remove_phone_numbers=text_norm_config.get('remove_phone_numbers', False),
                expand_contractions=text_norm_config.get('expand_contractions', False),
                fix_unicode=text_norm_config.get('fix_unicode', True)
            ) if pd.notna(x) else ""
        )
        
        # Add normalized content hash
        df['content_hash'] = df[content_column].apply(lambda x: compute_text_hash(x))
        
        self.stats['normalized_items'] += len(df)
        return df
    
    def _normalize_identities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize sender and conversation identities.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame
        """
        logger.info("Normalizing sender and conversation identities")
        
        # Add canonical sender column
        df['sender_canonical'] = df['sender'].apply(
            lambda x: self._get_canonical_identity(x) if pd.notna(x) else None
        )
        
        # Add canonical conversation column
        df['conversation_canonical'] = df['conversation'].apply(
            lambda x: self._get_canonical_identity(x) if pd.notna(x) else None
        )
        
        return df
    
    def _get_canonical_identity(self, name: str) -> str:
        """
        Get the canonical identity for a name.
        
        Args:
            name: Name to normalize
            
        Returns:
            Canonical identity
        """
        if not name:
            return name
        
        # Check direct match
        name_lower = name.lower()
        if name_lower in self.identity_mapping:
            return self.identity_mapping[name_lower]
        
        # Check fuzzy match if enabled
        fuzzy_matching = self.config.get('relationship_modeling', {}).get('identity', {}).get('fuzzy_matching', False)
        if fuzzy_matching:
            fuzzy_threshold = self.config.get('relationship_modeling', {}).get('identity', {}).get('fuzzy_threshold', 85)
            
            best_match = None
            best_score = 0
            
            for alias in self.identity_mapping.keys():
                score = fuzz.ratio(name_lower, alias)
                if score > fuzzy_threshold and score > best_score:
                    best_match = alias
                    best_score = score
            
            if best_match:
                return self.identity_mapping[best_match]
        
        # No match found, return original
        return name
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate messages.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with duplicates removed
        """
        logger.info("Removing duplicate messages")
        
        # Get deduplication config
        dedup_config = self.preprocess_config.get('deduplication', {})
        if not dedup_config.get('enabled', True):
            logger.info("Deduplication disabled, skipping")
            return df
        
        # Count before deduplication
        count_before = len(df)
        
        # Apply deduplication methods
        methods = dedup_config.get('methods', ['exact_match'])
        
        if 'exact_match' in methods:
            # Remove exact duplicates based on content hash
            df = df.drop_duplicates(subset=['content_hash', 'sender_canonical', 'conversation_canonical'])
        
        if 'near_duplicate' in methods:
            # Remove near-duplicates
            threshold = dedup_config.get('threshold', 0.95)
            df = self._remove_near_duplicates(df, threshold)
        
        # Count after deduplication
        count_after = len(df)
        duplicates_removed = count_before - count_after
        
        logger.info(f"Removed {duplicates_removed} duplicate messages")
        self.stats['duplicates_removed'] += duplicates_removed
        
        return df
    
    def _remove_near_duplicates(self, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """
        Remove near-duplicate messages.
        
        Args:
            df: DataFrame to process
            threshold: Similarity threshold for near-duplicates
            
        Returns:
            Processed DataFrame with near-duplicates removed
        """
        logger.info(f"Removing near-duplicates with threshold {threshold}")
        
        # Group by conversation and sender
        groups = df.groupby(['conversation_canonical', 'sender_canonical'])
        
        # Process each group
        keep_indices = []
        
        for (conv, sender), group in tqdm(groups, desc="Processing conversation groups"):
            # Sort by timestamp
            sorted_group = group.sort_values('timestamp')
            
            # Initialize list of messages to keep
            group_keep_indices = []
            
            for i, row in sorted_group.iterrows():
                # Check if this message is a near-duplicate of any kept message
                is_duplicate = False
                
                for keep_idx in group_keep_indices:
                    keep_row = sorted_group.loc[keep_idx]
                    
                    # Check if messages are near-duplicates
                    if is_near_duplicate(row['content'], keep_row['content'], threshold):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    group_keep_indices.append(i)
            
            keep_indices.extend(group_keep_indices)
        
        # Filter DataFrame to keep only non-duplicate messages
        filtered_df = df.loc[keep_indices].copy()
        
        return filtered_df
    
    def _filter_spam(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter spam messages.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with spam filtered
        """
        logger.info("Filtering spam messages")
        
        # Get spam filtering config
        spam_config = self.preprocess_config.get('spam_filtering', {})
        if not spam_config.get('enabled', True):
            logger.info("Spam filtering disabled, skipping")
            return df
        
        # Count before filtering
        count_before = len(df)
        
        # Load spam rules
        rules_file = spam_config.get('rules_file')
        if rules_file:
            try:
                with open(rules_file, 'r') as f:
                    spam_rules = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading spam rules: {str(e)}", exc_info=True)
                spam_rules = {}
        else:
            spam_rules = {}
        
        # Apply minimum content length filter
        min_length = spam_config.get('min_content_length', 3)
        df['is_spam'] = df['content'].apply(lambda x: len(str(x)) < min_length if pd.notna(x) else True)
        
        # Apply drop rules
        if 'drop_if' in spam_rules:
            for rule in spam_rules['drop_if']:
                if rule['type'] == 'length_lt':
                    # Already handled by min_content_length
                    pass
                elif rule['type'] == 'emoji_only':
                    # Simple emoji-only check (could be improved)
                    emoji_pattern = re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251\U0001f926-\U0001f937]+$')
                    df.loc[df['is_spam'] == False, 'is_spam'] = df.loc[df['is_spam'] == False, 'content'].apply(
                        lambda x: bool(emoji_pattern.match(str(x))) if pd.notna(x) else True
                    )
                elif rule['type'] == 'link_only':
                    # Simple link-only check
                    link_pattern = re.compile(r'^https?://\S+$')
                    df.loc[df['is_spam'] == False, 'is_spam'] = df.loc[df['is_spam'] == False, 'content'].apply(
                        lambda x: bool(link_pattern.match(str(x))) if pd.notna(x) else True
                    )
                elif rule['type'] == 'reaction_only':
                    # Simple reaction-only check
                    reaction_pattern = re.compile(r'^(haha|lol|wow|omg|👍|❤️|😂|😮|😍|👏)$', re.IGNORECASE)
                    df.loc[df['is_spam'] == False, 'is_spam'] = df.loc[df['is_spam'] == False, 'content'].apply(
                        lambda x: bool(reaction_pattern.match(str(x))) if pd.notna(x) else True
                    )
                elif rule['type'] == 'exact':
                    # Exact match check
                    if 'values' in rule:
                        exact_values = set(rule['values'])
                        df.loc[df['is_spam'] == False, 'is_spam'] = df.loc[df['is_spam'] == False, 'content'].apply(
                            lambda x: str(x).strip() in exact_values if pd.notna(x) else True
                        )
                elif rule['type'] == 'forward_dup':
                    # Forward duplicate check (already handled by deduplication)
                    pass
        
        # Apply keep rules (override spam classification)
        if 'keep_if' in spam_rules:
            for keyword in spam_rules['keep_if']:
                if isinstance(keyword, str):
                    # Simple keyword check
                    df.loc[df['is_spam'] == True, 'is_spam'] = ~df.loc[df['is_spam'] == True, 'content'].apply(
                        lambda x: keyword.lower() in str(x).lower() if pd.notna(x) else False
                    )
        
        # Filter out spam messages
        filtered_df = df[~df['is_spam']].copy()
        filtered_df = filtered_df.drop(columns=['is_spam'])
        
        # Count after filtering
        count_after = len(filtered_df)
        spam_filtered = count_before - count_after
        
        logger.info(f"Filtered {spam_filtered} spam messages")
        self.stats['spam_filtered'] += spam_filtered
        
        return filtered_df
    
    def _identify_subject_messages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify messages sent by the subject.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with subject messages identified
        """
        logger.info("Identifying subject messages")
        
        # If is_from_subject is already present, use it
        if 'is_from_subject' in df.columns:
            return df
        
        # Try to identify subject messages based on sender
        # This is a placeholder - in a real implementation, you would
        # use more sophisticated methods to identify the subject
        
        # For now, assume the most frequent sender is the subject
        sender_counts = df['sender_canonical'].value_counts()
        if not sender_counts.empty:
            most_frequent_sender = sender_counts.index[0]
            df['is_from_subject'] = df['sender_canonical'] == most_frequent_sender
            
            logger.info(f"Identified {df['is_from_subject'].sum()} messages from subject (assumed to be {most_frequent_sender})")
        else:
            df['is_from_subject'] = False
            logger.warning("Could not identify subject messages")
        
        return df
    
    def _add_text_message_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add additional metadata to text messages.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with additional metadata
        """
        logger.info("Adding text message metadata")
        
        # Add message length
        df['content_length'] = df['content'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
        
        # Add word count
        df['word_count'] = df['content'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
        
        # Add day of week
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Add hour of day
        df['hour_of_day'] = df['timestamp'].dt.hour
        
        # Add is_question flag
        df['is_question'] = df['content'].apply(
            lambda x: '?' in str(x) if pd.notna(x) else False
        )
        
        # Add has_url flag
        url_pattern = re.compile(r'https?://\S+')
        df['has_url'] = df['content'].apply(
            lambda x: bool(url_pattern.search(str(x))) if pd.notna(x) else False
        )
        
        # Add has_emoji flag (simple check)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251\U0001f926-\U0001f937]')
        df['has_emoji'] = df['content_original'].apply(
            lambda x: bool(emoji_pattern.search(str(x))) if pd.notna(x) else False
        )
        
        return df
    
    def process_emails(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process emails.
        
        Args:
            data: DataFrame of emails
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing {len(data)} emails")
        self.stats['total_items'] += len(data)
        
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # 1. Normalize text content
        df = self._normalize_text_content(df, 'body')
        
        # 2. Normalize sender/recipient identities
        df = self._normalize_email_identities(df)
        
        # 3. Remove duplicates
        df = self._remove_duplicates(df)
        
        # 4. Filter spam
        df = self._filter_spam(df)
        
        # 5. Identify subject's emails
        df = self._identify_subject_emails(df)
        
        # 6. Add additional metadata
        df = self._add_email_metadata(df)
        
        # Save processed data
        processed_path = self.processed_dir / 'emails.parquet'
        df.to_parquet(processed_path, index=False)
        logger.info(f"Saved processed emails to {processed_path}")
        
        self.stats['processed_items'] += len(df)
        return df
    
    def _normalize_email_identities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize email sender and recipient identities.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame
        """
        logger.info("Normalizing email identities")
        
        # Extract name from email address
        def extract_name_from_email(email_str):
            if not pd.notna(email_str):
                return None
            
            # Try to extract name from "Name <email>" format
            name_match = re.match(r'"?([^"<]+)"?\s*<[^>]+>', email_str)
            if name_match:
                return name_match.group(1).strip()
            
            # Otherwise, use the part before @ as a fallback
            email_match = re.search(r'([^@]+)@', email_str)
            if email_match:
                return email_match.group(1).strip()
            
            return email_str
        
        # Add sender name column
        df['sender_name'] = df['sender'].apply(extract_name_from_email)
        
        # Add canonical sender column
        df['sender_canonical'] = df['sender_name'].apply(
            lambda x: self._get_canonical_identity(x) if pd.notna(x) else None
        )
        
        # Add recipient name column
        df['recipient_name'] = df['recipient'].apply(extract_name_from_email)
        
        # Add canonical recipient column
        df['recipient_canonical'] = df['recipient_name'].apply(
            lambda x: self._get_canonical_identity(x) if pd.notna(x) else None
        )
        
        return df
    
    def _identify_subject_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify emails sent by the subject.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with subject emails identified
        """
        logger.info("Identifying subject emails")
        
        # If is_from_subject is already present, use it
        if 'is_from_subject' in df.columns:
            return df
        
        # Try to identify subject emails based on sender
        # This is a placeholder - in a real implementation, you would
        # use more sophisticated methods to identify the subject
        
        # For now, assume the most frequent sender is the subject
        sender_counts = df['sender_canonical'].value_counts()
        if not sender_counts.empty:
            most_frequent_sender = sender_counts.index[0]
            df['is_from_subject'] = df['sender_canonical'] == most_frequent_sender
            
            logger.info(f"Identified {df['is_from_subject'].sum()} emails from subject (assumed to be {most_frequent_sender})")
        else:
            df['is_from_subject'] = False
            logger.warning("Could not identify subject emails")
        
        return df
    
    def _add_email_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add additional metadata to emails.
        
        Args:
            df: DataFrame to process
            
        Returns:
            Processed DataFrame with additional metadata
        """
        logger.info("Adding email metadata")
        
        # Add content length
        df['content_length'] = df['body'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
        
        # Add word count
        df['word_count'] = df['body'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
        
        # Add day of week
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Add hour of day
        df['hour_of_day'] = df['timestamp'].dt.hour
        
        # Add has_attachment flag
        if 'attachments' in df.columns:
            df['has_attachment'] = df['attachments'].apply(
                lambda x: len(x) > 0 if isinstance(x, list) else False
            )
        else:
            df['has_attachment'] = False
        
        # Add is_reply flag
        df['is_reply'] = df['subject'].apply(
            lambda x: str(x).lower().startswith('re:') if pd.notna(x) else False
        )
        
        # Add is_forward flag
        df['is_forward'] = df['subject'].apply(
            lambda x: str(x).lower().startswith('fw:') or str(x).lower().startswith('fwd:') if pd.notna(x) else False
        )
        
        return df
    
    def process_documents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process documents.
        
        Args:
            data: Dictionary of document data
            
        Returns:
            Processed document data
        """
        logger.info(f"Processing {len(data)} documents")
        self.stats['total_items'] += len(data)
        
        # Make a copy to avoid modifying the original
        processed_docs = {}
        
        for doc_id, doc_data in data.items():
            try:
                # Process document
                processed_doc = self._process_document(doc_id, doc_data)
                processed_docs[doc_id] = processed_doc
            except Exception as e:
                logger.warning(f"Error processing document {doc_id}: {str(e)}")
                self.stats['warnings'] += 1
        
        # Save processed data
        processed_path = self.processed_dir / 'documents.json'
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(processed_docs, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved processed documents to {processed_path}")
        
        self.stats['processed_items'] += len(processed_docs)
        return processed_docs
    
    def _process_document(self, doc_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single document.
        
        Args:
            doc_id: Document ID
            doc_data: Document data
            
        Returns:
            Processed document data
        """
        # Make a copy to avoid modifying the original
        processed_doc = doc_data.copy()
        
        # Normalize content
        if 'content' in processed_doc:
            # Get text normalization config
            text_norm_config = self.preprocess_config.get('text_normalization', {})
            
            # Save original content
            processed_doc['content_original'] = processed_doc['content']
            
            # Normalize content
            processed_doc['content'] = normalize_text(
                processed_doc['content'],
                lowercase=False,  # Don't lowercase document content
                remove_urls=text_norm_config.get('remove_urls', False),
                remove_emails=text_norm_config.get('remove_emails', False),
                remove_phone_numbers=text_norm_config.get('remove_phone_numbers', False),
                expand_contractions=False,  # Don't expand contractions in documents
                fix_unicode=text_norm_config.get('fix_unicode', True)
            )
            
            # Add content hash
            processed_doc['content_hash'] = compute_text_hash(processed_doc['content'])
            
            # Add content length
            processed_doc['content_length'] = len(processed_doc['content'])
            
            # Add word count
            processed_doc['word_count'] = len(processed_doc['content'].split())
            
            self.stats['normalized_items'] += 1
        
        return processed_doc
    
    def process_social_media(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process social media data.
        
        Args:
            data: Dictionary of social media data
            
        Returns:
            Processed social media data
        """
        logger.info(f"Processing social media data from {len(data)} platforms")
        
        processed_data = {}
        
        for platform, platform_data in data.items():
            logger.info(f"Processing {platform} data")
            
            try:
                if 'posts' in platform_data and isinstance(platform_data['posts'], pd.DataFrame):
                    # Process posts
                    posts_df = platform_data['posts'].copy()
                    self.stats['total_items'] += len(posts_df)
                    
                    # Normalize content
                    posts_df = self._normalize_text_content(posts_df, 'content')
                    
                    # Remove duplicates
                    posts_df = self._remove_duplicates(posts_df)
                    
                    # Add metadata
                    posts_df = self._add_social_media_metadata(posts_df, platform)
                    
                    # Update platform data
                    processed_platform_data = platform_data.copy()
                    processed_platform_data['posts'] = posts_df
                    processed_data[platform] = processed_platform_data
                    
                    # Save processed data
                    processed_path = self.processed_dir / f'social_media_{platform}_posts.parquet'
                    posts_df.to_parquet(processed_path, index=False)
                    logger.info(f"Saved processed {platform} posts to {processed_path}")
                    
                    self.stats['processed_items'] += len(posts_df)
                else:
                    logger.warning(f"No posts found for {platform}")
                    processed_data[platform] = platform_data
            except Exception as e:
                logger.error(f"Error processing {platform} data: {str(e)}", exc_info=True)
                self.stats['errors'] += 1
                processed_data[platform] = platform_data
        
        return processed_data
    
    def _add_social_media_metadata(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """
        Add additional metadata to social media posts.
        
        Args:
            df: DataFrame to process
            platform: Social media platform
            
        Returns:
            Processed DataFrame with additional metadata
        """
        logger.info(f"Adding {platform} metadata")
        
        # Add content length
        df['content_length'] = df['content'].apply(lambda x: len(str(x)) if pd.notna(x) else 0)
        
        # Add word count
        df['word_count'] = df['content'].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
        
        # Add day of week
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Add hour of day
        df['hour_of_day'] = df['timestamp'].dt.hour
        
        # Add has_url flag
        url_pattern = re.compile(r'https?://\S+')
        df['has_url'] = df['content'].apply(
            lambda x: bool(url_pattern.search(str(x))) if pd.notna(x) else False
        )
        
        # Add has_hashtag flag
        hashtag_pattern = re.compile(r'#\w+')
        df['has_hashtag'] = df['content_original'].apply(
            lambda x: bool(hashtag_pattern.search(str(x))) if pd.notna(x) else False
        )
        
        # Add has_mention flag
        mention_pattern = re.compile(r'@\w+')
        df['has_mention'] = df['content_original'].apply(
            lambda x: bool(mention_pattern.search(str(x))) if pd.notna(x) else False
        )
        
        # Add platform-specific metadata
        if platform == 'twitter':
            # Add is_retweet flag
            if 'retweeted_status' in df.columns:
                df['is_retweet'] = df['retweeted_status'].notna()
            elif 'tweet' in df.columns and isinstance(df['tweet'].iloc[0], dict):
                df['is_retweet'] = df['tweet'].apply(
                    lambda x: 'retweeted_status' in x if isinstance(x, dict) else False
                )
            else:
                df['is_retweet'] = False
            
            # Add is_reply flag
            if 'in_reply_to_status_id' in df.columns:
                df['is_reply'] = df['in_reply_to_status_id'].notna()
            elif 'tweet' in df.columns and isinstance(df['tweet'].iloc[0], dict):
                df['is_reply'] = df['tweet'].apply(
                    lambda x: x.get('in_reply_to_status_id') is not None if isinstance(x, dict) else False
                )
            else:
                df['is_reply'] = False
        
        elif platform == 'facebook':
            # Add post_type
            if 'type' in df.columns:
                df['post_type'] = df['type']
            else:
                df['post_type'] = 'status'
        
        return df
    
    def process_calendar(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process calendar data.
        
        Args:
            data: DataFrame of calendar events
            
        Returns:
            Processed DataFrame
        """
        # Placeholder for calendar data processing
        return data
    
    def process_location(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process location data.
        
        Args:
            data: DataFrame of location data
            
        Returns:
            Processed DataFrame
        """
        # Placeholder for location data processing
        return data
    
    def process_photos(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process photos.
        
        Args:
            data: Dictionary of photo data
            
        Returns:
            Processed photo data
        """
        # Placeholder for photo data processing
        return data


def process_all(config: Dict[str, Any], data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process all data sources.
    
    Args:
        config: Configuration dictionary
        data_sources: Dictionary of data sources
        
    Returns:
        Dictionary of processed data
    """
    preprocessor = DataPreprocessor(config)
    return preprocessor.process_all(data_sources)