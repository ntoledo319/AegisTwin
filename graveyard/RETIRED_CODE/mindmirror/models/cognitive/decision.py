"""Decision modeling for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import re
from collections import Counter, defaultdict
import json
import random
from datetime import datetime

from ...core.config import config_manager
from ...core.utils import normalize_text, save_pickle, load_pickle, ensure_dir

class DecisionModel:
    """Models decision-making processes and preferences."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the decision model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Decision style parameters
        self.decision_style = {
            'analytical': 0.5,  # Analytical vs. intuitive
            'risk_taking': 0.5,  # Risk-taking vs. risk-averse
            'speed': 0.5,  # Quick vs. deliberate
            'independence': 0.5,  # Independent vs. collaborative
            'optimism': 0.5,  # Optimistic vs. pessimistic
            'flexibility': 0.5,  # Flexible vs. rigid
            'emotion_influence': 0.5  # Emotional vs. rational
        }
        
        # Decision history
        self.decision_history = []
        
        # Decision patterns
        self.decision_patterns = {}
        
        # Decision triggers
        self.decision_triggers = {}
        
        # Decision preferences
        self.preferences = {}
        
        # Loaded flag
        self.is_loaded = False
        
        # Decision lexicons
        self._initialize_lexicons()
        
    def _initialize_lexicons(self) -> None:
        """Initialize lexicons for decision style detection."""
        # Decision style lexicon
        self.decision_lexicon = {
            'analytical': [
                'analyze', 'consider', 'evaluate', 'assess', 'examine', 'review',
                'study', 'research', 'investigate', 'explore', 'compare', 'contrast',
                'pros and cons', 'advantages', 'disadvantages', 'evidence', 'data',
                'information', 'facts', 'logic', 'reason', 'rational', 'objective',
                'systematic', 'methodical', 'thorough', 'detailed', 'careful'
            ],
            'intuitive': [
                'feel', 'sense', 'intuition', 'gut', 'instinct', 'hunch', 'impression',
                'spontaneous', 'immediate', 'automatic', 'quick', 'instant', 'natural',
                'innate', 'inherent', 'intrinsic', 'subconscious', 'unconscious',
                'implicit', 'tacit', 'intuitive', 'feeling', 'emotion', 'subjective'
            ],
            'risk_taking': [
                'risk', 'chance', 'gamble', 'bet', 'wager', 'venture', 'dare',
                'bold', 'brave', 'courageous', 'fearless', 'adventurous', 'daring',
                'audacious', 'intrepid', 'reckless', 'impulsive', 'spontaneous',
                'exciting', 'thrill', 'challenge', 'opportunity', 'potential'
            ],
            'risk_averse': [
                'safe', 'secure', 'certain', 'sure', 'guaranteed', 'reliable',
                'dependable', 'stable', 'steady', 'consistent', 'predictable',
                'cautious', 'careful', 'prudent', 'conservative', 'moderate',
                'measured', 'calculated', 'deliberate', 'thoughtful', 'wary'
            ],
            'quick': [
                'quick', 'fast', 'rapid', 'swift', 'speedy', 'prompt', 'immediate',
                'instant', 'instantaneous', 'hasty', 'hurried', 'rushed', 'urgent',
                'expedient', 'efficient', 'decisive', 'determined', 'resolute'
            ],
            'deliberate': [
                'slow', 'deliberate', 'careful', 'thorough', 'methodical', 'systematic',
                'meticulous', 'detailed', 'comprehensive', 'exhaustive', 'complete',
                'full', 'extensive', 'in-depth', 'rigorous', 'diligent', 'patient'
            ],
            'independent': [
                'independent', 'self', 'alone', 'individual', 'personal', 'private',
                'autonomous', 'self-reliant', 'self-sufficient', 'self-directed',
                'self-determined', 'self-governed', 'sovereign', 'free', 'separate'
            ],
            'collaborative': [
                'collaborative', 'together', 'group', 'team', 'collective', 'joint',
                'shared', 'mutual', 'common', 'cooperative', 'coordinated', 'combined',
                'united', 'allied', 'associated', 'affiliated', 'partnered', 'we'
            ],
            'optimistic': [
                'optimistic', 'positive', 'hopeful', 'confident', 'upbeat', 'cheerful',
                'bright', 'sunny', 'rosy', 'promising', 'favorable', 'encouraging',
                'reassuring', 'heartening', 'auspicious', 'propitious', 'good'
            ],
            'pessimistic': [
                'pessimistic', 'negative', 'doubtful', 'skeptical', 'cynical', 'gloomy',
                'dark', 'bleak', 'dismal', 'dire', 'grave', 'serious', 'severe',
                'critical', 'unfavorable', 'discouraging', 'disheartening', 'bad'
            ],
            'flexible': [
                'flexible', 'adaptable', 'adjustable', 'versatile', 'variable',
                'changeable', 'fluid', 'dynamic', 'plastic', 'malleable', 'pliable',
                'open', 'receptive', 'responsive', 'accommodating', 'amenable'
            ],
            'rigid': [
                'rigid', 'inflexible', 'unyielding', 'unbending', 'stiff', 'firm',
                'fixed', 'set', 'established', 'settled', 'determined', 'definite',
                'absolute', 'strict', 'exact', 'precise', 'specific', 'particular'
            ],
            'emotional': [
                'emotional', 'feeling', 'sentiment', 'passion', 'affect', 'mood',
                'temperament', 'disposition', 'attitude', 'sensibility', 'sensitivity',
                'heart', 'soul', 'spirit', 'psyche', 'mind', 'consciousness'
            ],
            'rational': [
                'rational', 'logical', 'reasonable', 'sensible', 'sound', 'valid',
                'cogent', 'coherent', 'consistent', 'orderly', 'methodical', 'systematic',
                'organized', 'structured', 'planned', 'deliberate', 'intentional'
            ]
        }
        
        # Decision trigger patterns
        self.trigger_patterns = [
            r'(?:I|we) (?:need|have|want) to (?:decide|choose|pick|select|determine) (?:between|if|whether|about|on) (.{5,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:trying|attempting|working) to (?:decide|choose|figure out|determine) (?:between|if|whether|about|on) (.{5,50})',
            r'(?:I|we) (?:can\'t|cannot) (?:decide|choose|determine|figure out) (?:between|if|whether|about|on) (.{5,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:not sure|uncertain|unsure|undecided) (?:about|on|if|whether) (.{5,50})',
            r'(?:Should|Shall|Could|Would|Will) (?:I|we) (.{5,50})\?',
            r'(?:I|we) (?:decided|chose|picked|selected|determined|opted) (?:to|for|against|on|that) (.{5,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:going|planning|intending) to (.{5,50})',
            r'(?:I|we) (?:think|believe|feel) (?:I|we) should (.{5,50})',
            r'(?:I|we) (?:don\'t|do not) (?:think|believe|feel) (?:I|we) should (.{5,50})'
        ]
        
        # Preference patterns
        self.preference_patterns = [
            r'(?:I|we) (?:like|love|enjoy|prefer|favor|fancy) (.{5,50})',
            r'(?:I|we) (?:don\'t|do not) (?:like|love|enjoy|prefer|favor|fancy) (.{5,50})',
            r'(?:I|we) (?:hate|dislike|detest|loathe|despise|can\'t stand) (.{5,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:fond of|keen on|into|partial to) (.{5,50})',
            r'(?:I\'m|I am|We\'re|We are) (?:not fond of|not keen on|not into|not partial to) (.{5,50})',
            r'(?:My|Our) favorite (.{5,50})',
            r'(?:I|we) would (?:rather|prefer to) (.{5,50})',
            r'(?:I|we) would (?:never|not) (.{5,50})'
        ]
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the decision model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training decision model...")
        
        # Filter to outgoing messages if user_name is provided
        if user_name:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing' or m.get('sender_name') == user_name]
        else:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing']
        
        print(f"Training on {len(outgoing_messages)} outgoing messages")
        
        # Extract text content
        texts = [m.get('text', '') for m in outgoing_messages if m.get('text')]
        
        # Analyze decision style
        self._analyze_decision_style(texts)
        
        # Extract decision history
        self._extract_decision_history(outgoing_messages)
        
        # Analyze decision patterns
        self._analyze_decision_patterns()
        
        # Extract decision triggers
        self._extract_decision_triggers(texts)
        
        # Extract preferences
        self._extract_preferences(texts)
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("Decision model training complete")
        
    def _analyze_decision_style(self, texts: List[str]) -> None:
        """Analyze decision style from texts.
        
        Args:
            texts: List of text messages.
        """
        if not texts:
            return
            
        # Initialize style scores
        style_scores = {
            'analytical': 0,
            'intuitive': 0,
            'risk_taking': 0,
            'risk_averse': 0,
            'quick': 0,
            'deliberate': 0,
            'independent': 0,
            'collaborative': 0,
            'optimistic': 0,
            'pessimistic': 0,
            'flexible': 0,
            'rigid': 0,
            'emotional': 0,
            'rational': 0
        }
        
        # Count style-related words
        for text in texts:
            text_lower = text.lower()
            
            for style, keywords in self.decision_lexicon.items():
                for keyword in keywords:
                    # Count occurrences of the keyword
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                    style_scores[style] += count
                    
        # Calculate decision style parameters
        if style_scores['analytical'] + style_scores['intuitive'] > 0:
            self.decision_style['analytical'] = style_scores['analytical'] / (style_scores['analytical'] + style_scores['intuitive'])
            
        if style_scores['risk_taking'] + style_scores['risk_averse'] > 0:
            self.decision_style['risk_taking'] = style_scores['risk_taking'] / (style_scores['risk_taking'] + style_scores['risk_averse'])
            
        if style_scores['quick'] + style_scores['deliberate'] > 0:
            self.decision_style['speed'] = style_scores['quick'] / (style_scores['quick'] + style_scores['deliberate'])
            
        if style_scores['independent'] + style_scores['collaborative'] > 0:
            self.decision_style['independence'] = style_scores['independent'] / (style_scores['independent'] + style_scores['collaborative'])
            
        if style_scores['optimistic'] + style_scores['pessimistic'] > 0:
            self.decision_style['optimism'] = style_scores['optimistic'] / (style_scores['optimistic'] + style_scores['pessimistic'])
            
        if style_scores['flexible'] + style_scores['rigid'] > 0:
            self.decision_style['flexibility'] = style_scores['flexible'] / (style_scores['flexible'] + style_scores['rigid'])
            
        if style_scores['emotional'] + style_scores['rational'] > 0:
            self.decision_style['emotion_influence'] = style_scores['emotional'] / (style_scores['emotional'] + style_scores['rational'])
    
    def _extract_decision_history(self, messages: List[Dict[str, Any]]) -> None:
        """Extract decision history from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        # Decision indicator patterns
        decision_patterns = [
            r'(?:I|we) (?:decided|chose|picked|selected|determined|opted) (?:to|for|against|on|that) (.{5,100})',
            r'(?:I\'m|I am|We\'re|We are) (?:going|planning|intending) to (.{5,100})',
            r'(?:I|we) (?:will|won\'t|will not) (.{5,100})',
            r'(?:I|we) (?:have|haven\'t|have not) (?:decided|chosen|picked|selected|determined) (?:to|for|against|on|that) (.{5,100})'
        ]
        
        # Extract decisions
        for message in messages:
            text = message.get('text', '')
            if not text:
                continue
                
            message_date = message.get('message_date', '')
            if not message_date:
                continue
                
            try:
                date = datetime.strptime(message_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                date = None
                
            for pattern in decision_patterns:
                matches = re.findall(pattern, text)
                
                for match in matches:
                    decision = {
                        'text': match.strip(),
                        'date': date,
                        'context': text,
                        'message_id': message.get('index', '')
                    }
                    
                    self.decision_history.append(decision)
                    
        # Sort by date
        self.decision_history = sorted(self.decision_history, key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Limit history size
        max_history = config_manager.get_value('mindmirror', 'cognitive_model.decision.decision_history_length', 100)
        if len(self.decision_history) > max_history:
            self.decision_history = self.decision_history[-max_history:]
    
    def _analyze_decision_patterns(self) -> None:
        """Analyze patterns in decision history."""
        if not self.decision_history:
            return
            
        # Extract decision topics
        topics = []
        for decision in self.decision_history:
            text = decision['text'].lower()
            
            # Check for common decision topics
            topic_keywords = {
                'work': ['work', 'job', 'career', 'office', 'boss', 'colleague', 'meeting', 'project', 'task', 'deadline'],
                'education': ['school', 'college', 'university', 'class', 'course', 'study', 'homework', 'assignment', 'exam', 'test', 'grade'],
                'social': ['friend', 'hang out', 'party', 'dinner', 'lunch', 'coffee', 'drink', 'bar', 'club', 'social', 'people'],
                'family': ['family', 'parent', 'mom', 'dad', 'mother', 'father', 'brother', 'sister', 'sibling', 'relative'],
                'relationship': ['date', 'dating', 'boyfriend', 'girlfriend', 'partner', 'relationship', 'marriage', 'wedding', 'love', 'romantic'],
                'health': ['health', 'doctor', 'hospital', 'sick', 'ill', 'disease', 'condition', 'symptom', 'medicine', 'treatment', 'therapy'],
                'finance': ['money', 'finance', 'financial', 'bank', 'account', 'budget', 'spend', 'save', 'invest', 'loan', 'debt', 'credit'],
                'travel': ['travel', 'trip', 'vacation', 'holiday', 'flight', 'hotel', 'booking', 'reservation', 'destination', 'tour'],
                'shopping': ['buy', 'purchase', 'shop', 'shopping', 'store', 'mall', 'online', 'amazon', 'ebay', 'product', 'item'],
                'food': ['food', 'eat', 'restaurant', 'meal', 'breakfast', 'lunch', 'dinner', 'cook', 'cooking', 'recipe', 'grocery'],
                'entertainment': ['movie', 'film', 'show', 'tv', 'television', 'series', 'episode', 'watch', 'stream', 'netflix', 'hulu', 'amazon prime'],
                'technology': ['tech', 'technology', 'computer', 'laptop', 'phone', 'smartphone', 'device', 'gadget', 'app', 'software', 'hardware'],
                'housing': ['house', 'apartment', 'flat', 'condo', 'rent', 'lease', 'mortgage', 'move', 'moving', 'roommate', 'landlord']
            }
            
            found_topics = []
            for topic, keywords in topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    found_topics.append(topic)
                    
            # If no specific topic found, use 'other'
            if not found_topics:
                found_topics = ['other']
                
            topics.append(found_topics[0])  # Use the first matching topic
            
        # Count topics
        topic_counts = Counter(topics)
        
        # Calculate decision patterns
        self.decision_patterns = {
            'topics': dict(topic_counts),
            'total_decisions': len(self.decision_history)
        }
        
        # Normalize topic counts
        total = sum(topic_counts.values())
        if total > 0:
            self.decision_patterns['topic_distribution'] = {k: v / total for k, v in topic_counts.items()}
    
    def _extract_decision_triggers(self, texts: List[str]) -> None:
        """Extract decision triggers from texts.
        
        Args:
            texts: List of text messages.
        """
        # Extract triggers
        triggers = []
        for text in texts:
            for pattern in self.trigger_patterns:
                matches = re.findall(pattern, text)
                triggers.extend(matches)
                
        # Clean triggers
        cleaned_triggers = [trigger.strip() for trigger in triggers if len(trigger.strip()) > 5]
        
        # Group similar triggers
        trigger_groups = {}
        for trigger in cleaned_triggers:
            trigger_lower = trigger.lower()
            
            # Check if similar to existing group
            found_group = False
            for group_key, group_triggers in trigger_groups.items():
                # Check similarity based on common words
                trigger_words = set(trigger_lower.split())
                group_words = set(group_key.lower().split())
                
                common_words = trigger_words.intersection(group_words)
                
                # If significant overlap, add to this group
                if len(common_words) >= 2 and len(common_words) / len(trigger_words) > 0.3:
                    group_triggers.append(trigger)
                    found_group = True
                    break
                    
            # If no similar group found, create new group
            if not found_group:
                trigger_groups[trigger] = [trigger]
                
        # Convert to decision triggers format
        self.decision_triggers = {
            'groups': trigger_groups,
            'common_triggers': [group for group, triggers in sorted(
                trigger_groups.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:10]]
        }
    
    def _extract_preferences(self, texts: List[str]) -> None:
        """Extract preferences from texts.
        
        Args:
            texts: List of text messages.
        """
        # Extract likes and dislikes
        likes = []
        dislikes = []
        
        for text in texts:
            # Extract likes
            for pattern in self.preference_patterns[:4]:  # Positive preference patterns
                matches = re.findall(pattern, text)
                likes.extend(matches)
                
            # Extract dislikes
            for pattern in self.preference_patterns[4:]:  # Negative preference patterns
                matches = re.findall(pattern, text)
                dislikes.extend(matches)
                
        # Clean preferences
        cleaned_likes = [like.strip() for like in likes if len(like.strip()) > 3]
        cleaned_dislikes = [dislike.strip() for dislike in dislikes if len(dislike.strip()) > 3]
        
        # Group similar preferences
        like_groups = self._group_similar_items(cleaned_likes)
        dislike_groups = self._group_similar_items(cleaned_dislikes)
        
        # Convert to preferences format
        self.preferences = {
            'likes': {group: items for group, items in sorted(
                like_groups.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )},
            'dislikes': {group: items for group, items in sorted(
                dislike_groups.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )}
        }
    
    def _group_similar_items(self, items: List[str]) -> Dict[str, List[str]]:
        """Group similar items based on common words.
        
        Args:
            items: List of items to group.
            
        Returns:
            Dictionary mapping group keys to lists of items.
        """
        groups = {}
        for item in items:
            item_lower = item.lower()
            
            # Check if similar to existing group
            found_group = False
            for group_key, group_items in groups.items():
                # Check similarity based on common words
                item_words = set(item_lower.split())
                group_words = set(group_key.lower().split())
                
                common_words = item_words.intersection(group_words)
                
                # If significant overlap, add to this group
                if len(common_words) >= 2 and len(common_words) / len(item_words) > 0.3:
                    group_items.append(item)
                    found_group = True
                    break
                    
            # If no similar group found, create new group
            if not found_group:
                groups[item] = [item]
                
        return groups
    
    def save(self) -> None:
        """Save the decision model."""
        model_path = os.path.join(self.model_dir, 'decision_model.pkl')
        save_pickle(self.__dict__, model_path)
        print(f"Decision model saved to {model_path}")
    
    def load(self) -> bool:
        """Load the decision model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        model_path = os.path.join(self.model_dir, 'decision_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.__dict__.update(data)
                self.is_loaded = True
                print(f"Decision model loaded from {model_path}")
                return True
            except Exception as e:
                print(f"Error loading decision model: {e}")
                return False
        else:
            print(f"Decision model not found at {model_path}")
            return False
    
    def get_decision_style(self) -> Dict[str, float]:
        """Get decision style parameters.
        
        Returns:
            Dictionary of decision style parameters.
        """
        return self.decision_style
    
    def get_decision_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get decision history.
        
        Args:
            limit: Maximum number of decisions to return.
            
        Returns:
            List of decision dictionaries.
        """
        if limit:
            return self.decision_history[-limit:]
        return self.decision_history
    
    def get_decision_patterns(self) -> Dict[str, Any]:
        """Get decision patterns.
        
        Returns:
            Dictionary of decision patterns.
        """
        return self.decision_patterns
    
    def get_decision_triggers(self) -> Dict[str, Any]:
        """Get decision triggers.
        
        Returns:
            Dictionary of decision triggers.
        """
        return self.decision_triggers
    
    def get_preferences(self) -> Dict[str, Dict[str, List[str]]]:
        """Get preferences.
        
        Returns:
            Dictionary of preferences.
        """
        return self.preferences
    
    def get_top_decision_topics(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top decision topics.
        
        Args:
            top_n: Number of top topics to return.
            
        Returns:
            List of (topic, count) tuples.
        """
        if 'topics' not in self.decision_patterns:
            return []
            
        return Counter(self.decision_patterns['topics']).most_common(top_n)
    
    def get_top_preferences(self, preference_type: str = 'likes', top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top preferences.
        
        Args:
            preference_type: Type of preferences ('likes' or 'dislikes').
            top_n: Number of top preferences to return.
            
        Returns:
            List of (preference, count) tuples.
        """
        if preference_type not in self.preferences:
            return []
            
        return [(k, len(v)) for k, v in sorted(
            self.preferences[preference_type].items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:top_n]]
    
    def predict_decision(self, options: List[str], context: str = '') -> Dict[str, Any]:
        """Predict a decision based on the user's decision style and preferences.
        
        Args:
            options: List of decision options.
            context: Decision context.
            
        Returns:
            Dictionary with predicted decision and confidence.
        """
        if not self.is_loaded or not options:
            return {'decision': None, 'confidence': 0.0, 'reasoning': ''}
            
        # Initialize option scores
        option_scores = {option: 0.0 for option in options}
        
        # Score based on preferences
        for option in options:
            option_lower = option.lower()
            
            # Check likes
            for like_group, like_items in self.preferences.get('likes', {}).items():
                like_group_lower = like_group.lower()
                if any(word in option_lower for word in like_group_lower.split()):
                    option_scores[option] += 1.0 * len(like_items)
                    
            # Check dislikes
            for dislike_group, dislike_items in self.preferences.get('dislikes', {}).items():
                dislike_group_lower = dislike_group.lower()
                if any(word in option_lower for word in dislike_group_lower.split()):
                    option_scores[option] -= 1.0 * len(dislike_items)
                    
        # Adjust scores based on decision style
        for option in options:
            option_lower = option.lower()
            
            # Risk-taking vs. risk-averse
            risk_words = ['risk', 'chance', 'new', 'different', 'change', 'unknown']
            safety_words = ['safe', 'secure', 'familiar', 'known', 'proven', 'reliable']
            
            if any(word in option_lower for word in risk_words):
                option_scores[option] += (self.decision_style['risk_taking'] - 0.5) * 2
                
            if any(word in option_lower for word in safety_words):
                option_scores[option] += (1 - self.decision_style['risk_taking'] - 0.5) * 2
                
            # Analytical vs. intuitive
            analytical_words = ['logical', 'rational', 'systematic', 'methodical', 'organized']
            intuitive_words = ['feel', 'sense', 'intuition', 'gut', 'instinct']
            
            if any(word in option_lower for word in analytical_words):
                option_scores[option] += (self.decision_style['analytical'] - 0.5) * 2
                
            if any(word in option_lower for word in intuitive_words):
                option_scores[option] += (1 - self.decision_style['analytical'] - 0.5) * 2
                
            # Optimistic vs. pessimistic
            optimistic_words = ['good', 'great', 'excellent', 'positive', 'opportunity']
            pessimistic_words = ['bad', 'problem', 'issue', 'negative', 'difficult']
            
            if any(word in option_lower for word in optimistic_words):
                option_scores[option] += (self.decision_style['optimism'] - 0.5) * 2
                
            if any(word in option_lower for word in pessimistic_words):
                option_scores[option] += (1 - self.decision_style['optimism'] - 0.5) * 2
                
        # Get the highest scoring option
        if not option_scores:
            return {'decision': None, 'confidence': 0.0, 'reasoning': ''}
            
        best_option = max(option_scores.items(), key=lambda x: x[1])
        
        # Calculate confidence (normalize score to 0-1 range)
        scores = list(option_scores.values())
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            confidence = 0.5  # Equal scores, moderate confidence
        else:
            # Normalize the best score to 0-1 range
            confidence = (best_option[1] - min_score) / (max_score - min_score)
            
        # Generate reasoning
        reasoning = self._generate_decision_reasoning(best_option[0], option_scores, context)
        
        return {
            'decision': best_option[0],
            'confidence': min(1.0, max(0.0, confidence)),
            'reasoning': reasoning,
            'all_scores': option_scores
        }
    
    def _generate_decision_reasoning(self, decision: str, option_scores: Dict[str, float], context: str) -> str:
        """Generate reasoning for a decision.
        
        Args:
            decision: The selected decision.
            option_scores: Scores for all options.
            context: Decision context.
            
        Returns:
            Reasoning text.
        """
        reasoning = []
        
        # Add context-based reasoning
        if context:
            reasoning.append(f"Based on the context: &quot;{context}&quot;")
            
        # Add preference-based reasoning
        decision_lower = decision.lower()
        
        # Check likes
        matching_likes = []
        for like_group, like_items in self.preferences.get('likes', {}).items():
            like_group_lower = like_group.lower()
            if any(word in decision_lower for word in like_group_lower.split()):
                matching_likes.append(like_group)
                
        if matching_likes:
            if len(matching_likes) == 1:
                reasoning.append(f"This aligns with the preference for {matching_likes[0]}")
            else:
                reasoning.append(f"This aligns with preferences for {', '.join(matching_likes[:-1])} and {matching_likes[-1]}")
                
        # Check decision style
        style_reasons = []
        
        # Risk-taking vs. risk-averse
        risk_words = ['risk', 'chance', 'new', 'different', 'change', 'unknown']
        safety_words = ['safe', 'secure', 'familiar', 'known', 'proven', 'reliable']
        
        if any(word in decision_lower for word in risk_words) and self.decision_style['risk_taking'] > 0.6:
            style_reasons.append("tendency to take risks")
        elif any(word in decision_lower for word in safety_words) and self.decision_style['risk_taking'] < 0.4:
            style_reasons.append("preference for safety and security")
            
        # Analytical vs. intuitive
        analytical_words = ['logical', 'rational', 'systematic', 'methodical', 'organized']
        intuitive_words = ['feel', 'sense', 'intuition', 'gut', 'instinct']
        
        if any(word in decision_lower for word in analytical_words) and self.decision_style['analytical'] > 0.6:
            style_reasons.append("analytical approach to decisions")
        elif any(word in decision_lower for word in intuitive_words) and self.decision_style['analytical'] < 0.4:
            style_reasons.append("intuitive decision-making style")
            
        # Optimistic vs. pessimistic
        optimistic_words = ['good', 'great', 'excellent', 'positive', 'opportunity']
        pessimistic_words = ['bad', 'problem', 'issue', 'negative', 'difficult']
        
        if any(word in decision_lower for word in optimistic_words) and self.decision_style['optimism'] > 0.6:
            style_reasons.append("optimistic outlook")
        elif any(word in decision_lower for word in pessimistic_words) and self.decision_style['optimism'] < 0.4:
            style_reasons.append("cautious perspective")
            
        if style_reasons:
            if len(style_reasons) == 1:
                reasoning.append(f"This choice reflects a {style_reasons[0]}")
            else:
                reasoning.append(f"This choice reflects {', '.join(style_reasons[:-1])} and {style_reasons[-1]}")
                
        # Add comparison to other options
        other_options = [option for option in option_scores if option != decision]
        if other_options:
            # Sort other options by score (descending)
            sorted_options = sorted(other_options, key=lambda x: option_scores[x], reverse=True)
            
            # Compare with the highest scoring alternative
            best_alternative = sorted_options[0]
            score_diff = option_scores[decision] - option_scores[best_alternative]
            
            if score_diff > 2:
                reasoning.append(f"This is strongly preferred over {best_alternative}")
            elif score_diff > 0.5:
                reasoning.append(f"This is moderately preferred over {best_alternative}")
            else:
                reasoning.append(f"This is slightly preferred over {best_alternative}")
                
        return " ".join(reasoning)
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get a summary of the decision model.
        
        Returns:
            Dictionary containing decision summary.
        """
        return {
            'decision_style': self.decision_style,
            'top_decision_topics': self.get_top_decision_topics(3),
            'recent_decisions': self.get_decision_history(5),
            'top_likes': self.get_top_preferences('likes', 3),
            'top_dislikes': self.get_top_preferences('dislikes', 3)
        }
    
    def generate_decision_description(self) -> str:
        """Generate a human-readable description of the decision style.
        
        Returns:
            Text description of the decision style.
        """
        if not self.is_loaded:
            return "Decision model not loaded."
            
        description = []
        
        # Decision style
        description.append("# Decision-Making Profile\n")
        
        description.append("## Decision Style\n")
        
        # Analytical vs. intuitive
        analytical_score = self.decision_style['analytical']
        if analytical_score > 0.66:
            description.append("- **Highly analytical** in decision-making, preferring logical analysis and systematic evaluation of options")
        elif analytical_score > 0.33:
            description.append("- Balances **analytical thinking** with intuition when making decisions")
        else:
            description.append("- Primarily **intuitive** decision-maker, often going with gut feelings and instincts")
            
        # Risk-taking vs. risk-averse
        risk_score = self.decision_style['risk_taking']
        if risk_score > 0.66:
            description.append("- **Risk-taking** approach, comfortable with uncertainty and willing to take chances")
        elif risk_score > 0.33:
            description.append("- **Moderate risk tolerance**, weighing potential benefits against risks")
        else:
            description.append("- **Risk-averse** tendency, preferring safer options with more predictable outcomes")
            
        # Quick vs. deliberate
        speed_score = self.decision_style['speed']
        if speed_score > 0.66:
            description.append("- Makes decisions **quickly**, without excessive deliberation")
        elif speed_score > 0.33:
            description.append("- **Moderate decision speed**, taking sufficient time without unnecessary delay")
        else:
            description.append("- **Deliberate** decision-maker, carefully considering options before committing")
            
        # Independent vs. collaborative
        independence_score = self.decision_style['independence']
        if independence_score > 0.66:
            description.append("- **Independent** decision-maker, comfortable deciding without input from others")
        elif independence_score > 0.33:
            description.append("- Balances **independent thinking** with seeking input from others")
        else:
            description.append("- **Collaborative** decision-maker, valuing others' perspectives and input")
            
        # Optimistic vs. pessimistic
        optimism_score = self.decision_style['optimism']
        if optimism_score > 0.66:
            description.append("- **Optimistic** outlook when evaluating options and outcomes")
        elif optimism_score > 0.33:
            description.append("- **Balanced perspective** between optimism and caution")
        else:
            description.append("- **Cautious** approach, often considering potential negative outcomes")
            
        # Decision topics
        description.append("\n## Decision Patterns\n")
        
        top_topics = self.get_top_decision_topics(3)
        if top_topics:
            description.append("Most common decision topics:")
            for topic, count in top_topics:
                description.append(f"- **{topic.capitalize()}**: {count} decisions")
                
        # Preferences
        description.append("\n## Preferences\n")
        
        top_likes = self.get_top_preferences('likes', 3)
        if top_likes:
            description.append("Strong preferences for:")
            for preference, count in top_likes:
                description.append(f"- {preference}")
                
        top_dislikes = self.get_top_preferences('dislikes', 3)
        if top_dislikes:
            description.append("\nTends to avoid:")
            for preference, count in top_dislikes:
                description.append(f"- {preference}")
                
        # Recent decisions
        description.append("\n## Recent Decisions\n")
        
        recent_decisions = self.get_decision_history(3)
        if recent_decisions:
            for decision in recent_decisions:
                date_str = decision['date'].strftime('%Y-%m-%d') if decision['date'] else 'Unknown date'
                description.append(f"- {decision['text']} ({date_str})")
                
        return "\n".join(description)