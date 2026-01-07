"""
Messaging connector for extracting data from messaging platforms.
"""

import asyncio
import json
import os
import re
import zipfile
import sqlite3
import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from core.logging import get_logger
from core.utils import generate_id, timestamp_now, ensure_directory
from .base import DataConnectorBase

logger = get_logger(__name__)

class MessagingConnector(DataConnectorBase):
    """
    Connector for extracting data from messaging platforms.
    
    This connector supports:
    - WhatsApp chat exports
    - Telegram chat exports
    - Signal backups
    - SMS backups
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the messaging connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - platform: Messaging platform ("whatsapp", "telegram", "signal", "sms")
                - source_path: Path to the backup file or directory
                - output_dir: Directory to save processed data (default: "data/messaging")
        """
        super().__init__(config)
        self.platform = config.get("platform", "").lower()
        self.source_path = config.get("source_path", "")
        self.output_dir = config.get("output_dir", "data/messaging")
        
        # Ensure output directory exists
        ensure_directory(self.output_dir)
        
        # Platform-specific handlers
        self.platform_handlers = {
            "whatsapp": self._extract_whatsapp,
            "telegram": self._extract_telegram,
            "signal": self._extract_signal,
            "sms": self._extract_sms,
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
                logger.error(f"Unsupported messaging platform: {self.platform}")
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
        Extract data from the messaging platform.
        
        Args:
            parameters: Optional parameters for extraction:
                - start_date: Start date for filtering messages (YYYY-MM-DD)
                - end_date: End date for filtering messages (YYYY-MM-DD)
                - contact: Filter by contact name or number
                - max_messages: Maximum number of messages to extract
        
        Returns:
            List of raw message data dictionaries
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
            logger.info(f"Extracted {len(raw_data)} messages from {self.platform}")
            return raw_data
            
        except Exception as e:
            logger.error(f"Failed to extract {self.platform} data: {str(e)}")
            return []
    
    async def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw message data into standardized format.
        
        Args:
            raw_data: Raw message data from extraction
            
        Returns:
            List of standardized message data dictionaries
        """
        transformed_messages = []
        
        for raw_message in raw_data:
            try:
                # Create standardized message format
                message_data = {
                    "id": raw_message.get("id", generate_id("msg")),
                    "source_id": f"{self.platform}_{raw_message.get('id', '')}",
                    "type": "message",
                    "platform": self.platform,
                    "date": raw_message.get("timestamp", ""),
                    "sender": raw_message.get("sender", ""),
                    "recipient": raw_message.get("recipient", ""),
                    "content": raw_message.get("content", ""),
                    "has_attachments": raw_message.get("has_attachments", False),
                    "attachments": raw_message.get("attachments", []),
                    "chat_id": raw_message.get("chat_id", ""),
                    "chat_name": raw_message.get("chat_name", ""),
                    "is_group": raw_message.get("is_group", False),
                    "metadata": {
                        "platform": self.platform,
                        "raw_id": raw_message.get("id", ""),
                        "message_type": raw_message.get("message_type", "text"),
                        "connector_id": self.connector_id,
                        "extraction_time": timestamp_now()
                    }
                }
                
                transformed_messages.append(message_data)
                
            except Exception as e:
                logger.error(f"Failed to transform message: {str(e)}")
                continue
        
        return transformed_messages
    
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
        
        # Messaging-specific validation
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
                "message": f"Unsupported messaging platform: {self.platform}"
            }
        
        return {
            "valid": True,
            "message": "Configuration is valid"
        }
    
    async def _extract_whatsapp(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from WhatsApp chat export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        messages = []
        
        # Check if source is a file or directory
        source_path = Path(self.source_path)
        
        if source_path.is_file() and source_path.suffix == '.txt':
            # Single chat export file
            chat_files = [source_path]
        elif source_path.is_dir():
            # Directory with multiple chat export files
            chat_files = list(source_path.glob('*.txt'))
        else:
            logger.error(f"Invalid WhatsApp source: {self.source_path}")
            return []
        
        # Process each chat file
        for chat_file in chat_files:
            try:
                # Extract chat name from filename
                chat_name = chat_file.stem
                
                # Determine if it's a group chat (simple heuristic)
                is_group = " - " in chat_name or "group" in chat_name.lower()
                
                # Parse the chat file
                with open(chat_file, 'r', encoding='utf-8', errors='ignore') as f:
                    chat_content = f.read()
                
                # Extract messages using regex
                # WhatsApp format: [DD/MM/YY, HH:MM:SS] Sender: Message
                message_pattern = r'\[(\d{2}/\d{2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.*?)(?=\[\d{2}/\d{2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?\]|$)'
                
                matches = re.findall(message_pattern, chat_content, re.DOTALL)
                
                for match in matches:
                    date_str, time_str, sender, content = match
                    
                    # Parse date and time
                    try:
                        # Handle different date formats
                        if len(date_str.split('/')[2]) == 2:  # YY format
                            date_format = "%d/%m/%y"
                        else:  # YYYY format
                            date_format = "%d/%m/%Y"
                        
                        # Parse date
                        message_date = datetime.datetime.strptime(date_str, date_format)
                        
                        # Parse time
                        if len(time_str.split(':')) == 2:  # HH:MM format
                            time_format = "%H:%M"
                        else:  # HH:MM:SS format
                            time_format = "%H:%M:%S"
                        
                        message_time = datetime.datetime.strptime(time_str, time_format)
                        
                        # Combine date and time
                        timestamp = datetime.datetime(
                            message_date.year,
                            message_date.month,
                            message_date.day,
                            message_time.hour,
                            message_time.minute,
                            message_time.second if len(time_str.split(':')) > 2 else 0
                        ).isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date/time: {date_str} {time_str}: {str(e)}")
                        timestamp = timestamp_now()
                    
                    # Clean up sender name
                    sender = sender.strip()
                    
                    # Check for attachments
                    has_attachments = False
                    attachments = []
                    
                    # Look for common attachment indicators
                    attachment_indicators = [
                        "<Media omitted>",
                        "<image omitted>",
                        "<video omitted>",
                        "<audio omitted>",
                        "<document omitted>",
                        "<GIF omitted>",
                        "<sticker omitted>"
                    ]
                    
                    for indicator in attachment_indicators:
                        if indicator in content:
                            has_attachments = True
                            attachment_type = indicator.strip("<>").split()[0].lower()
                            attachments.append({
                                "type": attachment_type,
                                "filename": None,
                                "path": None,
                                "size": 0
                            })
                            # Remove the indicator from content
                            content = content.replace(indicator, "").strip()
                    
                    # Apply filters
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if message_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if message_date > end_date:
                            continue
                    
                    if parameters.get("contact") and parameters["contact"].lower() not in sender.lower():
                        continue
                    
                    # Create message object
                    message = {
                        "id": generate_id("whatsapp"),
                        "timestamp": timestamp,
                        "sender": sender,
                        "recipient": chat_name if not is_group else None,
                        "content": content.strip(),
                        "has_attachments": has_attachments,
                        "attachments": attachments,
                        "chat_id": chat_name,
                        "chat_name": chat_name,
                        "is_group": is_group,
                        "message_type": "text" if not has_attachments else "media"
                    }
                    
                    messages.append(message)
                
                logger.info(f"Extracted {len(messages)} messages from WhatsApp chat: {chat_name}")
                
            except Exception as e:
                logger.error(f"Failed to process WhatsApp chat file {chat_file}: {str(e)}")
        
        # Apply max_messages limit if specified
        max_messages = parameters.get("max_messages")
        if max_messages and len(messages) > max_messages:
            messages = messages[:max_messages]
        
        return messages
    
    async def _extract_telegram(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Telegram chat export.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        messages = []
        
        # Check if source is a file or directory
        source_path = Path(self.source_path)
        
        if source_path.is_file() and source_path.suffix == '.json':
            # Single chat export file
            chat_files = [source_path]
        elif source_path.is_dir():
            # Directory with multiple chat export files
            chat_files = list(source_path.glob('*.json'))
        else:
            logger.error(f"Invalid Telegram source: {self.source_path}")
            return []
        
        # Process each chat file
        for chat_file in chat_files:
            try:
                # Load JSON data
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                
                # Extract chat info
                chat_name = chat_data.get("name", chat_file.stem)
                chat_type = chat_data.get("type", "personal_chat")
                is_group = chat_type in ["group", "supergroup"]
                
                # Process messages
                raw_messages = chat_data.get("messages", [])
                
                for raw_message in raw_messages:
                    # Extract basic info
                    message_id = raw_message.get("id", generate_id("telegram"))
                    sender = raw_message.get("from", "")
                    date_str = raw_message.get("date", "")
                    
                    # Parse date
                    try:
                        # Telegram date format: "YYYY-MM-DDTHH:MM:SS"
                        timestamp = datetime.datetime.fromisoformat(date_str).isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                        timestamp = timestamp_now()
                    
                    # Extract content based on message type
                    message_type = raw_message.get("type", "message")
                    content = ""
                    has_attachments = False
                    attachments = []
                    
                    if message_type == "message":
                        content = raw_message.get("text", "")
                        
                        # Check for formatted text
                        if isinstance(content, list):
                            # Telegram stores formatted text as a list of text elements
                            text_parts = []
                            for part in content:
                                if isinstance(part, str):
                                    text_parts.append(part)
                                elif isinstance(part, dict) and "text" in part:
                                    text_parts.append(part["text"])
                            content = "".join(text_parts)
                    
                    elif message_type in ["photo", "video", "audio", "voice_message", "sticker", "animation"]:
                        has_attachments = True
                        content = raw_message.get("text", "") or raw_message.get("caption", "")
                        
                        # Extract media info
                        media_file = raw_message.get("file", "")
                        media_type = message_type
                        
                        attachments.append({
                            "type": media_type,
                            "filename": media_file,
                            "path": None,
                            "size": raw_message.get("file_size", 0),
                            "mime_type": raw_message.get("mime_type", "")
                        })
                    
                    # Apply filters
                    message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if message_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if message_date > end_date:
                            continue
                    
                    if parameters.get("contact") and parameters["contact"].lower() not in sender.lower():
                        continue
                    
                    # Create message object
                    message = {
                        "id": message_id,
                        "timestamp": timestamp,
                        "sender": sender,
                        "recipient": chat_name if not is_group else None,
                        "content": content,
                        "has_attachments": has_attachments,
                        "attachments": attachments,
                        "chat_id": chat_name,
                        "chat_name": chat_name,
                        "is_group": is_group,
                        "message_type": message_type
                    }
                    
                    messages.append(message)
                
                logger.info(f"Extracted {len(messages)} messages from Telegram chat: {chat_name}")
                
            except Exception as e:
                logger.error(f"Failed to process Telegram chat file {chat_file}: {str(e)}")
        
        # Apply max_messages limit if specified
        max_messages = parameters.get("max_messages")
        if max_messages and len(messages) > max_messages:
            messages = messages[:max_messages]
        
        return messages
    
    async def _extract_signal(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from Signal backup.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        # Signal backups are encrypted SQLite databases
        # This is a simplified implementation that assumes an unencrypted backup
        messages = []
        
        # Check if source is a file with .db extension
        source_path = Path(self.source_path)
        
        if not (source_path.is_file() and source_path.suffix == '.db'):
            logger.error(f"Invalid Signal source: {self.source_path}. Expected a .db file.")
            return []
        
        try:
            # Connect to the database
            conn = sqlite3.connect(str(source_path))
            cursor = conn.cursor()
            
            # Query messages
            cursor.execute("""
                SELECT 
                    m._id, 
                    m.date_sent, 
                    c.name, 
                    m.body, 
                    m.has_attachment,
                    c.group_id
                FROM messages m
                JOIN conversations c ON m.thread_id = c._id
                ORDER BY m.date_sent DESC
            """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                message_id, date_sent, chat_name, body, has_attachment, group_id = row
                
                # Convert timestamp to ISO format
                try:
                    # Signal stores timestamps as milliseconds since epoch
                    timestamp = datetime.datetime.fromtimestamp(date_sent / 1000).isoformat()
                except Exception as e:
                    logger.warning(f"Failed to parse date: {date_sent}: {str(e)}")
                    timestamp = timestamp_now()
                
                # Determine if it's a group chat
                is_group = group_id is not None
                
                # Get attachments if any
                attachments = []
                if has_attachment:
                    try:
                        cursor.execute("""
                            SELECT 
                                a._id,
                                a.content_type,
                                a.size
                            FROM attachments a
                            JOIN message_attachments ma ON a._id = ma.attachment_id
                            WHERE ma.message_id = ?
                        """, (message_id,))
                        
                        attachment_rows = cursor.fetchall()
                        
                        for att_row in attachment_rows:
                            att_id, content_type, size = att_row
                            
                            # Determine attachment type
                            if content_type.startswith("image/"):
                                att_type = "image"
                            elif content_type.startswith("video/"):
                                att_type = "video"
                            elif content_type.startswith("audio/"):
                                att_type = "audio"
                            else:
                                att_type = "file"
                            
                            attachments.append({
                                "type": att_type,
                                "filename": f"attachment_{att_id}",
                                "path": None,
                                "size": size,
                                "mime_type": content_type
                            })
                    except Exception as e:
                        logger.warning(f"Failed to get attachments for message {message_id}: {str(e)}")
                
                # Apply filters
                message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                
                if parameters.get("start_date"):
                    start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                    if message_date < start_date:
                        continue
                
                if parameters.get("end_date"):
                    end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                    if message_date > end_date:
                        continue
                
                # Create message object
                message = {
                    "id": str(message_id),
                    "timestamp": timestamp,
                    "sender": "Unknown",  # Signal DB structure may vary
                    "recipient": chat_name,
                    "content": body or "",
                    "has_attachments": bool(attachments),
                    "attachments": attachments,
                    "chat_id": str(chat_name),
                    "chat_name": chat_name,
                    "is_group": is_group,
                    "message_type": "text" if not attachments else "media"
                }
                
                messages.append(message)
            
            # Close connection
            conn.close()
            
            logger.info(f"Extracted {len(messages)} messages from Signal backup")
            
        except Exception as e:
            logger.error(f"Failed to process Signal backup: {str(e)}")
        
        # Apply max_messages limit if specified
        max_messages = parameters.get("max_messages")
        if max_messages and len(messages) > max_messages:
            messages = messages[:max_messages]
        
        return messages
    
    async def _extract_sms(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from SMS backup.
        
        Args:
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        messages = []
        
        # Check if source is a file with .xml or .db extension
        source_path = Path(self.source_path)
        
        if source_path.is_file():
            if source_path.suffix == '.xml':
                # XML backup (common for SMS Backup & Restore app)
                return await self._extract_sms_xml(source_path, parameters)
            elif source_path.suffix == '.db':
                # SQLite backup (common for Android SMS databases)
                return await self._extract_sms_db(source_path, parameters)
            else:
                logger.error(f"Unsupported SMS backup format: {source_path}")
                return []
        else:
            logger.error(f"Invalid SMS source: {self.source_path}")
            return []
    
    async def _extract_sms_xml(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract SMS data from XML backup.
        
        Args:
            source_path: Path to XML backup file
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        messages = []
        
        try:
            import xml.etree.ElementTree as ET
            
            # Parse XML file
            tree = ET.parse(source_path)
            root = tree.getroot()
            
            # Process SMS messages
            for sms in root.findall(".//sms"):
                try:
                    # Extract message data
                    message_id = sms.get("_id", generate_id("sms"))
                    address = sms.get("address", "")  # Phone number
                    date_str = sms.get("date", "")  # Timestamp in milliseconds
                    body = sms.get("body", "")
                    type_code = int(sms.get("type", "1"))
                    
                    # Determine message direction
                    # Type 1: Received, Type 2: Sent
                    is_sent = type_code == 2
                    sender = "Me" if is_sent else address
                    recipient = address if is_sent else "Me"
                    
                    # Convert timestamp to ISO format
                    try:
                        # SMS timestamps are in milliseconds since epoch
                        timestamp = datetime.datetime.fromtimestamp(int(date_str) / 1000).isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                        timestamp = timestamp_now()
                    
                    # Apply filters
                    message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if message_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if message_date > end_date:
                            continue
                    
                    if parameters.get("contact") and parameters["contact"].lower() not in address.lower():
                        continue
                    
                    # Create message object
                    message = {
                        "id": message_id,
                        "timestamp": timestamp,
                        "sender": sender,
                        "recipient": recipient,
                        "content": body,
                        "has_attachments": False,  # SMS typically don't have attachments
                        "attachments": [],
                        "chat_id": address,
                        "chat_name": address,
                        "is_group": False,
                        "message_type": "text"
                    }
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning(f"Failed to process SMS message: {str(e)}")
            
            # Process MMS messages if present
            for mms in root.findall(".//mms"):
                try:
                    # Extract message data
                    message_id = mms.get("_id", generate_id("mms"))
                    address = mms.get("address", "")  # Phone number
                    date_str = mms.get("date", "")  # Timestamp in milliseconds
                    type_code = int(mms.get("msg_box", "1"))
                    
                    # Determine message direction
                    # Type 1: Received, Type 2: Sent
                    is_sent = type_code == 2
                    sender = "Me" if is_sent else address
                    recipient = address if is_sent else "Me"
                    
                    # Convert timestamp to ISO format
                    try:
                        # MMS timestamps are in milliseconds since epoch
                        timestamp = datetime.datetime.fromtimestamp(int(date_str) / 1000).isoformat()
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {date_str}: {str(e)}")
                        timestamp = timestamp_now()
                    
                    # Extract message body and attachments
                    body = ""
                    attachments = []
                    
                    # Check for parts (text and media)
                    for part in mms.findall(".//part"):
                        content_type = part.get("ct", "")
                        
                        if content_type == "text/plain":
                            # Text part
                            body = part.get("text", "")
                        elif content_type.startswith("image/") or content_type.startswith("video/") or content_type.startswith("audio/"):
                            # Media part
                            data = part.get("data", "")
                            name = part.get("name", f"attachment_{len(attachments)}")
                            
                            # Determine attachment type
                            if content_type.startswith("image/"):
                                att_type = "image"
                            elif content_type.startswith("video/"):
                                att_type = "video"
                            elif content_type.startswith("audio/"):
                                att_type = "audio"
                            else:
                                att_type = "file"
                            
                            attachments.append({
                                "type": att_type,
                                "filename": name,
                                "path": None,
                                "size": 0,
                                "mime_type": content_type
                            })
                    
                    # Apply filters
                    message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                    
                    if parameters.get("start_date"):
                        start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                        if message_date < start_date:
                            continue
                    
                    if parameters.get("end_date"):
                        end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                        if message_date > end_date:
                            continue
                    
                    if parameters.get("contact") and parameters["contact"].lower() not in address.lower():
                        continue
                    
                    # Create message object
                    message = {
                        "id": message_id,
                        "timestamp": timestamp,
                        "sender": sender,
                        "recipient": recipient,
                        "content": body,
                        "has_attachments": bool(attachments),
                        "attachments": attachments,
                        "chat_id": address,
                        "chat_name": address,
                        "is_group": False,
                        "message_type": "mms"
                    }
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning(f"Failed to process MMS message: {str(e)}")
            
            logger.info(f"Extracted {len(messages)} messages from SMS XML backup")
            
        except Exception as e:
            logger.error(f"Failed to process SMS XML backup: {str(e)}")
        
        # Apply max_messages limit if specified
        max_messages = parameters.get("max_messages")
        if max_messages and len(messages) > max_messages:
            messages = messages[:max_messages]
        
        return messages
    
    async def _extract_sms_db(self, source_path: Path, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract SMS data from SQLite database backup.
        
        Args:
            source_path: Path to SQLite database file
            parameters: Extraction parameters
            
        Returns:
            List of raw message data dictionaries
        """
        messages = []
        
        try:
            # Connect to the database
            conn = sqlite3.connect(str(source_path))
            cursor = conn.cursor()
            
            # Check if it's an Android SMS database
            try:
                # Try to query the SMS table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sms'")
                has_sms_table = cursor.fetchone() is not None
                
                if has_sms_table:
                    # Query SMS messages
                    cursor.execute("""
                        SELECT 
                            _id, 
                            address, 
                            date, 
                            body, 
                            type
                        FROM sms
                        ORDER BY date DESC
                    """)
                    
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        message_id, address, date_sent, body, type_code = row
                        
                        # Determine message direction
                        # Type 1: Received, Type 2: Sent
                        is_sent = type_code == 2
                        sender = "Me" if is_sent else address
                        recipient = address if is_sent else "Me"
                        
                        # Convert timestamp to ISO format
                        try:
                            # SMS timestamps are in milliseconds since epoch
                            timestamp = datetime.datetime.fromtimestamp(int(date_sent) / 1000).isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_sent}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Apply filters
                        message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if message_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if message_date > end_date:
                                continue
                        
                        if parameters.get("contact") and parameters["contact"].lower() not in address.lower():
                            continue
                        
                        # Create message object
                        message = {
                            "id": str(message_id),
                            "timestamp": timestamp,
                            "sender": sender,
                            "recipient": recipient,
                            "content": body or "",
                            "has_attachments": False,
                            "attachments": [],
                            "chat_id": address,
                            "chat_name": address,
                            "is_group": False,
                            "message_type": "text"
                        }
                        
                        messages.append(message)
                
                # Check for MMS table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mms'")
                has_mms_table = cursor.fetchone() is not None
                
                if has_mms_table:
                    # Query MMS messages
                    cursor.execute("""
                        SELECT 
                            _id, 
                            address, 
                            date, 
                            msg_box
                        FROM mms
                        ORDER BY date DESC
                    """)
                    
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        message_id, address, date_sent, type_code = row
                        
                        # Determine message direction
                        # Type 1: Received, Type 2: Sent
                        is_sent = type_code == 2
                        sender = "Me" if is_sent else address
                        recipient = address if is_sent else "Me"
                        
                        # Convert timestamp to ISO format
                        try:
                            # MMS timestamps are in milliseconds since epoch
                            timestamp = datetime.datetime.fromtimestamp(int(date_sent) / 1000).isoformat()
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {date_sent}: {str(e)}")
                            timestamp = timestamp_now()
                        
                        # Try to get message body and attachments
                        body = ""
                        attachments = []
                        
                        try:
                            # Query parts table for text and media
                            cursor.execute("""
                                SELECT 
                                    ct, 
                                    text
                                FROM part
                                WHERE mid = ?
                            """, (message_id,))
                            
                            part_rows = cursor.fetchall()
                            
                            for part_row in part_rows:
                                content_type, text = part_row
                                
                                if content_type == "text/plain":
                                    body = text or ""
                                elif content_type.startswith("image/") or content_type.startswith("video/") or content_type.startswith("audio/"):
                                    # Determine attachment type
                                    if content_type.startswith("image/"):
                                        att_type = "image"
                                    elif content_type.startswith("video/"):
                                        att_type = "video"
                                    elif content_type.startswith("audio/"):
                                        att_type = "audio"
                                    else:
                                        att_type = "file"
                                    
                                    attachments.append({
                                        "type": att_type,
                                        "filename": f"attachment_{len(attachments)}",
                                        "path": None,
                                        "size": 0,
                                        "mime_type": content_type
                                    })
                        except Exception as e:
                            logger.warning(f"Failed to get MMS parts for message {message_id}: {str(e)}")
                        
                        # Apply filters
                        message_date = datetime.datetime.fromisoformat(timestamp.split("T")[0])
                        
                        if parameters.get("start_date"):
                            start_date = datetime.datetime.fromisoformat(parameters["start_date"])
                            if message_date < start_date:
                                continue
                        
                        if parameters.get("end_date"):
                            end_date = datetime.datetime.fromisoformat(parameters["end_date"])
                            if message_date > end_date:
                                continue
                        
                        if parameters.get("contact") and parameters["contact"].lower() not in address.lower():
                            continue
                        
                        # Create message object
                        message = {
                            "id": str(message_id),
                            "timestamp": timestamp,
                            "sender": sender,
                            "recipient": recipient,
                            "content": body,
                            "has_attachments": bool(attachments),
                            "attachments": attachments,
                            "chat_id": address,
                            "chat_name": address,
                            "is_group": False,
                            "message_type": "mms"
                        }
                        
                        messages.append(message)
                
            except sqlite3.OperationalError as e:
                logger.warning(f"Failed to query SMS database: {str(e)}")
            
            # Close connection
            conn.close()
            
            logger.info(f"Extracted {len(messages)} messages from SMS database backup")
            
        except Exception as e:
            logger.error(f"Failed to process SMS database backup: {str(e)}")
        
        # Apply max_messages limit if specified
        max_messages = parameters.get("max_messages")
        if max_messages and len(messages) > max_messages:
            messages = messages[:max_messages]
        
        return messages