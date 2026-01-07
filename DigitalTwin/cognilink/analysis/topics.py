"""
Topic Analyzer for CogniLink

This module analyzes communication content to identify topics, themes,
and knowledge areas present in the communications.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Counter as CounterType
from datetime import datetime
from collections import Counter, defaultdict
import json
import re
import string
import math

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    """
    Analyzer for topics and themes in communication content.
    
    This class identifies and analyzes topics, themes, and knowledge areas
    in communication content using text analysis techniques.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the topic analyzer.
        
        Args:
            config: Configuration dictionary for the analyzer
        """
        self.config = config or {}
        self.stopwords = self._load_stopwords()
        
        # Initialize NLP components if available
        self.nlp = None
        self.lda_model = None
        
        # Try to load spaCy if available
        try:
            import spacy
            self.nlp = spacy.load(self.config.get('spacy_model', 'en_core_web_sm'))
            logger.info("Loaded spaCy NLP model")
        except (ImportError, OSError):
            logger.warning("spaCy not available or model not found. Some features will be limited.")
        
        # Try to load gensim if available
        try:
            import gensim
            logger.info("gensim library available for topic modeling")
        except ImportError:
            logger.warning("gensim not available. Topic modeling will be limited.")
    
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
            'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now',
            'hi', 'hello', 'hey', 'thanks', 'thank', 'regards', 'best', 'sincerely',
            'please', 'would', 'could', 'may', 'might', 'must', 'need', 'shall',
            'should', 'will', 'would', 'yes', 'no', 'ok', 'okay', 'right', 'sure',
            'well', 'um', 'uh', 'hmm', 'huh', 'eh', 'ah', 'oh', 'ooh', 'ow', 'wow',
            'alas', 'eh', 'er', 'etc', 'hmm', 'yep', 'yeah', 'nope', 'nah'
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
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for topic analysis.
        
        Args:
            text: Text to preprocess
            
        Returns:
            List of preprocessed tokens
        """
        if not text or not isinstance(text, str):
            return []
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Tokenize
        if self.nlp:
            # Use spaCy for tokenization and lemmatization
            doc = self.nlp(text)
            tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and len(token.text) > 2]
        else:
            # Simple tokenization
            tokens = [word for word in text.split() if word not in self.stopwords and len(word) > 2]
        
        return tokens
    
    def extract_topics_lda(self, texts: List[str], num_topics: int = 5, 
                          words_per_topic: int = 10) -> List[Dict[str, Any]]:
        """
        Extract topics using Latent Dirichlet Allocation (LDA).
        
        Args:
            texts: List of text documents
            num_topics: Number of topics to extract
            words_per_topic: Number of words per topic
            
        Returns:
            List of topic dictionaries
        """
        if not texts:
            logger.warning("No texts provided for topic extraction")
            return []
        
        try:
            from gensim import corpora, models
            
            # Preprocess texts
            processed_texts = [self.preprocess_text(text) for text in texts]
            
            # Filter out empty documents
            processed_texts = [tokens for tokens in processed_texts if tokens]
            
            if not processed_texts:
                logger.warning("No valid texts after preprocessing")
                return []
            
            # Create dictionary
            dictionary = corpora.Dictionary(processed_texts)
            
            # Filter out extreme values
            dictionary.filter_extremes(no_below=2, no_above=0.9)
            
            # Create corpus
            corpus = [dictionary.doc2bow(text) for text in processed_texts]
            
            # Train LDA model
            lda_model = models.LdaModel(
                corpus=corpus,
                id2word=dictionary,
                num_topics=num_topics,
                passes=10,
                alpha='auto',
                per_word_topics=True
            )
            
            # Extract topics
            topics = []
            for topic_id in range(num_topics):
                topic_words = lda_model.show_topic(topic_id, words_per_topic)
                topics.append({
                    'id': topic_id,
                    'words': [{'word': word, 'weight': weight} for word, weight in topic_words],
                    'label': self._generate_topic_label([word for word, _ in topic_words[:5]])
                })
            
            # Store model for later use
            self.lda_model = lda_model
            
            return topics
        
        except ImportError:
            logger.warning("gensim not available. Using simple topic extraction.")
            return self._extract_topics_simple(texts, num_topics, words_per_topic)
        
        except Exception as e:
            logger.error(f"Error in LDA topic extraction: {str(e)}")
            return self._extract_topics_simple(texts, num_topics, words_per_topic)
    
    def _extract_topics_simple(self, texts: List[str], num_topics: int = 5,
                              words_per_topic: int = 10) -> List[Dict[str, Any]]:
        """
        Simple topic extraction using word frequency and co-occurrence.
        
        Args:
            texts: List of text documents
            num_topics: Number of topics to extract
            words_per_topic: Number of words per topic
            
        Returns:
            List of topic dictionaries
        """
        if not texts:
            return []
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Filter out empty documents
        processed_texts = [tokens for tokens in processed_texts if tokens]
        
        if not processed_texts:
            return []
        
        # Count word frequencies
        word_counts = Counter()
        for tokens in processed_texts:
            word_counts.update(tokens)
        
        # Get most common words
        common_words = [word for word, _ in word_counts.most_common(num_topics * words_per_topic)]
        
        # Create simple topics based on co-occurrence
        topics = []
        
        # Build co-occurrence matrix
        co_occurrence = defaultdict(Counter)
        
        for tokens in processed_texts:
            # Count co-occurrences within each document
            for i, word1 in enumerate(tokens):
                if word1 not in common_words:
                    continue
                
                for word2 in tokens[i+1:]:
                    if word2 not in common_words:
                        continue
                    
                    co_occurrence[word1][word2] += 1
                    co_occurrence[word2][word1] += 1
        
        # Create topics based on co-occurrence clusters
        used_words = set()
        
        for i in range(min(num_topics, len(common_words))):
            # Find a seed word not yet used
            seed_word = None
            for word in common_words:
                if word not in used_words:
                    seed_word = word
                    break
            
            if not seed_word:
                break
            
            # Find related words based on co-occurrence
            related_words = co_occurrence[seed_word].most_common(words_per_topic - 1)
            topic_words = [(seed_word, word_counts[seed_word])]
            
            for word, count in related_words:
                if word not in used_words:
                    topic_words.append((word, count))
                    used_words.add(word)
                    
                    if len(topic_words) >= words_per_topic:
                        break
            
            # Mark seed word as used
            used_words.add(seed_word)
            
            # Create topic
            topics.append({
                'id': i,
                'words': [{'word': word, 'weight': count / max(1, word_counts[word])} 
                         for word, count in topic_words],
                'label': self._generate_topic_label([word for word, _ in topic_words[:5]])
            })
        
        return topics
    
    def _generate_topic_label(self, top_words: List[str]) -> str:
        """
        Generate a descriptive label for a topic based on its top words.
        
        Args:
            top_words: List of top words in the topic
            
        Returns:
            Topic label
        """
        if not top_words:
            return "Unknown Topic"
        
        # Simple approach: join top 2-3 words
        if len(top_words) >= 3:
            return f"{top_words[0].capitalize()} / {top_words[1]} / {top_words[2]}"
        elif len(top_words) == 2:
            return f"{top_words[0].capitalize()} / {top_words[1]}"
        else:
            return top_words[0].capitalize()
    
    def analyze_topic_distribution(self, texts: List[str], topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze the distribution of topics across documents.
        
        Args:
            texts: List of text documents
            topics: List of topics from extract_topics_lda
            
        Returns:
            List of document topic distributions
        """
        if not texts or not topics:
            return []
        
        try:
            # If we have a trained LDA model, use it
            if self.lda_model:
                from gensim import corpora
                
                # Preprocess texts
                processed_texts = [self.preprocess_text(text) for text in texts]
                
                # Create corpus
                dictionary = self.lda_model.id2word
                corpus = [dictionary.doc2bow(text) for text in processed_texts]
                
                # Get topic distributions
                distributions = []
                
                for i, doc_bow in enumerate(corpus):
                    # Get topic distribution for document
                    doc_topics = self.lda_model.get_document_topics(doc_bow)
                    
                    # Convert to dictionary
                    topic_dist = {topic_id: weight for topic_id, weight in doc_topics}
                    
                    # Create distribution entry
                    distributions.append({
                        'document_id': i,
                        'topics': [{'topic_id': topic_id, 'weight': weight} 
                                 for topic_id, weight in sorted(topic_dist.items(), 
                                                              key=lambda x: x[1], 
                                                              reverse=True)]
                    })
                
                return distributions
            else:
                # Fall back to simple keyword matching
                return self._analyze_topic_distribution_simple(texts, topics)
        
        except Exception as e:
            logger.error(f"Error in topic distribution analysis: {str(e)}")
            return self._analyze_topic_distribution_simple(texts, topics)
    
    def _analyze_topic_distribution_simple(self, texts: List[str], 
                                         topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Simple analysis of topic distribution using keyword matching.
        
        Args:
            texts: List of text documents
            topics: List of topics
            
        Returns:
            List of document topic distributions
        """
        if not texts or not topics:
            return []
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Create topic word sets
        topic_words = {}
        for topic in topics:
            words = [item['word'] for item in topic['words']]
            topic_words[topic['id']] = set(words)
        
        # Analyze distribution for each document
        distributions = []
        
        for i, tokens in enumerate(processed_texts):
            # Count topic word occurrences
            topic_counts = {}
            
            for topic_id, word_set in topic_words.items():
                # Count matching words
                matches = sum(1 for token in tokens if token in word_set)
                if matches > 0:
                    topic_counts[topic_id] = matches
            
            # Normalize to get weights
            total_matches = sum(topic_counts.values()) or 1
            topic_weights = {topic_id: count / total_matches 
                           for topic_id, count in topic_counts.items()}
            
            # Create distribution entry
            distributions.append({
                'document_id': i,
                'topics': [{'topic_id': topic_id, 'weight': weight} 
                         for topic_id, weight in sorted(topic_weights.items(), 
                                                      key=lambda x: x[1], 
                                                      reverse=True)]
            })
        
        return distributions
    
    def extract_key_phrases(self, texts: List[str], max_phrases: int = 10) -> List[Dict[str, Any]]:
        """
        Extract key phrases from texts.
        
        Args:
            texts: List of text documents
            max_phrases: Maximum number of key phrases to extract
            
        Returns:
            List of key phrase dictionaries
        """
        if not texts:
            return []
        
        # Combine texts
        combined_text = " ".join(texts)
        
        # Try to use advanced NLP if available
        if self.nlp:
            try:
                # Process with spaCy
                doc = self.nlp(combined_text)
                
                # Extract noun phrases
                noun_phrases = []
                
                for chunk in doc.noun_chunks:
                    # Clean and normalize phrase
                    phrase = chunk.text.lower()
                    phrase = re.sub(r'[^\w\s]', '', phrase)
                    phrase = re.sub(r'\s+', ' ', phrase).strip()
                    
                    # Filter out short or stopword-only phrases
                    words = phrase.split()
                    if (len(words) > 1 and 
                        len(phrase) > 3 and 
                        not all(word in self.stopwords for word in words)):
                        noun_phrases.append(phrase)
                
                # Count phrase frequencies
                phrase_counts = Counter(noun_phrases)
                
                # Get top phrases
                top_phrases = phrase_counts.most_common(max_phrases)
                
                # Format results
                return [{'phrase': phrase, 'count': count} for phrase, count in top_phrases]
            
            except Exception as e:
                logger.error(f"Error in spaCy key phrase extraction: {str(e)}")
        
        # Fall back to simple n-gram extraction
        return self._extract_ngram_phrases(combined_text, max_phrases)
    
    def _extract_ngram_phrases(self, text: str, max_phrases: int = 10) -> List[Dict[str, Any]]:
        """
        Extract key phrases using n-gram frequency.
        
        Args:
            text: Text to analyze
            max_phrases: Maximum number of phrases to extract
            
        Returns:
            List of key phrase dictionaries
        """
        # Normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize
        tokens = text.split()
        
        # Generate n-grams (2-3 words)
        bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
        trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)]
        
        # Filter n-grams
        filtered_bigrams = [bg for bg in bigrams if not all(word in self.stopwords for word in bg.split())]
        filtered_trigrams = [tg for tg in trigrams if not all(word in self.stopwords for word in tg.split())]
        
        # Combine and count
        all_ngrams = filtered_bigrams + filtered_trigrams
        ngram_counts = Counter(all_ngrams)
        
        # Get top phrases
        top_phrases = ngram_counts.most_common(max_phrases)
        
        # Format results
        return [{'phrase': phrase, 'count': count} for phrase, count in top_phrases]
    
    def analyze_topic_trends(self, texts: List[str], timestamps: List[datetime], 
                           num_topics: int = 5) -> Dict[str, Any]:
        """
        Analyze how topics change over time.
        
        Args:
            texts: List of text documents
            timestamps: List of document timestamps
            num_topics: Number of topics to extract
            
        Returns:
            Dictionary with topic trend analysis results
        """
        if not texts or not timestamps or len(texts) != len(timestamps):
            logger.warning("Invalid inputs for topic trend analysis")
            return {
                'topics': [],
                'time_periods': [],
                'topic_trends': []
            }
        
        # Extract topics from all texts
        topics = self.extract_topics_lda(texts, num_topics=num_topics)
        
        # Sort documents by timestamp
        sorted_data = sorted(zip(texts, timestamps), key=lambda x: x[1])
        sorted_texts, sorted_timestamps = zip(*sorted_data)
        
        # Determine time periods (e.g., months)
        min_date = min(timestamps).date().replace(day=1)
        max_date = max(timestamps).date().replace(day=1)
        
        # Create monthly periods
        periods = []
        current_date = min_date
        while current_date <= max_date:
            next_month = current_date.month + 1
            next_year = current_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_date = current_date.replace(year=next_year, month=next_month)
            
            periods.append((current_date, next_date))
            current_date = next_date
        
        # Group texts by period
        period_texts = [[] for _ in periods]
        
        for text, timestamp in zip(sorted_texts, sorted_timestamps):
            date = timestamp.date()
            for i, (start_date, end_date) in enumerate(periods):
                if start_date <= date < end_date:
                    period_texts[i].append(text)
                    break
        
        # Analyze topic distribution for each period
        period_distributions = []
        
        for period_idx, texts_in_period in enumerate(period_texts):
            if not texts_in_period:
                # No texts in this period
                period_distributions.append({})
                continue
            
            # Analyze topic distribution
            distributions = self.analyze_topic_distribution(texts_in_period, topics)
            
            # Aggregate distributions for the period
            topic_weights = defaultdict(float)
            
            for dist in distributions:
                for topic in dist['topics']:
                    topic_weights[topic['topic_id']] += topic['weight']
            
            # Normalize weights
            total_weight = sum(topic_weights.values()) or 1
            normalized_weights = {topic_id: weight / total_weight 
                                for topic_id, weight in topic_weights.items()}
            
            period_distributions.append(normalized_weights)
        
        # Format time periods
        formatted_periods = [{'start': start.isoformat(), 'end': end.isoformat()} 
                           for start, end in periods]
        
        # Format topic trends
        topic_trends = []
        
        for topic in topics:
            topic_id = topic['id']
            trend_data = []
            
            for period_idx, dist in enumerate(period_distributions):
                weight = dist.get(topic_id, 0)
                trend_data.append({
                    'period_idx': period_idx,
                    'weight': weight
                })
            
            topic_trends.append({
                'topic_id': topic_id,
                'trend': trend_data
            })
        
        return {
            'topics': topics,
            'time_periods': formatted_periods,
            'topic_trends': topic_trends
        }
    
    def extract_knowledge_areas(self, texts: List[str], num_areas: int = 5) -> List[Dict[str, Any]]:
        """
        Extract knowledge areas from texts.
        
        Args:
            texts: List of text documents
            num_areas: Number of knowledge areas to extract
            
        Returns:
            List of knowledge area dictionaries
        """
        # Knowledge area extraction is similar to topic extraction but focuses on
        # identifying domains of knowledge rather than specific topics
        
        # Extract topics first
        topics = self.extract_topics_lda(texts, num_topics=num_areas * 2)
        
        if not topics:
            return []
        
        # Define knowledge area categories
        knowledge_categories = {
            'technology': {'software', 'hardware', 'code', 'programming', 'data', 'algorithm',
                         'computer', 'system', 'network', 'database', 'cloud', 'app',
                         'application', 'web', 'mobile', 'development', 'tech', 'technology',
                         'server', 'api', 'interface', 'platform', 'digital', 'online',
                         'internet', 'cyber', 'security', 'encryption', 'ai', 'ml',
                         'artificial', 'intelligence', 'machine', 'learning'},
            
            'business': {'business', 'company', 'market', 'customer', 'client', 'product',
                       'service', 'sales', 'revenue', 'profit', 'strategy', 'management',
                       'team', 'project', 'deadline', 'meeting', 'presentation', 'report',
                       'budget', 'finance', 'investment', 'investor', 'stakeholder',
                       'marketing', 'brand', 'growth', 'startup', 'enterprise', 'corporate'},
            
            'science': {'science', 'research', 'study', 'experiment', 'theory', 'hypothesis',
                      'analysis', 'data', 'results', 'findings', 'publication', 'journal',
                      'physics', 'chemistry', 'biology', 'mathematics', 'statistics',
                      'scientific', 'academic', 'professor', 'laboratory', 'experiment'},
            
            'arts': {'art', 'design', 'creative', 'music', 'film', 'movie', 'book',
                   'literature', 'novel', 'story', 'author', 'writer', 'artist',
                   'painting', 'drawing', 'photography', 'theater', 'performance',
                   'culture', 'exhibition', 'gallery', 'museum', 'aesthetic'},
            
            'health': {'health', 'medical', 'doctor', 'patient', 'hospital', 'clinic',
                     'treatment', 'therapy', 'medicine', 'disease', 'condition',
                     'symptom', 'diagnosis', 'healthcare', 'wellness', 'fitness',
                     'exercise', 'diet', 'nutrition', 'mental', 'physical'},
            
            'education': {'education', 'school', 'university', 'college', 'student',
                        'teacher', 'professor', 'class', 'course', 'lecture', 'learn',
                        'study', 'academic', 'degree', 'curriculum', 'teaching',
                        'learning', 'training', 'skill', 'knowledge', 'educational'},
            
            'finance': {'finance', 'money', 'bank', 'investment', 'fund', 'stock',
                      'market', 'trading', 'financial', 'economy', 'economic',
                      'currency', 'payment', 'transaction', 'account', 'budget',
                      'expense', 'income', 'revenue', 'profit', 'loss', 'tax'},
            
            'legal': {'legal', 'law', 'lawyer', 'attorney', 'court', 'judge',
                    'case', 'contract', 'agreement', 'compliance', 'regulation',
                    'regulatory', 'legislation', 'statute', 'rights', 'liability',
                    'lawsuit', 'plaintiff', 'defendant', 'jurisdiction'}
        }
        
        # Score topics against knowledge categories
        knowledge_areas = []
        
        for category, keywords in knowledge_categories.items():
            # Calculate score for each topic
            topic_scores = []
            
            for topic in topics:
                topic_words = [item['word'] for item in topic['words']]
                
                # Calculate overlap score
                overlap = sum(1 for word in topic_words if word in keywords)
                score = overlap / len(topic_words) if topic_words else 0
                
                if score > 0:
                    topic_scores.append((topic['id'], score))
            
            # If we have matching topics, create a knowledge area
            if topic_scores:
                # Sort by score
                topic_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Get related topics
                related_topics = []
                for topic_id, score in topic_scores[:3]:  # Top 3 related topics
                    # Find the topic
                    for topic in topics:
                        if topic['id'] == topic_id:
                            related_topics.append({
                                'topic_id': topic_id,
                                'relevance': score,
                                'words': topic['words'][:5]  # Top 5 words
                            })
                            break
                
                # Create knowledge area
                knowledge_areas.append({
                    'name': category.capitalize(),
                    'related_topics': related_topics,
                    'relevance_score': sum(score for _, score in topic_scores)
                })
        
        # Sort by relevance score
        knowledge_areas.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top N areas
        return knowledge_areas[:num_areas]
    
    def generate_comprehensive_report(self, texts: List[str], 
                                    timestamps: List[datetime] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all topic analyses.
        
        Args:
            texts: List of text documents
            timestamps: Optional list of document timestamps
            
        Returns:
            Dictionary with all analysis results
        """
        if not texts:
            logger.warning("No texts provided for topic analysis")
            return {
                'topics': [],
                'key_phrases': [],
                'knowledge_areas': [],
                'topic_trends': None,
                'generated_at': datetime.now().isoformat()
            }
        
        # Extract topics
        topics = self.extract_topics_lda(texts, num_topics=8)
        
        # Extract key phrases
        key_phrases = self.extract_key_phrases(texts, max_phrases=20)
        
        # Extract knowledge areas
        knowledge_areas = self.extract_knowledge_areas(texts, num_areas=5)
        
        # Analyze topic trends if timestamps provided
        topic_trends = None
        if timestamps and len(timestamps) == len(texts):
            topic_trends = self.analyze_topic_trends(texts, timestamps, num_topics=5)
        
        # Combine into comprehensive report
        report = {
            'topics': topics,
            'key_phrases': key_phrases,
            'knowledge_areas': knowledge_areas,
            'topic_trends': topic_trends,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def save_report_to_file(self, report: Dict[str, Any], filepath: str) -> None:
        """
        Save a topic analysis report to file.
        
        Args:
            report: Topic analysis report
            filepath: Path where the report should be saved
        """
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Topic analysis report saved to {filepath}")