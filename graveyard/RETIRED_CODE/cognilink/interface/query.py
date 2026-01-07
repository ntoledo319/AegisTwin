"""
Natural Language Query Interface for CogniLink

This module provides functionality for querying CogniLink data using natural language.
"""

import os
import re
import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import datetime

logger = logging.getLogger(__name__)

class QueryEngine:
    """
    Natural language query engine for CogniLink.
    
    This class provides methods for parsing and executing natural language queries
    against CogniLink data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the query engine.
        
        Args:
            config: Optional configuration dictionary
        """
        from cognilink.core.config import Config
        from cognilink.core.cache import Cache
        
        self.config = config or {}
        self.system_config = Config()
        self.cache = Cache()
        
        # Define query patterns
        self.query_patterns = [
            # Communication patterns
            {
                'pattern': r'(?:show|get|find|display|what are) (?:my )?(?:top|most frequent|main) (?:contacts|people|communicators)',
                'type': 'top_contacts',
                'params': {
                    'limit': self._extract_number
                }
            },
            {
                'pattern': r'(?:show|get|find|display|how many) (?:messages|communications|emails) (?:per|by|for each) (day|week|month)',
                'type': 'frequency_by_period',
                'params': {
                    'period': lambda match: match.group(1)
                }
            },
            {
                'pattern': r'(?:show|get|find|display|when) (?:is|are) (?:my )?(?:peak|busiest|most active) (?:time|hours|period)',
                'type': 'peak_activity_time',
                'params': {}
            },
            {
                'pattern': r'(?:show|get|find|display) (?:my )?(?:communication|message|email) (?:pattern|activity) (?:with|to) (\w+)',
                'type': 'contact_activity',
                'params': {
                    'contact': lambda match: match.group(1)
                }
            },
            
            # Relationship analysis
            {
                'pattern': r'(?:show|get|find|display|who are) (?:my )?(?:closest|strongest|key) (?:contacts|relationships|connections)',
                'type': 'key_relationships',
                'params': {
                    'limit': self._extract_number
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:my )?(?:relationship|connection) (?:with|to) (\w+)',
                'type': 'specific_relationship',
                'params': {
                    'contact': lambda match: match.group(1)
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:my )?(?:social|communication) (?:network|graph)',
                'type': 'communication_network',
                'params': {}
            },
            
            # Topic analysis
            {
                'pattern': r'(?:show|get|find|display|what are) (?:my )?(?:top|main|most common) (?:topics|subjects|themes)',
                'type': 'top_topics',
                'params': {
                    'limit': self._extract_number
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:topics|subjects|themes) (?:discussed|talked about) (?:with|to) (\w+)',
                'type': 'contact_topics',
                'params': {
                    'contact': lambda match: match.group(1)
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:messages|communications|emails) (?:about|related to|mentioning) (\w+)',
                'type': 'topic_messages',
                'params': {
                    'topic': lambda match: match.group(1)
                }
            },
            
            # Time-based queries
            {
                'pattern': r'(?:show|get|find|display) (?:messages|communications|emails) (?:from|in|during) (January|February|March|April|May|June|July|August|September|October|November|December)',
                'type': 'messages_by_month',
                'params': {
                    'month': lambda match: match.group(1)
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:messages|communications|emails) (?:from|in|during) (\d{4})',
                'type': 'messages_by_year',
                'params': {
                    'year': lambda match: int(match.group(1))
                }
            },
            {
                'pattern': r'(?:show|get|find|display) (?:messages|communications|emails) (?:between|from) (\d{4}-\d{2}-\d{2}) (?:and|to) (\d{4}-\d{2}-\d{2})',
                'type': 'messages_by_date_range',
                'params': {
                    'start_date': lambda match: match.group(1),
                    'end_date': lambda match: match.group(2)
                }
            },
            
            # General queries
            {
                'pattern': r'(?:show|get|find|display) (?:all|my) (?:data|information|stats|statistics)',
                'type': 'all_data',
                'params': {}
            },
            {
                'pattern': r'(?:show|get|find|display) (?:summary|overview)',
                'type': 'summary',
                'params': {}
            }
        ]
    
    def parse_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            Tuple of (query_type, parameters)
        """
        # Normalize query
        query = query.lower().strip()
        
        # Try to match query against patterns
        for pattern_info in self.query_patterns:
            pattern = pattern_info['pattern']
            match = re.search(pattern, query, re.IGNORECASE)
            
            if match:
                # Extract parameters
                params = {}
                for param_name, param_extractor in pattern_info['params'].items():
                    if callable(param_extractor):
                        params[param_name] = param_extractor(match)
                    else:
                        params[param_name] = param_extractor
                
                return pattern_info['type'], params
        
        # No match found
        return 'unknown', {}
    
    def execute_query(self, query: str, data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute a natural language query.
        
        Args:
            query: Natural language query string
            data: Optional data to query (if None, loads from cache/files)
            
        Returns:
            Query results
        """
        # Parse query
        query_type, params = self.parse_query(query)
        
        # If query type is unknown, return error
        if query_type == 'unknown':
            return {
                'success': False,
                'error': 'Could not understand query',
                'query': query,
                'suggestions': [
                    'Try asking about your top contacts',
                    'Try asking about your communication patterns',
                    'Try asking about your most discussed topics'
                ]
            }
        
        # Load data if not provided
        if data is None:
            data = self._load_data()
        
        # Execute query based on type
        try:
            if query_type == 'top_contacts':
                result = self._query_top_contacts(data, params)
            elif query_type == 'frequency_by_period':
                result = self._query_frequency_by_period(data, params)
            elif query_type == 'peak_activity_time':
                result = self._query_peak_activity_time(data, params)
            elif query_type == 'contact_activity':
                result = self._query_contact_activity(data, params)
            elif query_type == 'key_relationships':
                result = self._query_key_relationships(data, params)
            elif query_type == 'specific_relationship':
                result = self._query_specific_relationship(data, params)
            elif query_type == 'communication_network':
                result = self._query_communication_network(data, params)
            elif query_type == 'top_topics':
                result = self._query_top_topics(data, params)
            elif query_type == 'contact_topics':
                result = self._query_contact_topics(data, params)
            elif query_type == 'topic_messages':
                result = self._query_topic_messages(data, params)
            elif query_type == 'messages_by_month':
                result = self._query_messages_by_month(data, params)
            elif query_type == 'messages_by_year':
                result = self._query_messages_by_year(data, params)
            elif query_type == 'messages_by_date_range':
                result = self._query_messages_by_date_range(data, params)
            elif query_type == 'all_data':
                result = self._query_all_data(data, params)
            elif query_type == 'summary':
                result = self._query_summary(data, params)
            else:
                result = {
                    'success': False,
                    'error': f'Query type not implemented: {query_type}',
                    'query': query
                }
            
            # Add query info to result
            result['query'] = query
            result['query_type'] = query_type
            result['params'] = params
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                'success': False,
                'error': f'Error executing query: {str(e)}',
                'query': query,
                'query_type': query_type,
                'params': params
            }
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """
        Load data from cache or files.
        
        Returns:
            List of data items
        """
        # Try to get from cache
        data = self.cache.get('all_data')
        if data is not None:
            return data
        
        # Load from files
        data_dir = self.system_config.get('paths', 'data_dir')
        all_data = []
        
        # Find all data files
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.startswith('import_') and file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_data = json.load(f)
                            all_data.extend(file_data)
                    except Exception as e:
                        logger.warning(f"Could not load data from {file_path}: {str(e)}")
        
        # Cache data
        self.cache.set('all_data', all_data)
        
        return all_data
    
    def _extract_number(self, match: re.Match) -> int:
        """
        Extract a number from a query match.
        
        Args:
            match: Regex match object
            
        Returns:
            Extracted number or default value
        """
        # Try to find a number in the query
        number_match = re.search(r'\b(\d+)\b', match.string)
        if number_match:
            return int(number_match.group(1))
        
        # Default value
        return 10
    
    def _query_top_contacts(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for top contacts.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get limit parameter
        limit = params.get('limit', 10)
        
        # Count messages per contact
        contact_counts = {}
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                
                if sender:
                    contact_counts[sender] = contact_counts.get(sender, 0) + 1
                if recipient:
                    contact_counts[recipient] = contact_counts.get(recipient, 0) + 1
        
        # Sort contacts by message count
        sorted_contacts = sorted(contact_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Get top contacts
        top_contacts = []
        for i, (contact, count) in enumerate(sorted_contacts[:limit]):
            top_contacts.append({
                'rank': i + 1,
                'name': contact,
                'message_count': count
            })
        
        return {
            'success': True,
            'top_contacts': top_contacts,
            'total_contacts': len(contact_counts)
        }
    
    def _query_frequency_by_period(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for message frequency by period.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get period parameter
        period = params.get('period', 'day')
        
        # Count messages per period
        period_counts = {}
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
                        if period == 'day':
                            period_key = date.strftime('%Y-%m-%d')
                        elif period == 'week':
                            # ISO week format: YYYY-Www
                            period_key = f"{date.strftime('%Y-W%W')}"
                        elif period == 'month':
                            period_key = date.strftime('%Y-%m')
                        else:
                            period_key = date.strftime('%Y-%m-%d')
                        
                        period_counts[period_key] = period_counts.get(period_key, 0) + 1
                    except ValueError:
                        pass
        
        # Sort periods
        sorted_periods = sorted(period_counts.items())
        
        # Format results
        frequency_data = [
            {'period': period, 'count': count}
            for period, count in sorted_periods
        ]
        
        return {
            'success': True,
            'frequency_data': frequency_data,
            'period': period,
            'total_messages': sum(period_counts.values())
        }
    
    def _query_peak_activity_time(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for peak activity time.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Count messages per hour
        hour_counts = {}
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        hour = date.hour
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    except ValueError:
                        pass
        
        # Find peak hour
        peak_hour = max(hour_counts.items(), key=lambda x: x[1], default=(0, 0))
        
        # Count messages per day of week
        day_counts = {}
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        day = date.strftime('%A')  # Full day name
                        day_counts[day] = day_counts.get(day, 0) + 1
                    except ValueError:
                        pass
        
        # Find peak day
        peak_day = max(day_counts.items(), key=lambda x: x[1], default=('', 0))
        
        # Format hour for display
        peak_hour_formatted = f"{peak_hour[0]:02d}:00 - {peak_hour[0]:02d}:59"
        
        return {
            'success': True,
            'peak_hour': peak_hour[0],
            'peak_hour_formatted': peak_hour_formatted,
            'peak_hour_count': peak_hour[1],
            'peak_day': peak_day[0],
            'peak_day_count': peak_day[1],
            'hour_activity': {str(hour): count for hour, count in sorted(hour_counts.items())},
            'day_activity': {day: count for day, count in sorted(day_counts.items(), 
                                                               key=lambda x: ['Monday', 'Tuesday', 'Wednesday', 
                                                                             'Thursday', 'Friday', 'Saturday', 
                                                                             'Sunday'].index(x[0]))}
        }
    
    def _query_contact_activity(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for activity with a specific contact.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get contact parameter
        contact = params.get('contact', '')
        
        # Find messages with contact
        messages = []
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                
                if contact.lower() in sender.lower() or contact.lower() in recipient.lower():
                    messages.append(item)
        
        # Count messages by date
        date_counts = {}
        for message in messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = date.strftime('%Y-%m-%d')
                    date_counts[date_key] = date_counts.get(date_key, 0) + 1
                except ValueError:
                    pass
        
        # Sort dates
        sorted_dates = sorted(date_counts.items())
        
        # Format results
        activity_data = [
            {'date': date, 'count': count}
            for date, count in sorted_dates
        ]
        
        return {
            'success': True,
            'contact': contact,
            'total_messages': len(messages),
            'activity_data': activity_data,
            'first_message_date': sorted_dates[0][0] if sorted_dates else None,
            'last_message_date': sorted_dates[-1][0] if sorted_dates else None
        }
    
    def _query_key_relationships(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for key relationships.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Similar to top contacts but with more relationship metrics
        # Get limit parameter
        limit = params.get('limit', 10)
        
        # Count messages per contact
        contact_data = {}
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                timestamp = item.get('timestamp', '')
                
                if sender and recipient:
                    # Initialize contact data if needed
                    if sender not in contact_data:
                        contact_data[sender] = {'sent': 0, 'received': 0, 'first_date': None, 'last_date': None}
                    if recipient not in contact_data:
                        contact_data[recipient] = {'sent': 0, 'received': 0, 'first_date': None, 'last_date': None}
                    
                    # Update counts
                    contact_data[sender]['sent'] += 1
                    contact_data[recipient]['received'] += 1
                    
                    # Update dates if timestamp is valid
                    if timestamp:
                        try:
                            date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            
                            # Update sender dates
                            if contact_data[sender]['first_date'] is None or date < contact_data[sender]['first_date']:
                                contact_data[sender]['first_date'] = date
                            if contact_data[sender]['last_date'] is None or date > contact_data[sender]['last_date']:
                                contact_data[sender]['last_date'] = date
                            
                            # Update recipient dates
                            if contact_data[recipient]['first_date'] is None or date < contact_data[recipient]['first_date']:
                                contact_data[recipient]['first_date'] = date
                            if contact_data[recipient]['last_date'] is None or date > contact_data[recipient]['last_date']:
                                contact_data[recipient]['last_date'] = date
                        except ValueError:
                            pass
        
        # Calculate total messages and relationship strength
        for contact, stats in contact_data.items():
            stats['total'] = stats['sent'] + stats['received']
            
            # Calculate balance (0 = completely one-sided, 1 = perfectly balanced)
            if stats['total'] > 0:
                stats['balance'] = 1 - abs(stats['sent'] - stats['received']) / stats['total']
            else:
                stats['balance'] = 0
            
            # Calculate relationship duration in days
            if stats['first_date'] and stats['last_date']:
                stats['duration_days'] = (stats['last_date'] - stats['first_date']).days
            else:
                stats['duration_days'] = 0
            
            # Calculate relationship strength (simple formula combining total messages and balance)
            stats['strength'] = stats['total'] * (0.5 + 0.5 * stats['balance'])
        
        # Sort contacts by relationship strength
        sorted_contacts = sorted(contact_data.items(), key=lambda x: x[1]['strength'], reverse=True)
        
        # Get key relationships
        key_relationships = []
        for i, (contact, stats) in enumerate(sorted_contacts[:limit]):
            key_relationships.append({
                'rank': i + 1,
                'name': contact,
                'total_messages': stats['total'],
                'sent_messages': stats['sent'],
                'received_messages': stats['received'],
                'balance': stats['balance'],
                'duration_days': stats['duration_days'],
                'first_date': stats['first_date'].isoformat() if stats['first_date'] else None,
                'last_date': stats['last_date'].isoformat() if stats['last_date'] else None,
                'strength': stats['strength']
            })
        
        return {
            'success': True,
            'key_relationships': key_relationships,
            'total_contacts': len(contact_data)
        }
    
    def _query_specific_relationship(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for a specific relationship.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get contact parameter
        contact = params.get('contact', '')
        
        # Find messages with contact
        sent_messages = []
        received_messages = []
        
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                
                if contact.lower() in sender.lower() and sender.lower() != 'me':
                    received_messages.append(item)
                elif contact.lower() in recipient.lower() and recipient.lower() != 'me':
                    sent_messages.append(item)
        
        # Extract relationship metrics
        total_messages = len(sent_messages) + len(received_messages)
        
        # Calculate balance
        if total_messages > 0:
            balance = 1 - abs(len(sent_messages) - len(received_messages)) / total_messages
        else:
            balance = 0
        
        # Find first and last message dates
        all_messages = sent_messages + received_messages
        dates = []
        
        for message in all_messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    dates.append(date)
                except ValueError:
                    pass
        
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None
        
        # Calculate duration
        if first_date and last_date:
            duration_days = (last_date - first_date).days
        else:
            duration_days = 0
        
        # Count messages by date
        date_counts = {}
        for message in all_messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = date.strftime('%Y-%m-%d')
                    date_counts[date_key] = date_counts.get(date_key, 0) + 1
                except ValueError:
                    pass
        
        # Sort dates
        sorted_dates = sorted(date_counts.items())
        
        # Format results
        activity_data = [
            {'date': date, 'count': count}
            for date, count in sorted_dates
        ]
        
        return {
            'success': True,
            'contact': contact,
            'total_messages': total_messages,
            'sent_messages': len(sent_messages),
            'received_messages': len(received_messages),
            'balance': balance,
            'duration_days': duration_days,
            'first_date': first_date.isoformat() if first_date else None,
            'last_date': last_date.isoformat() if last_date else None,
            'activity_data': activity_data
        }
    
    def _query_communication_network(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for communication network.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Build communication network
        contacts = set()
        connections = {}
        
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                
                if sender and recipient:
                    contacts.add(sender)
                    contacts.add(recipient)
                    
                    # Create connection key (alphabetical order to avoid duplicates)
                    connection_key = tuple(sorted([sender, recipient]))
                    
                    # Increment connection count
                    connections[connection_key] = connections.get(connection_key, 0) + 1
        
        # Create nodes and edges for network visualization
        nodes = []
        edges = []
        
        # Add nodes
        for contact in contacts:
            nodes.append({
                'id': contact,
                'name': contact
            })
        
        # Add edges
        for (source, target), weight in connections.items():
            edges.append({
                'source': source,
                'target': target,
                'weight': weight
            })
        
        return {
            'success': True,
            'network': {
                'nodes': nodes,
                'edges': edges
            },
            'total_contacts': len(contacts),
            'total_connections': len(connections)
        }
    
    def _query_top_topics(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for top topics.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get limit parameter
        limit = params.get('limit', 10)
        
        # Extract topics from messages
        topics = {}
        
        for item in data:
            if item.get('type') == 'message':
                # Check if message has topics
                message_topics = item.get('topics', [])
                
                for topic in message_topics:
                    topics[topic] = topics.get(topic, 0) + 1
        
        # If no topics found, try to extract from content
        if not topics:
            # Simple keyword extraction
            from collections import Counter
            import string
            
            # Common English stopwords
            stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                        "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
                        'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
                        'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
                        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 
                        'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 
                        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 
                        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
                        'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 
                        'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                        'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
                        'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 
                        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
                        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 
                        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 
                        'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 
                        'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', 
                        "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 
                        'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', 
                        "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 
                        'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', 
                        "won't", 'wouldn', "wouldn't"}
            
            # Extract words from message content
            words = []
            for item in data:
                if item.get('type') == 'message':
                    content = item.get('content', '')
                    if content:
                        # Tokenize and clean words
                        content = content.lower()
                        content = content.translate(str.maketrans('', '', string.punctuation))
                        message_words = content.split()
                        
                        # Filter out stopwords and short words
                        message_words = [word for word in message_words 
                                        if word not in stopwords and len(word) > 3]
                        
                        words.extend(message_words)
            
            # Count word frequencies
            word_counts = Counter(words)
            
            # Convert to topics dictionary
            topics = dict(word_counts)
        
        # Sort topics by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        # Get top topics
        top_topics = []
        for i, (topic, count) in enumerate(sorted_topics[:limit]):
            top_topics.append({
                'rank': i + 1,
                'topic': topic,
                'count': count
            })
        
        return {
            'success': True,
            'top_topics': top_topics,
            'total_topics': len(topics)
        }
    
    def _query_contact_topics(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for topics discussed with a specific contact.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get contact parameter
        contact = params.get('contact', '')
        
        # Find messages with contact
        messages = []
        for item in data:
            if item.get('type') == 'message':
                sender = item.get('sender', '')
                recipient = item.get('recipient', '')
                
                if contact.lower() in sender.lower() or contact.lower() in recipient.lower():
                    messages.append(item)
        
        # Extract topics from messages
        topics = {}
        
        for message in messages:
            # Check if message has topics
            message_topics = message.get('topics', [])
            
            for topic in message_topics:
                topics[topic] = topics.get(topic, 0) + 1
        
        # If no topics found, try to extract from content
        if not topics:
            # Simple keyword extraction
            from collections import Counter
            import string
            
            # Common English stopwords
            stopwords = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
                        "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
                        'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 
                        'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 
                        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 
                        'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 
                        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 
                        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
                        'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 
                        'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                        'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
                        'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 
                        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
                        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 
                        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 
                        'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 
                        'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', 
                        "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 
                        'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', 
                        "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 
                        'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', 
                        "won't", 'wouldn', "wouldn't"}
            
            # Extract words from message content
            words = []
            for message in messages:
                content = message.get('content', '')
                if content:
                    # Tokenize and clean words
                    content = content.lower()
                    content = content.translate(str.maketrans('', '', string.punctuation))
                    message_words = content.split()
                    
                    # Filter out stopwords and short words
                    message_words = [word for word in message_words 
                                    if word not in stopwords and len(word) > 3]
                    
                    words.extend(message_words)
            
            # Count word frequencies
            word_counts = Counter(words)
            
            # Convert to topics dictionary
            topics = dict(word_counts)
        
        # Sort topics by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        
        # Get top topics
        top_topics = []
        for i, (topic, count) in enumerate(sorted_topics[:10]):
            top_topics.append({
                'rank': i + 1,
                'topic': topic,
                'count': count
            })
        
        return {
            'success': True,
            'contact': contact,
            'top_topics': top_topics,
            'total_topics': len(topics),
            'total_messages': len(messages)
        }
    
    def _query_topic_messages(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for messages about a specific topic.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get topic parameter
        topic = params.get('topic', '')
        
        # Find messages about topic
        messages = []
        for item in data:
            if item.get('type') == 'message':
                # Check if message has topics
                message_topics = item.get('topics', [])
                content = item.get('content', '')
                
                if topic.lower() in [t.lower() for t in message_topics] or topic.lower() in content.lower():
                    messages.append(item)
        
        # Sort messages by date
        messages.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Format messages for output
        formatted_messages = []
        for message in messages[:20]:  # Limit to 20 messages
            formatted_messages.append({
                'sender': message.get('sender', ''),
                'recipient': message.get('recipient', ''),
                'timestamp': message.get('timestamp', ''),
                'content': message.get('content', '')[:100] + ('...' if len(message.get('content', '')) > 100 else '')
            })
        
        return {
            'success': True,
            'topic': topic,
            'total_messages': len(messages),
            'messages': formatted_messages
        }
    
    def _query_messages_by_month(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for messages in a specific month.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get month parameter
        month = params.get('month', '')
        
        # Map month name to number
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month_num = month_map.get(month.lower(), None)
        
        if month_num is None:
            return {
                'success': False,
                'error': f'Invalid month: {month}'
            }
        
        # Find messages in month
        messages = []
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if date.month == month_num:
                            messages.append(item)
                    except ValueError:
                        pass
        
        # Group messages by year
        year_counts = {}
        for message in messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    year = date.year
                    year_counts[year] = year_counts.get(year, 0) + 1
                except ValueError:
                    pass
        
        # Sort years
        sorted_years = sorted(year_counts.items())
        
        # Format results
        year_data = [
            {'year': year, 'count': count}
            for year, count in sorted_years
        ]
        
        return {
            'success': True,
            'month': month,
            'month_number': month_num,
            'total_messages': len(messages),
            'year_data': year_data
        }
    
    def _query_messages_by_year(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for messages in a specific year.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get year parameter
        year = params.get('year', datetime.datetime.now().year)
        
        # Find messages in year
        messages = []
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if date.year == year:
                            messages.append(item)
                    except ValueError:
                        pass
        
        # Group messages by month
        month_counts = {}
        for message in messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    month = date.month
                    month_counts[month] = month_counts.get(month, 0) + 1
                except ValueError:
                    pass
        
        # Format results
        month_data = []
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        for month in range(1, 13):
            month_data.append({
                'month': month,
                'month_name': month_names[month - 1],
                'count': month_counts.get(month, 0)
            })
        
        return {
            'success': True,
            'year': year,
            'total_messages': len(messages),
            'month_data': month_data
        }
    
    def _query_messages_by_date_range(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for messages in a specific date range.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get date range parameters
        start_date_str = params.get('start_date', '')
        end_date_str = params.get('end_date', '')
        
        try:
            start_date = datetime.datetime.fromisoformat(start_date_str)
            end_date = datetime.datetime.fromisoformat(end_date_str)
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid date format. Use YYYY-MM-DD format.'
            }
        
        # Find messages in date range
        messages = []
        for item in data:
            if item.get('type') == 'message':
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if start_date <= date <= end_date:
                            messages.append(item)
                    except ValueError:
                        pass
        
        # Group messages by date
        date_counts = {}
        for message in messages:
            timestamp = message.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    date_key = date.strftime('%Y-%m-%d')
                    date_counts[date_key] = date_counts.get(date_key, 0) + 1
                except ValueError:
                    pass
        
        # Sort dates
        sorted_dates = sorted(date_counts.items())
        
        # Format results
        date_data = [
            {'date': date, 'count': count}
            for date, count in sorted_dates
        ]
        
        return {
            'success': True,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'total_messages': len(messages),
            'date_data': date_data
        }
    
    def _query_all_data(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for all data statistics.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Count items by type
        type_counts = {}
        for item in data:
            item_type = item.get('type', 'unknown')
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # Count messages by platform
        platform_counts = {}
        for item in data:
            if item.get('type') == 'message':
                platform = item.get('platform', 'unknown')
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Find date range
        dates = []
        for item in data:
            timestamp = item.get('timestamp', '')
            if timestamp:
                try:
                    date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    dates.append(date)
                except ValueError:
                    pass
        
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None
        
        # Calculate duration
        if first_date and last_date:
            duration_days = (last_date - first_date).days
        else:
            duration_days = 0
        
        return {
            'success': True,
            'total_items': len(data),
            'type_counts': type_counts,
            'platform_counts': platform_counts,
            'first_date': first_date.isoformat() if first_date else None,
            'last_date': last_date.isoformat() if last_date else None,
            'duration_days': duration_days
        }
    
    def _query_summary(self, data: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for a summary of the data.
        
        Args:
            data: Data to query
            params: Query parameters
            
        Returns:
            Query results
        """
        # Get basic statistics
        all_data_stats = self._query_all_data(data, params)
        
        # Get top contacts
        top_contacts_stats = self._query_top_contacts(data, {'limit': 5})
        
        # Get peak activity time
        peak_activity_stats = self._query_peak_activity_time(data, {})
        
        # Get top topics
        top_topics_stats = self._query_top_topics(data, {'limit': 5})
        
        return {
            'success': True,
            'total_items': all_data_stats['total_items'],
            'type_counts': all_data_stats['type_counts'],
            'platform_counts': all_data_stats['platform_counts'],
            'first_date': all_data_stats['first_date'],
            'last_date': all_data_stats['last_date'],
            'duration_days': all_data_stats['duration_days'],
            'top_contacts': top_contacts_stats['top_contacts'],
            'peak_hour': peak_activity_stats['peak_hour'],
            'peak_hour_formatted': peak_activity_stats['peak_hour_formatted'],
            'peak_day': peak_activity_stats['peak_day'],
            'top_topics': top_topics_stats['top_topics']
        }


def query_data(query: str, data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Query data using natural language.
    
    Args:
        query: Natural language query string
        data: Optional data to query (if None, loads from cache/files)
        
    Returns:
        Query results
    """
    engine = QueryEngine()
    return engine.execute_query(query, data)