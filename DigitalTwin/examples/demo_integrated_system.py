"""
Demonstration script for the integrated system.

This script shows how the integrated system combines functionality from:
1. Advanced Data Analysis Twin
2. CogniLink
3. MindMirror

to create a powerful platform for personal data analysis and digital twin interaction.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components from integrated system
from core.engine import Engine
from data_processing.pipeline import DataPipeline
from digital_twin.integration.cognitive_twin import CognitiveTwin
from knowledge_graph.builder import KnowledgeGraphBuilder
from visualization.dashboards.interactive import InteractiveDashboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class IntegratedSystemDemo:
    """Demonstration of the integrated system capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.engine = None
        self.data_pipeline = None
        self.cognitive_twin = None
        self.knowledge_graph_builder = None
        self.dashboard = None
        
    async def initialize(self):
        """Initialize the integrated system components."""
        logger.info("Initializing integrated system demo...")
        
        # Initialize core engine
        self.engine = Engine()
        await self.engine.initialize()
        
        # Get references to key components
        self.data_pipeline = self.engine.data_pipeline
        self.cognitive_twin = self.engine.cognitive_twin
        self.knowledge_graph_builder = self.engine.knowledge_graph_builder
        
        # Initialize dashboard
        self.dashboard = InteractiveDashboard()
        
        logger.info("Integrated system demo initialization complete")
        
    async def run_demo(self):
        """Run the integrated system demonstration."""
        logger.info("Running integrated system demonstration")
        
        # Step 1: Import and process sample data
        await self.import_sample_data()
        
        # Step 2: Analyze data
        analysis_results = await self.analyze_data()
        
        # Step 3: Generate insights
        insights = await self.generate_insights()
        
        # Step 4: Interact with digital twin
        twin_interaction = await self.interact_with_twin()
        
        # Step 5: Visualize results
        visualization_urls = await self.visualize_results(analysis_results, insights)
        
        # Print summary
        self.print_demo_summary(analysis_results, insights, twin_interaction, visualization_urls)
        
    async def import_sample_data(self):
        """Import and process sample data."""
        logger.info("Importing sample data...")
        
        # Import email data
        email_import_result = await self.data_pipeline.import_data(
            source="email",
            path="examples/data/sample_emails.mbox",
            options={
                "format": "mbox",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            }
        )
        logger.info(f"Imported {email_import_result['record_count']} email messages")
        
        # Import message data
        message_import_result = await self.data_pipeline.import_data(
            source="messages",
            path="examples/data/sample_messages.json",
            options={
                "format": "json",
                "platform": "whatsapp"
            }
        )
        logger.info(f"Imported {message_import_result['record_count']} chat messages")
        
        # Import calendar data
        calendar_import_result = await self.data_pipeline.import_data(
            source="calendar",
            path="examples/data/sample_calendar.ics",
            options={
                "format": "ics"
            }
        )
        logger.info(f"Imported {calendar_import_result['record_count']} calendar events")
        
        # Process all imported data
        processing_result = await self.data_pipeline.process_all()
        logger.info(f"Processed {processing_result['total_records']} records from {len(processing_result['sources'])} sources")
        
        return processing_result
        
    async def analyze_data(self):
        """Analyze the imported data."""
        logger.info("Analyzing data...")
        
        # Get user ID (for demo purposes)
        user_id = "demo_user"
        
        # Run analysis
        analysis_results = await self.engine.analyze_data(user_id)
        
        # Log analysis summary
        logger.info("Analysis complete:")
        logger.info(f"- Communication patterns: {len(analysis_results['communication']['patterns'])} patterns identified")
        logger.info(f"- Relationships: {len(analysis_results['communication']['relationships'])} relationships analyzed")
        logger.info(f"- Topics: {len(analysis_results['advanced']['topics'])} topics extracted")
        logger.info(f"- Entities: {len(analysis_results['advanced']['entities'])} entities identified")
        logger.info(f"- Cognitive profile: {len(analysis_results['cognitive'])} cognitive dimensions analyzed")
        
        return analysis_results
        
    async def generate_insights(self):
        """Generate insights from the analyzed data."""
        logger.info("Generating insights...")
        
        # Get user ID (for demo purposes)
        user_id = "demo_user"
        
        # Generate insights
        insights = await self.engine.generate_insights(user_id)
        
        # Log insights summary
        logger.info(f"Generated {len(insights)} insights:")
        for i, insight in enumerate(insights[:5], 1):
            logger.info(f"{i}. {insight['title']} (score: {insight['score']:.2f})")
        if len(insights) > 5:
            logger.info(f"... and {len(insights) - 5} more insights")
            
        return insights
        
    async def interact_with_twin(self):
        """Demonstrate interaction with the digital twin."""
        logger.info("Interacting with digital twin...")
        
        # Sample conversation with the digital twin
        conversation = [
            "Hello, can you tell me about my communication patterns?",
            "What are my most frequent topics of discussion?",
            "Who are my closest contacts based on communication frequency?",
            "What insights do you have about my productivity?",
            "Can you summarize my calendar for the next week?"
        ]
        
        # Process each message and get responses
        responses = []
        for message in conversation:
            logger.info(f"User: {message}")
            
            # Get response from digital twin
            response = await self.cognitive_twin.process_message(message)
            
            logger.info(f"Twin: {response['text']}")
            responses.append(response)
            
        return {
            "conversation": list(zip(conversation, [r["text"] for r in responses])),
            "detailed_responses": responses
        }
        
    async def visualize_results(self, analysis_results, insights):
        """Visualize the results of the analysis and insights."""
        logger.info("Generating visualizations...")
        
        # Create visualizations
        visualizations = {
            "communication_patterns": await self.dashboard.create_visualization(
                "communication_patterns",
                analysis_results["communication"]["patterns"]
            ),
            "relationship_network": await self.dashboard.create_visualization(
                "relationship_network",
                analysis_results["communication"]["relationships"]
            ),
            "topic_distribution": await self.dashboard.create_visualization(
                "topic_distribution",
                analysis_results["advanced"]["topics"]
            ),
            "cognitive_profile": await self.dashboard.create_visualization(
                "cognitive_profile",
                analysis_results["cognitive"]
            ),
            "insights_dashboard": await self.dashboard.create_visualization(
                "insights_dashboard",
                insights
            )
        }
        
        # Generate URLs for visualizations
        visualization_urls = {}
        for name, viz in visualizations.items():
            url = f"http://localhost:8000/visualization/{viz['id']}"
            visualization_urls[name] = url
            logger.info(f"Visualization '{name}' available at: {url}")
            
        return visualization_urls
        
    def print_demo_summary(self, analysis_results, insights, twin_interaction, visualization_urls):
        """Print a summary of the demonstration results."""
        print("\n" + "="*80)
        print("INTEGRATED SYSTEM DEMONSTRATION SUMMARY")
        print("="*80)
        
        print("\nDATA ANALYSIS RESULTS:")
        print(f"- Communication patterns: {len(analysis_results['communication']['patterns'])} patterns identified")
        print(f"- Relationships: {len(analysis_results['communication']['relationships'])} relationships analyzed")
        print(f"- Topics: {len(analysis_results['advanced']['topics'])} topics extracted")
        print(f"- Entities: {len(analysis_results['advanced']['entities'])} entities identified")
        print(f"- Cognitive dimensions: {len(analysis_results['cognitive'])} dimensions analyzed")
        
        print("\nTOP INSIGHTS:")
        for i, insight in enumerate(insights[:5], 1):
            print(f"{i}. {insight['title']} (score: {insight['score']:.2f})")
            print(f"   {insight['description'][:100]}...")
            
        print("\nDIGITAL TWIN INTERACTION SAMPLE:")
        for i, (question, answer) in enumerate(twin_interaction["conversation"][:3], 1):
            print(f"Q{i}: {question}")
            print(f"A{i}: {answer[:100]}...")
            
        print("\nVISUALIZATIONS:")
        for name, url in visualization_urls.items():
            print(f"- {name}: {url}")
            
        print("\nINTEGRATION HIGHLIGHTS:")
        print("1. CogniLink's communication analysis enhanced with Advanced Data Analysis Twin's NLP")
        print("2. MindMirror's cognitive modeling integrated with the digital twin conversation engine")
        print("3. Knowledge graph combining relationship data from all three systems")
        print("4. Unified visualization dashboard presenting insights from all components")
        print("5. Seamless data flow between all system components")
        
        print("\n" + "="*80)
        print("END OF DEMONSTRATION")
        print("="*80 + "\n")


# Mock implementation of InteractiveDashboard for demonstration purposes
class InteractiveDashboard:
    """Mock implementation of the interactive dashboard."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.visualizations = {}
        self.next_id = 1
        
    async def create_visualization(self, viz_type, data):
        """Create a visualization of the specified type with the given data."""
        viz_id = f"{viz_type}_{self.next_id}"
        self.next_id += 1
        
        # In a real implementation, this would create actual visualizations
        visualization = {
            "id": viz_id,
            "type": viz_type,
            "created_at": datetime.now().isoformat(),
            "data_summary": f"{len(data)} data points" if isinstance(data, list) else "Complex data structure"
        }
        
        self.visualizations[viz_id] = visualization
        return visualization


# Run the demonstration
async def main():
    """Run the integrated system demonstration."""
    demo = IntegratedSystemDemo()
    await demo.initialize()
    await demo.run_demo()


if __name__ == "__main__":
    # Create examples directory if it doesn't exist
    os.makedirs("examples", exist_ok=True)
    
    # Run the demo
    asyncio.run(main())