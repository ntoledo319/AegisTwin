"""
Cognitive-Twin Omega - Data Ingestion System

This module provides comprehensive data ingestion capabilities for Cognitive-Twin Omega,
enabling the system to import, parse, and normalize data from various sources
including text messages, emails, documents, social media, and more.
"""

import logging
import json
import csv
import re
import os
import email
import mailbox
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import hashlib

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import yaml
from tqdm import tqdm
import tiktoken
from dateutil import parser as date_parser

from cognitive_twin.core.utils import ensure_dir, normalize_text, compute_text_hash

# Initialize logger
logger = logging.getLogger(__name__)

class DataIngestManager:
    """
    Manages the ingestion of data from various sources into Cognitive-Twin Omega.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data ingest manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.raw_dir = Path(config['paths']['raw'])
        self.interim_dir = Path(config['paths']['interim'])
        
        # Ensure directories exist
        ensure_dir(self.raw_dir)
        ensure_dir(self.interim_dir)
        
        # Initialize data sources
        self.data_sources = config.get('data_sources', {})
        
        # Initialize timezone
        self.timezone = config.get('project', {}).get('timezone', 'UTC')
        
        # Initialize stats
        self.stats = {
            'total_sources': 0,
            'processed_sources': 0,
            'total_items': 0,
            'processed_items': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def load_all_sources(self) -> Dict[str, Any]:
        """
        Load all enabled data sources.
        
        Returns:
            Dictionary of loaded data by source type
        """
        logger.info("Loading all enabled data sources")
        
        results = {}
        self.stats['total_sources'] = 0
        self.stats['processed_sources'] = 0
        
        # Process each data source type
        for source_type, source_config in self.data_sources.items():
            if source_config.get('enabled', False):
                logger.info(f"Processing {source_type} data source")
                self.stats['total_sources'] += 1
                
                try:
                    result = self.load_source(source_type)
                    if result is not None:
                        results[source_type] = result
                        self.stats['processed_sources'] += 1
                except Exception as e:
                    logger.error(f"Error processing {source_type} data source: {str(e)}", exc_info=True)
                    self.stats['errors'] += 1
        
        logger.info(f"Loaded {self.stats['processed_sources']}/{self.stats['total_sources']} data sources")
        logger.info(f"Processed {self.stats['processed_items']} items with {self.stats['errors']} errors and {self.stats['warnings']} warnings")
        
        return results
    
    def load_source(self, source_type: str) -> Optional[Any]:
        """
        Load a specific data source.
        
        Args:
            source_type: Type of data source to load
            
        Returns:
            Loaded data or None if not available
        """
        if source_type not in self.data_sources:
            logger.warning(f"Unknown data source type: {source_type}")
            return None
        
        source_config = self.data_sources[source_type]
        if not source_config.get('enabled', False):
            logger.warning(f"Data source {source_type} is not enabled")
            return None
        
        logger.info(f"Loading {source_type} data")
        
        # Dispatch to appropriate loader
        if source_type == 'text_messages':
            return self._load_text_messages(source_config)
        elif source_type == 'emails':
            return self._load_emails(source_config)
        elif source_type == 'documents':
            return self._load_documents(source_config)
        elif source_type == 'social_media':
            return self._load_social_media(source_config)
        elif source_type == 'calendar':
            return self._load_calendar(source_config)
        elif source_type == 'location':
            return self._load_location(source_config)
        elif source_type == 'photos':
            return self._load_photos(source_config)
        else:
            logger.warning(f"No loader implemented for data source type: {source_type}")
            return None
    
    def _load_text_messages(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load text messages from various formats.
        
        Args:
            config: Configuration for text messages
            
        Returns:
            DataFrame of text messages
        """
        logger.info("Loading text messages")
        
        formats = config.get('formats', [])
        if not formats:
            logger.warning("No formats specified for text messages")
            return pd.DataFrame()
        
        # Find the primary format
        primary_format = None
        for fmt in formats:
            if fmt.get('is_primary', False):
                primary_format = fmt
                break
        
        # If no primary format is specified, use the first one
        if primary_format is None and formats:
            primary_format = formats[0]
            logger.info(f"No primary format specified, using {primary_format['type']}")
        
        # Load the primary format
        if primary_format:
            if primary_format['type'] == 'csv':
                return self._load_text_messages_csv(primary_format)
            elif primary_format['type'] == 'json':
                return self._load_text_messages_json(primary_format)
            elif primary_format['type'] == 'html':
                return self._load_text_messages_html(primary_format)
            else:
                logger.warning(f"Unsupported text message format: {primary_format['type']}")
                return pd.DataFrame()
        else:
            logger.warning("No formats available for text messages")
            return pd.DataFrame()
    
    def _load_text_messages_csv(self, format_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load text messages from a CSV file.
        
        Args:
            format_config: Configuration for CSV format
            
        Returns:
            DataFrame of text messages
        """
        path = format_config['path']
        mapping = format_config.get('mapping', {})
        
        logger.info(f"Loading text messages from CSV: {path}")
        
        try:
            # Read the CSV file
            df = pd.read_csv(path, encoding='utf-8-sig', low_memory=False)
            
            # Apply column mapping
            column_mapping = {
                mapping.get('timestamp', 'Message Date'): 'timestamp',
                mapping.get('sender', 'Sender Name'): 'sender',
                mapping.get('content', 'Text'): 'content',
                mapping.get('conversation', 'Chat Session'): 'conversation'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure required columns exist
            required_columns = ['timestamp', 'sender', 'content', 'conversation']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Required column '{col}' not found in CSV")
                    df[col] = None
            
            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Drop rows with missing timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Add message_id column
            df['message_id'] = df.apply(
                lambda row: compute_text_hash(f"{row['conversation']}|{row['timestamp']}|{row['sender']}|{row['content']}"),
                axis=1
            )
            
            # Add source column
            df['source'] = 'text_messages_csv'
            
            # Add is_from_subject column (placeholder, will be updated later)
            df['is_from_subject'] = False
            
            logger.info(f"Loaded {len(df)} text messages from CSV")
            self.stats['processed_items'] += len(df)
            
            # Save interim file
            interim_path = self.interim_dir / 'text_messages_csv.parquet'
            df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim text messages to {interim_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading text messages from CSV: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return pd.DataFrame()
    
    def _load_text_messages_json(self, format_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load text messages from a JSON file.
        
        Args:
            format_config: Configuration for JSON format
            
        Returns:
            DataFrame of text messages
        """
        path = format_config['path']
        
        logger.info(f"Loading text messages from JSON: {path}")
        
        try:
            # Read the JSON file
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract messages
            if isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
            elif isinstance(data, list):
                messages = data
            else:
                logger.warning("Unexpected JSON structure")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(messages)
            
            # Map columns
            column_mapping = {
                'timestamp': 'timestamp',
                'date': 'timestamp',
                'sender_name': 'sender',
                'sender': 'sender',
                'content': 'content',
                'text': 'content',
                'message': 'content',
                'conversation': 'conversation',
                'chat': 'conversation',
                'thread': 'conversation'
            }
            
            # Rename columns that exist in the DataFrame
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Ensure required columns exist
            required_columns = ['timestamp', 'sender', 'content', 'conversation']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"Required column '{col}' not found in JSON")
                    df[col] = None
            
            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Drop rows with missing timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Add message_id column
            df['message_id'] = df.apply(
                lambda row: compute_text_hash(f"{row['conversation']}|{row['timestamp']}|{row['sender']}|{row['content']}"),
                axis=1
            )
            
            # Add source column
            df['source'] = 'text_messages_json'
            
            # Add is_from_subject column if available
            if 'is_from_me' in df.columns:
                df['is_from_subject'] = df['is_from_me']
            else:
                df['is_from_subject'] = False
            
            logger.info(f"Loaded {len(df)} text messages from JSON")
            self.stats['processed_items'] += len(df)
            
            # Save interim file
            interim_path = self.interim_dir / 'text_messages_json.parquet'
            df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim text messages to {interim_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading text messages from JSON: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return pd.DataFrame()
    
    def _load_text_messages_html(self, format_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load text messages from an HTML viewer file.
        
        Args:
            format_config: Configuration for HTML format
            
        Returns:
            DataFrame of text messages
        """
        path = format_config['path']
        
        logger.info(f"Loading text messages from HTML: {path}")
        
        try:
            # Read the HTML file
            with open(path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract messages (this is a placeholder - actual implementation would depend on HTML structure)
            messages = []
            message_elements = soup.select('.message')  # Adjust selector based on actual HTML structure
            
            for msg_elem in message_elements:
                try:
                    # Extract message data (adjust based on actual HTML structure)
                    timestamp_elem = msg_elem.select_one('.timestamp')
                    sender_elem = msg_elem.select_one('.sender')
                    content_elem = msg_elem.select_one('.content')
                    conversation_elem = msg_elem.select_one('.conversation')
                    
                    timestamp = timestamp_elem.text.strip() if timestamp_elem else None
                    sender = sender_elem.text.strip() if sender_elem else None
                    content = content_elem.text.strip() if content_elem else None
                    conversation = conversation_elem.text.strip() if conversation_elem else None
                    
                    if timestamp and sender and content:
                        messages.append({
                            'timestamp': timestamp,
                            'sender': sender,
                            'content': content,
                            'conversation': conversation
                        })
                except Exception as e:
                    logger.warning(f"Error parsing message element: {str(e)}")
                    self.stats['warnings'] += 1
            
            # Convert to DataFrame
            df = pd.DataFrame(messages)
            
            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Drop rows with missing timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Add message_id column
            df['message_id'] = df.apply(
                lambda row: compute_text_hash(f"{row['conversation']}|{row['timestamp']}|{row['sender']}|{row['content']}"),
                axis=1
            )
            
            # Add source column
            df['source'] = 'text_messages_html'
            
            # Add is_from_subject column (placeholder, will be updated later)
            df['is_from_subject'] = False
            
            logger.info(f"Loaded {len(df)} text messages from HTML")
            self.stats['processed_items'] += len(df)
            
            # Save interim file
            interim_path = self.interim_dir / 'text_messages_html.parquet'
            df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim text messages to {interim_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading text messages from HTML: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return pd.DataFrame()
    
    def _load_emails(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load emails from various formats.
        
        Args:
            config: Configuration for emails
            
        Returns:
            DataFrame of emails
        """
        logger.info("Loading emails")
        
        formats = config.get('formats', [])
        if not formats:
            logger.warning("No formats specified for emails")
            return pd.DataFrame()
        
        all_emails = []
        
        for fmt in formats:
            if fmt['type'] == 'mbox':
                emails = self._load_emails_mbox(fmt)
                if not emails.empty:
                    all_emails.append(emails)
            elif fmt['type'] == 'eml_directory':
                emails = self._load_emails_eml_directory(fmt)
                if not emails.empty:
                    all_emails.append(emails)
            else:
                logger.warning(f"Unsupported email format: {fmt['type']}")
        
        if all_emails:
            # Combine all email DataFrames
            combined_df = pd.concat(all_emails, ignore_index=True)
            
            # Save interim file
            interim_path = self.interim_dir / 'emails.parquet'
            combined_df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim emails to {interim_path}")
            
            return combined_df
        else:
            logger.warning("No emails loaded")
            return pd.DataFrame()
    
    def _load_emails_mbox(self, format_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load emails from an mbox file.
        
        Args:
            format_config: Configuration for mbox format
            
        Returns:
            DataFrame of emails
        """
        path = format_config['path']
        
        logger.info(f"Loading emails from mbox: {path}")
        
        try:
            # Open the mbox file
            mbox = mailbox.mbox(path)
            
            emails = []
            for message in tqdm(mbox, desc="Processing emails"):
                try:
                    # Extract email data
                    email_data = self._parse_email_message(message)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Error parsing email: {str(e)}")
                    self.stats['warnings'] += 1
            
            # Convert to DataFrame
            df = pd.DataFrame(emails)
            
            # Add source column
            df['source'] = 'emails_mbox'
            
            logger.info(f"Loaded {len(df)} emails from mbox")
            self.stats['processed_items'] += len(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading emails from mbox: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return pd.DataFrame()
    
    def _load_emails_eml_directory(self, format_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load emails from a directory of .eml files.
        
        Args:
            format_config: Configuration for eml directory format
            
        Returns:
            DataFrame of emails
        """
        path = format_config['path']
        
        logger.info(f"Loading emails from eml directory: {path}")
        
        try:
            # Get all .eml files in the directory
            eml_files = list(Path(path).glob('**/*.eml'))
            
            emails = []
            for eml_file in tqdm(eml_files, desc="Processing eml files"):
                try:
                    # Read the .eml file
                    with open(eml_file, 'rb') as f:
                        message = email.message_from_binary_file(f)
                    
                    # Extract email data
                    email_data = self._parse_email_message(message)
                    if email_data:
                        email_data['file_path'] = str(eml_file)
                        emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Error parsing email file {eml_file}: {str(e)}")
                    self.stats['warnings'] += 1
            
            # Convert to DataFrame
            df = pd.DataFrame(emails)
            
            # Add source column
            df['source'] = 'emails_eml'
            
            logger.info(f"Loaded {len(df)} emails from eml directory")
            self.stats['processed_items'] += len(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading emails from eml directory: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return pd.DataFrame()
    
    def _parse_email_message(self, message: email.message.Message) -> Dict[str, Any]:
        """
        Parse an email message.
        
        Args:
            message: Email message object
            
        Returns:
            Dictionary with email data
        """
        # Extract headers
        from_addr = message.get('From', '')
        to_addr = message.get('To', '')
        cc_addr = message.get('Cc', '')
        subject = message.get('Subject', '')
        date_str = message.get('Date', '')
        message_id = message.get('Message-ID', '')
        
        # Parse date
        try:
            timestamp = date_parser.parse(date_str)
        except:
            timestamp = None
        
        # Extract body
        body_text = ""
        body_html = ""
        
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                
                try:
                    if content_type == 'text/plain':
                        body_text += payload.decode('utf-8', errors='replace')
                    elif content_type == 'text/html':
                        body_html += payload.decode('utf-8', errors='replace')
                except:
                    pass
        else:
            # Not multipart - get the payload directly
            payload = message.get_payload(decode=True)
            if payload:
                try:
                    body_text = payload.decode('utf-8', errors='replace')
                except:
                    pass
        
        # If we have HTML but no text, extract text from HTML
        if not body_text and body_html:
            try:
                soup = BeautifulSoup(body_html, 'html.parser')
                body_text = soup.get_text(separator=' ', strip=True)
            except:
                pass
        
        # Generate a unique ID if none exists
        if not message_id:
            message_id = compute_text_hash(f"{from_addr}|{to_addr}|{subject}|{date_str}")
        
        # Determine if the email is from the subject
        # This is a placeholder - in a real implementation, you would
        # compare with known email addresses of the subject
        is_from_subject = False
        
        return {
            'message_id': message_id,
            'timestamp': timestamp,
            'sender': from_addr,
            'recipient': to_addr,
            'cc': cc_addr,
            'subject': subject,
            'body': body_text,
            'body_html': body_html,
            'is_from_subject': is_from_subject
        }
    
    def _load_documents(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load documents from various formats.
        
        Args:
            config: Configuration for documents
            
        Returns:
            Dictionary of documents
        """
        logger.info("Loading documents")
        
        formats = config.get('formats', [])
        if not formats:
            logger.warning("No formats specified for documents")
            return {}
        
        all_documents = {}
        
        for fmt in formats:
            if fmt['type'] == 'directory':
                documents = self._load_documents_directory(fmt)
                if documents:
                    all_documents.update(documents)
            else:
                logger.warning(f"Unsupported document format: {fmt['type']}")
        
        if all_documents:
            # Save interim file
            interim_path = self.interim_dir / 'documents.json'
            with open(interim_path, 'w', encoding='utf-8') as f:
                json.dump(all_documents, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved interim documents to {interim_path}")
            
            return all_documents
        else:
            logger.warning("No documents loaded")
            return {}
    
    def _load_documents_directory(self, format_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load documents from a directory.
        
        Args:
            format_config: Configuration for directory format
            
        Returns:
            Dictionary of documents
        """
        path = format_config['path']
        extensions = format_config.get('extensions', ['.pdf', '.docx', '.txt', '.md'])
        
        logger.info(f"Loading documents from directory: {path}")
        
        try:
            # Get all document files in the directory
            doc_files = []
            for ext in extensions:
                doc_files.extend(list(Path(path).glob(f'**/*{ext}')))
            
            documents = {}
            for doc_file in tqdm(doc_files, desc="Processing documents"):
                try:
                    # Extract document data
                    doc_data = self._parse_document(doc_file)
                    if doc_data:
                        doc_id = compute_text_hash(str(doc_file))
                        documents[doc_id] = doc_data
                except Exception as e:
                    logger.warning(f"Error parsing document {doc_file}: {str(e)}")
                    self.stats['warnings'] += 1
            
            logger.info(f"Loaded {len(documents)} documents from directory")
            self.stats['processed_items'] += len(documents)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error loading documents from directory: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return {}
    
    def _parse_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document data
        """
        # Get file metadata
        file_name = file_path.name
        file_ext = file_path.suffix.lower()
        file_size = file_path.stat().st_size
        modified_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # Extract content based on file type
        content = ""
        
        if file_ext == '.txt' or file_ext == '.md':
            # Plain text or Markdown
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with another encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    logger.warning(f"Could not read text file: {file_path}")
        
        elif file_ext == '.pdf':
            # PDF - placeholder for actual PDF extraction
            # In a real implementation, you would use a library like PyMuPDF or pdfplumber
            content = f"[PDF content would be extracted from {file_name}]"
        
        elif file_ext == '.docx':
            # DOCX - placeholder for actual DOCX extraction
            # In a real implementation, you would use a library like python-docx
            content = f"[DOCX content would be extracted from {file_name}]"
        
        # Generate a title if none exists
        title = file_name
        
        # Extract creation date if available
        creation_date = modified_time
        
        return {
            'file_path': str(file_path),
            'file_name': file_name,
            'file_type': file_ext,
            'file_size': file_size,
            'title': title,
            'content': content,
            'creation_date': creation_date.isoformat(),
            'modified_date': modified_time.isoformat()
        }
    
    def _load_social_media(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load social media data from various platforms.
        
        Args:
            config: Configuration for social media
            
        Returns:
            Dictionary of social media data by platform
        """
        logger.info("Loading social media data")
        
        platforms = config.get('platforms', {})
        if not platforms:
            logger.warning("No platforms specified for social media")
            return {}
        
        all_platforms = {}
        
        for platform_name, platform_config in platforms.items():
            if platform_name == 'twitter':
                platform_data = self._load_twitter_data(platform_config)
                if platform_data:
                    all_platforms['twitter'] = platform_data
            elif platform_name == 'facebook':
                platform_data = self._load_facebook_data(platform_config)
                if platform_data:
                    all_platforms['facebook'] = platform_data
            elif platform_name == 'instagram':
                platform_data = self._load_instagram_data(platform_config)
                if platform_data:
                    all_platforms['instagram'] = platform_data
            elif platform_name == 'linkedin':
                platform_data = self._load_linkedin_data(platform_config)
                if platform_data:
                    all_platforms['linkedin'] = platform_data
            else:
                logger.warning(f"Unsupported social media platform: {platform_name}")
        
        if all_platforms:
            # Save interim file
            interim_path = self.interim_dir / 'social_media.json'
            with open(interim_path, 'w', encoding='utf-8') as f:
                json.dump(all_platforms, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved interim social media data to {interim_path}")
            
            return all_platforms
        else:
            logger.warning("No social media data loaded")
            return {}
    
    def _load_twitter_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load Twitter data from an archive.
        
        Args:
            config: Configuration for Twitter data
            
        Returns:
            Dictionary of Twitter data
        """
        path = config.get('path')
        if not path:
            logger.warning("No path specified for Twitter data")
            return {}
        
        logger.info(f"Loading Twitter data from: {path}")
        
        try:
            # Check for tweets.js file
            tweets_file = Path(path) / 'data' / 'tweets.js'
            if not tweets_file.exists():
                tweets_file = Path(path) / 'tweet.js'
            
            if not tweets_file.exists():
                logger.warning(f"No tweets file found at {tweets_file}")
                return {}
            
            # Read the tweets file
            with open(tweets_file, 'r', encoding='utf-8') as f:
                tweets_js = f.read()
            
            # Extract JSON from JavaScript
            json_str = re.search(r'= (\[.*\])', tweets_js, re.DOTALL)
            if not json_str:
                logger.warning("Could not extract JSON from tweets.js")
                return {}
            
            tweets_data = json.loads(json_str.group(1))
            
            # Convert to DataFrame
            tweets_df = pd.DataFrame(tweets_data)
            
            # Process tweets
            if 'tweet' in tweets_df.columns:
                # Newer format
                tweets_df['content'] = tweets_df['tweet'].apply(lambda x: x.get('full_text', ''))
                tweets_df['timestamp'] = pd.to_datetime(tweets_df['tweet'].apply(lambda x: x.get('created_at', '')))
            else:
                # Older format
                tweets_df['content'] = tweets_df['text']
                tweets_df['timestamp'] = pd.to_datetime(tweets_df['created_at'])
            
            # Add is_from_subject column (all tweets are from the subject)
            tweets_df['is_from_subject'] = True
            
            # Add message_id column
            tweets_df['message_id'] = tweets_df.apply(
                lambda row: compute_text_hash(f"twitter|{row['timestamp']}|{row['content']}"),
                axis=1
            )
            
            # Add source column
            tweets_df['source'] = 'twitter'
            
            logger.info(f"Loaded {len(tweets_df)} tweets")
            self.stats['processed_items'] += len(tweets_df)
            
            # Save interim file
            interim_path = self.interim_dir / 'twitter_tweets.parquet'
            tweets_df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim Twitter data to {interim_path}")
            
            return {
                'posts': tweets_df,
                'metadata': {
                    'count': len(tweets_df),
                    'date_range': [
                        tweets_df['timestamp'].min().isoformat() if not tweets_df.empty else None,
                        tweets_df['timestamp'].max().isoformat() if not tweets_df.empty else None
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading Twitter data: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return {}
    
    def _load_facebook_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load Facebook data from an archive.
        
        Args:
            config: Configuration for Facebook data
            
        Returns:
            Dictionary of Facebook data
        """
        path = config.get('path')
        if not path:
            logger.warning("No path specified for Facebook data")
            return {}
        
        logger.info(f"Loading Facebook data from: {path}")
        
        try:
            # Check for posts directory
            posts_dir = Path(path) / 'posts'
            if not posts_dir.exists():
                logger.warning(f"No posts directory found at {posts_dir}")
                return {}
            
            # Find posts files
            posts_files = list(posts_dir.glob('*.json'))
            if not posts_files:
                logger.warning(f"No posts files found in {posts_dir}")
                return {}
            
            all_posts = []
            
            for posts_file in posts_files:
                try:
                    # Read the posts file
                    with open(posts_file, 'r', encoding='utf-8') as f:
                        posts_data = json.load(f)
                    
                    # Extract posts
                    if isinstance(posts_data, dict) and 'status_updates' in posts_data:
                        posts = posts_data['status_updates']
                        all_posts.extend(posts)
                except Exception as e:
                    logger.warning(f"Error processing posts file {posts_file}: {str(e)}")
                    self.stats['warnings'] += 1
            
            # Convert to DataFrame
            posts_df = pd.DataFrame(all_posts)
            
            # Process posts
            if 'data' in posts_df.columns:
                # Extract content and timestamp
                posts_df['content'] = posts_df['data'].apply(lambda x: x.get('post', ''))
                posts_df['timestamp'] = pd.to_datetime(posts_df['timestamp'])
            
            # Add is_from_subject column (all posts are from the subject)
            posts_df['is_from_subject'] = True
            
            # Add message_id column
            posts_df['message_id'] = posts_df.apply(
                lambda row: compute_text_hash(f"facebook|{row['timestamp']}|{row['content']}"),
                axis=1
            )
            
            # Add source column
            posts_df['source'] = 'facebook'
            
            logger.info(f"Loaded {len(posts_df)} Facebook posts")
            self.stats['processed_items'] += len(posts_df)
            
            # Save interim file
            interim_path = self.interim_dir / 'facebook_posts.parquet'
            posts_df.to_parquet(interim_path, index=False)
            logger.info(f"Saved interim Facebook data to {interim_path}")
            
            return {
                'posts': posts_df,
                'metadata': {
                    'count': len(posts_df),
                    'date_range': [
                        posts_df['timestamp'].min().isoformat() if not posts_df.empty else None,
                        posts_df['timestamp'].max().isoformat() if not posts_df.empty else None
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading Facebook data: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
            return {}
    
    def _load_instagram_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load Instagram data from an archive.
        
        Args:
            config: Configuration for Instagram data
            
        Returns:
            Dictionary of Instagram data
        """
        # Placeholder for Instagram data loading
        # Similar implementation to Twitter and Facebook
        return {}
    
    def _load_linkedin_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load LinkedIn data from an archive.
        
        Args:
            config: Configuration for LinkedIn data
            
        Returns:
            Dictionary of LinkedIn data
        """
        # Placeholder for LinkedIn data loading
        # Similar implementation to Twitter and Facebook
        return {}
    
    def _load_calendar(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load calendar data from various formats.
        
        Args:
            config: Configuration for calendar data
            
        Returns:
            DataFrame of calendar events
        """
        # Placeholder for calendar data loading
        return pd.DataFrame()
    
    def _load_location(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Load location data from various formats.
        
        Args:
            config: Configuration for location data
            
        Returns:
            DataFrame of location data
        """
        # Placeholder for location data loading
        return pd.DataFrame()
    
    def _load_photos(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load photos from a directory.
        
        Args:
            config: Configuration for photos
            
        Returns:
            Dictionary of photo data
        """
        # Placeholder for photo data loading
        return {}


def load_all_sources(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load all enabled data sources.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of loaded data by source type
    """
    ingest_manager = DataIngestManager(config)
    return ingest_manager.load_all_sources()

def load_source(config: Dict[str, Any], source_type: str) -> Optional[Any]:
    """
    Load a specific data source.
    
    Args:
        config: Configuration dictionary
        source_type: Type of data source to load
        
    Returns:
        Loaded data or None if not available
    """
    ingest_manager = DataIngestManager(config)
    return ingest_manager.load_source(source_type)