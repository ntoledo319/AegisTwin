"""Personality modeling for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from collections import Counter
import re
from datetime import datetime
import json

from ...core.config import config_manager
from ...core.utils import normalize_text, save_pickle, load_pickle, ensure_dir, extract_keywords, detect_emotion

class PersonalityModel:
    """Models personality traits and communication style."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the personality model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Big Five personality traits (OCEAN)
        # Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
        self.big_five = {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        }
        
        # Communication style traits
        self.communication_style = {
            'formality': 0.5,  # Formal vs. casual
            'verbosity': 0.5,  # Verbose vs. concise
            'expressiveness': 0.5,  # Expressive vs. reserved
            'directness': 0.5,  # Direct vs. indirect
            'politeness': 0.5,  # Polite vs. blunt
            'emotionality': 0.5,  # Emotional vs. logical
            'humor': 0.5,  # Humorous vs. serious
            'responsiveness': 0.5,  # Quick to respond vs. slow
            'initiative': 0.5,  # Initiates conversations vs. responds
            'detail_orientation': 0.5  # Detail-oriented vs. big picture
        }
        
        # Vocabulary and language patterns
        self.vocabulary = Counter()
        self.phrase_patterns = Counter()
        self.emoji_usage = Counter()
        self.punctuation_patterns = {}
        self.capitalization_style = {}
        self.greeting_patterns = Counter()
        self.farewell_patterns = Counter()
        
        # Emotional expression patterns
        self.emotion_patterns = {
            'joy': 0.0,
            'sadness': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'surprise': 0.0,
            'disgust': 0.0
        }
        
        # Temporal patterns
        self.time_of_day_activity = {
            'morning': 0,
            'afternoon': 0,
            'evening': 0,
            'night': 0
        }
        
        # Response patterns
        self.response_length_distribution = []
        self.response_time_distribution = []
        
        # Loaded flag
        self.is_loaded = False
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the personality model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training personality model...")
        
        # Filter to outgoing messages if user_name is provided
        if user_name:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing' or m.get('sender_name') == user_name]
        else:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing']
        
        print(f"Training on {len(outgoing_messages)} outgoing messages")
        
        # Extract text content
        texts = [m.get('text', '') for m in outgoing_messages if m.get('text')]
        
        # Analyze vocabulary
        self._analyze_vocabulary(texts)
        
        # Analyze communication style
        self._analyze_communication_style(texts, outgoing_messages)
        
        # Analyze emotional patterns
        self._analyze_emotional_patterns(texts)
        
        # Analyze temporal patterns
        self._analyze_temporal_patterns(outgoing_messages)
        
        # Analyze response patterns
        self._analyze_response_patterns(messages, outgoing_messages)
        
        # Infer Big Five traits
        self._infer_big_five_traits()
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("Personality model training complete")
        
    def _analyze_vocabulary(self, texts: List[str]) -> None:
        """Analyze vocabulary from texts.
        
        Args:
            texts: List of text messages.
        """
        # Combine all texts
        all_text = ' '.join(texts)
        
        # Tokenize
        words = re.findall(r'\b[a-zA-Z]+\b', all_text.lower())
        self.vocabulary = Counter(words)
        
        # Extract common phrases (n-grams)
        for n in range(2, 5):  # 2-grams to 4-grams
            ngrams = self._extract_ngrams(all_text, n)
            self.phrase_patterns.update(ngrams)
        
        # Extract emoji usage
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        emojis = []
        for text in texts:
            emojis.extend(emoji_pattern.findall(text))
        self.emoji_usage = Counter(emojis)
        
        # Analyze punctuation patterns
        punctuation_counts = {
            'exclamation': 0,
            'question': 0,
            'ellipsis': 0,
            'period': 0,
            'comma': 0,
            'multiple_punctuation': 0  # e.g., !!, ??, ...
        }
        
        for text in texts:
            punctuation_counts['exclamation'] += text.count('!')
            punctuation_counts['question'] += text.count('?')
            punctuation_counts['ellipsis'] += text.count('...')
            punctuation_counts['period'] += text.count('.')
            punctuation_counts['comma'] += text.count(',')
            punctuation_counts['multiple_punctuation'] += len(re.findall(r'[!?]{2,}', text))
            
        total_messages = len(texts)
        if total_messages > 0:
            self.punctuation_patterns = {k: v / total_messages for k, v in punctuation_counts.items()}
        
        # Analyze capitalization style
        capitalization_counts = {
            'all_lowercase': 0,
            'all_uppercase': 0,
            'sentence_case': 0,
            'title_case': 0,
            'mixed_case': 0
        }
        
        for text in texts:
            if not text:
                continue
                
            if text.islower():
                capitalization_counts['all_lowercase'] += 1
            elif text.isupper():
                capitalization_counts['all_uppercase'] += 1
            elif text[0].isupper() and text[1:].islower():
                capitalization_counts['sentence_case'] += 1
            elif all(word[0].isupper() for word in text.split() if word):
                capitalization_counts['title_case'] += 1
            else:
                capitalization_counts['mixed_case'] += 1
                
        if total_messages > 0:
            self.capitalization_style = {k: v / total_messages for k, v in capitalization_counts.items()}
        
        # Analyze greeting and farewell patterns
        greeting_patterns = [
            r'\bhey\b', r'\bhi\b', r'\bhello\b', r'\byo\b', r'\bhey there\b', 
            r'\bgood morning\b', r'\bgood afternoon\b', r'\bgood evening\b',
            r'\bwhat\'s up\b', r'\bwassup\b', r'\bhowdy\b', r'\bgreetings\b'
        ]
        
        farewell_patterns = [
            r'\bbye\b', r'\bgoodbye\b', r'\bsee you\b', r'\btalk to you later\b',
            r'\btalk later\b', r'\blater\b', r'\bgood night\b', r'\btake care\b',
            r'\bcheers\b', r'\bpeace\b', r'\bpeace out\b'
        ]
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in greeting_patterns:
                if re.search(pattern, text_lower):
                    self.greeting_patterns[pattern] += 1
                    
            for pattern in farewell_patterns:
                if re.search(pattern, text_lower):
                    self.farewell_patterns[pattern] += 1
    
    def _extract_ngrams(self, text: str, n: int) -> List[str]:
        """Extract n-grams from text.
        
        Args:
            text: Input text.
            n: Size of n-grams.
            
        Returns:
            List of n-grams.
        """
        words = text.lower().split()
        return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    
    def _analyze_communication_style(self, texts: List[str], messages: List[Dict[str, Any]]) -> None:
        """Analyze communication style from texts and messages.
        
        Args:
            texts: List of text messages.
            messages: List of message dictionaries.
        """
        if not texts:
            return
            
        # Calculate average message length
        avg_length = sum(len(text) for text in texts) / len(texts)
        
        # Calculate verbosity (normalized to 0-1 range)
        # Assume average message length of 100 characters is 0.5
        self.communication_style['verbosity'] = min(1.0, avg_length / 200)
        
        # Calculate formality
        formality_indicators = {
            'formal': [
                r'\bI am\b', r'\bcannot\b', r'\bdo not\b', r'\bwill not\b',
                r'\bthank you\b', r'\bsincerely\b', r'\bregards\b',
                r'\bplease\b', r'\bwould you\b', r'\bcould you\b'
            ],
            'informal': [
                r'\bI\'m\b', r'\bcan\'t\b', r'\bdon\'t\b', r'\bwon\'t\b',
                r'\bthanks\b', r'\bcya\b', r'\blol\b', r'\bomg\b',
                r'\bgonna\b', r'\bwanna\b', r'\bidk\b', r'\bbtw\b'
            ]
        }
        
        formal_count = 0
        informal_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in formality_indicators['formal']:
                formal_count += len(re.findall(pattern, text_lower))
                
            for pattern in formality_indicators['informal']:
                informal_count += len(re.findall(pattern, text_lower))
                
        total_indicators = formal_count + informal_count
        if total_indicators > 0:
            self.communication_style['formality'] = formal_count / total_indicators
        
        # Calculate expressiveness
        expressiveness_indicators = {
            'expressive': [
                r'!', r'\bwow\b', r'\bamazing\b', r'\bawesome\b',
                r'\blove\b', r'\bhate\b', r'\bexcited\b', r'\bincredible\b',
                r'[A-Z]{3,}', r'!!+', r'\?\?+'  # ALL CAPS, multiple ! or ?
            ],
            'reserved': [
                r'\bperhaps\b', r'\bmaybe\b', r'\bpossibly\b',
                r'\bsomewhat\b', r'\bslightly\b', r'\boccasionally\b'
            ]
        }
        
        expressive_count = 0
        reserved_count = 0
        
        for text in texts:
            for pattern in expressiveness_indicators['expressive']:
                expressive_count += len(re.findall(pattern, text))
                
            for pattern in expressiveness_indicators['reserved']:
                reserved_count += len(re.findall(pattern, text.lower()))
                
        total_exp = expressive_count + reserved_count
        if total_exp > 0:
            self.communication_style['expressiveness'] = expressive_count / total_exp
        
        # Calculate directness
        directness_indicators = {
            'direct': [
                r'\bI think\b', r'\bI want\b', r'\bI need\b',
                r'\bwe should\b', r'\byou should\b', r'\bdo this\b'
            ],
            'indirect': [
                r'\bmaybe we could\b', r'\bperhaps\b', r'\bpossibly\b',
                r'\bit might be\b', r'\bwould it be possible\b', r'\bI was wondering\b'
            ]
        }
        
        direct_count = 0
        indirect_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in directness_indicators['direct']:
                direct_count += len(re.findall(pattern, text_lower))
                
            for pattern in directness_indicators['indirect']:
                indirect_count += len(re.findall(pattern, text_lower))
                
        total_dir = direct_count + indirect_count
        if total_dir > 0:
            self.communication_style['directness'] = direct_count / total_dir
        
        # Calculate politeness
        politeness_indicators = {
            'polite': [
                r'\bplease\b', r'\bthank you\b', r'\bthanks\b',
                r'\bappreciate\b', r'\bkind\b', r'\bwould you mind\b',
                r'\bcould you please\b', r'\bexcuse me\b', r'\bsorry\b'
            ],
            'blunt': [
                r'\bjust\b', r'\bnow\b', r'\bhurry\b', r'\bquick\b',
                r'\bimmediately\b', r'\basap\b', r'\bdo it\b'
            ]
        }
        
        polite_count = 0
        blunt_count = 0
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in politeness_indicators['polite']:
                polite_count += len(re.findall(pattern, text_lower))
                
            for pattern in politeness_indicators['blunt']:
                blunt_count += len(re.findall(pattern, text_lower))
                
        total_pol = polite_count + blunt_count
        if total_pol > 0:
            self.communication_style['politeness'] = polite_count / total_pol
        
        # Calculate humor
        humor_indicators = [
            r'\blol\b', r'\bhaha\b', r'\bhehe\b', r'\blmao\b',
            r'\brofl\b', r'\bjoke\b', r'\bfunny\b', r'\bhumor\b',
            r'😂', r'🤣', r'😆', r'😄', r'😅', r'😁'
        ]
        
        humor_count = 0
        for text in texts:
            text_lower = text.lower()
            
            for pattern in humor_indicators:
                humor_count += len(re.findall(pattern, text_lower))
                
        # Normalize humor (assume 1 humor indicator per 5 messages is average)
        avg_humor = humor_count / len(texts)
        self.communication_style['humor'] = min(1.0, avg_humor * 5)
        
        # Calculate initiative (ratio of conversation starters)
        if messages:
            # Group messages by conversation
            conversations = {}
            for message in messages:
                chat_session = message.get('chat_session', '')
                if chat_session:
                    if chat_session not in conversations:
                        conversations[chat_session] = []
                    conversations[chat_session].append(message)
            
            # Count conversation starters
            starter_count = 0
            for chat_session, chat_messages in conversations.items():
                # Sort by date
                chat_messages.sort(key=lambda m: m.get('message_date', ''))
                
                # Check if user started the conversation
                if chat_messages and chat_messages[0].get('type') == 'Outgoing':
                    starter_count += 1
                    
            if conversations:
                self.communication_style['initiative'] = starter_count / len(conversations)
    
    def _analyze_emotional_patterns(self, texts: List[str]) -> None:
        """Analyze emotional patterns from texts.
        
        Args:
            texts: List of text messages.
        """
        if not texts:
            return
            
        # Combine emotions across all texts
        all_emotions = {
            'joy': 0.0,
            'sadness': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'surprise': 0.0,
            'disgust': 0.0
        }
        
        for text in texts:
            emotions = detect_emotion(text)
            for emotion, score in emotions.items():
                all_emotions[emotion] += score
                
        # Normalize
        total = sum(all_emotions.values())
        if total > 0:
            self.emotion_patterns = {k: v / total for k, v in all_emotions.items()}
            
        # Calculate emotionality (ratio of emotional to logical content)
        emotion_words_count = 0
        logical_words_count = 0
        
        emotion_indicators = [
            r'\bfeel\b', r'\bfeeling\b', r'\bfelt\b', r'\blove\b', r'\bhate\b',
            r'\bsad\b', r'\bhappy\b', r'\bangry\b', r'\bscared\b', r'\bafraid\b',
            r'\bexcited\b', r'\bnervous\b', r'\bupset\b', r'\bworried\b',
            r'\bfear\b', r'\bjoy\b', r'\bsorrow\b', r'\bdelight\b', r'\bfury\b'
        ]
        
        logical_indicators = [
            r'\bthink\b', r'\bbelieve\b', r'\bconsider\b', r'\banalysis\b',
            r'\blogic\b', r'\breason\b', r'\bfact\b', r'\bevidence\b',
            r'\bargument\b', r'\bproof\b', r'\bdata\b', r'\binformation\b',
            r'\bconclude\b', r'\bcalculate\b', r'\bestimate\b', r'\bevaluate\b'
        ]
        
        for text in texts:
            text_lower = text.lower()
            
            for pattern in emotion_indicators:
                emotion_words_count += len(re.findall(pattern, text_lower))
                
            for pattern in logical_indicators:
                logical_words_count += len(re.findall(pattern, text_lower))
                
        total_words = emotion_words_count + logical_words_count
        if total_words > 0:
            self.communication_style['emotionality'] = emotion_words_count / total_words
    
    def _analyze_temporal_patterns(self, messages: List[Dict[str, Any]]) -> None:
        """Analyze temporal patterns from messages.
        
        Args:
            messages: List of message dictionaries.
        """
        if not messages:
            return
            
        # Count messages by time of day
        for message in messages:
            message_date_str = message.get('message_date', '')
            if not message_date_str:
                continue
                
            try:
                message_date = datetime.strptime(message_date_str, '%Y-%m-%d %H:%M:%S')
                hour = message_date.hour
                
                if 5 <= hour < 12:
                    self.time_of_day_activity['morning'] += 1
                elif 12 <= hour < 17:
                    self.time_of_day_activity['afternoon'] += 1
                elif 17 <= hour < 22:
                    self.time_of_day_activity['evening'] += 1
                else:
                    self.time_of_day_activity['night'] += 1
            except ValueError:
                continue
    
    def _analyze_response_patterns(self, all_messages: List[Dict[str, Any]], 
                                 outgoing_messages: List[Dict[str, Any]]) -> None:
        """Analyze response patterns from messages.
        
        Args:
            all_messages: List of all message dictionaries.
            outgoing_messages: List of outgoing message dictionaries.
        """
        if not outgoing_messages:
            return
            
        # Calculate response length distribution
        self.response_length_distribution = [len(m.get('text', '')) for m in outgoing_messages if m.get('text')]
        
        # Calculate response time distribution
        if len(all_messages) > 1:
            # Sort messages by date
            sorted_messages = sorted(all_messages, key=lambda m: m.get('message_date', ''))
            
            response_times = []
            last_incoming = None
            
            for message in sorted_messages:
                message_date_str = message.get('message_date', '')
                if not message_date_str:
                    continue
                    
                try:
                    message_date = datetime.strptime(message_date_str, '%Y-%m-%d %H:%M:%S')
                    
                    if message.get('type') == 'Incoming' and last_incoming is None:
                        last_incoming = message_date
                    elif message.get('type') == 'Outgoing' and last_incoming is not None:
                        # Calculate response time in seconds
                        response_time = (message_date - last_incoming).total_seconds()
                        
                        # Only count if response time is reasonable (less than a day)
                        if 0 < response_time < 86400:  # 24 hours
                            response_times.append(response_time)
                            last_incoming = None
                except ValueError:
                    continue
                    
            self.response_time_distribution = response_times
            
            # Calculate responsiveness (normalized to 0-1 range)
            if response_times:
                # Calculate median response time
                median_response_time = np.median(response_times)
                
                # Normalize: 0 = immediate response, 1 = very slow response
                # Assume median response time of 1 hour (3600 seconds) is 0.5
                normalized_response_time = 1.0 - min(1.0, 3600 / (median_response_time + 1))
                
                self.communication_style['responsiveness'] = 1.0 - normalized_response_time
    
    def _infer_big_five_traits(self) -> None:
        """Infer Big Five personality traits from communication style."""
        # Openness: related to vocabulary diversity, expressiveness
        vocab_size = len(self.vocabulary)
        vocab_diversity = min(1.0, vocab_size / 5000)  # Normalize
        self.big_five['openness'] = (vocab_diversity + self.communication_style['expressiveness']) / 2
        
        # Conscientiousness: related to formality, detail orientation, responsiveness
        self.big_five['conscientiousness'] = (
            self.communication_style['formality'] +
            self.communication_style['detail_orientation'] +
            self.communication_style['responsiveness']
        ) / 3
        
        # Extraversion: related to verbosity, expressiveness, initiative
        self.big_five['extraversion'] = (
            self.communication_style['verbosity'] +
            self.communication_style['expressiveness'] +
            self.communication_style['initiative']
        ) / 3
        
        # Agreeableness: related to politeness, emotionality
        self.big_five['agreeableness'] = (
            self.communication_style['politeness'] +
            self.emotion_patterns['joy'] +
            (1.0 - self.emotion_patterns['anger'])
        ) / 3
        
        # Neuroticism: related to negative emotions
        self.big_five['neuroticism'] = (
            self.emotion_patterns['sadness'] +
            self.emotion_patterns['fear'] +
            self.emotion_patterns['anger'] +
            self.emotion_patterns['disgust']
        ) / 4
    
    def save(self) -> None:
        """Save the personality model."""
        model_path = os.path.join(self.model_dir, 'personality_model.pkl')
        save_pickle(self.__dict__, model_path)
        print(f"Personality model saved to {model_path}")
    
    def load(self) -> bool:
        """Load the personality model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        model_path = os.path.join(self.model_dir, 'personality_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.__dict__.update(data)
                self.is_loaded = True
                print(f"Personality model loaded from {model_path}")
                return True
            except Exception as e:
                print(f"Error loading personality model: {e}")
                return False
        else:
            print(f"Personality model not found at {model_path}")
            return False
    
    def get_big_five(self) -> Dict[str, float]:
        """Get Big Five personality traits.
        
        Returns:
            Dictionary of Big Five traits.
        """
        return self.big_five
    
    def get_communication_style(self) -> Dict[str, float]:
        """Get communication style traits.
        
        Returns:
            Dictionary of communication style traits.
        """
        return self.communication_style
    
    def get_emotion_patterns(self) -> Dict[str, float]:
        """Get emotion patterns.
        
        Returns:
            Dictionary of emotion patterns.
        """
        return self.emotion_patterns
    
    def get_top_vocabulary(self, top_n: int = 100) -> List[Tuple[str, int]]:
        """Get top vocabulary words.
        
        Args:
            top_n: Number of top words to return.
            
        Returns:
            List of (word, count) tuples.
        """
        return self.vocabulary.most_common(top_n)
    
    def get_top_phrases(self, top_n: int = 50) -> List[Tuple[str, int]]:
        """Get top phrases.
        
        Args:
            top_n: Number of top phrases to return.
            
        Returns:
            List of (phrase, count) tuples.
        """
        return self.phrase_patterns.most_common(top_n)
    
    def get_top_emojis(self, top_n: int = 20) -> List[Tuple[str, int]]:
        """Get top emojis.
        
        Args:
            top_n: Number of top emojis to return.
            
        Returns:
            List of (emoji, count) tuples.
        """
        return self.emoji_usage.most_common(top_n)
    
    def get_greeting_patterns(self) -> List[Tuple[str, int]]:
        """Get greeting patterns.
        
        Returns:
            List of (pattern, count) tuples.
        """
        return self.greeting_patterns.most_common()
    
    def get_farewell_patterns(self) -> List[Tuple[str, int]]:
        """Get farewell patterns.
        
        Returns:
            List of (pattern, count) tuples.
        """
        return self.farewell_patterns.most_common()
    
    def get_time_of_day_activity(self) -> Dict[str, int]:
        """Get time of day activity.
        
        Returns:
            Dictionary of time of day activity.
        """
        return self.time_of_day_activity
    
    def get_response_time_stats(self) -> Dict[str, float]:
        """Get response time statistics.
        
        Returns:
            Dictionary of response time statistics.
        """
        if not self.response_time_distribution:
            return {}
            
        return {
            'min': min(self.response_time_distribution),
            'max': max(self.response_time_distribution),
            'mean': np.mean(self.response_time_distribution),
            'median': np.median(self.response_time_distribution),
            'std': np.std(self.response_time_distribution)
        }
    
    def get_response_length_stats(self) -> Dict[str, float]:
        """Get response length statistics.
        
        Returns:
            Dictionary of response length statistics.
        """
        if not self.response_length_distribution:
            return {}
            
        return {
            'min': min(self.response_length_distribution),
            'max': max(self.response_length_distribution),
            'mean': np.mean(self.response_length_distribution),
            'median': np.median(self.response_length_distribution),
            'std': np.std(self.response_length_distribution)
        }
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of the personality model.
        
        Returns:
            Dictionary containing personality summary.
        """
        return {
            'big_five': self.big_five,
            'communication_style': self.communication_style,
            'emotion_patterns': self.emotion_patterns,
            'top_vocabulary': self.get_top_vocabulary(20),
            'top_phrases': self.get_top_phrases(10),
            'top_emojis': self.get_top_emojis(10),
            'time_of_day_activity': self.time_of_day_activity,
            'response_time_stats': self.get_response_time_stats(),
            'response_length_stats': self.get_response_length_stats()
        }
    
    def generate_personality_description(self) -> str:
        """Generate a human-readable description of the personality.
        
        Returns:
            Text description of the personality.
        """
        if not self.is_loaded:
            return "Personality model not loaded."
            
        description = []
        
        # Big Five traits
        description.append("# Personality Profile\n")
        
        description.append("## Big Five Personality Traits\n")
        for trait, score in self.big_five.items():
            level = "high" if score > 0.66 else "moderate" if score > 0.33 else "low"
            description.append(f"- **{trait.capitalize()}**: {level} ({score:.2f})")
            
        # Communication style
        description.append("\n## Communication Style\n")
        
        style_descriptions = {
            'formality': ("formal", "casual"),
            'verbosity': ("verbose", "concise"),
            'expressiveness': ("expressive", "reserved"),
            'directness': ("direct", "indirect"),
            'politeness': ("polite", "blunt"),
            'emotionality': ("emotional", "logical"),
            'humor': ("humorous", "serious"),
            'responsiveness': ("quick to respond", "slow to respond"),
            'initiative': ("conversation starter", "conversation responder"),
            'detail_orientation': ("detail-oriented", "big picture")
        }
        
        for style, score in self.communication_style.items():
            positive, negative = style_descriptions.get(style, ("high", "low"))
            if score > 0.66:
                description.append(f"- Tends to be **{positive}** ({score:.2f})")
            elif score < 0.33:
                description.append(f"- Tends to be **{negative}** ({score:.2f})")
            else:
                description.append(f"- Balanced between {positive} and {negative} ({score:.2f})")
                
        # Emotional patterns
        description.append("\n## Emotional Expression\n")
        
        # Sort emotions by score
        sorted_emotions = sorted(self.emotion_patterns.items(), key=lambda x: x[1], reverse=True)
        
        description.append("Dominant emotions in communication:")
        for emotion, score in sorted_emotions[:3]:
            if score > 0.1:  # Only include significant emotions
                description.append(f"- **{emotion.capitalize()}**: {score:.2f}")
                
        # Language patterns
        description.append("\n## Language Patterns\n")
        
        # Top phrases
        if self.phrase_patterns:
            description.append("Frequently used phrases:")
            for phrase, count in self.get_top_phrases(5):
                description.append(f"- &quot;{phrase}&quot; ({count} times)")
                
        # Emoji usage
        if self.emoji_usage:
            description.append("\nFrequently used emojis:")
            for emoji, count in self.get_top_emojis(5):
                description.append(f"- {emoji} ({count} times)")
                
        # Temporal patterns
        description.append("\n## Temporal Patterns\n")
        
        # Time of day activity
        total_messages = sum(self.time_of_day_activity.values())
        if total_messages > 0:
            description.append("Activity by time of day:")
            for time_of_day, count in sorted(self.time_of_day_activity.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_messages) * 100
                description.append(f"- **{time_of_day.capitalize()}**: {percentage:.1f}% ({count} messages)")
                
        # Response patterns
        description.append("\n## Response Patterns\n")
        
        # Response time
        response_time_stats = self.get_response_time_stats()
        if response_time_stats:
            median_seconds = response_time_stats.get('median', 0)
            if median_seconds < 60:
                description.append(f"- Typically responds within {median_seconds:.0f} seconds")
            elif median_seconds < 3600:
                description.append(f"- Typically responds within {median_seconds/60:.1f} minutes")
            else:
                description.append(f"- Typically responds within {median_seconds/3600:.1f} hours")
                
        # Response length
        response_length_stats = self.get_response_length_stats()
        if response_length_stats:
            avg_length = response_length_stats.get('mean', 0)
            description.append(f"- Average message length: {avg_length:.0f} characters")
            
        return "\n".join(description)