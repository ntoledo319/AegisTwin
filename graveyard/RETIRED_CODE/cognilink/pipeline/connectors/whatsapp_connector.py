"""
WhatsApp Connector for CogniLink

This module provides functionality to import data from WhatsApp exports,
including chat messages, media, and contact information.
"""

import os
import json
import logging
import zipfile
import re
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import csv

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class WhatsAppConnector(BaseConnector):
    """
    Connector for importing WhatsApp data.
    
    This class handles extraction of chat messages, media files, and contact information
    from WhatsApp exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the WhatsApp connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "whatsapp"
        self.user_info = {}
        
        # Regular expressions for parsing WhatsApp chat exports
        self.message_pattern = re.compile(
            r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]?\s+-\s+([^:]+):\s+(.+)$'
        )
        self.system_message_pattern = re.compile(
            r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]?\s+-\s+(.+)$'
        )
        self.date_formats = [
            '%m/%d/%y, %I:%M %p',  # 01/31/20, 8:30 PM
            '%d/%m/%y, %I:%M %p',  # 31/01/20, 8:30 PM
            '%m/%d/%Y, %I:%M %p',  # 01/31/2020, 8:30 PM
            '%d/%m/%Y, %I:%M %p',  # 31/01/2020, 8:30 PM
            '%m/%d/%y, %H:%M',     # 01/31/20, 20:30
            '%d/%m/%y, %H:%M',     # 31/01/20, 20:30
            '%m/%d/%Y, %H:%M',     # 01/31/2020, 20:30
            '%d/%m/%Y, %H:%M',     # 31/01/2020, 20:30
            '%m/%d/%y, %I:%M:%S %p',  # 01/31/20, 8:30:00 PM
            '%d/%m/%y, %I:%M:%S %p',  # 31/01/20, 8:30:00 PM
            '%m/%d/%Y, %I:%M:%S %p',  # 01/31/2020, 8:30:00 PM
            '%d/%m/%Y, %I:%M:%S %p',  # 31/01/2020, 8:30:00 PM
            '%m/%d/%y, %H:%M:%S',     # 01/31/20, 20:30:00
            '%d/%m/%y, %H:%M:%S',     # 31/01/20, 20:30:00
            '%m/%d/%Y, %H:%M:%S',     # 01/31/2020, 20:30:00
            '%d/%m/%Y, %H:%M:%S',     # 31/01/2020, 20:30:00
        ]
    
    def extract_from_file(self, file_path: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a WhatsApp export file.
        
        Args:
            file_path: Path to the WhatsApp export file (ZIP, TXT, or directory)
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_whatsapp_directory(temp_dir)
        
        # Handle TXT file (direct chat export)
        elif file_path.endswith('.txt'):
            yield from self._extract_chat_from_txt(file_path)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_whatsapp_directory(file_path)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_whatsapp_directory(self, directory_path: str) -> Iterator[Dict[str, Any]]:
        """
        Process a WhatsApp export directory.
        
        Args:
            directory_path: Path to the WhatsApp export directory
                
        Yields:
            Dictionaries containing normalized data
        """
        # Look for chat export files
        chat_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.txt') and 'WhatsApp Chat with' in file:
                    chat_files.append(os.path.join(root, file))
        
        if chat_files:
            logger.info(f"Found {len(chat_files)} WhatsApp chat export files")
            for chat_file in chat_files:
                yield from self._extract_chat_from_txt(chat_file)
        else:
            logger.warning("No WhatsApp chat export files found in directory")
        
        # Look for contacts file
        contacts_file = os.path.join(directory_path, 'contacts.vcf')
        if os.path.exists(contacts_file):
            yield from self._extract_contacts_from_vcf(contacts_file)
        else:
            # Try alternate location
            contacts_file = self._find_file(directory_path, 'contacts.vcf')
            if contacts_file:
                yield from self._extract_contacts_from_vcf(contacts_file)
            else:
                logger.warning("No WhatsApp contacts file found in directory")
    
    def _find_file(self, directory_path: str, filename: str) -> Optional[str]:
        """
        Find a file in a directory tree.
        
        Args:
            directory_path: Path to the directory to search
            filename: Name of the file to find
                
        Returns:
            Path to the file if found, None otherwise
        """
        for root, _, files in os.walk(directory_path):
            if filename in files:
                return os.path.join(root, filename)
        return None
    
    def _parse_timestamp(self, date_str: str) -> Optional[datetime]:
        """
        Parse a timestamp from a WhatsApp chat export.
        
        Args:
            date_str: Date string from WhatsApp chat export
                
        Returns:
            Parsed datetime object or None if parsing fails
        """
        for date_format in self.date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _extract_chat_from_txt(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract chat messages from a WhatsApp chat export TXT file.
        
        Args:
            file_path: Path to the WhatsApp chat export TXT file
                
        Yields:
            Dictionaries containing normalized message data
        """
        try:
            # Extract chat name from filename
            chat_name = os.path.basename(file_path)
            chat_name = chat_name.replace('WhatsApp Chat with ', '').replace('.txt', '')
            
            # Determine if this is a group chat
            is_group = False
            if ' - ' in chat_name or ' group' in chat_name.lower():
                is_group = True
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            logger.info(f"Processing WhatsApp chat with {chat_name} ({len(lines)} lines)")
            
            # Process each line
            current_message = None
            message_id = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to match as a regular message
                match = self.message_pattern.match(line)
                if match:
                    # If we have a current message, yield it before starting a new one
                    if current_message:
                        if self._apply_filters(current_message):
                            self.item_count += 1
                            yield current_message
                    
                    # Extract message components
                    date_str, sender, content = match.groups()
                    timestamp = self._parse_timestamp(date_str)
                    
                    # Create new message
                    message_id += 1
                    current_message = {
                        'id': f"whatsapp_msg_{os.path.basename(file_path)}_{message_id}",
                        'chat_name': chat_name,
                        'content': content,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender': sender.strip(),
                        'is_group': is_group,
                        'group_name': chat_name if is_group else None,
                        'has_media': '<Media omitted>' in content,
                        'platform': 'whatsapp',
                        'type': 'message',
                        'source': 'whatsapp_export'
                    }
                    continue
                
                # Try to match as a system message
                match = self.system_message_pattern.match(line)
                if match:
                    # If we have a current message, yield it before starting a new one
                    if current_message:
                        if self._apply_filters(current_message):
                            self.item_count += 1
                            yield current_message
                    
                    # Extract message components
                    date_str, content = match.groups()
                    timestamp = self._parse_timestamp(date_str)
                    
                    # Create new system message
                    message_id += 1
                    current_message = {
                        'id': f"whatsapp_system_{os.path.basename(file_path)}_{message_id}",
                        'chat_name': chat_name,
                        'content': content,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'sender': 'System',
                        'is_group': is_group,
                        'group_name': chat_name if is_group else None,
                        'is_system_message': True,
                        'platform': 'whatsapp',
                        'type': 'system_message',
                        'source': 'whatsapp_export'
                    }
                    continue
                
                # If no match, this line is a continuation of the previous message
                if current_message:
                    current_message['content'] += f"\n{line}"
            
            # Don't forget to yield the last message
            if current_message:
                if self._apply_filters(current_message):
                    self.item_count += 1
                    yield current_message
        
        except Exception as e:
            logger.error(f"Error extracting chat from WhatsApp export: {str(e)}")
    
    def _extract_contacts_from_vcf(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from a WhatsApp contacts VCF file.
        
        Args:
            file_path: Path to the WhatsApp contacts VCF file
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                vcf_content = f.read()
            
            # Split the VCF file into individual contacts
            contacts = vcf_content.split('BEGIN:VCARD')
            contacts = [c for c in contacts if c.strip()]
            
            logger.info(f"Found {len(contacts)} contacts in WhatsApp export")
            
            for i, contact_data in enumerate(contacts):
                try:
                    # Extract name
                    name_match = re.search(r'FN:(.*?)(?:\r?\n)', contact_data)
                    name = name_match.group(1) if name_match else f"Unknown Contact {i+1}"
                    
                    # Extract phone number
                    phone_match = re.search(r'TEL;[^:]*:(.*?)(?:\r?\n)', contact_data)
                    phone = phone_match.group(1) if phone_match else ""
                    
                    # Extract WhatsApp ID (usually the phone number)
                    whatsapp_id_match = re.search(r'IMPP;[^:]*:whatsapp:([^@\r\n]+)', contact_data)
                    whatsapp_id = whatsapp_id_match.group(1) if whatsapp_id_match else phone
                    
                    # Create normalized contact data
                    contact = {
                        'id': f"whatsapp_contact_{whatsapp_id or i}",
                        'name': name,
                        'phone': phone,
                        'whatsapp_id': whatsapp_id,
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'whatsapp',
                        'type': 'contact',
                        'source': 'whatsapp_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact):
                        self.item_count += 1
                        yield contact
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing WhatsApp contact: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting contacts from WhatsApp export: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for WhatsApp data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item