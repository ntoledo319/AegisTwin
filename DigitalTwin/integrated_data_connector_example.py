"""
Example implementation of an integrated data connector that combines functionality
from CogniLink and Advanced Data Analysis Twin.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime

# Import components from CogniLink
from cognilink.pipeline.connectors.base import BaseConnector as CogniLinkConnector
from cognilink.core.utils import parse_date, extract_entities

# Import components from Advanced Data Analysis Twin
from advanced_data_analysis_twin.data_processing.connectors.base import DataConnector
from advanced_data_analysis_twin.core.models import DataSource, DataBatch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedEmailConnector:
    """
    Integrated email connector that combines functionality from CogniLink and 
    Advanced Data Analysis Twin to provide enhanced email data processing.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the integrated email connector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize CogniLink connector
        self.cognilink_connector = CogniLinkConnector(
            connector_type="email",
            config=self.config.get("cognilink", {})
        )
        
        # Initialize Advanced Data Analysis Twin connector
        self.adatwin_connector = DataConnector(
            source_type="email",
            config=self.config.get("adatwin", {})
        )
        
        # Set up cache directory
        self.cache_dir = self.config.get("cache_dir", "cache/email")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info("Initialized integrated email connector")
        
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to email service using provided credentials.
        
        Args:
            credentials: Email service credentials
            
        Returns:
            True if connection successful, False otherwise
        """
        logger.info("Connecting to email service")
        
        # Connect using CogniLink connector
        cognilink_success = await self.cognilink_connector.connect(credentials)
        
        # Connect using Advanced Data Analysis Twin connector
        adatwin_success = await self.adatwin_connector.connect(credentials)
        
        return cognilink_success and adatwin_success
        
    async def import_data(self, 
                         source_path: str, 
                         format_type: str = "mbox", 
                         start_date: Optional[Union[str, datetime]] = None,
                         end_date: Optional[Union[str, datetime]] = None,
                         limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Import email data from the specified source.
        
        Args:
            source_path: Path to email data source
            format_type: Format of email data (mbox, eml, json)
            start_date: Start date for filtering emails
            end_date: End date for filtering emails
            limit: Maximum number of emails to import
            
        Returns:
            Dictionary with import results
        """
        logger.info(f"Importing email data from {source_path} (format: {format_type})")
        
        # Parse dates if provided as strings
        if isinstance(start_date, str):
            start_date = parse_date(start_date)
        if isinstance(end_date, str):
            end_date = parse_date(end_date)
            
        # Import data using CogniLink connector (focused on communication analysis)
        cognilink_data = await self.cognilink_connector.import_data(
            source_path=source_path,
            format_type=format_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Import data using Advanced Data Analysis Twin connector (focused on content analysis)
        adatwin_data = await self.adatwin_connector.import_data(
            source=DataSource(
                path=source_path,
                type=format_type
            ),
            filters={
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        )
        
        # Integrate the data from both sources
        integrated_data = self._integrate_data(cognilink_data, adatwin_data)
        
        # Cache the integrated data
        cache_path = os.path.join(
            self.cache_dir, 
            f"email_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(cache_path, 'w') as f:
            json.dump(integrated_data, f)
            
        logger.info(f"Imported {len(integrated_data['messages'])} emails, cached at {cache_path}")
        
        return {
            "status": "success",
            "message_count": len(integrated_data["messages"]),
            "date_range": {
                "start": integrated_data["metadata"]["date_range"]["start"],
                "end": integrated_data["metadata"]["date_range"]["end"]
            },
            "cache_path": cache_path,
            "integrated_data": integrated_data
        }
        
    def _integrate_data(self, 
                       cognilink_data: Dict[str, Any], 
                       adatwin_data: DataBatch) -> Dict[str, Any]:
        """
        Integrate data from CogniLink and Advanced Data Analysis Twin.
        
        Args:
            cognilink_data: Data from CogniLink connector
            adatwin_data: Data from Advanced Data Analysis Twin connector
            
        Returns:
            Integrated data
        """
        logger.info("Integrating data from CogniLink and Advanced Data Analysis Twin")
        
        # Start with CogniLink data structure (focused on communication metadata)
        integrated_data = {
            "metadata": cognilink_data["metadata"],
            "messages": [],
            "contacts": cognilink_data.get("contacts", []),
            "statistics": cognilink_data.get("statistics", {})
        }
        
        # Add Advanced Data Analysis Twin metadata
        integrated_data["metadata"]["adatwin"] = {
            "source_type": adatwin_data.source.type,
            "processed_at": adatwin_data.processed_at.isoformat(),
            "record_count": adatwin_data.record_count
        }
        
        # Create a mapping of message IDs between the two systems
        message_id_map = {}
        for i, msg in enumerate(cognilink_data["messages"]):
            if "message_id" in msg:
                message_id_map[msg["message_id"]] = i
                
        # Enhance each message with Advanced Data Analysis Twin data
        for i, msg in enumerate(cognilink_data["messages"]):
            enhanced_msg = dict(msg)
            
            # Find corresponding message in Advanced Data Analysis Twin data
            adatwin_msg = None
            if "message_id" in msg and msg["message_id"] in adatwin_data.records_by_id:
                adatwin_msg = adatwin_data.records_by_id[msg["message_id"]]
            elif i < len(adatwin_data.records):
                # Fallback to index-based matching if IDs don't match
                adatwin_msg = adatwin_data.records[i]
                
            # Enhance with Advanced Data Analysis Twin data if available
            if adatwin_msg:
                # Add enhanced content analysis
                enhanced_msg["enhanced"] = {
                    "entities": adatwin_msg.entities,
                    "sentiment": adatwin_msg.sentiment,
                    "topics": adatwin_msg.topics,
                    "importance": adatwin_msg.importance,
                    "summary": adatwin_msg.summary
                }
                
                # Add extracted attachments info
                if hasattr(adatwin_msg, 'attachments') and adatwin_msg.attachments:
                    enhanced_msg["attachments"] = [
                        {
                            "filename": att.filename,
                            "mime_type": att.mime_type,
                            "size": att.size,
                            "content_id": att.content_id,
                            "extracted_text": att.extracted_text if hasattr(att, 'extracted_text') else None
                        }
                        for att in adatwin_msg.attachments
                    ]
            
            integrated_data["messages"].append(enhanced_msg)
            
        # Add enhanced statistics using MindMirror cognitive analysis
        try:
            integrated_data["enhanced_statistics"] = self._generate_enhanced_statistics(integrated_data["messages"])
        except Exception as e:
            logger.error(f"Error generating enhanced statistics: {str(e)}")
            integrated_data["enhanced_statistics"] = {}
            
        return integrated_data
        
    def _generate_enhanced_statistics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate enhanced statistics using MindMirror cognitive analysis.
        
        Args:
            messages: List of messages
            
        Returns:
            Enhanced statistics
        """
        logger.info("Generating enhanced statistics using MindMirror cognitive analysis")
        
        # Convert messages to DataFrame for easier analysis
        df = pd.DataFrame(messages)
        
        # Basic statistics
        stats = {
            "message_count": len(messages),
            "date_range": {
                "start": min(df["date"]) if not df.empty and "date" in df else None,
                "end": max(df["date"]) if not df.empty and "date" in df else None
            },
            "top_senders": df["from"].value_counts().head(10).to_dict() if not df.empty and "from" in df else {},
            "top_recipients": df["to"].explode().value_counts().head(10).to_dict() if not df.empty and "to" in df else {}
        }
        
        # Enhanced cognitive statistics (would normally use MindMirror)
        # For this example, we'll simulate some cognitive analysis results
        stats["cognitive"] = {
            "communication_style": {
                "formality": 0.75,
                "verbosity": 0.62,
                "emotionality": 0.45,
                "assertiveness": 0.68
            },
            "topic_distribution": {
                "work": 0.45,
                "personal": 0.25,
                "technical": 0.20,
                "administrative": 0.10
            },
            "sentiment_trends": {
                "overall": 0.65,
                "by_month": {
                    "2023-01": 0.70,
                    "2023-02": 0.65,
                    "2023-03": 0.60
                }
            },
            "relationship_indicators": {
                "professional": 0.80,
                "personal": 0.40,
                "collaborative": 0.75
            }
        }
        
        return stats
        
    async def process_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a batch of integrated data.
        
        Args:
            batch_data: Batch of integrated data
            
        Returns:
            Processing results
        """
        logger.info(f"Processing batch of {len(batch_data.get('messages', []))} messages")
        
        # Process using CogniLink for communication analysis
        cognilink_results = await self.cognilink_connector.process_batch({
            "messages": batch_data["messages"],
            "metadata": batch_data["metadata"]
        })
        
        # Process using Advanced Data Analysis Twin for content analysis
        adatwin_batch = DataBatch(
            source=DataSource(type="email", path="memory"),
            records=batch_data["messages"],
            processed_at=datetime.now()
        )
        adatwin_results = await self.adatwin_connector.process_batch(adatwin_batch)
        
        # Integrate results
        integrated_results = {
            "communication_analysis": cognilink_results,
            "content_analysis": {
                "entities": adatwin_results.entities,
                "topics": adatwin_results.topics,
                "sentiment": adatwin_results.sentiment,
                "summaries": adatwin_results.summaries
            },
            "enhanced_statistics": batch_data.get("enhanced_statistics", {})
        }
        
        return integrated_results


# Example usage
async def example_usage():
    """Example usage of the integrated email connector."""
    
    # Configuration
    config = {
        "cognilink": {
            "cache_enabled": True,
            "extraction_level": "full"
        },
        "adatwin": {
            "nlp_enabled": True,
            "entity_extraction": True,
            "sentiment_analysis": True
        },
        "cache_dir": "cache/email"
    }
    
    # Create connector
    connector = IntegratedEmailConnector(config)
    
    # Connect (if needed)
    credentials = {
        "email": "user@example.com",
        "password": "password123"
    }
    connected = await connector.connect(credentials)
    
    if not connected:
        logger.error("Failed to connect to email service")
        return
    
    # Import data
    import_results = await connector.import_data(
        source_path="data/emails/inbox.mbox",
        format_type="mbox",
        start_date="2023-01-01",
        end_date="2023-03-31"
    )
    
    # Process batch
    if "integrated_data" in import_results:
        processing_results = await connector.process_batch(import_results["integrated_data"])
        
        # Print some results
        print(f"Processed {len(import_results['integrated_data']['messages'])} messages")
        print(f"Found {len(processing_results['content_analysis']['entities'])} entities")
        print(f"Top topics: {processing_results['content_analysis']['topics'][:5]}")
        print(f"Overall sentiment: {processing_results['content_analysis']['sentiment']['overall']}")
        
        # Communication analysis
        print("\nCommunication Analysis:")
        print(f"Patterns: {processing_results['communication_analysis']['patterns']}")
        print(f"Top contacts: {processing_results['communication_analysis']['top_contacts']}")
        
        # Enhanced statistics
        print("\nEnhanced Statistics:")
        print(f"Communication style: {processing_results['enhanced_statistics']['cognitive']['communication_style']}")
        print(f"Topic distribution: {processing_results['enhanced_statistics']['cognitive']['topic_distribution']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())