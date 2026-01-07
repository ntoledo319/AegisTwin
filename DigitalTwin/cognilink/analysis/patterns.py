"""
Communication Pattern Analyzer for CogniLink

This module analyzes communication patterns to identify trends, habits,
and behavioral insights from communication data.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import statistics
from collections import Counter, defaultdict
import networkx as nx
import json

from cognilink.core.comm_graph import CommunicationGraph

logger = logging.getLogger(__name__)

class CommunicationPatternAnalyzer:
    """
    Analyzer for communication patterns and behaviors.
    
    This class identifies patterns in communication data such as:
    - Communication frequency and timing
    - Response patterns and delays
    - Communication habits and routines
    - Changes in communication behavior over time
    """
    
    def __init__(self, comm_graph: CommunicationGraph = None):
        """
        Initialize the communication pattern analyzer.
        
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
    
    def analyze_communication_frequency(self, time_period: str = 'day') -> Dict[str, Any]:
        """
        Analyze communication frequency over time.
        
        Args:
            time_period: Time period for grouping ('hour', 'day', 'week', 'month')
            
        Returns:
            Dictionary with frequency analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for frequency analysis")
            return {
                'time_period': time_period,
                'frequency_data': {},
                'peak_periods': [],
                'average_per_period': 0,
                'total_communications': 0
            }
        
        # Extract timestamps from all communications
        timestamps = []
        for _, _, data in self.comm_graph.graph.edges(data=True):
            if 'first_comm' in data:
                try:
                    timestamp = datetime.fromisoformat(data['first_comm'])
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue
        
        if not timestamps:
            logger.warning("No valid timestamps found for frequency analysis")
            return {
                'time_period': time_period,
                'frequency_data': {},
                'peak_periods': [],
                'average_per_period': 0,
                'total_communications': 0
            }
        
        # Group by time period
        frequency_data = defaultdict(int)
        
        for timestamp in timestamps:
            if time_period == 'hour':
                key = timestamp.strftime('%Y-%m-%d %H:00')
            elif time_period == 'day':
                key = timestamp.strftime('%Y-%m-%d')
            elif time_period == 'week':
                # ISO week format: YYYY-Www
                key = f"{timestamp.isocalendar()[0]}-W{timestamp.isocalendar()[1]:02d}"
            elif time_period == 'month':
                key = timestamp.strftime('%Y-%m')
            else:
                logger.warning(f"Unknown time period: {time_period}, using day")
                key = timestamp.strftime('%Y-%m-%d')
            
            frequency_data[key] += 1
        
        # Convert to regular dict for JSON serialization
        frequency_data = dict(frequency_data)
        
        # Calculate statistics
        values = list(frequency_data.values())
        total_communications = sum(values)
        average_per_period = total_communications / len(frequency_data) if frequency_data else 0
        
        # Find peak periods (periods with communication count > average)
        peak_periods = [period for period, count in frequency_data.items() 
                       if count > average_per_period]
        
        return {
            'time_period': time_period,
            'frequency_data': frequency_data,
            'peak_periods': peak_periods,
            'average_per_period': average_per_period,
            'total_communications': total_communications
        }
    
    def analyze_response_patterns(self) -> Dict[str, Any]:
        """
        Analyze response patterns between communicators.
        
        Returns:
            Dictionary with response pattern analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for response pattern analysis")
            return {
                'average_response_time': None,
                'response_rates': {},
                'non_responders': [],
                'quick_responders': []
            }
        
        # Calculate response times and rates
        response_times = []
        response_rates = {}
        non_responders = []
        quick_responders = []
        
        # For each person in the graph
        for person in self.comm_graph.graph.nodes():
            # Get all incoming and outgoing communications
            incoming = list(self.comm_graph.graph.in_edges(person, data=True))
            outgoing = list(self.comm_graph.graph.out_edges(person, data=True))
            
            if not incoming:
                continue  # Skip if no incoming messages
            
            # Calculate response rate
            total_incoming = sum(data.get('count', 1) for _, _, data in incoming)
            total_outgoing = sum(data.get('count', 1) for _, _, data in outgoing)
            
            response_rate = total_outgoing / total_incoming if total_incoming > 0 else 0
            response_rates[person] = response_rate
            
            if response_rate < 0.2 and total_incoming > 5:
                non_responders.append(person)
            
            # Calculate response times
            person_response_times = []
            
            # For each person who sent messages to this person
            for sender, _, in_data in incoming:
                # Check if this person responded to the sender
                if self.comm_graph.graph.has_edge(person, sender):
                    # Get timestamps of communications
                    try:
                        last_received = datetime.fromisoformat(in_data.get('last_comm'))
                        out_data = self.comm_graph.graph[person][sender]
                        first_sent = datetime.fromisoformat(out_data.get('first_comm'))
                        
                        # Calculate response time if first_sent is after last_received
                        if first_sent > last_received:
                            response_time = (first_sent - last_received).total_seconds() / 3600  # hours
                            person_response_times.append(response_time)
                    except (ValueError, TypeError, KeyError):
                        continue
            
            # Calculate average response time for this person
            if person_response_times:
                avg_response_time = statistics.mean(person_response_times)
                response_times.extend(person_response_times)
                
                if avg_response_time < 2 and len(person_response_times) > 3:  # Less than 2 hours avg
                    quick_responders.append((person, avg_response_time))
        
        # Calculate overall average response time
        average_response_time = statistics.mean(response_times) if response_times else None
        
        # Sort quick responders by response time
        quick_responders.sort(key=lambda x: x[1])
        
        return {
            'average_response_time': average_response_time,
            'response_rates': response_rates,
            'non_responders': non_responders,
            'quick_responders': [p[0] for p in quick_responders[:10]]  # Top 10 quick responders
        }
    
    def analyze_communication_habits(self) -> Dict[str, Any]:
        """
        Analyze communication habits and routines.
        
        Returns:
            Dictionary with communication habits analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for habits analysis")
            return {
                'time_of_day_distribution': {},
                'day_of_week_distribution': {},
                'preferred_times': {},
                'communication_gaps': []
            }
        
        # Extract timestamps from all communications
        timestamps = []
        for _, _, data in self.comm_graph.graph.edges(data=True):
            if 'first_comm' in data:
                try:
                    timestamp = datetime.fromisoformat(data['first_comm'])
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue
        
        if not timestamps:
            logger.warning("No valid timestamps found for habits analysis")
            return {
                'time_of_day_distribution': {},
                'day_of_week_distribution': {},
                'preferred_times': {},
                'communication_gaps': []
            }
        
        # Analyze time of day distribution
        hours = [ts.hour for ts in timestamps]
        time_of_day = {
            'morning': sum(1 for h in hours if 5 <= h < 12),
            'afternoon': sum(1 for h in hours if 12 <= h < 17),
            'evening': sum(1 for h in hours if 17 <= h < 22),
            'night': sum(1 for h in hours if h >= 22 or h < 5)
        }
        
        # Analyze day of week distribution
        days = [ts.weekday() for ts in timestamps]
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = {day_names[i]: days.count(i) for i in range(7)}
        
        # Analyze preferred communication times for each person
        preferred_times = {}
        for person in self.comm_graph.graph.nodes():
            # Get all outgoing communications
            outgoing = list(self.comm_graph.graph.out_edges(person, data=True))
            
            if not outgoing:
                continue
            
            # Extract timestamps
            person_timestamps = []
            for _, _, data in outgoing:
                if 'first_comm' in data:
                    try:
                        timestamp = datetime.fromisoformat(data['first_comm'])
                        person_timestamps.append(timestamp)
                    except (ValueError, TypeError):
                        continue
            
            if not person_timestamps:
                continue
            
            # Calculate preferred time of day
            person_hours = [ts.hour for ts in person_timestamps]
            person_time_of_day = {
                'morning': sum(1 for h in person_hours if 5 <= h < 12),
                'afternoon': sum(1 for h in person_hours if 12 <= h < 17),
                'evening': sum(1 for h in person_hours if 17 <= h < 22),
                'night': sum(1 for h in person_hours if h >= 22 or h < 5)
            }
            
            # Find preferred time
            preferred_time = max(person_time_of_day.items(), key=lambda x: x[1])[0]
            preferred_times[person] = preferred_time
        
        # Identify communication gaps
        communication_gaps = []
        
        # Sort timestamps
        sorted_timestamps = sorted(timestamps)
        
        if len(sorted_timestamps) > 1:
            # Calculate gaps between consecutive timestamps
            for i in range(1, len(sorted_timestamps)):
                gap = (sorted_timestamps[i] - sorted_timestamps[i-1]).total_seconds() / 86400  # days
                
                # Consider gaps of more than 7 days
                if gap > 7:
                    gap_start = sorted_timestamps[i-1].strftime('%Y-%m-%d')
                    gap_end = sorted_timestamps[i].strftime('%Y-%m-%d')
                    gap_length = round(gap, 1)
                    
                    communication_gaps.append({
                        'start_date': gap_start,
                        'end_date': gap_end,
                        'length_days': gap_length
                    })
        
        return {
            'time_of_day_distribution': time_of_day,
            'day_of_week_distribution': day_of_week,
            'preferred_times': preferred_times,
            'communication_gaps': communication_gaps
        }
    
    def analyze_communication_changes(self, window_size: int = 30) -> Dict[str, Any]:
        """
        Analyze changes in communication patterns over time.
        
        Args:
            window_size: Size of the time window in days
            
        Returns:
            Dictionary with communication changes analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_edges() == 0:
            logger.warning("No communication graph data available for changes analysis")
            return {
                'trend_data': {},
                'increasing_contacts': [],
                'decreasing_contacts': [],
                'new_contacts': [],
                'dormant_contacts': []
            }
        
        # Extract timestamps and organize by person
        person_timestamps = defaultdict(list)
        
        for source, target, data in self.comm_graph.graph.edges(data=True):
            if 'first_comm' in data:
                try:
                    timestamp = datetime.fromisoformat(data['first_comm'])
                    person_timestamps[source].append(timestamp)
                    person_timestamps[target].append(timestamp)
                except (ValueError, TypeError):
                    continue
        
        if not person_timestamps:
            logger.warning("No valid timestamps found for changes analysis")
            return {
                'trend_data': {},
                'increasing_contacts': [],
                'decreasing_contacts': [],
                'new_contacts': [],
                'dormant_contacts': []
            }
        
        # Find overall date range
        all_timestamps = [ts for timestamps in person_timestamps.values() for ts in timestamps]
        min_date = min(all_timestamps).date()
        max_date = max(all_timestamps).date()
        
        # Calculate number of days in range
        days_range = (max_date - min_date).days + 1
        
        # If range is too small, adjust window size
        if days_range < window_size * 2:
            window_size = max(days_range // 4, 1)
            logger.warning(f"Date range too small, adjusted window size to {window_size} days")
        
        # Create time windows
        windows = []
        current_date = min_date
        while current_date <= max_date:
            window_end = current_date + timedelta(days=window_size)
            windows.append((current_date, window_end))
            current_date = window_end
        
        # Calculate communication frequency in each window
        trend_data = {}
        
        for person, timestamps in person_timestamps.items():
            person_trend = []
            
            for window_start, window_end in windows:
                # Count communications in this window
                count = sum(1 for ts in timestamps 
                           if window_start <= ts.date() < window_end)
                
                person_trend.append({
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat(),
                    'count': count
                })
            
            trend_data[person] = person_trend
        
        # Identify increasing and decreasing trends
        increasing_contacts = []
        decreasing_contacts = []
        
        for person, trend in trend_data.items():
            if len(trend) < 2:
                continue
            
            # Calculate slope of trend
            counts = [t['count'] for t in trend]
            
            # Simple trend calculation: compare first and last windows
            first_count = counts[0]
            last_count = counts[-1]
            
            # Require at least 3 communications for meaningful trend
            if sum(counts) < 3:
                continue
            
            # Calculate percent change
            if first_count > 0:
                percent_change = (last_count - first_count) / first_count * 100
            else:
                percent_change = float('inf') if last_count > 0 else 0
            
            if percent_change > 50:  # Significant increase
                increasing_contacts.append((person, percent_change))
            elif percent_change < -50:  # Significant decrease
                decreasing_contacts.append((person, percent_change))
        
        # Sort by magnitude of change
        increasing_contacts.sort(key=lambda x: x[1], reverse=True)
        decreasing_contacts.sort(key=lambda x: x[1])
        
        # Identify new and dormant contacts
        new_contacts = []
        dormant_contacts = []
        
        # Define recent window (last 25% of time range)
        recent_cutoff = max_date - timedelta(days=days_range // 4)
        dormant_cutoff = max_date - timedelta(days=days_range // 2)
        
        for person, timestamps in person_timestamps.items():
            dates = [ts.date() for ts in timestamps]
            
            # New contacts: first communication in recent window
            first_comm = min(dates)
            if first_comm >= recent_cutoff:
                new_contacts.append(person)
            
            # Dormant contacts: no communication since dormant cutoff
            last_comm = max(dates)
            if last_comm <= dormant_cutoff:
                dormant_contacts.append(person)
        
        return {
            'trend_data': trend_data,
            'increasing_contacts': [p[0] for p in increasing_contacts[:10]],  # Top 10
            'decreasing_contacts': [p[0] for p in decreasing_contacts[:10]],  # Top 10
            'new_contacts': new_contacts,
            'dormant_contacts': dormant_contacts
        }
    
    def identify_communication_clusters(self) -> Dict[str, Any]:
        """
        Identify clusters or groups in communication patterns.
        
        Returns:
            Dictionary with communication cluster analysis results
        """
        if not self.comm_graph or self.comm_graph.graph.number_of_nodes() < 3:
            logger.warning("Insufficient communication graph data for cluster analysis")
            return {
                'clusters': [],
                'isolated_individuals': [],
                'bridge_individuals': []
            }
        
        # Convert to undirected graph for community detection
        undirected = self.comm_graph.graph.to_undirected()
        
        # Identify communities
        communities = {}
        try:
            # Try to use community detection algorithms
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(undirected)
                
                # Group by community
                for node, community_id in partition.items():
                    if community_id not in communities:
                        communities[community_id] = []
                    communities[community_id].append(node)
            except ImportError:
                # Fall back to connected components
                for i, component in enumerate(nx.connected_components(undirected)):
                    communities[i] = list(component)
        except Exception as e:
            logger.error(f"Error in community detection: {str(e)}")
            # Fall back to connected components
            for i, component in enumerate(nx.connected_components(undirected)):
                communities[i] = list(component)
        
        # Format clusters
        clusters = [{'id': i, 'members': members} for i, members in communities.items()]
        
        # Identify isolated individuals (degree 1 or 0)
        isolated = [node for node, degree in dict(undirected.degree()).items() if degree <= 1]
        
        # Identify bridge individuals (nodes that connect communities)
        bridges = []
        
        # If we have multiple communities, find bridges
        if len(communities) > 1:
            # Create a mapping of node to community
            node_to_community = {}
            for comm_id, members in communities.items():
                for member in members:
                    node_to_community[member] = comm_id
            
            # Check each node's neighbors
            for node in undirected.nodes():
                neighbor_communities = set()
                for neighbor in undirected.neighbors(node):
                    if neighbor in node_to_community:
                        neighbor_communities.add(node_to_community[neighbor])
                
                # If node connects to multiple communities, it's a bridge
                if len(neighbor_communities) > 1:
                    bridges.append(node)
        
        return {
            'clusters': clusters,
            'isolated_individuals': isolated,
            'bridge_individuals': bridges
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all communication pattern analyses.
        
        Returns:
            Dictionary with all analysis results
        """
        # Run all analyses
        frequency = self.analyze_communication_frequency(time_period='day')
        response = self.analyze_response_patterns()
        habits = self.analyze_communication_habits()
        changes = self.analyze_communication_changes()
        clusters = self.identify_communication_clusters()
        
        # Combine into comprehensive report
        report = {
            'communication_frequency': frequency,
            'response_patterns': response,
            'communication_habits': habits,
            'communication_changes': changes,
            'communication_clusters': clusters,
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
        
        logger.info(f"Communication pattern analysis report saved to {filepath}")