"""
Advanced Usage Example for CogniLink

This script demonstrates more advanced usage of CogniLink, including:
- Custom configuration
- Filtering data during import
- Advanced analysis options
- Customized reporting
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import cognilink
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cognilink.core.utils import setup_logging
from cognilink.core.config import get_config_manager, ConfigManager
from cognilink.core.comm_graph import CommunicationGraph
from cognilink.pipeline.connectors.email_connector import EmailConnector
from cognilink.pipeline.connectors.message_connector import MessageConnector
from cognilink.pipeline.processors.text_processor import TextProcessor
from cognilink.analysis.patterns import CommunicationPatternAnalyzer
from cognilink.analysis.relationships import RelationshipAnalyzer
from cognilink.analysis.topics import TopicAnalyzer
from cognilink.interface.reports import ReportGenerator

def create_custom_config():
    """Create custom configuration for the example."""
    # Create a custom configuration
    config = {
        'connectors': {
            'email': {
                'max_emails': 100,
                'filters': {
                    'min_date': (datetime.now() - timedelta(days=30)).isoformat(),
                    'exclude_domains': ['spam.example.com', 'newsletter.example.com'],
                    'min_content_length': 10
                }
            },
            'message': {
                'max_messages': 100,
                'filters': {
                    'min_date': (datetime.now() - timedelta(days=30)).isoformat(),
                    'include_platforms': ['whatsapp', 'telegram', 'slack'],
                    'min_content_length': 5
                }
            }
        },
        'processors': {
            'text': {
                'max_text_length': 10000,
                'entity_extraction': {
                    'entity_types': ['PERSON', 'ORG', 'GPE', 'EMAIL', 'URL'],
                    'max_entities': 20
                },
                'keyword_extraction': {
                    'max_keywords': 15,
                    'min_word_length': 3
                }
            }
        },
        'analysis': {
            'patterns': {
                'frequency_period': 'day',
                'change_window_size': 7,
                'top_communicators': 5
            },
            'relationships': {
                'key_relationships': 10,
                'one_way_threshold': 0.2
            },
            'topics': {
                'num_topics': 5,
                'words_per_topic': 8,
                'num_key_phrases': 10
            }
        },
        'interface': {
            'reports': {
                'max_list_items': 5,
                'charts': {
                    'width': 600,
                    'height': 400,
                    'interactive': True
                }
            }
        }
    }
    
    return config

def filter_emails(email_data):
    """
    Custom filter function for emails.
    
    Args:
        email_data: Email data dictionary
        
    Returns:
        True if the email should be included, False otherwise
    """
    # Skip emails with empty content
    if not email_data.get('content'):
        return False
    
    # Skip emails with certain subjects
    subject = email_data.get('subject', '').lower()
    if any(term in subject for term in ['newsletter', 'promotion', 'offer']):
        return False
    
    # Include all other emails
    return True

def filter_messages(message_data):
    """
    Custom filter function for messages.
    
    Args:
        message_data: Message data dictionary
        
    Returns:
        True if the message should be included, False otherwise
    """
    # Skip very short messages
    if len(message_data.get('content', '')) < 10:
        return False
    
    # Skip messages from certain platforms
    if message_data.get('platform') == 'unknown':
        return False
    
    # Include all other messages
    return True

def main():
    """Run the advanced usage example."""
    # Set up logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting CogniLink advanced usage example")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create custom configuration
    custom_config = create_custom_config()
    
    # Save custom configuration to files
    config_dir = os.path.join(output_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    for section, config in custom_config.items():
        with open(os.path.join(config_dir, f"{section}.json"), 'w') as f:
            json.dump(config, f, indent=2)
    
    # Initialize components with custom configuration
    email_connector = EmailConnector(custom_config['connectors']['email'])
    message_connector = MessageConnector(custom_config['connectors']['message'])
    text_processor = TextProcessor(custom_config['processors']['text'])
    
    # Initialize communication graph
    comm_graph = CommunicationGraph()
    
    # Import email data with custom filtering
    logger.info("Importing email data with custom filtering")
    email_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sample_emails.json')
    
    if os.path.exists(email_path):
        for email_data in email_connector.extract_from_json(email_path):
            # Apply custom filter
            if not filter_emails(email_data):
                continue
            
            # Process text content
            if 'content' in email_data and email_data['content']:
                content_analysis = text_processor.process_text(email_data['content'])
                
                # Add extracted entities and keywords to metadata
                email_data['entities'] = content_analysis['entities']
                email_data['keywords'] = content_analysis['keywords']
                email_data['sentiment'] = content_analysis['sentiment']
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in email_data and email_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(email_data['timestamp'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Add to communication graph
            sender = email_data.get('sender', 'unknown')
            recipients = email_data.get('recipients', [])
            message_id = email_data.get('id', '')
            
            # Skip if no sender or recipients
            if not sender or not recipients:
                continue
            
            # Add communication to graph
            metadata = {
                'type': 'email',
                'subject': email_data.get('subject', ''),
                'content': email_data.get('content', ''),
                'entities': email_data.get('entities', []),
                'keywords': email_data.get('keywords', []),
                'sentiment': email_data.get('sentiment', {})
            }
            
            comm_graph.add_communication(sender, recipients, timestamp, message_id, metadata)
    else:
        logger.warning(f"Email sample file not found: {email_path}")
    
    # Import message data with custom filtering
    logger.info("Importing message data with custom filtering")
    message_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sample_messages.json')
    
    if os.path.exists(message_path):
        for message_data in message_connector.extract_from_json(message_path):
            # Apply custom filter
            if not filter_messages(message_data):
                continue
            
            # Process text content
            if 'content' in message_data and message_data['content']:
                content_analysis = text_processor.process_text(message_data['content'])
                
                # Add extracted entities and keywords to metadata
                message_data['entities'] = content_analysis['entities']
                message_data['keywords'] = content_analysis['keywords']
                message_data['sentiment'] = content_analysis['sentiment']
            
            # Parse timestamp
            timestamp = None
            if 'timestamp' in message_data and message_data['timestamp']:
                try:
                    timestamp = datetime.fromisoformat(message_data['timestamp'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Add to communication graph
            sender = message_data.get('sender', 'unknown')
            
            # Handle recipient(s)
            recipients = []
            if 'recipient' in message_data and message_data['recipient']:
                recipients = [message_data['recipient']]
            elif 'recipients' in message_data and message_data['recipients']:
                if isinstance(message_data['recipients'], list):
                    recipients = message_data['recipients']
                else:
                    recipients = [message_data['recipients']]
            
            # If no explicit recipient but has conversation_id, use that as a virtual recipient
            if not recipients and 'conversation_id' in message_data:
                recipients = [f"conversation:{message_data['conversation_id']}"]
            
            # Skip if no sender or recipients
            if not sender or not recipients:
                continue
            
            message_id = message_data.get('id', '')
            
            # Add communication to graph
            metadata = {
                'type': 'message',
                'platform': message_data.get('platform', 'unknown'),
                'content': message_data.get('content', ''),
                'entities': message_data.get('entities', []),
                'keywords': message_data.get('keywords', []),
                'sentiment': message_data.get('sentiment', {})
            }
            
            comm_graph.add_communication(sender, recipients, timestamp, message_id, metadata)
    else:
        logger.warning(f"Message sample file not found: {message_path}")
    
    # Save communication graph
    graph_path = os.path.join(output_dir, 'advanced_comm_graph.json')
    comm_graph.save_to_file(graph_path)
    logger.info(f"Communication graph saved to {graph_path}")
    
    # Analyze communication patterns with custom settings
    logger.info("Analyzing communication patterns with custom settings")
    pattern_analyzer = CommunicationPatternAnalyzer(comm_graph)
    
    # Custom pattern analysis
    frequency_analysis = pattern_analyzer.analyze_communication_frequency(
        time_period=custom_config['analysis']['patterns']['frequency_period']
    )
    
    response_analysis = pattern_analyzer.analyze_response_patterns()
    
    habits_analysis = pattern_analyzer.analyze_communication_habits()
    
    changes_analysis = pattern_analyzer.analyze_communication_changes(
        window_size=custom_config['analysis']['patterns']['change_window_size']
    )
    
    clusters_analysis = pattern_analyzer.identify_communication_clusters()
    
    # Combine pattern analyses
    pattern_results = {
        'communication_frequency': frequency_analysis,
        'response_patterns': response_analysis,
        'communication_habits': habits_analysis,
        'communication_changes': changes_analysis,
        'communication_clusters': clusters_analysis,
        'generated_at': datetime.now().isoformat()
    }
    
    # Analyze relationships with custom settings
    logger.info("Analyzing relationships with custom settings")
    relationship_analyzer = RelationshipAnalyzer(comm_graph)
    
    # Custom relationship analysis
    key_relationships = relationship_analyzer.identify_key_relationships(
        top_n=custom_config['analysis']['relationships']['key_relationships']
    )
    
    relationship_categories = relationship_analyzer.categorize_relationships()
    
    relationship_evolution = relationship_analyzer.analyze_relationship_evolution()
    
    relationship_groups = relationship_analyzer.identify_relationship_groups()
    
    relationship_balance = relationship_analyzer.analyze_relationship_balance()
    
    # Combine relationship analyses
    relationship_results = {
        'key_relationships': key_relationships,
        'relationship_categories': relationship_categories,
        'relationship_evolution': relationship_evolution,
        'relationship_groups': relationship_groups,
        'relationship_balance': relationship_balance,
        'generated_at': datetime.now().isoformat()
    }
    
    # Analyze topics with custom settings
    logger.info("Analyzing topics with custom settings")
    topic_analyzer = TopicAnalyzer(custom_config['analysis']['topics'])
    
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
    
    # Custom topic analysis
    topics = topic_analyzer.extract_topics_lda(
        texts,
        num_topics=custom_config['analysis']['topics']['num_topics'],
        words_per_topic=custom_config['analysis']['topics']['words_per_topic']
    )
    
    key_phrases = topic_analyzer.extract_key_phrases(
        texts,
        max_phrases=custom_config['analysis']['topics']['num_key_phrases']
    )
    
    knowledge_areas = topic_analyzer.extract_knowledge_areas(
        texts,
        num_areas=5
    )
    
    topic_trends = None
    if timestamps:
        topic_trends = topic_analyzer.analyze_topic_trends(
            texts,
            timestamps,
            num_topics=custom_config['analysis']['topics']['num_topics']
        )
    
    # Combine topic analyses
    topic_results = {
        'topics': topics,
        'key_phrases': key_phrases,
        'knowledge_areas': knowledge_areas,
        'topic_trends': topic_trends,
        'generated_at': datetime.now().isoformat()
    }
    
    # Combine all results
    analysis_results = {
        'patterns': pattern_results,
        'relationships': relationship_results,
        'topics': topic_results
    }
    
    # Generate reports with custom settings
    logger.info("Generating reports with custom settings")
    report_generator = ReportGenerator(custom_config['interface']['reports'])
    
    # Generate HTML report
    html_path = os.path.join(output_dir, 'advanced_report.html')
    report_generator.generate_html_report(analysis_results, html_path)
    logger.info(f"HTML report saved to {html_path}")
    
    # Generate Markdown report
    md_path = os.path.join(output_dir, 'advanced_report.md')
    report_generator.generate_markdown_report(analysis_results, md_path)
    logger.info(f"Markdown report saved to {md_path}")
    
    # Generate JSON report
    json_path = os.path.join(output_dir, 'advanced_report.json')
    report_generator.generate_json_report(analysis_results, json_path)
    logger.info(f"JSON report saved to {json_path}")
    
    logger.info("Advanced example completed successfully")

if __name__ == '__main__':
    main()