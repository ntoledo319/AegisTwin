"""
Demonstration script for the Integrated Data Analysis & Digital Twin System.

This script shows how to use the core components of the system to:
1. Import data from various sources
2. Process and analyze the data
3. Generate insights
4. Interact with the digital twin
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
from core.config import config
from core.db import db_manager

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
        
    async def initialize(self):
        """Initialize the integrated system components."""
        logger.info("Initializing integrated system demo...")
        
        # Initialize database connections
        await db_manager.initialize()
        
        # Initialize core engine
        self.engine = Engine()
        await self.engine.initialize()
        
        logger.info("Integrated system demo initialization complete")
        
    async def shutdown(self):
        """Shutdown the integrated system components."""
        logger.info("Shutting down integrated system demo...")
        
        # Shutdown core engine
        if self.engine:
            await self.engine.shutdown()
            
        # Close database connections
        await db_manager.shutdown()
        
        logger.info("Integrated system demo shutdown complete")
        
    async def run_demo(self):
        """Run the integrated system demonstration."""
        logger.info("Running integrated system demonstration")
        
        # Step 1: Process sample data
        await self.process_sample_data()
        
        # Step 2: Analyze data
        analysis_results = await self.analyze_data()
        
        # Step 3: Generate insights
        insights = await self.generate_insights()
        
        # Step 4: Interact with digital twin
        twin_interaction = await self.interact_with_twin()
        
        # Print summary
        self.print_demo_summary(analysis_results, insights, twin_interaction)
        
    async def process_sample_data(self):
        """Process sample data."""
        logger.info("Processing sample data...")
        
        # Process email data
        email_data = "Sample email data"
        email_result = await self.engine.process_data("email", email_data)
        logger.info(f"Email data processed: {email_result['status']}")
        
        # Process message data
        message_data = "Sample message data"
        message_result = await self.engine.process_data("messages", message_data)
        logger.info(f"Message data processed: {message_result['status']}")
        
        # Process calendar data
        calendar_data = "Sample calendar data"
        calendar_result = await self.engine.process_data("calendar", calendar_data)
        logger.info(f"Calendar data processed: {calendar_result['status']}")
        
        logger.info("Sample data processing complete")
        
    async def analyze_data(self):
        """Analyze the processed data."""
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
            
            # Simulate response from digital twin
            response = {
                "text": f"This is a simulated response to: '{message}'",
                "type": "text",
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "message_id": f"msg_{len(responses) + 1}",
                    "conversation_id": "conv_demo",
                    "confidence": 0.95
                }
            }
            
            logger.info(f"Twin: {response['text']}")
            responses.append(response)
            
        return {
            "conversation": list(zip(conversation, [r["text"] for r in responses])),
            "detailed_responses": responses
        }
        
    def print_demo_summary(self, analysis_results, insights, twin_interaction):
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
            print(f"   {insight['description']}")
            
        print("\nDIGITAL TWIN INTERACTION SAMPLE:")
        for i, (question, answer) in enumerate(twin_interaction["conversation"][:3], 1):
            print(f"Q{i}: {question}")
            print(f"A{i}: {answer}")
            
        print("\nINTEGRATION HIGHLIGHTS:")
        print("1. Data from multiple sources processed and analyzed")
        print("2. Communication analysis combined with cognitive modeling")
        print("3. Insights generated from integrated analysis")
        print("4. Digital twin interaction based on comprehensive user model")
        
        print("\n" + "="*80)
        print("END OF DEMONSTRATION")
        print("="*80 + "\n")

async def main():
    """Run the integrated system demonstration."""
    demo = IntegratedSystemDemo()
    try:
        await demo.initialize()
        await demo.run_demo()
    finally:
        await demo.shutdown()

if __name__ == "__main__":
    asyncio.run(main())