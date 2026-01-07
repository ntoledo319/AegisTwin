"""
iOS Backup Connector for CogniLink

This module provides functionality to import data from iOS backups,
including messages, contacts, and other data.
"""

import os
import logging
import sqlite3
import plistlib
import hashlib
import shutil
import tempfile
from typing import Dict, List, Any, Optional, Iterator, Tuple
from datetime import datetime, timedelta

from cognilink.pipeline.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

class IOSBackupConnector(BaseConnector):
    """
    Connector for importing data from iOS backups.
    
    This class handles extraction of messages, contacts, and other data
    from iOS backup files.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the iOS backup connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "ios_backup"
        self.temp_dir = None
    
    def extract_from_file(self, backup_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            data_types: List of data types to extract (e.g., ["messages", "contacts"])
            **kwargs: Additional arguments
            
        Yields:
            Dictionaries containing normalized data
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup directory not found: {backup_path}")
            return
        
        # Default to extracting all data types if none specified
        data_types = data_types or ["messages", "contacts", "calls", "notes", "calendar"]
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            self.temp_dir = temp_dir
            
            try:
                # Extract data based on requested types
                if "messages" in data_types:
                    yield from self._extract_messages(backup_path)
                
                if "contacts" in data_types:
                    yield from self._extract_contacts(backup_path)
                
                if "calls" in data_types:
                    yield from self._extract_call_history(backup_path)
                
                if "notes" in data_types:
                    yield from self._extract_notes(backup_path)
                
                if "calendar" in data_types:
                    yield from self._extract_calendar(backup_path)
                
                logger.info(f"Completed iOS backup extraction: {self.item_count} items extracted, {self.error_count} errors")
            
            finally:
                # Clean up
                self.temp_dir = None
    
    def _extract_messages(self, backup_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract messages from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            
        Yields:
            Dictionaries containing normalized message data
        """
        # Path to the SMS database in iOS backups
        sms_db_path = self._find_file_in_backup(backup_path, "Library/SMS/sms.db")
        
        if not sms_db_path:
            logger.warning("SMS database not found in backup")
            return
        
        # Copy the database to a temporary location for processing
        temp_db_path = os.path.join(self.temp_dir, "sms.db")
        shutil.copy2(sms_db_path, temp_db_path)
        
        try:
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for messages
            query = """
            SELECT 
                message.ROWID as message_id,
                message.date as timestamp,
                message.text as content,
                message.is_from_me as is_sent,
                message.handle_id as contact_id,
                handle.id as contact_identifier
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            ORDER BY message.date DESC
            """
            
            cursor.execute(query)
            messages = cursor.fetchall()
            
            logger.info(f"Found {len(messages)} messages in SMS database")
            
            # Process each message
            for msg in messages:
                try:
                    # Convert timestamp from Apple's format (seconds since 2001-01-01) to Unix timestamp
                    mac_epoch = datetime(2001, 1, 1)
                    timestamp = mac_epoch + timedelta(seconds=msg['timestamp']/1000000000)
                    
                    # Determine sender and recipient
                    is_sent = bool(msg['is_sent'])
                    contact_id = msg['contact_identifier'] if not is_sent else "me"
                    sender = "me" if is_sent else contact_id
                    recipient = contact_id if is_sent else "me"
                    
                    # Create normalized message data
                    message_data = {
                        'id': f"ios_message_{msg['message_id']}",
                        'sender': sender,
                        'recipient': recipient,
                        'content': msg['content'] or "",
                        'timestamp': timestamp.isoformat(),
                        'platform': 'ios_imessage' if 'service' in msg and msg['service'] == 'iMessage' else 'ios_sms',
                        'is_sent': is_sent,
                        'source': 'ios_backup'
                    }
                    
                    # Apply filters
                    if self._apply_filters(message_data):
                        self.item_count += 1
                        yield message_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing message {msg['message_id']}: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting messages from iOS backup: {str(e)}")
    
    def _extract_contacts(self, backup_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            
        Yields:
            Dictionaries containing normalized contact data
        """
        # Path to the contacts database in iOS backups
        contacts_db_path = self._find_file_in_backup(backup_path, "Library/AddressBook/AddressBook.sqlitedb")
        
        if not contacts_db_path:
            logger.warning("Contacts database not found in backup")
            return
        
        # Copy the database to a temporary location for processing
        temp_db_path = os.path.join(self.temp_dir, "contacts.db")
        shutil.copy2(contacts_db_path, temp_db_path)
        
        try:
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for contacts
            query = """
            SELECT 
                ABPerson.ROWID as contact_id,
                ABPerson.First as first_name,
                ABPerson.Last as last_name,
                ABPerson.Organization as organization
            FROM ABPerson
            """
            
            cursor.execute(query)
            contacts = cursor.fetchall()
            
            logger.info(f"Found {len(contacts)} contacts in database")
            
            # Process each contact
            for contact in contacts:
                try:
                    # Get contact details
                    contact_id = contact['contact_id']
                    
                    # Get email addresses
                    cursor.execute("""
                    SELECT value FROM ABMultiValue
                    WHERE record_id = ? AND property = 4
                    """, (contact_id,))
                    emails = [row[0] for row in cursor.fetchall()]
                    
                    # Get phone numbers
                    cursor.execute("""
                    SELECT value FROM ABMultiValue
                    WHERE record_id = ? AND property = 3
                    """, (contact_id,))
                    phones = [row[0] for row in cursor.fetchall()]
                    
                    # Create normalized contact data
                    contact_data = {
                        'id': f"ios_contact_{contact_id}",
                        'first_name': contact['first_name'] or "",
                        'last_name': contact['last_name'] or "",
                        'organization': contact['organization'] or "",
                        'emails': emails,
                        'phones': phones,
                        'source': 'ios_backup',
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have creation time
                        'type': 'contact'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact_data):
                        self.item_count += 1
                        yield contact_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing contact {contact_id}: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting contacts from iOS backup: {str(e)}")
    
    def _extract_call_history(self, backup_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract call history from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            
        Yields:
            Dictionaries containing normalized call data
        """
        # Path to the call history database in iOS backups
        calls_db_path = self._find_file_in_backup(backup_path, "Library/CallHistoryDB/CallHistory.storedata")
        
        if not calls_db_path:
            logger.warning("Call history database not found in backup")
            return
        
        # Copy the database to a temporary location for processing
        temp_db_path = os.path.join(self.temp_dir, "calls.db")
        shutil.copy2(calls_db_path, temp_db_path)
        
        try:
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for calls
            query = """
            SELECT 
                ROWID as call_id,
                date as timestamp,
                address as phone_number,
                duration,
                flags
            FROM call
            ORDER BY date DESC
            """
            
            cursor.execute(query)
            calls = cursor.fetchall()
            
            logger.info(f"Found {len(calls)} calls in database")
            
            # Process each call
            for call in calls:
                try:
                    # Convert timestamp from Apple's format (seconds since 2001-01-01) to Unix timestamp
                    mac_epoch = datetime(2001, 1, 1)
                    timestamp = mac_epoch + timedelta(seconds=call['timestamp']/1000000000)
                    
                    # Determine call type based on flags
                    flags = call['flags']
                    if flags & 1:  # Incoming call
                        call_type = "incoming"
                        sender = call['phone_number']
                        recipient = "me"
                    else:  # Outgoing call
                        call_type = "outgoing"
                        sender = "me"
                        recipient = call['phone_number']
                    
                    # Check if call was missed
                    if flags & 4:
                        call_type = "missed"
                    
                    # Create normalized call data
                    call_data = {
                        'id': f"ios_call_{call['call_id']}",
                        'sender': sender,
                        'recipient': recipient,
                        'timestamp': timestamp.isoformat(),
                        'duration': call['duration'],
                        'call_type': call_type,
                        'source': 'ios_backup',
                        'type': 'call'
                    }
                    
                    # Apply filters
                    if self._apply_filters(call_data):
                        self.item_count += 1
                        yield call_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing call {call['call_id']}: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting call history from iOS backup: {str(e)}")
    
    def _extract_notes(self, backup_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract notes from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            
        Yields:
            Dictionaries containing normalized note data
        """
        # Path to the notes database in iOS backups
        notes_db_path = self._find_file_in_backup(backup_path, "Library/Notes/notes.sqlite")
        
        if not notes_db_path:
            logger.warning("Notes database not found in backup")
            return
        
        # Copy the database to a temporary location for processing
        temp_db_path = os.path.join(self.temp_dir, "notes.db")
        shutil.copy2(notes_db_path, temp_db_path)
        
        try:
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for notes
            query = """
            SELECT 
                ZNOTE.Z_PK as note_id,
                ZNOTE.ZCREATIONDATE as created_date,
                ZNOTE.ZMODIFICATIONDATE as modified_date,
                ZNOTE.ZTITLE as title,
                ZNOTEBODY.ZCONTENT as content
            FROM ZNOTE
            LEFT JOIN ZNOTEBODY ON ZNOTE.Z_PK = ZNOTEBODY.Z_NOTE
            ORDER BY ZNOTE.ZMODIFICATIONDATE DESC
            """
            
            cursor.execute(query)
            notes = cursor.fetchall()
            
            logger.info(f"Found {len(notes)} notes in database")
            
            # Process each note
            for note in notes:
                try:
                    # Convert timestamp from Apple's format (seconds since 2001-01-01) to Unix timestamp
                    mac_epoch = datetime(2001, 1, 1)
                    created_date = mac_epoch + timedelta(seconds=note['created_date'])
                    modified_date = mac_epoch + timedelta(seconds=note['modified_date'])
                    
                    # Extract content from HTML if needed
                    content = note['content'] or ""
                    if content.startswith("<html>"):
                        # Simple HTML to text conversion
                        content = content.replace("<div>", "\n").replace("</div>", "")
                        content = re.sub(r'<[^>]+>', '', content)
                    
                    # Create normalized note data
                    note_data = {
                        'id': f"ios_note_{note['note_id']}",
                        'title': note['title'] or "Untitled Note",
                        'content': content,
                        'created_at': created_date.isoformat(),
                        'modified_at': modified_date.isoformat(),
                        'timestamp': modified_date.isoformat(),  # Use modified date as primary timestamp
                        'source': 'ios_backup',
                        'type': 'note'
                    }
                    
                    # Apply filters
                    if self._apply_filters(note_data):
                        self.item_count += 1
                        yield note_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing note {note['note_id']}: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting notes from iOS backup: {str(e)}")
    
    def _extract_calendar(self, backup_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract calendar events from an iOS backup.
        
        Args:
            backup_path: Path to the iOS backup directory
            
        Yields:
            Dictionaries containing normalized calendar event data
        """
        # Path to the calendar database in iOS backups
        calendar_db_path = self._find_file_in_backup(backup_path, "Library/Calendar/Calendar.sqlitedb")
        
        if not calendar_db_path:
            logger.warning("Calendar database not found in backup")
            return
        
        # Copy the database to a temporary location for processing
        temp_db_path = os.path.join(self.temp_dir, "calendar.db")
        shutil.copy2(calendar_db_path, temp_db_path)
        
        try:
            # Connect to the database
            conn = sqlite3.connect(temp_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query for calendar events
            query = """
            SELECT 
                CalendarItem.ROWID as event_id,
                CalendarItem.summary as title,
                CalendarItem.description as description,
                CalendarItem.start_date as start_date,
                CalendarItem.end_date as end_date,
                CalendarItem.all_day as all_day,
                Calendar.title as calendar_name
            FROM CalendarItem
            LEFT JOIN Calendar ON CalendarItem.calendar_id = Calendar.ROWID
            ORDER BY CalendarItem.start_date DESC
            """
            
            cursor.execute(query)
            events = cursor.fetchall()
            
            logger.info(f"Found {len(events)} calendar events in database")
            
            # Process each event
            for event in events:
                try:
                    # Convert timestamp from Apple's format (seconds since 2001-01-01) to Unix timestamp
                    mac_epoch = datetime(2001, 1, 1)
                    start_date = mac_epoch + timedelta(seconds=event['start_date'])
                    end_date = mac_epoch + timedelta(seconds=event['end_date'])
                    
                    # Create normalized event data
                    event_data = {
                        'id': f"ios_event_{event['event_id']}",
                        'title': event['title'] or "Untitled Event",
                        'description': event['description'] or "",
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'all_day': bool(event['all_day']),
                        'calendar_name': event['calendar_name'] or "Default",
                        'timestamp': start_date.isoformat(),  # Use start date as primary timestamp
                        'source': 'ios_backup',
                        'type': 'calendar_event'
                    }
                    
                    # Apply filters
                    if self._apply_filters(event_data):
                        self.item_count += 1
                        yield event_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing calendar event {event['event_id']}: {str(e)}")
            
            conn.close()
        
        except Exception as e:
            logger.error(f"Error extracting calendar events from iOS backup: {str(e)}")
    
    def _find_file_in_backup(self, backup_path: str, relative_path: str) -> Optional[str]:
        """
        Find a file in an iOS backup by its relative path.
        
        Args:
            backup_path: Path to the iOS backup directory
            relative_path: Relative path of the file in the iOS filesystem
            
        Returns:
            Full path to the file in the backup, or None if not found
        """
        # iOS backups store files with hashed filenames
        # First try the domain-based hash (iOS 10 and later)
        domain = "HomeDomain"
        filename = self._hash_path(domain, relative_path)
        file_path = os.path.join(backup_path, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        # Try without domain (iOS 9 and earlier)
        filename = self._hash_path_old(relative_path)
        file_path = os.path.join(backup_path, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        # Try to find the file in the Manifest.db (iOS 10 and later)
        manifest_db_path = os.path.join(backup_path, "Manifest.db")
        if os.path.exists(manifest_db_path):
            try:
                conn = sqlite3.connect(manifest_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT fileID FROM Files WHERE relativePath = ?", (relative_path,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    file_id = result[0]
                    file_path = os.path.join(backup_path, file_id)
                    if os.path.exists(file_path):
                        return file_path
            except Exception as e:
                logger.error(f"Error searching Manifest.db: {str(e)}")
        
        return None
    
    def _hash_path(self, domain: str, relative_path: str) -> str:
        """
        Hash a file path using the iOS 10+ backup format.
        
        Args:
            domain: The domain of the file (e.g., "HomeDomain")
            relative_path: Relative path of the file
            
        Returns:
            Hashed filename used in the backup
        """
        hash_input = domain + "-" + relative_path
        return hashlib.sha1(hash_input.encode('utf-8')).hexdigest()
    
    def _hash_path_old(self, relative_path: str) -> str:
        """
        Hash a file path using the iOS 9 and earlier backup format.
        
        Args:
            relative_path: Relative path of the file
            
        Returns:
            Hashed filename used in the backup
        """
        return hashlib.sha1(relative_path.encode('utf-8')).hexdigest()
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
            
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for iOS backups as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item