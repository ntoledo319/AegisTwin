"""
Personality engine for the digital twin.

This module provides the core personality engine for the digital twin,
responsible for modeling and generating personality-driven behaviors.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class PersonalityEngine:
    """Core personality engine for the digital twin."""
    
    def __init__(self):
        """Initialize the personality engine."""
        self.personality_traits = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        self.communication_style = {
            'assertiveness': 0.5,
            'emotionality': 0.5,
            'formality': 0.5,
            'descriptors': []
        }
        
        self.decision_style = {
            'analytical': 0.5,
            'intuitive': 0.5,
            'deliberate': 0.5,
            'spontaneous': 0.5,
            'primary_style': None
        }
        
        self.interaction_style = {
            'dominant': 0.5,
            'submissive': 0.5,
            'cooperative': 0.5,
            'competitive': 0.5,
            'warm': 0.5,
            'cold': 0.5,
            'primary_style': None
        }
        
        self.model = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the personality engine with real AI."""
        logger.info("Initializing personality engine with AI")
        
        try:
            # Import AI modules
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../src'))
            
            from cognitive_twin.ai.personality_ai import PersonalityAI
            from cognitive_twin.memory.memory_manager import MemoryManager
            
            # Initialize AI components
            self.personality_ai = PersonalityAI()
            self.memory_manager = MemoryManager()
            
            # Set default personality traits (will be overridden by AI analysis)
            self._set_default_personality()
            
            # Initialize model
            self.model = PersonalityModel(self.personality_traits)
            
            self.initialized = True
            logger.info("Personality engine initialized with AI")
            
        except Exception as e:
            logger.error(f"Error initializing personality engine: {e}")
            # Fallback to default initialization
            self._set_default_personality()
            self.model = PersonalityModel(self.personality_traits)
            self.initialized = True
            logger.warning("Personality engine initialized with fallback mode")
    
    def _set_default_personality(self):
        """Set default personality traits."""
        # Set balanced traits with slight variations
        self.personality_traits = {
            'openness': 0.6,
            'conscientiousness': 0.7,
            'extraversion': 0.5,
            'agreeableness': 0.6,
            'neuroticism': 0.4
        }
        
        # Set communication style based on traits
        self.communication_style = {
            'assertiveness': 0.5 + (self.personality_traits['extraversion'] - 0.5) * 0.5,
            'emotionality': 0.5 + (self.personality_traits['neuroticism'] - 0.5) * 0.5,
            'formality': 0.5 + (self.personality_traits['conscientiousness'] - 0.5) * 0.5,
            'descriptors': self._generate_communication_descriptors()
        }
        
        # Set decision style based on traits
        analytical_score = 0.5 + (self.personality_traits['conscientiousness'] - self.personality_traits['openness']) / 2
        intuitive_score = 1.0 - analytical_score
        deliberate_score = 0.5 + (self.personality_traits['conscientiousness'] - self.personality_traits['extraversion']) / 2
        spontaneous_score = 1.0 - deliberate_score
        
        self.decision_style = {
            'analytical': analytical_score,
            'intuitive': intuitive_score,
            'deliberate': deliberate_score,
            'spontaneous': spontaneous_score,
            'primary_style': 'analytical' if analytical_score > intuitive_score else 'intuitive'
        }
        
        # Set interaction style based on traits
        dominant_score = 0.5 + (self.personality_traits['extraversion'] - self.personality_traits['agreeableness']) / 2
        submissive_score = 1.0 - dominant_score
        cooperative_score = 0.5 + (self.personality_traits['agreeableness'] - self.personality_traits['neuroticism']) / 2
        competitive_score = 1.0 - cooperative_score
        warm_score = 0.5 + (self.personality_traits['agreeableness'] + self.personality_traits['extraversion'] - 1.0) / 2
        cold_score = 1.0 - warm_score
        
        self.interaction_style = {
            'dominant': dominant_score,
            'submissive': submissive_score,
            'cooperative': cooperative_score,
            'competitive': competitive_score,
            'warm': warm_score,
            'cold': cold_score,
            'primary_style': self._determine_primary_interaction_style(dominant_score, cooperative_score)
        }
    
    def _generate_communication_descriptors(self) -> List[str]:
        """Generate communication style descriptors based on traits."""
        descriptors = []
        
        # Assertiveness descriptors
        if self.communication_style['assertiveness'] > 0.7:
            descriptors.append('direct')
        elif self.communication_style['assertiveness'] < 0.3:
            descriptors.append('tentative')
        
        # Emotionality descriptors
        if self.communication_style['emotionality'] > 0.7:
            descriptors.append('expressive')
        elif self.communication_style['emotionality'] < 0.3:
            descriptors.append('reserved')
        
        # Formality descriptors
        if self.communication_style['formality'] > 0.7:
            descriptors.append('formal')
        elif self.communication_style['formality'] < 0.3:
            descriptors.append('casual')
        
        # Trait-based descriptors
        if self.personality_traits['openness'] > 0.7:
            descriptors.append('creative')
        if self.personality_traits['conscientiousness'] > 0.7:
            descriptors.append('organized')
        if self.personality_traits['extraversion'] > 0.7:
            descriptors.append('outgoing')
        if self.personality_traits['agreeableness'] > 0.7:
            descriptors.append('friendly')
        if self.personality_traits['neuroticism'] < 0.3:
            descriptors.append('calm')
        
        return descriptors
    
    def _determine_primary_interaction_style(self, dominant_score: float, cooperative_score: float) -> str:
        """Determine primary interaction style based on dominance and cooperation scores."""
        if dominant_score > 0.6 and cooperative_score > 0.6:
            return 'leading'
        elif dominant_score > 0.6 and cooperative_score < 0.4:
            return 'directing'
        elif dominant_score < 0.4 and cooperative_score > 0.6:
            return 'supporting'
        elif dominant_score < 0.4 and cooperative_score < 0.4:
            return 'avoiding'
        else:
            return 'balanced'
    
    async def analyze_personality(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze personality from data using real AI.
        
        Args:
            data: Data to analyze (messages, behavior, etc.)
            user_id: User identifier for caching and memory
            
        Returns:
            Personality analysis results
        """
        if not self.initialized:
            await self.initialize()
        
        logger.info("Analyzing personality from data using AI")
        
        try:
            # Extract text data for analysis
            texts = self._extract_texts_from_data(data)
            
            if not texts:
                logger.warning("No text data found for personality analysis")
                return self._get_fallback_analysis()
            
            # Use AI to analyze personality
            if hasattr(self, 'personality_ai') and self.personality_ai:
                ai_profile = await self.personality_ai.extract_personality(
                    texts=texts,
                    user_id=user_id,
                    analysis_depth="comprehensive"
                )
                
                if "error" not in ai_profile:
                    # Update personality traits with AI results
                    self.personality_traits.update(ai_profile.get("big_five", {}))
                    self.communication_style.update(ai_profile.get("communication_style", {}))
                    self.decision_style.update(ai_profile.get("decision_style", {}))
                    
                    # Update interaction style based on new traits
                    self._update_decision_interaction_styles()
                    
                    # Store in memory if user_id provided
                    if user_id and hasattr(self, 'memory_manager') and self.memory_manager:
                        await self.memory_manager.store_personality_data(
                            user_id=user_id,
                            personality_profile=ai_profile,
                            source="ai_analysis"
                        )
                    
                    # Create analysis results
                    analysis_results = {
                        'traits': self.personality_traits.copy(),
                        'communication_style': self.communication_style.copy(),
                        'decision_style': self.decision_style.copy(),
                        'interaction_style': self.interaction_style.copy(),
                        'ai_insights': ai_profile.get("insights", []),
                        'confidence': ai_profile.get("confidence_scores", {}).get("overall_confidence", 0.8),
                        'analysis_method': 'ai_analysis',
                        'model_used': 'claude-3-sonnet',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    logger.info(f"Personality analysis completed with AI for user {user_id}")
                    return analysis_results
                else:
                    logger.error(f"AI personality analysis failed: {ai_profile.get('error')}")
                    return self._get_fallback_analysis()
            else:
                logger.warning("AI personality analyzer not available, using fallback")
                return self._get_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in personality analysis: {e}")
            return self._get_fallback_analysis()
    
    def _extract_texts_from_data(self, data: Dict[str, Any]) -> List[str]:
        """Extract text data for personality analysis"""
        texts = []
        
        # Extract from different data sources
        if "messages" in data:
            messages = data["messages"]
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict) and "content" in msg:
                        texts.append(str(msg["content"]))
                    elif isinstance(msg, str):
                        texts.append(msg)
        
        if "conversations" in data:
            conversations = data["conversations"]
            if isinstance(conversations, list):
                for conv in conversations:
                    if isinstance(conv, dict):
                        if "message" in conv:
                            texts.append(str(conv["message"]))
                        if "response" in conv:
                            texts.append(str(conv["response"]))
        
        if "text" in data:
            texts.append(str(data["text"]))
        
        if "content" in data:
            texts.append(str(data["content"]))
        
        # Filter out empty or very short texts
        texts = [text for text in texts if text and len(text.strip()) > 10]
        
        return texts
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Get fallback analysis when AI is not available"""
        return {
            'traits': self.personality_traits.copy(),
            'communication_style': self.communication_style.copy(),
            'decision_style': self.decision_style.copy(),
            'interaction_style': self.interaction_style.copy(),
            'confidence': 0.3,
            'analysis_method': 'fallback',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def update(self, data: Any, analysis_results: Dict[str, Any] = None):
        """
        Update the personality engine with new data and analysis results.
        
        Args:
            data: New data
            analysis_results: Analysis results (optional)
        """
        logger.info("Updating personality engine")
        
        if not self.initialized:
            await self.initialize()
        
        # Update from analysis results if available
        if analysis_results:
            await self._update_from_analysis(analysis_results)
        
        # Update model
        if self.model:
            await self.model.update(self.personality_traits)
    
    async def _update_from_analysis(self, analysis_results: Dict[str, Any]):
        """
        Update personality from analysis results.
        
        Args:
            analysis_results: Analysis results
        """
        # Check for cognitive analysis results
        if 'cognitive' in analysis_results:
            cognitive = analysis_results['cognitive']
            
            # Update from personality analysis
            if 'personality' in cognitive:
                personality = cognitive['personality']
                
                # Check if we have a personality profile
                if 'personality_profile' in personality:
                    profile = personality['personality_profile']
                    
                    # Update traits if available
                    if 'big_five_traits' in profile:
                        traits = profile['big_five_traits']
                        # Gradually adjust traits (70% existing, 30% new)
                        for trait, value in traits.items():
                            if trait in self.personality_traits:
                                self.personality_traits[trait] = 0.7 * self.personality_traits[trait] + 0.3 * value
                    
                    # Update communication style if available
                    if 'communication_style' in profile:
                        comm_style = profile['communication_style']
                        if 'scores' in comm_style:
                            scores = comm_style['scores']
                            # Gradually adjust style (70% existing, 30% new)
                            for style, value in scores.items():
                                if style in self.communication_style:
                                    self.communication_style[style] = 0.7 * self.communication_style[style] + 0.3 * value
                        
                        if 'descriptors' in comm_style:
                            # Update descriptors
                            self.communication_style['descriptors'] = comm_style['descriptors']
                    
                    # Update decision style if available
                    if 'decision_style' in profile:
                        decision = profile['decision_style']
                        if 'primary_style' in decision:
                            self.decision_style['primary_style'] = decision['primary_style']
                    
                    # Update interaction style if available
                    if 'interaction_style' in profile:
                        interaction = profile['interaction_style']
                        if 'primary_style' in interaction:
                            self.interaction_style['primary_style'] = interaction['primary_style']
    
    async def enhance_with_model(self, model):
        """
        Enhance the personality engine with an external model.
        
        Args:
            model: External personality model
        """
        logger.info("Enhancing personality engine with external model")
        
        if not self.initialized:
            await self.initialize()
        
        # Get traits from external model
        external_traits = await model.get_traits()
        
        # Blend traits (60% existing, 40% external)
        for trait, value in external_traits.items():
            if trait in self.personality_traits:
                self.personality_traits[trait] = 0.6 * self.personality_traits[trait] + 0.4 * value
        
        # Update communication style based on new traits
        self.communication_style = {
            'assertiveness': 0.5 + (self.personality_traits['extraversion'] - 0.5) * 0.5,
            'emotionality': 0.5 + (self.personality_traits['neuroticism'] - 0.5) * 0.5,
            'formality': 0.5 + (self.personality_traits['conscientiousness'] - 0.5) * 0.5,
            'descriptors': self._generate_communication_descriptors()
        }
        
        # Update decision and interaction styles
        self._update_decision_interaction_styles()
        
        # Update model
        if self.model:
            await self.model.update(self.personality_traits)
    
    def _update_decision_interaction_styles(self):
        """Update decision and interaction styles based on current traits."""
        # Update decision style
        analytical_score = 0.5 + (self.personality_traits['conscientiousness'] - self.personality_traits['openness']) / 2
        intuitive_score = 1.0 - analytical_score
        deliberate_score = 0.5 + (self.personality_traits['conscientiousness'] - self.personality_traits['extraversion']) / 2
        spontaneous_score = 1.0 - deliberate_score
        
        self.decision_style = {
            'analytical': analytical_score,
            'intuitive': intuitive_score,
            'deliberate': deliberate_score,
            'spontaneous': spontaneous_score,
            'primary_style': 'analytical' if analytical_score > intuitive_score else 'intuitive'
        }
        
        # Update interaction style
        dominant_score = 0.5 + (self.personality_traits['extraversion'] - self.personality_traits['agreeableness']) / 2
        submissive_score = 1.0 - dominant_score
        cooperative_score = 0.5 + (self.personality_traits['agreeableness'] - self.personality_traits['neuroticism']) / 2
        competitive_score = 1.0 - cooperative_score
        warm_score = 0.5 + (self.personality_traits['agreeableness'] + self.personality_traits['extraversion'] - 1.0) / 2
        cold_score = 1.0 - warm_score
        
        self.interaction_style = {
            'dominant': dominant_score,
            'submissive': submissive_score,
            'cooperative': cooperative_score,
            'competitive': competitive_score,
            'warm': warm_score,
            'cold': cold_score,
            'primary_style': self._determine_primary_interaction_style(dominant_score, cooperative_score)
        }
    
    async def get_profile(self) -> Dict[str, Any]:
        """
        Get the personality profile.
        
        Returns:
            Dictionary of personality profile
        """
        if not self.initialized:
            await self.initialize()
        
        return {
            'traits': self.personality_traits,
            'communication_style': self.communication_style,
            'decision_style': self.decision_style,
            'interaction_style': self.interaction_style
        }
    
    async def get_response_style(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get the response style based on personality and context.
        
        Args:
            context: Context information (optional)
            
        Returns:
            Dictionary of response style parameters
        """
        if not self.initialized:
            await self.initialize()
        
        # Base response style on personality traits
        response_style = {
            'tone': self._determine_tone(),
            'complexity': self._determine_complexity(),
            'formality': self.communication_style['formality'],
            'emotionality': self.communication_style['emotionality'],
            'assertiveness': self.communication_style['assertiveness'],
            'verbosity': self._determine_verbosity()
        }
        
        # Adjust based on context if available
        if context:
            response_style = self._adjust_for_context(response_style, context)
        
        return response_style
    
    def _determine_tone(self) -> str:
        """Determine tone based on personality traits."""
        # Tone is primarily influenced by agreeableness, neuroticism, and extraversion
        if self.personality_traits['agreeableness'] > 0.7 and self.personality_traits['extraversion'] > 0.6:
            return 'warm'
        elif self.personality_traits['neuroticism'] > 0.7:
            return 'anxious'
        elif self.personality_traits['agreeableness'] < 0.3:
            return 'critical'
        elif self.personality_traits['extraversion'] > 0.7 and self.personality_traits['openness'] > 0.6:
            return 'enthusiastic'
        elif self.personality_traits['conscientiousness'] > 0.7:
            return 'precise'
        else:
            return 'neutral'
    
    def _determine_complexity(self) -> float:
        """Determine response complexity based on personality traits."""
        # Complexity is primarily influenced by openness and conscientiousness
        base_complexity = 0.5
        openness_factor = (self.personality_traits['openness'] - 0.5) * 0.6
        conscientiousness_factor = (self.personality_traits['conscientiousness'] - 0.5) * 0.4
        
        complexity = base_complexity + openness_factor + conscientiousness_factor
        return max(0.1, min(0.9, complexity))  # Clamp between 0.1 and 0.9
    
    def _determine_verbosity(self) -> float:
        """Determine response verbosity based on personality traits."""
        # Verbosity is primarily influenced by extraversion and openness
        base_verbosity = 0.5
        extraversion_factor = (self.personality_traits['extraversion'] - 0.5) * 0.7
        openness_factor = (self.personality_traits['openness'] - 0.5) * 0.3
        
        verbosity = base_verbosity + extraversion_factor + openness_factor
        return max(0.1, min(0.9, verbosity))  # Clamp between 0.1 and 0.9
    
    def _adjust_for_context(self, response_style: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust response style based on context.
        
        Args:
            response_style: Base response style
            context: Context information
            
        Returns:
            Adjusted response style
        """
        adjusted_style = response_style.copy()
        
        # Adjust for formality of context
        if 'formality' in context:
            # Blend personality-based formality with context formality
            adjusted_style['formality'] = 0.7 * response_style['formality'] + 0.3 * context['formality']
        
        # Adjust for emotional content
        if 'emotional_content' in context:
            # Responsive people adjust more to emotional content
            adjustment_factor = 0.3 + (self.personality_traits['agreeableness'] * 0.2)
            adjusted_style['emotionality'] = (1 - adjustment_factor) * response_style['emotionality'] + adjustment_factor * context['emotional_content']
        
        # Adjust for urgency
        if 'urgency' in context and context['urgency'] > 0.7:
            # Increase assertiveness and reduce complexity for urgent matters
            adjusted_style['assertiveness'] = min(1.0, response_style['assertiveness'] + 0.2)
            adjusted_style['complexity'] = max(0.1, response_style['complexity'] - 0.1)
        
        return adjusted_style
    
    async def create_personality_profile(self, traits: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Create a personality profile with specified traits.
        
        Args:
            traits: Personality traits (optional)
            
        Returns:
            Dictionary of personality profile
        """
        if not self.initialized:
            await self.initialize()
        
        # Use provided traits or current traits
        profile_traits = traits if traits else self.personality_traits.copy()
        
        # Calculate communication style based on traits
        comm_style = {
            'assertiveness': 0.5 + (profile_traits['extraversion'] - 0.5) * 0.5,
            'emotionality': 0.5 + (profile_traits['neuroticism'] - 0.5) * 0.5,
            'formality': 0.5 + (profile_traits['conscientiousness'] - 0.5) * 0.5
        }
        
        # Generate descriptors
        descriptors = []
        if comm_style['assertiveness'] > 0.7:
            descriptors.append('direct')
        elif comm_style['assertiveness'] < 0.3:
            descriptors.append('tentative')
        
        if comm_style['emotionality'] > 0.7:
            descriptors.append('expressive')
        elif comm_style['emotionality'] < 0.3:
            descriptors.append('reserved')
        
        if comm_style['formality'] > 0.7:
            descriptors.append('formal')
        elif comm_style['formality'] < 0.3:
            descriptors.append('casual')
        
        comm_style['descriptors'] = descriptors
        
        # Calculate decision style
        analytical_score = 0.5 + (profile_traits['conscientiousness'] - profile_traits['openness']) / 2
        intuitive_score = 1.0 - analytical_score
        deliberate_score = 0.5 + (profile_traits['conscientiousness'] - profile_traits['extraversion']) / 2
        spontaneous_score = 1.0 - deliberate_score
        
        decision_style = {
            'analytical': analytical_score,
            'intuitive': intuitive_score,
            'deliberate': deliberate_score,
            'spontaneous': spontaneous_score,
            'primary_style': 'analytical' if analytical_score > intuitive_score else 'intuitive'
        }
        
        # Calculate interaction style
        dominant_score = 0.5 + (profile_traits['extraversion'] - profile_traits['agreeableness']) / 2
        submissive_score = 1.0 - dominant_score
        cooperative_score = 0.5 + (profile_traits['agreeableness'] - profile_traits['neuroticism']) / 2
        competitive_score = 1.0 - cooperative_score
        warm_score = 0.5 + (profile_traits['agreeableness'] + profile_traits['extraversion'] - 1.0) / 2
        cold_score = 1.0 - warm_score
        
        # Determine primary interaction style
        primary_style = None
        if dominant_score > 0.6 and cooperative_score > 0.6:
            primary_style = 'leading'
        elif dominant_score > 0.6 and cooperative_score < 0.4:
            primary_style = 'directing'
        elif dominant_score < 0.4 and cooperative_score > 0.6:
            primary_style = 'supporting'
        elif dominant_score < 0.4 and cooperative_score < 0.4:
            primary_style = 'avoiding'
        else:
            primary_style = 'balanced'
        
        interaction_style = {
            'dominant': dominant_score,
            'submissive': submissive_score,
            'cooperative': cooperative_score,
            'competitive': competitive_score,
            'warm': warm_score,
            'cold': cold_score,
            'primary_style': primary_style
        }
        
        # Create profile
        profile = {
            'traits': profile_traits,
            'communication_style': comm_style,
            'decision_style': decision_style,
            'interaction_style': interaction_style,
            'created_at': datetime.now().isoformat()
        }
        
        return profile


class PersonalityModel:
    """Model for personality simulation and prediction."""
    
    def __init__(self, traits: Dict[str, float]):
        """
        Initialize the personality model.
        
        Args:
            traits: Initial personality traits
        """
        self.traits = traits.copy()
        self.trait_history = [traits.copy()]
        self.last_update = datetime.now()
    
    async def update(self, traits: Dict[str, float]):
        """
        Update the model with new traits.
        
        Args:
            traits: New personality traits
        """
        self.traits = traits.copy()
        self.trait_history.append(traits.copy())
        self.last_update = datetime.now()
        
        # Limit history length
        if len(self.trait_history) > 100:
            self.trait_history = self.trait_history[-100:]
    
    async def predict_response(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict response characteristics based on personality and message.
        
        Args:
            message: Input message
            context: Context information (optional)
            
        Returns:
            Dictionary of predicted response characteristics
        """
        # Base prediction on personality traits
        prediction = {
            'tone': self._predict_tone(),
            'length': self._predict_length(),
            'formality': self._predict_formality(),
            'emotionality': self._predict_emotionality(),
            'focus': self._predict_focus()
        }
        
        # Adjust based on message content
        prediction = self._adjust_for_message(prediction, message)
        
        # Adjust based on context if available
        if context:
            prediction = self._adjust_for_context(prediction, context)
        
        return prediction
    
    def _predict_tone(self) -> str:
        """Predict response tone based on personality traits."""
        # Similar to PersonalityEngine._determine_tone
        if self.traits['agreeableness'] > 0.7 and self.traits['extraversion'] > 0.6:
            return 'warm'
        elif self.traits['neuroticism'] > 0.7:
            return 'anxious'
        elif self.traits['agreeableness'] < 0.3:
            return 'critical'
        elif self.traits['extraversion'] > 0.7 and self.traits['openness'] > 0.6:
            return 'enthusiastic'
        elif self.traits['conscientiousness'] > 0.7:
            return 'precise'
        else:
            return 'neutral'
    
    def _predict_length(self) -> str:
        """Predict response length based on personality traits."""
        # Length is primarily influenced by extraversion and conscientiousness
        verbosity = 0.5 + (self.traits['extraversion'] - 0.5) * 0.6 + (self.traits['conscientiousness'] - 0.5) * 0.4
        
        if verbosity > 0.7:
            return 'long'
        elif verbosity < 0.3:
            return 'short'
        else:
            return 'medium'
    
    def _predict_formality(self) -> str:
        """Predict response formality based on personality traits."""
        # Formality is primarily influenced by conscientiousness
        formality = self.traits['conscientiousness']
        
        if formality > 0.7:
            return 'formal'
        elif formality < 0.3:
            return 'casual'
        else:
            return 'neutral'
    
    def _predict_emotionality(self) -> str:
        """Predict response emotionality based on personality traits."""
        # Emotionality is influenced by neuroticism and extraversion
        emotionality = 0.5 + (self.traits['neuroticism'] - 0.5) * 0.5 + (self.traits['extraversion'] - 0.5) * 0.5
        
        if emotionality > 0.7:
            return 'emotional'
        elif emotionality < 0.3:
            return 'reserved'
        else:
            return 'balanced'
    
    def _predict_focus(self) -> str:
        """Predict response focus based on personality traits."""
        # Focus is influenced by agreeableness and extraversion
        other_focus = self.traits['agreeableness']
        self_focus = self.traits['extraversion']
        
        if other_focus > 0.7 and self_focus < 0.5:
            return 'other-focused'
        elif self_focus > 0.7 and other_focus < 0.5:
            return 'self-focused'
        elif other_focus > 0.6 and self_focus > 0.6:
            return 'relationship-focused'
        else:
            return 'balanced'
    
    def _adjust_for_message(self, prediction: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Adjust prediction based on message content.
        
        Args:
            prediction: Base prediction
            message: Input message
            
        Returns:
            Adjusted prediction
        """
        adjusted = prediction.copy()
        
        # Simple adjustments based on message characteristics
        # In a real implementation, this would use more sophisticated NLP
        
        # Check for questions
        if '?' in message:
            # More likely to be other-focused when responding to questions
            if adjusted['focus'] != 'other-focused' and self.traits['agreeableness'] > 0.4:
                adjusted['focus'] = 'other-focused'
        
        # Check for emotional content
        emotional_words = ['happy', 'sad', 'angry', 'excited', 'worried', 'love', 'hate', 'afraid']
        has_emotional_content = any(word in message.lower() for word in emotional_words)
        
        if has_emotional_content and self.traits['agreeableness'] > 0.5:
            # More likely to be emotional when responding to emotional content
            if adjusted['emotionality'] == 'reserved':
                adjusted['emotionality'] = 'balanced'
            elif adjusted['emotionality'] == 'balanced':
                adjusted['emotionality'] = 'emotional'
        
        # Check for formal language
        formal_indicators = ['dear', 'sincerely', 'regards', 'request', 'inquire', 'formal']
        has_formal_indicators = any(word in message.lower() for word in formal_indicators)
        
        if has_formal_indicators:
            # More likely to match formality level
            if adjusted['formality'] == 'casual' and self.traits['conscientiousness'] > 0.4:
                adjusted['formality'] = 'neutral'
            elif adjusted['formality'] == 'neutral' and self.traits['conscientiousness'] > 0.6:
                adjusted['formality'] = 'formal'
        
        return adjusted
    
    def _adjust_for_context(self, prediction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust prediction based on context.
        
        Args:
            prediction: Base prediction
            context: Context information
            
        Returns:
            Adjusted prediction
        """
        adjusted = prediction.copy()
        
        # Adjust for relationship context
        if 'relationship' in context:
            relationship = context['relationship']
            
            if relationship == 'professional':
                # More formal and reserved in professional contexts
                if self.traits['conscientiousness'] > 0.4:
                    adjusted['formality'] = 'formal'
                if self.traits['neuroticism'] < 0.7:  # Unless very neurotic
                    adjusted['emotionality'] = 'reserved'
            
            elif relationship == 'close':
                # More warm and emotional in close relationships
                if self.traits['agreeableness'] > 0.4:
                    adjusted['tone'] = 'warm'
                if self.traits['extraversion'] > 0.4:
                    adjusted['emotionality'] = 'emotional'
        
        # Adjust for conversation history
        if 'history_length' in context:
            history_length = context['history_length']
            
            if history_length > 10:  # Long conversation
                # Tend to be more concise in long conversations
                if adjusted['length'] == 'long' and self.traits['conscientiousness'] > 0.5:
                    adjusted['length'] = 'medium'
        
        return adjusted