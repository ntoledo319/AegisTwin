"""
Communication Graph for CogniLink

This module implements a graph-based representation of communication patterns
between individuals, allowing for analysis of relationships and information flow.
"""

import networkx as nx
from typing import Dict, List, Tuple, Any, Optional, Set
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CommunicationGraph:
    """
    A graph-based representation of communication patterns.
    
    This class uses NetworkX to create and analyze a graph where:
    - Nodes represent individuals (email addresses, phone numbers, etc.)
    - Edges represent communications between individuals
    - Edge attributes store metadata about communications (frequency, sentiment, etc.)
    """
    
    def __init__(self):
        """Initialize an empty communication graph."""
        self.graph = nx.DiGraph()
        self.metadata = {
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0,
            "time_range": {"start": None, "end": None}
        }
    
    def add_communication(self, 
                         sender: str, 
                         recipients: List[str], 
                         timestamp: datetime,
                         message_id: str,
                         metadata: Dict[str, Any] = None) -> None:
        """
        Add a communication event to the graph.
        
        Args:
            sender: Identifier for the sender
            recipients: List of recipient identifiers
            timestamp: When the communication occurred
            message_id: Unique identifier for the message
            metadata: Additional information about the communication
        """
        # Add nodes if they don't exist
        if sender not in self.graph:
            self.graph.add_node(sender, type="person", first_seen=timestamp.isoformat())
        
        # Update time range
        if not self.metadata["time_range"]["start"] or timestamp < datetime.fromisoformat(self.metadata["time_range"]["start"]):
            self.metadata["time_range"]["start"] = timestamp.isoformat()
        if not self.metadata["time_range"]["end"] or timestamp > datetime.fromisoformat(self.metadata["time_range"]["end"]):
            self.metadata["time_range"]["end"] = timestamp.isoformat()
        
        # Add edges for each recipient
        for recipient in recipients:
            if recipient not in self.graph:
                self.graph.add_node(recipient, type="person", first_seen=timestamp.isoformat())
            
            # If edge already exists, update it
            if self.graph.has_edge(sender, recipient):
                self.graph[sender][recipient]["count"] += 1
                self.graph[sender][recipient]["messages"].append(message_id)
                
                # Update timestamp ranges
                if timestamp < datetime.fromisoformat(self.graph[sender][recipient]["first_comm"]):
                    self.graph[sender][recipient]["first_comm"] = timestamp.isoformat()
                if timestamp > datetime.fromisoformat(self.graph[sender][recipient]["last_comm"]):
                    self.graph[sender][recipient]["last_comm"] = timestamp.isoformat()
                
                # Update metadata if provided
                if metadata:
                    for key, value in metadata.items():
                        if key in self.graph[sender][recipient]:
                            if isinstance(self.graph[sender][recipient][key], list):
                                self.graph[sender][recipient][key].append(value)
                            else:
                                self.graph[sender][recipient][key] = [self.graph[sender][recipient][key], value]
                        else:
                            self.graph[sender][recipient][key] = value
            else:
                # Create new edge
                edge_data = {
                    "count": 1,
                    "first_comm": timestamp.isoformat(),
                    "last_comm": timestamp.isoformat(),
                    "messages": [message_id]
                }
                
                # Add any additional metadata
                if metadata:
                    edge_data.update(metadata)
                
                self.graph.add_edge(sender, recipient, **edge_data)
        
        # Update graph metadata
        self.metadata["message_count"] += 1
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def get_top_communicators(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        Get the individuals with the most outgoing communications.
        
        Args:
            n: Number of top communicators to return
            
        Returns:
            List of (person_id, message_count) tuples
        """
        # Count outgoing messages for each node
        outgoing_counts = {node: sum(data["count"] for _, _, data in self.graph.out_edges(node, data=True))
                          for node in self.graph.nodes()}
        
        # Sort by count and return top n
        return sorted(outgoing_counts.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_strongest_relationships(self, n: int = 10) -> List[Tuple[str, str, int]]:
        """
        Get the pairs with the most communications between them.
        
        Args:
            n: Number of relationships to return
            
        Returns:
            List of (person1, person2, message_count) tuples
        """
        # Get all edges with their counts
        edges_with_counts = [(u, v, data["count"]) for u, v, data in self.graph.edges(data=True)]
        
        # Sort by count and return top n
        return sorted(edges_with_counts, key=lambda x: x[2], reverse=True)[:n]
    
    def get_communities(self) -> Dict[int, Set[str]]:
        """
        Detect communities in the communication graph.
        
        Returns:
            Dictionary mapping community IDs to sets of person IDs
        """
        # Convert to undirected graph for community detection
        undirected = self.graph.to_undirected()
        
        # Use Louvain method for community detection
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(undirected)
            
            # Group by community
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = set()
                communities[community_id].add(node)
            
            return communities
        except ImportError:
            logger.warning("python-louvain package not installed. Using connected components instead.")
            # Fall back to connected components
            components = list(nx.connected_components(undirected))
            return {i: component for i, component in enumerate(components)}
    
    def get_central_figures(self, n: int = 10, method: str = "betweenness") -> List[Tuple[str, float]]:
        """
        Identify central figures in the communication network.
        
        Args:
            n: Number of central figures to return
            method: Centrality measure to use ('betweenness', 'eigenvector', or 'degree')
            
        Returns:
            List of (person_id, centrality_score) tuples
        """
        if method == "betweenness":
            centrality = nx.betweenness_centrality(self.graph)
        elif method == "eigenvector":
            centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
        elif method == "degree":
            centrality = nx.degree_centrality(self.graph)
        else:
            raise ValueError(f"Unknown centrality method: {method}")
        
        # Sort by centrality score and return top n
        return sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the communication graph to a file.
        
        Args:
            filepath: Path where the graph should be saved
        """
        # Convert graph to dictionary
        data = {
            "metadata": self.metadata,
            "nodes": list(self.graph.nodes(data=True)),
            "edges": [(u, v, d) for u, v, d in self.graph.edges(data=True)]
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Communication graph saved to {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'CommunicationGraph':
        """
        Load a communication graph from a file.
        
        Args:
            filepath: Path to the saved graph file
            
        Returns:
            CommunicationGraph instance
        """
        # Create new graph instance
        comm_graph = cls()
        
        # Load data from file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Restore metadata
        comm_graph.metadata = data["metadata"]
        
        # Restore graph
        for node, attrs in data["nodes"]:
            comm_graph.graph.add_node(node, **attrs)
        
        for u, v, attrs in data["edges"]:
            comm_graph.graph.add_edge(u, v, **attrs)
        
        logger.info(f"Communication graph loaded from {filepath}")
        return comm_graph