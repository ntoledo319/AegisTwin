"""
Relationship Analyzer for CogniLink

This module analyzes communication data to identify and characterize
relationships between individuals in the communication network.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import statistics
from collections import Counter, defaultdict
import networkx as nx
import json
import math

from cognilink.core.comm_graph import CommunicationGraph

logger = logging.getLogger(__name__)

class RelationshipAnalyzer:
    """
    Analyzer for relationships in communication data.
    
    This class identifies and characterizes relationships between individuals
    based on their communication patterns, frequency, and content.
    """
    
    def __init__(self, comm_graph: CommunicationGraph = None):
        """
        Initialize the relationship analyzer.
        
        Args:
            comm_graph: Optional communication graph to analyze
        """
        self.comm_graph = comm_graph or CommunicationGraph()
    
    def set_graph(self, comm_graph: CommunicationGraph) -> None:
        """
        Set the communication graph to analyze.
        
        Args:
            comm_graph: Communication graph to analyze
        """
        self.comm_graph = comm_graph
    
    def identify_key_relationships(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Identify the most significant relationships based on communication frequency.
        
        Args:
            top_n: Number of top relationships to return
            
        Returns:
            List of dictionaries describing key relationships
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for relationship analysis")
            return []
        
        # Calculate relationship strength based on communication frequency
        relationships = []
        
        for source, target, data in self.comm_graph.graph.edges(data=True):
            # Skip self-loops
            if source == target:
                continue
            
            # Get communication count
            count = data.get('count', 1)
            
            # Check if there's a reciprocal relationship
            reciprocal = self.comm_graph.graph.has_edge(target, source)
            reciprocal_count = 0
            
            if reciprocal:
                reciprocal_data = self.comm_graph.graph[target][source]
                reciprocal_count = reciprocal_data.get('count', 1)
            
            # Calculate relationship strength
            strength = count + reciprocal_count
            
            # Calculate balance (how reciprocal the relationship is)
            if strength > 0:
                balance = min(count, reciprocal_count) / strength
            else:
                balance = 0
            
            # Get time span of relationship
            time_span_days = 0
            try:
                first_comm = datetime.fromisoformat(data.get('first_comm'))
                last_comm = datetime.fromisoformat(data.get('last_comm'))
                time_span_days = (last_comm - first_comm).days + 1
            except (ValueError, TypeError, KeyError):
                pass
            
            # Create relationship entry
            relationship = {
                'person1': source,
                'person2': target,
                'strength': strength,
                'balance': balance,
                'messages_sent': count,
                'messages_received': reciprocal_count,
                'time_span_days': time_span_days,
                'is_reciprocal': reciprocal
            }
            
            relationships.append(relationship)
        
        # Sort by strength and return top N
        relationships.sort(key=lambda x: x['strength'], reverse=True)
        return relationships[:top_n]
    
    def categorize_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize relationships based on communication patterns.
        
        Returns:
            Dictionary mapping relationship categories to lists of relationships
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for relationship categorization")
            return {
                'close': [],
                'regular': [],
                'occasional': [],
                'one_way': [],
                'dormant': []
            }
        
        # Categories
        categories = {
            'close': [],      # High frequency, reciprocal
            'regular': [],    # Medium frequency, reciprocal
            'occasional': [], # Low frequency, may be reciprocal
            'one_way': [],    # Significant imbalance in communication
            'dormant': []     # No recent communication
        }
        
        # Get all relationships
        relationships = []
        
        for source, target, data in self.comm_graph.graph.edges(data=True):
            # Skip self-loops
            if source == target:
                continue
            
            # Get communication count
            count = data.get('count', 1)
            
            # Check if there's a reciprocal relationship
            reciprocal = self.comm_graph.graph.has_edge(target, source)
            reciprocal_count = 0
            
            if reciprocal:
                reciprocal_data = self.comm_graph.graph[target][source]
                reciprocal_count = reciprocal_data.get('count', 1)
            
            # Calculate relationship strength and balance
            strength = count + reciprocal_count
            balance = min(count, reciprocal_count) / strength if strength > 0 else 0
            
            # Get time span and recency
            time_span_days = 0
            days_since_last_comm = 999999  # Large default value
            
            try:
                first_comm = datetime.fromisoformat(data.get('first_comm'))
                last_comm = datetime.fromisoformat(data.get('last_comm'))
                time_span_days = (last_comm - first_comm).days + 1
                days_since_last_comm = (datetime.now() - last_comm).days
            except (ValueError, TypeError, KeyError):
                pass
            
            # Create relationship entry
            relationship = {
                'person1': source,
                'person2': target,
                'strength': strength,
                'balance': balance,
                'messages_sent': count,
                'messages_received': reciprocal_count,
                'time_span_days': time_span_days,
                'days_since_last_comm': days_since_last_comm,
                'is_reciprocal': reciprocal
            }
            
            relationships.append(relationship)
        
        # Calculate statistics for categorization
        if relationships:
            strengths = [r['strength'] for r in relationships]
            median_strength = statistics.median(strengths)
            
            # Categorize each relationship
            for relationship in relationships:
                # One-way relationships
                if relationship['balance'] < 0.2:
                    categories['one_way'].append(relationship)
                    continue
                
                # Dormant relationships (no communication in 90+ days)
                if relationship['days_since_last_comm'] > 90:
                    categories['dormant'].append(relationship)
                    continue
                
                # Categorize by strength
                if relationship['strength'] >= median_strength * 2:
                    categories['close'].append(relationship)
                elif relationship['strength'] >= median_strength:
                    categories['regular'].append(relationship)
                else:
                    categories['occasional'].append(relationship)
        
        return categories
    
    def analyze_relationship_evolution(self) -> List[Dict[str, Any]]:
        """
        Analyze how relationships have evolved over time.
        
        Returns:
            List of dictionaries describing relationship evolution
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for relationship evolution analysis")
            return []
        
        # Get all relationships with sufficient data
        relationships = []
        
        for source, target, data in self.comm_graph.graph.edges(data=True):
            # Skip self-loops
            if source == target:
                continue
            
            # Skip if we don't have message IDs with timestamps
            if 'messages' not in data:
                continue
            
            # Get message IDs
            message_ids = data.get('messages', [])
            
            # Skip if too few messages
            if len(message_ids) < 5:
                continue
            
            # Check if there's a reciprocal relationship
            reciprocal = self.comm_graph.graph.has_edge(target, source)
            reciprocal_message_ids = []
            
            if reciprocal:
                reciprocal_data = self.comm_graph.graph[target][source]
                reciprocal_message_ids = reciprocal_data.get('messages', [])
            
            # Get time span
            try:
                first_comm = datetime.fromisoformat(data.get('first_comm'))
                last_comm = datetime.fromisoformat(data.get('last_comm'))
                time_span_days = (last_comm - first_comm).days + 1
                
                # Skip if time span is too short
                if time_span_days < 30:
                    continue
                
                # Create relationship entry
                relationship = {
                    'person1': source,
                    'person2': target,
                    'message_count': len(message_ids),
                    'reciprocal_message_count': len(reciprocal_message_ids),
                    'first_comm': first_comm.isoformat(),
                    'last_comm': last_comm.isoformat(),
                    'time_span_days': time_span_days,
                    'is_reciprocal': reciprocal
                }
                
                relationships.append(relationship)
            except (ValueError, TypeError, KeyError):
                continue
        
        # Analyze evolution for each relationship
        for relationship in relationships:
            # Calculate metrics for evolution analysis
            source = relationship['person1']
            target = relationship['person2']
            
            # Get message timestamps if available
            timestamps = []
            try:
                # This is a simplified approach - in a real implementation,
                # we would need to extract timestamps from the actual messages
                first_comm = datetime.fromisoformat(relationship['first_comm'])
                last_comm = datetime.fromisoformat(relationship['last_comm'])
                
                # Create some synthetic timestamps for demonstration
                message_count = relationship['message_count']
                
                if message_count > 0 and relationship['time_span_days'] > 0:
                    # Distribute messages evenly across the time span
                    interval = relationship['time_span_days'] / message_count
                    
                    for i in range(message_count):
                        ts = first_comm + timedelta(days=i * interval)
                        if ts <= last_comm:
                            timestamps.append(ts)
            except (ValueError, TypeError, KeyError):
                continue
            
            if not timestamps:
                continue
            
            # Divide time span into periods (e.g., quarters)
            periods = min(4, len(timestamps) // 5)  # At least 5 messages per period
            if periods < 2:
                continue
            
            # Sort timestamps
            timestamps.sort()
            
            # Split into periods
            period_size = len(timestamps) // periods
            period_messages = [timestamps[i:i+period_size] for i in range(0, len(timestamps), period_size)]
            
            # Calculate frequency for each period
            frequency_trend = []
            
            for i, period in enumerate(period_messages):
                if not period:
                    continue
                
                period_start = period[0]
                period_end = period[-1]
                period_days = (period_end - period_start).days + 1
                
                if period_days > 0:
                    frequency = len(period) / period_days
                    
                    frequency_trend.append({
                        'period': i + 1,
                        'start_date': period_start.isoformat(),
                        'end_date': period_end.isoformat(),
                        'message_count': len(period),
                        'frequency': frequency
                    })
            
            # Calculate trend
            if len(frequency_trend) >= 2:
                first_frequency = frequency_trend[0]['frequency']
                last_frequency = frequency_trend[-1]['frequency']
                
                if first_frequency > 0:
                    change_percent = (last_frequency - first_frequency) / first_frequency * 100
                else:
                    change_percent = float('inf') if last_frequency > 0 else 0
                
                # Determine trend
                if change_percent > 25:
                    trend = "increasing"
                elif change_percent < -25:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                relationship['frequency_trend'] = frequency_trend
                relationship['trend'] = trend
                relationship['change_percent'] = change_percent
            else:
                relationship['trend'] = "insufficient_data"
        
        # Filter out relationships without trend data
        return [r for r in relationships if 'trend' in r]
    
    def identify_relationship_groups(self) -> Dict[str, Any]:
        """
        Identify groups of related relationships.
        
        Returns:
            Dictionary with relationship group analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_nodes() < 3:
            logger.warning("Insufficient communication graph data for relationship group analysis")
            return {
                'groups': [],
                'central_figures': [],
                'isolated_figures': []
            }
        
        # Create undirected graph for group analysis
        undirected = self.comm_graph.graph.to_undirected()
        
        # Identify communities/groups
        groups = []
        
        try:
            # Try to use community detection algorithms
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(undirected)
                
                # Group by community
                communities = defaultdict(list)
                for node, community_id in partition.items():
                    communities[community_id].append(node)
                
                # Format groups
                for community_id, members in communities.items():
                    # Skip singleton groups
                    if len(members) < 2:
                        continue
                    
                    # Calculate group density
                    subgraph = undirected.subgraph(members)
                    n = len(members)
                    max_edges = n * (n - 1) / 2
                    density = subgraph.number_of_edges() / max_edges if max_edges > 0 else 0
                    
                    groups.append({
                        'id': community_id,
                        'members': members,
                        'size': len(members),
                        'density': density
                    })
            except ImportError:
                # Fall back to connected components
                for i, component in enumerate(nx.connected_components(undirected)):
                    if len(component) < 2:
                        continue
                    
                    # Calculate group density
                    subgraph = undirected.subgraph(component)
                    n = len(component)
                    max_edges = n * (n - 1) / 2
                    density = subgraph.number_of_edges() / max_edges if max_edges > 0 else 0
                    
                    groups.append({
                        'id': i,
                        'members': list(component),
                        'size': len(component),
                        'density': density
                    })
        except Exception as e:
            logger.error(f"Error in community detection: {str(e)}")
            # Fall back to connected components
            for i, component in enumerate(nx.connected_components(undirected)):
                if len(component) < 2:
                    continue
                
                groups.append({
                    'id': i,
                    'members': list(component),
                    'size': len(component),
                    'density': 0
                })
        
        # Identify central figures using centrality measures
        central_figures = []
        
        try:
            # Calculate betweenness centrality
            betweenness = nx.betweenness_centrality(undirected)
            
            # Calculate degree centrality
            degree = nx.degree_centrality(undirected)
            
            # Combine centrality measures
            centrality = {}
            for node in undirected.nodes():
                centrality[node] = betweenness.get(node, 0) + degree.get(node, 0)
            
            # Get top central figures
            central_figures = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            central_figures = [{'person': p, 'centrality': c} for p, c in central_figures]
        except Exception as e:
            logger.error(f"Error calculating centrality: {str(e)}")
        
        # Identify isolated figures (degree 0 or 1)
        isolated_figures = [node for node, degree in dict(undirected.degree()).items() if degree <= 1]
        
        return {
            'groups': groups,
            'central_figures': central_figures,
            'isolated_figures': isolated_figures
        }
    
    def analyze_relationship_balance(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze the balance of communication in relationships.
        
        Returns:
            Dictionary with relationship balance analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for relationship balance analysis")
            return {
                'balanced': [],
                'imbalanced_outgoing': [],
                'imbalanced_incoming': []
            }
        
        # Categories
        categories = {
            'balanced': [],              # Roughly equal communication in both directions
            'imbalanced_outgoing': [],   # Person sends significantly more than receives
            'imbalanced_incoming': []    # Person receives significantly more than sends
        }
        
        # Analyze balance for each person
        for person in self.comm_graph.graph.nodes():
            # Get outgoing and incoming communications
            outgoing = list(self.comm_graph.graph.out_edges(person, data=True))
            incoming = list(self.comm_graph.graph.in_edges(person, data=True))
            
            # Skip if no communications
            if not outgoing and not incoming:
                continue
            
            # Calculate total messages sent and received
            sent = sum(data.get('count', 1) for _, _, data in outgoing)
            received = sum(data.get('count', 1) for _, _, data in incoming)
            
            # Calculate balance ratio
            total = sent + received
            if total > 0:
                sent_ratio = sent / total
                received_ratio = received / total
                
                # Determine category based on balance
                if abs(sent_ratio - received_ratio) < 0.2:  # Within 20% is considered balanced
                    category = 'balanced'
                elif sent_ratio > received_ratio:
                    category = 'imbalanced_outgoing'
                else:
                    category = 'imbalanced_incoming'
                
                # Add to appropriate category
                categories[category].append({
                    'person': person,
                    'sent': sent,
                    'received': received,
                    'sent_ratio': sent_ratio,
                    'received_ratio': received_ratio,
                    'imbalance': abs(sent_ratio - received_ratio)
                })
        
        # Sort each category by imbalance
        for category in categories:
            categories[category].sort(key=lambda x: x['imbalance'], reverse=True)
        
        return categories
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all relationship analyses.
        
        Returns:
            Dictionary with all analysis results
        """
        # Run all analyses
        key_relationships = self.identify_key_relationships(top_n=20)
        categories = self.categorize_relationships()
        evolution = self.analyze_relationship_evolution()
        groups = self.identify_relationship_groups()
        balance = self.analyze_relationship_balance()
        
        # Combine into comprehensive report
        report = {
            'key_relationships': key_relationships,
            'relationship_categories': categories,
            'relationship_evolution': evolution,
            'relationship_groups': groups,
            'relationship_balance': balance,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def save_report_to_file(self, filepath: str) -> None:
        """
        Generate a comprehensive report and save to file.
        
        Args:
            filepath: Path where the report should be saved
        """
        report = self.generate_comprehensive_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Relationship analysis report saved to {filepath}")