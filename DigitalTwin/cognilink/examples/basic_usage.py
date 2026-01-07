"""
Basic Usage Example for CogniLink

This script demonstrates the basic usage of CogniLink to import, analyze, and report on
communication data.
"""

import os
import sys
import logging
from datetime import datetime

# Add the parent directory to the path so we can import cognilink
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cognilink.core.utils import setup_logging
from cognilink.core.comm_graph import CommunicationGraph
from cognilink.pipeline.connectors.email_connector import EmailConnector
from cognilink.pipeline.connectors.message_connector import MessageConnector
from cognilink.analysis.patterns import CommunicationPatternAnalyzer
from cognilink.analysis.relationships import RelationshipAnalyzer
from cognilink.analysis.topics import TopicAnalyzer
from cognilink.interface.reports import ReportGenerator

def main():
    """Run the basic usage example."""
    # Set up logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting CogniLink basic usage example")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize communication graph
    comm_graph = CommunicationGraph()
    
    # Import email data
    logger.info("Importing email data")
    email_connector = EmailConnector()
    email_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sample_emails.json')
    
    for email_data in email_connector.extract_from_json(email_path):
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
            'content': email_data.get('content', '')
        }
        
        comm_graph.add_communication(sender, recipients, timestamp, message_id, metadata)
    
    # Import message data
    logger.info("Importing message data")
    message_connector = MessageConnector()
    message_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample', 'sample_messages.json')
    
    for message_data in message_connector.extract_from_json(message_path):
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
            'content': message_data.get('content', '')
        }
        
        comm_graph.add_communication(sender, recipients, timestamp, message_id, metadata)
    
    # Save communication graph
    graph_path = os.path.join(output_dir, 'comm_graph.json')
    comm_graph.save_to_file(graph_path)
    logger.info(f"Communication graph saved to {graph_path}")
    
    # Analyze communication patterns
    logger.info("Analyzing communication patterns")
    pattern_analyzer = CommunicationPatternAnalyzer(comm_graph)
    pattern_results = pattern_analyzer.generate_comprehensive_report()
    
    # Analyze relationships
    logger.info("Analyzing relationships")
    relationship_analyzer = RelationshipAnalyzer(comm_graph)
    relationship_results = relationship_analyzer.generate_comprehensive_report()
    
    # Analyze topics
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
    html_path = os.path.join(output_dir, 'report.html')
    report_generator.generate_html_report(analysis_results, html_path)
    logger.info(f"HTML report saved to {html_path}")
    
    # Generate Markdown report
    md_path = os.path.join(output_dir, 'report.md')
    report_generator.generate_markdown_report(analysis_results, md_path)
    logger.info(f"Markdown report saved to {md_path}")
    
    # Generate JSON report
    json_path = os.path.join(output_dir, 'report.json')
    report_generator.generate_json_report(analysis_results, json_path)
    logger.info(f"JSON report saved to {json_path}")
    
    logger.info("Example completed successfully")

if __name__ == '__main__':
    main()