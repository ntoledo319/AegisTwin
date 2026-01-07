"""
Network analysis module for advanced analysis.

This module provides functionality for analyzing network structures and relationships,
including graph analysis, community detection, and centrality measures.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class NetworkAnalyzer:
    """Analyzer for network structures and relationships."""
    
    def __init__(self):
        """Initialize the network analyzer."""
        self.graph_available = False
        self.community_detection_available = False
        self.graph = None
        
        # Try to import network analysis libraries
        try:
            import networkx as nx
            self.nx = nx
            self.graph_available = True
            logger.info("NetworkX graph analysis available")
            
            # Try to import community detection
            try:
                import community
                self.community = community
                self.community_detection_available = True
                logger.info("Community detection available")
            except ImportError:
                logger.warning("Community detection not available")
                
        except ImportError:
            logger.warning("NetworkX not available for graph analysis")
    
    async def analyze(self, nodes: List[Dict[str, Any]], 
                     edges: List[Dict[str, Any]],
                     directed: bool = False) -> Dict[str, Any]:
        """
        Analyze network structure.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            directed: Whether the graph is directed
            
        Returns:
            Dictionary of network analysis results
        """
        logger.info(f"Analyzing network with {len(nodes)} nodes and {len(edges)} edges")
        
        if not self.graph_available:
            return {"error": "Graph analysis not available"}
        
        try:
            # Create graph
            if directed:
                G = self.nx.DiGraph()
            else:
                G = self.nx.Graph()
            
            # Add nodes
            for node in nodes:
                # Ensure node has an id
                if 'id' not in node:
                    logger.warning("Node missing id, skipping")
                    continue
                
                # Add node with attributes
                G.add_node(node['id'], **{k: v for k, v in node.items() if k != 'id'})
            
            # Add edges
            for edge in edges:
                # Ensure edge has source and target
                if 'source' not in edge or 'target' not in edge:
                    logger.warning("Edge missing source or target, skipping")
                    continue
                
                # Add edge with attributes
                G.add_edge(edge['source'], edge['target'], **{k: v for k, v in edge.items() if k not in ['source', 'target']})
            
            # Store graph
            self.graph = G
            
            # Basic graph statistics
            graph_stats = await self._calculate_graph_statistics(G)
            
            # Centrality measures
            centrality = await self._calculate_centrality(G)
            
            # Community detection
            communities = await self._detect_communities(G)
            
            # Path analysis
            paths = await self._analyze_paths(G)
            
            # Combine results
            results = {
                "statistics": graph_stats,
                "centrality": centrality,
                "communities": communities,
                "paths": paths
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing network: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_graph_statistics(self, G) -> Dict[str, Any]:
        """
        Calculate basic graph statistics.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of graph statistics
        """
        try:
            # Basic statistics
            node_count = G.number_of_nodes()
            edge_count = G.number_of_edges()
            
            # Density
            density = self.nx.density(G)
            
            # Check if graph is connected
            if G.is_directed():
                is_connected = self.nx.is_strongly_connected(G)
                if not is_connected:
                    is_weakly_connected = self.nx.is_weakly_connected(G)
                else:
                    is_weakly_connected = True
                
                # Number of strongly connected components
                num_components = self.nx.number_strongly_connected_components(G)
                
                # Largest strongly connected component
                largest_component = max(self.nx.strongly_connected_components(G), key=len)
                largest_component_size = len(largest_component)
                
            else:
                is_connected = self.nx.is_connected(G)
                is_weakly_connected = is_connected
                
                # Number of connected components
                num_components = self.nx.number_connected_components(G)
                
                # Largest connected component
                largest_component = max(self.nx.connected_components(G), key=len)
                largest_component_size = len(largest_component)
            
            # Average clustering coefficient
            avg_clustering = self.nx.average_clustering(G)
            
            # Average degree
            degrees = [d for _, d in G.degree()]
            avg_degree = sum(degrees) / len(degrees) if degrees else 0
            
            # Degree distribution
            degree_counts = defaultdict(int)
            for _, degree in G.degree():
                degree_counts[degree] += 1
            
            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "density": float(density),
                "is_connected": is_connected,
                "is_weakly_connected": is_weakly_connected,
                "num_components": num_components,
                "largest_component_size": largest_component_size,
                "largest_component_percentage": (largest_component_size / node_count) * 100 if node_count > 0 else 0,
                "avg_clustering": float(avg_clustering),
                "avg_degree": float(avg_degree),
                "degree_distribution": dict(degree_counts)
            }
            
        except Exception as e:
            logger.error(f"Error calculating graph statistics: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_centrality(self, G) -> Dict[str, Any]:
        """
        Calculate centrality measures.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of centrality measures
        """
        try:
            # Degree centrality
            degree_centrality = self.nx.degree_centrality(G)
            
            # In-degree and out-degree centrality for directed graphs
            if G.is_directed():
                in_degree_centrality = self.nx.in_degree_centrality(G)
                out_degree_centrality = self.nx.out_degree_centrality(G)
            else:
                in_degree_centrality = out_degree_centrality = None
            
            # Betweenness centrality
            betweenness_centrality = self.nx.betweenness_centrality(G)
            
            # Closeness centrality
            closeness_centrality = self.nx.closeness_centrality(G)
            
            # Eigenvector centrality
            try:
                eigenvector_centrality = self.nx.eigenvector_centrality(G, max_iter=1000)
            except:
                eigenvector_centrality = None
                logger.warning("Eigenvector centrality calculation failed")
            
            # PageRank
            try:
                pagerank = self.nx.pagerank(G)
            except:
                pagerank = None
                logger.warning("PageRank calculation failed")
            
            # Find most central nodes
            most_central = {}
            
            if degree_centrality:
                most_central['degree'] = max(degree_centrality.items(), key=lambda x: x[1])[0]
            
            if betweenness_centrality:
                most_central['betweenness'] = max(betweenness_centrality.items(), key=lambda x: x[1])[0]
            
            if closeness_centrality:
                most_central['closeness'] = max(closeness_centrality.items(), key=lambda x: x[1])[0]
            
            if eigenvector_centrality:
                most_central['eigenvector'] = max(eigenvector_centrality.items(), key=lambda x: x[1])[0]
            
            if pagerank:
                most_central['pagerank'] = max(pagerank.items(), key=lambda x: x[1])[0]
            
            return {
                "degree_centrality": {str(k): float(v) for k, v in degree_centrality.items()},
                "in_degree_centrality": {str(k): float(v) for k, v in in_degree_centrality.items()} if in_degree_centrality else None,
                "out_degree_centrality": {str(k): float(v) for k, v in out_degree_centrality.items()} if out_degree_centrality else None,
                "betweenness_centrality": {str(k): float(v) for k, v in betweenness_centrality.items()},
                "closeness_centrality": {str(k): float(v) for k, v in closeness_centrality.items()},
                "eigenvector_centrality": {str(k): float(v) for k, v in eigenvector_centrality.items()} if eigenvector_centrality else None,
                "pagerank": {str(k): float(v) for k, v in pagerank.items()} if pagerank else None,
                "most_central_nodes": most_central
            }
            
        except Exception as e:
            logger.error(f"Error calculating centrality: {str(e)}")
            return {"error": str(e)}
    
    async def _detect_communities(self, G) -> Dict[str, Any]:
        """
        Detect communities in the graph.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of community detection results
        """
        try:
            # If graph is directed, convert to undirected for community detection
            if G.is_directed():
                G_undirected = self.nx.Graph(G)
            else:
                G_undirected = G
            
            # Detect communities using Louvain method if available
            if self.community_detection_available:
                partition = self.community.best_partition(G_undirected)
                
                # Convert partition to community structure
                communities = defaultdict(list)
                for node, community_id in partition.items():
                    communities[community_id].append(node)
                
                # Calculate modularity
                modularity = self.community.modularity(partition, G_undirected)
                
                # Count communities
                num_communities = len(communities)
                
                # Calculate community sizes
                community_sizes = {community_id: len(nodes) for community_id, nodes in communities.items()}
                
                # Calculate average community size
                avg_community_size = sum(community_sizes.values()) / len(community_sizes) if community_sizes else 0
                
                return {
                    "algorithm": "louvain",
                    "num_communities": num_communities,
                    "modularity": float(modularity),
                    "communities": {str(k): [str(n) for n in v] for k, v in communities.items()},
                    "community_sizes": {str(k): v for k, v in community_sizes.items()},
                    "avg_community_size": float(avg_community_size),
                    "node_community": {str(k): v for k, v in partition.items()}
                }
            else:
                # Fallback to connected components
                if G.is_directed():
                    components = list(self.nx.weakly_connected_components(G))
                else:
                    components = list(self.nx.connected_components(G))
                
                # Convert components to community structure
                communities = {i: list(component) for i, component in enumerate(components)}
                
                # Count communities
                num_communities = len(communities)
                
                # Calculate community sizes
                community_sizes = {community_id: len(nodes) for community_id, nodes in communities.items()}
                
                # Calculate average community size
                avg_community_size = sum(community_sizes.values()) / len(community_sizes) if community_sizes else 0
                
                # Create node to community mapping
                node_community = {}
                for community_id, nodes in communities.items():
                    for node in nodes:
                        node_community[node] = community_id
                
                return {
                    "algorithm": "connected_components",
                    "num_communities": num_communities,
                    "communities": {str(k): [str(n) for n in v] for k, v in communities.items()},
                    "community_sizes": {str(k): v for k, v in community_sizes.items()},
                    "avg_community_size": float(avg_community_size),
                    "node_community": {str(k): v for k, v in node_community.items()}
                }
                
        except Exception as e:
            logger.error(f"Error detecting communities: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_paths(self, G) -> Dict[str, Any]:
        """
        Analyze paths in the graph.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of path analysis results
        """
        try:
            # Check if graph is connected
            if G.is_directed():
                is_connected = self.nx.is_strongly_connected(G)
            else:
                is_connected = self.nx.is_connected(G)
            
            # If graph is not connected, use largest component
            if not is_connected:
                if G.is_directed():
                    largest_component = max(self.nx.strongly_connected_components(G), key=len)
                else:
                    largest_component = max(self.nx.connected_components(G), key=len)
                
                G_connected = G.subgraph(largest_component).copy()
            else:
                G_connected = G
            
            # Calculate diameter
            try:
                diameter = self.nx.diameter(G_connected)
            except:
                diameter = None
                logger.warning("Diameter calculation failed")
            
            # Calculate average shortest path length
            try:
                avg_path_length = self.nx.average_shortest_path_length(G_connected)
            except:
                avg_path_length = None
                logger.warning("Average shortest path length calculation failed")
            
            # Calculate eccentricity
            try:
                eccentricity = self.nx.eccentricity(G_connected)
                radius = self.nx.radius(G_connected)
                center = self.nx.center(G_connected)
                periphery = self.nx.periphery(G_connected)
            except:
                eccentricity = radius = center = periphery = None
                logger.warning("Eccentricity calculation failed")
            
            return {
                "diameter": int(diameter) if diameter is not None else None,
                "avg_path_length": float(avg_path_length) if avg_path_length is not None else None,
                "radius": int(radius) if radius is not None else None,
                "eccentricity": {str(k): int(v) for k, v in eccentricity.items()} if eccentricity else None,
                "center": [str(n) for n in center] if center else None,
                "periphery": [str(n) for n in periphery] if periphery else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing paths: {str(e)}")
            return {"error": str(e)}
    
    async def find_shortest_path(self, source: Any, target: Any) -> Dict[str, Any]:
        """
        Find shortest path between two nodes.
        
        Args:
            source: Source node
            target: Target node
            
        Returns:
            Dictionary with shortest path information
        """
        if not self.graph_available or self.graph is None:
            return {"error": "Graph not available"}
        
        try:
            # Check if nodes exist
            if source not in self.graph.nodes or target not in self.graph.nodes:
                return {"error": "Source or target node not found in graph"}
            
            # Find shortest path
            try:
                path = self.nx.shortest_path(self.graph, source=source, target=target)
                path_length = len(path) - 1
                
                # Get edge attributes along path
                edges = []
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    edge_data = self.graph.get_edge_data(u, v)
                    edges.append({
                        "source": str(u),
                        "target": str(v),
                        "attributes": edge_data
                    })
                
                return {
                    "path": [str(n) for n in path],
                    "length": path_length,
                    "edges": edges
                }
            except self.nx.NetworkXNoPath:
                return {"error": "No path exists between source and target"}
                
        except Exception as e:
            logger.error(f"Error finding shortest path: {str(e)}")
            return {"error": str(e)}
    
    async def find_all_paths(self, source: Any, target: Any, cutoff: int = 3) -> Dict[str, Any]:
        """
        Find all paths between two nodes up to a cutoff length.
        
        Args:
            source: Source node
            target: Target node
            cutoff: Maximum path length
            
        Returns:
            Dictionary with all paths information
        """
        if not self.graph_available or self.graph is None:
            return {"error": "Graph not available"}
        
        try:
            # Check if nodes exist
            if source not in self.graph.nodes or target not in self.graph.nodes:
                return {"error": "Source or target node not found in graph"}
            
            # Find all paths
            try:
                all_paths = list(self.nx.all_simple_paths(self.graph, source=source, target=target, cutoff=cutoff))
                
                # Format paths
                formatted_paths = []
                for path in all_paths:
                    # Get edge attributes along path
                    edges = []
                    for i in range(len(path) - 1):
                        u, v = path[i], path[i+1]
                        edge_data = self.graph.get_edge_data(u, v)
                        edges.append({
                            "source": str(u),
                            "target": str(v),
                            "attributes": edge_data
                        })
                    
                    formatted_paths.append({
                        "path": [str(n) for n in path],
                        "length": len(path) - 1,
                        "edges": edges
                    })
                
                return {
                    "paths": formatted_paths,
                    "count": len(formatted_paths)
                }
            except self.nx.NetworkXNoPath:
                return {"error": "No path exists between source and target"}
                
        except Exception as e:
            logger.error(f"Error finding all paths: {str(e)}")
            return {"error": str(e)}
    
    async def get_node_neighbors(self, node: Any) -> Dict[str, Any]:
        """
        Get neighbors of a node.
        
        Args:
            node: Node to get neighbors for
            
        Returns:
            Dictionary with neighbor information
        """
        if not self.graph_available or self.graph is None:
            return {"error": "Graph not available"}
        
        try:
            # Check if node exists
            if node not in self.graph.nodes:
                return {"error": "Node not found in graph"}
            
            # Get neighbors
            neighbors = list(self.graph.neighbors(node))
            
            # Get edge attributes
            edges = []
            for neighbor in neighbors:
                edge_data = self.graph.get_edge_data(node, neighbor)
                edges.append({
                    "source": str(node),
                    "target": str(neighbor),
                    "attributes": edge_data
                })
            
            return {
                "node": str(node),
                "neighbors": [str(n) for n in neighbors],
                "count": len(neighbors),
                "edges": edges
            }
                
        except Exception as e:
            logger.error(f"Error getting node neighbors: {str(e)}")
            return {"error": str(e)}