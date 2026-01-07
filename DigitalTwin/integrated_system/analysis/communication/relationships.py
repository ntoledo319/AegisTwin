"""
Communication relationship analysis module.

This module provides functionality for analyzing relationships in communication data,
including contact frequency, sentiment, and relationship strength.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import networkx as nx

logger = logging.getLogger(__name__)

class RelationshipAnalyzer:
    """Analyzer for communication relationships."""
    
    def __init__(self):
        """Initialize the relationship analyzer."""
        self.relationships = {}
        self.graph = nx.Graph()
        
    async def analyze(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationships in messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary of relationship analysis results
        """
        logger.info(f"Analyzing relationships in {len(messages)} messages")
        
        if not messages:
            return {"relationships": {}, "error": "No messages to analyze"}
        
        # Convert to DataFrame for easier analysis
        try:
            df = pd.DataFrame(messages)
            
            # Ensure required columns exist
            required_columns = ['sender', 'recipient', 'timestamp', 'content']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {"relationships": {}, "error": f"Messages missing required fields: {missing_columns}"}
            
            # Convert timestamps to datetime objects if they're not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Analyze contact frequency
            contact_frequency = self._analyze_contact_frequency(df)
            
            # Analyze sentiment if possible
            sentiment_analysis = self._analyze_sentiment(df)
            
            # Analyze relationship strength
            relationship_strength = self._analyze_relationship_strength(df)
            
            # Build relationship graph
            self._build_relationship_graph(df)
            
            # Analyze relationship network
            network_analysis = self._analyze_network()
            
            # Combine all relationship analyses
            all_relationships = {
                "contact_frequency": contact_frequency,
                "sentiment": sentiment_analysis,
                "strength": relationship_strength,
                "network": network_analysis
            }
            
            # Store relationships
            self.relationships = all_relationships
            
            return {"relationships": all_relationships}
            
        except Exception as e:
            logger.error(f"Error analyzing relationships: {str(e)}")
            return {"relationships": {}, "error": str(e)}
    
    def _analyze_contact_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze contact frequency between individuals.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of contact frequency metrics
        """
        # Create pairs of sender-recipient
        df['pair'] = df.apply(lambda row: tuple(sorted([row['sender'], row['recipient']])), axis=1)
        
        # Count messages per pair
        pair_counts = df.groupby('pair').size().to_dict()
        
        # Calculate messages per day for each pair
        df['date'] = df['timestamp'].dt.date
        pair_date_counts = df.groupby(['pair', 'date']).size().reset_index()
        pair_date_counts.columns = ['pair', 'date', 'count']
        
        # Calculate average messages per day for each pair
        avg_messages_per_day = pair_date_counts.groupby('pair')['count'].mean().to_dict()
        
        # Calculate days since last contact for each pair
        latest_date = df['date'].max()
        latest_contact = df.groupby('pair')['date'].max().to_dict()
        days_since_contact = {pair: (latest_date - date).days for pair, date in latest_contact.items()}
        
        # Calculate contact consistency (standard deviation of days between contacts)
        contact_consistency = {}
        for pair in pair_counts.keys():
            pair_df = df[df['pair'] == pair].sort_values('date')
            pair_df['days_between'] = pair_df['date'].diff().dt.days
            consistency = pair_df['days_between'].std()
            contact_consistency[pair] = float(consistency) if not pd.isna(consistency) else None
        
        return {
            "message_counts": pair_counts,
            "avg_messages_per_day": avg_messages_per_day,
            "days_since_contact": days_since_contact,
            "contact_consistency": contact_consistency
        }
    
    def _analyze_sentiment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze sentiment in communications between individuals.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of sentiment metrics
        """
        # Try to use a sentiment analysis library if available
        try:
            from textblob import TextBlob
            
            # Calculate sentiment for each message
            df['sentiment'] = df['content'].apply(lambda x: TextBlob(str(x)).sentiment.polarity if x else 0)
            
            # Calculate average sentiment for each sender-recipient pair
            df['pair'] = df.apply(lambda row: tuple(sorted([row['sender'], row['recipient']])), axis=1)
            avg_sentiment = df.groupby('pair')['sentiment'].mean().to_dict()
            
            # Calculate sentiment variance for each pair
            sentiment_variance = df.groupby('pair')['sentiment'].var().to_dict()
            
            # Calculate sentiment trend over time
            sentiment_trends = {}
            for pair in avg_sentiment.keys():
                pair_df = df[df['pair'] == pair].sort_values('timestamp')
                
                # If we have enough data points, calculate trend
                if len(pair_df) >= 5:
                    # Create time-based index
                    pair_df['time_index'] = range(len(pair_df))
                    
                    # Calculate correlation between time and sentiment
                    correlation = pair_df['time_index'].corr(pair_df['sentiment'])
                    sentiment_trends[pair] = float(correlation) if not pd.isna(correlation) else 0
                else:
                    sentiment_trends[pair] = None
            
            return {
                "avg_sentiment": avg_sentiment,
                "sentiment_variance": sentiment_variance,
                "sentiment_trends": sentiment_trends
            }
            
        except ImportError:
            logger.warning("TextBlob not available for sentiment analysis")
            return {"error": "Sentiment analysis library not available"}
    
    def _analyze_relationship_strength(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze relationship strength between individuals.
        
        Args:
            df: DataFrame of messages
            
        Returns:
            Dictionary of relationship strength metrics
        """
        # Create pairs of sender-recipient
        df['pair'] = df.apply(lambda row: tuple(sorted([row['sender'], row['recipient']])), axis=1)
        
        # Calculate message count factor (normalized by max count)
        pair_counts = df.groupby('pair').size()
        max_count = pair_counts.max()
        message_count_factor = (pair_counts / max_count).to_dict() if max_count > 0 else {}
        
        # Calculate recency factor (more recent = stronger)
        latest_date = df['timestamp'].max().date()
        latest_contact = df.groupby('pair')['timestamp'].max()
        latest_contact_date = latest_contact.dt.date
        days_since = (latest_date - latest_contact_date).dt.days
        max_days = days_since.max()
        recency_factor = (1 - (days_since / max_days)).to_dict() if max_days > 0 else {}
        
        # Calculate response rate factor
        response_rates = {}
        for pair in pair_counts.index:
            person1, person2 = pair
            
            # Get messages in this conversation
            conversation = df[df['pair'] == pair].sort_values('timestamp')
            
            # Calculate response rate for person1
            person1_messages = conversation[conversation['sender'] == person1]
            responses_to_person1 = 0
            
            for _, msg in person1_messages.iterrows():
                # Find messages that came after this one
                later_messages = conversation[(conversation['timestamp'] > msg['timestamp']) & 
                                             (conversation['sender'] == person2)]
                
                # If there's at least one later message within a reasonable time (1 day), count it as a response
                if len(later_messages[later_messages['timestamp'] - msg['timestamp'] <= timedelta(days=1)]) > 0:
                    responses_to_person1 += 1
            
            # Calculate response rate
            person1_response_rate = responses_to_person1 / len(person1_messages) if len(person1_messages) > 0 else 0
            
            # Calculate response rate for person2
            person2_messages = conversation[conversation['sender'] == person2]
            responses_to_person2 = 0
            
            for _, msg in person2_messages.iterrows():
                # Find messages that came after this one
                later_messages = conversation[(conversation['timestamp'] > msg['timestamp']) & 
                                             (conversation['sender'] == person1)]
                
                # If there's at least one later message within a reasonable time (1 day), count it as a response
                if len(later_messages[later_messages['timestamp'] - msg['timestamp'] <= timedelta(days=1)]) > 0:
                    responses_to_person2 += 1
            
            # Calculate response rate
            person2_response_rate = responses_to_person2 / len(person2_messages) if len(person2_messages) > 0 else 0
            
            # Average response rate for the pair
            avg_response_rate = (person1_response_rate + person2_response_rate) / 2
            response_rates[pair] = avg_response_rate
        
        # Calculate message length factor
        df['message_length'] = df['content'].apply(lambda x: len(str(x)) if x else 0)
        avg_message_length = df.groupby('pair')['message_length'].mean()
        max_length = avg_message_length.max()
        message_length_factor = (avg_message_length / max_length).to_dict() if max_length > 0 else {}
        
        # Calculate overall relationship strength (weighted average of factors)
        relationship_strength = {}
        for pair in pair_counts.index:
            # Get factors with weights
            factors = [
                (message_count_factor.get(pair, 0), 0.4),  # 40% weight on message count
                (recency_factor.get(pair, 0), 0.3),        # 30% weight on recency
                (response_rates.get(pair, 0), 0.2),        # 20% weight on response rate
                (message_length_factor.get(pair, 0), 0.1)  # 10% weight on message length
            ]
            
            # Calculate weighted average
            strength = sum(factor * weight for factor, weight in factors)
            relationship_strength[pair] = strength
        
        return {
            "message_count_factor": message_count_factor,
            "recency_factor": recency_factor,
            "response_rates": response_rates,
            "message_length_factor": message_length_factor,
            "relationship_strength": relationship_strength
        }
    
    def _build_relationship_graph(self, df: pd.DataFrame) -> None:
        """
        Build a graph representing relationships.
        
        Args:
            df: DataFrame of messages
        """
        # Create a new graph
        self.graph = nx.Graph()
        
        # Add nodes (people)
        senders = set(df['sender'])
        recipients = set(df['recipient'])
        all_people = senders.union(recipients)
        
        for person in all_people:
            self.graph.add_node(person)
        
        # Create pairs of sender-recipient
        df['pair'] = df.apply(lambda row: tuple(sorted([row['sender'], row['recipient']])), axis=1)
        
        # Count messages per pair
        pair_counts = df.groupby('pair').size().to_dict()
        
        # Add edges with weights based on message count
        for pair, count in pair_counts.items():
            person1, person2 = pair
            self.graph.add_edge(person1, person2, weight=count)
    
    def _analyze_network(self) -> Dict[str, Any]:
        """
        Analyze the relationship network.
        
        Returns:
            Dictionary of network metrics
        """
        if not self.graph.nodes():
            return {"error": "No relationship graph available"}
        
        try:
            # Calculate centrality measures
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            closeness_centrality = nx.closeness_centrality(self.graph)
            
            # Calculate clustering coefficient
            clustering = nx.clustering(self.graph)
            avg_clustering = nx.average_clustering(self.graph)
            
            # Identify communities
            try:
                from community import best_partition
                communities = best_partition(self.graph)
            except ImportError:
                # Fallback to connected components
                communities = {}
                for i, component in enumerate(nx.connected_components(self.graph)):
                    for node in component:
                        communities[node] = i
            
            # Calculate network density
            density = nx.density(self.graph)
            
            return {
                "degree_centrality": degree_centrality,
                "betweenness_centrality": betweenness_centrality,
                "closeness_centrality": closeness_centrality,
                "clustering": clustering,
                "avg_clustering": avg_clustering,
                "communities": communities,
                "density": density
            }
            
        except Exception as e:
            logger.error(f"Error analyzing network: {str(e)}")
            return {"error": str(e)}
    
    def get_strongest_relationships(self, top_n: int = 5) -> List[Tuple[Tuple[str, str], float]]:
        """
        Get the strongest relationships.
        
        Args:
            top_n: Number of top relationships to return
            
        Returns:
            List of (pair, strength) tuples
        """
        if not self.relationships or 'strength' not in self.relationships:
            return []
        
        # Get relationship strengths
        strengths = self.relationships['strength'].get('relationship_strength', {})
        
        # Sort by strength (descending)
        sorted_relationships = sorted(strengths.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N
        return sorted_relationships[:top_n]
    
    def get_relationship_graph(self) -> nx.Graph:
        """
        Get the relationship graph.
        
        Returns:
            NetworkX graph of relationships
        """
        return self.graph