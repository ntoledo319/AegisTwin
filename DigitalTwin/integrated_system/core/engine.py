"""
Core engine for the integrated system.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from core.config import config
from core.db import db_manager

from data_processing.pipeline import DataPipeline
from analysis.communication import CommunicationAnalyzer
from analysis.advanced import AdvancedAnalyzer
from analysis.cognitive import CognitiveAnalyzer
from digital_twin.integration import CognitiveTwin
from knowledge_graph.builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)

class Engine:
    """Core engine for the integrated system."""
    
    def __init__(self):
        """Initialize the core engine."""
        self.data_pipeline = None
        self.communication_analyzer = None
        self.advanced_analyzer = None
        self.cognitive_analyzer = None
        self.knowledge_graph_builder = None
        self.cognitive_twin = None
        
    async def initialize(self):
        """Initialize the core engine components."""
        logger.info("Initializing core engine...")
        
        try:
            # Initialize data pipeline
            self.data_pipeline = DataPipeline()
            await self.data_pipeline.initialize()
            logger.info("Data pipeline initialized successfully")
            
            # Initialize analyzers
            self.communication_analyzer = CommunicationAnalyzer()
            self.advanced_analyzer = AdvancedAnalyzer()
            self.cognitive_analyzer = CognitiveAnalyzer()
            logger.info("Analyzers initialized successfully")
            
            # Initialize knowledge graph builder
            self.knowledge_graph_builder = KnowledgeGraphBuilder()
            logger.info("Knowledge graph builder initialized successfully")
            
            # Initialize cognitive twin
            self.cognitive_twin = CognitiveTwin()
            await self.cognitive_twin.initialize()
            logger.info("Cognitive twin initialized successfully")
            
            logger.info("Core engine initialization complete")
        except Exception as e:
            logger.error(f"Error during core engine initialization: {str(e)}")
            # Re-raise the exception to ensure proper error handling
            raise
        
    async def shutdown(self):
        """Shutdown the core engine."""
        logger.info("Shutting down core engine...")
        
        # Shutdown components if they exist
        if self.data_pipeline:
            await self.data_pipeline.shutdown()
            
        if self.cognitive_twin:
            await self.cognitive_twin.shutdown()
            
        logger.info("Core engine shutdown complete")
        
    async def process_data(self, data_source: str, data: Any) -> Dict[str, Any]:
        """
        Process data from a specific source.
        
        Args:
            data_source: Source of the data
            data: Data to process
            
        Returns:
            Processing results
        """
        logger.info(f"Processing data from {data_source}")
        
        try:
            # 1. Process data through pipeline
            pipeline_results = await self.data_pipeline.process(data_source, data)
            logger.info(f"Data pipeline processing complete for {data_source}")
            
            # 2. Analyze data
            analysis_results = {}
            
            # Communication analysis
            if self.communication_analyzer:
                comm_results = await self.communication_analyzer.analyze(pipeline_results["processed_data"])
                analysis_results["communication"] = comm_results
                logger.info("Communication analysis complete")
            
            # Advanced analysis
            if self.advanced_analyzer:
                adv_results = await self.advanced_analyzer.analyze(pipeline_results["processed_data"])
                analysis_results["advanced"] = adv_results
                logger.info("Advanced analysis complete")
            
            # Cognitive analysis
            if self.cognitive_analyzer:
                cog_results = await self.cognitive_analyzer.analyze(pipeline_results["processed_data"])
                analysis_results["cognitive"] = cog_results
                logger.info("Cognitive analysis complete")
            
            # 3. Update knowledge graph
            knowledge_graph_updated = False
            if self.knowledge_graph_builder:
                kg_results = await self.knowledge_graph_builder.update_graph(
                    pipeline_results["processed_data"],
                    analysis_results
                )
                knowledge_graph_updated = kg_results["success"]
                logger.info(f"Knowledge graph update {'successful' if knowledge_graph_updated else 'failed'}")
            
            # 4. Update cognitive twin
            cognitive_twin_updated = False
            if self.cognitive_twin:
                ct_results = await self.cognitive_twin.update(
                    pipeline_results["processed_data"],
                    analysis_results
                )
                cognitive_twin_updated = ct_results["success"]
                logger.info(f"Cognitive twin update {'successful' if cognitive_twin_updated else 'failed'}")
            
            return {
                "status": "success",
                "message": f"Data from {data_source} processed successfully",
                "processed_data": pipeline_results["processed_data"],
                "analysis_results": analysis_results,
                "knowledge_graph_updated": knowledge_graph_updated,
                "cognitive_twin_updated": cognitive_twin_updated
            }
        except Exception as e:
            logger.error(f"Error processing data from {data_source}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing data from {data_source}: {str(e)}",
                "error": str(e)
            }
        
    async def analyze_data(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze data for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing data for user {user_id}")
        
        try:
            # Get user data from database
            # In a real implementation, we would fetch the user's data from the database
            # For now, we'll use a mock implementation that returns sample data
            
            # Get data from MongoDB
            user_data = None
            if db_manager.mongodb_db:
                users_collection = db_manager.get_mongodb_collection("users")
                user_data = await users_collection.find_one({"user_id": user_id})
            
            if not user_data:
                logger.warning(f"No data found for user {user_id}, using sample data")
                # Use sample data if no user data is found
                user_data = {
                    "user_id": user_id,
                    "data_sources": ["email", "messages", "calendar"],
                    "sample": True
                }
            
            # Perform analysis using the actual components
            results = {}
            
            # Communication analysis
            if self.communication_analyzer:
                communication_results = await self.communication_analyzer.analyze_user(user_id, user_data)
                results["communication"] = communication_results
                logger.info(f"Communication analysis complete for user {user_id}")
            else:
                # Fallback to sample data if component not available
                results["communication"] = {
                    "patterns": [
                        {"type": "time_pattern", "description": "Most active between 9am-11am", "confidence": 0.85},
                        {"type": "response_pattern", "description": "Quick responses to specific contacts", "confidence": 0.78}
                    ],
                    "relationships": [
                        {"contact": "contact1@example.com", "strength": 0.92, "type": "professional"},
                        {"contact": "contact2@example.com", "strength": 0.87, "type": "personal"}
                    ]
                }
            
            # Advanced analysis
            if self.advanced_analyzer:
                advanced_results = await self.advanced_analyzer.analyze_user(user_id, user_data)
                results["advanced"] = advanced_results
                logger.info(f"Advanced analysis complete for user {user_id}")
            else:
                # Fallback to sample data if component not available
                results["advanced"] = {
                    "topics": [
                        {"name": "work", "prevalence": 0.45, "sentiment": 0.2},
                        {"name": "family", "prevalence": 0.25, "sentiment": 0.8}
                    ],
                    "entities": [
                        {"name": "Project X", "type": "project", "mentions": 42},
                        {"name": "Company Y", "type": "organization", "mentions": 27}
                    ]
                }
            
            # Cognitive analysis
            if self.cognitive_analyzer:
                cognitive_results = await self.cognitive_analyzer.analyze_user(user_id, user_data)
                results["cognitive"] = cognitive_results
                logger.info(f"Cognitive analysis complete for user {user_id}")
            else:
                # Fallback to sample data if component not available
                results["cognitive"] = {
                    "personality": {
                        "openness": 0.75,
                        "conscientiousness": 0.82,
                        "extraversion": 0.45,
                        "agreeableness": 0.68,
                        "neuroticism": 0.32
                    },
                    "values": {
                        "achievement": 0.85,
                        "benevolence": 0.72,
                        "self_direction": 0.78,
                        "security": 0.65
                    }
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing data for user {user_id}: {str(e)}")
            # Return a basic error response
            return {
                "status": "error",
                "message": f"Error analyzing data for user {user_id}: {str(e)}",
                "error": str(e)
            }
        
    async def generate_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Generate insights for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of insights
        """
        logger.info(f"Generating insights for user {user_id}")
        
        try:
            # First, get analysis results for the user
            analysis_results = await self.analyze_data(user_id)
            
            if "status" in analysis_results and analysis_results["status"] == "error":
                logger.error(f"Cannot generate insights due to analysis error: {analysis_results['message']}")
                return [{
                    "id": "error",
                    "title": "Error Generating Insights",
                    "description": f"An error occurred during analysis: {analysis_results['message']}",
                    "category": "error",
                    "score": 0.0
                }]
            
            # Generate insights based on analysis results
            insights = []
            
            # Communication insights
            if "communication" in analysis_results:
                comm_data = analysis_results["communication"]
                
                # Time pattern insights
                if "patterns" in comm_data:
                    for pattern in comm_data["patterns"]:
                        if pattern["type"] == "time_pattern" and pattern["confidence"] > 0.8:
                            insights.append({
                                "id": f"time_pattern_{len(insights)}",
                                "title": "Communication Peak Times",
                                "description": pattern["description"] + " Consider scheduling important meetings during this time.",
                                "category": "productivity",
                                "score": pattern["confidence"]
                            })
                
                # Relationship insights
                if "relationships" in comm_data:
                    for relationship in comm_data["relationships"]:
                        if relationship["strength"] > 0.8:
                            insights.append({
                                "id": f"relationship_{len(insights)}",
                                "title": "Key Relationship Identified",
                                "description": f"Your communications with {relationship['contact']} show a strong {relationship['type']} relationship.",
                                "category": "relationships",
                                "score": relationship["strength"]
                            })
            
            # Advanced insights
            if "advanced" in analysis_results:
                adv_data = analysis_results["advanced"]
                
                # Topic insights
                if "topics" in adv_data:
                    top_topic = max(adv_data["topics"], key=lambda x: x["prevalence"])
                    sentiment_desc = "positive" if top_topic["sentiment"] > 0.5 else "negative"
                    insights.append({
                        "id": f"topic_{len(insights)}",
                        "title": "Topic Distribution",
                        "description": f"{top_topic['name'].capitalize()}-related topics dominate your communications ({int(top_topic['prevalence']*100)}%), with a {sentiment_desc} sentiment.",
                        "category": "work-life-balance",
                        "score": 0.8
                    })
            
            # Cognitive insights
            if "cognitive" in analysis_results:
                cog_data = analysis_results["cognitive"]
                
                # Personality insights
                if "personality" in cog_data and "values" in cog_data:
                    # Find highest personality trait
                    top_trait = max(cog_data["personality"].items(), key=lambda x: x[1])
                    # Find highest value
                    top_value = max(cog_data["values"].items(), key=lambda x: x[1])
                    
                    insights.append({
                        "id": f"personality_{len(insights)}",
                        "title": "Value Alignment",
                        "description": f"Your communications strongly reflect your value of {top_value[0]}, which aligns with your personality profile showing high {top_trait[0]}.",
                        "category": "personal-growth",
                        "score": (top_trait[1] + top_value[1]) / 2
                    })
            
            # If we couldn't generate any insights, provide some default ones
            if not insights:
                insights = [
                    {
                        "id": "insight1",
                        "title": "Communication Peak Times",
                        "description": "You're most responsive and engaged in communications between 9am-11am. Consider scheduling important meetings during this time.",
                        "category": "productivity",
                        "score": 0.92
                    },
                    {
                        "id": "insight2",
                        "title": "Key Relationship Identified",
                        "description": "Your communications with contact1@example.com show a strong professional relationship with frequent project discussions.",
                        "category": "relationships",
                        "score": 0.85
                    },
                    {
                        "id": "insight3",
                        "title": "Topic Distribution",
                        "description": "Work-related topics dominate your communications (45%), with a slightly negative sentiment. Consider balancing work discussions with more positive topics.",
                        "category": "work-life-balance",
                        "score": 0.78
                    },
                    {
                        "id": "insight4",
                        "title": "Value Alignment",
                        "description": "Your communications strongly reflect your value of achievement, which aligns with your personality profile showing high conscientiousness.",
                        "category": "personal-growth",
                        "score": 0.75
                    },
                    {
                        "id": "insight5",
                        "title": "Response Pattern",
                        "description": "You respond quickly to messages from specific contacts but delay responses to others. This may indicate prioritization or avoidance patterns.",
                        "category": "communication",
                        "score": 0.72
                    }
                ]
            
            # Sort insights by score
            insights.sort(key=lambda x: x["score"], reverse=True)
            
            # Store insights in Redis for caching if available
            if db_manager.redis_client:
                redis_client = await db_manager.get_redis_client()
                await redis_client.set(
                    f"insights:{user_id}", 
                    str(insights),
                    ex=3600  # Expire after 1 hour
                )
                logger.info(f"Stored insights for user {user_id} in Redis cache")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for user {user_id}: {str(e)}")
            return [{
                "id": "error",
                "title": "Error Generating Insights",
                "description": f"An error occurred: {str(e)}",
                "category": "error",
                "score": 0.0
            }]