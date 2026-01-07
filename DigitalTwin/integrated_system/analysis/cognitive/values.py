"""
Values analysis module for cognitive analysis.

This module provides functionality for analyzing personal values and priorities
based on communication data and behavior patterns.
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)

class ValuesAnalyzer:
    """Analyzer for personal values and priorities."""
    
    def __init__(self):
        """Initialize the values analyzer."""
        self.nlp_available = False
        
        # Try to import NLP libraries
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.nlp_available = True
            logger.info("spaCy NLP model loaded successfully")
        except:
            logger.warning("spaCy model not available for values analysis")
        
        # Initialize values dictionary
        self.values = {}
        
        # Initialize value indicators
        self._initialize_value_indicators()
    
    def _initialize_value_indicators(self):
        """Initialize linguistic indicators for values."""
        # Words and phrases associated with each value
        self.value_indicators = {
            'achievement': [
                'success', 'accomplish', 'achieve', 'win', 'excel', 'perform', 'goal',
                'ambition', 'progress', 'advance', 'improve', 'develop', 'grow', 'result',
                'outcome', 'milestone', 'objective', 'target', 'aspire', 'strive'
            ],
            'benevolence': [
                'help', 'care', 'support', 'assist', 'aid', 'benefit', 'serve',
                'kindness', 'compassion', 'empathy', 'sympathy', 'concern', 'welfare',
                'wellbeing', 'charity', 'volunteer', 'donate', 'give', 'share', 'generous'
            ],
            'conformity': [
                'follow', 'obey', 'comply', 'adhere', 'respect', 'rule', 'norm',
                'standard', 'convention', 'tradition', 'custom', 'proper', 'appropriate',
                'correct', 'right', 'acceptable', 'expected', 'should', 'must', 'ought'
            ],
            'hedonism': [
                'enjoy', 'pleasure', 'fun', 'delight', 'happy', 'joy', 'excitement',
                'thrill', 'entertainment', 'leisure', 'relax', 'comfort', 'indulge',
                'treat', 'luxury', 'experience', 'sensation', 'feeling', 'desire', 'want'
            ],
            'power': [
                'control', 'influence', 'lead', 'authority', 'command', 'direct', 'manage',
                'supervise', 'dominate', 'rule', 'govern', 'power', 'strength', 'force',
                'impact', 'status', 'position', 'rank', 'prestige', 'reputation'
            ],
            'security': [
                'safe', 'secure', 'protect', 'defend', 'guard', 'shield', 'shelter',
                'stability', 'certainty', 'predictability', 'reliability', 'dependability',
                'trust', 'confidence', 'assurance', 'guarantee', 'insurance', 'prevention',
                'precaution', 'caution'
            ],
            'self_direction': [
                'choose', 'decide', 'determine', 'independence', 'freedom', 'liberty',
                'autonomy', 'self-reliance', 'self-sufficiency', 'self-determination',
                'option', 'alternative', 'preference', 'selection', 'choice', 'path',
                'direction', 'way', 'route', 'course'
            ],
            'stimulation': [
                'new', 'novel', 'change', 'variety', 'diverse', 'different', 'unique',
                'challenge', 'adventure', 'excitement', 'thrill', 'risk', 'danger',
                'daring', 'bold', 'brave', 'courageous', 'explore', 'discover', 'experience'
            ],
            'tradition': [
                'tradition', 'custom', 'ritual', 'ceremony', 'heritage', 'legacy', 'history',
                'ancestor', 'generation', 'family', 'culture', 'religion', 'faith', 'belief',
                'practice', 'habit', 'routine', 'conventional', 'established', 'old'
            ],
            'universalism': [
                'equality', 'justice', 'fairness', 'rights', 'freedom', 'peace', 'harmony',
                'unity', 'tolerance', 'acceptance', 'understanding', 'environment', 'nature',
                'earth', 'planet', 'sustainable', 'conservation', 'protection', 'preservation',
                'diversity'
            ]
        }
        
        # Moral foundations indicators
        self.moral_foundations = {
            'care_harm': [
                'care', 'harm', 'suffer', 'protect', 'safe', 'defend', 'hurt', 'pain',
                'compassion', 'empathy', 'kindness', 'gentle', 'cruel', 'brutal', 'abuse',
                'violence', 'victim', 'vulnerable', 'comfort', 'sympathy'
            ],
            'fairness_cheating': [
                'fair', 'unfair', 'equal', 'unequal', 'justice', 'injustice', 'right',
                'wrong', 'deserve', 'bias', 'discriminate', 'prejudice', 'privilege',
                'rights', 'equity', 'impartial', 'balanced', 'honest', 'cheat', 'fraud'
            ],
            'loyalty_betrayal': [
                'loyal', 'disloyal', 'betray', 'traitor', 'faithful', 'unfaithful', 'patriot',
                'team', 'group', 'family', 'community', 'nation', 'together', 'united',
                'solidarity', 'devotion', 'commitment', 'dedication', 'allegiance', 'trust'
            ],
            'authority_subversion': [
                'authority', 'respect', 'obey', 'disobey', 'defer', 'rebel', 'tradition',
                'hierarchy', 'order', 'chaos', 'command', 'submit', 'comply', 'defy',
                'leader', 'follower', 'rank', 'position', 'status', 'superior'
            ],
            'sanctity_degradation': [
                'pure', 'impure', 'clean', 'dirty', 'sacred', 'profane', 'holy', 'sin',
                'disgust', 'gross', 'dignity', 'honor', 'shame', 'decency', 'indecent',
                'obscene', 'wholesome', 'corrupt', 'innocent', 'depraved'
            ],
            'liberty_oppression': [
                'freedom', 'liberty', 'oppress', 'tyranny', 'independence', 'dependent',
                'choice', 'force', 'coerce', 'autonomy', 'restrict', 'constrain', 'control',
                'dictate', 'impose', 'free', 'liberate', 'emancipate', 'enslave', 'dominate'
            ]
        }
    
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze values based on messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of values analysis results
        """
        logger.info(f"Analyzing values from {len(messages)} messages")
        
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
                values_profiles = {}
                for sender, sender_texts in sender_messages.items():
                    profile = await self._analyze_texts(sender_texts)
                    values_profiles[sender] = profile
                
                return {
                    "multiple_senders": True,
                    "values_profiles": values_profiles
                }
            else:
                # Single sender or unknown senders
                profile = await self._analyze_texts(texts)
                
                return {
                    "multiple_senders": False,
                    "values_profile": profile
                }
                
        except Exception as e:
            logger.error(f"Error analyzing values: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_texts(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze values from texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of values analysis results
        """
        # Combine all texts
        combined_text = " ".join(texts).lower()
        
        # Analyze Schwartz values
        schwartz_values = await self._analyze_schwartz_values(combined_text)
        
        # Analyze moral foundations
        moral_foundations = await self._analyze_moral_foundations(combined_text)
        
        # Analyze value priorities
        value_priorities = await self._analyze_value_priorities(combined_text, schwartz_values)
        
        # Store values
        self.values = {
            "schwartz_values": schwartz_values,
            "moral_foundations": moral_foundations,
            "value_priorities": value_priorities
        }
        
        return {
            "schwartz_values": schwartz_values,
            "moral_foundations": moral_foundations,
            "value_priorities": value_priorities
        }
    
    async def _analyze_schwartz_values(self, text: str) -> Dict[str, float]:
        """
        Analyze Schwartz values from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of Schwartz value scores
        """
        # Initialize value scores
        value_scores = {value: 0.0 for value in self.value_indicators.keys()}
        
        # Count value indicators in text
        for value, indicators in self.value_indicators.items():
            count = 0
            for word in indicators:
                count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            value_scores[value] = count
        
        # Normalize scores
        total_count = sum(value_scores.values())
        if total_count > 0:
            for value in value_scores:
                value_scores[value] = value_scores[value] / total_count
        
        # Apply some randomness to avoid identical scores
        for value in value_scores:
            value_scores[value] = min(1.0, max(0.0, value_scores[value] + np.random.normal(0, 0.02)))
        
        # Re-normalize after adding randomness
        total = sum(value_scores.values())
        if total > 0:
            for value in value_scores:
                value_scores[value] = value_scores[value] / total
        
        return value_scores
    
    async def _analyze_moral_foundations(self, text: str) -> Dict[str, float]:
        """
        Analyze moral foundations from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of moral foundation scores
        """
        # Initialize foundation scores
        foundation_scores = {foundation: 0.0 for foundation in self.moral_foundations.keys()}
        
        # Count foundation indicators in text
        for foundation, indicators in self.moral_foundations.items():
            count = 0
            for word in indicators:
                count += len(re.findall(r'\b' + re.escape(word) + r'\b', text))
            
            foundation_scores[foundation] = count
        
        # Normalize scores
        total_count = sum(foundation_scores.values())
        if total_count > 0:
            for foundation in foundation_scores:
                foundation_scores[foundation] = foundation_scores[foundation] / total_count
        
        # Apply some randomness to avoid identical scores
        for foundation in foundation_scores:
            foundation_scores[foundation] = min(1.0, max(0.0, foundation_scores[foundation] + np.random.normal(0, 0.02)))
        
        # Re-normalize after adding randomness
        total = sum(foundation_scores.values())
        if total > 0:
            for foundation in foundation_scores:
                foundation_scores[foundation] = foundation_scores[foundation] / total
        
        return foundation_scores
    
    async def _analyze_value_priorities(self, text: str, schwartz_values: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze value priorities based on text and Schwartz values.
        
        Args:
            text: Text to analyze
            schwartz_values: Schwartz value scores
            
        Returns:
            Dictionary of value priority analysis
        """
        # Get top values
        sorted_values = sorted(schwartz_values.items(), key=lambda x: x[1], reverse=True)
        top_values = sorted_values[:3]
        bottom_values = sorted_values[-3:]
        
        # Analyze value conflicts
        value_conflicts = []
        
        # Check for potential conflicts between top values
        conflict_pairs = [
            ('self_direction', 'conformity'),
            ('self_direction', 'tradition'),
            ('stimulation', 'security'),
            ('hedonism', 'conformity'),
            ('achievement', 'benevolence'),
            ('power', 'universalism'),
            ('power', 'benevolence')
        ]
        
        for value1, value2 in conflict_pairs:
            if (value1 in [v[0] for v in top_values] and value2 in [v[0] for v in top_values]):
                conflict_strength = min(schwartz_values[value1], schwartz_values[value2])
                value_conflicts.append({
                    'values': [value1, value2],
                    'strength': conflict_strength
                })
        
        # Determine value orientation
        # Self-enhancement vs. Self-transcendence
        self_enhancement = schwartz_values['achievement'] + schwartz_values['power'] + schwartz_values['hedonism']
        self_transcendence = schwartz_values['benevolence'] + schwartz_values['universalism']
        
        # Conservation vs. Openness to change
        conservation = schwartz_values['security'] + schwartz_values['conformity'] + schwartz_values['tradition']
        openness_to_change = schwartz_values['self_direction'] + schwartz_values['stimulation'] + schwartz_values['hedonism']
        
        # Determine primary value orientation
        primary_orientation = None
        if self_enhancement > self_transcendence and self_enhancement > conservation and self_enhancement > openness_to_change:
            primary_orientation = 'Self-Enhancement'
        elif self_transcendence > self_enhancement and self_transcendence > conservation and self_transcendence > openness_to_change:
            primary_orientation = 'Self-Transcendence'
        elif conservation > self_enhancement and conservation > self_transcendence and conservation > openness_to_change:
            primary_orientation = 'Conservation'
        elif openness_to_change > self_enhancement and openness_to_change > self_transcendence and openness_to_change > conservation:
            primary_orientation = 'Openness to Change'
        
        # Determine value stability
        # Check if there are clear priorities or if values are more evenly distributed
        value_std = np.std(list(schwartz_values.values()))
        value_stability = 'Stable' if value_std > 0.05 else 'Flexible'
        
        return {
            'top_values': [{'value': v[0], 'score': v[1]} for v in top_values],
            'bottom_values': [{'value': v[0], 'score': v[1]} for v in bottom_values],
            'value_conflicts': value_conflicts,
            'orientations': {
                'self_enhancement': float(self_enhancement),
                'self_transcendence': float(self_transcendence),
                'conservation': float(conservation),
                'openness_to_change': float(openness_to_change)
            },
            'primary_orientation': primary_orientation,
            'value_stability': value_stability
        }
    
    def get_values(self) -> Dict[str, Any]:
        """
        Get the current values analysis results.
        
        Returns:
            Dictionary of values analysis results
        """
        return self.values