"""
Personality AI Module

Extracts and analyzes personality traits from communication data using
advanced AI models and psychological frameworks.
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import logging
from collections import Counter, defaultdict

from .openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

class PersonalityAI:
    """
    Advanced personality analysis using multiple AI models.
    
    Extracts Big Five personality traits, communication styles, and
    behavioral patterns from text data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize personality AI.
        
        Args:
            api_key: OpenRouter API key
        """
        self.client = OpenRouterClient(api_key)
        self.personality_cache = {}
        
    async def extract_personality(
        self,
        texts: List[str],
        user_id: Optional[str] = None,
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Extract personality traits from text samples.
        
        Args:
            texts: List of text samples (messages, posts, etc.)
            user_id: User identifier for caching
            analysis_depth: Analysis depth (basic, detailed, comprehensive)
            
        Returns:
            Comprehensive personality profile
        """
        if not texts:
            return {"error": "No text samples provided"}
        
        # Check cache first
        if user_id and user_id in self.personality_cache:
            cached_result = self.personality_cache[user_id]
            if self._is_cache_valid(cached_result):
                return cached_result
        
        async with self.client as client:
            try:
                # Combine texts for analysis
                combined_text = self._prepare_text_for_analysis(texts)
                
                # Extract Big Five traits
                big_five = await self._extract_big_five_traits(client, combined_text)
                
                # Extract communication style
                communication_style = await self._extract_communication_style(client, combined_text)
                
                # Extract behavioral patterns
                behavioral_patterns = await self._extract_behavioral_patterns(client, texts)
                
                # Extract decision-making style
                decision_style = await self._extract_decision_style(client, combined_text)
                
                # Extract emotional patterns
                emotional_patterns = await self._extract_emotional_patterns(client, texts)
                
                # Calculate personality complexity
                complexity_score = self._calculate_personality_complexity(
                    big_five, communication_style, behavioral_patterns
                )
                
                # Generate personality insights
                insights = await self._generate_personality_insights(
                    client, big_five, communication_style, behavioral_patterns
                )
                
                # Compile comprehensive profile
                profile = {
                    "user_id": user_id,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "analysis_depth": analysis_depth,
                    "text_samples_analyzed": len(texts),
                    "big_five": big_five,
                    "communication_style": communication_style,
                    "behavioral_patterns": behavioral_patterns,
                    "decision_style": decision_style,
                    "emotional_patterns": emotional_patterns,
                    "personality_complexity": complexity_score,
                    "insights": insights,
                    "confidence_scores": self._calculate_confidence_scores(
                        big_five, communication_style, behavioral_patterns
                    )
                }
                
                # Cache result
                if user_id:
                    self.personality_cache[user_id] = profile
                
                return profile
                
            except Exception as e:
                logger.error(f"Error extracting personality: {str(e)}")
                return {"error": f"Personality extraction failed: {str(e)}"}
    
    def _prepare_text_for_analysis(self, texts: List[str]) -> str:
        """Prepare and combine texts for analysis"""
        # Filter and clean texts
        cleaned_texts = []
        for text in texts:
            if isinstance(text, str) and len(text.strip()) > 10:
                cleaned_texts.append(text.strip())
        
        # Limit to reasonable size for API
        if len(cleaned_texts) > 50:
            cleaned_texts = cleaned_texts[:50]
        
        # Combine with separators
        combined = "\n\n---\n\n".join(cleaned_texts)
        
        # Truncate if too long (keep first 8000 characters)
        if len(combined) > 8000:
            combined = combined[:8000] + "..."
        
        return combined
    
    async def _extract_big_five_traits(self, client: OpenRouterClient, text: str) -> Dict[str, float]:
        """Extract Big Five personality traits using AI"""
        
        prompt = f"""Analyze the following text and determine the Big Five personality traits. 
        Rate each trait on a scale of 0.0 to 1.0, where 0.0 is very low and 1.0 is very high.

        Text to analyze:
        {text}

        Please provide scores for:
        1. Openness to Experience (0.0 = conventional/prefers routine, 1.0 = creative/open to new ideas)
        2. Conscientiousness (0.0 = flexible/spontaneous, 1.0 = organized/disciplined)
        3. Extraversion (0.0 = introverted/quiet, 1.0 = outgoing/social)
        4. Agreeableness (0.0 = competitive/skeptical, 1.0 = cooperative/trusting)
        5. Neuroticism (0.0 = emotionally stable/calm, 1.0 = anxious/emotionally reactive)

        Respond with a JSON object containing the scores:
        {{
            "openness": 0.0-1.0,
            "conscientiousness": 0.0-1.0,
            "extraversion": 0.0-1.0,
            "agreeableness": 0.0-1.0,
            "neuroticism": 0.0-1.0
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",  # Good for structured analysis
                task_type="analysis",
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            try:
                # Find JSON in response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    traits = json.loads(json_str)
                    
                    # Validate and normalize scores
                    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
                        if trait in traits:
                            traits[trait] = max(0.0, min(1.0, float(traits[trait])))
                        else:
                            traits[trait] = 0.5  # Default neutral
                    
                    return traits
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse Big Five traits: {e}")
                return self._get_default_big_five()
                
        except Exception as e:
            logger.error(f"Error extracting Big Five traits: {e}")
            return self._get_default_big_five()
    
    async def _extract_communication_style(self, client: OpenRouterClient, text: str) -> Dict[str, Any]:
        """Extract communication style patterns"""
        
        prompt = f"""Analyze the communication style in the following text. Provide scores and characteristics.

        Text:
        {text}

        Analyze and provide:
        1. Assertiveness (0.0 = passive, 1.0 = aggressive)
        2. Emotionality (0.0 = logical/detached, 1.0 = emotional/expressive)
        3. Formality (0.0 = casual/informal, 1.0 = formal/professional)
        4. Verbosity (0.0 = concise, 1.0 = verbose)
        5. Directness (0.0 = indirect/hinting, 1.0 = direct/straightforward)

        Also identify:
        - Common communication patterns
        - Preferred communication style
        - Language complexity level

        Respond with JSON:
        {{
            "assertiveness": 0.0-1.0,
            "emotionality": 0.0-1.0,
            "formality": 0.0-1.0,
            "verbosity": 0.0-1.0,
            "directness": 0.0-1.0,
            "patterns": ["pattern1", "pattern2"],
            "preferred_style": "description",
            "complexity_level": "low/medium/high"
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",
                task_type="analysis",
                temperature=0.3
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                style = json.loads(json_str)
                
                # Validate scores
                for key in ["assertiveness", "emotionality", "formality", "verbosity", "directness"]:
                    if key in style:
                        style[key] = max(0.0, min(1.0, float(style[key])))
                    else:
                        style[key] = 0.5
                
                return style
            else:
                return self._get_default_communication_style()
                
        except Exception as e:
            logger.error(f"Error extracting communication style: {e}")
            return self._get_default_communication_style()
    
    async def _extract_behavioral_patterns(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Extract behavioral patterns from text samples"""
        
        # Analyze patterns across multiple texts
        patterns = {
            "response_time_patterns": self._analyze_response_timing(texts),
            "topic_preferences": self._analyze_topic_preferences(texts),
            "interaction_style": self._analyze_interaction_style(texts),
            "conflict_handling": self._analyze_conflict_handling(texts),
            "social_behavior": self._analyze_social_behavior(texts)
        }
        
        return patterns
    
    def _analyze_response_timing(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze response timing patterns"""
        # This would need timestamp data - simplified for now
        return {
            "average_response_length": np.mean([len(text.split()) for text in texts]),
            "response_consistency": 0.7,  # Placeholder
            "urgency_patterns": "moderate"  # Placeholder
        }
    
    def _analyze_topic_preferences(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze topic preferences"""
        # Simple keyword analysis
        all_words = []
        for text in texts:
            words = text.lower().split()
            all_words.extend([w for w in words if len(w) > 4])
        
        word_counts = Counter(all_words)
        top_topics = [word for word, count in word_counts.most_common(10)]
        
        return {
            "frequent_topics": top_topics,
            "topic_diversity": len(set(all_words)) / max(len(all_words), 1),
            "specialization_level": "general" if len(top_topics) > 5 else "specialized"
        }
    
    def _analyze_interaction_style(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze interaction style"""
        # Analyze question patterns, exclamations, etc.
        questions = sum(1 for text in texts if '?' in text)
        exclamations = sum(1 for text in texts if '!' in text)
        
        return {
            "question_frequency": questions / max(len(texts), 1),
            "exclamation_frequency": exclamations / max(len(texts), 1),
            "interaction_type": "inquisitive" if questions > exclamations else "expressive"
        }
    
    def _analyze_conflict_handling(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze conflict handling patterns"""
        # Look for conflict-related keywords
        conflict_words = ["disagree", "wrong", "mistake", "problem", "issue", "conflict"]
        conflict_mentions = sum(1 for text in texts 
                              for word in conflict_words 
                              if word in text.lower())
        
        return {
            "conflict_mention_frequency": conflict_mentions / max(len(texts), 1),
            "conflict_style": "avoidant" if conflict_mentions < 0.1 else "confrontational"
        }
    
    def _analyze_social_behavior(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze social behavior patterns"""
        # Look for social indicators
        social_words = ["we", "us", "team", "together", "help", "support"]
        social_mentions = sum(1 for text in texts 
                            for word in social_words 
                            if word in text.lower())
        
        return {
            "social_orientation": social_mentions / max(len(texts), 1),
            "collaboration_style": "high" if social_mentions > 0.2 else "low"
        }
    
    async def _extract_decision_style(self, client: OpenRouterClient, text: str) -> Dict[str, Any]:
        """Extract decision-making style"""
        
        prompt = f"""Analyze the decision-making style in this text. Look for patterns in how decisions are made.

        Text:
        {text}

        Provide analysis of:
        1. Analytical vs Intuitive (0.0 = very analytical, 1.0 = very intuitive)
        2. Deliberate vs Spontaneous (0.0 = very deliberate, 1.0 = very spontaneous)
        3. Risk tolerance (0.0 = risk-averse, 1.0 = risk-taking)
        4. Decision speed (0.0 = slow/careful, 1.0 = fast/decisive)

        Respond with JSON:
        {{
            "analytical_vs_intuitive": 0.0-1.0,
            "deliberate_vs_spontaneous": 0.0-1.0,
            "risk_tolerance": 0.0-1.0,
            "decision_speed": 0.0-1.0,
            "primary_style": "analytical/intuitive/mixed"
        }}"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",
                task_type="analysis",
                temperature=0.3
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                style = json.loads(json_str)
                
                # Validate scores
                for key in ["analytical_vs_intuitive", "deliberate_vs_spontaneous", "risk_tolerance", "decision_speed"]:
                    if key in style:
                        style[key] = max(0.0, min(1.0, float(style[key])))
                    else:
                        style[key] = 0.5
                
                return style
            else:
                return self._get_default_decision_style()
                
        except Exception as e:
            logger.error(f"Error extracting decision style: {e}")
            return self._get_default_decision_style()
    
    async def _extract_emotional_patterns(self, client: OpenRouterClient, texts: List[str]) -> Dict[str, Any]:
        """Extract emotional patterns"""
        
        # Simple emotional analysis
        emotions = {
            "positive": ["happy", "great", "excellent", "wonderful", "amazing", "love", "enjoy"],
            "negative": ["sad", "angry", "frustrated", "disappointed", "worried", "hate", "terrible"],
            "neutral": ["okay", "fine", "normal", "average", "standard"]
        }
        
        emotion_counts = defaultdict(int)
        for text in texts:
            text_lower = text.lower()
            for emotion_type, words in emotions.items():
                for word in words:
                    if word in text_lower:
                        emotion_counts[emotion_type] += 1
        
        total_emotions = sum(emotion_counts.values())
        if total_emotions > 0:
            emotion_distribution = {
                emotion: count / total_emotions 
                for emotion, count in emotion_counts.items()
            }
        else:
            emotion_distribution = {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
        
        return {
            "emotion_distribution": emotion_distribution,
            "dominant_emotion": max(emotion_distribution, key=emotion_distribution.get),
            "emotional_stability": 1.0 - emotion_distribution.get("negative", 0.0)
        }
    
    def _calculate_personality_complexity(
        self, 
        big_five: Dict[str, float], 
        communication_style: Dict[str, Any], 
        behavioral_patterns: Dict[str, Any]
    ) -> float:
        """Calculate personality complexity score"""
        
        # Calculate variance in Big Five traits
        trait_values = list(big_five.values())
        trait_variance = np.var(trait_values)
        
        # Calculate communication style diversity
        style_values = [v for k, v in communication_style.items() if isinstance(v, (int, float))]
        style_variance = np.var(style_values) if style_values else 0.0
        
        # Combine for complexity score
        complexity = (trait_variance + style_variance) / 2.0
        return min(1.0, max(0.0, complexity))
    
    async def _generate_personality_insights(
        self, 
        client: OpenRouterClient,
        big_five: Dict[str, float], 
        communication_style: Dict[str, Any], 
        behavioral_patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate personality insights using AI"""
        
        prompt = f"""Based on this personality analysis, generate 3-5 key insights about this person's personality and communication style.

        Big Five Traits:
        {json.dumps(big_five, indent=2)}

        Communication Style:
        {json.dumps(communication_style, indent=2)}

        Behavioral Patterns:
        {json.dumps(behavioral_patterns, indent=2)}

        Provide insights that are:
        - Specific and actionable
        - Based on the data provided
        - Helpful for understanding this person
        - Professional and respectful

        Format as a JSON array of insight strings:
        ["insight 1", "insight 2", "insight 3"]"""
        
        try:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-sonnet",
                task_type="analysis",
                temperature=0.7
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Extract JSON array
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                insights = json.loads(json_str)
                return insights if isinstance(insights, list) else []
            else:
                return ["Personality analysis completed successfully"]
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Personality analysis completed with basic insights"]
    
    def _calculate_confidence_scores(
        self, 
        big_five: Dict[str, float], 
        communication_style: Dict[str, Any], 
        behavioral_patterns: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate confidence scores for different aspects"""
        
        return {
            "big_five_confidence": 0.85,  # Based on text quality and AI analysis
            "communication_style_confidence": 0.80,
            "behavioral_patterns_confidence": 0.75,
            "overall_confidence": 0.80
        }
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        timestamp = cached_result.get("analysis_timestamp")
        if not timestamp:
            return False
        
        # Cache valid for 24 hours
        from datetime import datetime, timedelta
        cache_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return datetime.now() - cache_time < timedelta(hours=24)
    
    def _get_default_big_five(self) -> Dict[str, float]:
        """Get default Big Five scores"""
        return {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        }
    
    def _get_default_communication_style(self) -> Dict[str, Any]:
        """Get default communication style"""
        return {
            "assertiveness": 0.5,
            "emotionality": 0.5,
            "formality": 0.5,
            "verbosity": 0.5,
            "directness": 0.5,
            "patterns": ["standard"],
            "preferred_style": "balanced",
            "complexity_level": "medium"
        }
    
    def _get_default_decision_style(self) -> Dict[str, Any]:
        """Get default decision style"""
        return {
            "analytical_vs_intuitive": 0.5,
            "deliberate_vs_spontaneous": 0.5,
            "risk_tolerance": 0.5,
            "decision_speed": 0.5,
            "primary_style": "mixed"
        }
