"""
Advanced Connectors Example for CogniLink

This script demonstrates how to use the advanced connectors in CogniLink
to import data from various sources like iOS backups, Twitter, Spotify, and dating apps.
"""

import os
import sys
import logging
from datetime import datetime

# Add the parent directory to the path so we can import cognilink
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cognilink.core.utils import setup_logging
from cognilink.core.comm_graph import CommunicationGraph
from cognilink.pipeline.connectors import (
    IOSBackupConnector,
    TwitterConnector,
    SpotifyConnector,
    TinderConnector
)
from cognilink.analysis.patterns import CommunicationPatternAnalyzer
from cognilink.analysis.relationships import RelationshipAnalyzer
from cognilink.analysis.topics import TopicAnalyzer
from cognilink.interface.reports import ReportGenerator

def main():
    """Run the advanced connectors example."""
    # Set up logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting CogniLink advanced connectors example")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize communication graph
    comm_graph = CommunicationGraph()
    
    # Define sample data paths (these are placeholders - replace with actual paths)
    ios_backup_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'ios_backup')
    twitter_export_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'twitter_export.zip')
    spotify_export_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'spotify_export.zip')
    tinder_export_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'tinder_export.json')
    
    # Check which sample data files exist
    available_data = []
    if os.path.exists(ios_backup_path):
        available_data.append(("iOS Backup", ios_backup_path))
    if os.path.exists(twitter_export_path):
        available_data.append(("Twitter Export", twitter_export_path))
    if os.path.exists(spotify_export_path):
        available_data.append(("Spotify Export", spotify_export_path))
    if os.path.exists(tinder_export_path):
        available_data.append(("Tinder Export", tinder_export_path))
    
    if not available_data:
        logger.warning("No sample data files found. This example requires sample data to demonstrate the connectors.")
        logger.info("You can provide your own data files by placing them in the data/sample directory.")
        logger.info("Example paths:")
        logger.info(f"  iOS Backup: {ios_backup_path}")
        logger.info(f"  Twitter Export: {twitter_export_path}")
        logger.info(f"  Spotify Export: {spotify_export_path}")
        logger.info(f"  Tinder Export: {tinder_export_path}")
        return
    
    logger.info(f"Found {len(available_data)} sample data files")
    
    # Process each available data source
    for data_name, data_path in available_data:
        logger.info(f"Processing {data_name} from {data_path}")
        
        if "iOS Backup" in data_name:
            process_ios_backup(data_path, comm_graph)
        elif "Twitter" in data_name:
            process_twitter_export(data_path, comm_graph)
        elif "Spotify" in data_name:
            process_spotify_export(data_path, comm_graph)
        elif "Tinder" in data_name:
            process_tinder_export(data_path, comm_graph)
    
    # Save communication graph
    graph_path = os.path.join(output_dir, 'advanced_connectors_graph.json')
    comm_graph.save_to_file(graph_path)
    logger.info(f"Communication graph saved to {graph_path}")
    
    # Analyze the data
    logger.info("Analyzing communication patterns")
    pattern_analyzer = CommunicationPatternAnalyzer(comm_graph)
    pattern_results = pattern_analyzer.generate_comprehensive_report()
    
    logger.info("Analyzing relationships")
    relationship_analyzer = RelationshipAnalyzer(comm_graph)
    relationship_results = relationship_analyzer.generate_comprehensive_report()
    
    logger.info("Analyzing topics")
    topic_analyzer = TopicAnalyzer()
    
    # Extract text content from communications
    texts = []
    timestamps = []
    
    for source, target, data in comm_graph.graph.edges(data=True):
        if 'content' in data:
            texts.append(data['content'])
            
            # Try to get timestamp
            try:
                timestamp = datetime.fromisoformat(data.get('first_comm'))
                timestamps.append(timestamp)
            except (ValueError, TypeError):
                timestamps.append(datetime.now())
    
    topic_results = topic_analyzer.generate_comprehensive_report(texts, timestamps)
    
    # Combine results
    analysis_results = {
        'patterns': pattern_results,
        'relationships': relationship_results,
        'topics': topic_results
    }
    
    # Generate reports
    logger.info("Generating reports")
    report_generator = ReportGenerator()
    
    # Generate HTML report
    html_path = os.path.join(output_dir, 'advanced_connectors_report.html')
    report_generator.generate_html_report(analysis_results, html_path)
    logger.info(f"HTML report saved to {html_path}")
    
    # Generate Markdown report
    md_path = os.path.join(output_dir, 'advanced_connectors_report.md')
    report_generator.generate_markdown_report(analysis_results, md_path)
    logger.info(f"Markdown report saved to {md_path}")
    
    logger.info("Advanced connectors example completed successfully")

def process_ios_backup(backup_path: str, comm_graph: CommunicationGraph) -> None:
    """
    Process an iOS backup and add data to the communication graph.
    
    Args:
        backup_path: Path to the iOS backup directory
        comm_graph: Communication graph to add data to
    """
    logger = logging.getLogger(__name__)
    logger.info("Processing iOS backup")
    
    # Initialize iOS backup connector
    ios_connector = IOSBackupConnector()
    
    # Extract messages from the backup
    for message_data in ios_connector.extract_from_file(backup_path, data_types=["messages"]):
        try:
            # Parse timestamp
            timestamp = None
            if 'timestamp' in message_data and message_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(message_data['timestamp'])
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Add to communication graph
            sender = message_data.get('sender', 'unknown')
            recipient = message_data.get('recipient', 'unknown')
            
            # Skip if no sender or recipient
            if not sender or not recipient:
                continue
            
            message_id = message_data.get('id', '')
            
            # Add communication to graph
            metadata = {
                'type': 'message',
                'platform': 'ios',
                'content': message_data.get('content', '')
            }
            
            comm_graph.add_communication(sender, [recipient], timestamp, message_id, metadata)
        
        except Exception as e:
            logger.error(f"Error processing iOS message: {str(e)}")
    
    logger.info(f"Processed {ios_connector.item_count} iOS messages")

def process_twitter_export(export_path: str, comm_graph: CommunicationGraph) -> None:
    """
    Process a Twitter export and add data to the communication graph.
    
    Args:
        export_path: Path to the Twitter export file
        comm_graph: Communication graph to add data to
    """
    logger = logging.getLogger(__name__)
    logger.info("Processing Twitter export")
    
    # Initialize Twitter connector
    twitter_connector = TwitterConnector()
    
    # Extract direct messages from the export
    for message_data in twitter_connector.extract_from_file(export_path, data_types=["dms"]):
        try:
            # Only process direct messages
            if message_data.get('type') != 'direct_message':
                continue
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in message_data and message_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(message_data['timestamp'])
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Add to communication graph
            sender = message_data.get('sender', 'unknown')
            recipient = message_data.get('recipient', 'unknown')
            
            # Skip if no sender or recipient
            if not sender or not recipient:
                continue
            
            message_id = message_data.get('id', '')
            
            # Add communication to graph
            metadata = {
                'type': 'message',
                'platform': 'twitter',
                'content': message_data.get('content', '')
            }
            
            comm_graph.add_communication(sender, [recipient], timestamp, message_id, metadata)
        
        except Exception as e:
            logger.error(f"Error processing Twitter message: {str(e)}")
    
    logger.info(f"Processed {twitter_connector.item_count} Twitter items")

def process_spotify_export(export_path: str, comm_graph: CommunicationGraph) -> None:
    """
    Process a Spotify export and add data to the communication graph.
    
    Args:
        export_path: Path to the Spotify export file
        comm_graph: Communication graph to add data to
    """
    logger = logging.getLogger(__name__)
    logger.info("Processing Spotify export")
    
    # Initialize Spotify connector
    spotify_connector = SpotifyConnector()
    
    # Extract listening history from the export
    for history_data in spotify_connector.extract_from_file(export_path, data_types=["history"]):
        try:
            # Only process listening history
            if history_data.get('type') != 'listening_history':
                continue
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in history_data and history_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(history_data['timestamp'])
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # For Spotify listening history, we'll create a special kind of communication
            # where the "sender" is the artist and the "recipient" is the user
            sender = history_data.get('artist_name', 'unknown')
            recipient = 'me'
            
            # Skip if no sender
            if not sender:
                continue
            
            message_id = history_data.get('id', '')
            
            # Create content from track information
            content = f"Track: {history_data.get('track_name', '')}\nAlbum: {history_data.get('album_name', '')}"
            
            # Add communication to graph
            metadata = {
                'type': 'listening',
                'platform': 'spotify',
                'content': content,
                'track_name': history_data.get('track_name', ''),
                'album_name': history_data.get('album_name', ''),
                'ms_played': history_data.get('ms_played', 0)
            }
            
            comm_graph.add_communication(sender, [recipient], timestamp, message_id, metadata)
        
        except Exception as e:
            logger.error(f"Error processing Spotify history: {str(e)}")
    
    logger.info(f"Processed {spotify_connector.item_count} Spotify items")

def process_tinder_export(export_path: str, comm_graph: CommunicationGraph) -> None:
    """
    Process a Tinder export and add data to the communication graph.
    
    Args:
        export_path: Path to the Tinder export file
        comm_graph: Communication graph to add data to
    """
    logger = logging.getLogger(__name__)
    logger.info("Processing Tinder export")
    
    # Initialize Tinder connector
    tinder_connector = TinderConnector()
    
    # Extract messages from the export
    for message_data in tinder_connector.extract_from_file(export_path, data_types=["messages"]):
        try:
            # Only process messages
            if message_data.get('type') != 'message':
                continue
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in message_data and message_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(message_data['timestamp'])
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Add to communication graph
            sender = message_data.get('sender', 'unknown')
            recipient = message_data.get('recipient', 'unknown')
            
            # Skip if no sender or recipient
            if not sender or not recipient:
                continue
            
            message_id = message_data.get('id', '')
            
            # Add communication to graph
            metadata = {
                'type': 'message',
                'platform': 'tinder',
                'content': message_data.get('content', ''),
                'match_id': message_data.get('match_id', '')
            }
            
            comm_graph.add_communication(sender, [recipient], timestamp, message_id, metadata)
        
        except Exception as e:
            logger.error(f"Error processing Tinder message: {str(e)}")
    
    logger.info(f"Processed {tinder_connector.item_count} Tinder items")

if __name__ == '__main__':
    main()