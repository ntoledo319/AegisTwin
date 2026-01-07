"""
Personality analysis module for cognitive analysis.

This module provides functionality for analyzing personality traits and characteristics
based on communication data and behavior patterns.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)

class PersonalityAnalyzer:
    """Analyzer for personality traits and characteristics."""
    
    def __init__(self):
        """Initialize the personality analyzer."""
        self.nlp_available = False
        self.ml_available = False
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for personality analysis")
        
        # Try to import ML libraries
        try:
            import sklearn
            self.ml_available = True
            logger.info("scikit-learn available for personality analysis")
        except ImportError:
            logger.warning("scikit-learn not available for personality analysis")
        
        # Initialize personality traits dictionary
        self.personality_traits = {
            'openness': 0.0,
            'conscientiousness': 0.0,
            'extraversion': 0.0,
            'agreeableness': 0.0,
            'neuroticism': 0.0
        }
        
        # Initialize trait indicators
        self._initialize_trait_indicators()
    
    def _initialize_trait_indicators(self):
        """Initialize linguistic indicators for personality traits."""
        # Words and phrases associated with each trait
        # These are simplified indicators for demonstration purposes
        self.trait_indicators = {
            'openness': {
                'positive': [
                    'art', 'creative', 'curious', 'imagination', 'explore', 'idea', 'unique',
                    'original', 'adventure', 'fantasy', 'culture', 'innovative', 'artistic',
                    'dream', 'philosophy', 'abstract', 'intellectual', 'diverse', 'novel'
                ],
                'negative': [
                    'routine', 'conventional', 'traditional', 'familiar', 'practical', 'concrete',
                    'predictable', 'simple', 'straightforward', 'obvious', 'standard'
                ]
            },
            'conscientiousness': {
                'positive': [
                    'responsible', 'organized', 'efficient', 'thorough', 'plan', 'detail',
                    'schedule', 'punctual', 'precise', 'methodical', 'disciplined', 'goal',
                    'achievement', 'careful', 'diligent', 'systematic', 'reliable', 'consistent'
                ],
                'negative': [
                    'lazy', 'messy', 'careless', 'impulsive', 'spontaneous', 'disorganized',
                    'procrastinate', 'late', 'unreliable', 'inconsistent', 'distracted'
                ]
            },
            'extraversion': {
                'positive': [
                    'social', 'outgoing', 'energetic', 'talkative', 'active', 'enthusiastic',
                    'group', 'party', 'people', 'friend', 'excitement', 'adventure', 'fun',
                    'lively', 'expressive', 'bold', 'assertive', 'confident'
                ],
                'negative': [
                    'quiet', 'reserved', 'shy', 'solitary', 'alone', 'private', 'withdrawn',
                    'reflective', 'independent', 'individual', 'intimate', 'personal'
                ]
            },
            'agreeableness': {
                'positive': [
                    'kind', 'compassionate', 'cooperative', 'helpful', 'sympathetic', 'warm',
                    'considerate', 'friendly', 'generous', 'trusting', 'forgiving', 'patient',
                    'understanding', 'empathy', 'supportive', 'harmony', 'team'
                ],
                'negative': [
                    'critical', 'argumentative', 'skeptical', 'competitive', 'challenging',
                    'demanding', 'stubborn', 'suspicious', 'tough', 'harsh', 'uncooperative'
                ]
            },
            'neuroticism': {
                'positive': [
                    'worry', 'anxious', 'stress', 'nervous', 'tense', 'upset', 'moody',
                    'emotional', 'sensitive', 'insecure', 'fear', 'doubt', 'vulnerable',
                    'unstable', 'concerned', 'overwhelmed', 'frustrated'
                ],
                'negative': [
                    'calm', 'relaxed', 'stable', 'balanced', 'secure', 'confident', 'resilient',
                    'composed', 'steady', 'peaceful', 'content', 'easygoing', 'optimistic'
                ]
            }
        }
        
        # Communication style indicators
        self.communication_style_indicators = {
            'assertiveness': {
                'high': [
                    'definitely', 'absolutely', 'certainly', 'strongly', 'must', 'will',
                    'always', 'never', 'every', 'all', 'none', 'best', 'worst', 'clearly'
                ],
                'low': [
                    'perhaps', 'maybe', 'possibly', 'might', 'could', 'sometimes', 'often',
                    'occasionally', 'somewhat', 'relatively', 'fairly', 'kind of', 'sort of'
                ]
            },
            'emotionality': {
                'high': [
                    'love', 'hate', 'amazing', 'terrible', 'awesome', 'awful', 'excited',
                    'thrilled', 'devastated', 'ecstatic', 'furious', 'wonderful', 'horrible',
                    'fantastic', 'dreadful', 'incredible', 'adore', 'despise'
                ],
                'low': [
                    'good', 'bad', 'fine', 'okay', 'alright', 'satisfactory', 'acceptable',
                    'reasonable', 'adequate', 'sufficient', 'suitable', 'appropriate'
                ]
            },
            'formality': {
                'high': [
                    'furthermore', 'nevertheless', 'consequently', 'therefore', 'however',
                    'regarding', 'concerning', 'additionally', 'subsequently', 'previously',
                    'accordingly', 'moreover', 'thus', 'hence', 'whilst'
                ],
                'low': [
                    'anyway', 'so', 'like', 'just', 'kind of', 'sort of', 'you know',
                    'I mean', 'basically', 'actually', 'pretty', 'really', 'totally',
                    'literally', 'honestly', 'seriously'
                ]
            }
        }
    
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze personality traits based on messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of personality analysis results
        """
        logger.info(f"Analyzing personality traits from {len(messages)} messages")
        
        if not messages:
            return {"error": "No messages to analyze"}
        
        try:
            # Extract text content from messages
            texts = []
            senders = set()
            
            for message in messages:
                if 'content' in message and message['content']:
                    texts.append(str(message['content']))
                elif 'text' in message and message['text']:
                    texts.append(str(message['text']))
                
                if 'sender' in message:
                    senders.add(message['sender'])
            
            # If multiple senders, we need to analyze each separately
            if len(senders) > 1:
                # Group messages by sender
                sender_messages = {}
                for message in messages:
                    sender = message.get('sender')
                    if not sender:
                        continue
                    
                    if sender not in sender_messages:
                        sender_messages[sender] = []
                    
                    content = message.get('content') or message.get('text')
                    if content:
                        sender_messages[sender].append(str(content))
                
                # Analyze each sender
                personality_profiles = {}
                for sender, sender_texts in sender_messages.items():
                    profile = await self._analyze_texts(sender_texts)
                    personality_profiles[sender] = profile
                
                return {
                    "multiple_senders": True,
                    "personality_profiles": personality_profiles
                }
            else:
                # Single sender or unknown senders
                profile = await self._analyze_texts(texts)
                
                return {
                    "multiple_senders": False,
                    "personality_profile": profile
                }
                
        except Exception as e:
            logger.error(f"Error analyzing personality: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_texts(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze personality traits from texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of personality traits
        """
        # Combine all texts
        combined_text = " ".join(texts).lower()
        
        # Analyze Big Five traits
        big_five_traits = await self._analyze_big_five(combined_text)
        
        # Analyze communication style
        communication_style = await self._analyze_communication_style(combined_text)
        
        # Analyze decision-making style
        decision_style = await self._analyze_decision_style(combined_text, big_five_traits)
        
        # Analyze interaction style
        interaction_style = await self._analyze_interaction_style(combined_text, big_five_traits)
        
        # Store personality traits
        self.personality_traits = big_five_traits
        
        return {
            "big_five_traits": big_five_traits,
            "communication_style": communication_style,
            "decision_style": decision_style,
            "interaction_style": interaction_style
        }
    
    async def _analyze_big_five(self, text: str) -> Dict[str, float]:
        """
        Analyze Big Five personality traits from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of Big Five trait scores
        """
        # Initialize trait scores
        trait_scores = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        # Count trait indicators in text
        for trait, indicators in self.trait_indicators.items():
            positive_count = 0
            negative_count = 0
            
            # Count positive indicators
            for word in indicators['positive']:
                positive_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            # Count negative indicators
            for word in indicators['negative']:
                negative_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            # Calculate trait score
            total_count = positive_count + negative_count
            if total_count > 0:
                # Normalize score between 0 and 1
                trait_scores[trait] = min(1.0, max(0.0, 0.5 + (positive_count - negative_count) / (2 * total_count)))
            
            # Apply some randomness to avoid identical scores
            trait_scores[trait] = min(1.0, max(0.0, trait_scores[trait] + np.random.normal(0, 0.05)))
        
        return trait_scores
    
    async def _analyze_communication_style(self, text: str) -> Dict[str, Any]:
        """
        Analyze communication style from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of communication style characteristics
        """
        # Initialize style scores
        style_scores = {
            'assertiveness': 0.5,
            'emotionality': 0.5,
            'formality': 0.5
        }
        
        # Count style indicators in text
        for style, indicators in self.communication_style_indicators.items():
            high_count = 0
            low_count = 0
            
            # Count high indicators
            for word in indicators['high']:
                high_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            # Count low indicators
            for word in indicators['low']:
                low_count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            # Calculate style score
            total_count = high_count + low_count
            if total_count > 0:
                # Normalize score between 0 and 1
                style_scores[style] = min(1.0, max(0.0, 0.5 + (high_count - low_count) / (2 * total_count)))
            
            # Apply some randomness to avoid identical scores
            style_scores[style] = min(1.0, max(0.0, style_scores[style] + np.random.normal(0, 0.05)))
        
        # Calculate additional metrics
        
        # Average sentence length
        sentences = re.split(r'[.!?]+', text)
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in valid_sentences) / len(valid_sentences) if valid_sentences else 0
        
        # Question frequency
        question_count = text.count('?')
        question_ratio = question_count / len(valid_sentences) if valid_sentences else 0
        
        # Exclamation frequency
        exclamation_count = text.count('!')
        exclamation_ratio = exclamation_count / len(valid_sentences) if valid_sentences else 0
        
        # First person pronoun usage
        first_person_count = len(re.findall(r'\b(i|me|my|mine|myself)\b', text))
        word_count = len(text.split())
        first_person_ratio = first_person_count / word_count if word_count > 0 else 0
        
        # Determine communication style descriptors
        descriptors = []
        
        if style_scores['assertiveness'] > 0.7:
            descriptors.append('direct')
        elif style_scores['assertiveness'] < 0.3:
            descriptors.append('tentative')
        
        if style_scores['emotionality'] > 0.7:
            descriptors.append('expressive')
        elif style_scores['emotionality'] < 0.3:
            descriptors.append('reserved')
        
        if style_scores['formality'] > 0.7:
            descriptors.append('formal')
        elif style_scores['formality'] < 0.3:
            descriptors.append('casual')
        
        if question_ratio > 0.3:
            descriptors.append('inquisitive')
        
        if exclamation_ratio > 0.2:
            descriptors.append('emphatic')
        
        if first_person_ratio > 0.1:
            descriptors.append('self-focused')
        elif first_person_ratio < 0.03:
            descriptors.append('objective')
        
        if avg_sentence_length > 20:
            descriptors.append('verbose')
        elif avg_sentence_length < 8:
            descriptors.append('concise')
        
        return {
            'scores': style_scores,
            'metrics': {
                'avg_sentence_length': float(avg_sentence_length),
                'question_ratio': float(question_ratio),
                'exclamation_ratio': float(exclamation_ratio),
                'first_person_ratio': float(first_person_ratio)
            },
            'descriptors': descriptors
        }
    
    async def _analyze_decision_style(self, text: str, big_five_traits: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze decision-making style based on text and Big Five traits.
        
        Args:
            text: Text to analyze
            big_five_traits: Big Five personality trait scores
            
        Returns:
            Dictionary of decision-making style characteristics
        """
        # Initialize decision style scores
        decision_scores = {
            'analytical': 0.0,
            'intuitive': 0.0,
            'deliberate': 0.0,
            'spontaneous': 0.0,
            'risk_averse': 0.0,
            'risk_seeking': 0.0
        }
        
        # Analytical vs. Intuitive
        # Higher openness and lower conscientiousness tend toward intuitive
        # Lower openness and higher conscientiousness tend toward analytical
        analytical_score = 0.5 + (big_five_traits['conscientiousness'] - big_five_traits['openness']) / 2
        decision_scores['analytical'] = min(1.0, max(0.0, analytical_score))
        decision_scores['intuitive'] = 1.0 - decision_scores['analytical']
        
        # Deliberate vs. Spontaneous
        # Higher conscientiousness and lower extraversion tend toward deliberate
        # Lower conscientiousness and higher extraversion tend toward spontaneous
        deliberate_score = 0.5 + (big_five_traits['conscientiousness'] - big_five_traits['extraversion']) / 2
        decision_scores['deliberate'] = min(1.0, max(0.0, deliberate_score))
        decision_scores['spontaneous'] = 1.0 - decision_scores['deliberate']
        
        # Risk-averse vs. Risk-seeking
        # Higher neuroticism and lower openness tend toward risk-averse
        # Lower neuroticism and higher openness tend toward risk-seeking
        risk_averse_score = 0.5 + (big_five_traits['neuroticism'] - big_five_traits['openness']) / 2
        decision_scores['risk_averse'] = min(1.0, max(0.0, risk_averse_score))
        decision_scores['risk_seeking'] = 1.0 - decision_scores['risk_averse']
        
        # Look for decision-related words in text
        analytical_words = ['analyze', 'consider', 'evaluate', 'assess', 'examine', 'weigh', 'compare', 'measure']
        intuitive_words = ['feel', 'sense', 'intuition', 'gut', 'instinct', 'impression', 'hunch']
        deliberate_words = ['plan', 'careful', 'thorough', 'methodical', 'systematic', 'organized', 'strategic']
        spontaneous_words = ['quick', 'immediate', 'spontaneous', 'impulse', 'sudden', 'instant', 'rapid']
        risk_averse_words = ['safe', 'secure', 'certain', 'sure', 'guaranteed', 'reliable', 'stable']
        risk_seeking_words = ['risk', 'chance', 'opportunity', 'adventure', 'exciting', 'possibility', 'potential']
        
        # Count occurrences of decision-related words
        analytical_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in analytical_words)
        intuitive_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in intuitive_words)
        deliberate_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in deliberate_words)
        spontaneous_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in spontaneous_words)
        risk_averse_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in risk_averse_words)
        risk_seeking_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in risk_seeking_words)
        
        # Adjust scores based on word counts
        if analytical_count + intuitive_count > 0:
            analytical_ratio = analytical_count / (analytical_count + intuitive_count)
            decision_scores['analytical'] = (decision_scores['analytical'] + analytical_ratio) / 2
            decision_scores['intuitive'] = 1.0 - decision_scores['analytical']
        
        if deliberate_count + spontaneous_count > 0:
            deliberate_ratio = deliberate_count / (deliberate_count + spontaneous_count)
            decision_scores['deliberate'] = (decision_scores['deliberate'] + deliberate_ratio) / 2
            decision_scores['spontaneous'] = 1.0 - decision_scores['deliberate']
        
        if risk_averse_count + risk_seeking_count > 0:
            risk_averse_ratio = risk_averse_count / (risk_averse_count + risk_seeking_count)
            decision_scores['risk_averse'] = (decision_scores['risk_averse'] + risk_averse_ratio) / 2
            decision_scores['risk_seeking'] = 1.0 - decision_scores['risk_averse']
        
        # Determine primary decision style
        primary_style = None
        if decision_scores['analytical'] > 0.6 and decision_scores['deliberate'] > 0.6:
            primary_style = 'Methodical'
        elif decision_scores['analytical'] > 0.6 and decision_scores['spontaneous'] > 0.6:
            primary_style = 'Logical'
        elif decision_scores['intuitive'] > 0.6 and decision_scores['deliberate'] > 0.6:
            primary_style = 'Reflective'
        elif decision_scores['intuitive'] > 0.6 and decision_scores['spontaneous'] > 0.6:
            primary_style = 'Instinctive'
        
        # Determine risk orientation
        risk_orientation = None
        if decision_scores['risk_averse'] > 0.7:
            risk_orientation = 'Highly Cautious'
        elif decision_scores['risk_averse'] > 0.6:
            risk_orientation = 'Cautious'
        elif decision_scores['risk_seeking'] > 0.7:
            risk_orientation = 'Bold'
        elif decision_scores['risk_seeking'] > 0.6:
            risk_orientation = 'Adventurous'
        else:
            risk_orientation = 'Balanced'
        
        return {
            'scores': decision_scores,
            'primary_style': primary_style,
            'risk_orientation': risk_orientation
        }
    
    async def _analyze_interaction_style(self, text: str, big_five_traits: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze interaction style based on text and Big Five traits.
        
        Args:
            text: Text to analyze
            big_five_traits: Big Five personality trait scores
            
        Returns:
            Dictionary of interaction style characteristics
        """
        # Initialize interaction style scores
        interaction_scores = {
            'dominant': 0.0,
            'submissive': 0.0,
            'cooperative': 0.0,
            'competitive': 0.0,
            'warm': 0.0,
            'cold': 0.0
        }
        
        # Dominant vs. Submissive
        # Higher extraversion and lower agreeableness tend toward dominant
        # Lower extraversion and higher agreeableness tend toward submissive
        dominant_score = 0.5 + (big_five_traits['extraversion'] - big_five_traits['agreeableness']) / 2
        interaction_scores['dominant'] = min(1.0, max(0.0, dominant_score))
        interaction_scores['submissive'] = 1.0 - interaction_scores['dominant']
        
        # Cooperative vs. Competitive
        # Higher agreeableness and lower neuroticism tend toward cooperative
        # Lower agreeableness and higher neuroticism tend toward competitive
        cooperative_score = 0.5 + (big_five_traits['agreeableness'] - big_five_traits['neuroticism']) / 2
        interaction_scores['cooperative'] = min(1.0, max(0.0, cooperative_score))
        interaction_scores['competitive'] = 1.0 - interaction_scores['cooperative']
        
        # Warm vs. Cold
        # Higher agreeableness and higher extraversion tend toward warm
        # Lower agreeableness and lower extraversion tend toward cold
        warm_score = 0.5 + (big_five_traits['agreeableness'] + big_five_traits['extraversion'] - 1.0) / 2
        interaction_scores['warm'] = min(1.0, max(0.0, warm_score))
        interaction_scores['cold'] = 1.0 - interaction_scores['warm']
        
        # Look for interaction-related words in text
        dominant_words = ['lead', 'direct', 'control', 'command', 'instruct', 'decide', 'determine', 'insist']
        submissive_words = ['follow', 'agree', 'accept', 'comply', 'yield', 'submit', 'obey', 'accommodate']
        cooperative_words = ['help', 'support', 'assist', 'collaborate', 'together', 'team', 'share', 'contribute']
        competitive_words = ['win', 'beat', 'compete', 'challenge', 'outperform', 'achieve', 'succeed', 'best']
        warm_words = ['care', 'love', 'appreciate', 'enjoy', 'like', 'friend', 'kind', 'nice', 'happy']
        cold_words = ['indifferent', 'detached', 'distant', 'aloof', 'reserved', 'formal', 'professional', 'objective']
        
        # Count occurrences of interaction-related words
        dominant_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in dominant_words)
        submissive_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in submissive_words)
        cooperative_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in cooperative_words)
        competitive_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in competitive_words)
        warm_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in warm_words)
        cold_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text)) for word in cold_words)
        
        # Adjust scores based on word counts
        if dominant_count + submissive_count > 0:
            dominant_ratio = dominant_count / (dominant_count + submissive_count)
            interaction_scores['dominant'] = (interaction_scores['dominant'] + dominant_ratio) / 2
            interaction_scores['submissive'] = 1.0 - interaction_scores['dominant']
        
        if cooperative_count + competitive_count > 0:
            cooperative_ratio = cooperative_count / (cooperative_count + competitive_count)
            interaction_scores['cooperative'] = (interaction_scores['cooperative'] + cooperative_ratio) / 2
            interaction_scores['competitive'] = 1.0 - interaction_scores['cooperative']
        
        if warm_count + cold_count > 0:
            warm_ratio = warm_count / (warm_count + cold_count)
            interaction_scores['warm'] = (interaction_scores['warm'] + warm_ratio) / 2
            interaction_scores['cold'] = 1.0 - interaction_scores['warm']
        
        # Determine primary interaction style
        primary_style = None
        if interaction_scores['dominant'] > 0.6 and interaction_scores['cooperative'] > 0.6:
            primary_style = 'Leading'
        elif interaction_scores['dominant'] > 0.6 and interaction_scores['competitive'] > 0.6:
            primary_style = 'Directing'
        elif interaction_scores['submissive'] > 0.6 and interaction_scores['cooperative'] > 0.6:
            primary_style = 'Supporting'
        elif interaction_scores['submissive'] > 0.6 and interaction_scores['competitive'] > 0.6:
            primary_style = 'Avoiding'
        
        # Determine interpersonal warmth
        interpersonal_warmth = None
        if interaction_scores['warm'] > 0.7:
            interpersonal_warmth = 'Very Warm'
        elif interaction_scores['warm'] > 0.6:
            interpersonal_warmth = 'Warm'
        elif interaction_scores['cold'] > 0.7:
            interpersonal_warmth = 'Very Reserved'
        elif interaction_scores['cold'] > 0.6:
            interpersonal_warmth = 'Reserved'
        else:
            interpersonal_warmth = 'Neutral'
        
        return {
            'scores': interaction_scores,
            'primary_style': primary_style,
            'interpersonal_warmth': interpersonal_warmth
        }
    
    def get_personality_traits(self) -> Dict[str, float]:
        """
        Get the current personality trait scores.
        
        Returns:
            Dictionary of personality trait scores
        """
        return self.personality_traits