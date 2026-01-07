"""
Recommendation Engine Adapter for the Digital Twin.

This module provides an adapter for integrating ATLAS's ContentRecommendationEngine
with the Digital Twin system for personalized content recommendations.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class ContentRecommendation:
    """Data class for content recommendations."""
    content_id: str
    content_type: str  # discussion, post, event, project
    title: str
    score: float
    reasoning: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = None


class RecommendationEngine:
    """
    Recommendation engine adapter for the Digital Twin.
    
    Provides personalized content recommendations based on user personality,
    interests, and behavior. Adapts ATLAS's ContentRecommendationEngine
    for use with the Digital Twin system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the recommendation engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.user_interactions = {}
        self.content_features = {}
        self.user_profiles = {}
        
        # Recommendation parameters
        self.params = {
            'max_recommendations': self.config.get('max_recommendations', 20),
            'min_confidence': self.config.get('min_confidence', 0.2),
            'weight_collaborative': self.config.get('weight_collaborative', 0.4),
            'weight_content_based': self.config.get('weight_content_based', 0.3),
            'weight_personality': self.config.get('weight_personality', 0.2),
            'weight_recency': self.config.get('weight_recency', 0.1)
        }
        
        # Initialize NLP components if available
        self.tfidf_vectorizer = None
        self.content_tfidf = None
        self.content_ids = []
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            self.tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            self.similarity_func = cosine_similarity
            logger.info("TF-IDF vectorizer initialized")
        except ImportError:
            logger.warning("scikit-learn not available, using fallback text matching")
            
        logger.info("Recommendation Engine initialized")

    def update_content_data(self, content_items: List[Dict[str, Any]], 
                          user_interactions: List[Dict[str, Any]],
                          user_profiles: List[Dict[str, Any]]) -> None:
        """
        Update content and interaction data for recommendations.

        Args:
            content_items: List of content items with metadata
            user_interactions: List of user interactions with content
            user_profiles: List of user profiles with interests
        """
        try:
            # Process content features
            self.content_features = {}
            content_texts = []
            content_ids = []
            
            for item in content_items:
                content_id = item['id']
                self.content_features[content_id] = {
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'content_type': item.get('content_type', 'unknown'),
                    'created_at': item.get('created_at'),
                    'tags': item.get('tags', []),
                    'engagement_score': item.get('engagement_score', 0.0),
                    'view_count': item.get('view_count', 0),
                    'like_count': item.get('like_count', 0)
                }
                
                # Combine text for TF-IDF
                text_content = f"{item.get('title', '')} {item.get('description', '')}"
                content_texts.append(text_content)
                content_ids.append(content_id)
            
            # Fit TF-IDF vectorizer if available
            if self.tfidf_vectorizer and content_texts:
                self.content_tfidf = self.tfidf_vectorizer.fit_transform(content_texts)
                self.content_ids = content_ids
            
            # Process user interactions
            self.user_interactions = defaultdict(lambda: defaultdict(float))
            for interaction in user_interactions:
                user_id = interaction['user_id']
                content_id = interaction['content_id']
                interaction_type = interaction.get('interaction_type', 'view')
                
                # Weight different interaction types
                weights = {'view': 1.0, 'like': 2.0, 'comment': 3.0, 'share': 4.0}
                weight = weights.get(interaction_type, 1.0)
                
                self.user_interactions[user_id][content_id] += weight
            
            # Process user profiles
            self.user_profiles = {p['user_id']: p for p in user_profiles}
            
            logger.info(f"Updated content data: {len(content_items)} items, "
                       f"{len(user_interactions)} interactions")
                       
        except Exception as e:
            logger.error(f"Error updating content data: {e}")
            raise

    def generate_recommendations(self, user_id: str, 
                              personality_profile: Dict[str, Any],
                              content_types: Optional[List[str]] = None,
                              limit: int = 10) -> List[ContentRecommendation]:
        """
        Generate personalized content recommendations for a user.

        Args:
            user_id: User ID
            personality_profile: User's personality profile
            content_types: Optional list of content types to filter by
            limit: Maximum number of recommendations to return

        Returns:
            List of content recommendations
        """
        try:
            if user_id not in self.user_profiles:
                # Create a basic profile from personality data
                self.user_profiles[user_id] = {
                    'user_id': user_id,
                    'interests': self._extract_interests_from_personality(personality_profile),
                    'created_at': datetime.now().isoformat()
                }
            
            recommendations = []
            
            # Get collaborative filtering recommendations
            collab_recs = self._collaborative_filtering_recommendations(user_id, limit * 2)
            
            # Get content-based recommendations
            content_recs = self._content_based_recommendations(user_id, limit * 2)
            
            # Get personality-based recommendations
            personality_recs = self._personality_based_recommendations(personality_profile, limit * 2)
            
            # Get popularity-based recommendations
            popularity_recs = self._popularity_based_recommendations(user_id, limit)
            
            # Combine and score recommendations
            combined_scores = defaultdict(float)
            recommendation_sources = defaultdict(list)
            
            # Add collaborative filtering scores
            for content_id, score in collab_recs:
                combined_scores[content_id] += self.params['weight_collaborative'] * score
                recommendation_sources[content_id].append('collaborative')
            
            # Add content-based scores
            for content_id, score in content_recs:
                combined_scores[content_id] += self.params['weight_content_based'] * score
                recommendation_sources[content_id].append('content-based')
            
            # Add personality-based scores
            for content_id, score in personality_recs:
                combined_scores[content_id] += self.params['weight_personality'] * score
                recommendation_sources[content_id].append('personality')
            
            # Add popularity scores
            for content_id, score in popularity_recs:
                combined_scores[content_id] += (1.0 - self.params['weight_collaborative'] - 
                                              self.params['weight_content_based'] - 
                                              self.params['weight_personality']) * score
                recommendation_sources[content_id].append('popularity')
            
            # Create recommendation objects
            for content_id, score in combined_scores.items():
                if content_id in self.content_features:
                    features = self.content_features[content_id]
                    
                    # Filter by content type if specified
                    if content_types and features['content_type'] not in content_types:
                        continue
                    
                    # Skip if user already interacted with this content
                    if content_id in self.user_interactions.get(user_id, {}):
                        continue
                    
                    # Apply recency boost
                    recency_score = self._calculate_recency_score(features['created_at'])
                    final_score = score + (self.params['weight_recency'] * recency_score)
                    
                    if final_score >= self.params['min_confidence']:
                        recommendation = ContentRecommendation(
                            content_id=content_id,
                            content_type=features['content_type'],
                            title=features['title'],
                            score=final_score,
                            reasoning=f"Recommended based on: {', '.join(recommendation_sources[content_id])}",
                            confidence=min(final_score * 1.1, 1.0),
                            metadata=features
                        )
                        recommendations.append(recommendation)
            
            # Sort by score and limit results
            recommendations.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _collaborative_filtering_recommendations(self, user_id: str, 
                                              limit: int) -> List[Tuple[str, float]]:
        """
        Generate recommendations using collaborative filtering.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations

        Returns:
            List of (content_id, score) tuples
        """
        try:
            if user_id not in self.user_interactions:
                return []
            
            user_items = self.user_interactions[user_id]
            recommendations = []
            
            # Find similar users
            similar_users = self._find_similar_users(user_id, top_k=20)
            
            # Get items liked by similar users
            candidate_items = defaultdict(float)
            
            for similar_user, similarity in similar_users:
                for item_id, rating in self.user_interactions[similar_user].items():
                    if item_id not in user_items:  # Not already interacted with
                        candidate_items[item_id] += similarity * rating
            
            # Normalize scores
            if candidate_items:
                max_score = max(candidate_items.values())
                if max_score > 0:
                    for item_id in candidate_items:
                        candidate_items[item_id] /= max_score
            
            # Sort and return top recommendations
            recommendations = sorted(candidate_items.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {e}")
            return []

    def _content_based_recommendations(self, user_id: str, 
                                    limit: int) -> List[Tuple[str, float]]:
        """
        Generate recommendations using content-based filtering.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations

        Returns:
            List of (content_id, score) tuples
        """
        try:
            user_profile = self.user_profiles.get(user_id, {})
            user_interests = set(user_profile.get('interests', []))
            
            if not user_interests or not hasattr(self, 'content_tfidf') or self.content_tfidf is None:
                return []
            
            # Create user interest profile
            interest_text = ' '.join(user_interests)
            
            if self.tfidf_vectorizer and self.similarity_func:
                # Use TF-IDF for similarity
                user_vector = self.tfidf_vectorizer.transform([interest_text])
                
                # Calculate similarity with all content
                similarities = self.similarity_func(user_vector, self.content_tfidf).flatten()
                
                # Get top similar content
                content_similarities = list(zip(self.content_ids, similarities))
                content_similarities.sort(key=lambda x: x[1], reverse=True)
                
                return content_similarities[:limit]
            else:
                # Fallback to basic matching
                return self._basic_content_matching(user_interests, limit)
            
        except Exception as e:
            logger.error(f"Error in content-based filtering: {e}")
            return []

    def _personality_based_recommendations(self, personality_profile: Dict[str, Any], 
                                        limit: int) -> List[Tuple[str, float]]:
        """
        Generate recommendations based on personality profile.

        Args:
            personality_profile: User's personality profile
            limit: Maximum number of recommendations

        Returns:
            List of (content_id, score) tuples
        """
        try:
            # Extract personality dimensions
            dimensions = personality_profile.get('dimensions', {})
            openness = dimensions.get('openness', 0.5)
            conscientiousness = dimensions.get('conscientiousness', 0.5)
            extraversion = dimensions.get('extraversion', 0.5)
            agreeableness = dimensions.get('agreeableness', 0.5)
            neuroticism = dimensions.get('neuroticism', 0.5)
            
            # Calculate content affinity scores based on personality
            content_scores = []
            
            for content_id, features in self.content_features.items():
                score = 0.0
                
                # Content type affinity based on personality
                content_type = features.get('content_type', '')
                
                # Openness correlates with interest in creative, novel content
                if 'creative' in content_type or 'novel' in content_type:
                    score += openness * 0.3
                
                # Conscientiousness correlates with interest in educational, practical content
                if 'educational' in content_type or 'practical' in content_type:
                    score += conscientiousness * 0.3
                
                # Extraversion correlates with interest in social, interactive content
                if 'social' in content_type or 'interactive' in content_type:
                    score += extraversion * 0.3
                
                # Agreeableness correlates with interest in cooperative, helpful content
                if 'cooperative' in content_type or 'helpful' in content_type:
                    score += agreeableness * 0.3
                
                # Low neuroticism (emotional stability) correlates with interest in challenging content
                if 'challenging' in content_type:
                    score += (1.0 - neuroticism) * 0.3
                
                # Tag-based scoring
                tags = features.get('tags', [])
                for tag in tags:
                    if 'creative' in tag or 'innovative' in tag:
                        score += openness * 0.1
                    if 'educational' in tag or 'informative' in tag:
                        score += conscientiousness * 0.1
                    if 'social' in tag or 'community' in tag:
                        score += extraversion * 0.1
                    if 'helpful' in tag or 'supportive' in tag:
                        score += agreeableness * 0.1
                    if 'calming' in tag or 'relaxing' in tag:
                        score += neuroticism * 0.1
                
                # Add a base score to ensure some results
                score += 0.2
                
                # Normalize score
                score = min(score, 1.0)
                
                content_scores.append((content_id, score))
            
            # Sort by score
            content_scores.sort(key=lambda x: x[1], reverse=True)
            
            return content_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error in personality-based recommendations: {e}")
            return []

    def _popularity_based_recommendations(self, user_id: str, 
                                       limit: int) -> List[Tuple[str, float]]:
        """
        Generate recommendations based on content popularity.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations

        Returns:
            List of (content_id, score) tuples
        """
        try:
            popularity_scores = []
            
            for content_id, features in self.content_features.items():
                # Skip if user already interacted
                if content_id in self.user_interactions.get(user_id, {}):
                    continue
                
                # Calculate popularity score
                engagement = features.get('engagement_score', 0.0)
                views = features.get('view_count', 0)
                likes = features.get('like_count', 0)
                
                popularity = (engagement * 0.5) + (views * 0.003) + (likes * 0.1)
                popularity_scores.append((content_id, min(popularity / 100.0, 1.0)))
            
            # Sort by popularity
            popularity_scores.sort(key=lambda x: x[1], reverse=True)
            
            return popularity_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error in popularity-based recommendations: {e}")
            return []

    def _find_similar_users(self, user_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find users similar to the given user based on interaction patterns.

        Args:
            user_id: User ID
            top_k: Maximum number of similar users to return

        Returns:
            List of (user_id, similarity_score) tuples
        """
        try:
            if user_id not in self.user_interactions:
                return []
            
            user_items = self.user_interactions[user_id]
            similarities = []
            
            for other_user_id, other_items in self.user_interactions.items():
                if other_user_id == user_id:
                    continue
                
                # Calculate Jaccard similarity
                user_set = set(user_items.keys())
                other_set = set(other_items.keys())
                
                if not user_set or not other_set:
                    continue
                
                intersection = len(user_set & other_set)
                union = len(user_set | other_set)
                
                if union > 0:
                    jaccard_sim = intersection / union
                    
                    # Weight by interaction strength
                    strength_sim = self._calculate_interaction_strength_similarity(
                        user_items, other_items
                    )
                    
                    final_similarity = (jaccard_sim * 0.7) + (strength_sim * 0.3)
                    similarities.append((other_user_id, final_similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []

    def _calculate_interaction_strength_similarity(self, items1: Dict[str, float], 
                                                items2: Dict[str, float]) -> float:
        """
        Calculate similarity based on interaction strength patterns.

        Args:
            items1: First user's interaction strengths
            items2: Second user's interaction strengths

        Returns:
            Similarity score between 0 and 1
        """
        try:
            common_items = set(items1.keys()) & set(items2.keys())
            
            if not common_items:
                return 0.0
            
            # Calculate correlation of interaction strengths for common items
            values1 = [items1[item] for item in common_items]
            values2 = [items2[item] for item in common_items]
            
            if len(values1) < 2:
                return 0.0
            
            try:
                correlation = np.corrcoef(values1, values2)[0, 1]
                
                # Handle NaN case
                if np.isnan(correlation):
                    return 0.0
                
                return max(correlation, 0.0)  # Only positive correlations
            except:
                # Fallback if numpy not available or other error
                return len(common_items) / max(len(items1), len(items2))
            
        except Exception as e:
            logger.error(f"Error calculating interaction strength similarity: {e}")
            return 0.0

    def _calculate_recency_score(self, created_at: Optional[datetime]) -> float:
        """
        Calculate recency score for content.

        Args:
            created_at: Content creation timestamp

        Returns:
            Recency score between 0 and 1
        """
        try:
            if not created_at:
                return 0.0
            
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    return 0.0
            
            now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            age_days = (now - created_at).days
            
            # Exponential decay with half-life of 7 days
            try:
                recency_score = np.exp(-age_days / 7.0)
            except:
                # Fallback if numpy not available
                recency_score = 1.0 / (1.0 + age_days / 7.0)
            
            return recency_score
            
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.0

    def _extract_interests_from_personality(self, personality_profile: Dict[str, Any]) -> List[str]:
        """
        Extract likely interests from personality profile.

        Args:
            personality_profile: User's personality profile

        Returns:
            List of inferred interests
        """
        interests = []
        
        # Extract from traits
        traits = personality_profile.get('traits', {})
        for trait_name, trait_value in traits.items():
            if trait_value > 0.7:
                interests.append(trait_name)
        
        # Extract from dimensions
        dimensions = personality_profile.get('dimensions', {})
        
        # Openness correlates with interest in arts, creativity, innovation
        if dimensions.get('openness', 0.0) > 0.7:
            interests.extend(['arts', 'creativity', 'innovation', 'exploration'])
            
        # Conscientiousness correlates with interest in organization, achievement
        if dimensions.get('conscientiousness', 0.0) > 0.7:
            interests.extend(['productivity', 'organization', 'achievement', 'learning'])
            
        # Extraversion correlates with interest in social activities
        if dimensions.get('extraversion', 0.0) > 0.7:
            interests.extend(['social', 'events', 'networking', 'community'])
            
        # Agreeableness correlates with interest in cooperation, helping
        if dimensions.get('agreeableness', 0.0) > 0.7:
            interests.extend(['cooperation', 'helping', 'community', 'support'])
            
        # Low neuroticism correlates with interest in adventure, challenges
        if dimensions.get('neuroticism', 0.0) < 0.3:
            interests.extend(['adventure', 'challenges', 'sports', 'outdoors'])
        
        return list(set(interests))  # Remove duplicates

    def _basic_content_matching(self, user_interests: set, limit: int) -> List[Tuple[str, float]]:
        """
        Basic content matching when TF-IDF is not available.

        Args:
            user_interests: Set of user interests
            limit: Maximum number of recommendations

        Returns:
            List of (content_id, score) tuples
        """
        content_scores = []
        
        for content_id, features in self.content_features.items():
            # Extract content tags and keywords
            tags = set(features.get('tags', []))
            title_words = set(features.get('title', '').lower().split())
            desc_words = set(features.get('description', '').lower().split())
            
            content_keywords = tags.union(title_words).union(desc_words)
            
            # Calculate overlap
            overlap = len(user_interests.intersection(content_keywords))
            total = len(user_interests.union(content_keywords))
            
            if total > 0:
                similarity = overlap / total
                content_scores.append((content_id, similarity))
        
        # Sort by score
        content_scores.sort(key=lambda x: x[1], reverse=True)
        
        return content_scores[:limit]

    def get_trending_content(self, limit: int = 10, 
                          time_window_hours: int = 24) -> List[ContentRecommendation]:
        """
        Get trending content based on recent engagement.

        Args:
            limit: Maximum number of results
            time_window_hours: Time window for trending content

        Returns:
            List of trending content recommendations
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            trending_scores = []
            
            for content_id, features in self.content_features.items():
                created_at = features.get('created_at')
                if not created_at:
                    continue
                
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        continue
                
                # Only consider recent content
                if created_at < cutoff_time:
                    continue
                
                # Calculate trending score
                engagement = features.get('engagement_score', 0.0)
                views = features.get('view_count', 0)
                likes = features.get('like_count', 0)
                
                # Weight recent engagement more heavily
                age_hours = (datetime.now() - created_at).total_seconds() / 3600
                recency_weight = max(1.0 - (age_hours / time_window_hours), 0.1)
                
                trending_score = (engagement + views * 0.1 + likes * 0.5) * recency_weight
                trending_scores.append((content_id, trending_score))
            
            # Sort by trending score
            trending_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Create recommendation objects
            recommendations = []
            for content_id, score in trending_scores[:limit]:
                features = self.content_features[content_id]
                recommendation = ContentRecommendation(
                    content_id=content_id,
                    content_type=features['content_type'],
                    title=features['title'],
                    score=min(score / 100.0, 1.0),  # Normalize
                    reasoning="Trending content with high recent engagement",
                    confidence=0.8,
                    metadata=features
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting trending content: {e}")
            return []