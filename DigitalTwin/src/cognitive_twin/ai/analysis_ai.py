"""
Analysis AI Module

Provides advanced data analysis capabilities using multiple AI models
for insights, predictions, and pattern recognition.
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
from collections import Counter, defaultdict

from .openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

class AnalysisAI:
    """
    Advanced analysis system using multiple AI models for insights and predictions.
    
    Provides sentiment analysis, topic modeling, trend analysis, and predictive insights
    using optimal models for each task type.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analysis AI.
        
        Args:
            api_key: OpenRouter API key
        """
        self.client = OpenRouterClient(api_key)
        self.analysis_cache = {}
        
    async def analyze_text_data(
        self,
        texts: List[str],
        analysis_types: List[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive text data analysis.
        
        Args:
            texts: List of text samples to analyze
            analysis_types: Types of analysis to perform
            user_id: User identifier for caching
            
        Returns:
            Comprehensive analysis results
        """
        if not texts:
            return {"error": "No text data provided"}
        
        if analysis_types is None:
            analysis_types = ["sentiment", "topics", "entities", "insights", "trends"]
        
        # Check cache
        cache_key = f"{user_id}_{hash(tuple(texts))}" if user_id else None
        if cache_key and cache_key in self.analysis_cache:
            cached_result = self.analysis_cache[cache_key]
            if self._is_cache_valid(cached_result):
                return cached_result
        
        async with self.client as client:
            try:
                results = {}
                
                # Run analyses in parallel
                tasks = []
                
                if "sentiment" in analysis_types:
                    tasks.append(self._analyze_sentiment(client, texts))
                
                if "topics" in analysis_types:
                    tasks.append(self._analyze_topics(client, texts))
                
                if "entities" in analysis_types:
                    tasks.append(self._analyze_entities(client, texts))
                
                if "insights" in analysis_types:
                    tasks.append(self._generate_insights(client, texts))
                
                if "trends" in analysis_types:
                    tasks.append(self._analyze_trends(client, texts))
                
                # Wait for all analyses to complete
                analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(analysis_results):
                    if isinstance(result, Exception):
                        logger.error(f"Analysis task {i} failed: {result}")
                        continue
                    
                    analysis_type = analysis_types[i]
                    results[analysis_type] = result
                
                # Add metadata
                results["metadata"] = {
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "text_count": len(texts),
                    "analysis_types": analysis_types,
                    "user_id": user_id
                }
                
                # Cache results
                if cache_key:
                    self.analysis_cache[cache_key] = results
                
                return results
                
            except Exception as e:
                logger.error(f"Error in text analysis: {str(e)}")
                return {"error": f"Analysis failed: {str(e)}"}
    
    async def _analyze_sentiment(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Advanced sentiment analysis using AI"""
        
        # Combine texts for analysis
        combined_text = "\n\n".join(texts[:20])  # Limit for API
        
        prompt = f"""Analyze the sentiment and emotional tone of the following texts. Provide detailed sentiment analysis.

        Texts:
        {combined_text}

        Analyze and provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Sentiment scores (0.0 to 1.0 for positive, negative, neutral)
        3. Emotional tone (joy, anger, fear, sadness, surprise, disgust)
        4. Sentiment trends across texts
        5. Key emotional indicators

        Respond with JSON:
        {{
            "overall_sentiment": "positive/negative/neutral",
            "sentiment_scores": {{
                "positive": 0.0-1.0,
                "negative": 0.0-1.0,
                "neutral": 0.0-1.0
            }},
            "emotional_tone": {{
                "joy": 0.0-1.0,
                "anger": 0.0-1.0,
                "fear": 0.0-1.0,
                "sadness": 0.0-1.0,
                "surprise": 0.0-1.0,
                "disgust": 0.0-1.0
            }},
            "sentiment_trend": "improving/declining/stable",
            "key_indicators": ["indicator1", "indicator2"],
            "confidence": 0.0-1.0
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",  # Good for nuanced analysis
                task_type="analysis",
                temperature=0.3
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                sentiment_data = json.loads(json_str)
                
                # Validate and normalize scores
                if "sentiment_scores" in sentiment_data:
                    for key in ["positive", "negative", "neutral"]:
                        if key in sentiment_data["sentiment_scores"]:
                            sentiment_data["sentiment_scores"][key] = max(0.0, min(1.0, float(sentiment_data["sentiment_scores"][key])))
                
                if "emotional_tone" in sentiment_data:
                    for emotion in ["joy", "anger", "fear", "sadness", "surprise", "disgust"]:
                        if emotion in sentiment_data["emotional_tone"]:
                            sentiment_data["emotional_tone"][emotion] = max(0.0, min(1.0, float(sentiment_data["emotional_tone"][emotion])))
                
                return sentiment_data
            else:
                return self._get_default_sentiment()
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._get_default_sentiment()
    
    async def _analyze_topics(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Advanced topic analysis using AI"""
        
        combined_text = "\n\n".join(texts[:20])
        
        prompt = f"""Analyze the topics and themes in the following texts. Identify main topics, subtopics, and thematic patterns.

        Texts:
        {combined_text}

        Provide:
        1. Main topics (3-5 primary topics)
        2. Subtopic breakdown for each main topic
        3. Topic relevance scores (0.0-1.0)
        4. Topic relationships and connections
        5. Emerging themes or patterns

        Respond with JSON:
        {{
            "main_topics": [
                {{
                    "topic": "topic name",
                    "relevance": 0.0-1.0,
                    "subtopics": ["subtopic1", "subtopic2"],
                    "key_phrases": ["phrase1", "phrase2"]
                }}
            ],
            "topic_relationships": [
                {{
                    "topic1": "topic name",
                    "topic2": "topic name", 
                    "relationship": "related/opposite/supporting",
                    "strength": 0.0-1.0
                }}
            ],
            "emerging_themes": ["theme1", "theme2"],
            "topic_diversity": 0.0-1.0
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-opus",  # Best for complex topic analysis
                task_type="analysis",
                temperature=0.4
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                topic_data = json.loads(json_str)
                
                # Validate topic data
                if "main_topics" in topic_data:
                    for topic in topic_data["main_topics"]:
                        if "relevance" in topic:
                            topic["relevance"] = max(0.0, min(1.0, float(topic["relevance"])))
                
                return topic_data
            else:
                return self._get_default_topics()
                
        except Exception as e:
            logger.error(f"Error in topic analysis: {e}")
            return self._get_default_topics()
    
    async def _analyze_entities(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Advanced entity recognition and analysis"""
        
        combined_text = "\n\n".join(texts[:20])
        
        prompt = f"""Extract and analyze entities (people, places, organizations, concepts) from the following texts.

        Texts:
        {combined_text}

        Identify and categorize:
        1. People (names, roles, relationships)
        2. Organizations (companies, institutions, groups)
        3. Locations (places, addresses, regions)
        4. Concepts (ideas, technologies, methodologies)
        5. Events (meetings, deadlines, milestones)
        6. Products/Services mentioned

        For each entity, provide:
        - Entity name
        - Category
        - Frequency of mention
        - Context/role
        - Importance score (0.0-1.0)

        Respond with JSON:
        {{
            "people": [
                {{
                    "name": "entity name",
                    "frequency": 1,
                    "context": "role/description",
                    "importance": 0.0-1.0
                }}
            ],
            "organizations": [...],
            "locations": [...],
            "concepts": [...],
            "events": [...],
            "products": [...],
            "entity_network": [
                {{
                    "entity1": "name",
                    "entity2": "name",
                    "relationship": "relationship type",
                    "strength": 0.0-1.0
                }}
            ]
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",
                task_type="analysis",
                temperature=0.2  # Lower temperature for more consistent entity extraction
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                entity_data = json.loads(json_str)
                
                # Validate entity data
                for category in ["people", "organizations", "locations", "concepts", "events", "products"]:
                    if category in entity_data:
                        for entity in entity_data[category]:
                            if "importance" in entity:
                                entity["importance"] = max(0.0, min(1.0, float(entity["importance"])))
                
                return entity_data
            else:
                return self._get_default_entities()
                
        except Exception as e:
            logger.error(f"Error in entity analysis: {e}")
            return self._get_default_entities()
    
    async def _generate_insights(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Generate actionable insights from text data"""
        
        combined_text = "\n\n".join(texts[:20])
        
        prompt = f"""Analyze the following texts and generate actionable insights and recommendations.

        Texts:
        {combined_text}

        Provide:
        1. Key insights (3-5 main insights)
        2. Patterns and trends identified
        3. Potential opportunities
        4. Areas of concern or risk
        5. Actionable recommendations
        6. Priority levels for recommendations

        Focus on insights that are:
        - Specific and actionable
        - Based on evidence in the texts
        - Relevant for decision-making
        - Clear and concise

        Respond with JSON:
        {{
            "key_insights": [
                {{
                    "insight": "insight description",
                    "evidence": "supporting evidence",
                    "confidence": 0.0-1.0,
                    "impact": "high/medium/low"
                }}
            ],
            "patterns": [
                {{
                    "pattern": "pattern description",
                    "frequency": "how often observed",
                    "significance": "high/medium/low"
                }}
            ],
            "opportunities": [
                {{
                    "opportunity": "opportunity description",
                    "potential_impact": "high/medium/low",
                    "feasibility": "high/medium/low"
                }}
            ],
            "concerns": [
                {{
                    "concern": "concern description",
                    "severity": "high/medium/low",
                    "urgency": "high/medium/low"
                }}
            ],
            "recommendations": [
                {{
                    "recommendation": "action to take",
                    "priority": "high/medium/low",
                    "timeline": "immediate/short-term/long-term",
                    "expected_outcome": "expected result"
                }}
            ]
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-opus",  # Best for insight generation
                task_type="analysis",
                temperature=0.6
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                insights_data = json.loads(json_str)
                
                # Validate insights data
                for category in ["key_insights", "recommendations"]:
                    if category in insights_data:
                        for item in insights_data[category]:
                            if "confidence" in item:
                                item["confidence"] = max(0.0, min(1.0, float(item["confidence"])))
                
                return insights_data
            else:
                return self._get_default_insights()
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return self._get_default_insights()
    
    async def _analyze_trends(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Analyze trends and patterns over time"""
        
        # This would ideally use timestamped data, but we'll work with what we have
        combined_text = "\n\n".join(texts[:20])
        
        prompt = f"""Analyze trends and patterns in the following texts. Look for changes, developments, and temporal patterns.

        Texts:
        {combined_text}

        Identify:
        1. Trending topics (increasing/decreasing mentions)
        2. Sentiment trends (improving/declining/stable)
        3. Communication pattern changes
        4. Emerging themes
        5. Declining themes
        6. Cyclical patterns
        7. Anomalies or unusual occurrences

        Respond with JSON:
        {{
            "trending_topics": [
                {{
                    "topic": "topic name",
                    "trend": "increasing/decreasing/stable",
                    "velocity": 0.0-1.0,
                    "significance": "high/medium/low"
                }}
            ],
            "sentiment_trends": {{
                "overall_trend": "improving/declining/stable",
                "trend_strength": 0.0-1.0,
                "volatility": 0.0-1.0
            }},
            "communication_patterns": [
                {{
                    "pattern": "pattern description",
                    "change": "increasing/decreasing/stable",
                    "impact": "high/medium/low"
                }}
            ],
            "emerging_themes": ["theme1", "theme2"],
            "declining_themes": ["theme1", "theme2"],
            "anomalies": [
                {{
                    "anomaly": "description",
                    "significance": "high/medium/low",
                    "potential_cause": "possible explanation"
                }}
            ]
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",
                task_type="analysis",
                temperature=0.4
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                trends_data = json.loads(json_str)
                
                # Validate trends data
                if "trending_topics" in trends_data:
                    for topic in trends_data["trending_topics"]:
                        if "velocity" in topic:
                            topic["velocity"] = max(0.0, min(1.0, float(topic["velocity"])))
                
                return trends_data
            else:
                return self._get_default_trends()
                
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return self._get_default_trends()
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        timestamp = cached_result.get("metadata", {}).get("analysis_timestamp")
        if not timestamp:
            return False
        
        # Cache valid for 1 hour
        cache_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return datetime.now() - cache_time < timedelta(hours=1)
    
    def _get_default_sentiment(self) -> Dict[str, Any]:
        """Get default sentiment analysis"""
        return {
            "overall_sentiment": "neutral",
            "sentiment_scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34},
            "emotional_tone": {"joy": 0.2, "anger": 0.1, "fear": 0.1, "sadness": 0.1, "surprise": 0.1, "disgust": 0.1},
            "sentiment_trend": "stable",
            "key_indicators": ["neutral language"],
            "confidence": 0.5
        }
    
    def _get_default_topics(self) -> Dict[str, Any]:
        """Get default topic analysis"""
        return {
            "main_topics": [
                {"topic": "general communication", "relevance": 0.8, "subtopics": ["discussion"], "key_phrases": ["communication"]}
            ],
            "topic_relationships": [],
            "emerging_themes": ["communication"],
            "topic_diversity": 0.3
        }
    
    def _get_default_entities(self) -> Dict[str, Any]:
        """Get default entity analysis"""
        return {
            "people": [],
            "organizations": [],
            "locations": [],
            "concepts": [],
            "events": [],
            "products": [],
            "entity_network": []
        }
    
    def _get_default_insights(self) -> Dict[str, Any]:
        """Get default insights"""
        return {
            "key_insights": [
                {"insight": "Communication patterns observed", "evidence": "Text analysis", "confidence": 0.6, "impact": "medium"}
            ],
            "patterns": [],
            "opportunities": [],
            "concerns": [],
            "recommendations": [
                {"recommendation": "Continue monitoring communication patterns", "priority": "medium", "timeline": "ongoing", "expected_outcome": "Better understanding"}
            ]
        }
    
    def _get_default_trends(self) -> Dict[str, Any]:
        """Get default trends analysis"""
        return {
            "trending_topics": [],
            "sentiment_trends": {"overall_trend": "stable", "trend_strength": 0.3, "volatility": 0.2},
            "communication_patterns": [],
            "emerging_themes": [],
            "declining_themes": [],
            "anomalies": []
        }
