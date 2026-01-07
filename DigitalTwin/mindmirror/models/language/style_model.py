"""Language style modeling for MindMirror."""

import os
from typing import Dict, Any, List, Optional, Tuple
import re
from collections import Counter, defaultdict
import random
import json
import numpy as np
from datetime import datetime

from ...core.config import config_manager
from ...core.utils import normalize_text, save_pickle, load_pickle, ensure_dir

class StyleModel:
    """Models language style for text generation."""
    
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize the style model.
        
        Args:
            model_dir: Directory to store model data.
        """
        self.model_dir = model_dir or config_manager.get_value('mindmirror', 'data.model_dir', 'data/models')
        ensure_dir(self.model_dir)
        
        # Vocabulary
        self.vocabulary = Counter()
        self.max_vocabulary_size = config_manager.get_value('mindmirror', 'language_model.vocabulary_size', 50000)
        
        # N-gram models
        self.unigrams = Counter()
        self.bigrams = defaultdict(Counter)
        self.trigrams = defaultdict(Counter)
        
        # Sentence patterns
        self.sentence_starters = Counter()
        self.sentence_endings = Counter()
        self.sentence_lengths = []
        
        # Message patterns
        self.message_starters = Counter()
        self.message_endings = Counter()
        self.message_lengths = []
        
        # Punctuation patterns
        self.punctuation_patterns = {
            'exclamation': 0,
            'question': 0,
            'ellipsis': 0,
            'period': 0,
            'comma': 0,
            'multiple_punctuation': 0  # e.g., !!, ??, ...
        }
        self.punctuation_counts = 0
        
        # Capitalization patterns
        self.capitalization_patterns = {
            'all_lowercase': 0,
            'all_uppercase': 0,
            'sentence_case': 0,
            'title_case': 0,
            'mixed_case': 0
        }
        self.capitalization_counts = 0
        
        # Emoji usage
        self.emoji_usage = Counter()
        
        # Abbreviation usage
        self.abbreviation_usage = Counter()
        
        # Common phrases
        self.common_phrases = Counter()
        
        # Filler words
        self.filler_words = Counter()
        
        # Loaded flag
        self.is_loaded = False
        
    def train(self, messages: List[Dict[str, Any]], user_name: Optional[str] = None) -> None:
        """Train the style model on messages.
        
        Args:
            messages: List of messages to train on.
            user_name: Name of the user (to identify outgoing messages).
        """
        print("Training style model...")
        
        # Filter to outgoing messages if user_name is provided
        if user_name:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing' or m.get('sender_name') == user_name]
        else:
            outgoing_messages = [m for m in messages if m.get('type') == 'Outgoing']
        
        print(f"Training on {len(outgoing_messages)} outgoing messages")
        
        # Extract text content
        texts = [m.get('text', '') for m in outgoing_messages if m.get('text')]
        
        # Build vocabulary
        self._build_vocabulary(texts)
        
        # Build n-gram models
        self._build_ngram_models(texts)
        
        # Analyze sentence patterns
        self._analyze_sentence_patterns(texts)
        
        # Analyze message patterns
        self._analyze_message_patterns(texts)
        
        # Analyze punctuation patterns
        self._analyze_punctuation_patterns(texts)
        
        # Analyze capitalization patterns
        self._analyze_capitalization_patterns(texts)
        
        # Analyze emoji usage
        self._analyze_emoji_usage(texts)
        
        # Analyze abbreviation usage
        self._analyze_abbreviation_usage(texts)
        
        # Extract common phrases
        self._extract_common_phrases(texts)
        
        # Extract filler words
        self._extract_filler_words(texts)
        
        # Save the model
        self.save()
        
        self.is_loaded = True
        print("Style model training complete")
        
    def _build_vocabulary(self, texts: List[str]) -> None:
        """Build vocabulary from texts.
        
        Args:
            texts: List of text messages.
        """
        # Tokenize texts
        all_words = []
        for text in texts:
            # Split into words
            words = re.findall(r'\b[a-zA-Z0-9\']+\b', text.lower())
            all_words.extend(words)
            
        # Count word frequencies
        self.vocabulary = Counter(all_words)
        
        # Limit vocabulary size
        if len(self.vocabulary) > self.max_vocabulary_size:
            self.vocabulary = Counter(dict(self.vocabulary.most_common(self.max_vocabulary_size)))
            
    def _build_ngram_models(self, texts: List[str]) -> None:
        """Build n-gram models from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset n-gram models
        self.unigrams = Counter()
        self.bigrams = defaultdict(Counter)
        self.trigrams = defaultdict(Counter)
        
        # Process each text
        for text in texts:
            # Tokenize
            words = re.findall(r'\b[a-zA-Z0-9\']+\b', text.lower())
            
            # Skip short texts
            if len(words) < 3:
                continue
                
            # Count unigrams
            self.unigrams.update(words)
            
            # Count bigrams
            for i in range(len(words) - 1):
                self.bigrams[words[i]][words[i+1]] += 1
                
            # Count trigrams
            for i in range(len(words) - 2):
                self.trigrams[(words[i], words[i+1])][words[i+2]] += 1
                
    def _analyze_sentence_patterns(self, texts: List[str]) -> None:
        """Analyze sentence patterns from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset sentence patterns
        self.sentence_starters = Counter()
        self.sentence_endings = Counter()
        self.sentence_lengths = []
        
        # Process each text
        for text in texts:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            
            # Skip empty sentences
            sentences = [s.strip() for s in sentences if s.strip()]
            
            for sentence in sentences:
                # Get sentence length
                words = re.findall(r'\b[a-zA-Z0-9\']+\b', sentence)
                self.sentence_lengths.append(len(words))
                
                # Get sentence starter
                if words:
                    self.sentence_starters[words[0].lower()] += 1
                    
                # Get sentence ending
                if words:
                    self.sentence_endings[words[-1].lower()] += 1
                    
    def _analyze_message_patterns(self, texts: List[str]) -> None:
        """Analyze message patterns from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset message patterns
        self.message_starters = Counter()
        self.message_endings = Counter()
        self.message_lengths = []
        
        # Process each text
        for text in texts:
            # Get message length
            words = re.findall(r'\b[a-zA-Z0-9\']+\b', text)
            self.message_lengths.append(len(words))
            
            # Get message starter
            if words:
                self.message_starters[words[0].lower()] += 1
                
            # Get message ending
            if words:
                self.message_endings[words[-1].lower()] += 1
                
    def _analyze_punctuation_patterns(self, texts: List[str]) -> None:
        """Analyze punctuation patterns from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset punctuation patterns
        self.punctuation_patterns = {
            'exclamation': 0,
            'question': 0,
            'ellipsis': 0,
            'period': 0,
            'comma': 0,
            'multiple_punctuation': 0
        }
        self.punctuation_counts = 0
        
        # Process each text
        for text in texts:
            self.punctuation_patterns['exclamation'] += text.count('!')
            self.punctuation_patterns['question'] += text.count('?')
            self.punctuation_patterns['ellipsis'] += text.count('...')
            self.punctuation_patterns['period'] += text.count('.')
            self.punctuation_patterns['comma'] += text.count(',')
            self.punctuation_patterns['multiple_punctuation'] += len(re.findall(r'[!?]{2,}', text))
            
            # Count total punctuation
            self.punctuation_counts += sum(1 for c in text if c in '.,;:!?')
            
    def _analyze_capitalization_patterns(self, texts: List[str]) -> None:
        """Analyze capitalization patterns from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset capitalization patterns
        self.capitalization_patterns = {
            'all_lowercase': 0,
            'all_uppercase': 0,
            'sentence_case': 0,
            'title_case': 0,
            'mixed_case': 0
        }
        self.capitalization_counts = 0
        
        # Process each text
        for text in texts:
            if not text:
                continue
                
            self.capitalization_counts += 1
            
            if text.islower():
                self.capitalization_patterns['all_lowercase'] += 1
            elif text.isupper():
                self.capitalization_patterns['all_uppercase'] += 1
            elif text[0].isupper() and text[1:].islower():
                self.capitalization_patterns['sentence_case'] += 1
            elif all(word[0].isupper() for word in text.split() if word):
                self.capitalization_patterns['title_case'] += 1
            else:
                self.capitalization_patterns['mixed_case'] += 1
                
    def _analyze_emoji_usage(self, texts: List[str]) -> None:
        """Analyze emoji usage from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset emoji usage
        self.emoji_usage = Counter()
        
        # Emoji pattern
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        
        # Process each text
        for text in texts:
            emojis = emoji_pattern.findall(text)
            self.emoji_usage.update(emojis)
            
    def _analyze_abbreviation_usage(self, texts: List[str]) -> None:
        """Analyze abbreviation usage from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset abbreviation usage
        self.abbreviation_usage = Counter()
        
        # Common abbreviations
        abbreviations = [
            'lol', 'rofl', 'lmao', 'brb', 'btw', 'omg', 'wtf', 'idk', 'imo', 'imho',
            'afaik', 'afk', 'asap', 'bff', 'fyi', 'gtg', 'irl', 'jk', 'lmk', 'nbd',
            'np', 'nsfw', 'nvm', 'ofc', 'omw', 'pov', 'rn', 'smh', 'tbh', 'tbt',
            'tfw', 'thx', 'til', 'tldr', 'ttyl', 'ty', 'wdym', 'yt', 'yolo'
        ]
        
        # Process each text
        for text in texts:
            text_lower = text.lower()
            for abbr in abbreviations:
                count = len(re.findall(r'\b' + re.escape(abbr) + r'\b', text_lower))
                if count > 0:
                    self.abbreviation_usage[abbr] += count
                    
    def _extract_common_phrases(self, texts: List[str]) -> None:
        """Extract common phrases from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset common phrases
        self.common_phrases = Counter()
        
        # Process each text
        for text in texts:
            # Extract 2-4 word phrases
            words = re.findall(r'\b[a-zA-Z0-9\']+\b', text.lower())
            
            # Skip short texts
            if len(words) < 2:
                continue
                
            # Extract 2-grams
            for i in range(len(words) - 1):
                phrase = ' '.join(words[i:i+2])
                self.common_phrases[phrase] += 1
                
            # Extract 3-grams
            if len(words) >= 3:
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    self.common_phrases[phrase] += 1
                    
            # Extract 4-grams
            if len(words) >= 4:
                for i in range(len(words) - 3):
                    phrase = ' '.join(words[i:i+4])
                    self.common_phrases[phrase] += 1
                    
    def _extract_filler_words(self, texts: List[str]) -> None:
        """Extract filler words from texts.
        
        Args:
            texts: List of text messages.
        """
        # Reset filler words
        self.filler_words = Counter()
        
        # Common filler words
        fillers = [
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 'so', 'actually',
            'basically', 'literally', 'honestly', 'seriously', 'totally', 'really',
            'just', 'kind of', 'sort of', 'anyway', 'anyhow', 'whatever', 'well'
        ]
        
        # Process each text
        for text in texts:
            text_lower = text.lower()
            for filler in fillers:
                count = len(re.findall(r'\b' + re.escape(filler) + r'\b', text_lower))
                if count > 0:
                    self.filler_words[filler] += count
                    
    def save(self) -> None:
        """Save the style model."""
        model_path = os.path.join(self.model_dir, 'style_model.pkl')
        save_pickle(self.__dict__, model_path)
        print(f"Style model saved to {model_path}")
        
    def load(self) -> bool:
        """Load the style model.
        
        Returns:
            True if model was loaded successfully, False otherwise.
        """
        model_path = os.path.join(self.model_dir, 'style_model.pkl')
        
        if os.path.exists(model_path):
            try:
                data = load_pickle(model_path)
                self.__dict__.update(data)
                self.is_loaded = True
                print(f"Style model loaded from {model_path}")
                return True
            except Exception as e:
                print(f"Error loading style model: {e}")
                return False
        else:
            print(f"Style model not found at {model_path}")
            return False
            
    def get_vocabulary(self, limit: int = None) -> List[Tuple[str, int]]:
        """Get vocabulary words.
        
        Args:
            limit: Maximum number of words to return.
            
        Returns:
            List of (word, count) tuples.
        """
        if limit:
            return self.vocabulary.most_common(limit)
        return self.vocabulary.most_common()
        
    def get_common_phrases(self, limit: int = None) -> List[Tuple[str, int]]:
        """Get common phrases.
        
        Args:
            limit: Maximum number of phrases to return.
            
        Returns:
            List of (phrase, count) tuples.
        """
        if limit:
            return self.common_phrases.most_common(limit)
        return self.common_phrases.most_common()
        
    def get_emoji_usage(self, limit: int = None) -> List[Tuple[str, int]]:
        """Get emoji usage.
        
        Args:
            limit: Maximum number of emojis to return.
            
        Returns:
            List of (emoji, count) tuples.
        """
        if limit:
            return self.emoji_usage.most_common(limit)
        return self.emoji_usage.most_common()
        
    def get_abbreviation_usage(self, limit: int = None) -> List[Tuple[str, int]]:
        """Get abbreviation usage.
        
        Args:
            limit: Maximum number of abbreviations to return.
            
        Returns:
            List of (abbreviation, count) tuples.
        """
        if limit:
            return self.abbreviation_usage.most_common(limit)
        return self.abbreviation_usage.most_common()
        
    def get_filler_words(self, limit: int = None) -> List[Tuple[str, int]]:
        """Get filler words.
        
        Args:
            limit: Maximum number of filler words to return.
            
        Returns:
            List of (filler, count) tuples.
        """
        if limit:
            return self.filler_words.most_common(limit)
        return self.filler_words.most_common()
        
    def get_punctuation_patterns(self) -> Dict[str, float]:
        """Get punctuation patterns.
        
        Returns:
            Dictionary of punctuation patterns.
        """
        if self.punctuation_counts == 0:
            return {k: 0.0 for k in self.punctuation_patterns}
            
        return {k: v / self.punctuation_counts for k, v in self.punctuation_patterns.items()}
        
    def get_capitalization_patterns(self) -> Dict[str, float]:
        """Get capitalization patterns.
        
        Returns:
            Dictionary of capitalization patterns.
        """
        if self.capitalization_counts == 0:
            return {k: 0.0 for k in self.capitalization_patterns}
            
        return {k: v / self.capitalization_counts for k, v in self.capitalization_patterns.items()}
        
    def get_message_length_stats(self) -> Dict[str, float]:
        """Get message length statistics.
        
        Returns:
            Dictionary of message length statistics.
        """
        if not self.message_lengths:
            return {}
            
        return {
            'min': min(self.message_lengths),
            'max': max(self.message_lengths),
            'mean': np.mean(self.message_lengths),
            'median': np.median(self.message_lengths),
            'std': np.std(self.message_lengths)
        }
        
    def get_sentence_length_stats(self) -> Dict[str, float]:
        """Get sentence length statistics.
        
        Returns:
            Dictionary of sentence length statistics.
        """
        if not self.sentence_lengths:
            return {}
            
        return {
            'min': min(self.sentence_lengths),
            'max': max(self.sentence_lengths),
            'mean': np.mean(self.sentence_lengths),
            'median': np.median(self.sentence_lengths),
            'std': np.std(self.sentence_lengths)
        }
        
    def get_style_summary(self) -> Dict[str, Any]:
        """Get a summary of the style model.
        
        Returns:
            Dictionary containing style summary.
        """
        return {
            'vocabulary_size': len(self.vocabulary),
            'top_words': self.get_vocabulary(20),
            'top_phrases': self.get_common_phrases(10),
            'top_emojis': self.get_emoji_usage(10),
            'top_abbreviations': self.get_abbreviation_usage(10),
            'top_filler_words': self.get_filler_words(10),
            'punctuation_patterns': self.get_punctuation_patterns(),
            'capitalization_patterns': self.get_capitalization_patterns(),
            'message_length_stats': self.get_message_length_stats(),
            'sentence_length_stats': self.get_sentence_length_stats()
        }
        
    def generate_text(self, prompt: str = '', length: int = 50, temperature: float = 0.7) -> str:
        """Generate text in the user's style.
        
        Args:
            prompt: Optional prompt to start generation.
            length: Maximum length of generated text in words.
            temperature: Controls randomness (0.0-1.0).
            
        Returns:
            Generated text.
        """
        if not self.is_loaded or not self.vocabulary:
            return "Style model not loaded or trained."
            
        # Prepare prompt
        if prompt:
            words = re.findall(r'\b[a-zA-Z0-9\']+\b', prompt.lower())
            if not words:
                words = []
        else:
            # Start with a common message starter
            if self.message_starters:
                words = [self._sample_from_counter(self.message_starters, temperature)]
            else:
                words = []
                
        # Generate text
        while len(words) < length:
            if len(words) >= 2:
                # Try trigram first
                bigram = (words[-2], words[-1])
                if bigram in self.trigrams and self.trigrams[bigram]:
                    next_word = self._sample_from_counter(self.trigrams[bigram], temperature)
                    words.append(next_word)
                    continue
                    
            if len(words) >= 1:
                # Try bigram
                if words[-1] in self.bigrams and self.bigrams[words[-1]]:
                    next_word = self._sample_from_counter(self.bigrams[words[-1]], temperature)
                    words.append(next_word)
                    continue
                    
            # Fall back to unigram
            if self.unigrams:
                next_word = self._sample_from_counter(self.unigrams, temperature)
                words.append(next_word)
            else:
                break
                
        # Apply capitalization
        text = ' '.join(words)
        text = self._apply_capitalization(text)
        
        # Apply punctuation
        text = self._apply_punctuation(text)
        
        # Add emojis
        text = self._add_emojis(text)
        
        return text
        
    def _sample_from_counter(self, counter: Counter, temperature: float) -> str:
        """Sample an item from a counter based on frequency and temperature.
        
        Args:
            counter: Counter object.
            temperature: Controls randomness (0.0-1.0).
            
        Returns:
            Sampled item.
        """
        items, weights = zip(*counter.items())
        
        # Apply temperature
        if temperature == 0:
            # Deterministic (always pick the most common)
            return items[weights.index(max(weights))]
            
        # Convert to probabilities
        weights = np.array(weights, dtype=np.float64)
        weights = weights ** (1.0 / max(0.0001, temperature))
        weights = weights / weights.sum()
        
        # Sample
        return np.random.choice(items, p=weights)
        
    def _apply_capitalization(self, text: str) -> str:
        """Apply capitalization pattern to text.
        
        Args:
            text: Input text.
            
        Returns:
            Text with applied capitalization.
        """
        if not text:
            return text
            
        # Get capitalization pattern probabilities
        cap_probs = self.get_capitalization_patterns()
        
        # If no patterns, use sentence case
        if not cap_probs or all(v == 0 for v in cap_probs.values()):
            return text[0].upper() + text[1:]
            
        # Sample capitalization pattern
        cap_pattern = max(cap_probs.items(), key=lambda x: x[1])[0]
        
        if cap_pattern == 'all_lowercase':
            return text.lower()
        elif cap_pattern == 'all_uppercase':
            return text.upper()
        elif cap_pattern == 'sentence_case':
            return text[0].upper() + text[1:]
        elif cap_pattern == 'title_case':
            return ' '.join(word[0].upper() + word[1:] for word in text.split())
        else:  # mixed_case
            return text
            
    def _apply_punctuation(self, text: str) -> str:
        """Apply punctuation pattern to text.
        
        Args:
            text: Input text.
            
        Returns:
            Text with applied punctuation.
        """
        if not text:
            return text
            
        # Get punctuation pattern probabilities
        punct_probs = self.get_punctuation_patterns()
        
        # If no patterns, use period
        if not punct_probs or all(v == 0 for v in punct_probs.values()):
            return text + '.'
            
        # Sample punctuation type
        punct_types = ['period', 'exclamation', 'question', 'ellipsis']
        punct_weights = [punct_probs.get(t, 0) for t in punct_types]
        
        # Ensure non-zero weights
        if sum(punct_weights) == 0:
            punct_weights = [1, 0, 0, 0]  # Default to period
            
        punct_type = random.choices(punct_types, weights=punct_weights)[0]
        
        # Apply punctuation
        if punct_type == 'period':
            text += '.'
        elif punct_type == 'exclamation':
            text += '!'
        elif punct_type == 'question':
            text += '?'
        elif punct_type == 'ellipsis':
            text += '...'
            
        # Check for multiple punctuation
        if punct_probs.get('multiple_punctuation', 0) > 0.2:
            if punct_type == 'exclamation':
                text += '!'
            elif punct_type == 'question':
                text += '?'
                
        return text
        
    def _add_emojis(self, text: str) -> str:
        """Add emojis to text based on learned patterns.
        
        Args:
            text: Input text.
            
        Returns:
            Text with added emojis.
        """
        if not text or not self.emoji_usage:
            return text
            
        # Calculate emoji frequency
        total_messages = len(self.message_lengths) or 1
        total_emojis = sum(self.emoji_usage.values())
        emoji_freq = total_emojis / total_messages
        
        # Decide whether to add emoji
        if random.random() > emoji_freq:
            return text
            
        # Sample emoji
        emoji = self._sample_from_counter(self.emoji_usage, 0.5)
        
        # Add emoji
        return text + ' ' + emoji
        
    def generate_style_description(self) -> str:
        """Generate a human-readable description of the language style.
        
        Returns:
            Text description of the language style.
        """
        if not self.is_loaded:
            return "Style model not loaded."
            
        description = []
        
        # Language style overview
        description.append("# Language Style Profile\n")
        
        description.append("## Vocabulary and Phrasing\n")
        
        # Vocabulary size
        description.append(f"- Vocabulary size: {len(self.vocabulary)} unique words")
        
        # Common phrases
        top_phrases = self.get_common_phrases(5)
        if top_phrases:
            description.append("\nFrequently used phrases:")
            for phrase, count in top_phrases:
                description.append(f"- &quot;{phrase}&quot; ({count} times)")
                
        # Abbreviations
        top_abbrs = self.get_abbreviation_usage(5)
        if top_abbrs:
            description.append("\nCommonly used abbreviations:")
            for abbr, count in top_abbrs:
                description.append(f"- &quot;{abbr}&quot; ({count} times)")
                
        # Filler words
        top_fillers = self.get_filler_words(5)
        if top_fillers:
            description.append("\nFiller words:")
            for filler, count in top_fillers:
                description.append(f"- &quot;{filler}&quot; ({count} times)")
                
        # Message structure
        description.append("\n## Message Structure\n")
        
        # Message length
        msg_stats = self.get_message_length_stats()
        if msg_stats:
            avg_length = msg_stats.get('mean', 0)
            description.append(f"- Average message length: {avg_length:.1f} words")
            
        # Sentence length
        sent_stats = self.get_sentence_length_stats()
        if sent_stats:
            avg_length = sent_stats.get('mean', 0)
            description.append(f"- Average sentence length: {avg_length:.1f} words")
            
        # Capitalization
        cap_patterns = self.get_capitalization_patterns()
        if cap_patterns:
            # Find dominant pattern
            dominant_cap = max(cap_patterns.items(), key=lambda x: x[1])
            if dominant_cap[1] > 0.5:
                if dominant_cap[0] == 'all_lowercase':
                    description.append("- Tends to use all lowercase")
                elif dominant_cap[0] == 'all_uppercase':
                    description.append("- Tends to use ALL UPPERCASE")
                elif dominant_cap[0] == 'sentence_case':
                    description.append("- Uses proper sentence case")
                elif dominant_cap[0] == 'title_case':
                    description.append("- Tends to Capitalize Many Words")
                else:
                    description.append("- Uses mixed capitalization")
                    
        # Punctuation
        punct_patterns = self.get_punctuation_patterns()
        if punct_patterns:
            # Check for distinctive patterns
            if punct_patterns.get('exclamation', 0) > 0.3:
                description.append("- Uses exclamation marks frequently!")
            if punct_patterns.get('question', 0) > 0.3:
                description.append("- Asks questions frequently?")
            if punct_patterns.get('ellipsis', 0) > 0.2:
                description.append("- Uses ellipses frequently...")
            if punct_patterns.get('multiple_punctuation', 0) > 0.2:
                description.append("- Often uses multiple punctuation marks!!")
                
        # Emoji usage
        top_emojis = self.get_emoji_usage(5)
        if top_emojis:
            description.append("\n## Emoji Usage\n")
            description.append("Favorite emojis:")
            for emoji, count in top_emojis:
                description.append(f"- {emoji} ({count} times)")
                
        return "\n".join(description)