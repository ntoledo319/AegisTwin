"""
Spotify Connector for CogniLink

This module provides functionality to import data from Spotify data exports,
including listening history, playlists, and user profile information.
"""

import os
import json
import logging
import zipfile
import csv
from typing import Dict, List, Any, Optional, Iterator
from datetime import datetime

from cognilink.pipeline.connectors.base_connector import BaseConnector
from cognilink.core.utils import parse_datetime

logger = logging.getLogger(__name__)

class SpotifyConnector(BaseConnector):
    """
    Connector for importing Spotify data.
    
    This class handles extraction of listening history, playlists, and user profile
    information from Spotify data exports.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Spotify connector.
        
        Args:
            config: Configuration dictionary for the connector
        """
        super().__init__(config)
        self.platform_name = "spotify"
        self.user_info = {}
    
    def extract_from_file(self, file_path: str, data_types: List[str] = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Extract data from a Spotify data export file.
        
        Args:
            file_path: Path to the Spotify data export file (ZIP or directory)
            data_types: List of data types to extract (e.g., ["history", "playlists", "profile"])
            **kwargs: Additional arguments
            
        Yields:
            Dictionaries containing normalized data
        """
        # Default to extracting all data types if none specified
        data_types = data_types or ["history", "playlists", "profile", "library"]
        
        # Handle ZIP file
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to a temporary directory
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    yield from self._process_spotify_directory(temp_dir, data_types)
        
        # Handle directory
        elif os.path.isdir(file_path):
            yield from self._process_spotify_directory(file_path, data_types)
        
        # Handle single JSON file (might be a specific export type)
        elif file_path.endswith('.json'):
            file_name = os.path.basename(file_path).lower()
            
            if "history" in data_types and ("streaminghistory" in file_name or "endsong" in file_name):
                yield from self._extract_listening_history(file_path)
            
            elif "playlists" in data_types and "playlists" in file_name:
                yield from self._extract_playlists(file_path)
            
            elif "profile" in data_types and "profile" in file_name:
                yield from self._extract_profile(file_path)
            
            elif "library" in data_types and "library" in file_name:
                yield from self._extract_library(file_path)
            
            else:
                logger.warning(f"Unrecognized Spotify JSON file: {file_path}")
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
    
    def _process_spotify_directory(self, directory_path: str, data_types: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Process a Spotify data export directory.
        
        Args:
            directory_path: Path to the Spotify data export directory
            data_types: List of data types to extract
            
        Yields:
            Dictionaries containing normalized data
        """
        # First, load user profile information
        if "profile" in data_types:
            # Try different possible paths for profile data
            profile_paths = [
                os.path.join(directory_path, "MyData", "Profile.json"),
                os.path.join(directory_path, "Profile.json"),
                os.path.join(directory_path, "profile.json")
            ]
            
            for profile_path in profile_paths:
                if os.path.exists(profile_path):
                    yield from self._extract_profile(profile_path)
                    break
        
        # Extract listening history
        if "history" in data_types:
            # Spotify provides streaming history in multiple files
            history_files = []
            
            # Check for old format (StreamingHistory*.json)
            for i in range(10):  # Check up to 10 files
                history_path = os.path.join(directory_path, f"MyData", f"StreamingHistory{i}.json")
                if os.path.exists(history_path):
                    history_files.append(history_path)
                
                # Also check in root directory
                history_path = os.path.join(directory_path, f"StreamingHistory{i}.json")
                if os.path.exists(history_path):
                    history_files.append(history_path)
            
            # Check for new format (endsong_*.json)
            for i in range(10):  # Check up to 10 files
                history_path = os.path.join(directory_path, f"MyData", f"endsong_{i}.json")
                if os.path.exists(history_path):
                    history_files.append(history_path)
                
                # Also check in root directory
                history_path = os.path.join(directory_path, f"endsong_{i}.json")
                if os.path.exists(history_path):
                    history_files.append(history_path)
            
            # Process each history file
            for history_path in history_files:
                yield from self._extract_listening_history(history_path)
        
        # Extract playlists
        if "playlists" in data_types:
            playlist_paths = [
                os.path.join(directory_path, "MyData", "Playlists.json"),
                os.path.join(directory_path, "Playlists.json"),
                os.path.join(directory_path, "playlists.json")
            ]
            
            for playlist_path in playlist_paths:
                if os.path.exists(playlist_path):
                    yield from self._extract_playlists(playlist_path)
                    break
        
        # Extract library (saved tracks, albums, etc.)
        if "library" in data_types:
            library_paths = [
                os.path.join(directory_path, "MyData", "YourLibrary.json"),
                os.path.join(directory_path, "YourLibrary.json"),
                os.path.join(directory_path, "your_library.json")
            ]
            
            for library_path in library_paths:
                if os.path.exists(library_path):
                    yield from self._extract_library(library_path)
                    break
    
    def _extract_profile(self, profile_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract user profile information from a Spotify profile JSON file.
        
        Args:
            profile_path: Path to the profile JSON file
            
        Yields:
            Normalized profile data
        """
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Store user info for later use
            self.user_info = profile_data
            
            # Create normalized profile data
            profile = {
                'id': f"spotify_profile_{profile_data.get('username', '')}",
                'username': profile_data.get('username', ''),
                'display_name': profile_data.get('displayName', ''),
                'email': profile_data.get('email', ''),
                'country': profile_data.get('country', ''),
                'created_at': profile_data.get('createdFromFacebook', False),
                'birthdate': profile_data.get('birthdate', ''),
                'follower_count': profile_data.get('followerCount', 0),
                'following_count': profile_data.get('followingCount', 0),
                'timestamp': datetime.now().isoformat(),  # Use current time as we don't have a specific timestamp
                'platform': 'spotify',
                'type': 'profile',
                'source': 'spotify_export'
            }
            
            # Apply filters
            if self._apply_filters(profile):
                self.item_count += 1
                yield profile
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing Spotify profile: {str(e)}")
    
    def _extract_listening_history(self, history_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract listening history from a Spotify history JSON file.
        
        Args:
            history_path: Path to the history JSON file
            
        Yields:
            Dictionaries containing normalized listening history data
        """
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            logger.info(f"Found {len(history_data)} listening events in {history_path}")
            
            # Determine if this is the new format (endsong) or old format (StreamingHistory)
            is_new_format = "endsong" in os.path.basename(history_path).lower()
            
            for i, item in enumerate(history_data):
                try:
                    # Extract data based on format
                    if is_new_format:
                        # New format (endsong)
                        track_name = item.get('master_metadata_track_name', item.get('track_name', ''))
                        artist_name = item.get('master_metadata_album_artist_name', item.get('artist_name', ''))
                        album_name = item.get('master_metadata_album_album_name', item.get('album_name', ''))
                        ms_played = item.get('ms_played', 0)
                        timestamp_str = item.get('ts', '')
                        reason_start = item.get('reason_start', '')
                        reason_end = item.get('reason_end', '')
                        shuffle = item.get('shuffle', False)
                        skipped = reason_end == 'skipped'
                        
                        # Additional fields in new format
                        spotify_track_uri = item.get('spotify_track_uri', '')
                        spotify_episode_uri = item.get('spotify_episode_uri', '')
                        episode_name = item.get('episode_name', '')
                        episode_show_name = item.get('episode_show_name', '')
                        
                        # Determine if this is a podcast or music
                        is_podcast = bool(episode_name or episode_show_name or spotify_episode_uri)
                        
                    else:
                        # Old format (StreamingHistory)
                        track_name = item.get('trackName', '')
                        artist_name = item.get('artistName', '')
                        album_name = ''  # Not available in old format
                        ms_played = item.get('msPlayed', 0)
                        timestamp_str = item.get('endTime', '')
                        reason_start = ''  # Not available in old format
                        reason_end = ''  # Not available in old format
                        shuffle = False  # Not available in old format
                        skipped = False  # Not available in old format
                        spotify_track_uri = ''  # Not available in old format
                        spotify_episode_uri = ''  # Not available in old format
                        episode_name = ''  # Not available in old format
                        episode_show_name = ''  # Not available in old format
                        is_podcast = False  # Can't determine in old format
                    
                    # Parse timestamp
                    timestamp = parse_datetime(timestamp_str) if timestamp_str else datetime.now()
                    
                    # Create normalized listening history data
                    history_item = {
                        'id': f"spotify_listen_{os.path.basename(history_path)}_{i}",
                        'track_name': track_name,
                        'artist_name': artist_name,
                        'album_name': album_name,
                        'ms_played': ms_played,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'reason_start': reason_start,
                        'reason_end': reason_end,
                        'shuffle': shuffle,
                        'skipped': skipped,
                        'spotify_track_uri': spotify_track_uri,
                        'spotify_episode_uri': spotify_episode_uri,
                        'episode_name': episode_name,
                        'episode_show_name': episode_show_name,
                        'is_podcast': is_podcast,
                        'platform': 'spotify',
                        'type': 'listening_history',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(history_item):
                        self.item_count += 1
                        yield history_item
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing listening history item: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting listening history from {history_path}: {str(e)}")
    
    def _extract_playlists(self, playlists_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract playlists from a Spotify playlists JSON file.
        
        Args:
            playlists_path: Path to the playlists JSON file
            
        Yields:
            Dictionaries containing normalized playlist and track data
        """
        try:
            with open(playlists_path, 'r', encoding='utf-8') as f:
                playlists_data = json.load(f)
            
            # Handle different formats
            if isinstance(playlists_data, dict) and 'playlists' in playlists_data:
                playlists = playlists_data['playlists']
            else:
                playlists = playlists_data
            
            logger.info(f"Found {len(playlists)} playlists in {playlists_path}")
            
            for playlist in playlists:
                try:
                    playlist_name = playlist.get('name', '')
                    playlist_description = playlist.get('description', '')
                    playlist_id = playlist.get('id', '')
                    last_modified = playlist.get('lastModifiedDate', '')
                    
                    # Parse timestamp
                    timestamp = parse_datetime(last_modified) if last_modified else datetime.now()
                    
                    # Get tracks
                    tracks = playlist.get('items', [])
                    
                    # Create normalized playlist data
                    playlist_data = {
                        'id': f"spotify_playlist_{playlist_id}",
                        'name': playlist_name,
                        'description': playlist_description,
                        'track_count': len(tracks),
                        'last_modified': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'spotify',
                        'type': 'playlist',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(playlist_data):
                        self.item_count += 1
                        yield playlist_data
                    
                    # Process each track in the playlist
                    for i, track in enumerate(tracks):
                        try:
                            track_name = track.get('track', {}).get('trackName', '')
                            artist_name = track.get('track', {}).get('artistName', '')
                            album_name = track.get('track', {}).get('albumName', '')
                            
                            # Create normalized track data
                            track_data = {
                                'id': f"spotify_playlist_track_{playlist_id}_{i}",
                                'playlist_id': playlist_id,
                                'playlist_name': playlist_name,
                                'track_name': track_name,
                                'artist_name': artist_name,
                                'album_name': album_name,
                                'position': i,
                                'timestamp': timestamp.isoformat() if timestamp else None,
                                'platform': 'spotify',
                                'type': 'playlist_track',
                                'source': 'spotify_export'
                            }
                            
                            # Apply filters
                            if self._apply_filters(track_data):
                                self.item_count += 1
                                yield track_data
                        
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"Error processing playlist track: {str(e)}")
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing playlist: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting playlists from {playlists_path}: {str(e)}")
    
    def _extract_library(self, library_path: str) -> Iterator[Dict[str, Any]]:
        """
        Extract library items from a Spotify library JSON file.
        
        Args:
            library_path: Path to the library JSON file
            
        Yields:
            Dictionaries containing normalized library item data
        """
        try:
            with open(library_path, 'r', encoding='utf-8') as f:
                library_data = json.load(f)
            
            # Process tracks
            tracks = library_data.get('tracks', [])
            logger.info(f"Found {len(tracks)} saved tracks in library")
            
            for i, track in enumerate(tracks):
                try:
                    track_name = track.get('track', '')
                    artist_name = track.get('artist', '')
                    album_name = track.get('album', '')
                    added_at = track.get('addedAt', '')
                    
                    # Parse timestamp
                    timestamp = parse_datetime(added_at) if added_at else datetime.now()
                    
                    # Create normalized track data
                    track_data = {
                        'id': f"spotify_saved_track_{i}",
                        'track_name': track_name,
                        'artist_name': artist_name,
                        'album_name': album_name,
                        'added_at': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'spotify',
                        'type': 'saved_track',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(track_data):
                        self.item_count += 1
                        yield track_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing saved track: {str(e)}")
            
            # Process albums
            albums = library_data.get('albums', [])
            logger.info(f"Found {len(albums)} saved albums in library")
            
            for i, album in enumerate(albums):
                try:
                    album_name = album.get('album', '')
                    artist_name = album.get('artist', '')
                    added_at = album.get('addedAt', '')
                    
                    # Parse timestamp
                    timestamp = parse_datetime(added_at) if added_at else datetime.now()
                    
                    # Create normalized album data
                    album_data = {
                        'id': f"spotify_saved_album_{i}",
                        'album_name': album_name,
                        'artist_name': artist_name,
                        'added_at': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'spotify',
                        'type': 'saved_album',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(album_data):
                        self.item_count += 1
                        yield album_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing saved album: {str(e)}")
            
            # Process artists
            artists = library_data.get('artists', [])
            logger.info(f"Found {len(artists)} followed artists in library")
            
            for i, artist in enumerate(artists):
                try:
                    artist_name = artist.get('name', '')
                    added_at = artist.get('addedAt', '')
                    
                    # Parse timestamp
                    timestamp = parse_datetime(added_at) if added_at else datetime.now()
                    
                    # Create normalized artist data
                    artist_data = {
                        'id': f"spotify_followed_artist_{i}",
                        'artist_name': artist_name,
                        'added_at': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'spotify',
                        'type': 'followed_artist',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(artist_data):
                        self.item_count += 1
                        yield artist_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing followed artist: {str(e)}")
            
            # Process shows (podcasts)
            shows = library_data.get('shows', [])
            logger.info(f"Found {len(shows)} followed shows in library")
            
            for i, show in enumerate(shows):
                try:
                    show_name = show.get('name', '')
                    publisher = show.get('publisher', '')
                    added_at = show.get('addedAt', '')
                    
                    # Parse timestamp
                    timestamp = parse_datetime(added_at) if added_at else datetime.now()
                    
                    # Create normalized show data
                    show_data = {
                        'id': f"spotify_followed_show_{i}",
                        'show_name': show_name,
                        'publisher': publisher,
                        'added_at': timestamp.isoformat() if timestamp else None,
                        'timestamp': timestamp.isoformat() if timestamp else None,
                        'platform': 'spotify',
                        'type': 'followed_show',
                        'source': 'spotify_export'
                    }
                    
                    # Apply filters
                    if self._apply_filters(show_data):
                        self.item_count += 1
                        yield show_data
                
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"Error processing followed show: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error extracting library from {library_path}: {str(e)}")
    
    def _normalize_item(self, item: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Normalize an item from the source format to the CogniLink format.
        
        Args:
            item: Item data from the source
            **kwargs: Additional arguments specific to the connector
            
        Returns:
            Normalized item dictionary or None if the item should be skipped
        """
        # This method is not used directly for Spotify data as we normalize
        # during extraction, but we implement it to satisfy the abstract method
        return item