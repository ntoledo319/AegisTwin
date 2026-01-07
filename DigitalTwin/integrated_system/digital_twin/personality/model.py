"""
Personality model for the digital twin.

This module provides a more sophisticated personality model for the digital twin,
extending the basic personality engine with advanced modeling capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
import numpy as np
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class PersonalityModel:
    """Advanced personality model for the digital twin."""
    
    def __init__(self):
        """Initialize the personality model."""
        self.traits = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        self.facets = {
            'openness': {
                'imagination': 0.5,
                'artistic_interests': 0.5,
                'emotionality': 0.5,
                'adventurousness': 0.5,
                'intellect': 0.5,
                'liberalism': 0.5
            },
            'conscientiousness': {
                'self_efficacy': 0.5,
                'orderliness': 0.5,
                'dutifulness': 0.5,
                'achievement_striving': 0.5,
                'self_discipline': 0.5,
                'cautiousness': 0.5
            },
            'extraversion': {
                'friendliness': 0.5,
                'gregariousness': 0.5,
                'assertiveness': 0.5,
                'activity_level': 0.5,
                'excitement_seeking': 0.5,
                'cheerfulness': 0.5
            },
            'agreeableness': {
                'trust': 0.5,
                'morality': 0.5,
                'altruism': 0.5,
                'cooperation': 0.5,
                'modesty': 0.5,
                'sympathy': 0.5
            },
            'neuroticism': {
                'anxiety': 0.5,
                'anger': 0.5,
                'depression': 0.5,
                'self_consciousness': 0.5,
                'immoderation': 0.5,
                'vulnerability': 0.5
            }
        }
        
        self.values = {
            'achievement': 0.5,
            'benevolence': 0.5,
            'conformity': 0.5,
            'hedonism': 0.5,
            'power': 0.5,
            'security': 0.5,
            'self_direction': 0.5,
            'stimulation': 0.5,
            'tradition': 0.5,
            'universalism': 0.5
        }
        
        self.interests = {
            'artistic': 0.5,
            'scientific': 0.5,
            'nature': 0.5,
            'social': 0.5,
            'political': 0.5,
            'technological': 0.5,
            'athletic': 0.5,
            'musical': 0.5,
            'literary': 0.5,
            'culinary': 0.5
        }
        
        self.trait_history = []
        self.initialized = False
        self.model_path = "data/personality_model.json"
    
    async def initialize(self):
        """Initialize the personality model."""
        logger.info("Initializing advanced personality model")
        
        # Try to load model from file
        if await self._load_model():
            logger.info("Loaded personality model from file")
        else:
            # Set default personality
            self._set_default_personality()
            logger.info("Set default personality model")
        
        # Initialize history
        self.trait_history = [{
            'traits': self.traits.copy(),
            'timestamp': datetime.now().isoformat()
        }]
        
        self.initialized = True
        logger.info("Advanced personality model initialized")
    
    async def _load_model(self) -> bool:
        """
        Load model from file.
        
        Returns:
            True if model was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'r') as f:
                    model_data = json.load(f)
                
                # Load traits
                if 'traits' in model_data:
                    self.traits = model_data['traits']
                
                # Load facets
                if 'facets' in model_data:
                    self.facets = model_data['facets']
                
                # Load values
                if 'values' in model_data:
                    self.values = model_data['values']
                
                # Load interests
                if 'interests' in model_data:
                    self.interests = model_data['interests']
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading personality model: {str(e)}")
            return False
    
    async def _save_model(self):
        """Save model to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Create model data
            model_data = {
                'traits': self.traits,
                'facets': self.facets,
                'values': self.values,
                'interests': self.interests,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.model_path, 'w') as f:
                json.dump(model_data, f, indent=2)
            
            logger.info("Saved personality model to file")
            return True
        except Exception as e:
            logger.error(f"Error saving personality model: {str(e)}")
            return False
    
    def _set_default_personality(self):
        """Set default personality traits, facets, values, and interests."""
        # Set balanced traits with slight variations
        self.traits = {
            'openness': 0.65,
            'conscientiousness': 0.7,
            'extraversion': 0.55,
            'agreeableness': 0.6,
            'neuroticism': 0.4
        }
        
        # Set facets based on traits
        self._set_facets_from_traits()
        
        # Set values based on traits
        self._set_values_from_traits()
        
        # Set interests based on traits
        self._set_interests_from_traits()
    
    def _set_facets_from_traits(self):
        """Set facet values based on trait values."""
        # Openness facets
        self.facets['openness']['imagination'] = self.traits['openness'] + np.random.normal(0, 0.05)
        self.facets['openness']['artistic_interests'] = self.traits['openness'] + np.random.normal(0, 0.05)
        self.facets['openness']['emotionality'] = (self.traits['openness'] + self.traits['neuroticism']) / 2 + np.random.normal(0, 0.05)
        self.facets['openness']['adventurousness'] = (self.traits['openness'] + self.traits['extraversion']) / 2 + np.random.normal(0, 0.05)
        self.facets['openness']['intellect'] = self.traits['openness'] + np.random.normal(0, 0.05)
        self.facets['openness']['liberalism'] = self.traits['openness'] + np.random.normal(0, 0.05)
        
        # Conscientiousness facets
        self.facets['conscientiousness']['self_efficacy'] = self.traits['conscientiousness'] + np.random.normal(0, 0.05)
        self.facets['conscientiousness']['orderliness'] = self.traits['conscientiousness'] + np.random.normal(0, 0.05)
        self.facets['conscientiousness']['dutifulness'] = self.traits['conscientiousness'] + np.random.normal(0, 0.05)
        self.facets['conscientiousness']['achievement_striving'] = self.traits['conscientiousness'] + np.random.normal(0, 0.05)
        self.facets['conscientiousness']['self_discipline'] = self.traits['conscientiousness'] + np.random.normal(0, 0.05)
        self.facets['conscientiousness']['cautiousness'] = (self.traits['conscientiousness'] + (1 - self.traits['neuroticism'])) / 2 + np.random.normal(0, 0.05)
        
        # Extraversion facets
        self.facets['extraversion']['friendliness'] = (self.traits['extraversion'] + self.traits['agreeableness']) / 2 + np.random.normal(0, 0.05)
        self.facets['extraversion']['gregariousness'] = self.traits['extraversion'] + np.random.normal(0, 0.05)
        self.facets['extraversion']['assertiveness'] = self.traits['extraversion'] + np.random.normal(0, 0.05)
        self.facets['extraversion']['activity_level'] = self.traits['extraversion'] + np.random.normal(0, 0.05)
        self.facets['extraversion']['excitement_seeking'] = (self.traits['extraversion'] + self.traits['openness']) / 2 + np.random.normal(0, 0.05)
        self.facets['extraversion']['cheerfulness'] = (self.traits['extraversion'] + (1 - self.traits['neuroticism'])) / 2 + np.random.normal(0, 0.05)
        
        # Agreeableness facets
        self.facets['agreeableness']['trust'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        self.facets['agreeableness']['morality'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        self.facets['agreeableness']['altruism'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        self.facets['agreeableness']['cooperation'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        self.facets['agreeableness']['modesty'] = (self.traits['agreeableness'] + (1 - self.traits['extraversion'])) / 2 + np.random.normal(0, 0.05)
        self.facets['agreeableness']['sympathy'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        
        # Neuroticism facets
        self.facets['neuroticism']['anxiety'] = self.traits['neuroticism'] + np.random.normal(0, 0.05)
        self.facets['neuroticism']['anger'] = self.traits['neuroticism'] + np.random.normal(0, 0.05)
        self.facets['neuroticism']['depression'] = self.traits['neuroticism'] + np.random.normal(0, 0.05)
        self.facets['neuroticism']['self_consciousness'] = self.traits['neuroticism'] + np.random.normal(0, 0.05)
        self.facets['neuroticism']['immoderation'] = (self.traits['neuroticism'] + (1 - self.traits['conscientiousness'])) / 2 + np.random.normal(0, 0.05)
        self.facets['neuroticism']['vulnerability'] = self.traits['neuroticism'] + np.random.normal(0, 0.05)
        
        # Clamp all facet values to [0.1, 0.9] range
        for trait, facets in self.facets.items():
            for facet in facets:
                self.facets[trait][facet] = max(0.1, min(0.9, self.facets[trait][facet]))
    
    def _set_values_from_traits(self):
        """Set value priorities based on trait values."""
        # Achievement is influenced by conscientiousness and extraversion
        self.values['achievement'] = (self.traits['conscientiousness'] * 0.7 + self.traits['extraversion'] * 0.3) + np.random.normal(0, 0.05)
        
        # Benevolence is influenced by agreeableness
        self.values['benevolence'] = self.traits['agreeableness'] + np.random.normal(0, 0.05)
        
        # Conformity is influenced by conscientiousness and (low) openness
        self.values['conformity'] = (self.traits['conscientiousness'] * 0.6 + (1 - self.traits['openness']) * 0.4) + np.random.normal(0, 0.05)
        
        # Hedonism is influenced by extraversion and (low) conscientiousness
        self.values['hedonism'] = (self.traits['extraversion'] * 0.7 + (1 - self.traits['conscientiousness']) * 0.3) + np.random.normal(0, 0.05)
        
        # Power is influenced by extraversion and (low) agreeableness
        self.values['power'] = (self.traits['extraversion'] * 0.5 + (1 - self.traits['agreeableness']) * 0.5) + np.random.normal(0, 0.05)
        
        # Security is influenced by conscientiousness and neuroticism
        self.values['security'] = (self.traits['conscientiousness'] * 0.5 + self.traits['neuroticism'] * 0.5) + np.random.normal(0, 0.05)
        
        # Self-direction is influenced by openness and (low) neuroticism
        self.values['self_direction'] = (self.traits['openness'] * 0.7 + (1 - self.traits['neuroticism']) * 0.3) + np.random.normal(0, 0.05)
        
        # Stimulation is influenced by openness and extraversion
        self.values['stimulation'] = (self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.05)
        
        # Tradition is influenced by conscientiousness and (low) openness
        self.values['tradition'] = (self.traits['conscientiousness'] * 0.5 + (1 - self.traits['openness']) * 0.5) + np.random.normal(0, 0.05)
        
        # Universalism is influenced by agreeableness and openness
        self.values['universalism'] = (self.traits['agreeableness'] * 0.5 + self.traits['openness'] * 0.5) + np.random.normal(0, 0.05)
        
        # Clamp all value priorities to [0.1, 0.9] range
        for value in self.values:
            self.values[value] = max(0.1, min(0.9, self.values[value]))
    
    def _set_interests_from_traits(self):
        """Set interests based on trait values."""
        # Artistic interest is influenced by openness
        self.interests['artistic'] = self.traits['openness'] + np.random.normal(0, 0.1)
        
        # Scientific interest is influenced by openness and conscientiousness
        self.interests['scientific'] = (self.traits['openness'] * 0.7 + self.traits['conscientiousness'] * 0.3) + np.random.normal(0, 0.1)
        
        # Nature interest is influenced by openness and agreeableness
        self.interests['nature'] = (self.traits['openness'] * 0.5 + self.traits['agreeableness'] * 0.5) + np.random.normal(0, 0.1)
        
        # Social interest is influenced by extraversion and agreeableness
        self.interests['social'] = (self.traits['extraversion'] * 0.7 + self.traits['agreeableness'] * 0.3) + np.random.normal(0, 0.1)
        
        # Political interest is influenced by openness and extraversion
        self.interests['political'] = (self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.1)
        
        # Technological interest is influenced by openness and conscientiousness
        self.interests['technological'] = (self.traits['openness'] * 0.6 + self.traits['conscientiousness'] * 0.4) + np.random.normal(0, 0.1)
        
        # Athletic interest is influenced by extraversion and conscientiousness
        self.interests['athletic'] = (self.traits['extraversion'] * 0.6 + self.traits['conscientiousness'] * 0.4) + np.random.normal(0, 0.1)
        
        # Musical interest is influenced by openness
        self.interests['musical'] = self.traits['openness'] + np.random.normal(0, 0.1)
        
        # Literary interest is influenced by openness
        self.interests['literary'] = self.traits['openness'] + np.random.normal(0, 0.1)
        
        # Culinary interest is influenced by openness and extraversion
        self.interests['culinary'] = (self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.1)
        
        # Clamp all interests to [0.1, 0.9] range
        for interest in self.interests:
            self.interests[interest] = max(0.1, min(0.9, self.interests[interest]))
    
    async def update(self, traits: Dict[str, float] = None, data: Any = None, analysis_results: Dict[str, Any] = None):
        """
        Update the personality model with new data.
        
        Args:
            traits: New personality traits (optional)
            data: New data (optional)
            analysis_results: Analysis results (optional)
        """
        logger.info("Updating advanced personality model")
        
        if not self.initialized:
            await self.initialize()
        
        # Update from traits if provided
        if traits:
            await self._update_from_traits(traits)
        
        # Update from analysis results if available
        if analysis_results:
            await self._update_from_analysis(analysis_results)
        
        # Update from data if available
        if data:
            await self._update_from_data(data)
        
        # Add to history
        self.trait_history.append({
            'traits': self.traits.copy(),
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit history length
        if len(self.trait_history) > 100:
            self.trait_history = self.trait_history[-100:]
        
        # Save model
        await self._save_model()
    
    async def _update_from_traits(self, traits: Dict[str, float]):
        """
        Update model from traits.
        
        Args:
            traits: New personality traits
        """
        # Gradually adjust traits (80% existing, 20% new)
        for trait, value in traits.items():
            if trait in self.traits:
                self.traits[trait] = 0.8 * self.traits[trait] + 0.2 * value
        
        # Update facets based on new traits
        self._update_facets_from_traits()
        
        # Update values based on new traits
        self._update_values_from_traits()
        
        # Update interests based on new traits
        self._update_interests_from_traits()
    
    async def _update_from_analysis(self, analysis_results: Dict[str, Any]):
        """
        Update model from analysis results.
        
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
                        # Gradually adjust traits (80% existing, 20% new)
                        for trait, value in traits.items():
                            if trait in self.traits:
                                self.traits[trait] = 0.8 * self.traits[trait] + 0.2 * value
                        
                        # Update facets, values, and interests
                        self._update_facets_from_traits()
                        self._update_values_from_traits()
                        self._update_interests_from_traits()
            
            # Update from values analysis
            if 'values' in cognitive:
                values = cognitive['values']
                
                # Check if we have a values profile
                if 'values_profile' in values:
                    profile = values['values_profile']
                    
                    # Update Schwartz values if available
                    if 'schwartz_values' in profile:
                        schwartz_values = profile['schwartz_values']
                        # Gradually adjust values (80% existing, 20% new)
                        for value, score in schwartz_values.items():
                            if value in self.values:
                                self.values[value] = 0.8 * self.values[value] + 0.2 * score
    
    async def _update_from_data(self, data: Any):
        """
        Update model from data.
        
        Args:
            data: New data
        """
        # Extract messages from data
        messages = self._extract_messages(data)
        
        if not messages:
            return
        
        # Analyze message content for trait indicators
        trait_indicators = self._analyze_trait_indicators(messages)
        
        # Update traits based on indicators
        for trait, indicator in trait_indicators.items():
            if trait in self.traits:
                # Small adjustment based on indicators (95% existing, 5% new)
                self.traits[trait] = 0.95 * self.traits[trait] + 0.05 * indicator
        
        # Update facets, values, and interests
        self._update_facets_from_traits()
        self._update_values_from_traits()
        self._update_interests_from_traits()
    
    def _extract_messages(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract messages from data.
        
        Args:
            data: Data containing messages
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # If data is already a list of messages, return it
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        
        # If data is a dictionary with a 'messages' key, return that
        if isinstance(data, dict) and 'messages' in data:
            return data['messages']
        
        # If data is a dictionary with a 'data' key, try that
        if isinstance(data, dict) and 'data' in data:
            if isinstance(data['data'], list):
                return data['data']
            elif isinstance(data['data'], dict) and 'messages' in data['data']:
                return data['data']['messages']
        
        # If we couldn't extract messages, return empty list
        return []
    
    def _analyze_trait_indicators(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analyze messages for trait indicators.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of trait indicators
        """
        # Initialize trait indicators
        trait_indicators = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        # Extract text content from messages
        texts = []
        for message in messages:
            if 'content' in message and message['content']:
                texts.append(str(message['content']))
            elif 'text' in message and message['text']:
                texts.append(str(message['text']))
        
        if not texts:
            return trait_indicators
        
        # Combine all texts
        combined_text = " ".join(texts).lower()
        
        # Define trait indicators
        trait_words = {
            'openness': [
                'art', 'creative', 'curious', 'imagination', 'explore', 'idea', 'unique',
                'original', 'adventure', 'fantasy', 'culture', 'innovative', 'artistic',
                'dream', 'philosophy', 'abstract', 'intellectual', 'diverse', 'novel'
            ],
            'conscientiousness': [
                'responsible', 'organized', 'efficient', 'thorough', 'plan', 'detail',
                'schedule', 'punctual', 'precise', 'methodical', 'disciplined', 'goal',
                'achievement', 'careful', 'diligent', 'systematic', 'reliable', 'consistent'
            ],
            'extraversion': [
                'social', 'outgoing', 'energetic', 'talkative', 'active', 'enthusiastic',
                'group', 'party', 'people', 'friend', 'excitement', 'adventure', 'fun',
                'lively', 'expressive', 'bold', 'assertive', 'confident'
            ],
            'agreeableness': [
                'kind', 'compassionate', 'cooperative', 'helpful', 'sympathetic', 'warm',
                'considerate', 'friendly', 'generous', 'trusting', 'forgiving', 'patient',
                'understanding', 'empathy', 'supportive', 'harmony', 'team'
            ],
            'neuroticism': [
                'worry', 'anxious', 'stress', 'nervous', 'tense', 'upset', 'moody',
                'emotional', 'sensitive', 'insecure', 'fear', 'doubt', 'vulnerable',
                'unstable', 'concerned', 'overwhelmed', 'frustrated'
            ]
        }
        
        # Count trait words in text
        trait_counts = {}
        for trait, words in trait_words.items():
            count = 0
            for word in words:
                # Count word occurrences
                count += combined_text.count(f" {word} ")
            trait_counts[trait] = count
        
        # Calculate trait indicators
        total_count = sum(trait_counts.values())
        if total_count > 0:
            for trait, count in trait_counts.items():
                # Normalize count to [0.3, 0.7] range
                normalized_count = 0.3 + (count / total_count) * 0.4
                trait_indicators[trait] = normalized_count
        
        return trait_indicators
    
    def _update_facets_from_traits(self):
        """Update facet values based on trait values."""
        # Similar to _set_facets_from_traits but with smaller adjustments
        # Openness facets
        self.facets['openness']['imagination'] = 0.9 * self.facets['openness']['imagination'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        self.facets['openness']['artistic_interests'] = 0.9 * self.facets['openness']['artistic_interests'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        self.facets['openness']['emotionality'] = 0.9 * self.facets['openness']['emotionality'] + 0.1 * ((self.traits['openness'] + self.traits['neuroticism']) / 2 + np.random.normal(0, 0.02))
        self.facets['openness']['adventurousness'] = 0.9 * self.facets['openness']['adventurousness'] + 0.1 * ((self.traits['openness'] + self.traits['extraversion']) / 2 + np.random.normal(0, 0.02))
        self.facets['openness']['intellect'] = 0.9 * self.facets['openness']['intellect'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        self.facets['openness']['liberalism'] = 0.9 * self.facets['openness']['liberalism'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        
        # Conscientiousness facets
        self.facets['conscientiousness']['self_efficacy'] = 0.9 * self.facets['conscientiousness']['self_efficacy'] + 0.1 * (self.traits['conscientiousness'] + np.random.normal(0, 0.02))
        self.facets['conscientiousness']['orderliness'] = 0.9 * self.facets['conscientiousness']['orderliness'] + 0.1 * (self.traits['conscientiousness'] + np.random.normal(0, 0.02))
        self.facets['conscientiousness']['dutifulness'] = 0.9 * self.facets['conscientiousness']['dutifulness'] + 0.1 * (self.traits['conscientiousness'] + np.random.normal(0, 0.02))
        self.facets['conscientiousness']['achievement_striving'] = 0.9 * self.facets['conscientiousness']['achievement_striving'] + 0.1 * (self.traits['conscientiousness'] + np.random.normal(0, 0.02))
        self.facets['conscientiousness']['self_discipline'] = 0.9 * self.facets['conscientiousness']['self_discipline'] + 0.1 * (self.traits['conscientiousness'] + np.random.normal(0, 0.02))
        self.facets['conscientiousness']['cautiousness'] = 0.9 * self.facets['conscientiousness']['cautiousness'] + 0.1 * ((self.traits['conscientiousness'] + (1 - self.traits['neuroticism'])) / 2 + np.random.normal(0, 0.02))
        
        # Extraversion facets
        self.facets['extraversion']['friendliness'] = 0.9 * self.facets['extraversion']['friendliness'] + 0.1 * ((self.traits['extraversion'] + self.traits['agreeableness']) / 2 + np.random.normal(0, 0.02))
        self.facets['extraversion']['gregariousness'] = 0.9 * self.facets['extraversion']['gregariousness'] + 0.1 * (self.traits['extraversion'] + np.random.normal(0, 0.02))
        self.facets['extraversion']['assertiveness'] = 0.9 * self.facets['extraversion']['assertiveness'] + 0.1 * (self.traits['extraversion'] + np.random.normal(0, 0.02))
        self.facets['extraversion']['activity_level'] = 0.9 * self.facets['extraversion']['activity_level'] + 0.1 * (self.traits['extraversion'] + np.random.normal(0, 0.02))
        self.facets['extraversion']['excitement_seeking'] = 0.9 * self.facets['extraversion']['excitement_seeking'] + 0.1 * ((self.traits['extraversion'] + self.traits['openness']) / 2 + np.random.normal(0, 0.02))
        self.facets['extraversion']['cheerfulness'] = 0.9 * self.facets['extraversion']['cheerfulness'] + 0.1 * ((self.traits['extraversion'] + (1 - self.traits['neuroticism'])) / 2 + np.random.normal(0, 0.02))
        
        # Agreeableness facets
        self.facets['agreeableness']['trust'] = 0.9 * self.facets['agreeableness']['trust'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        self.facets['agreeableness']['morality'] = 0.9 * self.facets['agreeableness']['morality'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        self.facets['agreeableness']['altruism'] = 0.9 * self.facets['agreeableness']['altruism'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        self.facets['agreeableness']['cooperation'] = 0.9 * self.facets['agreeableness']['cooperation'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        self.facets['agreeableness']['modesty'] = 0.9 * self.facets['agreeableness']['modesty'] + 0.1 * ((self.traits['agreeableness'] + (1 - self.traits['extraversion'])) / 2 + np.random.normal(0, 0.02))
        self.facets['agreeableness']['sympathy'] = 0.9 * self.facets['agreeableness']['sympathy'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        
        # Neuroticism facets
        self.facets['neuroticism']['anxiety'] = 0.9 * self.facets['neuroticism']['anxiety'] + 0.1 * (self.traits['neuroticism'] + np.random.normal(0, 0.02))
        self.facets['neuroticism']['anger'] = 0.9 * self.facets['neuroticism']['anger'] + 0.1 * (self.traits['neuroticism'] + np.random.normal(0, 0.02))
        self.facets['neuroticism']['depression'] = 0.9 * self.facets['neuroticism']['depression'] + 0.1 * (self.traits['neuroticism'] + np.random.normal(0, 0.02))
        self.facets['neuroticism']['self_consciousness'] = 0.9 * self.facets['neuroticism']['self_consciousness'] + 0.1 * (self.traits['neuroticism'] + np.random.normal(0, 0.02))
        self.facets['neuroticism']['immoderation'] = 0.9 * self.facets['neuroticism']['immoderation'] + 0.1 * ((self.traits['neuroticism'] + (1 - self.traits['conscientiousness'])) / 2 + np.random.normal(0, 0.02))
        self.facets['neuroticism']['vulnerability'] = 0.9 * self.facets['neuroticism']['vulnerability'] + 0.1 * (self.traits['neuroticism'] + np.random.normal(0, 0.02))
        
        # Clamp all facet values to [0.1, 0.9] range
        for trait, facets in self.facets.items():
            for facet in facets:
                self.facets[trait][facet] = max(0.1, min(0.9, self.facets[trait][facet]))
    
    def _update_values_from_traits(self):
        """Update value priorities based on trait values."""
        # Similar to _set_values_from_traits but with smaller adjustments
        # Achievement
        self.values['achievement'] = 0.9 * self.values['achievement'] + 0.1 * ((self.traits['conscientiousness'] * 0.7 + self.traits['extraversion'] * 0.3) + np.random.normal(0, 0.02))
        
        # Benevolence
        self.values['benevolence'] = 0.9 * self.values['benevolence'] + 0.1 * (self.traits['agreeableness'] + np.random.normal(0, 0.02))
        
        # Conformity
        self.values['conformity'] = 0.9 * self.values['conformity'] + 0.1 * ((self.traits['conscientiousness'] * 0.6 + (1 - self.traits['openness']) * 0.4) + np.random.normal(0, 0.02))
        
        # Hedonism
        self.values['hedonism'] = 0.9 * self.values['hedonism'] + 0.1 * ((self.traits['extraversion'] * 0.7 + (1 - self.traits['conscientiousness']) * 0.3) + np.random.normal(0, 0.02))
        
        # Power
        self.values['power'] = 0.9 * self.values['power'] + 0.1 * ((self.traits['extraversion'] * 0.5 + (1 - self.traits['agreeableness']) * 0.5) + np.random.normal(0, 0.02))
        
        # Security
        self.values['security'] = 0.9 * self.values['security'] + 0.1 * ((self.traits['conscientiousness'] * 0.5 + self.traits['neuroticism'] * 0.5) + np.random.normal(0, 0.02))
        
        # Self-direction
        self.values['self_direction'] = 0.9 * self.values['self_direction'] + 0.1 * ((self.traits['openness'] * 0.7 + (1 - self.traits['neuroticism']) * 0.3) + np.random.normal(0, 0.02))
        
        # Stimulation
        self.values['stimulation'] = 0.9 * self.values['stimulation'] + 0.1 * ((self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.02))
        
        # Tradition
        self.values['tradition'] = 0.9 * self.values['tradition'] + 0.1 * ((self.traits['conscientiousness'] * 0.5 + (1 - self.traits['openness']) * 0.5) + np.random.normal(0, 0.02))
        
        # Universalism
        self.values['universalism'] = 0.9 * self.values['universalism'] + 0.1 * ((self.traits['agreeableness'] * 0.5 + self.traits['openness'] * 0.5) + np.random.normal(0, 0.02))
        
        # Clamp all value priorities to [0.1, 0.9] range
        for value in self.values:
            self.values[value] = max(0.1, min(0.9, self.values[value]))
    
    def _update_interests_from_traits(self):
        """Update interests based on trait values."""
        # Similar to _set_interests_from_traits but with smaller adjustments
        # Artistic
        self.interests['artistic'] = 0.9 * self.interests['artistic'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        
        # Scientific
        self.interests['scientific'] = 0.9 * self.interests['scientific'] + 0.1 * ((self.traits['openness'] * 0.7 + self.traits['conscientiousness'] * 0.3) + np.random.normal(0, 0.02))
        
        # Nature
        self.interests['nature'] = 0.9 * self.interests['nature'] + 0.1 * ((self.traits['openness'] * 0.5 + self.traits['agreeableness'] * 0.5) + np.random.normal(0, 0.02))
        
        # Social
        self.interests['social'] = 0.9 * self.interests['social'] + 0.1 * ((self.traits['extraversion'] * 0.7 + self.traits['agreeableness'] * 0.3) + np.random.normal(0, 0.02))
        
        # Political
        self.interests['political'] = 0.9 * self.interests['political'] + 0.1 * ((self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.02))
        
        # Technological
        self.interests['technological'] = 0.9 * self.interests['technological'] + 0.1 * ((self.traits['openness'] * 0.6 + self.traits['conscientiousness'] * 0.4) + np.random.normal(0, 0.02))
        
        # Athletic
        self.interests['athletic'] = 0.9 * self.interests['athletic'] + 0.1 * ((self.traits['extraversion'] * 0.6 + self.traits['conscientiousness'] * 0.4) + np.random.normal(0, 0.02))
        
        # Musical
        self.interests['musical'] = 0.9 * self.interests['musical'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        
        # Literary
        self.interests['literary'] = 0.9 * self.interests['literary'] + 0.1 * (self.traits['openness'] + np.random.normal(0, 0.02))
        
        # Culinary
        self.interests['culinary'] = 0.9 * self.interests['culinary'] + 0.1 * ((self.traits['openness'] * 0.5 + self.traits['extraversion'] * 0.5) + np.random.normal(0, 0.02))
        
        # Clamp all interests to [0.1, 0.9] range
        for interest in self.interests:
            self.interests[interest] = max(0.1, min(0.9, self.interests[interest]))
    
    async def get_traits(self) -> Dict[str, float]:
        """
        Get personality traits.
        
        Returns:
            Dictionary of personality traits
        """
        if not self.initialized:
            await self.initialize()
        
        return self.traits.copy()
    
    async def get_facets(self) -> Dict[str, Dict[str, float]]:
        """
        Get personality facets.
        
        Returns:
            Dictionary of personality facets
        """
        if not self.initialized:
            await self.initialize()
        
        return self.facets.copy()
    
    async def get_values(self) -> Dict[str, float]:
        """
        Get value priorities.
        
        Returns:
            Dictionary of value priorities
        """
        if not self.initialized:
            await self.initialize()
        
        return self.values.copy()
    
    async def get_interests(self) -> Dict[str, float]:
        """
        Get interests.
        
        Returns:
            Dictionary of interests
        """
        if not self.initialized:
            await self.initialize()
        
        return self.interests.copy()
    
    async def get_profile(self) -> Dict[str, Any]:
        """
        Get the complete personality profile.
        
        Returns:
            Dictionary of personality profile
        """
        if not self.initialized:
            await self.initialize()
        
        return {
            'traits': self.traits.copy(),
            'facets': self.facets.copy(),
            'values': self.values.copy(),
            'interests': self.interests.copy(),
            'trait_history': self.trait_history[-10:],  # Last 10 history points
            'last_updated': datetime.now().isoformat()
        }
    
    async def get_trait_development(self) -> Dict[str, List[float]]:
        """
        Get trait development over time.
        
        Returns:
            Dictionary of trait development
        """
        if not self.initialized:
            await self.initialize()
        
        # Extract trait values from history
        trait_development = {trait: [] for trait in self.traits}
        
        for history_point in self.trait_history:
            for trait in self.traits:
                if trait in history_point['traits']:
                    trait_development[trait].append(history_point['traits'][trait])
        
        return trait_development
    
    async def predict_behavior(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict behavior in a given situation.
        
        Args:
            situation: Situation description
            
        Returns:
            Dictionary of predicted behavior
        """
        if not self.initialized:
            await self.initialize()
        
        # Extract situation characteristics
        situation_type = situation.get('type', 'general')
        social_context = situation.get('social_context', 'neutral')
        pressure_level = situation.get('pressure_level', 0.5)
        familiarity = situation.get('familiarity', 0.5)
        
        # Base behavior prediction on personality traits
        behavior = {
            'approach': self._predict_approach(situation_type, social_context),
            'engagement_level': self._predict_engagement(social_context, familiarity),
            'emotional_response': self._predict_emotional_response(situation_type, pressure_level),
            'decision_style': self._predict_decision_style(pressure_level, familiarity),
            'communication_style': self._predict_communication_style(social_context)
        }
        
        return behavior
    
    def _predict_approach(self, situation_type: str, social_context: str) -> str:
        """
        Predict approach to a situation.
        
        Args:
            situation_type: Type of situation
            social_context: Social context
            
        Returns:
            Predicted approach
        """
        # Calculate approach tendencies
        active_tendency = self.traits['extraversion'] * 0.4 + self.traits['openness'] * 0.3 + (1 - self.traits['neuroticism']) * 0.3
        cautious_tendency = self.traits['conscientiousness'] * 0.5 + self.traits['neuroticism'] * 0.3 + (1 - self.traits['openness']) * 0.2
        social_tendency = self.traits['extraversion'] * 0.5 + self.traits['agreeableness'] * 0.5
        
        # Adjust for situation type
        if situation_type == 'challenge':
            active_tendency += 0.1
        elif situation_type == 'threat':
            cautious_tendency += 0.2
        elif situation_type == 'opportunity':
            active_tendency += 0.2
        
        # Adjust for social context
        if social_context == 'group':
            if social_tendency > 0.6:
                active_tendency += 0.1
            else:
                active_tendency -= 0.1
        elif social_context == 'authority':
            if self.traits['conscientiousness'] > 0.6:
                cautious_tendency += 0.1
        
        # Determine approach
        if active_tendency > cautious_tendency + 0.2:
            return 'proactive'
        elif cautious_tendency > active_tendency + 0.2:
            return 'cautious'
        else:
            return 'balanced'
    
    def _predict_engagement(self, social_context: str, familiarity: float) -> str:
        """
        Predict engagement level.
        
        Args:
            social_context: Social context
            familiarity: Familiarity level
            
        Returns:
            Predicted engagement level
        """
        # Base engagement on extraversion and openness
        base_engagement = self.traits['extraversion'] * 0.7 + self.traits['openness'] * 0.3
        
        # Adjust for social context
        if social_context == 'group':
            if self.traits['extraversion'] > 0.6:
                base_engagement += 0.1
            else:
                base_engagement -= 0.1
        elif social_context == 'one-on-one':
            if self.traits['agreeableness'] > 0.6:
                base_engagement += 0.1
        
        # Adjust for familiarity
        familiarity_adjustment = (familiarity - 0.5) * 0.2
        adjusted_engagement = base_engagement + familiarity_adjustment
        
        # Determine engagement level
        if adjusted_engagement > 0.7:
            return 'high'
        elif adjusted_engagement < 0.4:
            return 'low'
        else:
            return 'moderate'
    
    def _predict_emotional_response(self, situation_type: str, pressure_level: float) -> str:
        """
        Predict emotional response.
        
        Args:
            situation_type: Type of situation
            pressure_level: Pressure level
            
        Returns:
            Predicted emotional response
        """
        # Base emotional response on neuroticism and extraversion
        emotional_intensity = self.traits['neuroticism'] * 0.6 + self.traits['extraversion'] * 0.4
        positive_tendency = (1 - self.traits['neuroticism']) * 0.5 + self.traits['extraversion'] * 0.3 + self.traits['agreeableness'] * 0.2
        
        # Adjust for situation type
        if situation_type == 'threat':
            emotional_intensity += 0.2
            positive_tendency -= 0.2
        elif situation_type == 'opportunity':
            positive_tendency += 0.2
        
        # Adjust for pressure level
        pressure_adjustment = (pressure_level - 0.5) * 0.4
        emotional_intensity += pressure_adjustment
        positive_tendency -= pressure_adjustment * 0.5
        
        # Clamp values
        emotional_intensity = max(0.1, min(0.9, emotional_intensity))
        positive_tendency = max(0.1, min(0.9, positive_tendency))
        
        # Determine emotional response
        if emotional_intensity > 0.7:
            if positive_tendency > 0.6:
                return 'excited'
            elif positive_tendency < 0.4:
                return 'anxious'
            else:
                return 'intense'
        elif emotional_intensity < 0.4:
            if positive_tendency > 0.6:
                return 'content'
            elif positive_tendency < 0.4:
                return 'reserved'
            else:
                return 'calm'
        else:
            if positive_tendency > 0.6:
                return 'positive'
            elif positive_tendency < 0.4:
                return 'concerned'
            else:
                return 'neutral'
    
    def _predict_decision_style(self, pressure_level: float, familiarity: float) -> str:
        """
        Predict decision style.
        
        Args:
            pressure_level: Pressure level
            familiarity: Familiarity level
            
        Returns:
            Predicted decision style
        """
        # Base decision style on traits
        analytical_tendency = self.traits['conscientiousness'] * 0.6 + (1 - self.traits['neuroticism']) * 0.4
        intuitive_tendency = self.traits['openness'] * 0.7 + self.traits['extraversion'] * 0.3
        
        # Adjust for pressure level
        if pressure_level > 0.7:
            # Under high pressure, people tend to rely more on intuition
            analytical_tendency -= 0.1
            intuitive_tendency += 0.1
        
        # Adjust for familiarity
        if familiarity > 0.7:
            # With high familiarity, people tend to rely more on intuition
            intuitive_tendency += 0.1
        elif familiarity < 0.3:
            # With low familiarity, people tend to be more analytical
            analytical_tendency += 0.1
        
        # Determine decision style
        if analytical_tendency > intuitive_tendency + 0.2:
            return 'analytical'
        elif intuitive_tendency > analytical_tendency + 0.2:
            return 'intuitive'
        else:
            return 'balanced'
    
    def _predict_communication_style(self, social_context: str) -> str:
        """
        Predict communication style.
        
        Args:
            social_context: Social context
            
        Returns:
            Predicted communication style
        """
        # Base communication style on traits
        assertiveness = self.traits['extraversion'] * 0.6 + (1 - self.traits['agreeableness']) * 0.4
        expressiveness = self.traits['extraversion'] * 0.5 + self.traits['openness'] * 0.3 + self.traits['neuroticism'] * 0.2
        formality = self.traits['conscientiousness'] * 0.7 + (1 - self.traits['extraversion']) * 0.3
        
        # Adjust for social context
        if social_context == 'authority':
            assertiveness -= 0.1
            formality += 0.2
        elif social_context == 'group':
            if self.traits['extraversion'] > 0.6:
                assertiveness += 0.1
            else:
                assertiveness -= 0.1
        
        # Determine communication style descriptors
        descriptors = []
        
        if assertiveness > 0.7:
            descriptors.append('assertive')
        elif assertiveness < 0.3:
            descriptors.append('reserved')
        
        if expressiveness > 0.7:
            descriptors.append('expressive')
        elif expressiveness < 0.3:
            descriptors.append('controlled')
        
        if formality > 0.7:
            descriptors.append('formal')
        elif formality < 0.3:
            descriptors.append('casual')
        
        # Combine descriptors
        if descriptors:
            return ', '.join(descriptors)
        else:
            return 'balanced'