"""
Communication topic analysis module.

This module provides functionality for analyzing topics in communication data,
including topic extraction, clustering, and trend analysis.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import re

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    """Analyzer for communication topics."""
    
    def __init__(self):
        """Initialize the topic analyzer."""
        self.topics = {}
        self.nlp_available = False
        self.vectorizer = None
        self.lda_model = None
        
        # Try to import NLP libraries
        try:
            import spacy
            import sklearn
            from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
            from sklearn.decomposition import LatentDirichletAllocation
            
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.nlp_available = True
            except:
                logger.warning("spaCy model 'en_core_web_sm' not available")
                
            # Initialize vectorizer and LDA model
            self.vectorizer = CountVectorizer(
                max_df=0.95,
                min_df=2,
                stop_words='english',
                max_features=1000
            )
            
            self.lda_model = LatentDirichletAllocation(
                n_components=10,
                random_state=42
            )
            
        except ImportError:
            logger.warning("NLP libraries not available for advanced topic analysis")
    
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze topics in messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of topic analysis results
        """
        logger.info(f"Analyzing topics in {len(messages)} messages")
        
        if not messages:
            return {"topics": {}, "error": "No messages to analyze"}
        
        # Convert to DataFrame for easier analysis
        try:
            df = pd.DataFrame(messages)
            
            # Ensure content column exists
            if 'content' not in df.columns:
                return {"topics": {}, "error": "Messages missing content field"}
            
            # Ensure timestamp column exists
            if 'timestamp' not in df.columns:
                return {"topics": {}, "error": "Messages missing timestamp field"}
            
            # Convert timestamps to datetime objects if they're not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Basic keyword extraction
            keyword_topics = self._extract_keywords(df)
            
            # Advanced topic modeling if NLP libraries are available
            if self.nlp_available:
                advanced_topics = self._extract_topics_lda(df)
                topic_trends = self._analyze_topic_trends(df)
                topic_relationships = self._analyze_topic_relationships(df)
                
                all_topics = {
                    "keywords": keyword_topics,
                    "topics": advanced_topics,
                    "trends": topic_trends,
                    "relationships": topic_relationships
                }
            else:
                all_topics = {
                    "keywords": keyword_topics,
                    "note": "Advanced topic analysis not available due to missing NLP libraries"
                }
            
            # Store topics
            self.topics = all_topics
            
            return {"topics": all_topics}
            
        except Exception as e:
            logger.error(f"Error analyzing topics: {str(e)}")
            return {"topics": {}, "error": str(e)}
    
    def _extract_keywords(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract keywords from messages using basic techniques.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of keyword analysis results
        """
        # Combine all message content
        all_text = " ".join(df['content'].fillna("").astype(str))
        
        # Remove URLs
        all_text = re.sub(r'https?://\S+|www\.\S+', '', all_text)
        
        # Remove special characters and convert to lowercase
        all_text = re.sub(r'[^\w\s]', '', all_text.lower())
        
        # Split into words
        words = all_text.split()
        
        # Remove common stop words
        stop_words = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
            'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        top_keywords = word_counts.most_common(50)
        
        # Extract bigrams (pairs of consecutive words)
        bigrams = []
        for i in range(len(filtered_words) - 1):
            bigrams.append((filtered_words[i], filtered_words[i+1]))
        
        # Count bigram frequencies
        bigram_counts = Counter(bigrams)
        
        # Get top bigrams
        top_bigrams = bigram_counts.most_common(30)
        
        # Format bigrams as strings
        formatted_bigrams = [f"{b[0]} {b[1]}" for b, count in top_bigrams]
        bigram_counts_dict = {f"{b[0]} {b[1]}": count for (b[0], b[1]), count in top_bigrams}
        
        return {
            "top_keywords": dict(top_keywords),
            "top_bigrams": bigram_counts_dict
        }
    
    def _extract_topics_lda(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract topics using Latent Dirichlet Allocation.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of LDA topic analysis results
        """
        if not self.nlp_available or self.vectorizer is None or self.lda_model is None:
            return {"error": "NLP libraries not available for LDA topic analysis"}
        
        try:
            # Preprocess text
            processed_texts = []
            for text in df['content'].fillna("").astype(str):
                # Remove URLs
                text = re.sub(r'https?://\S+|www\.\S+', '', text)
                
                # Process with spaCy
                doc = self.nlp(text)
                
                # Keep only nouns, adjectives, verbs, and adverbs
                tokens = [token.lemma_.lower() for token in doc 
                         if (token.pos_ in ['NOUN', 'ADJ', 'VERB', 'ADV']) and 
                            (not token.is_stop) and 
                            (len(token.text) > 2)]
                
                processed_texts.append(" ".join(tokens))
            
            # Create document-term matrix
            dtm = self.vectorizer.fit_transform(processed_texts)
            
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Fit LDA model
            self.lda_model.fit(dtm)
            
            # Extract topics
            topics = []
            for topic_idx, topic in enumerate(self.lda_model.components_):
                # Get top words for this topic
                top_words_idx = topic.argsort()[:-11:-1]
                top_words = [feature_names[i] for i in top_words_idx]
                
                topics.append({
                    "id": topic_idx,
                    "words": top_words,
                    "weights": topic[top_words_idx].tolist()
                })
            
            # Get topic distribution for each document
            doc_topic_dist = self.lda_model.transform(dtm)
            
            # Assign dominant topic to each document
            dominant_topics = []
            for i, dist in enumerate(doc_topic_dist):
                dominant_topic = np.argmax(dist)
                dominant_topics.append({
                    "message_index": i,
                    "topic_id": int(dominant_topic),
                    "confidence": float(dist[dominant_topic])
                })
            
            return {
                "model_topics": topics,
                "document_topics": dominant_topics,
                "coherence_score": None  # Would require additional computation
            }
            
        except Exception as e:
            logger.error(f"Error in LDA topic extraction: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_topic_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze how topics change over time.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of topic trend analysis results
        """
        if not self.nlp_available or self.vectorizer is None or self.lda_model is None:
            return {"error": "NLP libraries not available for topic trend analysis"}
        
        try:
            # Ensure we have timestamps
            if 'timestamp' not in df.columns:
                return {"error": "Messages missing timestamp field"}
            
            # Group messages by time period (e.g., month)
            df['month'] = df['timestamp'].dt.to_period('M')
            
            # Get unique time periods
            time_periods = df['month'].unique()
            
            # Analyze topics for each time period
            period_topics = {}
            for period in time_periods:
                # Get messages for this period
                period_df = df[df['month'] == period]
                
                # Extract keywords for this period
                period_keywords = self._extract_keywords(period_df)
                
                # Store results
                period_topics[str(period)] = period_keywords
            
            # Analyze topic evolution
            topic_evolution = self._analyze_topic_evolution(period_topics)
            
            return {
                "period_topics": period_topics,
                "topic_evolution": topic_evolution
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic trends: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_topic_evolution(self, period_topics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how topics evolve over time.
        
        Args:
            period_topics: Dictionary of topics by time period
            
        Returns:
            Dictionary of topic evolution analysis results
        """
        # Get all periods in chronological order
        periods = sorted(period_topics.keys())
        
        if len(periods) < 2:
            return {"note": "Not enough time periods for evolution analysis"}
        
        # Track keyword frequency changes
        keyword_trends = {}
        
        # For each period (except the first), compare with previous period
        for i in range(1, len(periods)):
            current_period = periods[i]
            previous_period = periods[i-1]
            
            # Get keywords for both periods
            current_keywords = period_topics[current_period].get('top_keywords', {})
            previous_keywords = period_topics[previous_period].get('top_keywords', {})
            
            # Find keywords in both periods
            common_keywords = set(current_keywords.keys()) & set(previous_keywords.keys())
            
            # Calculate change in frequency
            for keyword in common_keywords:
                current_count = current_keywords[keyword]
                previous_count = previous_keywords[keyword]
                change = current_count - previous_count
                
                if keyword not in keyword_trends:
                    keyword_trends[keyword] = []
                
                keyword_trends[keyword].append({
                    "period": current_period,
                    "count": current_count,
                    "previous_count": previous_count,
                    "change": change
                })
            
            # Find new keywords
            new_keywords = set(current_keywords.keys()) - set(previous_keywords.keys())
            for keyword in new_keywords:
                if keyword not in keyword_trends:
                    keyword_trends[keyword] = []
                
                keyword_trends[keyword].append({
                    "period": current_period,
                    "count": current_keywords[keyword],
                    "previous_count": 0,
                    "change": current_keywords[keyword],
                    "new": True
                })
            
            # Find disappeared keywords
            disappeared_keywords = set(previous_keywords.keys()) - set(current_keywords.keys())
            for keyword in disappeared_keywords:
                if keyword not in keyword_trends:
                    keyword_trends[keyword] = []
                
                keyword_trends[keyword].append({
                    "period": current_period,
                    "count": 0,
                    "previous_count": previous_keywords[keyword],
                    "change": -previous_keywords[keyword],
                    "disappeared": True
                })
        
        # Calculate overall trend for each keyword
        keyword_overall_trends = {}
        for keyword, trends in keyword_trends.items():
            if len(trends) >= 2:
                # Calculate slope of trend line
                counts = [t['count'] for t in trends]
                x = list(range(len(counts)))
                
                # Simple linear regression
                mean_x = sum(x) / len(x)
                mean_y = sum(counts) / len(counts)
                
                numerator = sum((x[i] - mean_x) * (counts[i] - mean_y) for i in range(len(x)))
                denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
                
                slope = numerator / denominator if denominator != 0 else 0
                
                keyword_overall_trends[keyword] = {
                    "slope": slope,
                    "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                    "data_points": len(trends)
                }
        
        return {
            "keyword_trends": keyword_trends,
            "keyword_overall_trends": keyword_overall_trends
        }
    
    def _analyze_topic_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze relationships between topics.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of topic relationship analysis results
        """
        if not self.nlp_available:
            return {"error": "NLP libraries not available for topic relationship analysis"}
        
        try:
            # Extract keywords for each message
            message_keywords = []
            for text in df['content'].fillna("").astype(str):
                # Process with spaCy
                doc = self.nlp(text)
                
                # Extract keywords (nouns and proper nouns)
                keywords = [token.text.lower() for token in doc if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop]
                
                message_keywords.append(keywords)
            
            # Find co-occurring keywords
            keyword_cooccurrence = {}
            
            for keywords in message_keywords:
                # Create pairs of keywords
                for i in range(len(keywords)):
                    for j in range(i+1, len(keywords)):
                        # Create a sorted pair to avoid duplicates
                        pair = tuple(sorted([keywords[i], keywords[j]]))
                        
                        if pair in keyword_cooccurrence:
                            keyword_cooccurrence[pair] += 1
                        else:
                            keyword_cooccurrence[pair] = 1
            
            # Sort by frequency
            sorted_cooccurrence = sorted(keyword_cooccurrence.items(), key=lambda x: x[1], reverse=True)
            
            # Get top co-occurrences
            top_cooccurrences = sorted_cooccurrence[:100]
            
            # Format results
            formatted_cooccurrences = {f"{pair[0]}-{pair[1]}": count for pair, count in top_cooccurrences}
            
            return {
                "keyword_cooccurrence": formatted_cooccurrences
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic relationships: {str(e)}")
            return {"error": str(e)}
    
    def get_top_topics(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Get the top topics by frequency.
        
        Args:
            top_n: Number of top topics to return
            
        Returns:
            List of (topic, frequency) tuples
        """
        if not self.topics or 'keywords' not in self.topics:
            return []
        
        # Get top keywords
        top_keywords = self.topics['keywords'].get('top_keywords', {})
        
        # Sort by frequency (descending)
        sorted_topics = sorted(top_keywords.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N
        return sorted_topics[:top_n]