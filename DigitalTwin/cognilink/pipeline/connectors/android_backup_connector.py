"""
Android Backup Connector for CogniLink

This module provides functionality to import data from Android device backups,
including SMS messages, call logs, and contacts.
"""

import os
import json
import logging
import zipfile
import sqlite3
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class AndroidBackupConnector(BaseConnector):
    """
    Connector for importing Android backup data.
    
    This class handles extraction of SMS messages, call logs, and contacts
    from Android device backups.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Android backup connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "android"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from an Android backup file.
        
        Args:
            file_path: Path to the Android backup file (ZIP, ADB backup, or directory)
            data_types: List of data types to extract (e.g., ["sms", "calls", "contacts"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["sms", "calls", "contacts", "apps"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_android_directory(temp_dir, data_types)
        
        # Handle ADB backup file
        elif file_path.endswith('.ab'):
            # ADB backups require special handling
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert ADB backup to TAR
                tar_path = os.path.join(temp_dir, "backup.tar")
                os.system(f"dd if={file_path} bs=24 skip=1 | python -c 'import zlib,sys;sys.stdout.buffer.write(zlib.decompress(sys.stdin.buffer.read()))' > {tar_path}")
                
                # Extract TAR file
                extract_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_dir, exist_ok=True)
                os.system(f"tar -xf {tar_path} -C {extract_dir}")
                
                yield from self._process_android_directory(extract_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_android_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_android_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process an Android backup directory.
        
        Args:
            directory_path: Path to the Android backup directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # Extract SMS messages
        if "sms" in data_types:
            sms_db_path = self._find_file(directory_path, "mmssms.db")
            if sms_db_path:
                yield from self._extract_sms(sms_db_path)
            else:
                logger.warning("SMS database not found in Android backup")
        
        # Extract call logs
        if "calls" in data_types:
            calls_db_path = self._find_file(directory_path, "calllog.db")
            if calls_db_path:
                yield from self._extract_calls(calls_db_path)
            else:
                # Try alternate location
                calls_db_path = self._find_file(directory_path, "contacts2.db")
                if calls_db_path:
                    yield from self._extract_calls(calls_db_path)
                else:
                    logger.warning("Call log database not found in Android backup")
        
        # Extract contacts
        if "contacts" in data_types:
            contacts_db_path = self._find_file(directory_path, "contacts2.db")
            if contacts_db_path:
                yield from self._extract_contacts(contacts_db_path)
            else:
                logger.warning("Contacts database not found in Android backup")
        
        # Extract app data
        if "apps" in data_types:
            # Look for WhatsApp data
            whatsapp_db_path = self._find_file(directory_path, "msgstore.db")
            if whatsapp_db_path:
                yield from self._extract_whatsapp(whatsapp_db_path)
            
            # Look for other app data as needed
            # ...
    
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
    
    def _extract_sms(self, db_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract SMS messages from an Android SMS database.
        
        Args:
            db_path: Path to the SMS database
                
        Yields:
            Dictionaries containing normalized SMS data
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for SMS messages
            cursor.execute("""
                SELECT 
                    _id, 
                    address, 
                    date, 
                    body, 
                    type, 
                    read 
                FROM sms
                ORDER BY date DESC
            """)
            
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} SMS messages in Android backup")
            
            for row in rows:
                try:
                    # Determine if the message was sent or received
                    # Type 1 = Received, Type 2 = Sent
                    is_sent = row['type'] == 2
                    
                    # Parse timestamp
                    timestamp = datetime.fromtimestamp(row['date'] / 1000)  # Android stores timestamps in milliseconds
                    
                    # Create normalized message data
                    sms_data = {
                        'id': f"android_sms_{row['_id']}",
                        'content': row['body'],
                        'timestamp': timestamp.isoformat(),
                        'sender': 'me' if is_sent else row['address'],
                        'recipient': row['address'] if is_sent else 'me',
                        'is_sent': is_sent,
                        'is_read': row['read'] == 1,
                        'platform': 'android',
                        'type': 'sms',
                        'source': 'android_backup'
                    }
                    
                    # Apply filters
                    if self._apply_filters(sms_data):
                        self.item_count += 1
                        yield sms_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing SMS message: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting SMS messages from Android backup: {str(e)}")
    
    def _extract_calls(self, db_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract call logs from an Android calls database.
        
        Args:
            db_path: Path to the calls database
                
        Yields:
            Dictionaries containing normalized call log data
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try to query the calls table
            try:
                cursor.execute("""
                    SELECT 
                        _id, 
                        number, 
                        date, 
                        duration, 
                        type, 
                        name 
                    FROM calls
                    ORDER BY date DESC
                """)
            except sqlite3.OperationalError:
                # If the calls table doesn't exist, try the call_log table
                try:
                    cursor.execute("""
                        SELECT 
                            _id, 
                            number, 
                            date, 
                            duration, 
                            type, 
                            name 
                        FROM call_log
                        ORDER BY date DESC
                    """)
                except sqlite3.OperationalError:
                    logger.error("Could not find calls or call_log table in database")
                    conn.close()
                    return
            
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} call logs in Android backup")
            
            for row in rows:
                try:
                    # Parse timestamp
                    timestamp = datetime.fromtimestamp(row['date'] / 1000)  # Android stores timestamps in milliseconds
                    
                    # Determine call type
                    # Type 1 = Incoming, Type 2 = Outgoing, Type 3 = Missed
                    call_type = "incoming"
                    if row['type'] == 2:
                        call_type = "outgoing"
                    elif row['type'] == 3:
                        call_type = "missed"
                    
                    # Create normalized call data
                    call_data = {
                        'id': f"android_call_{row['_id']}",
                        'number': row['number'],
                        'name': row.get('name', ''),
                        'timestamp': timestamp.isoformat(),
                        'duration': row['duration'],  # Duration in seconds
                        'call_type': call_type,
                        'platform': 'android',
                        'type': 'call',
                        'source': 'android_backup'
                    }
                    
                    # Apply filters
                    if self._apply_filters(call_data):
                        self.item_count += 1
                        yield call_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing call log: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting call logs from Android backup: {str(e)}")
    
    def _extract_contacts(self, db_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from an Android contacts database.
        
        Args:
            db_path: Path to the contacts database
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for contacts
            cursor.execute("""
                SELECT 
                    c._id, 
                    c.display_name, 
                    c.times_contacted, 
                    c.last_time_contacted
                FROM contacts AS c
                ORDER BY c.display_name
            """)
            
            contacts = cursor.fetchall()
            logger.info(f"Found {len(contacts)} contacts in Android backup")
            
            for contact in contacts:
                try:
                    contact_id = contact['_id']
                    
                    # Get phone numbers for this contact
                    cursor.execute("""
                        SELECT 
                            number, 
                            type 
                        FROM phone_lookup 
                        WHERE person = ?
                    """, (contact_id,))
                    
                    phone_numbers = []
                    for phone_row in cursor.fetchall():
                        phone_type = "other"
                        if phone_row['type'] == 1:
                            phone_type = "home"
                        elif phone_row['type'] == 2:
                            phone_type = "mobile"
                        elif phone_row['type'] == 3:
                            phone_type = "work"
                        
                        phone_numbers.append({
                            'number': phone_row['number'],
                            'type': phone_type
                        })
                    
                    # Get email addresses for this contact
                    cursor.execute("""
                        SELECT 
                            data, 
                            type 
                        FROM email_lookup 
                        WHERE person = ?
                    """, (contact_id,))
                    
                    email_addresses = []
                    for email_row in cursor.fetchall():
                        email_type = "other"
                        if email_row['type'] == 1:
                            email_type = "home"
                        elif email_row['type'] == 2:
                            email_type = "work"
                        
                        email_addresses.append({
                            'email': email_row['data'],
                            'type': email_type
                        })
                    
                    # Parse timestamp
                    last_contacted = None
                    if contact['last_time_contacted'] and contact['last_time_contacted'] > 0:
                        last_contacted = datetime.fromtimestamp(contact['last_time_contacted'] / 1000)
                    
                    # Create normalized contact data
                    contact_data = {
                        'id': f"android_contact_{contact_id}",
                        'name': contact['display_name'],
                        'phone_numbers': phone_numbers,
                        'email_addresses': email_addresses,
                        'times_contacted': contact['times_contacted'],
                        'last_contacted': last_contacted.isoformat() if last_contacted else None,
                        'platform': 'android',
                        'type': 'contact',
                        'source': 'android_backup'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact_data):
                        self.item_count += 1
                        yield contact_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing contact: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting contacts from Android backup: {str(e)}")
    
    def _extract_whatsapp(self, db_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract WhatsApp messages from an Android WhatsApp database.
        
        Args:
            db_path: Path to the WhatsApp database
                
        Yields:
            Dictionaries containing normalized WhatsApp message data
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for WhatsApp messages
            cursor.execute("""
                SELECT 
                    _id, 
                    key_remote_jid, 
                    key_from_me, 
                    data, 
                    timestamp, 
                    media_url, 
                    media_mime_type, 
                    media_name
                FROM messages
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} WhatsApp messages in Android backup")
            
            for row in rows:
                try:
                    # Determine if the message was sent or received
                    is_sent = row['key_from_me'] == 1
                    
                    # Parse timestamp
                    timestamp = datetime.fromtimestamp(row['timestamp'] / 1000)  # WhatsApp stores timestamps in milliseconds
                    
                    # Extract recipient/sender from JID
                    jid = row['key_remote_jid']
                    contact = jid.split('@')[0] if jid and '@' in jid else jid
                    
                    # Check if this is a group chat
                    is_group = jid and '-' in jid
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"whatsapp_msg_{row['_id']}",
                        'content': row['data'] or '',
                        'timestamp': timestamp.isoformat(),
                        'sender': 'me' if is_sent else contact,
                        'recipient': contact if is_sent else 'me',
                        'is_sent': is_sent,
                        'is_group': is_group,
                        'group_id': jid if is_group else None,
                        'has_media': bool(row['media_url']),
                        'media_type': row['media_mime_type'],
                        'media_name': row['media_name'],
                        'media_url': row['media_url'],
                        'platform': 'whatsapp',
                        'type': 'message',
                        'source': 'android_backup'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing WhatsApp message: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting WhatsApp messages from Android backup: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Android data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item