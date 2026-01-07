"""
Email connector for extracting data from email accounts.
"""

import asyncio
import email
import imaplib
import re
import quopri
import base64
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from core.logging import get_logger
from core.utils import generate_id, timestamp_now, ensure_directory
from .base import DataConnectorBase

logger = get_logger(__name__)

class EmailConnector(DataConnectorBase):
    """
    Connector for extracting data from email accounts using IMAP.
    
    This connector supports:
    - Gmail, Outlook, Yahoo, and other IMAP-enabled email providers
    - Filtering by date range, sender, subject, and other criteria
    - Extracting email content, attachments, and metadata
    - Handling various email formats and encodings
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - host: IMAP server hostname
                - port: IMAP server port
                - username: Email account username
                - password: Email account password
                - use_ssl: Whether to use SSL (default: True)
                - folder: Email folder to extract from (default: "INBOX")
                - save_attachments: Whether to save attachments (default: False)
                - attachments_dir: Directory to save attachments (default: "attachments")
        """
        super().__init__(config)
        self.host = config.get("host", "")
        self.port = config.get("port", 993)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.use_ssl = config.get("use_ssl", True)
        self.folder = config.get("folder", "INBOX")
        self.save_attachments = config.get("save_attachments", False)
        self.attachments_dir = config.get("attachments_dir", "attachments")
        
        if self.save_attachments:
            ensure_directory(self.attachments_dir)
    
    async def connect(self) -> bool:
        """
        Connect to the email server using IMAP.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # IMAP is not async, so run in a thread pool
            def _connect():
                if self.use_ssl:
                    conn = imaplib.IMAP4_SSL(self.host, self.port)
                else:
                    conn = imaplib.IMAP4(self.host, self.port)
                
                conn.login(self.username, self.password)
                conn.select(self.folder)
                return conn
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(None, _connect)
            
            self.connected = True
            logger.info(f"Connected to email server: {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to email server: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the email server.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.connection:
            return True
        
        try:
            # IMAP is not async, so run in a thread pool
            def _disconnect():
                self.connection.close()
                self.connection.logout()
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _disconnect)
            
            self.connected = False
            self.connection = None
            logger.info(f"Disconnected from email server: {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from email server: {str(e)}")
            return False
    
    async def extract_data(self, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract emails from the server based on parameters.
        
        Args:
            parameters: Optional parameters for extraction:
                - since: Date string (YYYY-MM-DD) to filter emails since
                - before: Date string (YYYY-MM-DD) to filter emails before
                - sender: Filter by sender email
                - subject: Filter by subject text
                - max_emails: Maximum number of emails to extract
                - include_body: Whether to include email body (default: True)
                - include_attachments: Whether to include attachments (default: False)
        
        Returns:
            List of raw email data dictionaries
        """
        if not self.connected or not self.connection:
            connected = await self.connect()
            if not connected:
                return []
        
        parameters = parameters or {}
        
        # Build search criteria
        search_criteria = []
        
        # Date filters
        if "since" in parameters:
            since_date = datetime.strptime(parameters["since"], "%Y-%m-%d").strftime("%d-%b-%Y")
            search_criteria.append(f'SINCE "{since_date}"')
        
        if "before" in parameters:
            before_date = datetime.strptime(parameters["before"], "%Y-%m-%d").strftime("%d-%b-%Y")
            search_criteria.append(f'BEFORE "{before_date}"')
        
        # Sender filter
        if "sender" in parameters:
            search_criteria.append(f'FROM "{parameters["sender"]}"')
        
        # Subject filter
        if "subject" in parameters:
            search_criteria.append(f'SUBJECT "{parameters["subject"]}"')
        
        # Default to all emails if no criteria specified
        if not search_criteria:
            search_criteria.append("ALL")
        
        # Combine criteria
        search_string = " ".join(search_criteria)
        
        try:
            # IMAP is not async, so run in thread pool
            def _search_and_fetch():
                # Search for emails
                status, data = self.connection.search(None, search_string)
                if status != "OK":
                    logger.error(f"Failed to search emails: {status}")
                    return []
                
                # Get email IDs
                email_ids = data[0].split()
                
                # Limit number of emails if specified
                max_emails = parameters.get("max_emails")
                if max_emails and len(email_ids) > max_emails:
                    email_ids = email_ids[-max_emails:]
                
                # Fetch emails
                emails = []
                for email_id in email_ids:
                    status, data = self.connection.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {email_id}: {status}")
                        continue
                    
                    emails.append({
                        "email_id": email_id.decode("utf-8"),
                        "raw_data": data[0][1]
                    })
                
                return emails
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            raw_emails = await loop.run_in_executor(None, _search_and_fetch)
            
            logger.info(f"Extracted {len(raw_emails)} emails from {self.host}")
            return raw_emails
            
        except Exception as e:
            logger.error(f"Failed to extract emails: {str(e)}")
            return []
    
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw email data into standardized format.
        
        Args:
            raw_data: Raw email data from extraction
            
        Returns:
            List of standardized email data dictionaries
        """
        transformed_emails = []
        
        for raw_email in raw_data:
            try:
                # Parse email
                email_message = email.message_from_bytes(raw_email["raw_data"])
                
                # Extract basic metadata
                email_data = {
                    "id": raw_email["email_id"],
                    "source_id": f"email_{self.username}_{raw_email['email_id']}",
                    "type": "email",
                    "date": self._parse_date(email_message["Date"]),
                    "subject": self._decode_header(email_message["Subject"]),
                    "from": self._parse_address(email_message["From"]),
                    "to": self._parse_address(email_message["To"]),
                    "cc": self._parse_address(email_message.get("Cc", "")),
                    "has_attachments": False,
                    "attachments": [],
                    "body_text": "",
                    "body_html": "",
                    "headers": {
                        k: self._decode_header(v) for k, v in email_message.items()
                    },
                    "metadata": {
                        "message_id": email_message.get("Message-ID", ""),
                        "in_reply_to": email_message.get("In-Reply-To", ""),
                        "references": email_message.get("References", ""),
                        "connector_id": self.connector_id,
                        "extraction_time": timestamp_now()
                    }
                }
                
                # Process email parts
                attachments = []
                
                # Process email body and attachments
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))
                        
                        # Handle attachments
                        if "attachment" in content_disposition:
                            attachment = self._process_attachment(part)
                            if attachment:
                                attachments.append(attachment)
                        
                        # Handle email body
                        elif content_type == "text/plain" and not email_data["body_text"]:
                            email_data["body_text"] = self._get_part_content(part)
                        
                        elif content_type == "text/html" and not email_data["body_html"]:
                            email_data["body_html"] = self._get_part_content(part)
                
                else:
                    # Handle non-multipart email
                    content_type = email_message.get_content_type()
                    
                    if content_type == "text/plain":
                        email_data["body_text"] = self._get_part_content(email_message)
                    elif content_type == "text/html":
                        email_data["body_html"] = self._get_part_content(email_message)
                
                # Update attachment info
                email_data["has_attachments"] = len(attachments) > 0
                email_data["attachments"] = attachments
                
                transformed_emails.append(email_data)
                
            except Exception as e:
                logger.error(f"Failed to transform email: {str(e)}")
                continue
        
        return transformed_emails
    
    async def validate_config(self) -> Dict[str, Any]:
        """
        Validate the connector configuration.
        
        Returns:
            Dictionary with validation results
        """
        # First run the base validation
        base_validation = await super().validate_config()
        if not base_validation["valid"]:
            return base_validation
        
        # Email-specific validation
        required_fields = ["host", "username", "password"]
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "message": f"Missing required configuration fields: {', '.join(missing_fields)}"
            }
        
        return {
            "valid": True,
            "message": "Configuration is valid"
        }
    
    def _decode_header(self, header_value: Optional[str]) -> str:
        """
        Decode email header value.
        
        Args:
            header_value: Raw header value
            
        Returns:
            Decoded header value
        """
        if not header_value:
            return ""
        
        try:
            decoded_parts = []
            for part, encoding in decode_header(header_value):
                if isinstance(part, bytes):
                    if encoding:
                        decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
                    else:
                        decoded_parts.append(part.decode("utf-8", errors="replace"))
                else:
                    decoded_parts.append(part)
            
            return "".join(decoded_parts)
            
        except Exception as e:
            logger.warning(f"Failed to decode header: {str(e)}")
            return header_value
    
    def _parse_date(self, date_str: Optional[str]) -> str:
        """
        Parse email date to ISO format.
        
        Args:
            date_str: Email date string
            
        Returns:
            ISO formatted date string
        """
        if not date_str:
            return timestamp_now()
        
        try:
            # Try various date formats
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S",
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # If all formats fail, use current time
            logger.warning(f"Could not parse date: {date_str}")
            return timestamp_now()
            
        except Exception as e:
            logger.warning(f"Failed to parse date: {str(e)}")
            return timestamp_now()
    
    def _parse_address(self, address_str: Optional[str]) -> List[Dict[str, str]]:
        """
        Parse email address string into structured format.
        
        Args:
            address_str: Email address string (can be multiple addresses)
            
        Returns:
            List of dictionaries with name and email
        """
        if not address_str:
            return []
        
        try:
            addresses = []
            
            # Split multiple addresses
            for addr in address_str.split(","):
                addr = addr.strip()
                if not addr:
                    continue
                
                # Extract name and email
                match = re.match(r'"?([^"<]+)"?\s*<?([^>]*)>?', addr)
                
                if match:
                    name, email_addr = match.groups()
                    addresses.append({
                        "name": name.strip(),
                        "email": email_addr.strip()
                    })
                else:
                    # Just an email address
                    addresses.append({
                        "name": "",
                        "email": addr
                    })
            
            return addresses
            
        except Exception as e:
            logger.warning(f"Failed to parse address: {str(e)}")
            return [{"name": "", "email": address_str}]
    
    def _get_part_content(self, part) -> str:
        """
        Get content from email part, handling different encodings.
        
        Args:
            part: Email part
            
        Returns:
            Decoded content as string
        """
        content = ""
        
        try:
            # Get content
            payload = part.get_payload(decode=True)
            if not payload:
                return ""
            
            # Get charset
            charset = part.get_content_charset() or "utf-8"
            
            # Decode content
            try:
                content = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                # Try utf-8 if specified charset fails
                content = payload.decode("utf-8", errors="replace")
            
            return content
            
        except Exception as e:
            logger.warning(f"Failed to get part content: {str(e)}")
            return ""
    
    def _process_attachment(self, part) -> Dict[str, Any]:
        """
        Process email attachment.
        
        Args:
            part: Email part containing attachment
            
        Returns:
            Attachment metadata dictionary
        """
        try:
            # Get filename
            filename = part.get_filename()
            if not filename:
                return {}
            
            # Decode filename if needed
            filename = self._decode_header(filename)
            
            # Get content type
            content_type = part.get_content_type()
            
            # Get attachment data
            attachment_data = part.get_payload(decode=True)
            if not attachment_data:
                return {}
            
            # Calculate size
            size = len(attachment_data)
            
            # Save attachment if configured
            file_path = None
            if self.save_attachments:
                file_path = Path(self.attachments_dir) / filename
                with open(file_path, "wb") as f:
                    f.write(attachment_data)
            
            return {
                "filename": filename,
                "content_type": content_type,
                "size": size,
                "file_path": str(file_path) if file_path else None
            }
            
        except Exception as e:
            logger.warning(f"Failed to process attachment: {str(e)}")
            return {}