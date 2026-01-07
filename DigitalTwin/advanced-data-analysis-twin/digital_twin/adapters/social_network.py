"""
Social Network Adapter for the Digital Twin.

This module provides an adapter for integrating ATLAS's SocialNetworkAnalyzer
with the Digital Twin system for social network analysis and connection recommendations.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class ConnectionRecommendation:
    """Data class for connection recommendations."""
    target_user_id: str
    score: float
    reasoning: str
    mutual_connections: int
    shared_interests: List[str] = None
    shared_communities: List[str] = None
    confidence: float = 0.0


@dataclass
class SocialMetrics:
    """Data class for social network metrics."""
    centrality_score: float
    influence_score: float
    community_bridges: int
    network_reach: int
    engagement_coefficient: float


class SocialNetworkAdapter:
    """
    Social network adapter for the Digital Twin.
    
    Provides social network analysis and connection recommendations based on
    user relationships, interests, and communities. Adapts ATLAS's SocialNetworkAnalyzer
    for use with the Digital Twin system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the social network adapter.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.graph = None
        self.community_graph = None
        self.user_features = {}
        
        # Algorithm parameters
        self.recommendation_params = {
            'max_recommendations': self.config.get('max_recommendations', 20),
            'min_confidence': self.config.get('min_confidence', 0.3),
            'weight_mutual_connections': self.config.get('weight_mutual_connections', 0.4),
            'weight_shared_interests': self.config.get('weight_shared_interests', 0.3),
            'weight_community_overlap': self.config.get('weight_community_overlap', 0.2),
            'weight_activity_similarity': self.config.get('weight_activity_similarity', 0.1),
            'weight_personality_compatibility': self.config.get('weight_personality_compatibility', 0.2)
        }
        
        # Initialize NetworkX if available
        try:
            import networkx as nx
            self.graph = nx.Graph()
            self.community_graph = nx.Graph()
            self.nx = nx
            logger.info("NetworkX initialized for social graph analysis")
        except ImportError:
            logger.warning("NetworkX not available, using fallback graph implementation")
            self.graph = self._create_fallback_graph()
            self.community_graph = self._create_fallback_graph()
        
        # Caching for performance
        self._centrality_cache = {}
        self._community_cache = {}
        self._last_graph_update = None
        
        logger.info("Social Network Adapter initialized")

    def update_social_graph(self, connections: List[Dict[str, Any]], 
                          user_profiles: List[Dict[str, Any]],
                          community_memberships: List[Dict[str, Any]]) -> None:
        """
        Update the social graph with latest connection and user data.

        Args:
            connections: List of connection records with user IDs and metadata
            user_profiles: List of user profile data with interests and traits
            community_memberships: List of community membership records
        """
        try:
            # Clear existing graph
            if hasattr(self.graph, 'clear'):
                self.graph.clear()
                self.community_graph.clear()
            else:
                self.graph = self._create_fallback_graph()
                self.community_graph = self._create_fallback_graph()
                
            self.user_features.clear()
            
            # Build user feature profiles
            for profile in user_profiles:
                user_id = profile['user_id']
                self.user_features[user_id] = {
                    'interests': profile.get('interests', []),
                    'traits': profile.get('traits', {}),
                    'personality': profile.get('personality', {}),
                    'communities': [],
                    'activity_score': profile.get('activity_score', 0.0),
                    'reputation_score': profile.get('reputation_score', 0.0),
                    'location': profile.get('location', ''),
                    'created_at': profile.get('created_at')
                }
                
                # Add node to graph
                if hasattr(self.graph, 'add_node'):
                    self.graph.add_node(user_id, **self.user_features[user_id])
                else:
                    self._add_node_to_fallback(self.graph, user_id, self.user_features[user_id])
            
            # Add community memberships to user features
            for membership in community_memberships:
                user_id = membership['user_id']
                community_id = membership['community_id']
                if user_id in self.user_features:
                    self.user_features[user_id]['communities'].append(community_id)
            
            # Build connection edges
            for connection in connections:
                if connection['status'] == 'accepted':
                    user1 = connection['requester_id']
                    user2 = connection['target_id']
                    
                    # Calculate edge weight based on interaction strength
                    weight = self._calculate_connection_strength(connection)
                    
                    # Add edge to graph
                    if hasattr(self.graph, 'add_edge'):
                        self.graph.add_edge(user1, user2, 
                                         weight=weight,
                                         created_at=connection.get('created_at'),
                                         interaction_count=connection.get('interaction_count', 0))
                    else:
                        self._add_edge_to_fallback(self.graph, user1, user2, {
                            'weight': weight,
                            'created_at': connection.get('created_at'),
                            'interaction_count': connection.get('interaction_count', 0)
                        })
            
            # Build community co-membership graph
            self._build_community_graph(community_memberships)
            
            # Clear caches
            self._centrality_cache = {}
            self._community_cache = {}
            self._last_graph_update = datetime.now()
            
            logger.info(f"Social graph updated: {self._count_nodes()} users, "
                       f"{self._count_edges()} connections")
                       
        except Exception as e:
            logger.error(f"Error updating social graph: {e}")
            raise

    def generate_connection_recommendations(self, user_id: str, 
                                          personality_profile: Dict[str, Any],
                                          limit: int = 10,
                                          exclude_existing: bool = True) -> List[ConnectionRecommendation]:
        """
        Generate personalized connection recommendations for a user.

        Args:
            user_id: Target user ID for recommendations
            personality_profile: User's personality profile
            limit: Maximum number of recommendations to return
            exclude_existing: Whether to exclude existing connections

        Returns:
            List of connection recommendations sorted by relevance score
        """
        try:
            if not self._has_node(user_id):
                logger.warning(f"User {user_id} not found in social graph")
                return []
            
            recommendations = []
            
            # Update user features with personality profile if not already present
            if user_id in self.user_features and 'personality' not in self.user_features[user_id]:
                self.user_features[user_id]['personality'] = personality_profile
            
            # Get existing connections to exclude
            existing_connections = set(self._get_neighbors(user_id)) if exclude_existing else set()
            existing_connections.add(user_id)  # Exclude self
            
            # Generate candidates from multiple sources
            candidates = self._get_recommendation_candidates(user_id, existing_connections)
            
            # Score each candidate
            for candidate_id in candidates:
                score_data = self._calculate_recommendation_score(
                    user_id, candidate_id, personality_profile
                )
                
                if score_data['score'] >= self.recommendation_params['min_confidence']:
                    recommendation = ConnectionRecommendation(
                        target_user_id=candidate_id,
                        score=score_data['score'],
                        reasoning=score_data['reasoning'],
                        mutual_connections=score_data['mutual_connections'],
                        shared_interests=score_data['shared_interests'],
                        shared_communities=score_data['shared_communities'],
                        confidence=score_data['confidence']
                    )
                    recommendations.append(recommendation)
            
            # Sort by score and limit results
            recommendations.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} connection recommendations for user {user_id}")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating connection recommendations: {e}")
            return []

    def analyze_user_social_metrics(self, user_id: str) -> Optional[SocialMetrics]:
        """
        Analyze comprehensive social metrics for a user.

        Args:
            user_id: User ID to analyze

        Returns:
            SocialMetrics object with detailed network analysis
        """
        try:
            if not self._has_node(user_id):
                return None
            
            # Calculate centrality measures
            centrality_scores = self._get_centrality_scores()
            
            # Betweenness centrality (bridge connections)
            betweenness = centrality_scores.get('betweenness', {}).get(user_id, 0.0)
            
            # Degree centrality (direct connections)
            degree = centrality_scores.get('degree', {}).get(user_id, 0.0)
            
            # PageRank (influence score)
            pagerank = centrality_scores.get('pagerank', {}).get(user_id, 0.0)
            
            # Calculate network reach (2-hop connections)
            network_reach = len(self._get_n_hop_neighbors(user_id, 2)) - 1  # Exclude self
            
            # Community bridges (how many communities user connects)
            user_communities = set(self.user_features.get(user_id, {}).get('communities', []))
            community_bridges = len(user_communities)
            
            # Engagement coefficient based on interaction patterns
            engagement_coefficient = self._calculate_engagement_coefficient(user_id)
            
            # Overall centrality score (weighted combination)
            centrality_score = (0.4 * degree + 0.3 * pagerank + 0.3 * betweenness)
            
            return SocialMetrics(
                centrality_score=centrality_score,
                influence_score=pagerank,
                community_bridges=community_bridges,
                network_reach=network_reach,
                engagement_coefficient=engagement_coefficient
            )
            
        except Exception as e:
            logger.error(f"Error analyzing social metrics for user {user_id}: {e}")
            return None

    def detect_communities(self, resolution: float = 1.0) -> Dict[str, List[str]]:
        """
        Detect communities in the social network.

        Args:
            resolution: Resolution parameter for community detection

        Returns:
            Dictionary mapping community IDs to lists of user IDs
        """
        try:
            if self._count_nodes() == 0:
                return {}
            
            # Check if NetworkX is available
            if hasattr(self.nx, 'community'):
                # Use Louvain algorithm for community detection
                communities = self.nx.community.louvain_communities(self.graph, resolution=resolution)
                
                # Convert to dictionary format
                community_dict = {}
                for i, community in enumerate(communities):
                    community_dict[f"community_{i}"] = list(community)
                
                logger.info(f"Detected {len(community_dict)} communities")
                return community_dict
            else:
                # Fallback to basic community detection
                return self._basic_community_detection()
            
        except Exception as e:
            logger.error(f"Error detecting communities: {e}")
            return {}

    def calculate_network_health_score(self) -> float:
        """
        Calculate overall network health score based on connectivity and engagement.

        Returns:
            Network health score between 0.0 and 1.0
        """
        try:
            if self._count_nodes() < 2:
                return 0.0
            
            # Check if NetworkX is available
            if hasattr(self.nx, 'density'):
                # Connectivity metrics
                density = self.nx.density(self.graph)
                
                # Check if graph is connected
                if self.nx.is_connected(self.graph):
                    connectivity_score = 1.0
                else:
                    # Use largest connected component size ratio
                    largest_cc = max(self.nx.connected_components(self.graph), key=len)
                    connectivity_score = len(largest_cc) / self._count_nodes()
                
                # Average clustering coefficient
                clustering = self.nx.average_clustering(self.graph)
                
                # Activity distribution (how evenly distributed are connections)
                degrees = [d for n, d in self.graph.degree()]
                degree_variance = np.var(degrees) if degrees else 0
                max_possible_variance = (self._count_nodes() - 1) ** 2 / 4
                degree_evenness = 1.0 - (degree_variance / max_possible_variance) if max_possible_variance > 0 else 1.0
            else:
                # Fallback metrics
                density = self._calculate_fallback_density()
                connectivity_score = self._calculate_fallback_connectivity()
                clustering = 0.5  # Default value
                degree_evenness = 0.5  # Default value
            
            # Weighted health score
            health_score = (
                0.3 * connectivity_score +
                0.2 * min(density * 10, 1.0) +  # Scale density to reasonable range
                0.3 * clustering +
                0.2 * degree_evenness
            )
            
            return min(max(health_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating network health score: {e}")
            return 0.0

    def find_influential_users(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Find most influential users in the network.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of tuples (user_id, influence_score)
        """
        try:
            centrality_scores = self._get_centrality_scores()
            pagerank_scores = centrality_scores.get('pagerank', {})
            
            # Sort by PageRank score
            influential_users = sorted(pagerank_scores.items(), 
                                    key=lambda x: x[1], reverse=True)
            
            return influential_users[:limit]
            
        except Exception as e:
            logger.error(f"Error finding influential users: {e}")
            return []

    def predict_connection_probability(self, user1: str, user2: str, 
                                     personality_profile1: Dict[str, Any] = None,
                                     personality_profile2: Dict[str, Any] = None) -> float:
        """
        Predict probability of connection between two users.

        Args:
            user1: First user ID
            user2: Second user ID
            personality_profile1: First user's personality profile (optional)
            personality_profile2: Second user's personality profile (optional)

        Returns:
            Probability score between 0.0 and 1.0
        """
        try:
            if not self._has_node(user1) or not self._has_node(user2):
                return 0.0
            
            if self._has_edge(user1, user2):
                return 1.0  # Already connected
            
            # Calculate features for prediction
            features = self._extract_connection_features(user1, user2)
            
            # Simple scoring based on multiple factors
            score = 0.0
            
            # Mutual connections (preferential attachment)
            mutual_neighbors = len(list(self._get_common_neighbors(user1, user2)))
            
            user1_degree = self._get_degree(user1)
            user2_degree = self._get_degree(user2)
            
            if user1_degree > 0 and user2_degree > 0:
                jaccard_coefficient = mutual_neighbors / (
                    user1_degree + user2_degree - mutual_neighbors
                )
                score += 0.4 * jaccard_coefficient
            
            # Shared interests/communities
            user1_features = self.user_features.get(user1, {})
            user2_features = self.user_features.get(user2, {})
            
            # Interest similarity
            interests1 = set(user1_features.get('interests', []))
            interests2 = set(user2_features.get('interests', []))
            if interests1 and interests2:
                interest_similarity = len(interests1 & interests2) / len(interests1 | interests2)
                score += 0.3 * interest_similarity
            
            # Community overlap
            communities1 = set(user1_features.get('communities', []))
            communities2 = set(user2_features.get('communities', []))
            if communities1 and communities2:
                community_overlap = len(communities1 & communities2) / len(communities1 | communities2)
                score += 0.3 * community_overlap
            
            # Personality compatibility (if profiles provided)
            if personality_profile1 and personality_profile2:
                compatibility = self._calculate_personality_compatibility(
                    personality_profile1, personality_profile2
                )
                score += 0.2 * compatibility
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error predicting connection probability: {e}")
            return 0.0

    # Private helper methods
    def _calculate_connection_strength(self, connection: Dict[str, Any]) -> float:
        """Calculate connection strength based on interaction data."""
        base_weight = 1.0
        interaction_count = connection.get('interaction_count', 0)
        
        # Weight based on interaction frequency
        interaction_weight = min(interaction_count / 10.0, 2.0)  # Cap at 2x
        
        return base_weight + interaction_weight

    def _build_community_graph(self, memberships: List[Dict[str, Any]]) -> None:
        """Build a graph of community co-memberships."""
        community_members = defaultdict(list)
        
        # Group users by community
        for membership in memberships:
            community_members[membership['community_id']].append(membership['user_id'])
        
        # Create edges between users in same communities
        for community_id, members in community_members.items():
            for i, user1 in enumerate(members):
                for user2 in members[i+1:]:
                    if self._has_edge(user1, user2, graph='community'):
                        # Update existing edge
                        edge_data = self._get_edge_data(user1, user2, graph='community')
                        edge_data['weight'] += 1
                        if 'communities' in edge_data:
                            edge_data['communities'].append(community_id)
                        else:
                            edge_data['communities'] = [community_id]
                    else:
                        # Add new edge
                        if hasattr(self.community_graph, 'add_edge'):
                            self.community_graph.add_edge(user1, user2, 
                                                       weight=1, 
                                                       communities=[community_id])
                        else:
                            self._add_edge_to_fallback(self.community_graph, user1, user2, {
                                'weight': 1,
                                'communities': [community_id]
                            })

    def _get_recommendation_candidates(self, user_id: str, exclude: Set[str]) -> Set[str]:
        """Get candidate users for recommendations."""
        candidates = set()
        
        # Friend-of-friend recommendations
        for neighbor in self._get_neighbors(user_id):
            for friend_of_friend in self._get_neighbors(neighbor):
                if friend_of_friend not in exclude:
                    candidates.add(friend_of_friend)
        
        # Community-based recommendations
        user_communities = self.user_features.get(user_id, {}).get('communities', [])
        for community_id in user_communities:
            for other_user, features in self.user_features.items():
                if (other_user not in exclude and 
                    community_id in features.get('communities', [])):
                    candidates.add(other_user)
        
        # Interest-based recommendations
        user_interests = set(self.user_features.get(user_id, {}).get('interests', []))
        if user_interests:
            for other_user, features in self.user_features.items():
                if other_user not in exclude:
                    other_interests = set(features.get('interests', []))
                    if user_interests & other_interests:  # Has shared interests
                        candidates.add(other_user)
        
        return candidates

    def _calculate_recommendation_score(self, user_id: str, candidate_id: str,
                                      personality_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate recommendation score for a candidate."""
        user_features = self.user_features.get(user_id, {})
        candidate_features = self.user_features.get(candidate_id, {})
        
        # Mutual connections
        mutual_connections = len(list(self._get_common_neighbors(user_id, candidate_id)))
        mutual_score = min(mutual_connections / 5.0, 1.0)  # Normalize
        
        # Shared interests
        user_interests = set(user_features.get('interests', []))
        candidate_interests = set(candidate_features.get('interests', []))
        shared_interests = list(user_interests & candidate_interests)
        interest_score = len(shared_interests) / max(len(user_interests | candidate_interests), 1)
        
        # Shared communities
        user_communities = set(user_features.get('communities', []))
        candidate_communities = set(candidate_features.get('communities', []))
        shared_communities = list(user_communities & candidate_communities)
        community_score = len(shared_communities) / max(len(user_communities | candidate_communities), 1)
        
        # Activity similarity
        user_activity = user_features.get('activity_score', 0.0)
        candidate_activity = candidate_features.get('activity_score', 0.0)
        activity_similarity = 1.0 - abs(user_activity - candidate_activity) / max(user_activity + candidate_activity, 1.0)
        
        # Personality compatibility
        personality_compatibility = 0.5  # Default value
        if personality_profile:
            candidate_personality = candidate_features.get('personality', {})
            if candidate_personality:
                personality_compatibility = self._calculate_personality_compatibility(
                    personality_profile, candidate_personality
                )
        
        # Weighted final score
        params = self.recommendation_params
        final_score = (
            params['weight_mutual_connections'] * mutual_score +
            params['weight_shared_interests'] * interest_score +
            params['weight_community_overlap'] * community_score +
            params['weight_activity_similarity'] * activity_similarity +
            params['weight_personality_compatibility'] * personality_compatibility
        )
        
        # Generate reasoning
        reasons = []
        if mutual_connections > 0:
            reasons.append(f"{mutual_connections} mutual connection(s)")
        if shared_interests:
            reasons.append(f"shared interests: {', '.join(shared_interests[:3])}")
        if shared_communities:
            reasons.append(f"shared communities: {len(shared_communities)}")
        if personality_compatibility > 0.7:
            reasons.append("high personality compatibility")
        
        reasoning = "Recommended based on " + ", ".join(reasons) if reasons else "Recommended based on network analysis"
        
        return {
            'score': final_score,
            'confidence': min(final_score * 1.2, 1.0),
            'reasoning': reasoning,
            'mutual_connections': mutual_connections,
            'shared_interests': shared_interests,
            'shared_communities': shared_communities
        }

    def _calculate_personality_compatibility(self, profile1: Dict[str, Any], 
                                          profile2: Dict[str, Any]) -> float:
        """
        Calculate personality compatibility between two users.
        
        Uses the Big Five personality traits to determine compatibility.
        """
        try:
            # Extract dimensions
            dimensions1 = profile1.get('dimensions', {})
            dimensions2 = profile2.get('dimensions', {})
            
            if not dimensions1 or not dimensions2:
                return 0.5  # Default compatibility
            
            # Extract Big Five traits
            openness1 = dimensions1.get('openness', 0.5)
            conscientiousness1 = dimensions1.get('conscientiousness', 0.5)
            extraversion1 = dimensions1.get('extraversion', 0.5)
            agreeableness1 = dimensions1.get('agreeableness', 0.5)
            neuroticism1 = dimensions1.get('neuroticism', 0.5)
            
            openness2 = dimensions2.get('openness', 0.5)
            conscientiousness2 = dimensions2.get('conscientiousness', 0.5)
            extraversion2 = dimensions2.get('extraversion', 0.5)
            agreeableness2 = dimensions2.get('agreeableness', 0.5)
            neuroticism2 = dimensions2.get('neuroticism', 0.5)
            
            # Calculate compatibility scores
            
            # Openness: Similar levels are compatible
            openness_compat = 1.0 - abs(openness1 - openness2)
            
            # Conscientiousness: Similar levels are compatible
            conscientiousness_compat = 1.0 - abs(conscientiousness1 - conscientiousness2)
            
            # Extraversion: Complementary levels can be compatible
            # (extraverts can pair well with introverts)
            extraversion_diff = abs(extraversion1 - extraversion2)
            extraversion_compat = 1.0 - min(extraversion_diff, 1.0 - extraversion_diff)
            
            # Agreeableness: Higher levels are generally more compatible
            agreeableness_compat = (agreeableness1 + agreeableness2) / 2.0
            
            # Neuroticism: Lower levels are generally more compatible
            neuroticism_compat = 1.0 - (neuroticism1 + neuroticism2) / 2.0
            
            # Weighted compatibility score
            compatibility = (
                0.2 * openness_compat +
                0.2 * conscientiousness_compat +
                0.2 * extraversion_compat +
                0.2 * agreeableness_compat +
                0.2 * neuroticism_compat
            )
            
            return compatibility
            
        except Exception as e:
            logger.error(f"Error calculating personality compatibility: {e}")
            return 0.5  # Default compatibility

    def _calculate_engagement_coefficient(self, user_id: str) -> float:
        """Calculate engagement coefficient based on interaction patterns."""
        try:
            if not self._has_node(user_id):
                return 0.0
            
            # Get edges connected to user
            if hasattr(self.graph, 'edges'):
                edges = self.graph.edges(user_id, data=True)
                
                if not edges:
                    return 0.0
                
                # Calculate average interaction count
                total_interactions = sum(edge_data.get('interaction_count', 0) for _, _, edge_data in edges)
                avg_interactions = total_interactions / len(edges)
                
                # Normalize to 0-1 scale
                engagement = min(avg_interactions / 10.0, 1.0)
                
                return engagement
            else:
                # Fallback for custom graph implementation
                neighbors = self._get_neighbors(user_id)
                
                if not neighbors:
                    return 0.0
                
                total_interactions = 0
                for neighbor in neighbors:
                    edge_data = self._get_edge_data(user_id, neighbor)
                    total_interactions += edge_data.get('interaction_count', 0)
                
                avg_interactions = total_interactions / len(neighbors)
                
                # Normalize to 0-1 scale
                engagement = min(avg_interactions / 10.0, 1.0)
                
                return engagement
                
        except Exception as e:
            logger.error(f"Error calculating engagement coefficient: {e}")
            return 0.0

    def _get_centrality_scores(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate centrality scores for all users in the graph.
        
        Returns a dictionary with different centrality measures.
        """
        # Check if cached results are available
        if self._centrality_cache and self._last_graph_update:
            return self._centrality_cache
        
        centrality_scores = {
            'degree': {},
            'betweenness': {},
            'pagerank': {}
        }
        
        try:
            # Check if NetworkX is available
            if hasattr(self.nx, 'degree_centrality'):
                # Calculate degree centrality
                centrality_scores['degree'] = self.nx.degree_centrality(self.graph)
                
                # Calculate betweenness centrality (can be slow for large graphs)
                if self._count_nodes() < 1000:  # Only for smaller graphs
                    centrality_scores['betweenness'] = self.nx.betweenness_centrality(self.graph)
                else:
                    # Approximate betweenness for large graphs
                    centrality_scores['betweenness'] = self.nx.betweenness_centrality(
                        self.graph, k=min(100, self._count_nodes() // 10)
                    )
                
                # Calculate PageRank
                centrality_scores['pagerank'] = self.nx.pagerank(self.graph)
            else:
                # Fallback centrality calculations
                centrality_scores['degree'] = self._calculate_fallback_degree_centrality()
                centrality_scores['betweenness'] = {}  # Skip betweenness (too complex for fallback)
                centrality_scores['pagerank'] = self._calculate_fallback_pagerank()
        except Exception as e:
            logger.error(f"Error calculating centrality scores: {e}")
        
        # Cache the results
        self._centrality_cache = centrality_scores
        
        return centrality_scores

    def _extract_connection_features(self, user1: str, user2: str) -> Dict[str, Any]:
        """Extract features for connection prediction."""
        features = {}
        
        # Mutual connections
        features['mutual_connections'] = len(list(self._get_common_neighbors(user1, user2)))
        
        # User features
        user1_features = self.user_features.get(user1, {})
        user2_features = self.user_features.get(user2, {})
        
        # Shared interests
        user1_interests = set(user1_features.get('interests', []))
        user2_interests = set(user2_features.get('interests', []))
        features['shared_interests'] = len(user1_interests & user2_interests)
        features['total_interests'] = len(user1_interests | user2_interests)
        
        # Shared communities
        user1_communities = set(user1_features.get('communities', []))
        user2_communities = set(user2_features.get('communities', []))
        features['shared_communities'] = len(user1_communities & user2_communities)
        features['total_communities'] = len(user1_communities | user2_communities)
        
        # Activity scores
        features['user1_activity'] = user1_features.get('activity_score', 0.0)
        features['user2_activity'] = user2_features.get('activity_score', 0.0)
        
        return features

    # Graph utility methods for fallback implementation
    def _create_fallback_graph(self):
        """Create a fallback graph implementation when NetworkX is not available."""
        return {
            'nodes': {},
            'edges': {}
        }

    def _add_node_to_fallback(self, graph, node_id, attributes=None):
        """Add a node to the fallback graph."""
        graph['nodes'][node_id] = attributes or {}

    def _add_edge_to_fallback(self, graph, node1, node2, attributes=None):
        """Add an edge to the fallback graph."""
        if node1 not in graph['edges']:
            graph['edges'][node1] = {}
        if node2 not in graph['edges']:
            graph['edges'][node2] = {}
        
        graph['edges'][node1][node2] = attributes or {}
        graph['edges'][node2][node1] = attributes or {}  # Undirected graph

    def _has_node(self, node_id, graph='main'):
        """Check if a node exists in the graph."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'has_node'):
            return g.has_node(node_id)
        else:
            return node_id in g['nodes']

    def _has_edge(self, node1, node2, graph='main'):
        """Check if an edge exists in the graph."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'has_edge'):
            return g.has_edge(node1, node2)
        else:
            return node1 in g['edges'] and node2 in g['edges'][node1]

    def _get_neighbors(self, node_id, graph='main'):
        """Get neighbors of a node."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'neighbors'):
            return g.neighbors(node_id)
        else:
            return g['edges'].get(node_id, {}).keys()

    def _get_edge_data(self, node1, node2, graph='main'):
        """Get edge data between two nodes."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'get_edge_data'):
            return g.get_edge_data(node1, node2) or {}
        else:
            if node1 in g['edges'] and node2 in g['edges'][node1]:
                return g['edges'][node1][node2]
            return {}

    def _get_common_neighbors(self, node1, node2, graph='main'):
        """Get common neighbors between two nodes."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'common_neighbors'):
            return g.common_neighbors(node1, node2)
        else:
            neighbors1 = set(self._get_neighbors(node1, graph))
            neighbors2 = set(self._get_neighbors(node2, graph))
            return neighbors1.intersection(neighbors2)

    def _get_degree(self, node_id, graph='main'):
        """Get degree of a node."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'degree'):
            return g.degree(node_id)
        else:
            return len(g['edges'].get(node_id, {}))

    def _count_nodes(self, graph='main'):
        """Count nodes in the graph."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'number_of_nodes'):
            return g.number_of_nodes()
        else:
            return len(g['nodes'])

    def _count_edges(self, graph='main'):
        """Count edges in the graph."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(g, 'number_of_edges'):
            return g.number_of_edges()
        else:
            count = 0
            for node in g['edges']:
                count += len(g['edges'][node])
            return count // 2  # Divide by 2 because each edge is counted twice in undirected graph

    def _get_n_hop_neighbors(self, node_id, n, graph='main'):
        """Get n-hop neighbors of a node."""
        g = self.graph if graph == 'main' else self.community_graph
        
        if hasattr(self.nx, 'single_source_shortest_path_length'):
            return self.nx.single_source_shortest_path_length(g, node_id, cutoff=n)
        else:
            # Breadth-first search implementation
            visited = {node_id: 0}
            current_level = [node_id]
            
            for i in range(1, n + 1):
                next_level = []
                for node in current_level:
                    for neighbor in self._get_neighbors(node, graph):
                        if neighbor not in visited:
                            visited[neighbor] = i
                            next_level.append(neighbor)
                current_level = next_level
                
            return visited

    def _calculate_fallback_degree_centrality(self):
        """Calculate degree centrality without NetworkX."""
        centrality = {}
        n = self._count_nodes() - 1  # Normalize by n-1
        
        if n == 0:
            return centrality
            
        for node in self.graph['nodes']:
            centrality[node] = self._get_degree(node) / n
            
        return centrality

    def _calculate_fallback_pagerank(self):
        """Calculate a simple approximation of PageRank without NetworkX."""
        pagerank = {}
        nodes = list(self.graph['nodes'].keys())
        n = len(nodes)
        
        if n == 0:
            return pagerank
            
        # Initialize with equal probabilities
        for node in nodes:
            pagerank[node] = 1.0 / n
            
        # Simple iterative approximation (5 iterations)
        damping = 0.85
        for _ in range(5):
            new_pagerank = {}
            for node in nodes:
                new_pagerank[node] = (1 - damping) / n
                
                # Add contribution from neighbors
                neighbors = list(self._get_neighbors(node))
                for neighbor in neighbors:
                    if neighbors:  # Avoid division by zero
                        new_pagerank[node] += damping * pagerank[neighbor] / self._get_degree(neighbor)
                        
            pagerank = new_pagerank
            
        return pagerank

    def _calculate_fallback_density(self):
        """Calculate graph density without NetworkX."""
        n = self._count_nodes()
        m = self._count_edges()
        
        if n <= 1:
            return 0.0
            
        return (2 * m) / (n * (n - 1))

    def _calculate_fallback_connectivity(self):
        """Calculate a simple connectivity score without NetworkX."""
        # Use a simple BFS to find the largest connected component
        nodes = list(self.graph['nodes'].keys())
        if not nodes:
            return 0.0
            
        visited = set()
        largest_component = 0
        
        for node in nodes:
            if node not in visited:
                # Start BFS from this node
                component = set()
                queue = [node]
                visited.add(node)
                component.add(node)
                
                while queue:
                    current = queue.pop(0)
                    for neighbor in self._get_neighbors(current):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
                
                largest_component = max(largest_component, len(component))
        
        return largest_component / len(nodes)

    def _basic_community_detection(self):
        """Basic community detection without NetworkX."""
        communities = {}
        nodes = list(self.graph['nodes'].keys())
        
        if not nodes:
            return communities
            
        # Simple clustering based on shared connections
        visited = set()
        community_id = 0
        
        for node in nodes:
            if node not in visited:
                # Start a new community
                community = []
                queue = [node]
                visited.add(node)
                
                while queue:
                    current = queue.pop(0)
                    community.append(current)
                    
                    # Add neighbors with high connection strength
                    for neighbor in self._get_neighbors(current):
                        if neighbor not in visited:
                            edge_data = self._get_edge_data(current, neighbor)
                            if edge_data.get('weight', 1.0) > 1.5:  # Strong connection
                                visited.add(neighbor)
                                queue.append(neighbor)
                
                if community:
                    communities[f"community_{community_id}"] = community
                    community_id += 1
        
        return communities