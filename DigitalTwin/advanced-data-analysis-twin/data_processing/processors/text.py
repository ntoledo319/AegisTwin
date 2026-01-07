"""
Text processor for analyzing and processing textual content.
"""

import re
import string
from typing import Dict, Any, List, Optional, Tuple, Set
import asyncio
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter

from core.logging import get_logger
from core.utils import generate_id, timestamp_now

logger = get_logger(__name__)

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    logger.info("Downloading required NLTK resources...")
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

class TextProcessor:
    """
    Processor for analyzing and processing textual content.
    
    This processor provides functionality for:
    - Text normalization and cleaning
    - Tokenization and lemmatization
    - Keyword extraction
    - Named entity recognition
    - Sentiment analysis
    - Topic extraction
    - Text summarization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the text processor.
        
        Args:
            config: Configuration dictionary with the following optional keys:
                - language: Language code (default: "en")
                - use_spacy: Whether to use spaCy for NLP (default: False)
                - min_keyword_length: Minimum length for keywords (default: 3)
                - max_keywords: Maximum number of keywords to extract (default: 20)
                - stopwords_file: Path to custom stopwords file (default: None)
        """
        self.config = config or {}
        self.processor_id = generate_id("text_processor")
        self.language = self.config.get("language", "en")
        self.use_spacy = self.config.get("use_spacy", False)
        self.min_keyword_length = self.config.get("min_keyword_length", 3)
        self.max_keywords = self.config.get("max_keywords", 20)
        
        # Initialize NLTK components
        self.stop_words = set(stopwords.words(self.language))
        self.lemmatizer = WordNetLemmatizer()
        
        # Add custom stopwords if provided
        if "stopwords_file" in self.config:
            try:
                with open(self.config["stopwords_file"], "r", encoding="utf-8") as f:
                    custom_stopwords = {line.strip().lower() for line in f if line.strip()}
                    self.stop_words.update(custom_stopwords)
            except Exception as e:
                logger.warning(f"Failed to load custom stopwords: {str(e)}")
        
        # Initialize spaCy if enabled
        self.nlp = None
        if self.use_spacy:
            try:
                import spacy
                self.nlp = spacy.load(f"{self.language}_core_web_sm")
                logger.info(f"Loaded spaCy model: {self.language}_core_web_sm")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {str(e)}")
                self.use_spacy = False
    
    async def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text and extract various features.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary with processed text features
        """
        if not text:
            return {
                "normalized": "",
                "tokens": [],
                "sentences": [],
                "keywords": [],
                "entities": [],
                "sentiment": 0.0,
                "summary": "",
                "language": self.language,
                "metadata": {
                    "processor_id": self.processor_id,
                    "timestamp": timestamp_now(),
                    "text_length": 0,
                    "processing_time": 0.0
                }
            }
        
        start_time = asyncio.get_event_loop().time()
        
        # Normalize text
        normalized = await self.normalize_text(text)
        
        # Tokenize text
        tokens = await self.tokenize_text(normalized)
        sentences = await self.tokenize_sentences(normalized)
        
        # Extract features
        keywords = await self.extract_keywords(normalized)
        entities = await self.extract_entities(text)
        sentiment = await self.analyze_sentiment(text)
        summary = await self.summarize_text(text)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "normalized": normalized,
            "tokens": tokens,
            "sentences": sentences,
            "keywords": keywords,
            "entities": entities,
            "sentiment": sentiment,
            "summary": summary,
            "language": self.language,
            "metadata": {
                "processor_id": self.processor_id,
                "timestamp": timestamp_now(),
                "text_length": len(text),
                "processing_time": processing_time
            }
        }
    
    async def process_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Process a batch of texts.
        
        Args:
            texts: List of texts to process
            
        Returns:
            List of dictionaries with processed text features
        """
        results = []
        for text in texts:
            result = await self.process_text(text)
            results.append(result)
        return results
    
    async def normalize_text(self, text: str) -> str:
        """
        Normalize text by removing special characters, extra whitespace, etc.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if self.use_spacy and self.nlp:
            # Use spaCy for tokenization
            doc = self.nlp(text)
            return [token.text for token in doc]
        else:
            # Use NLTK for tokenization
            return word_tokenize(text)
    
    async def tokenize_sentences(self, text: str) -> List[str]:
        """
        Tokenize text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if self.use_spacy and self.nlp:
            # Use spaCy for sentence tokenization
            doc = self.nlp(text)
            return [sent.text for sent in doc.sents]
        else:
            # Use NLTK for sentence tokenization
            return sent_tokenize(text)
    
    async def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of keyword dictionaries with text and score
        """
        if not text:
            return []
        
        # Tokenize and clean
        tokens = await self.tokenize_text(text)
        
        # Remove stopwords and short words
        filtered_tokens = [
            token for token in tokens
            if token not in self.stop_words and len(token) >= self.min_keyword_length
        ]
        
        # Lemmatize tokens
        lemmatized_tokens = []
        for token in filtered_tokens:
            pos_tag = nltk.pos_tag([token])[0][1][0].lower()
            pos = 'a' if pos_tag == 'j' else pos_tag if pos_tag in ['n', 'v', 'r'] else 'n'
            lemma = self.lemmatizer.lemmatize(token, pos=pos)
            lemmatized_tokens.append(lemma)
        
        # Count frequencies
        word_freq = Counter(lemmatized_tokens)
        
        # Convert to keyword list with scores
        keywords = [
            {"text": word, "score": count / len(lemmatized_tokens) if lemmatized_tokens else 0}
            for word, count in word_freq.most_common(self.max_keywords)
        ]
        
        return keywords
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries with text, type, and confidence
        """
        if not text:
            return []
        
        entities = []
        
        if self.use_spacy and self.nlp:
            # Use spaCy for entity extraction
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    "confidence": 0.9  # spaCy doesn't provide confidence scores
                })
        else:
            # Use NLTK for basic NER
            tokens = word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            chunks = nltk.ne_chunk(pos_tags)
            
            current_entity = []
            current_type = None
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    # This is a named entity
                    if current_entity and current_type != chunk.label():
                        # Save previous entity
                        entity_text = ' '.join([word for word, tag in current_entity])
                        entities.append({
                            "text": entity_text,
                            "type": current_type,
                            "start_char": -1,  # NLTK doesn't provide character positions
                            "end_char": -1,
                            "confidence": 0.7
                        })
                        current_entity = []
                    
                    current_type = chunk.label()
                    current_entity.extend(chunk.leaves())
                elif current_entity:
                    # Save previous entity
                    entity_text = ' '.join([word for word, tag in current_entity])
                    entities.append({
                        "text": entity_text,
                        "type": current_type,
                        "start_char": -1,
                        "end_char": -1,
                        "confidence": 0.7
                    })
                    current_entity = []
                    current_type = None
            
            # Save last entity if any
            if current_entity:
                entity_text = ' '.join([word for word, tag in current_entity])
                entities.append({
                    "text": entity_text,
                    "type": current_type,
                    "start_char": -1,
                    "end_char": -1,
                    "confidence": 0.7
                })
        
        return entities
    
    async def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text
            
        Returns:
            Sentiment score (-1.0 to 1.0, where -1 is negative, 0 is neutral, 1 is positive)
        """
        if not text:
            return 0.0
        
        try:
            # Simple lexicon-based sentiment analysis
            # For production use, consider using a more sophisticated approach
            
            # Load positive and negative word lists
            positive_words = {
                "good", "great", "excellent", "wonderful", "amazing", "fantastic",
                "terrific", "outstanding", "superb", "brilliant", "awesome",
                "happy", "joy", "love", "like", "best", "better", "positive",
                "beautiful", "perfect", "pleasant", "nice", "enjoy", "enjoyed",
                "impressive", "impressed", "recommend", "recommended", "satisfied",
                "satisfaction", "pleased", "pleasure", "delighted", "delight"
            }
            
            negative_words = {
                "bad", "terrible", "awful", "horrible", "poor", "worst",
                "negative", "disappointing", "disappointed", "disappointment",
                "hate", "dislike", "sad", "unhappy", "unfortunate", "regret",
                "regrettable", "mediocre", "inferior", "useless", "worthless",
                "waste", "problem", "issue", "trouble", "difficult", "hard",
                "complicated", "confusing", "confused", "frustrating", "frustrated",
                "frustration", "annoying", "annoyed", "angry", "upset"
            }
            
            # Normalize and tokenize
            normalized = await self.normalize_text(text)
            tokens = normalized.split()
            
            # Count positive and negative words
            positive_count = sum(1 for token in tokens if token in positive_words)
            negative_count = sum(1 for token in tokens if token in negative_words)
            
            # Calculate sentiment score
            total_count = positive_count + negative_count
            if total_count == 0:
                return 0.0
            
            return (positive_count - negative_count) / total_count
            
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment: {str(e)}")
            return 0.0
    
    async def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a summary of the text.
        
        Args:
            text: Input text
            max_sentences: Maximum number of sentences in the summary
            
        Returns:
            Summarized text
        """
        if not text:
            return ""
        
        try:
            # Simple extractive summarization
            # For production use, consider using a more sophisticated approach
            
            # Tokenize into sentences
            sentences = await self.tokenize_sentences(text)
            
            if len(sentences) <= max_sentences:
                return text
            
            # Score sentences based on word frequency
            word_freq = Counter()
            for sentence in sentences:
                normalized = await self.normalize_text(sentence)
                tokens = normalized.split()
                filtered_tokens = [token for token in tokens if token not in self.stop_words]
                word_freq.update(filtered_tokens)
            
            # Calculate sentence scores
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                normalized = await self.normalize_text(sentence)
                tokens = normalized.split()
                filtered_tokens = [token for token in tokens if token not in self.stop_words]
                
                if filtered_tokens:
                    score = sum(word_freq[token] for token in filtered_tokens) / len(filtered_tokens)
                    sentence_scores[i] = score
            
            # Get top sentences
            top_indices = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
            top_indices = sorted([idx for idx, score in top_indices])
            
            # Combine sentences in original order
            summary = " ".join(sentences[idx] for idx in top_indices)
            
            return summary
            
        except Exception as e:
            logger.warning(f"Failed to summarize text: {str(e)}")
            return text[:200] + "..." if len(text) > 200 else text