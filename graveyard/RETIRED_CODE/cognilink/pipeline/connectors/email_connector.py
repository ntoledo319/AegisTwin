"""
Email Connector for CogniLink

This module provides functionality to import email data from various sources
including MBOX files, EML files, and email service APIs.
"""

import os
import mailbox
import email
from email.utils import parseaddr, parsedate_to_datetime
import logging
from typing import List, Dict, Any, Optional, Iterator, Tuple
from datetime import datetime
import json
import re

from cognilink.core.utils import normalize_email, generate_message_id, parse_datetime

logger = logging.getLogger(__name__)

class EmailConnector:
    """
    Connector for importing email data from various sources.
    
    This class handles the extraction and normalization of email data
    from different formats and sources.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the email connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        self.config = config or {}
        self.email_count = 0
        self.error_count = 0
    
    def extract_from_mbox(self, mbox_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract emails from an MBOX file.
        
        Args:
            mbox_path: Path to the MBOX file
            
        Yields:
            Dictionaries containing normalized email data
        """
        if not os.path.exists(mbox_path):
            logger.error(f"MBOX file not found: {mbox_path}")
            return
        
        try:
            mbox = mailbox.mbox(mbox_path)
            logger.info(f"Processing MBOX file with {len(mbox)} messages")
            
            for message in mbox:
                try:
                    email_data = self._parse_email_message(message)
                    if email_data:
                        self.email_count += 1
                        yield email_data
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing email: {str(e)}")
                    
                    # Log progress periodically
                    if (self.email_count + self.error_count) % 1000 == 0:
                        logger.info(f"Processed {self.email_count} emails ({self.error_count} errors)")
            
            logger.info(f"Completed MBOX processing: {self.email_count} emails extracted, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Failed to process MBOX file {mbox_path}: {str(e)}")
    
    def extract_from_eml_directory(self, directory_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract emails from a directory of EML files.
        
        Args:
            directory_path: Path to directory containing EML files
            
        Yields:
            Dictionaries containing normalized email data
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return
        
        eml_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.eml')]
        logger.info(f"Found {len(eml_files)} EML files in {directory_path}")
        
        for filename in eml_files:
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'rb') as f:
                    msg = email.message_from_binary_file(f)
                    email_data = self._parse_email_message(msg)
                    if email_data:
                        self.email_count += 1
                        yield email_data
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing EML file {filename}: {str(e)}")
        
        logger.info(f"Completed EML processing: {self.email_count} emails extracted, {self.error_count} errors")
    
    def extract_from_json(self, json_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract emails from a JSON file containing email data.
        
        Args:
            json_path: Path to the JSON file
            
        Yields:
            Dictionaries containing normalized email data
        """
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            emails = []
            if isinstance(data, list):
                emails = data
            elif isinstance(data, dict) and 'emails' in data:
                emails = data['emails']
            elif isinstance(data, dict) and 'messages' in data:
                emails = data['messages']
            else:
                logger.error(f"Unrecognized JSON format in {json_path}")
                return
            
            logger.info(f"Processing {len(emails)} emails from JSON file")
            
            for email_data in emails:
                try:
                    normalized_data = self._normalize_json_email(email_data)
                    if normalized_data:
                        self.email_count += 1
                        yield normalized_data
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing email from JSON: {str(e)}")
            
            logger.info(f"Completed JSON processing: {self.email_count} emails extracted, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Failed to process JSON file {json_path}: {str(e)}")
    
    def _parse_email_message(self, msg) -> Dict[str, Any]:
        """
        Parse an email.message.Message object into a normalized dictionary.
        
        Args:
            msg: Email message object
            
        Returns:
            Dictionary containing normalized email data
        """
        # Extract headers
        headers = {}
        for key in msg.keys():
            headers[key.lower()] = msg[key]
        
        # Get basic metadata
        subject = msg.get('subject', '')
        from_header = msg.get('from', '')
        to_header = msg.get('to', '')
        cc_header = msg.get('cc', '')
        date_header = msg.get('date', '')
        
        # Parse sender
        sender_name, sender_email = parseaddr(from_header)
        sender_email = normalize_email(sender_email)
        
        # Parse recipients
        to_recipients = self._parse_address_list(to_header)
        cc_recipients = self._parse_address_list(cc_header)
        all_recipients = to_recipients + cc_recipients
        
        # Parse date
        try:
            date = parsedate_to_datetime(date_header)
        except (TypeError, ValueError):
            date = parse_datetime(date_header) if date_header else None
        
        # Extract content
        content = self._extract_email_content(msg)
        
        # Create email data dictionary
        email_data = {
            'sender': sender_email,
            'sender_name': sender_name,
            'recipients': all_recipients,
            'to': to_recipients,
            'cc': cc_recipients,
            'subject': subject,
            'content': content,
            'timestamp': date.isoformat() if date else None,
            'headers': headers
        }
        
        # Generate a unique ID
        email_data['id'] = generate_message_id(email_data)
        
        return email_data
    
    def _extract_email_content(self, msg) -> str:
        """
        Extract the text content from an email message.
        
        Args:
            msg: Email message object
            
        Returns:
            Extracted text content
        """
        content = ""
        
        # Check if this is a multipart message
        if msg.is_multipart():
            # Iterate through parts and extract text content
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get text content
                if content_type == "text/plain":
                    try:
                        part_content = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            part_content = part_content.decode(charset, errors='replace')
                        except (LookupError, UnicodeDecodeError):
                            part_content = part_content.decode('utf-8', errors='replace')
                        
                        content += part_content + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting plain text content: {str(e)}")
                
                # If no plain text, try HTML
                elif content_type == "text/html" and not content:
                    try:
                        part_content = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            part_content = part_content.decode(charset, errors='replace')
                        except (LookupError, UnicodeDecodeError):
                            part_content = part_content.decode('utf-8', errors='replace')
                        
                        # Simple HTML to text conversion
                        part_content = re.sub(r'<[^>]+>', ' ', part_content)
                        part_content = re.sub(r'\s+', ' ', part_content)
                        
                        content += part_content + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting HTML content: {str(e)}")
        else:
            # Not multipart - get content directly
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        content = payload.decode(charset, errors='replace')
                    except (LookupError, UnicodeDecodeError):
                        content = payload.decode('utf-8', errors='replace')
                    
                    # If HTML, convert to text
                    if msg.get_content_type() == "text/html":
                        content = re.sub(r'<[^>]+>', ' ', content)
                        content = re.sub(r'\s+', ' ', content)
            except Exception as e:
                logger.warning(f"Error extracting message content: {str(e)}")
        
        return content.strip()
    
    def _parse_address_list(self, address_header: str) -> List[str]:
        """
        Parse a comma-separated list of email addresses.
        
        Args:
            address_header: Header containing email addresses
            
        Returns:
            List of normalized email addresses
        """
        if not address_header:
            return []
        
        addresses = []
        
        # Split by commas and process each address
        for addr in address_header.split(','):
            _, email_addr = parseaddr(addr.strip())
            if email_addr:
                normalized = normalize_email(email_addr)
                if normalized:
                    addresses.append(normalized)
        
        return addresses
    
    def _normalize_json_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize email data from a JSON source.
        
        Args:
            email_data: Raw email data from JSON
            
        Returns:
            Normalized email data dictionary
        """
        normalized = {}
        
        # Map common field names
        field_mappings = {
            'from': ['from', 'sender', 'from_email', 'sender_email'],
            'to': ['to', 'recipients', 'to_recipients'],
            'cc': ['cc', 'cc_recipients'],
            'subject': ['subject', 'title', 'email_subject'],
            'body': ['body', 'content', 'text', 'message', 'email_body'],
            'date': ['date', 'timestamp', 'time', 'sent_at', 'sent_date']
        }
        
        # Extract sender
        sender = None
        for field in field_mappings['from']:
            if field in email_data:
                sender = email_data[field]
                break
        
        if isinstance(sender, dict) and 'email' in sender:
            sender = sender['email']
        
        normalized['sender'] = normalize_email(sender) if sender else ''
        
        # Extract recipients
        to_recipients = []
        for field in field_mappings['to']:
            if field in email_data:
                recipients = email_data[field]
                if recipients:
                    if isinstance(recipients, str):
                        to_recipients = self._parse_address_list(recipients)
                    elif isinstance(recipients, list):
                        for r in recipients:
                            if isinstance(r, str):
                                to_recipients.append(normalize_email(r))
                            elif isinstance(r, dict) and 'email' in r:
                                to_recipients.append(normalize_email(r['email']))
                    break
        
        normalized['to'] = to_recipients
        
        # Extract CC recipients
        cc_recipients = []
        for field in field_mappings['cc']:
            if field in email_data:
                recipients = email_data[field]
                if recipients:
                    if isinstance(recipients, str):
                        cc_recipients = self._parse_address_list(recipients)
                    elif isinstance(recipients, list):
                        for r in recipients:
                            if isinstance(r, str):
                                cc_recipients.append(normalize_email(r))
                            elif isinstance(r, dict) and 'email' in r:
                                cc_recipients.append(normalize_email(r['email']))
                    break
        
        normalized['cc'] = cc_recipients
        normalized['recipients'] = to_recipients + cc_recipients
        
        # Extract subject
        subject = None
        for field in field_mappings['subject']:
            if field in email_data:
                subject = email_data[field]
                break
        
        normalized['subject'] = subject or ''
        
        # Extract content
        content = None
        for field in field_mappings['body']:
            if field in email_data:
                content = email_data[field]
                break
        
        normalized['content'] = content or ''
        
        # Extract date
        date_str = None
        for field in field_mappings['date']:
            if field in email_data:
                date_str = email_data[field]
                break
        
        if date_str:
            if isinstance(date_str, (int, float)):
                # Assume Unix timestamp
                date = datetime.fromtimestamp(date_str)
                normalized['timestamp'] = date.isoformat()
            else:
                date = parse_datetime(str(date_str))
                normalized['timestamp'] = date.isoformat() if date else None
        else:
            normalized['timestamp'] = None
        
        # Generate ID
        normalized['id'] = email_data.get('id') or generate_message_id(normalized)
        
        # Include original headers if available
        if 'headers' in email_data:
            normalized['headers'] = email_data['headers']
        
        return normalized