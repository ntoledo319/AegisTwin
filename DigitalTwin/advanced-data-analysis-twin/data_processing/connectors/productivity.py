"""
Productivity connector for extracting data from productivity platforms.
"""

import asyncio
import json
import os
import re
import csv
import zipfile
import datetime
import email
from email import policy
from email.parser import BytesParser
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import xml.etree.ElementTree as ET
import sqlite3

from core.logging import get_logger
from core.utils import generate_id, timestamp_now, ensure_directory
from .base import DataConnectorBase

logger = get_logger(__name__)

class ProductivityConnector(DataConnectorBase):
    """
    Connector for extracting data from productivity platforms.
    
    This connector supports:
    - Google Workspace (Gmail, Calendar, Drive, Docs)
    - Microsoft 365 (Outlook, Calendar, OneDrive, Office)
    - Calendar exports (ICS files)
    - Document collections
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the productivity connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - platform: Productivity platform ("google", "microsoft", "calendar", "documents")
                - source_path: Path to the data export file or directory
                - output_dir: Directory to save processed data (default: "data/productivity")
        """
        super().__init__(config)
        self.platform = config.get("platform", "").lower()
        self.source_path = config.get("source_path", "")
        self.output_dir = config.get("output_dir", "data/productivity")
        
        # Ensure output directory exists
        ensure_directory(self.output_dir)
        
        # Platform-specific handlers
        self.platform_handlers = {
            "google": self._extract_google,
            "microsoft": self._extract_microsoft,
            "calendar": self._extract_calendar,
            "documents": self._extract_documents,
        }
    
    async def connect(self) -> bool:
        """
        Verify that the source path exists and is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if source path exists
            if not os.path.exists(self.source_path):
                logger.error(f"Source path does not exist: {self.source_path}")
                return False
            
            # Check if platform is supported
            if self.platform not in self.platform_handlers:
                logger.error(f"Unsupported productivity platform: {self.platform}")
                return False
            
            self.connected = True
            logger.info(f"Connected to {self.platform} data source: {self.source_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.platform} data source: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the data source.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        self.connected = False
        return True
    
    async def extract_data(self, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract data from the productivity platform.
        
        Args:
            parameters: Optional parameters for extraction:
                - content_types: List of content types to extract (emails, calendar, documents, etc.)
                - start_date: Start date for filtering content (YYYY-MM-DD)
                - end_date: End date for filtering content (YYYY-MM-DD)
                - max_items: Maximum number of items to extract
        
        Returns:
            List of raw productivity data dictionaries
        """
        if not self.connected:
            connected = await self.connect()
            if not connected:
                return []
        
        parameters = parameters or {}
        
        try:
            # Call platform-specific handler
            handler = self.platform_handlers.get(self.platform)
            if not handler:
                logger.error(f"No handler for platform: {self.platform}")
                return []
            
            raw_data = await handler(parameters)
            logger.info(f"Extracted {len(raw_data)} items from {self.platform}")
            return raw_data
            
        except Exception as e:
            logger.error(f"Failed to extract {self.platform} data: {str(e)}")
            return []
    
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw productivity data into standardized format.
        
        Args:
            raw_data: Raw productivity data from extraction
            
        Returns:
            List of standardized productivity data dictionaries
        """
        transformed_items = []
        
        for raw_item in raw_data:
            try:
                # Create standardized productivity item format
                item_data = {
                    "id": raw_item.get("id", generate_id("productivity")),
                    "source_id": f"{self.platform}_{raw_item.get('id', '')}",
                    "type": raw_item.get("type", "document"),
                    "platform": self.platform,
                    "date": raw_item.get("timestamp", ""),
                    "title": raw_item.get("title", ""),
                    "content": raw_item.get("content", ""),
                    "has_attachments": raw_item.get("has_attachments", False),
                    "attachments": raw_item.get("attachments", []),
                    "metadata": {
                        "platform": self.platform,
                        "raw_id": raw_item.get("id", ""),
                        "content_type": raw_item.get("type", "document"),
                        "connector_id": self.connector_id,
                        "extraction_time": timestamp_now()
                    }
                }
                
                # Add platform-specific fields
                if self.platform == "google":
                    item_data["metadata"]["google_type"] = raw_item.get("google_type", "")
                elif self.platform == "microsoft":
                    item_data["metadata"]["microsoft_type"] = raw_item.get("microsoft_type", "")
                
                transformed_items.append(item_data)
                
            except Exception as e:
                logger.error(f"Failed to transform productivity item: {str(e)}")
                continue
        
        return transformed_items
    
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
        
        # Productivity-specific validation
        required_fields = ["platform", "source_path"]
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
                "message": f"Missing required configuration fields: {', '.join(missing_fields)}"
            }
        
        # Check if platform is supported
        if self.platform not in self.platform_handlers:
            return {
                "valid": False,
                "message": f"Unsupported productivity platform: {self.platform}"
            }
        
        return {
            "valid": True,
            "message": "Configuration is valid"
        }
    
    async def _extract_google(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Google Workspace export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Google Workspace data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Google Workspace source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["gmail", "calendar", "drive", "docs"])
        
        # Extract Gmail data
        if "gmail" in content_types:
            emails = await self._extract_google_gmail(source_path, parameters)
            items.extend(emails)
        
        # Extract Calendar data
        if "calendar" in content_types:
            events = await self._extract_google_calendar(source_path, parameters)
            items.extend(events)
        
        # Extract Drive data
        if "drive" in content_types:
            files = await self._extract_google_drive(source_path, parameters)
            items.extend(files)
        
        # Extract Docs data
        if "docs" in content_types:
            docs = await self._extract_google_docs(source_path, parameters)
            items.extend(docs)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_google_gmail(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Gmail data from Google Workspace export.
        
        Args:
            source_path: Path to Google Workspace export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Gmail data dictionaries
        """
        emails = []
        
        # Look for Gmail directory
        gmail_dir = source_path / "Mail"
        
        if not gmail_dir.exists() or not gmail_dir.is_dir():
            logger.warning(f"Gmail directory not found: {gmail_dir}")
            return []
        
        # Look for .mbox files or directories with .eml files
        mbox_files = list(gmail_dir.glob("*.mbox"))
        eml_dirs = [d for d in gmail_dir.iterdir() if d.is_dir()]
        
        # Process .mbox files
        for mbox_file in mbox_files:
            try:
                # Extract label/folder name from filename
                label = mbox_file.stem
                
                # Read the mbox file
                with open(mbox_file, 'rb') as f:
                    mbox_content = f.read()
                
                # Split the mbox file into individual emails
                # Mbox files use "From " at the start of a line to separate messages
                email_separator = b"\nFrom "
                email_parts = mbox_content.split(email_separator)
                
                # Process each email
                for i, email_part in enumerate(email_parts):
                    if i == 0 and not email_part.startswith(b"From "):
                        # Skip the first part if it doesn't start with "From "
                        continue
                    
                    if i > 0:
                        # Add the separator back for all but the first email
                        email_part = b"From " + email_part
                    
                    try:
                        # Parse the email
                        parser = BytesParser(policy=policy.default)
                        msg = parser.parsebytes(email_part)
                        
                        # Extract basic info
                        email_id = msg.get("Message-ID", generate_id("gmail"))
                        date_str = msg.get("Date", "")
                        subject = msg.get("Subject", "")
                        from_addr = msg.get("From", "")
                        to_addr = msg.get("To", "")
                        
                        # Parse date
                        try:
                            # Email date formats can vary
                            date_formats = [
                                "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                                "%a, %d %b %Y %H:%M:%S %Z",
                                "%d %b %Y %H:%M:%S %z",
                                "%a, %d %b %Y %H:%M:%S"
                            ]
                            
                            timestamp = None
                            for fmt in date_formats:
                                try:
                                    date_obj = datetime.datetime.strptime(date_str, fmt)
                                    timestamp = date_obj.isoformat()
                                    break
                                except ValueError:
                                    continue
                            
                            if not timestamp:
                                raise ValueError(f"Could not parse date: {date_str}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        email_date = datetime.datetime.fromisoformat(timestamp.split("+")[0].split("Z")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if email_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if email_date > end_date:
                                continue
                        
                        # Extract content
                        content = ""
                        html_content = ""
                        
                        # Get plain text content
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    content = part.get_content()
                                    break
                            
                            # If no plain text, try to get HTML content
                            if not content:
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/html":
                                        html_content = part.get_content()
                                        break
                        else:
                            content_type = msg.get_content_type()
                            if content_type == "text/plain":
                                content = msg.get_content()
                            elif content_type == "text/html":
                                html_content = msg.get_content()
                        
                        # Extract attachments
                        attachments = []
                        has_attachments = False
                        
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_disposition() == "attachment":
                                    has_attachments = True
                                    filename = part.get_filename()
                                    content_type = part.get_content_type()
                                    
                                    # Determine attachment type
                                    att_type = "file"
                                    if content_type.startswith("image/"):
                                        att_type = "image"
                                    elif content_type.startswith("video/"):
                                        att_type = "video"
                                    elif content_type.startswith("audio/"):
                                        att_type = "audio"
                                    
                                    attachments.append({
                                        "type": att_type,
                                        "filename": filename,
                                        "content_type": content_type,
                                        "size": len(part.get_payload(decode=True))
                                    })
                        
                        # Create email object
                        email_obj = {
                            "id": email_id,
                            "timestamp": timestamp,
                            "title": subject,
                            "content": content or html_content,
                            "has_attachments": has_attachments,
                            "attachments": attachments,
                            "type": "email",
                            "google_type": "gmail",
                            "from": from_addr,
                            "to": to_addr,
                            "cc": msg.get("Cc", ""),
                            "bcc": msg.get("Bcc", ""),
                            "label": label,
                            "html_content": html_content
                        }
                        
                        emails.append(email_obj)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process email in {mbox_file}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Failed to process Gmail mbox file {mbox_file}: {str(e)}")
        
        # Process directories with .eml files
        for eml_dir in eml_dirs:
            try:
                # Extract label/folder name from directory name
                label = eml_dir.name
                
                # Find all .eml files
                eml_files = list(eml_dir.glob("*.eml"))
                
                # Process each .eml file
                for eml_file in eml_files:
                    try:
                        # Parse the email
                        with open(eml_file, 'rb') as f:
                            parser = BytesParser(policy=policy.default)
                            msg = parser.parse(f)
                        
                        # Extract basic info
                        email_id = msg.get("Message-ID", generate_id("gmail"))
                        date_str = msg.get("Date", "")
                        subject = msg.get("Subject", "")
                        from_addr = msg.get("From", "")
                        to_addr = msg.get("To", "")
                        
                        # Parse date
                        try:
                            # Email date formats can vary
                            date_formats = [
                                "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                                "%a, %d %b %Y %H:%M:%S %Z",
                                "%d %b %Y %H:%M:%S %z",
                                "%a, %d %b %Y %H:%M:%S"
                            ]
                            
                            timestamp = None
                            for fmt in date_formats:
                                try:
                                    date_obj = datetime.datetime.strptime(date_str, fmt)
                                    timestamp = date_obj.isoformat()
                                    break
                                except ValueError:
                                    continue
                            
                            if not timestamp:
                                raise ValueError(f"Could not parse date: {date_str}")
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply date filters
                        email_date = datetime.datetime.fromisoformat(timestamp.split("+")[0].split("Z")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if email_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if email_date > end_date:
                                continue
                        
                        # Extract content
                        content = ""
                        html_content = ""
                        
                        # Get plain text content
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    content = part.get_content()
                                    break
                            
                            # If no plain text, try to get HTML content
                            if not content:
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/html":
                                        html_content = part.get_content()
                                        break
                        else:
                            content_type = msg.get_content_type()
                            if content_type == "text/plain":
                                content = msg.get_content()
                            elif content_type == "text/html":
                                html_content = msg.get_content()
                        
                        # Extract attachments
                        attachments = []
                        has_attachments = False
                        
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_disposition() == "attachment":
                                    has_attachments = True
                                    filename = part.get_filename()
                                    content_type = part.get_content_type()
                                    
                                    # Determine attachment type
                                    att_type = "file"
                                    if content_type.startswith("image/"):
                                        att_type = "image"
                                    elif content_type.startswith("video/"):
                                        att_type = "video"
                                    elif content_type.startswith("audio/"):
                                        att_type = "audio"
                                    
                                    attachments.append({
                                        "type": att_type,
                                        "filename": filename,
                                        "content_type": content_type,
                                        "size": len(part.get_payload(decode=True))
                                    })
                        
                        # Create email object
                        email_obj = {
                            "id": email_id,
                            "timestamp": timestamp,
                            "title": subject,
                            "content": content or html_content,
                            "has_attachments": has_attachments,
                            "attachments": attachments,
                            "type": "email",
                            "google_type": "gmail",
                            "from": from_addr,
                            "to": to_addr,
                            "cc": msg.get("Cc", ""),
                            "bcc": msg.get("Bcc", ""),
                            "label": label,
                            "html_content": html_content
                        }
                        
                        emails.append(email_obj)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process email file {eml_file}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Failed to process Gmail directory {eml_dir}: {str(e)}")
        
        logger.info(f"Extracted {len(emails)} emails from Gmail")
        return emails
    
    async def _extract_google_calendar(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Calendar data from Google Workspace export.
        
        Args:
            source_path: Path to Google Workspace export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Calendar data dictionaries
        """
        events = []
        
        # Look for Calendar directory
        calendar_dir = source_path / "Calendar"
        
        if not calendar_dir.exists() or not calendar_dir.is_dir():
            logger.warning(f"Calendar directory not found: {calendar_dir}")
            return []
        
        # Look for .ics files
        ics_files = list(calendar_dir.glob("*.ics"))
        
        # Process each .ics file
        for ics_file in ics_files:
            try:
                # Extract calendar name from filename
                calendar_name = ics_file.stem
                
                # Read the ICS file
                with open(ics_file, 'r', encoding='utf-8') as f:
                    ics_content = f.read()
                
                # Parse the ICS content
                # ICS files have a specific format with BEGIN:VEVENT and END:VEVENT markers
                event_blocks = re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', ics_content, re.DOTALL)
                
                # Process each event
                for event_block in event_blocks:
                    try:
                        # Extract event properties
                        uid_match = re.search(r'UID:(.*?)(?:\r?\n)', event_block)
                        summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', event_block)
                        dtstart_match = re.search(r'DTSTART(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                        dtend_match = re.search(r'DTEND(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                        location_match = re.search(r'LOCATION:(.*?)(?:\r?\n)', event_block)
                        description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n)', event_block)
                        
                        # Get values or defaults
                        event_id = uid_match.group(1) if uid_match else generate_id("gcal")
                        summary = summary_match.group(1) if summary_match else ""
                        dtstart = dtstart_match.group(1) if dtstart_match else ""
                        dtend = dtend_match.group(1) if dtend_match else ""
                        location = location_match.group(1) if location_match else ""
                        description = description_match.group(1) if description_match else ""
                        
                        # Parse dates
                        start_timestamp = ""
                        end_timestamp = ""
                        
                        try:
                            # ICS date formats can be:
                            # 20230101T120000Z (UTC)
                            # 20230101T120000 (local time)
                            if dtstart:
                                if "T" in dtstart:
                                    # Has time component
                                    if dtstart.endswith("Z"):
                                        # UTC time
                                        start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
                                    else:
                                        # Local time
                                        start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
                                else:
                                    # Date only
                                    start_date = datetime.datetime.strptime(dtstart, "%Y%m%d")
                                
                                start_timestamp = start_date.isoformat()
                            
                            if dtend:
                                if "T" in dtend:
                                    # Has time component
                                    if dtend.endswith("Z"):
                                        # UTC time
                                        end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%SZ")
                                    else:
                                        # Local time
                                        end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%S")
                                else:
                                    # Date only
                                    end_date = datetime.datetime.strptime(dtend, "%Y%m%d")
                                
                                end_timestamp = end_date.isoformat()
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse event dates: {dtstart}, {dtend}: {str(e)}")
                            if not start_timestamp:
                                start_timestamp = timestamp_now()
                            if not end_timestamp:
                                end_timestamp = start_timestamp
                        
                        # Apply date filters
                        event_date = datetime.datetime.fromisoformat(start_timestamp.split("+")[0].split("Z")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if event_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if event_date > end_date:
                                continue
                        
                        # Create event object
                        event_obj = {
                            "id": event_id,
                            "timestamp": start_timestamp,
                            "title": summary,
                            "content": description,
                            "has_attachments": False,
                            "attachments": [],
                            "type": "event",
                            "google_type": "calendar",
                            "calendar": calendar_name,
                            "location": location,
                            "start_time": start_timestamp,
                            "end_time": end_timestamp
                        }
                        
                        events.append(event_obj)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process calendar event: {str(e)}")
            
            except Exception as e:
                logger.error(f"Failed to process Calendar file {ics_file}: {str(e)}")
        
        logger.info(f"Extracted {len(events)} events from Google Calendar")
        return events
    
    async def _extract_google_drive(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Drive data from Google Workspace export.
        
        Args:
            source_path: Path to Google Workspace export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Drive data dictionaries
        """
        files = []
        
        # Look for Drive directory
        drive_dir = source_path / "Drive"
        
        if not drive_dir.exists() or not drive_dir.is_dir():
            logger.warning(f"Drive directory not found: {drive_dir}")
            return []
        
        # Look for files recursively
        all_files = list(drive_dir.glob("**/*"))
        all_files = [f for f in all_files if f.is_file()]
        
        # Process each file
        for file_path in all_files:
            try:
                # Extract file info
                file_id = generate_id("gdrive")
                file_name = file_path.name
                file_ext = file_path.suffix.lower()
                relative_path = file_path.relative_to(drive_dir)
                parent_dir = relative_path.parent
                
                # Get file stats
                file_stats = file_path.stat()
                file_size = file_stats.st_size
                file_mtime = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                
                # Apply date filters
                file_date = datetime.datetime.fromisoformat(file_mtime.split("+")[0])
                
                if parameters.get("start_date"):
                    start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                    if file_date < start_date:
                        continue
                
                if parameters.get("end_date"):
                    end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                    if file_date > end_date:
                        continue
                
                # Determine file type
                file_type = "file"
                if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    file_type = "image"
                elif file_ext in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"]:
                    file_type = "video"
                elif file_ext in [".mp3", ".wav", ".ogg", ".flac", ".aac"]:
                    file_type = "audio"
                elif file_ext in [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"]:
                    file_type = "document"
                elif file_ext in [".xls", ".xlsx", ".csv", ".ods"]:
                    file_type = "spreadsheet"
                elif file_ext in [".ppt", ".pptx", ".odp"]:
                    file_type = "presentation"
                
                # Extract content for text files
                content = ""
                if file_ext in [".txt", ".csv", ".md"] and file_size < 1024 * 1024:  # Limit to 1MB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read content from {file_path}: {str(e)}")
                
                # Create file object
                file_obj = {
                    "id": file_id,
                    "timestamp": file_mtime,
                    "title": file_name,
                    "content": content,
                    "has_attachments": False,
                    "attachments": [],
                    "type": "file",
                    "google_type": "drive",
                    "file_type": file_type,
                    "file_path": str(relative_path),
                    "file_size": file_size,
                    "parent_directory": str(parent_dir)
                }
                
                files.append(file_obj)
                
            except Exception as e:
                logger.warning(f"Failed to process Drive file {file_path}: {str(e)}")
        
        logger.info(f"Extracted {len(files)} files from Google Drive")
        return files
    
    async def _extract_google_docs(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Docs data from Google Workspace export.
        
        Args:
            source_path: Path to Google Workspace export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Docs data dictionaries
        """
        docs = []
        
        # Look for Docs directory
        docs_dir = source_path / "Drive" / "Docs"
        
        if not docs_dir.exists() or not docs_dir.is_dir():
            logger.warning(f"Docs directory not found: {docs_dir}")
            return []
        
        # Look for document files
        doc_files = list(docs_dir.glob("*.html")) + list(docs_dir.glob("*.txt"))
        
        # Process each document
        for doc_file in doc_files:
            try:
                # Extract document info
                doc_id = generate_id("gdocs")
                doc_name = doc_file.stem
                doc_ext = doc_file.suffix.lower()
                
                # Get file stats
                file_stats = doc_file.stat()
                file_mtime = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                
                # Apply date filters
                doc_date = datetime.datetime.fromisoformat(file_mtime.split("+")[0])
                
                if parameters.get("start_date"):
                    start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                    if doc_date < start_date:
                        continue
                
                if parameters.get("end_date"):
                    end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                    if doc_date > end_date:
                        continue
                
                # Extract content
                content = ""
                html_content = ""
                
                if doc_ext == ".html":
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            
                            # Extract text content from HTML
                            # This is a simple approach - for production, consider using a proper HTML parser
                            content = re.sub(r'<[^>]+>', ' ', html_content)
                            content = re.sub(r'\s+', ' ', content).strip()
                    except Exception as e:
                        logger.warning(f"Failed to read HTML content from {doc_file}: {str(e)}")
                else:
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read content from {doc_file}: {str(e)}")
                
                # Create document object
                doc_obj = {
                    "id": doc_id,
                    "timestamp": file_mtime,
                    "title": doc_name,
                    "content": content,
                    "has_attachments": False,
                    "attachments": [],
                    "type": "document",
                    "google_type": "docs",
                    "file_path": str(doc_file.relative_to(source_path)),
                    "html_content": html_content
                }
                
                docs.append(doc_obj)
                
            except Exception as e:
                logger.warning(f"Failed to process Docs file {doc_file}: {str(e)}")
        
        logger.info(f"Extracted {len(docs)} documents from Google Docs")
        return docs
    
    async def _extract_microsoft(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Microsoft 365 export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw Microsoft 365 data dictionaries
        """
        items = []
        
        # Check if source is a directory
        source_path = Path(self.source_path)
        
        if not source_path.is_dir():
            logger.error(f"Invalid Microsoft 365 source: {self.source_path}. Expected a directory.")
            return []
        
        # Determine content types to extract
        content_types = parameters.get("content_types", ["outlook", "calendar", "onedrive", "office"])
        
        # Extract Outlook data
        if "outlook" in content_types:
            emails = await self._extract_microsoft_outlook(source_path, parameters)
            items.extend(emails)
        
        # Extract Calendar data
        if "calendar" in content_types:
            events = await self._extract_microsoft_calendar(source_path, parameters)
            items.extend(events)
        
        # Extract OneDrive data
        if "onedrive" in content_types:
            files = await self._extract_microsoft_onedrive(source_path, parameters)
            items.extend(files)
        
        # Extract Office data
        if "office" in content_types:
            docs = await self._extract_microsoft_office(source_path, parameters)
            items.extend(docs)
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(items) > max_items:
            items = items[:max_items]
        
        return items
    
    async def _extract_microsoft_outlook(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Outlook data from Microsoft 365 export.
        
        Args:
            source_path: Path to Microsoft 365 export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Outlook data dictionaries
        """
        emails = []
        
        # Look for Outlook directory
        outlook_dir = source_path / "Outlook"
        
        if not outlook_dir.exists() or not outlook_dir.is_dir():
            logger.warning(f"Outlook directory not found: {outlook_dir}")
            return []
        
        # Look for .pst files, .msg files, or .eml files
        pst_files = list(outlook_dir.glob("*.pst"))
        msg_files = list(outlook_dir.glob("**/*.msg"))
        eml_files = list(outlook_dir.glob("**/*.eml"))
        
        # Process .eml files (most common in exports)
        for eml_file in eml_files:
            try:
                # Extract folder name from path
                folder = eml_file.parent.name
                
                # Parse the email
                with open(eml_file, 'rb') as f:
                    parser = BytesParser(policy=policy.default)
                    msg = parser.parse(f)
                
                # Extract basic info
                email_id = msg.get("Message-ID", generate_id("outlook"))
                date_str = msg.get("Date", "")
                subject = msg.get("Subject", "")
                from_addr = msg.get("From", "")
                to_addr = msg.get("To", "")
                
                # Parse date
                try:
                    # Email date formats can vary
                    date_formats = [
                        "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                        "%a, %d %b %Y %H:%M:%S %Z",
                        "%d %b %Y %H:%M:%S %z",
                        "%a, %d %b %Y %H:%M:%S"
                    ]
                    
                    timestamp = None
                    for fmt in date_formats:
                        try:
                            date_obj = datetime.datetime.strptime(date_str, fmt)
                            timestamp = date_obj.isoformat()
                            break
                        except ValueError:
                            continue
                    
                    if not timestamp:
                        raise ValueError(f"Could not parse date: {date_str}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                    timestamp = timestamp_now()
                
                # Apply date filters
                email_date = datetime.datetime.fromisoformat(timestamp.split("+")[0].split("Z")[0])
                
                if parameters.get("start_date"):
                    start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                    if email_date < start_date:
                        continue
                
                if parameters.get("end_date"):
                    end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                    if email_date > end_date:
                        continue
                
                # Extract content
                content = ""
                html_content = ""
                
                # Get plain text content
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            content = part.get_content()
                            break
                    
                    # If no plain text, try to get HTML content
                    if not content:
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/html":
                                html_content = part.get_content()
                                break
                else:
                    content_type = msg.get_content_type()
                    if content_type == "text/plain":
                        content = msg.get_content()
                    elif content_type == "text/html":
                        html_content = msg.get_content()
                
                # Extract attachments
                attachments = []
                has_attachments = False
                
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_disposition() == "attachment":
                            has_attachments = True
                            filename = part.get_filename()
                            content_type = part.get_content_type()
                            
                            # Determine attachment type
                            att_type = "file"
                            if content_type.startswith("image/"):
                                att_type = "image"
                            elif content_type.startswith("video/"):
                                att_type = "video"
                            elif content_type.startswith("audio/"):
                                att_type = "audio"
                            
                            attachments.append({
                                "type": att_type,
                                "filename": filename,
                                "content_type": content_type,
                                "size": len(part.get_payload(decode=True))
                            })
                
                # Create email object
                email_obj = {
                    "id": email_id,
                    "timestamp": timestamp,
                    "title": subject,
                    "content": content or html_content,
                    "has_attachments": has_attachments,
                    "attachments": attachments,
                    "type": "email",
                    "microsoft_type": "outlook",
                    "from": from_addr,
                    "to": to_addr,
                    "cc": msg.get("Cc", ""),
                    "bcc": msg.get("Bcc", ""),
                    "folder": folder,
                    "html_content": html_content
                }
                
                emails.append(email_obj)
                
            except Exception as e:
                logger.warning(f"Failed to process Outlook email file {eml_file}: {str(e)}")
        
        # Note: Processing .pst files requires specialized libraries like libpff
        # and is beyond the scope of this implementation
        if pst_files:
            logger.warning(f"Found {len(pst_files)} PST files, but processing them requires specialized libraries.")
        
        # Note: Processing .msg files requires specialized libraries like extract_msg
        # and is beyond the scope of this implementation
        if msg_files:
            logger.warning(f"Found {len(msg_files)} MSG files, but processing them requires specialized libraries.")
        
        logger.info(f"Extracted {len(emails)} emails from Outlook")
        return emails
    
    async def _extract_microsoft_calendar(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Calendar data from Microsoft 365 export.
        
        Args:
            source_path: Path to Microsoft 365 export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Calendar data dictionaries
        """
        events = []
        
        # Look for Calendar directory
        calendar_dir = source_path / "Calendar"
        
        if not calendar_dir.exists() or not calendar_dir.is_dir():
            logger.warning(f"Calendar directory not found: {calendar_dir}")
            return []
        
        # Look for .ics files
        ics_files = list(calendar_dir.glob("*.ics"))
        
        # Process each .ics file
        for ics_file in ics_files:
            try:
                # Extract calendar name from filename
                calendar_name = ics_file.stem
                
                # Read the ICS file
                with open(ics_file, 'r', encoding='utf-8') as f:
                    ics_content = f.read()
                
                # Parse the ICS content
                # ICS files have a specific format with BEGIN:VEVENT and END:VEVENT markers
                event_blocks = re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', ics_content, re.DOTALL)
                
                # Process each event
                for event_block in event_blocks:
                    try:
                        # Extract event properties
                        uid_match = re.search(r'UID:(.*?)(?:\r?\n)', event_block)
                        summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', event_block)
                        dtstart_match = re.search(r'DTSTART(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                        dtend_match = re.search(r'DTEND(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                        location_match = re.search(r'LOCATION:(.*?)(?:\r?\n)', event_block)
                        description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n)', event_block)
                        
                        # Get values or defaults
                        event_id = uid_match.group(1) if uid_match else generate_id("mscal")
                        summary = summary_match.group(1) if summary_match else ""
                        dtstart = dtstart_match.group(1) if dtstart_match else ""
                        dtend = dtend_match.group(1) if dtend_match else ""
                        location = location_match.group(1) if location_match else ""
                        description = description_match.group(1) if description_match else ""
                        
                        # Parse dates
                        start_timestamp = ""
                        end_timestamp = ""
                        
                        try:
                            # ICS date formats can be:
                            # 20230101T120000Z (UTC)
                            # 20230101T120000 (local time)
                            if dtstart:
                                if "T" in dtstart:
                                    # Has time component
                                    if dtstart.endswith("Z"):
                                        # UTC time
                                        start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
                                    else:
                                        # Local time
                                        start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
                                else:
                                    # Date only
                                    start_date = datetime.datetime.strptime(dtstart, "%Y%m%d")
                                
                                start_timestamp = start_date.isoformat()
                            
                            if dtend:
                                if "T" in dtend:
                                    # Has time component
                                    if dtend.endswith("Z"):
                                        # UTC time
                                        end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%SZ")
                                    else:
                                        # Local time
                                        end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%S")
                                else:
                                    # Date only
                                    end_date = datetime.datetime.strptime(dtend, "%Y%m%d")
                                
                                end_timestamp = end_date.isoformat()
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse event dates: {dtstart}, {dtend}: {str(e)}")
                            if not start_timestamp:
                                start_timestamp = timestamp_now()
                            if not end_timestamp:
                                end_timestamp = start_timestamp
                        
                        # Apply date filters
                        event_date = datetime.datetime.fromisoformat(start_timestamp.split("+")[0].split("Z")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if event_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if event_date > end_date:
                                continue
                        
                        # Create event object
                        event_obj = {
                            "id": event_id,
                            "timestamp": start_timestamp,
                            "title": summary,
                            "content": description,
                            "has_attachments": False,
                            "attachments": [],
                            "type": "event",
                            "microsoft_type": "calendar",
                            "calendar": calendar_name,
                            "location": location,
                            "start_time": start_timestamp,
                            "end_time": end_timestamp
                        }
                        
                        events.append(event_obj)
                        
                    except Exception as e:
                        logger.warning(f"Failed to process calendar event: {str(e)}")
            
            except Exception as e:
                logger.error(f"Failed to process Calendar file {ics_file}: {str(e)}")
        
        logger.info(f"Extracted {len(events)} events from Microsoft Calendar")
        return events
    
    async def _extract_microsoft_onedrive(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract OneDrive data from Microsoft 365 export.
        
        Args:
            source_path: Path to Microsoft 365 export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw OneDrive data dictionaries
        """
        files = []
        
        # Look for OneDrive directory
        onedrive_dir = source_path / "OneDrive"
        
        if not onedrive_dir.exists() or not onedrive_dir.is_dir():
            logger.warning(f"OneDrive directory not found: {onedrive_dir}")
            return []
        
        # Look for files recursively
        all_files = list(onedrive_dir.glob("**/*"))
        all_files = [f for f in all_files if f.is_file()]
        
        # Process each file
        for file_path in all_files:
            try:
                # Extract file info
                file_id = generate_id("onedrive")
                file_name = file_path.name
                file_ext = file_path.suffix.lower()
                relative_path = file_path.relative_to(onedrive_dir)
                parent_dir = relative_path.parent
                
                # Get file stats
                file_stats = file_path.stat()
                file_size = file_stats.st_size
                file_mtime = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                
                # Apply date filters
                file_date = datetime.datetime.fromisoformat(file_mtime.split("+")[0])
                
                if parameters.get("start_date"):
                    start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                    if file_date < start_date:
                        continue
                
                if parameters.get("end_date"):
                    end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                    if file_date > end_date:
                        continue
                
                # Determine file type
                file_type = "file"
                if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    file_type = "image"
                elif file_ext in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"]:
                    file_type = "video"
                elif file_ext in [".mp3", ".wav", ".ogg", ".flac", ".aac"]:
                    file_type = "audio"
                elif file_ext in [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"]:
                    file_type = "document"
                elif file_ext in [".xls", ".xlsx", ".csv", ".ods"]:
                    file_type = "spreadsheet"
                elif file_ext in [".ppt", ".pptx", ".odp"]:
                    file_type = "presentation"
                
                # Extract content for text files
                content = ""
                if file_ext in [".txt", ".csv", ".md"] and file_size < 1024 * 1024:  # Limit to 1MB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read content from {file_path}: {str(e)}")
                
                # Create file object
                file_obj = {
                    "id": file_id,
                    "timestamp": file_mtime,
                    "title": file_name,
                    "content": content,
                    "has_attachments": False,
                    "attachments": [],
                    "type": "file",
                    "microsoft_type": "onedrive",
                    "file_type": file_type,
                    "file_path": str(relative_path),
                    "file_size": file_size,
                    "parent_directory": str(parent_dir)
                }
                
                files.append(file_obj)
                
            except Exception as e:
                logger.warning(f"Failed to process OneDrive file {file_path}: {str(e)}")
        
        logger.info(f"Extracted {len(files)} files from OneDrive")
        return files
    
    async def _extract_microsoft_office(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Office data from Microsoft 365 export.
        
        Args:
            source_path: Path to Microsoft 365 export directory
            parameters: Extraction parameters
            
        Returns:
            List of raw Office data dictionaries
        """
        docs = []
        
        # Look for Office directory or files
        office_dirs = [
            source_path / "Word",
            source_path / "Excel",
            source_path / "PowerPoint",
            source_path / "OneNote"
        ]
        
        # Process each Office directory
        for office_dir in office_dirs:
            if not office_dir.exists() or not office_dir.is_dir():
                continue
            
            # Determine Office app
            office_app = office_dir.name.lower()
            
            # Look for files
            if office_app == "word":
                file_patterns = ["*.docx", "*.doc", "*.rtf", "*.txt"]
            elif office_app == "excel":
                file_patterns = ["*.xlsx", "*.xls", "*.csv"]
            elif office_app == "powerpoint":
                file_patterns = ["*.pptx", "*.ppt"]
            elif office_app == "onenote":
                file_patterns = ["*.one", "*.onetoc2", "*.htm", "*.html"]
            else:
                file_patterns = ["*.*"]
            
            # Find all matching files
            all_files = []
            for pattern in file_patterns:
                all_files.extend(list(office_dir.glob(f"**/{pattern}")))
            
            # Process each file
            for file_path in all_files:
                try:
                    # Extract file info
                    file_id = generate_id("msoffice")
                    file_name = file_path.name
                    file_ext = file_path.suffix.lower()
                    relative_path = file_path.relative_to(source_path)
                    
                    # Get file stats
                    file_stats = file_path.stat()
                    file_size = file_stats.st_size
                    file_mtime = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    
                    # Apply date filters
                    file_date = datetime.datetime.fromisoformat(file_mtime.split("+")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if file_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if file_date > end_date:
                            continue
                    
                    # Determine document type
                    doc_type = "document"
                    if file_ext in [".xlsx", ".xls", ".csv"]:
                        doc_type = "spreadsheet"
                    elif file_ext in [".pptx", ".ppt"]:
                        doc_type = "presentation"
                    elif file_ext in [".one", ".onetoc2"]:
                        doc_type = "notebook"
                    
                    # Extract content for text files
                    content = ""
                    if file_ext in [".txt", ".csv", ".md", ".htm", ".html"] and file_size < 1024 * 1024:  # Limit to 1MB
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                                # For HTML files, extract text content
                                if file_ext in [".htm", ".html"]:
                                    content = re.sub(r'<[^>]+>', ' ', content)
                                    content = re.sub(r'\s+', ' ', content).strip()
                        except Exception as e:
                            logger.warning(f"Failed to read content from {file_path}: {str(e)}")
                    
                    # Create document object
                    doc_obj = {
                        "id": file_id,
                        "timestamp": file_mtime,
                        "title": file_name,
                        "content": content,
                        "has_attachments": False,
                        "attachments": [],
                        "type": "document",
                        "microsoft_type": office_app,
                        "document_type": doc_type,
                        "file_path": str(relative_path),
                        "file_size": file_size
                    }
                    
                    docs.append(doc_obj)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Office file {file_path}: {str(e)}")
        
        logger.info(f"Extracted {len(docs)} documents from Microsoft Office")
        return docs
    
    async def _extract_calendar(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from calendar files.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw calendar data dictionaries
        """
        events = []
        
        # Check if source is a file or directory
        source_path = Path(self.source_path)
        
        if source_path.is_file():
            # Single calendar file
            if source_path.suffix.lower() == ".ics":
                events = await self._extract_ics_file(source_path, parameters)
            else:
                logger.error(f"Unsupported calendar file format: {source_path}")
        elif source_path.is_dir():
            # Directory with calendar files
            ics_files = list(source_path.glob("**/*.ics"))
            
            for ics_file in ics_files:
                file_events = await self._extract_ics_file(ics_file, parameters)
                events.extend(file_events)
        else:
            logger.error(f"Invalid calendar source: {self.source_path}")
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(events) > max_items:
            events = events[:max_items]
        
        return events
    
    async def _extract_ics_file(self, ics_file: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract events from an ICS file.
        
        Args:
            ics_file: Path to ICS file
            parameters: Extraction parameters
            
        Returns:
            List of raw event dictionaries
        """
        events = []
        
        try:
            # Extract calendar name from filename
            calendar_name = ics_file.stem
            
            # Read the ICS file
            with open(ics_file, 'r', encoding='utf-8') as f:
                ics_content = f.read()
            
            # Parse the ICS content
            # ICS files have a specific format with BEGIN:VEVENT and END:VEVENT markers
            event_blocks = re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', ics_content, re.DOTALL)
            
            # Process each event
            for event_block in event_blocks:
                try:
                    # Extract event properties
                    uid_match = re.search(r'UID:(.*?)(?:\r?\n)', event_block)
                    summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', event_block)
                    dtstart_match = re.search(r'DTSTART(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                    dtend_match = re.search(r'DTEND(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                    location_match = re.search(r'LOCATION:(.*?)(?:\r?\n)', event_block)
                    description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n)', event_block)
                    
                    # Get values or defaults
                    event_id = uid_match.group(1) if uid_match else generate_id("calendar")
                    summary = summary_match.group(1) if summary_match else ""
                    dtstart = dtstart_match.group(1) if dtstart_match else ""
                    dtend = dtend_match.group(1) if dtend_match else ""
                    location = location_match.group(1) if location_match else ""
                    description = description_match.group(1) if description_match else ""
                    
                    # Parse dates
                    start_timestamp = ""
                    end_timestamp = ""
                    
                    try:
                        # ICS date formats can be:
                        # 20230101T120000Z (UTC)
                        # 20230101T120000 (local time)
                        if dtstart:
                            if "T" in dtstart:
                                # Has time component
                                if dtstart.endswith("Z"):
                                    # UTC time
                                    start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ")
                                else:
                                    # Local time
                                    start_date = datetime.datetime.strptime(dtstart, "%Y%m%dT%H%M%S")
                            else:
                                # Date only
                                start_date = datetime.datetime.strptime(dtstart, "%Y%m%d")
                            
                            start_timestamp = start_date.isoformat()
                        
                        if dtend:
                            if "T" in dtend:
                                # Has time component
                                if dtend.endswith("Z"):
                                    # UTC time
                                    end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%SZ")
                                else:
                                    # Local time
                                    end_date = datetime.datetime.strptime(dtend, "%Y%m%dT%H%M%S")
                            else:
                                # Date only
                                end_date = datetime.datetime.strptime(dtend, "%Y%m%d")
                            
                            end_timestamp = end_date.isoformat()
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse event dates: {dtstart}, {dtend}: {str(e)}")
                        if not start_timestamp:
                            start_timestamp = timestamp_now()
                        if not end_timestamp:
                            end_timestamp = start_timestamp
                    
                    # Apply date filters
                    event_date = datetime.datetime.fromisoformat(start_timestamp.split("+")[0].split("Z")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if event_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if event_date > end_date:
                            continue
                    
                    # Create event object
                    event_obj = {
                        "id": event_id,
                        "timestamp": start_timestamp,
                        "title": summary,
                        "content": description,
                        "has_attachments": False,
                        "attachments": [],
                        "type": "event",
                        "calendar": calendar_name,
                        "location": location,
                        "start_time": start_timestamp,
                        "end_time": end_timestamp
                    }
                    
                    events.append(event_obj)
                    
                except Exception as e:
                    logger.warning(f"Failed to process calendar event: {str(e)}")
        
        except Exception as e:
            logger.error(f"Failed to process calendar file {ics_file}: {str(e)}")
        
        logger.info(f"Extracted {len(events)} events from calendar file {ics_file}")
        return events
    
    async def _extract_documents(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from document collections.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw document data dictionaries
        """
        documents = []
        
        # Check if source is a file or directory
        source_path = Path(self.source_path)
        
        if source_path.is_file():
            # Single document file
            documents = await self._extract_document_file(source_path, parameters)
        elif source_path.is_dir():
            # Directory with document files
            doc_files = list(source_path.glob("**/*.*"))
            doc_files = [f for f in doc_files if f.is_file()]
            
            for doc_file in doc_files:
                file_docs = await self._extract_document_file(doc_file, parameters)
                documents.extend(file_docs)
        else:
            logger.error(f"Invalid documents source: {self.source_path}")
        
        # Apply max_items limit if specified
        max_items = parameters.get("max_items")
        if max_items and len(documents) > max_items:
            documents = documents[:max_items]
        
        return documents
    
    async def _extract_document_file(self, file_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract content from a document file.
        
        Args:
            file_path: Path to document file
            parameters: Extraction parameters
            
        Returns:
            List containing a single document dictionary
        """
        try:
            # Extract file info
            file_id = generate_id("document")
            file_name = file_path.name
            file_ext = file_path.suffix.lower()
            
            # Get file stats
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            file_mtime = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            
            # Apply date filters
            file_date = datetime.datetime.fromisoformat(file_mtime.split("+")[0])
            
            if parameters.get("start_date"):
                start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                if file_date < start_date:
                    return []
            
            if parameters.get("end_date"):
                end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                if file_date > end_date:
                    return []
            
            # Determine document type
            doc_type = "document"
            if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                doc_type = "image"
            elif file_ext in [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"]:
                doc_type = "video"
            elif file_ext in [".mp3", ".wav", ".ogg", ".flac", ".aac"]:
                doc_type = "audio"
            elif file_ext in [".pdf"]:
                doc_type = "pdf"
            elif file_ext in [".doc", ".docx", ".rtf", ".odt"]:
                doc_type = "word"
            elif file_ext in [".xls", ".xlsx", ".csv", ".ods"]:
                doc_type = "spreadsheet"
            elif file_ext in [".ppt", ".pptx", ".odp"]:
                doc_type = "presentation"
            elif file_ext in [".txt", ".md", ".html", ".htm", ".xml", ".json"]:
                doc_type = "text"
            
            # Extract content for text files
            content = ""
            if file_ext in [".txt", ".md", ".csv", ".html", ".htm", ".xml", ".json"] and file_size < 1024 * 1024:  # Limit to 1MB
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # For HTML files, extract text content
                        if file_ext in [".htm", ".html"]:
                            content = re.sub(r'<[^>]+>', ' ', content)
                            content = re.sub(r'\s+', ' ', content).strip()
                except Exception as e:
                    logger.warning(f"Failed to read content from {file_path}: {str(e)}")
            
            # Create document object
            doc_obj = {
                "id": file_id,
                "timestamp": file_mtime,
                "title": file_name,
                "content": content,
                "has_attachments": False,
                "attachments": [],
                "type": "document",
                "document_type": doc_type,
                "file_path": str(file_path),
                "file_size": file_size
            }
            
            return [doc_obj]
            
        except Exception as e:
            logger.error(f"Failed to process document file {file_path}: {str(e)}")
            return []