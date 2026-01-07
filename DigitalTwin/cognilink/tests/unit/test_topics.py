"""
Unit tests for CogniLink topics analysis.
"""
import pytest
from unittest.mock import patch, MagicMock

from cognilink.analysis.topics import TopicAnalyzer

class TestTopicAnalyzer:
    """Tests for the TopicAnalyzer class."""
    
    def test_init(self):
        """Test TopicAnalyzer initialization."""
        config = {"num_topics": 5, "min_topic_size": 3}
        analyzer = TopicAnalyzer(config)
        
        assert analyzer.config == config
        assert analyzer.num_topics == 5
        assert analyzer.min_topic_size == 3
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = {"num_topics": 5, "min_topic_size": 3}
        analyzer = TopicAnalyzer(config)
        
        # Should not raise an exception
        analyzer.validate_config()
    
    def test_validate_config_invalid(self):
        """Test config validation with invalid config."""
        # Missing num_topics
        config = {"min_topic_size": 3}
        analyzer = TopicAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
        
        # Invalid num_topics
        config = {"num_topics": 0, "min_topic_size": 3}
        analyzer = TopicAnalyzer(config)
        
        with pytest.raises(ValueError):
            analyzer.validate_config()
    
    @patch('sklearn.feature_extraction.text.TfidfVectorizer')
    def test_extract_keywords(self, mock_tfidf):
        """Test keyword extraction."""
        # Mock TfidfVectorizer
        mock_vectorizer = MagicMock()
        mock_vectorizer.fit_transform.return_value = MagicMock()
        mock_vectorizer.get_feature_names_out.return_value = ["hello", "world", "test"]
        mock_tfidf.return_value = mock_vectorizer
        
        config = {"num_topics": 2, "min_topic_size": 1}
        analyzer = TopicAnalyzer(config)
        
        texts = ["Hello world", "This is a test", "Hello test"]
        keywords = analyzer.extract_keywords(texts)
        
        assert isinstance(keywords, list)
        assert len(keywords) == 3  # Should have 3 keywords
        assert "hello" in keywords
        assert "world" in keywords
        assert "test" in keywords
    
    @patch('sklearn.cluster.KMeans')
    @patch('sklearn.feature_extraction.text.TfidfVectorizer')
    def test_cluster_topics(self, mock_tfidf, mock_kmeans):
        """Test topic clustering."""
        # Mock TfidfVectorizer
        mock_vectorizer = MagicMock()
        mock_matrix = MagicMock()
        mock_vectorizer.fit_transform.return_value = mock_matrix
        mock_tfidf.return_value = mock_vectorizer
        
        # Mock KMeans
        mock_kmeans_instance = MagicMock()
        mock_kmeans_instance.labels_ = [0, 1, 0]  # 3 documents, 2 clusters
        mock_kmeans.return_value = mock_kmeans_instance
        
        config = {"num_topics": 2, "min_topic_size": 1}
        analyzer = TopicAnalyzer(config)
        
        texts = ["Hello world", "This is a test", "Hello test"]
        clusters = analyzer.cluster_topics(texts)
        
        assert isinstance(clusters, list)
        assert len(clusters) == 3  # Should have 3 documents
        assert clusters[0] == 0
        assert clusters[1] == 1
        assert clusters[2] == 0
    
    @patch('sklearn.decomposition.LatentDirichletAllocation')
    @patch('sklearn.feature_extraction.text.CountVectorizer')
    def test_extract_topics(self, mock_count_vec, mock_lda):
        """Test topic extraction."""
        # Mock CountVectorizer
        mock_vectorizer = MagicMock()
        mock_matrix = MagicMock()
        mock_vectorizer.fit_transform.return_value = mock_matrix
        mock_vectorizer.get_feature_names_out.return_value = ["hello", "world", "test"]
        mock_count_vec.return_value = mock_vectorizer
        
        # Mock LDA
        mock_lda_instance = MagicMock()
        mock_lda_instance.transform.return_value = [
            [0.8, 0.2],  # Document 1: 80% Topic 1, 20% Topic 2
            [0.3, 0.7],  # Document 2: 30% Topic 1, 70% Topic 2
            [0.6, 0.4]   # Document 3: 60% Topic 1, 40% Topic 2
        ]
        # Topic-word distribution
        mock_lda_instance.components_ = [
            [0.5, 0.3, 0.2],  # Topic 1: hello (0.5), world (0.3), test (0.2)
            [0.2, 0.2, 0.6]   # Topic 2: hello (0.2), world (0.2), test (0.6)
        ]
        mock_lda.return_value = mock_lda_instance
        
        config = {"num_topics": 2, "min_topic_size": 1}
        analyzer = TopicAnalyzer(config)
        
        texts = ["Hello world", "This is a test", "Hello test"]
        topics = analyzer.extract_topics(texts)
        
        assert isinstance(topics, dict)
        assert "topic_distribution" in topics
        assert "topic_keywords" in topics
        assert len(topics["topic_distribution"]) == 3  # 3 documents
        assert len(topics["topic_keywords"]) == 2  # 2 topics
    
    def test_analyze_topic_evolution(self):
        """Test topic evolution analysis."""
        config = {"num_topics": 2, "min_topic_size": 1}
        analyzer = TopicAnalyzer(config)
        
        # Sample data with timestamps
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello world",
                "analysis": {"normalized": "hello world"}
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-02T14:00:00",
                "content": "This is a test",
                "analysis": {"normalized": "this is a test"}
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-03T09:00:00",
                "content": "Hello test",
                "analysis": {"normalized": "hello test"}
            }
        ]
        
        # Mock the extract_topics method
        with patch.object(TopicAnalyzer, 'extract_topics') as mock_extract_topics:
            mock_extract_topics.return_value = {
                "topic_distribution": [
                    [0.8, 0.2],  # Document 1: 80% Topic 1, 20% Topic 2
                    [0.3, 0.7],  # Document 2: 30% Topic 1, 70% Topic 2
                    [0.6, 0.4]   # Document 3: 60% Topic 1, 40% Topic 2
                ],
                "topic_keywords": [
                    ["hello", "world"],  # Topic 1 keywords
                    ["test", "is"]       # Topic 2 keywords
                ]
            }
            
            evolution = analyzer.analyze_topic_evolution(data)
            
            assert isinstance(evolution, dict)
            assert "2023-01-01" in evolution
            assert "2023-01-02" in evolution
            assert "2023-01-03" in evolution
    
    def test_analyze(self):
        """Test the analyze method."""
        config = {"num_topics": 2, "min_topic_size": 1}
        analyzer = TopicAnalyzer(config)
        
        # Sample data
        data = [
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-01T10:00:00",
                "content": "Hello world",
                "analysis": {"normalized": "hello world"}
            },
            {
                "type": "email",
                "sender": "sender@example.com",
                "recipient": "recipient@example.com",
                "timestamp": "2023-01-02T14:00:00",
                "content": "This is a test",
                "analysis": {"normalized": "this is a test"}
            },
            {
                "type": "message",
                "sender": "Friend",
                "recipient": "User",
                "timestamp": "2023-01-03T09:00:00",
                "content": "Hello test",
                "analysis": {"normalized": "hello test"}
            }
        ]
        
        # Mock several methods to avoid actual computation
        with patch.object(TopicAnalyzer, 'extract_keywords') as mock_extract_keywords, \
             patch.object(TopicAnalyzer, 'cluster_topics') as mock_cluster_topics, \
             patch.object(TopicAnalyzer, 'extract_topics') as mock_extract_topics, \
             patch.object(TopicAnalyzer, 'analyze_topic_evolution') as mock_analyze_evolution:
            
            mock_extract_keywords.return_value = ["hello", "world", "test"]
            mock_cluster_topics.return_value = [0, 1, 0]
            mock_extract_topics.return_value = {
                "topic_distribution": [
                    [0.8, 0.2],  # Document 1: 80% Topic 1, 20% Topic 2
                    [0.3, 0.7],  # Document 2: 30% Topic 1, 70% Topic 2
                    [0.6, 0.4]   # Document 3: 60% Topic 1, 40% Topic 2
                ],
                "topic_keywords": [
                    ["hello", "world"],  # Topic 1 keywords
                    ["test", "is"]       # Topic 2 keywords
                ]
            }
            mock_analyze_evolution.return_value = {
                "2023-01-01": [0.8, 0.2],
                "2023-01-02": [0.3, 0.7],
                "2023-01-03": [0.6, 0.4]
            }
            
            results = analyzer.analyze(data)
            
            assert "keywords" in results
            assert "clusters" in results
            assert "topics" in results
            assert "topic_evolution" in results