"""
Communication analysis package.

This package provides functionality for analyzing communication data,
including patterns, relationships, and topics.
"""

import logging
from typing import Dict, List, Any, Optional
from .patterns import PatternAnalyzer
from .relationships import RelationshipAnalyzer
from .topics import TopicAnalyzer

logger = logging.getLogger(__name__)

class CommunicationAnalyzer:
    """Main analyzer for communication data."""
    
    def __init__(self):
        """Initialize the communication analyzer."""
        self.pattern_analyzer = PatternAnalyzer()
        self.relationship_analyzer = RelationshipAnalyzer()
        self.topic_analyzer = TopicAnalyzer()
        self.analysis_results = {}
    
    async def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Analyze communication data.
        
        Args:
            data: Communication data to analyze
            
        Returns:
            Dictionary of analysis results
        """
        logger.info("Starting communication analysis")
        
        # Extract messages from data
        messages = self._extract_messages(data)
        
        if not messages:
            logger.warning("No messages found for analysis")
            return {"error": "No messages found for analysis"}
        
        # Analyze patterns
        pattern_results = await self.pattern_analyzer.analyze(messages)
        
        # Analyze relationships
        relationship_results = await self.relationship_analyzer.analyze(messages)
        
        # Analyze topics
        topic_results = await self.topic_analyzer.analyze(messages)
        
        # Combine results
        results = {
            "patterns": pattern_results.get("patterns", {}),
            "relationships": relationship_results.get("relationships", {}),
            "topics": topic_results.get("topics", {})
        }
        
        # Store results
        self.analysis_results = results
        
        logger.info("Communication analysis complete")
        return results
    
    def _extract_messages(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract messages from data.
        
        Args:
            data: Data containing messages
            
        Returns:
            List of message dictionaries
        """
        # If data is already a list of messages, return it
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        
        # If data is a dictionary with a 'messages' key, return that
        if isinstance(data, dict) and 'messages' in data:
            return data['messages']
        
        # If data is a dictionary with a 'data' key, try that
        if isinstance(data, dict) and 'data' in data:
            if isinstance(data['data'], list):
                return data['data']
            elif isinstance(data['data'], dict) and 'messages' in data['data']:
                return data['data']['messages']
        
        # If we couldn't extract messages, return empty list
        logger.warning("Could not extract messages from data")
        return []
    
    async def generate_insights(self, data: Any) -> List[Dict[str, Any]]:
        """
        Generate insights from communication data.
        
        Args:
            data: Communication data
            
        Returns:
            List of insights
        """
        logger.info("Generating communication insights")
        
        # Analyze data if not already analyzed
        if not self.analysis_results:
            await self.analyze(data)
        
        insights = []
        
        # Generate pattern insights
        pattern_insights = self._generate_pattern_insights()
        insights.extend(pattern_insights)
        
        # Generate relationship insights
        relationship_insights = self._generate_relationship_insights()
        insights.extend(relationship_insights)
        
        # Generate topic insights
        topic_insights = self._generate_topic_insights()
        insights.extend(topic_insights)
        
        # Sort insights by score (higher is more important)
        sorted_insights = sorted(insights, key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Generated {len(sorted_insights)} communication insights")
        return sorted_insights
    
    def _generate_pattern_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from communication patterns.
        
        Returns:
            List of pattern insights
        """
        insights = []
        
        patterns = self.analysis_results.get('patterns', {})
        if not patterns:
            return insights
        
        # Frequency patterns
        frequency = patterns.get('frequency', {})
        if frequency:
            # Active days insight
            active_days_percentage = frequency.get('active_days_percentage')
            if active_days_percentage is not None:
                if active_days_percentage < 30:
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'frequency',
                        'title': 'Low Communication Frequency',
                        'description': f'Communication occurs on only {active_days_percentage:.1f}% of days, indicating sporadic interaction.',
                        'score': 0.7
                    })
                elif active_days_percentage > 80:
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'frequency',
                        'title': 'High Communication Frequency',
                        'description': f'Communication occurs on {active_days_percentage:.1f}% of days, indicating consistent interaction.',
                        'score': 0.6
                    })
            
            # Day of week patterns
            messages_by_day = frequency.get('messages_by_day_of_week', {})
            if messages_by_day:
                # Find the day with most messages
                max_day = max(messages_by_day.items(), key=lambda x: x[1])
                
                insights.append({
                    'type': 'pattern',
                    'subtype': 'frequency',
                    'title': f'Peak Communication Day: {max_day[0]}',
                    'description': f'Communication peaks on {max_day[0]}s with {max_day[1]} messages.',
                    'score': 0.5
                })
            
            # Hour of day patterns
            messages_by_hour = frequency.get('messages_by_hour', {})
            if messages_by_hour:
                # Convert to list of (hour, count) tuples
                hour_counts = [(int(hour), count) for hour, count in messages_by_hour.items()]
                
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
                
                insights.append({
                    'type': 'pattern',
                    'subtype': 'frequency',
                    'title': f'Peak Communication Time: {peak_time[0].capitalize()}',
                    'description': f'Communication is most active during the {peak_time[0]} hours.',
                    'score': 0.5
                })
        
        # Timing patterns
        timing = patterns.get('timing', {})
        if timing:
            # Response time insight
            avg_response_time = timing.get('avg_response_time_seconds')
            if avg_response_time is not None:
                if avg_response_time < 60:  # Less than a minute
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'timing',
                        'title': 'Very Fast Response Time',
                        'description': f'Average response time is {avg_response_time:.1f} seconds, indicating high engagement.',
                        'score': 0.8
                    })
                elif avg_response_time < 300:  # Less than 5 minutes
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'timing',
                        'title': 'Fast Response Time',
                        'description': f'Average response time is {avg_response_time/60:.1f} minutes, indicating good engagement.',
                        'score': 0.7
                    })
                elif avg_response_time > 86400:  # More than a day
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'timing',
                        'title': 'Slow Response Time',
                        'description': f'Average response time is {avg_response_time/86400:.1f} days, indicating low engagement.',
                        'score': 0.7
                    })
        
        # Style patterns
        style = patterns.get('style', {})
        if style:
            # Message length insight
            avg_message_length = style.get('avg_message_length')
            if avg_message_length is not None:
                if avg_message_length < 20:
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'style',
                        'title': 'Brief Communication Style',
                        'description': f'Average message length is only {avg_message_length:.1f} characters, indicating brief, to-the-point communication.',
                        'score': 0.6
                    })
                elif avg_message_length > 200:
                    insights.append({
                        'type': 'pattern',
                        'subtype': 'style',
                        'title': 'Detailed Communication Style',
                        'description': f'Average message length is {avg_message_length:.1f} characters, indicating detailed, thorough communication.',
                        'score': 0.6
                    })
            
            # Emoji usage insight
            emoji_percentage = style.get('emoji_percentage')
            if emoji_percentage is not None and emoji_percentage > 30:
                insights.append({
                    'type': 'pattern',
                    'subtype': 'style',
                    'title': 'High Emoji Usage',
                    'description': f'{emoji_percentage:.1f}% of messages contain emojis, indicating expressive communication.',
                    'score': 0.5
                })
            
            # Question frequency insight
            question_percentage = style.get('question_percentage')
            if question_percentage is not None and question_percentage > 30:
                insights.append({
                    'type': 'pattern',
                    'subtype': 'style',
                    'title': 'Inquisitive Communication Style',
                    'description': f'{question_percentage:.1f}% of messages contain questions, indicating an inquisitive communication style.',
                    'score': 0.6
                })
        
        return insights
    
    def _generate_relationship_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from relationship analysis.
        
        Returns:
            List of relationship insights
        """
        insights = []
        
        relationships = self.analysis_results.get('relationships', {})
        if not relationships:
            return insights
        
        # Relationship strength insights
        strength = relationships.get('strength', {})
        if strength:
            relationship_strength = strength.get('relationship_strength', {})
            if relationship_strength:
                # Get top relationships
                top_relationships = sorted(relationship_strength.items(), key=lambda x: x[1], reverse=True)[:5]
                
                for i, (pair, strength_value) in enumerate(top_relationships):
                    if i == 0:  # Strongest relationship
                        insights.append({
                            'type': 'relationship',
                            'subtype': 'strength',
                            'title': 'Strongest Relationship Identified',
                            'description': f'The strongest relationship is between {pair[0]} and {pair[1]} with a strength score of {strength_value:.2f}.',
                            'score': 0.8
                        })
                    elif i < 3:  # Other strong relationships
                        insights.append({
                            'type': 'relationship',
                            'subtype': 'strength',
                            'title': f'Strong Relationship: {pair[0]} and {pair[1]}',
                            'description': f'A strong relationship exists between {pair[0]} and {pair[1]} with a strength score of {strength_value:.2f}.',
                            'score': 0.7 - (i * 0.1)
                        })
        
        # Network insights
        network = relationships.get('network', {})
        if network:
            # Centrality insights
            degree_centrality = network.get('degree_centrality', {})
            if degree_centrality:
                # Find person with highest centrality
                top_central = max(degree_centrality.items(), key=lambda x: x[1])
                
                insights.append({
                    'type': 'relationship',
                    'subtype': 'network',
                    'title': 'Central Communication Figure',
                    'description': f'{top_central[0]} is the most central figure in the communication network with a centrality score of {top_central[1]:.2f}.',
                    'score': 0.7
                })
            
            # Community insights
            communities = network.get('communities', {})
            if communities:
                # Count members in each community
                community_counts = {}
                for person, community_id in communities.items():
                    if community_id in community_counts:
                        community_counts[community_id].append(person)
                    else:
                        community_counts[community_id] = [person]
                
                # Find largest community
                largest_community = max(community_counts.items(), key=lambda x: len(x[1]))
                
                if len(largest_community[1]) > 2:
                    insights.append({
                        'type': 'relationship',
                        'subtype': 'network',
                        'title': 'Communication Group Identified',
                        'description': f'A communication group of {len(largest_community[1])} people was identified, including {", ".join(largest_community[1][:3])}' + 
                                      (f' and {len(largest_community[1])-3} others' if len(largest_community[1]) > 3 else '') + '.',
                        'score': 0.7
                    })
        
        return insights
    
    def _generate_topic_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights from topic analysis.
        
        Returns:
            List of topic insights
        """
        insights = []
        
        topics = self.analysis_results.get('topics', {})
        if not topics:
            return insights
        
        # Keyword insights
        keywords = topics.get('keywords', {})
        if keywords:
            top_keywords = keywords.get('top_keywords', {})
            if top_keywords:
                # Get top 5 keywords
                top_5_keywords = sorted(top_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
                
                insights.append({
                    'type': 'topic',
                    'subtype': 'keywords',
                    'title': 'Top Communication Topics',
                    'description': f'The most discussed topics include: {", ".join([kw for kw, _ in top_5_keywords])}.',
                    'score': 0.7
                })
            
            # Bigram insights
            top_bigrams = keywords.get('top_bigrams', {})
            if top_bigrams:
                # Get top 3 bigrams
                top_3_bigrams = sorted(top_bigrams.items(), key=lambda x: x[1], reverse=True)[:3]
                
                insights.append({
                    'type': 'topic',
                    'subtype': 'keywords',
                    'title': 'Common Phrases',
                    'description': f'Common phrases in communication include: {", ".join([bg for bg, _ in top_3_bigrams])}.',
                    'score': 0.6
                })
        
        # Topic trend insights
        trends = topics.get('trends', {})
        if trends:
            topic_evolution = trends.get('topic_evolution', {})
            if topic_evolution:
                keyword_overall_trends = topic_evolution.get('keyword_overall_trends', {})
                
                # Find strongly increasing topics
                increasing_topics = [(kw, data) for kw, data in keyword_overall_trends.items() 
                                    if data.get('trend') == 'increasing' and data.get('slope', 0) > 0.5]
                
                if increasing_topics:
                    top_increasing = sorted(increasing_topics, key=lambda x: x[1].get('slope', 0), reverse=True)[:3]
                    
                    insights.append({
                        'type': 'topic',
                        'subtype': 'trends',
                        'title': 'Emerging Topics',
                        'description': f'Topics gaining traction: {", ".join([kw for kw, _ in top_increasing])}.',
                        'score': 0.7
                    })
                
                # Find strongly decreasing topics
                decreasing_topics = [(kw, data) for kw, data in keyword_overall_trends.items() 
                                    if data.get('trend') == 'decreasing' and data.get('slope', 0) < -0.5]
                
                if decreasing_topics:
                    top_decreasing = sorted(decreasing_topics, key=lambda x: x[1].get('slope', 0))[:3]
                    
                    insights.append({
                        'type': 'topic',
                        'subtype': 'trends',
                        'title': 'Declining Topics',
                        'description': f'Topics becoming less common: {", ".join([kw for kw, _ in top_decreasing])}.',
                        'score': 0.6
                    })
        
        return insights