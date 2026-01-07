"""
Google Suite Connector for CogniLink

This module provides functionality to import data from Google Takeout exports,
including Gmail, Google Calendar, Google Drive, and Google Photos.
"""

import os
import json
import logging
import zipfile
import csv
import email
import mailbox
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime
import tempfile
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime, generate_message_id

logger = logging.getLogger(__name__)

class GoogleConnector(BaseConnector):
    """
    Connector for importing Google Suite data.
    
    This class handles extraction of Gmail, Google Calendar, Google Drive,
    and Google Photos data from Google Takeout exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Google connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "google"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Google Takeout export file.
        
        Args:
            file_path: Path to the Google Takeout export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["gmail", "calendar", "drive", "photos"])
            **kwargs: Additional arguments
                
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["gmail", "calendar", "drive", "photos", "contacts", "youtube", "maps"]
        
        # Handle ZIP file
        if file_path.endswith('.zip') or file_path.endswith('.tgz'):
            with tempfile.TemporaryDirectory() as temp_dir:
                if file_path.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                else:  # .tgz file
                    import tarfile
                    with tarfile.open(file_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(temp_dir)
                
                yield from self._process_google_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_google_directory(file_path, data_types)
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_google_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Google Takeout export directory.
        
        Args:
            directory_path: Path to the Google Takeout export directory
            data_types: List of data types to extract
                
        Yields:
            Dictionaries containing normalized data
        """
        # Extract Gmail data
        if "gmail" in data_types:
            gmail_path = os.path.join(directory_path, "Mail")
            if os.path.exists(gmail_path) and os.path.isdir(gmail_path):
                yield from self._extract_gmail(gmail_path)
            
            # Try alternate location
            gmail_path = os.path.join(directory_path, "Takeout", "Mail")
            if os.path.exists(gmail_path) and os.path.isdir(gmail_path):
                yield from self._extract_gmail(gmail_path)
        
        # Extract Google Calendar data
        if "calendar" in data_types:
            calendar_path = os.path.join(directory_path, "Calendar")
            if os.path.exists(calendar_path) and os.path.isdir(calendar_path):
                yield from self._extract_calendar(calendar_path)
            
            # Try alternate location
            calendar_path = os.path.join(directory_path, "Takeout", "Calendar")
            if os.path.exists(calendar_path) and os.path.isdir(calendar_path):
                yield from self._extract_calendar(calendar_path)
        
        # Extract Google Drive data
        if "drive" in data_types:
            drive_path = os.path.join(directory_path, "Drive")
            if os.path.exists(drive_path) and os.path.isdir(drive_path):
                yield from self._extract_drive(drive_path)
            
            # Try alternate location
            drive_path = os.path.join(directory_path, "Takeout", "Drive")
            if os.path.exists(drive_path) and os.path.isdir(drive_path):
                yield from self._extract_drive(drive_path)
        
        # Extract Google Photos data
        if "photos" in data_types:
            photos_path = os.path.join(directory_path, "Google Photos")
            if os.path.exists(photos_path) and os.path.isdir(photos_path):
                yield from self._extract_photos(photos_path)
            
            # Try alternate location
            photos_path = os.path.join(directory_path, "Takeout", "Google Photos")
            if os.path.exists(photos_path) and os.path.isdir(photos_path):
                yield from self._extract_photos(photos_path)
        
        # Extract Google Contacts data
        if "contacts" in data_types:
            contacts_path = os.path.join(directory_path, "Contacts")
            if os.path.exists(contacts_path) and os.path.isdir(contacts_path):
                yield from self._extract_contacts(contacts_path)
            
            # Try alternate location
            contacts_path = os.path.join(directory_path, "Takeout", "Contacts")
            if os.path.exists(contacts_path) and os.path.isdir(contacts_path):
                yield from self._extract_contacts(contacts_path)
        
        # Extract YouTube data
        if "youtube" in data_types:
            youtube_path = os.path.join(directory_path, "YouTube and YouTube Music")
            if os.path.exists(youtube_path) and os.path.isdir(youtube_path):
                yield from self._extract_youtube(youtube_path)
            
            # Try alternate location
            youtube_path = os.path.join(directory_path, "Takeout", "YouTube and YouTube Music")
            if os.path.exists(youtube_path) and os.path.isdir(youtube_path):
                yield from self._extract_youtube(youtube_path)
        
        # Extract Google Maps data
        if "maps" in data_types:
            maps_path = os.path.join(directory_path, "Maps")
            if os.path.exists(maps_path) and os.path.isdir(maps_path):
                yield from self._extract_maps(maps_path)
            
            # Try alternate location
            maps_path = os.path.join(directory_path, "Takeout", "Maps")
            if os.path.exists(maps_path) and os.path.isdir(maps_path):
                yield from self._extract_maps(maps_path)
    
    def _extract_gmail(self, gmail_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Gmail data from a Google Takeout export.
        
        Args:
            gmail_path: Path to the Mail directory
                
        Yields:
            Dictionaries containing normalized email data
        """
        try:
            # Look for MBOX files
            mbox_files = []
            for root, _, files in os.walk(gmail_path):
                for file in files:
                    if file.endswith('.mbox'):
                        mbox_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(mbox_files)} MBOX files in Gmail export")
            
            for mbox_file in mbox_files:
                try:
                    # Get label name from file path
                    label = os.path.basename(mbox_file).replace('.mbox', '')
                    
                    # Process MBOX file
                    mbox = mailbox.mbox(mbox_file)
                    logger.info(f"Processing {len(mbox)} emails in {label} label")
                    
                    for message in mbox:
                        try:
                            # Parse email message
                            msg_id = message.get('Message-ID', '')
                            subject = message.get('Subject', '')
                            from_addr = message.get('From', '')
                            to_addr = message.get('To', '')
                            cc_addr = message.get('Cc', '')
                            bcc_addr = message.get('Bcc', '')
                            
                            # Parse date
                            date_str = message.get('Date', '')
                            timestamp = None
                            if date_str:
                                try:
                                    timestamp = parsedate_to_datetime(date_str)
                                except (ValueError, TypeError):
                                    timestamp = None
                            
                            # Get message content
                            content = ''
                            
                            # Handle multipart messages
                            if message.is_multipart():
                                for part in message.walk():
                                    content_type = part.get_content_type()
                                    if content_type == 'text/plain':
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            try:
                                                content += payload.decode('utf-8', errors='replace')
                                            except:
                                                content += str(payload)
                            else:
                                payload = message.get_payload(decode=True)
                                if payload:
                                    try:
                                        content = payload.decode('utf-8', errors='replace')
                                    except:
                                        content = str(payload)
                            
                            # Create normalized email data
                            email_data = {
                                'id': f"gmail_{msg_id}",
                                'message_id': msg_id,
                                'subject': subject,
                                'from': from_addr,
                                'to': to_addr,
                                'cc': cc_addr,
                                'bcc': bcc_addr,
                                'content': content,
                                'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                                'label': label,
                                'platform': 'gmail',
                                'type': 'email',
                                'source': 'google_takeout'
                            }
                            
                            # Apply filters
                            if self._apply_filters(email_data):
                                self.item_count += 1
                                yield email_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing Gmail message: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error processing MBOX file {mbox_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Gmail data: {str(e)}")
    
    def _extract_calendar(self, calendar_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Calendar data from a Google Takeout export.
        
        Args:
            calendar_path: Path to the Calendar directory
                
        Yields:
            Dictionaries containing normalized calendar event data
        """
        try:
            # Look for ICS files
            ics_files = []
            for root, _, files in os.walk(calendar_path):
                for file in files:
                    if file.endswith('.ics'):
                        ics_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(ics_files)} ICS files in Calendar export")
            
            for ics_file in ics_files:
                try:
                    # Get calendar name from file path
                    calendar_name = os.path.basename(ics_file).replace('.ics', '')
                    
                    # Process ICS file
                    with open(ics_file, 'r', encoding='utf-8', errors='ignore') as f:
                        ics_content = f.read()
                    
                    # Parse events using regex (simple approach)
                    event_blocks = re.split(r'BEGIN:VEVENT', ics_content)
                    
                    # Skip the first block (header)
                    event_blocks = event_blocks[1:]
                    
                    logger.info(f"Processing {len(event_blocks)} events in {calendar_name} calendar")
                    
                    for event_block in event_blocks:
                        try:
                            # Extract event properties
                            uid_match = re.search(r'UID:(.*?)(?:\r?\n)', event_block)
                            summary_match = re.search(r'SUMMARY:(.*?)(?:\r?\n)', event_block)
                            dtstart_match = re.search(r'DTSTART(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                            dtend_match = re.search(r'DTEND(?:;.+?)?:(.*?)(?:\r?\n)', event_block)
                            location_match = re.search(r'LOCATION:(.*?)(?:\r?\n)', event_block)
                            description_match = re.search(r'DESCRIPTION:(.*?)(?:\r?\n)', event_block)
                            
                            uid = uid_match.group(1) if uid_match else ''
                            summary = summary_match.group(1) if summary_match else ''
                            dtstart = dtstart_match.group(1) if dtstart_match else ''
                            dtend = dtend_match.group(1) if dtend_match else ''
                            location = location_match.group(1) if location_match else ''
                            description = description_match.group(1) if description_match else ''
                            
                            # Parse start and end times
                            start_time = None
                            end_time = None
                            
                            if dtstart:
                                try:
                                    # Handle different date formats
                                    if 'T' in dtstart:  # DateTime format
                                        start_time = datetime.strptime(dtstart, '%Y%m%dT%H%M%SZ')
                                    else:  # Date only format
                                        start_time = datetime.strptime(dtstart, '%Y%m%d')
                                except ValueError:
                                    pass
                            
                            if dtend:
                                try:
                                    # Handle different date formats
                                    if 'T' in dtend:  # DateTime format
                                        end_time = datetime.strptime(dtend, '%Y%m%dT%H%M%SZ')
                                    else:  # Date only format
                                        end_time = datetime.strptime(dtend, '%Y%m%d')
                                except ValueError:
                                    pass
                            
                            # Create normalized calendar event data
                            event_data = {
                                'id': f"gcal_event_{uid}",
                                'uid': uid,
                                'summary': summary,
                                'description': description,
                                'location': location,
                                'start_time': start_time.isoformat() if start_time else None,
                                'end_time': end_time.isoformat() if end_time else None,
                                'calendar_name': calendar_name,
                                'timestamp': start_time.isoformat() if start_time else datetime.now().isoformat(),
                                'platform': 'google_calendar',
                                'type': 'event',
                                'source': 'google_takeout'
                            }
                            
                            # Apply filters
                            if self._apply_filters(event_data):
                                self.item_count += 1
                                yield event_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing Calendar event: {str(e)}")
                
                except Exception as e:
                    logger.error(f"Error processing ICS file {ics_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Calendar data: {str(e)}")
    
    def _extract_drive(self, drive_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Drive data from a Google Takeout export.
        
        Args:
            drive_path: Path to the Drive directory
                
        Yields:
            Dictionaries containing normalized file data
        """
        try:
            # Process files and directories recursively
            for root, dirs, files in os.walk(drive_path):
                # Get relative path from drive_path
                rel_path = os.path.relpath(root, drive_path)
                if rel_path == '.':
                    rel_path = ''
                
                # Process files in current directory
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        
                        # Skip Google Drive metadata files
                        if file.endswith('.metadata.json'):
                            continue
                        
                        # Check if there's a metadata file for this file
                        metadata_path = file_path + '.metadata.json'
                        metadata = {}
                        
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except:
                                pass
                        
                        # Get file stats
                        file_stats = os.stat(file_path)
                        
                        # Get file modification time
                        mod_time = datetime.fromtimestamp(file_stats.st_mtime)
                        
                        # Get file size
                        file_size = file_stats.st_size
                        
                        # Get file type
                        file_type = os.path.splitext(file)[1].lstrip('.')
                        
                        # Create normalized file data
                        file_data = {
                            'id': f"gdrive_file_{generate_message_id({'path': os.path.join(rel_path, file)})}",
                            'name': file,
                            'path': os.path.join(rel_path, file),
                            'size': file_size,
                            'type': file_type,
                            'modified_time': mod_time.isoformat(),
                            'created_time': metadata.get('createdTime', mod_time.isoformat()),
                            'timestamp': mod_time.isoformat(),
                            'platform': 'google_drive',
                            'type': 'file',
                            'source': 'google_takeout'
                        }
                        
                        # Apply filters
                        if self._apply_filters(file_data):
                            self.item_count += 1
                            yield file_data
                    
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error processing Drive file {file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Drive data: {str(e)}")
    
    def _extract_photos(self, photos_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Photos data from a Google Takeout export.
        
        Args:
            photos_path: Path to the Google Photos directory
                
        Yields:
            Dictionaries containing normalized photo data
        """
        try:
            # Process albums and photos recursively
            for root, dirs, files in os.walk(photos_path):
                # Get album name from path
                album_name = os.path.basename(root)
                
                # Process files in current directory
                for file in files:
                    try:
                        # Skip JSON metadata files for now
                        if file.endswith('.json'):
                            continue
                        
                        file_path = os.path.join(root, file)
                        
                        # Check if there's a metadata file for this photo
                        base_name = os.path.splitext(file)[0]
                        metadata_path = os.path.join(root, base_name + '.json')
                        metadata = {}
                        
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except:
                                pass
                        
                        # Get file stats
                        file_stats = os.stat(file_path)
                        
                        # Get file modification time
                        mod_time = datetime.fromtimestamp(file_stats.st_mtime)
                        
                        # Get photo creation time from metadata
                        creation_time = None
                        if 'photoTakenTime' in metadata:
                            timestamp = metadata['photoTakenTime'].get('timestamp', '')
                            if timestamp:
                                try:
                                    creation_time = datetime.fromtimestamp(int(timestamp))
                                except (ValueError, TypeError):
                                    pass
                        
                        # Use modification time if creation time is not available
                        if not creation_time:
                            creation_time = mod_time
                        
                        # Get photo location from metadata
                        latitude = None
                        longitude = None
                        
                        if 'geoData' in metadata:
                            latitude = metadata['geoData'].get('latitude', None)
                            longitude = metadata['geoData'].get('longitude', None)
                        
                        # Create normalized photo data
                        photo_data = {
                            'id': f"gphotos_{generate_message_id({'path': file_path})}",
                            'name': file,
                            'album': album_name,
                            'creation_time': creation_time.isoformat(),
                            'latitude': latitude,
                            'longitude': longitude,
                            'timestamp': creation_time.isoformat(),
                            'platform': 'google_photos',
                            'type': 'photo',
                            'source': 'google_takeout'
                        }
                        
                        # Apply filters
                        if self._apply_filters(photo_data):
                            self.item_count += 1
                            yield photo_data
                    
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error processing Google Photos file {file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Google Photos data: {str(e)}")
    
    def _extract_contacts(self, contacts_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Contacts data from a Google Takeout export.
        
        Args:
            contacts_path: Path to the Contacts directory
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            # Look for contacts files
            contacts_files = []
            for root, _, files in os.walk(contacts_path):
                for file in files:
                    if file.endswith('.vcf') or file.endswith('.csv'):
                        contacts_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(contacts_files)} contacts files in Google Contacts export")
            
            for contacts_file in contacts_files:
                try:
                    if contacts_file.endswith('.vcf'):
                        yield from self._extract_contacts_from_vcf(contacts_file)
                    elif contacts_file.endswith('.csv'):
                        yield from self._extract_contacts_from_csv(contacts_file)
                
                except Exception as e:
                    logger.error(f"Error processing contacts file {contacts_file}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Google Contacts data: {str(e)}")
    
    def _extract_contacts_from_vcf(self, vcf_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from a VCF file.
        
        Args:
            vcf_path: Path to the VCF file
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            with open(vcf_path, 'r', encoding='utf-8', errors='ignore') as f:
                vcf_content = f.read()
            
            # Split the VCF file into individual contacts
            contacts = vcf_content.split('BEGIN:VCARD')
            contacts = [c for c in contacts if c.strip()]
            
            logger.info(f"Found {len(contacts)} contacts in VCF file")
            
            for i, contact_data in enumerate(contacts):
                try:
                    # Extract name
                    name_match = re.search(r'FN:(.*?)(?:\r?\n)', contact_data)
                    name = name_match.group(1) if name_match else f"Unknown Contact {i+1}"
                    
                    # Extract email addresses
                    email_matches = re.findall(r'EMAIL[^:]*:(.*?)(?:\r?\n)', contact_data)
                    emails = email_matches if email_matches else []
                    
                    # Extract phone numbers
                    phone_matches = re.findall(r'TEL[^:]*:(.*?)(?:\r?\n)', contact_data)
                    phones = phone_matches if phone_matches else []
                    
                    # Extract address
                    address_match = re.search(r'ADR[^:]*:(.*?)(?:\r?\n)', contact_data)
                    address = address_match.group(1) if address_match else ''
                    
                    # Extract organization
                    org_match = re.search(r'ORG:(.*?)(?:\r?\n)', contact_data)
                    organization = org_match.group(1) if org_match else ''
                    
                    # Extract title
                    title_match = re.search(r'TITLE:(.*?)(?:\r?\n)', contact_data)
                    title = title_match.group(1) if title_match else ''
                    
                    # Create normalized contact data
                    contact = {
                        'id': f"gcontact_{generate_message_id({'name': name})}",
                        'name': name,
                        'emails': emails,
                        'phones': phones,
                        'address': address,
                        'organization': organization,
                        'title': title,
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'google_contacts',
                        'type': 'contact',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact):
                        self.item_count += 1
                        yield contact
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing contact from VCF: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting contacts from VCF file: {str(e)}")
    
    def _extract_contacts_from_csv(self, csv_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract contacts from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
                
        Yields:
            Dictionaries containing normalized contact data
        """
        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                contacts = list(reader)
            
            logger.info(f"Found {len(contacts)} contacts in CSV file")
            
            for contact in contacts:
                try:
                    # Extract name components
                    name_components = []
                    if 'Name' in contact and contact['Name']:
                        name_components.append(contact['Name'])
                    elif 'Given Name' in contact and contact['Given Name']:
                        if 'Family Name' in contact and contact['Family Name']:
                            name_components.append(f"{contact['Given Name']} {contact['Family Name']}")
                        else:
                            name_components.append(contact['Given Name'])
                    
                    name = ' '.join(name_components) if name_components else 'Unknown Contact'
                    
                    # Extract emails
                    emails = []
                    for key in contact:
                        if 'E-mail' in key and contact[key]:
                            emails.append(contact[key])
                    
                    # Extract phones
                    phones = []
                    for key in contact:
                        if 'Phone' in key and contact[key]:
                            phones.append(contact[key])
                    
                    # Extract address components
                    address_components = []
                    for key in ['Address', 'Street', 'City', 'State', 'Postal Code', 'Country']:
                        if key in contact and contact[key]:
                            address_components.append(contact[key])
                    
                    address = ', '.join(address_components) if address_components else ''
                    
                    # Extract organization
                    organization = contact.get('Organization', '')
                    
                    # Extract title
                    title = contact.get('Title', '')
                    
                    # Create normalized contact data
                    contact_data = {
                        'id': f"gcontact_{generate_message_id({'name': name})}",
                        'name': name,
                        'emails': emails,
                        'phones': phones,
                        'address': address,
                        'organization': organization,
                        'title': title,
                        'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                        'platform': 'google_contacts',
                        'type': 'contact',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(contact_data):
                        self.item_count += 1
                        yield contact_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing contact from CSV: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting contacts from CSV file: {str(e)}")
    
    def _extract_youtube(self, youtube_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract YouTube data from a Google Takeout export.
        
        Args:
            youtube_path: Path to the YouTube directory
                
        Yields:
            Dictionaries containing normalized YouTube data
        """
        try:
            # Look for different YouTube data files
            watch_history_path = os.path.join(youtube_path, 'history', 'watch-history.json')
            search_history_path = os.path.join(youtube_path, 'history', 'search-history.json')
            subscriptions_path = os.path.join(youtube_path, 'subscriptions', 'subscriptions.json')
            
            # Extract watch history
            if os.path.exists(watch_history_path):
                yield from self._extract_youtube_watch_history(watch_history_path)
            
            # Extract search history
            if os.path.exists(search_history_path):
                yield from self._extract_youtube_search_history(search_history_path)
            
            # Extract subscriptions
            if os.path.exists(subscriptions_path):
                yield from self._extract_youtube_subscriptions(subscriptions_path)
        
        except Exception as e:
            logger.error(f"Error extracting YouTube data: {str(e)}")
    
    def _extract_youtube_watch_history(self, history_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract YouTube watch history from a JSON file.
        
        Args:
            history_path: Path to the watch-history.json file
                
        Yields:
            Dictionaries containing normalized watch history data
        """
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            logger.info(f"Found {len(history_data)} entries in YouTube watch history")
            
            for entry in history_data:
                try:
                    # Parse timestamp
                    timestamp = None
                    time_str = entry.get('time', '')
                    if time_str:
                        timestamp = parse_datetime(time_str)
                    
                    # Get video title
                    title = entry.get('title', '')
                    
                    # Get video URL
                    url = ''
                    for detail in entry.get('details', []):
                        if detail.get('name') == 'From Google Ads':
                            continue
                        url = detail.get('url', '')
                        if url:
                            break
                    
                    # Get channel name
                    subtitles = entry.get('subtitles', [])
                    channel = subtitles[0].get('name', '') if subtitles else ''
                    
                    # Create normalized watch history data
                    watch_data = {
                        'id': f"youtube_watch_{generate_message_id(entry)}",
                        'title': title,
                        'url': url,
                        'channel': channel,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'youtube',
                        'type': 'watch_history',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(watch_data):
                        self.item_count += 1
                        yield watch_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing YouTube watch history entry: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting YouTube watch history: {str(e)}")
    
    def _extract_youtube_search_history(self, history_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract YouTube search history from a JSON file.
        
        Args:
            history_path: Path to the search-history.json file
                
        Yields:
            Dictionaries containing normalized search history data
        """
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            logger.info(f"Found {len(history_data)} entries in YouTube search history")
            
            for entry in history_data:
                try:
                    # Parse timestamp
                    timestamp = None
                    time_str = entry.get('time', '')
                    if time_str:
                        timestamp = parse_datetime(time_str)
                    
                    # Get search query
                    title = entry.get('title', '')
                    query = title.replace('Searched for ', '') if title.startswith('Searched for ') else title
                    
                    # Create normalized search history data
                    search_data = {
                        'id': f"youtube_search_{generate_message_id(entry)}",
                        'query': query,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'youtube',
                        'type': 'search_history',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(search_data):
                        self.item_count += 1
                        yield search_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing YouTube search history entry: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting YouTube search history: {str(e)}")
    
    def _extract_youtube_subscriptions(self, subscriptions_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract YouTube subscriptions from a JSON file.
        
        Args:
            subscriptions_path: Path to the subscriptions.json file
                
        Yields:
            Dictionaries containing normalized subscription data
        """
        try:
            with open(subscriptions_path, 'r', encoding='utf-8') as f:
                subscriptions_data = json.load(f)
            
            logger.info(f"Found {len(subscriptions_data)} YouTube subscriptions")
            
            for subscription in subscriptions_data:
                try:
                    # Get channel name
                    channel_name = subscription.get('snippet', {}).get('title', '')
                    
                    # Get channel ID
                    channel_id = subscription.get('snippet', {}).get('resourceId', {}).get('channelId', '')
                    
                    # Get subscription date
                    timestamp = None
                    time_str = subscription.get('snippet', {}).get('publishedAt', '')
                    if time_str:
                        timestamp = parse_datetime(time_str)
                    
                    # Create normalized subscription data
                    subscription_data = {
                        'id': f"youtube_subscription_{channel_id}",
                        'channel_name': channel_name,
                        'channel_id': channel_id,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'youtube',
                        'type': 'subscription',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(subscription_data):
                        self.item_count += 1
                        yield subscription_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing YouTube subscription: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting YouTube subscriptions: {str(e)}")
    
    def _extract_maps(self, maps_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Maps data from a Google Takeout export.
        
        Args:
            maps_path: Path to the Maps directory
                
        Yields:
            Dictionaries containing normalized Maps data
        """
        try:
            # Look for different Maps data files
            location_history_path = os.path.join(maps_path, 'Location History', 'Location History.json')
            saved_places_path = os.path.join(maps_path, 'Saved Places', 'Saved Places.json')
            
            # Extract location history
            if os.path.exists(location_history_path):
                yield from self._extract_location_history(location_history_path)
            
            # Extract saved places
            if os.path.exists(saved_places_path):
                yield from self._extract_saved_places(saved_places_path)
        
        except Exception as e:
            logger.error(f"Error extracting Google Maps data: {str(e)}")
    
    def _extract_location_history(self, history_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Maps location history from a JSON file.
        
        Args:
            history_path: Path to the Location History.json file
                
        Yields:
            Dictionaries containing normalized location history data
        """
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            locations = history_data.get('locations', [])
            logger.info(f"Found {len(locations)} entries in Google Maps location history")
            
            # Sample the location history (can be very large)
            sample_size = min(1000, len(locations))
            sample_step = max(1, len(locations) // sample_size)
            
            for i in range(0, len(locations), sample_step):
                try:
                    location = locations[i]
                    
                    # Parse timestamp
                    timestamp = None
                    timestamp_ms = location.get('timestampMs', '')
                    if timestamp_ms:
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_ms) / 1000)
                        except (ValueError, TypeError):
                            pass
                    
                    # Get coordinates
                    latitude = float(location.get('latitudeE7', 0)) / 1e7
                    longitude = float(location.get('longitudeE7', 0)) / 1e7
                    
                    # Get accuracy
                    accuracy = location.get('accuracy', 0)
                    
                    # Create normalized location history data
                    location_data = {
                        'id': f"gmaps_location_{timestamp_ms}",
                        'latitude': latitude,
                        'longitude': longitude,
                        'accuracy': accuracy,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'google_maps',
                        'type': 'location_history',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(location_data):
                        self.item_count += 1
                        yield location_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Google Maps location history entry: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Google Maps location history: {str(e)}")
    
    def _extract_saved_places(self, places_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract Google Maps saved places from a JSON file.
        
        Args:
            places_path: Path to the Saved Places.json file
                
        Yields:
            Dictionaries containing normalized saved places data
        """
        try:
            with open(places_path, 'r', encoding='utf-8') as f:
                places_data = json.load(f)
            
            features = places_data.get('features', [])
            logger.info(f"Found {len(features)} saved places in Google Maps")
            
            for feature in features:
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # Get place name
                    name = properties.get('Title', '')
                    
                    # Get coordinates
                    coordinates = geometry.get('coordinates', [0, 0])
                    longitude, latitude = coordinates
                    
                    # Get place details
                    address = properties.get('Location', {}).get('Address', '')
                    category = properties.get('Location', {}).get('Business Type', '')
                    
                    # Parse timestamp
                    timestamp = None
                    time_str = properties.get('Create Time', '')
                    if time_str:
                        timestamp = parse_datetime(time_str)
                    
                    # Create normalized saved place data
                    place_data = {
                        'id': f"gmaps_place_{generate_message_id({'name': name, 'address': address})}",
                        'name': name,
                        'address': address,
                        'category': category,
                        'latitude': latitude,
                        'longitude': longitude,
                        'timestamp': timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        'platform': 'google_maps',
                        'type': 'saved_place',
                        'source': 'google_takeout'
                    }
                    
                    # Apply filters
                    if self._apply_filters(place_data):
                        self.item_count += 1
                        yield place_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing Google Maps saved place: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting Google Maps saved places: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
                
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Google data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item