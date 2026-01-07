"""
Natural Language Processing module for advanced analysis.

This module provides NLP capabilities for the integrated system,
including sentiment analysis, entity extraction, and text classification.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)

class NLPAnalyzer:
    """Natural Language Processing analyzer."""
    
    def __init__(self):
        """Initialize the NLP analyzer."""
        self.nlp_available = False
        self.sentiment_available = False
        self.ner_available = False
        self.classification_available = False
        
        # Try to import NLP libraries
        try:
            import spacy
            
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.nlp_available = True
                self.ner_available = True
                logger.info("spaCy NLP model loaded successfully")
            except:
                logger.warning("spaCy model 'en_core_web_sm' not available")
                
            # Try to import sentiment analysis
            try:
                from textblob import TextBlob
                self.sentiment_available = True
                logger.info("TextBlob sentiment analysis available")
            except ImportError:
                logger.warning("TextBlob not available for sentiment analysis")
            
            # Try to import text classification
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.naive_bayes import MultinomialNB
                self.classification_available = True
                self.vectorizer = TfidfVectorizer(max_features=1000)
                self.classifier = MultinomialNB()
                logger.info("scikit-learn text classification available")
            except ImportError:
                logger.warning("scikit-learn not available for text classification")
                
        except ImportError:
            logger.warning("spaCy not available for NLP analysis")
    
    async def analyze(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze texts using NLP techniques.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            Dictionary of NLP analysis results
        """
        logger.info(f"Analyzing {len(texts)} texts with NLP")
        
        if not texts:
            return {"error": "No texts to analyze"}
        
        results = {}
        
        # Sentiment analysis
        if self.sentiment_available:
            sentiment_results = await self._analyze_sentiment(texts)
            results["sentiment"] = sentiment_results
        
        # Entity extraction
        if self.ner_available:
            entity_results = await self._extract_entities(texts)
            results["entities"] = entity_results
        
        # Text statistics
        text_stats = await self._analyze_text_statistics(texts)
        results["statistics"] = text_stats
        
        # Readability
        readability = await self._analyze_readability(texts)
        results["readability"] = readability
        
        return results
    
    async def _analyze_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment in texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of sentiment analysis results
        """
        if not self.sentiment_available:
            return {"error": "Sentiment analysis not available"}
        
        try:
            from textblob import TextBlob
            
            # Calculate sentiment for each text
            sentiments = []
            for text in texts:
                if not text:
                    sentiments.append({"polarity": 0, "subjectivity": 0})
                    continue
                    
                blob = TextBlob(str(text))
                sentiments.append({
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity
                })
            
            # Calculate overall sentiment statistics
            polarities = [s["polarity"] for s in sentiments]
            subjectivities = [s["subjectivity"] for s in sentiments]
            
            avg_polarity = np.mean(polarities)
            avg_subjectivity = np.mean(subjectivities)
            
            # Count positive, negative, and neutral texts
            positive_count = sum(1 for p in polarities if p > 0.1)
            negative_count = sum(1 for p in polarities if p < -0.1)
            neutral_count = sum(1 for p in polarities if -0.1 <= p <= 0.1)
            
            # Calculate sentiment distribution
            total_texts = len(texts)
            sentiment_distribution = {
                "positive": positive_count / total_texts if total_texts > 0 else 0,
                "negative": negative_count / total_texts if total_texts > 0 else 0,
                "neutral": neutral_count / total_texts if total_texts > 0 else 0
            }
            
            return {
                "individual_sentiments": sentiments,
                "avg_polarity": float(avg_polarity),
                "avg_subjectivity": float(avg_subjectivity),
                "sentiment_counts": {
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count
                },
                "sentiment_distribution": sentiment_distribution
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {"error": str(e)}
    
    async def _extract_entities(self, texts: List[str]) -> Dict[str, Any]:
        """
        Extract named entities from texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of entity extraction results
        """
        if not self.ner_available:
            return {"error": "Named entity recognition not available"}
        
        try:
            # Process texts with spaCy
            all_entities = []
            entity_counts = Counter()
            entity_types = Counter()
            
            for text in texts:
                if not text:
                    continue
                    
                doc = self.nlp(str(text))
                
                # Extract entities
                for ent in doc.ents:
                    all_entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
                    
                    entity_counts[ent.text.lower()] += 1
                    entity_types[ent.label_] += 1
            
            # Get top entities
            top_entities = entity_counts.most_common(50)
            
            # Get entity type distribution
            total_entities = sum(entity_types.values())
            entity_type_distribution = {
                entity_type: count / total_entities if total_entities > 0 else 0
                for entity_type, count in entity_types.items()
            }
            
            return {
                "entities": all_entities,
                "top_entities": dict(top_entities),
                "entity_types": dict(entity_types),
                "entity_type_distribution": entity_type_distribution
            }
            
        except Exception as e:
            logger.error(f"Error in entity extraction: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_text_statistics(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze text statistics.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of text statistics
        """
        try:
            # Calculate text statistics
            text_lengths = []
            word_counts = []
            sentence_counts = []
            avg_word_lengths = []
            
            for text in texts:
                if not text:
                    text_lengths.append(0)
                    word_counts.append(0)
                    sentence_counts.append(0)
                    avg_word_lengths.append(0)
                    continue
                
                # Clean text
                clean_text = str(text).strip()
                
                # Calculate text length
                text_length = len(clean_text)
                text_lengths.append(text_length)
                
                # Calculate word count
                words = re.findall(r'\b\w+\b', clean_text.lower())
                word_count = len(words)
                word_counts.append(word_count)
                
                # Calculate sentence count
                sentences = re.split(r'[.!?]+', clean_text)
                sentence_count = sum(1 for s in sentences if s.strip())
                sentence_counts.append(sentence_count)
                
                # Calculate average word length
                if word_count > 0:
                    avg_word_length = sum(len(word) for word in words) / word_count
                else:
                    avg_word_length = 0
                avg_word_lengths.append(avg_word_length)
            
            # Calculate overall statistics
            avg_text_length = np.mean(text_lengths)
            avg_word_count = np.mean(word_counts)
            avg_sentence_count = np.mean(sentence_counts)
            avg_word_length = np.mean(avg_word_lengths)
            
            return {
                "avg_text_length": float(avg_text_length),
                "avg_word_count": float(avg_word_count),
                "avg_sentence_count": float(avg_sentence_count),
                "avg_word_length": float(avg_word_length),
                "text_lengths": text_lengths,
                "word_counts": word_counts,
                "sentence_counts": sentence_counts
            }
            
        except Exception as e:
            logger.error(f"Error in text statistics analysis: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_readability(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze text readability.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary of readability analysis results
        """
        try:
            # Calculate readability scores
            flesch_scores = []
            
            for text in texts:
                if not text:
                    flesch_scores.append(None)
                    continue
                
                # Clean text
                clean_text = str(text).strip()
                
                # Calculate word count
                words = re.findall(r'\b\w+\b', clean_text.lower())
                word_count = len(words)
                
                # Calculate sentence count
                sentences = re.split(r'[.!?]+', clean_text)
                sentence_count = sum(1 for s in sentences if s.strip())
                
                # Calculate syllable count (approximation)
                syllable_count = 0
                for word in words:
                    syllable_count += self._count_syllables(word)
                
                # Calculate Flesch Reading Ease score
                if word_count > 0 and sentence_count > 0:
                    flesch_score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
                else:
                    flesch_score = None
                
                flesch_scores.append(flesch_score)
            
            # Calculate average Flesch score
            valid_scores = [score for score in flesch_scores if score is not None]
            avg_flesch_score = np.mean(valid_scores) if valid_scores else None
            
            # Interpret Flesch score
            readability_level = None
            if avg_flesch_score is not None:
                if avg_flesch_score >= 90:
                    readability_level = "Very Easy"
                elif avg_flesch_score >= 80:
                    readability_level = "Easy"
                elif avg_flesch_score >= 70:
                    readability_level = "Fairly Easy"
                elif avg_flesch_score >= 60:
                    readability_level = "Standard"
                elif avg_flesch_score >= 50:
                    readability_level = "Fairly Difficult"
                elif avg_flesch_score >= 30:
                    readability_level = "Difficult"
                else:
                    readability_level = "Very Difficult"
            
            return {
                "flesch_scores": [float(score) if score is not None else None for score in flesch_scores],
                "avg_flesch_score": float(avg_flesch_score) if avg_flesch_score is not None else None,
                "readability_level": readability_level
            }
            
        except Exception as e:
            logger.error(f"Error in readability analysis: {str(e)}")
            return {"error": str(e)}
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word (approximation).
        
        Args:
            word: Word to count syllables in
            
        Returns:
            Number of syllables
        """
        # Remove non-alphanumeric characters
        word = re.sub(r'[^a-zA-Z]', '', word.lower())
        
        # Special cases
        if not word:
            return 0
        
        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            
            if is_vowel and not prev_is_vowel:
                count += 1
            
            prev_is_vowel = is_vowel
        
        # Adjust for silent 'e' at the end
        if word.endswith('e'):
            count -= 1
        
        # Ensure at least one syllable
        return max(1, count)
    
    async def classify_text(self, texts: List[str], labels: List[str]) -> Dict[str, Any]:
        """
        Classify texts into categories.
        
        Args:
            texts: List of text strings
            labels: List of corresponding labels
            
        Returns:
            Dictionary of classification results
        """
        if not self.classification_available:
            return {"error": "Text classification not available"}
        
        try:
            # Convert texts to feature vectors
            X = self.vectorizer.fit_transform(texts)
            
            # Train classifier
            self.classifier.fit(X, labels)
            
            # Get predictions
            predictions = self.classifier.predict(X)
            
            # Calculate accuracy
            accuracy = sum(1 for i, label in enumerate(labels) if label == predictions[i]) / len(labels)
            
            return {
                "predictions": predictions.tolist(),
                "accuracy": float(accuracy)
            }
            
        except Exception as e:
            logger.error(f"Error in text classification: {str(e)}")
            return {"error": str(e)}
    
    async def predict_category(self, text: str) -> Dict[str, Any]:
        """
        Predict category for a text.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with predicted category
        """
        if not self.classification_available or not hasattr(self.classifier, 'classes_'):
            return {"error": "Classifier not trained"}
        
        try:
            # Convert text to feature vector
            X = self.vectorizer.transform([text])
            
            # Get prediction
            prediction = self.classifier.predict(X)[0]
            
            # Get prediction probabilities
            probabilities = self.classifier.predict_proba(X)[0]
            
            # Create dictionary of probabilities
            prob_dict = {
                self.classifier.classes_[i]: float(prob)
                for i, prob in enumerate(probabilities)
            }
            
            return {
                "prediction": prediction,
                "probabilities": prob_dict
            }
            
        except Exception as e:
            logger.error(f"Error in category prediction: {str(e)}")
            return {"error": str(e)}