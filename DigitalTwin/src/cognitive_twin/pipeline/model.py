"""
Cognitive-Twin Omega - Cognitive Model Building System

This module provides comprehensive cognitive model building capabilities for Cognitive-Twin Omega,
enabling the system to construct a sophisticated model of a person's thought patterns,
beliefs, values, and decision-making processes based on analyzed data.
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from collections import defaultdict

import pandas as pd
import numpy as np
from tqdm import tqdm
import networkx as nx
from sklearn.cluster import DBSCAN
import torch

from cognitive_twin.core.utils import ensure_dir
from cognitive_twin.models.cognitive import CognitiveModel
from cognitive_twin.core.knowledge_graph import KnowledgeGraph

# Initialize logger
logger = logging.getLogger(__name__)

class ModelBuilder:
    """
    Manages the building of cognitive models for Cognitive-Twin Omega.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model builder.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.processed_dir = Path(config['paths']['processed'])
        self.models_dir = Path(config['paths']['models'])
        
        # Ensure directories exist
        ensure_dir(self.processed_dir)
        ensure_dir(self.models_dir)
        
        # Initialize stats
        self.stats = {
            'total_items': 0,
            'processed_items': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def build_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> CognitiveModel:
        """
        Build a cognitive model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Cognitive model
        """
        logger.info("Building cognitive model")
        
        # Initialize cognitive model
        cognitive_model = CognitiveModel(self.config)
        
        try:
            # Build the model from data
            cognitive_model.build_from_data(processed_data, analysis_results)
            
            # Save the model
            model_path = self.models_dir / 'cognitive'
            cognitive_model.save(model_path)
            logger.info(f"Saved cognitive model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building cognitive model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return cognitive_model
    
    def build_knowledge_graph(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> KnowledgeGraph:
        """
        Build a knowledge graph from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Knowledge graph
        """
        logger.info("Building knowledge graph")
        
        # Initialize knowledge graph
        knowledge_graph = KnowledgeGraph(self.config)
        
        try:
            # Build the knowledge graph from data
            knowledge_graph.build_from_data(processed_data, analysis_results)
            
            # Save the knowledge graph
            graph_path = self.models_dir / 'knowledge_graph'
            knowledge_graph.save(graph_path)
            logger.info(f"Saved knowledge graph to {graph_path}")
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return knowledge_graph
    
    def build_personality_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a personality model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Personality model
        """
        logger.info("Building personality model")
        
        personality_model = {}
        
        try:
            # Extract personality indicators from analysis results
            if 'personality_indicators' in analysis_results:
                personality_indicators = analysis_results['personality_indicators']
                
                # Extract Big Five traits
                if 'big_five' in personality_indicators:
                    personality_model['big_five'] = personality_indicators['big_five']
                
                # Extract cognitive patterns
                if 'cognitive_patterns' in personality_indicators:
                    personality_model['cognitive_patterns'] = personality_indicators['cognitive_patterns']
                
                # Extract emotional patterns
                if 'emotional_patterns' in personality_indicators:
                    personality_model['emotional_patterns'] = personality_indicators['emotional_patterns']
            
            # Extract communication style from analysis results
            if 'communication_style' in analysis_results:
                personality_model['communication_style'] = analysis_results['communication_style']
            
            # Extract values from analysis results
            if 'values' in analysis_results:
                personality_model['values'] = analysis_results['values']
            
            # Save the personality model
            model_path = self.models_dir / 'personality_model.json'
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(personality_model, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved personality model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building personality model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return personality_model
    
    def build_relationship_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a relationship model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Relationship model
        """
        logger.info("Building relationship model")
        
        relationship_model = {}
        
        try:
            # Extract entities from analysis results
            if 'entities' in analysis_results and 'people' in analysis_results['entities']:
                people = analysis_results['entities']['people']
                relationship_model['people'] = people
            
            # Extract relationships from analysis results
            if 'relationships' in analysis_results:
                relationship_model['relationships'] = analysis_results['relationships']
            
            # Extract relationship dynamics from text message analysis
            if 'text_messages' in analysis_results and 'relationship_analysis' in analysis_results['text_messages']:
                relationship_analysis = analysis_results['text_messages']['relationship_analysis']
                
                # Extract conversation network
                if 'conversation_network' in relationship_analysis:
                    relationship_model['conversation_network'] = relationship_analysis['conversation_network']
                
                # Extract conversation stats
                if 'conversation_stats' in relationship_analysis:
                    relationship_model['conversation_stats'] = relationship_analysis['conversation_stats']
            
            # Save the relationship model
            model_path = self.models_dir / 'relationship_model.json'
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(relationship_model, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved relationship model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building relationship model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return relationship_model
    
    def build_temporal_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a temporal model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Temporal model
        """
        logger.info("Building temporal model")
        
        temporal_model = {}
        
        try:
            # Extract temporal patterns from text message analysis
            if 'text_messages' in analysis_results and 'temporal_analysis' in analysis_results['text_messages']:
                temporal_analysis = analysis_results['text_messages']['temporal_analysis']
                
                # Extract activity patterns
                if 'activity_patterns' in temporal_analysis:
                    temporal_model['activity_patterns'] = temporal_analysis['activity_patterns']
                
                # Extract time series
                if 'time_series' in temporal_analysis:
                    temporal_model['time_series'] = temporal_analysis['time_series']
                
                # Extract active periods
                if 'active_periods' in temporal_analysis:
                    temporal_model['active_periods'] = temporal_analysis['active_periods']
                
                # Extract inactive periods
                if 'inactive_periods' in temporal_analysis:
                    temporal_model['inactive_periods'] = temporal_analysis['inactive_periods']
                
                # Extract response times
                if 'response_times' in temporal_analysis:
                    temporal_model['response_times'] = temporal_analysis['response_times']
            
            # Extract sentiment over time
            if 'text_messages' in analysis_results and 'sentiment_analysis' in analysis_results['text_messages']:
                sentiment_analysis = analysis_results['text_messages']['sentiment_analysis']
                
                if 'sentiment_over_time' in sentiment_analysis:
                    temporal_model['sentiment_over_time'] = sentiment_analysis['sentiment_over_time']
            
            # Extract cross-source temporal patterns
            if 'cross_source' in analysis_results and 'temporal_patterns' in analysis_results['cross_source']:
                temporal_model['cross_source_patterns'] = analysis_results['cross_source']['temporal_patterns']
            
            # Save the temporal model
            model_path = self.models_dir / 'temporal_model.json'
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(temporal_model, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved temporal model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building temporal model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return temporal_model
    
    def build_topic_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a topic model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Topic model
        """
        logger.info("Building topic model")
        
        topic_model = {}
        
        try:
            # Extract topics from text message analysis
            if 'text_messages' in analysis_results and 'topic_modeling' in analysis_results['text_messages']:
                topic_modeling = analysis_results['text_messages']['topic_modeling']
                
                # Extract LDA topics
                if 'lda_topics' in topic_modeling:
                    topic_model['lda_topics'] = topic_modeling['lda_topics']
                
                # Extract BERTopic topics
                if 'bertopics' in topic_modeling:
                    topic_model['bertopics'] = topic_modeling['bertopics']
                
                # Extract topic distribution
                if 'topic_distribution' in topic_modeling:
                    topic_model['topic_distribution'] = topic_modeling['topic_distribution']
            
            # Extract concepts from analysis results
            if 'concepts' in analysis_results:
                topic_model['concepts'] = analysis_results['concepts']
            
            # Save the topic model
            model_path = self.models_dir / 'topic_model.json'
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(topic_model, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved topic model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building topic model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return topic_model
    
    def build_language_model(self, processed_data: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a language model from processed data and analysis results.
        
        Args:
            processed_data: Dictionary of processed data
            analysis_results: Dictionary of analysis results
            
        Returns:
            Language model
        """
        logger.info("Building language model")
        
        language_model = {}
        
        try:
            # Extract linguistic features from text message analysis
            if 'text_messages' in analysis_results and 'content_analysis' in analysis_results['text_messages']:
                content_analysis = analysis_results['text_messages']['content_analysis']
                
                # Extract word frequency
                if 'word_frequency' in content_analysis:
                    language_model['word_frequency'] = content_analysis['word_frequency']
                
                # Extract n-grams
                if 'ngrams' in content_analysis:
                    language_model['ngrams'] = content_analysis['ngrams']
                
                # Extract vocabulary richness
                if 'vocabulary_richness' in content_analysis:
                    language_model['vocabulary_richness'] = content_analysis['vocabulary_richness']
                
                # Extract linguistic features
                if 'linguistic_features' in content_analysis:
                    language_model['linguistic_features'] = content_analysis['linguistic_features']
                
                # Extract subject-specific language
                if 'subject_word_frequency' in content_analysis:
                    language_model['subject_word_frequency'] = content_analysis['subject_word_frequency']
                
                # Extract distinctive words
                if 'distinctive_words' in content_analysis:
                    language_model['distinctive_words'] = content_analysis['distinctive_words']
            
            # Save the language model
            model_path = self.models_dir / 'language_model.json'
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(language_model, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved language model to {model_path}")
            
        except Exception as e:
            logger.error(f"Error building language model: {str(e)}", exc_info=True)
            self.stats['errors'] += 1
        
        return language_model
    
    def build_integrated_model(self, cognitive_model: CognitiveModel, knowledge_graph: KnowledgeGraph, 
                              personality_model: Dict[str, Any], relationship_model: Dict[str, Any],
                              temporal_model: Dict[str, Any], topic_model: Dict[str, Any],
                              language_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build an integrated model combining all component models.
        
        Args:
            cognitive_model: Cognitive model
            knowledge_graph: Knowledge graph
            personality_model: Personality model
            relationship_model: Relationship model
            temporal_model: Temporal model
            topic_model: Topic model
            language_model: Language model
            
        Returns:
            Integrated model
        """
        logger.info("Building integrated model")
        
        integrated_model = {
            'metadata': {
                'version': '1.0.0',
                'created': pd.Timestamp.now().isoformat(),
                'components': [
                    'cognitive_model',
                    'knowledge_graph',
                    'personality_model',
                    'relationship_model',
                    'temporal_model',
                    'topic_model',
                    'language_model'
                ]
            },
            'summary': {
                'personality': self._generate_personality_summary(personality_model),
                'relationships': self._generate_relationship_summary(relationship_model),
                'communication': self._generate_communication_summary(personality_model, language_model),
                'interests': self._generate_interest_summary(topic_model),
                'values': self._generate_value_summary(personality_model)
            }
        }
        
        # Save the integrated model
        model_path = self.models_dir / 'integrated_model.json'
        with open(model_path, 'w', encoding='utf-8') as f:
            json.dump(integrated_model, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved integrated model to {model_path}")
        
        return integrated_model
    
    def _generate_personality_summary(self, personality_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the personality model.
        
        Args:
            personality_model: Personality model
            
        Returns:
            Personality summary
        """
        summary = {}
        
        # Extract Big Five traits
        if 'big_five' in personality_model:
            big_five = personality_model['big_five']
            summary['big_five'] = {trait: data['score'] for trait, data in big_five.items()}
        
        # Extract dominant cognitive patterns
        if 'cognitive_patterns' in personality_model:
            cognitive_patterns = personality_model['cognitive_patterns']
            summary['dominant_cognitive_patterns'] = sorted(
                [(pattern, data['score']) for pattern, data in cognitive_patterns.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
        
        # Extract dominant emotional patterns
        if 'emotional_patterns' in personality_model:
            emotional_patterns = personality_model['emotional_patterns']
            summary['dominant_emotional_patterns'] = sorted(
                [(pattern, data['score']) for pattern, data in emotional_patterns.items()],
                key=lambda x: x[1],
                reverse=True
            )[:3]
        
        return summary
    
    def _generate_relationship_summary(self, relationship_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the relationship model.
        
        Args:
            relationship_model: Relationship model
            
        Returns:
            Relationship summary
        """
        summary = {}
        
        # Extract key relationships
        if 'conversation_stats' in relationship_model:
            conversation_stats = relationship_model['conversation_stats']
            
            # Sort conversations by message count
            sorted_conversations = sorted(
                conversation_stats.items(),
                key=lambda x: x[1]['message_count'],
                reverse=True
            )
            
            # Extract top conversations
            top_conversations = []
            for conversation, stats in sorted_conversations[:10]:
                top_conversations.append({
                    'name': conversation,
                    'message_count': stats['message_count'],
                    'duration_days': stats.get('duration_days', 0)
                })
            
            summary['top_relationships'] = top_conversations
        
        # Extract network metrics
        if 'conversation_network' in relationship_model:
            network = relationship_model['conversation_network']
            
            if 'central_figures' in network:
                summary['central_figures'] = list(network['central_figures'].keys())[:5]
        
        return summary
    
    def _generate_communication_summary(self, personality_model: Dict[str, Any], language_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of communication patterns.
        
        Args:
            personality_model: Personality model
            language_model: Language model
            
        Returns:
            Communication summary
        """
        summary = {}
        
        # Extract communication style
        if 'communication_style' in personality_model:
            communication_style = personality_model['communication_style']
            
            style_scores = {}
            for dimension, data in communication_style.items():
                if isinstance(data, dict) and 'score' in data:
                    style_scores[dimension] = data['score']
            
            summary['style_dimensions'] = style_scores
        
        # Extract vocabulary richness
        if 'vocabulary_richness' in language_model:
            vocabulary = language_model['vocabulary_richness']
            summary['vocabulary_richness'] = {
                'type_token_ratio': vocabulary.get('type_token_ratio', 0),
                'unique_words': vocabulary.get('unique_words', 0)
            }
        
        # Extract distinctive words
        if 'distinctive_words' in language_model:
            distinctive_words = language_model['distinctive_words']
            if 'text1_distinctive' in distinctive_words:
                summary['distinctive_words'] = distinctive_words['text1_distinctive'][:10]
        
        return summary
    
    def _generate_interest_summary(self, topic_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of interests based on topics.
        
        Args:
            topic_model: Topic model
            
        Returns:
            Interest summary
        """
        summary = {}
        
        # Extract topics
        topics = []
        
        if 'lda_topics' in topic_model:
            lda_topics = topic_model['lda_topics']
            for topic in lda_topics:
                topics.append({
                    'keywords': topic['top_words'][:5],
                    'weight': topic['weight']
                })
        
        elif 'bertopics' in topic_model:
            bertopics = topic_model['bertopics']
            for topic in bertopics:
                topics.append({
                    'keywords': topic['top_words'][:5],
                    'weight': topic['weight']
                })
        
        # Sort topics by weight
        sorted_topics = sorted(topics, key=lambda x: x['weight'], reverse=True)
        
        # Extract top topics
        summary['top_topics'] = sorted_topics[:5]
        
        return summary
    
    def _generate_value_summary(self, personality_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of values.
        
        Args:
            personality_model: Personality model
            
        Returns:
            Value summary
        """
        summary = {}
        
        # Extract core values
        if 'values' in personality_model and 'core_values' in personality_model['values']:
            core_values = personality_model['values']['core_values']
            
            # Sort values by score
            sorted_values = sorted(
                [(value, data['score']) for value, data in core_values.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Extract top values
            summary['top_values'] = sorted_values[:5]
        
        # Extract moral foundations
        if 'values' in personality_model and 'moral_foundations' in personality_model['values']:
            moral_foundations = personality_model['values']['moral_foundations']
            
            # Sort foundations by score
            sorted_foundations = sorted(
                [(foundation, data['score']) for foundation, data in moral_foundations.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Extract top foundations
            summary['moral_foundations'] = sorted_foundations
        
        return summary


def build_model(config: Dict[str, Any], analysis_results: Dict[str, Any]) -> CognitiveModel:
    """
    Build a cognitive model from analysis results.
    
    Args:
        config: Configuration dictionary
        analysis_results: Dictionary of analysis results
        
    Returns:
        Cognitive model
    """
    # Create model builder
    model_builder = ModelBuilder(config)
    
    # Build component models
    cognitive_model = model_builder.build_model({}, analysis_results)
    knowledge_graph = model_builder.build_knowledge_graph({}, analysis_results)
    personality_model = model_builder.build_personality_model({}, analysis_results)
    relationship_model = model_builder.build_relationship_model({}, analysis_results)
    temporal_model = model_builder.build_temporal_model({}, analysis_results)
    topic_model = model_builder.build_topic_model({}, analysis_results)
    language_model = model_builder.build_language_model({}, analysis_results)
    
    # Build integrated model
    integrated_model = model_builder.build_integrated_model(
        cognitive_model,
        knowledge_graph,
        personality_model,
        relationship_model,
        temporal_model,
        topic_model,
        language_model
    )
    
    return cognitive_model