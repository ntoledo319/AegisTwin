"""
Advanced analysis package.

This package provides advanced analysis capabilities for the integrated system,
including NLP, temporal analysis, and network analysis.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from .nlp import NLPAnalyzer
from .temporal import TemporalAnalyzer
from .network import NetworkAnalyzer

logger = logging.getLogger(__name__)

class AdvancedAnalyzer:
    """Main advanced analyzer."""
    
    def __init__(self):
        """Initialize the advanced analyzer."""
        self.nlp_analyzer = NLPAnalyzer()
        self.temporal_analyzer = TemporalAnalyzer()
        self.network_analyzer = NetworkAnalyzer()
        self.analysis_results = {}
    
    async def analyze(self, data: Any, communication_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze data using advanced techniques.
        
        Args:
            data: Data to analyze
            communication_results: Results from communication analysis (optional)
            
        Returns:
            Dictionary of analysis results
        """
        logger.info("Starting advanced analysis")
        
        # Extract text content for NLP analysis
        texts = self._extract_texts(data)
        
        # Extract temporal data
        temporal_data = self._extract_temporal_data(data)
        
        # Extract network data
        nodes, edges = self._extract_network_data(data, communication_results)
        
        # Perform NLP analysis
        nlp_results = await self.nlp_analyzer.analyze(texts)
        
        # Perform temporal analysis
        temporal_results = await self.temporal_analyzer.analyze(temporal_data)
        
        # Perform network analysis
        network_results = await self.network_analyzer.analyze(nodes, edges)
        
        # Combine results
        results = {
            "nlp": nlp_results,
            "temporal": temporal_results,
            "network": network_results
        }
        
        # Store results
        self.analysis_results = results
        
        logger.info("Advanced analysis complete")
        return results
    
    def _extract_texts(self, data: Any) -> List[str]:
        """
        Extract text content from data.
        
        Args:
            data: Data containing text content
            
        Returns:
            List of text strings
        """
        texts = []
        
        # If data is a list of dictionaries
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Look for content field in each item
            for item in data:
                if 'content' in item and item['content']:
                    texts.append(str(item['content']))
                elif 'text' in item and item['text']:
                    texts.append(str(item['text']))
                elif 'message' in item and item['message']:
                    texts.append(str(item['message']))
        
        # If data is a dictionary with a 'messages' key
        elif isinstance(data, dict) and 'messages' in data:
            messages = data['messages']
            if isinstance(messages, list):
                for message in messages:
                    if isinstance(message, dict):
                        if 'content' in message and message['content']:
                            texts.append(str(message['content']))
                        elif 'text' in message and message['text']:
                            texts.append(str(message['text']))
                        elif 'message' in message and message['message']:
                            texts.append(str(message['message']))
        
        # If data is a dictionary with a 'data' key
        elif isinstance(data, dict) and 'data' in data:
            return self._extract_texts(data['data'])
        
        logger.info(f"Extracted {len(texts)} texts for NLP analysis")
        return texts
    
    def _extract_temporal_data(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract temporal data.
        
        Args:
            data: Data containing temporal information
            
        Returns:
            List of dictionaries with temporal data
        """
        temporal_data = []
        
        # If data is a list of dictionaries
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Look for timestamp field in each item
            for item in data:
                if 'timestamp' in item:
                    temporal_data.append(item)
                elif 'date' in item:
                    # Copy item and add timestamp field
                    new_item = item.copy()
                    new_item['timestamp'] = item['date']
                    temporal_data.append(new_item)
        
        # If data is a dictionary with a 'messages' key
        elif isinstance(data, dict) and 'messages' in data:
            messages = data['messages']
            if isinstance(messages, list):
                for message in messages:
                    if isinstance(message, dict):
                        if 'timestamp' in message:
                            temporal_data.append(message)
                        elif 'date' in message:
                            # Copy message and add timestamp field
                            new_message = message.copy()
                            new_message['timestamp'] = message['date']
                            temporal_data.append(new_message)
        
        # If data is a dictionary with a 'data' key
        elif isinstance(data, dict) and 'data' in data:
            return self._extract_temporal_data(data['data'])
        
        logger.info(f"Extracted {len(temporal_data)} items for temporal analysis")
        return temporal_data
    
    def _extract_network_data(self, data: Any, communication_results: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract network data.
        
        Args:
            data: Data containing network information
            communication_results: Results from communication analysis (optional)
            
        Returns:
            Tuple of (nodes, edges) lists
        """
        nodes = []
        edges = []
        
        # If communication results are available, use relationship data
        if communication_results and 'relationships' in communication_results:
            relationships = communication_results['relationships']
            
            # Extract nodes from relationship data
            if 'strength' in relationships and 'relationship_strength' in relationships['strength']:
                relationship_strength = relationships['strength']['relationship_strength']
                
                # Create nodes set to avoid duplicates
                nodes_set = set()
                
                # Create edges from relationship strength
                for pair, strength in relationship_strength.items():
                    if isinstance(pair, tuple) and len(pair) == 2:
                        source, target = pair
                        
                        # Add nodes if not already added
                        if source not in nodes_set:
                            nodes.append({'id': source, 'type': 'person'})
                            nodes_set.add(source)
                        
                        if target not in nodes_set:
                            nodes.append({'id': target, 'type': 'person'})
                            nodes_set.add(target)
                        
                        # Add edge
                        edges.append({
                            'source': source,
                            'target': target,
                            'weight': strength,
                            'type': 'relationship'
                        })
        
        # If no network data was extracted from communication results, try to extract from data
        if not nodes or not edges:
            # If data is a list of dictionaries
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                # Look for sender and recipient fields in each item
                for item in data:
                    if 'sender' in item and 'recipient' in item:
                        sender = item['sender']
                        recipient = item['recipient']
                        
                        # Add nodes if not already added
                        if not any(node['id'] == sender for node in nodes):
                            nodes.append({'id': sender, 'type': 'person'})
                        
                        if not any(node['id'] == recipient for node in nodes):
                            nodes.append({'id': recipient, 'type': 'person'})
                        
                        # Add edge
                        edges.append({
                            'source': sender,
                            'target': recipient,
                            'type': 'message'
                        })
            
            # If data is a dictionary with a 'messages' key
            elif isinstance(data, dict) and 'messages' in data:
                messages = data['messages']
                if isinstance(messages, list):
                    for message in messages:
                        if isinstance(message, dict) and 'sender' in message and 'recipient' in message:
                            sender = message['sender']
                            recipient = message['recipient']
                            
                            # Add nodes if not already added
                            if not any(node['id'] == sender for node in nodes):
                                nodes.append({'id': sender, 'type': 'person'})
                            
                            if not any(node['id'] == recipient for node in nodes):
                                nodes.append({'id': recipient, 'type': 'person'})
                            
                            # Add edge
                            edges.append({
                                'source': sender,
                                'target': recipient,
                                'type': 'message'
                            })
            
            # If data is a dictionary with a 'data' key
            elif isinstance(data, dict) and 'data' in data:
                return self._extract_network_data(data['data'], communication_results)
        
        logger.info(f"Extracted {len(nodes)} nodes and {len(edges)} edges for network analysis")
        return nodes, edges
    
    async def generate_insights(self, data: Any) -> List[Dict[str, Any]]:
        """
        Generate insights from advanced analysis.
        
        Args:
            data: Data for analysis
            
        Returns:
            List of insights
        """
        logger.info("Generating advanced insights")
        
        # Analyze data if not already analyzed
        if not self.analysis_results:
            await self.analyze(data)
        
        insights = []
        
        # Generate NLP insights
        nlp_insights = self._generate_nlp_insights()
        insights.extend(nlp_insights)
        
        # Generate temporal insights
        temporal_insights = self._generate_temporal_insights()
        insights.extend(temporal_insights)
        
        # Generate network insights
        network_insights = self._generate_network_insights()
        insights.extend(network_insights)
        
        # Sort insights by score (higher is more important)
        sorted_insights = sorted(insights, key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Generated {len(sorted_insights)} advanced insights")
        return sorted_insights
    
    def _generate_nlp_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from NLP analysis.
        
        Returns:
            List of NLP insights
        """
        insights = []
        
        nlp_results = self.analysis_results.get('nlp', {})
        if not nlp_results:
            return insights
        
        # Sentiment insights
        sentiment = nlp_results.get('sentiment', {})
        if sentiment and 'error' not in sentiment:
            avg_polarity = sentiment.get('avg_polarity')
            if avg_polarity is not None:
                if avg_polarity > 0.25:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'sentiment',
                        'title': 'Positive Sentiment Detected',
                        'description': f'The overall sentiment is positive with a polarity score of {avg_polarity:.2f}.',
                        'score': 0.7
                    })
                elif avg_polarity < -0.25:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'sentiment',
                        'title': 'Negative Sentiment Detected',
                        'description': f'The overall sentiment is negative with a polarity score of {avg_polarity:.2f}.',
                        'score': 0.8
                    })
            
            sentiment_distribution = sentiment.get('sentiment_distribution', {})
            if sentiment_distribution:
                positive_pct = sentiment_distribution.get('positive', 0) * 100
                negative_pct = sentiment_distribution.get('negative', 0) * 100
                
                if positive_pct > 70:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'sentiment',
                        'title': 'Predominantly Positive Content',
                        'description': f'{positive_pct:.1f}% of content expresses positive sentiment.',
                        'score': 0.6
                    })
                elif negative_pct > 30:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'sentiment',
                        'title': 'Significant Negative Content',
                        'description': f'{negative_pct:.1f}% of content expresses negative sentiment.',
                        'score': 0.7
                    })
        
        # Entity insights
        entities = nlp_results.get('entities', {})
        if entities and 'error' not in entities:
            top_entities = entities.get('top_entities', {})
            if top_entities:
                # Get top 3 entities
                top_3 = sorted(top_entities.items(), key=lambda x: x[1], reverse=True)[:3]
                
                if top_3:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'entities',
                        'title': 'Key Entities Identified',
                        'description': f'The most frequently mentioned entities are: {", ".join([e[0] for e in top_3])}.',
                        'score': 0.6
                    })
            
            entity_types = entities.get('entity_types', {})
            if entity_types:
                # Check if there are many person mentions
                person_count = entity_types.get('PERSON', 0)
                if person_count > 10:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'entities',
                        'title': 'Multiple People Referenced',
                        'description': f'Content references {person_count} different people.',
                        'score': 0.5
                    })
                
                # Check if there are many organization mentions
                org_count = entity_types.get('ORG', 0)
                if org_count > 5:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'entities',
                        'title': 'Multiple Organizations Referenced',
                        'description': f'Content references {org_count} different organizations.',
                        'score': 0.5
                    })
        
        # Readability insights
        readability = nlp_results.get('readability', {})
        if readability and 'error' not in readability:
            readability_level = readability.get('readability_level')
            if readability_level:
                if readability_level in ['Difficult', 'Very Difficult']:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'readability',
                        'title': 'Complex Communication Style',
                        'description': f'The content has a {readability_level.lower()} readability level, indicating complex communication.',
                        'score': 0.6
                    })
                elif readability_level in ['Very Easy', 'Easy']:
                    insights.append({
                        'type': 'nlp',
                        'subtype': 'readability',
                        'title': 'Simple Communication Style',
                        'description': f'The content has an {readability_level.lower()} readability level, indicating straightforward communication.',
                        'score': 0.5
                    })
        
        return insights
    
    def _generate_temporal_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from temporal analysis.
        
        Returns:
            List of temporal insights
        """
        insights = []
        
        temporal_results = self.analysis_results.get('temporal', {})
        if not temporal_results:
            return insights
        
        # Time distribution insights
        time_distribution = temporal_results.get('time_distribution', {})
        if time_distribution and 'error' not in time_distribution:
            # Check for active days percentage
            active_days_percentage = time_distribution.get('active_days_percentage')
            if active_days_percentage is not None:
                if active_days_percentage < 30:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'activity',
                        'title': 'Sporadic Activity Pattern',
                        'description': f'Activity occurs on only {active_days_percentage:.1f}% of days, indicating sporadic engagement.',
                        'score': 0.7
                    })
                elif active_days_percentage > 80:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'activity',
                        'title': 'Consistent Activity Pattern',
                        'description': f'Activity occurs on {active_days_percentage:.1f}% of days, indicating consistent engagement.',
                        'score': 0.6
                    })
            
            # Check for day of week patterns
            events_by_day_of_week = time_distribution.get('events_by_day_of_week', {})
            if events_by_day_of_week:
                # Find the day with most events
                max_day = max(events_by_day_of_week.items(), key=lambda x: x[1])
                
                # Find the day with least events
                min_day = min(events_by_day_of_week.items(), key=lambda x: x[1])
                
                # Calculate ratio between max and min
                ratio = max_day[1] / min_day[1] if min_day[1] > 0 else float('inf')
                
                if ratio > 3:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'pattern',
                        'title': 'Strong Weekly Pattern',
                        'description': f'Activity peaks on {max_day[0]}s ({max_day[1]} events) and is lowest on {min_day[0]}s ({min_day[1]} events).',
                        'score': 0.7
                    })
            
            # Check for hour of day patterns
            events_by_hour = time_distribution.get('events_by_hour', {})
            if events_by_hour:
                # Convert to list of (hour, count) tuples
                hour_counts = [(int(hour), count) for hour, count in events_by_hour.items()]
                
                # Find peak hours (morning, afternoon, evening, night)
                morning_count = sum(count for hour, count in hour_counts if 5 <= hour < 12)
                afternoon_count = sum(count for hour, count in hour_counts if 12 <= hour < 17)
                evening_count = sum(count for hour, count in hour_counts if 17 <= hour < 22)
                night_count = sum(count for hour, count in hour_counts if hour >= 22 or hour < 5)
                
                # Find peak time of day
                time_counts = [
                    ('morning', morning_count),
                    ('afternoon', afternoon_count),
                    ('evening', evening_count),
                    ('night', night_count)
                ]
                
                peak_time = max(time_counts, key=lambda x: x[1])
                
                # Calculate percentage of activity during peak time
                total_count = sum(count for _, count in time_counts)
                peak_percentage = (peak_time[1] / total_count) * 100 if total_count > 0 else 0
                
                if peak_percentage > 50:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'pattern',
                        'title': f'Strong {peak_time[0].capitalize()} Activity Pattern',
                        'description': f'{peak_percentage:.1f}% of activity occurs during {peak_time[0]} hours.',
                        'score': 0.7
                    })
        
        # Trend insights
        trends = temporal_results.get('trends', {})
        if trends and 'error' not in trends:
            trend_direction = trends.get('trend_direction')
            trend_strength = trends.get('trend_strength')
            
            if trend_direction and trend_strength:
                if trend_direction == 'increasing' and trend_strength > 0.1:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'trend',
                        'title': 'Increasing Activity Trend',
                        'description': f'Activity is showing an increasing trend with a strength of {trend_strength:.2f}.',
                        'score': 0.8
                    })
                elif trend_direction == 'decreasing' and trend_strength > 0.1:
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'trend',
                        'title': 'Decreasing Activity Trend',
                        'description': f'Activity is showing a decreasing trend with a strength of {trend_strength:.2f}.',
                        'score': 0.8
                    })
        
        # Seasonality insights
        seasonality = temporal_results.get('seasonality', {})
        if seasonality and 'error' not in seasonality:
            seasonality_detected = seasonality.get('seasonality_detected')
            seasonality_strength = seasonality.get('seasonality_strength')
            
            if seasonality_detected and seasonality_strength > 0.3:
                insights.append({
                    'type': 'temporal',
                    'subtype': 'seasonality',
                    'title': 'Strong Weekly Pattern Detected',
                    'description': f'Activity shows a strong weekly pattern with a seasonality strength of {seasonality_strength:.2f}.',
                    'score': 0.7
                })
                
                # If we have day pattern information
                seasonal_pattern = seasonality.get('seasonal_pattern', {})
                if seasonal_pattern:
                    # Find the day with highest positive effect
                    max_day = max(seasonal_pattern.items(), key=lambda x: x[1])
                    
                    # Find the day with lowest negative effect
                    min_day = min(seasonal_pattern.items(), key=lambda x: x[1])
                    
                    insights.append({
                        'type': 'temporal',
                        'subtype': 'seasonality',
                        'title': 'Weekly Activity Pattern',
                        'description': f'Activity typically peaks on {max_day[0]}s and is lowest on {min_day[0]}s.',
                        'score': 0.6
                    })
        
        return insights
    
    def _generate_network_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from network analysis.
        
        Returns:
            List of network insights
        """
        insights = []
        
        network_results = self.analysis_results.get('network', {})
        if not network_results:
            return insights
        
        # Network statistics insights
        statistics = network_results.get('statistics', {})
        if statistics and 'error' not in statistics:
            # Check network size
            node_count = statistics.get('node_count')
            edge_count = statistics.get('edge_count')
            
            if node_count and edge_count:
                if node_count > 50:
                    insights.append({
                        'type': 'network',
                        'subtype': 'structure',
                        'title': 'Large Communication Network',
                        'description': f'The communication network involves {node_count} individuals with {edge_count} connections.',
                        'score': 0.7
                    })
            
            # Check network density
            density = statistics.get('density')
            if density is not None:
                if density < 0.1 and node_count > 10:
                    insights.append({
                        'type': 'network',
                        'subtype': 'structure',
                        'title': 'Sparse Communication Network',
                        'description': f'The communication network has a low density of {density:.3f}, indicating limited interconnections.',
                        'score': 0.6
                    })
                elif density > 0.5 and node_count > 10:
                    insights.append({
                        'type': 'network',
                        'subtype': 'structure',
                        'title': 'Dense Communication Network',
                        'description': f'The communication network has a high density of {density:.3f}, indicating many interconnections.',
                        'score': 0.6
                    })
            
            # Check connectivity
            is_connected = statistics.get('is_connected')
            num_components = statistics.get('num_components')
            
            if is_connected is not None and num_components is not None:
                if not is_connected and num_components > 3:
                    insights.append({
                        'type': 'network',
                        'subtype': 'structure',
                        'title': 'Fragmented Communication Network',
                        'description': f'The communication network is split into {num_components} separate groups with no interaction between them.',
                        'score': 0.7
                    })
        
        # Centrality insights
        centrality = network_results.get('centrality', {})
        if centrality and 'error' not in centrality:
            # Check for central figures
            most_central = centrality.get('most_central_nodes', {})
            
            if most_central:
                # Get the most central node by degree
                degree_central = most_central.get('degree')
                if degree_central:
                    insights.append({
                        'type': 'network',
                        'subtype': 'centrality',
                        'title': 'Key Communication Hub Identified',
                        'description': f'{degree_central} is a central figure in the communication network, connecting with many others.',
                        'score': 0.8
                    })
                
                # Get the most central node by betweenness
                betweenness_central = most_central.get('betweenness')
                if betweenness_central and betweenness_central != degree_central:
                    insights.append({
                        'type': 'network',
                        'subtype': 'centrality',
                        'title': 'Key Communication Bridge Identified',
                        'description': f'{betweenness_central} serves as an important bridge between different parts of the communication network.',
                        'score': 0.7
                    })
        
        # Community insights
        communities = network_results.get('communities', {})
        if communities and 'error' not in communities:
            num_communities = communities.get('num_communities')
            community_sizes = communities.get('community_sizes', {})
            
            if num_communities and num_communities > 1 and community_sizes:
                # Find the largest community
                largest_community_id = max(community_sizes.items(), key=lambda x: x[1])[0]
                largest_community_size = community_sizes[largest_community_id]
                
                # Get community members
                community_members = communities.get('communities', {}).get(largest_community_id, [])
                
                if community_members and len(community_members) >= 3:
                    insights.append({
                        'type': 'network',
                        'subtype': 'community',
                        'title': 'Strong Communication Group Identified',
                        'description': f'A closely connected group of {largest_community_size} individuals was identified, including {", ".join(community_members[:3])}' + 
                                      (f' and {len(community_members)-3} others' if len(community_members) > 3 else '') + '.',
                        'score': 0.7
                    })
                
                if num_communities > 2:
                    insights.append({
                        'type': 'network',
                        'subtype': 'community',
                        'title': 'Multiple Communication Groups',
                        'description': f'The communication network contains {num_communities} distinct groups with limited interaction between them.',
                        'score': 0.6
                    })
        
        # Path insights
        paths = network_results.get('paths', {})
        if paths and 'error' not in paths:
            diameter = paths.get('diameter')
            avg_path_length = paths.get('avg_path_length')
            
            if diameter is not None and avg_path_length is not None:
                if diameter > 6 and node_count > 20:
                    insights.append({
                        'type': 'network',
                        'subtype': 'paths',
                        'title': 'Extended Communication Chain',
                        'description': f'Information must pass through up to {diameter} people to reach across the entire network.',
                        'score': 0.6
                    })
                elif diameter <= 3 and node_count > 10:
                    insights.append({
                        'type': 'network',
                        'subtype': 'paths',
                        'title': 'Efficient Communication Network',
                        'description': f'Information can reach anyone in the network in {diameter} steps or fewer.',
                        'score': 0.5
                    })
        
        return insights