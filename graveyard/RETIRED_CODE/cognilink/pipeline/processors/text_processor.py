"""
Text Processor for CogniLink

This module provides functionality to process and analyze text content
from communications, extracting entities, sentiment, and other features.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import string
from collections import Counter
import json
import os

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Processor for analyzing and enriching text content.
    
    This class handles text analysis tasks such as entity extraction,
    sentiment analysis, topic detection, and content classification.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the text processor.
        
        Args:
            config: Configuration dictionary for the processor
        """
        self.config = config or {}
        
        # Load stopwords
        self.stopwords = self._load_stopwords()
        
        # Initialize NLP components if available
        self.nlp = None
        self.sentiment_analyzer = None
        self.entity_extractor = None
        
        # Try to load spaCy if available
        try:
            import spacy
            self.nlp = spacy.load(self.config.get('spacy_model', 'en_core_web_sm'))
            logger.info("Loaded spaCy NLP model")
        except (ImportError, OSError):
            logger.warning("spaCy not available or model not found. Some features will be limited.")
        
        # Try to load NLTK if available
        try:
            import nltk
            from nltk.sentiment import SentimentIntensityAnalyzer
            nltk.download('vader_lexicon', quiet=True)
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            logger.info("Loaded NLTK sentiment analyzer")
        except ImportError:
            logger.warning("NLTK not available. Sentiment analysis will be limited.")
    
    def _load_stopwords(self) -> Set[str]:
        """
        Load stopwords for text processing.
        
        Returns:
            Set of stopwords
        """
        # Default English stopwords
        default_stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 
            'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
            'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 
            'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 
            'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
        }
        
        # Try to load NLTK stopwords if available
        try:
            import nltk
            nltk.download('stopwords', quiet=True)
            from nltk.corpus import stopwords
            nltk_stopwords = set(stopwords.words('english'))
            return default_stopwords.union(nltk_stopwords)
        except ImportError:
            logger.warning("NLTK not available. Using default stopwords.")
            return default_stopwords
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text to extract features and metadata.
        
        Args:
            text: Text content to process
            
        Returns:
            Dictionary containing extracted features and metadata
        """
        if not text or not isinstance(text, str):
            return {
                'word_count': 0,
                'entities': [],
                'keywords': [],
                'sentiment': {'compound': 0, 'positive': 0, 'negative': 0, 'neutral': 0},
                'language': 'unknown'
            }
        
        # Basic text statistics
        word_count = len(text.split())
        
        # Extract entities
        entities = self.extract_entities(text)
        
        # Extract keywords
        keywords = self.extract_keywords(text)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(text)
        
        # Detect language
        language = self.detect_language(text)
        
        return {
            'word_count': word_count,
            'entities': entities,
            'keywords': keywords,
            'sentiment': sentiment,
            'language': language
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted entities with type and position
        """
        entities = []
        
        # Use spaCy if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'type': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            except Exception as e:
                logger.error(f"Error in spaCy entity extraction: {str(e)}")
        else:
            # Fallback to regex-based extraction
            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(email_pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'EMAIL',
                    'start': match.start(),
                    'end': match.end()
                })
            
            # Extract URLs
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            for match in re.finditer(url_pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'URL',
                    'start': match.start(),
                    'end': match.end()
                })
            
            # Extract phone numbers
            phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'
            for match in re.finditer(phone_pattern, text):
                entities.append({
                    'text': match.group(),
                    'type': 'PHONE',
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Text to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of extracted keywords
        """
        # Normalize text
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        words = text.split()
        
        # Remove stopwords
        words = [word for word in words if word not in self.stopwords and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Get top keywords
        keywords = [word for word, _ in word_counts.most_common(top_n)]
        
        return keywords
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        # Use NLTK if available
        if self.sentiment_analyzer:
            try:
                scores = self.sentiment_analyzer.polarity_scores(text)
                return scores
            except Exception as e:
                logger.error(f"Error in NLTK sentiment analysis: {str(e)}")
        
        # Simple fallback sentiment analysis
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                         'happy', 'pleased', 'delighted', 'love', 'like', 'best', 'better',
                         'awesome', 'outstanding', 'superb', 'perfect', 'brilliant'}
        
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing',
                         'hate', 'dislike', 'worst', 'worse', 'annoying', 'frustrating',
                         'useless', 'stupid', 'angry', 'upset', 'sad', 'unhappy'}
        
        # Normalize and tokenize
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Count sentiment words
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        total_words = len(words) or 1  # Avoid division by zero
        
        # Calculate scores
        positive = pos_count / total_words
        negative = neg_count / total_words
        neutral = 1.0 - (positive + negative)
        compound = positive - negative
        
        return {
            'compound': compound,
            'positive': positive,
            'negative': negative,
            'neutral': neutral
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code
        """
        # Try to use langdetect if available
        try:
            from langdetect import detect
            return detect(text)
        except ImportError:
            logger.warning("langdetect not available. Language detection limited.")
        except Exception as e:
            logger.error(f"Error in language detection: {str(e)}")
        
        # Simple fallback for English detection
        english_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I',
                        'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'}
        
        # Normalize and tokenize
        text = text.lower()
        words = set(re.findall(r'\b\w+\b', text))
        
        # Check overlap with English words
        overlap = words.intersection(english_words)
        if len(overlap) >= 3 and len(words) >= 5:
            return 'en'
        
        return 'unknown'
    
    def extract_topics(self, text: str, num_topics: int = 5) -> List[List[str]]:
        """
        Extract topics from text.
        
        Args:
            text: Text to analyze
            num_topics: Number of topics to extract
            
        Returns:
            List of topic word lists
        """
        # Try to use gensim if available
        try:
            from gensim import corpora, models
            
            # Normalize and tokenize
            text = text.lower()
            text = text.translate(str.maketrans('', '', string.punctuation))
            words = text.split()
            
            # Remove stopwords
            words = [word for word in words if word not in self.stopwords and len(word) > 2]
            
            # Create dictionary and corpus
            dictionary = corpora.Dictionary([words])
            corpus = [dictionary.doc2bow(words)]
            
            # Train LDA model
            lda_model = models.LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)
            
            # Extract topics
            topics = []
            for topic_id in range(num_topics):
                topic_words = [word for word, _ in lda_model.show_topic(topic_id, 5)]
                topics.append(topic_words)
            
            return topics
        
        except ImportError:
            logger.warning("gensim not available. Topic extraction limited.")
            
            # Simple fallback using keyword extraction
            keywords = self.extract_keywords(text, top_n=num_topics * 5)
            
            # Group into pseudo-topics
            topics = []
            for i in range(0, len(keywords), 5):
                topic = keywords[i:i+5]
                if topic:  # Ensure we don't add empty topics
                    topics.append(topic)
            
            # Ensure we have the requested number of topics
            while len(topics) < num_topics:
                topics.append(['unknown'])
            
            return topics[:num_topics]
        
        except Exception as e:
            logger.error(f"Error in topic extraction: {str(e)}")
            return [['unknown'] for _ in range(num_topics)]
    
    def classify_content(self, text: str) -> Dict[str, float]:
        """
        Classify text content into categories.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary mapping categories to confidence scores
        """
        # Define simple keyword-based categories
        categories = {
            'business': {'meeting', 'deadline', 'project', 'client', 'report', 'budget', 'proposal',
                        'contract', 'invoice', 'payment', 'schedule', 'conference', 'business'},
            'personal': {'family', 'friend', 'love', 'home', 'weekend', 'dinner', 'birthday',
                        'holiday', 'vacation', 'party', 'personal', 'feeling'},
            'technical': {'code', 'bug', 'server', 'database', 'api', 'software', 'hardware',
                         'system', 'error', 'update', 'version', 'technical', 'programming'},
            'social': {'meet', 'lunch', 'coffee', 'drink', 'party', 'event', 'gathering',
                      'invitation', 'celebrate', 'congratulations', 'thanks', 'social'}
        }
        
        # Normalize and tokenize
        text = text.lower()
        words = set(re.findall(r'\b\w+\b', text))
        
        # Calculate category scores
        scores = {}
        for category, keywords in categories.items():
            overlap = words.intersection(keywords)
            score = len(overlap) / (len(keywords) or 1)  # Avoid division by zero
            scores[category] = min(score, 1.0)  # Cap at 1.0
        
        return scores
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a summary of text.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summarized text
        """
        # Try to use sumy if available
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lex_rank import LexRankSummarizer
            
            # Parse text
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            
            # Create summarizer
            summarizer = LexRankSummarizer()
            
            # Generate summary
            summary_sentences = summarizer(parser.document, max_sentences)
            summary = ' '.join(str(sentence) for sentence in summary_sentences)
            
            return summary
        
        except ImportError:
            logger.warning("sumy not available. Using simple summarization.")
            
            # Simple fallback summarization
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            if len(sentences) <= max_sentences:
                return text
            
            # Score sentences based on position and keyword presence
            keywords = set(self.extract_keywords(text, top_n=20))
            
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                # Position score (first and last sentences are important)
                position_score = 1.0
                if i == 0:
                    position_score = 2.0
                elif i == len(sentences) - 1:
                    position_score = 1.5
                
                # Keyword score
                words = set(re.findall(r'\b\w+\b', sentence.lower()))
                keyword_score = len(words.intersection(keywords)) / (len(keywords) or 1)
                
                # Length score (prefer medium-length sentences)
                length = len(words)
                length_score = 1.0
                if length < 5:
                    length_score = 0.5
                elif length > 25:
                    length_score = 0.7
                
                # Total score
                total_score = position_score * 0.3 + keyword_score * 0.5 + length_score * 0.2
                
                scored_sentences.append((sentence, total_score))
            
            # Sort by score and take top sentences
            top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
            
            # Sort by original position
            summary_sentences = []
            for sentence, _ in top_sentences:
                original_index = sentences.index(sentence)
                summary_sentences.append((original_index, sentence))
            
            summary_sentences.sort()  # Sort by original position
            
            return ' '.join(sentence for _, sentence in summary_sentences)
        
        except Exception as e:
            logger.error(f"Error in text summarization: {str(e)}")
            
            # Return first few sentences as fallback
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return ' '.join(sentences[:max_sentences])