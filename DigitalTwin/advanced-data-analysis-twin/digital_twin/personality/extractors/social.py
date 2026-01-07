"""
Social Trait Extractor for the Digital Twin.

This module provides functionality for extracting personality traits from
social data (social media, contacts, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from ..traits import PersonalityTraitExtractor

logger = logging.getLogger(__name__)


class SocialTraitExtractor(PersonalityTraitExtractor):
    """
    Extractor for personality traits from social data.
    """

    async def extract_traits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from social data.

        Args:
            data: Social data dictionary containing social media, contacts, etc.

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        # Extract different types of social data
        social_media = data.get("social_media", {})
        contacts = data.get("contacts", [])
        interactions = data.get("interactions", [])
        groups = data.get("groups", [])
        
        if not social_media and not contacts and not interactions and not groups:
            logger.warning("No social data found")
            return traits

        # Process social media data
        if social_media:
            social_media_traits = await self._process_social_media(social_media)
            traits.update(social_media_traits)

        # Process contacts data
        if contacts:
            contacts_traits = await self._process_contacts(contacts)
            
            # Combine traits
            for trait, value in contacts_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process interactions data
        if interactions:
            interaction_traits = await self._process_interactions(interactions)
            
            # Combine traits
            for trait, value in interaction_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process groups data
        if groups:
            group_traits = await self._process_groups(groups)
            
            # Combine traits
            for trait, value in group_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        logger.debug(f"Extracted {len(traits)} traits from social data")
        return traits

    async def _process_social_media(self, social_media: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process social media data to extract traits.

        Args:
            social_media: Dictionary of social media data

        Returns:
            Dictionary of extracted traits
        """
        if not social_media:
            return {}

        # Initialize metrics
        post_count = 0
        comment_count = 0
        like_count = 0
        share_count = 0
        follower_count = 0
        following_count = 0
        total_engagement = 0
        post_length_total = 0
        hashtag_count = 0
        mention_count = 0
        media_count = 0
        
        # Process each platform's data
        for platform, data in social_media.items():
            # Skip if empty data
            if not data:
                continue
                
            # Extract metrics
            post_count += data.get("post_count", 0)
            comment_count += data.get("comment_count", 0)
            like_count += data.get("like_count", 0)
            share_count += data.get("share_count", 0)
            follower_count += data.get("follower_count", 0)
            following_count += data.get("following_count", 0)
            
            # Process posts if available
            posts = data.get("posts", [])
            for post in posts:
                content = post.get("content", "")
                
                # Skip if no content
                if not content:
                    continue
                    
                # Update metrics
                post_length_total += len(content.split())
                hashtag_count += content.count('#')
                mention_count += content.count('@')
                
                # Check for media
                if post.get("has_media", False):
                    media_count += 1
                    
                # Update engagement
                post_engagement = post.get("likes", 0) + post.get("comments", 0) + post.get("shares", 0)
                total_engagement += post_engagement
        
        # Calculate derived metrics
        total_posts = max(1, post_count)
        avg_post_length = post_length_total / total_posts
        avg_engagement = total_engagement / total_posts
        hashtag_rate = hashtag_count / total_posts
        mention_rate = mention_count / total_posts
        media_rate = media_count / total_posts
        
        # Calculate network metrics
        network_size = follower_count + following_count
        network_ratio = follower_count / max(1, following_count)
        
        # Calculate activity metrics
        activity_level = (post_count + comment_count) / 30  # Normalize to monthly activity
        engagement_ratio = (like_count + comment_count) / max(1, post_count)
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_social_media(
            activity_level,
            network_size,
            mention_rate
        )
        
        # Agreeableness traits
        traits["agreeableness"] = self._calculate_agreeableness_from_social_media(
            comment_count / max(1, post_count),
            like_count / max(1, post_count)
        )
        
        # Neuroticism traits
        traits["neuroticism"] = self._calculate_neuroticism_from_social_media(
            hashtag_rate,
            avg_post_length
        )
        
        # Additional traits
        traits["social_activity"] = min(1.0, activity_level / 30)  # Normalize to 30 posts/comments per month
        traits["social_engagement"] = min(1.0, engagement_ratio / 10)  # Normalize to 10 engagements per post
        traits["social_influence"] = min(1.0, network_ratio)  # Higher follower to following ratio = more influence
        traits["social_expressiveness"] = min(1.0, avg_post_length / 50)  # Normalize to 50 words per post
        traits["media_sharing_tendency"] = media_rate
        
        return traits

    async def _process_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process contacts data to extract traits.

        Args:
            contacts: List of contact records

        Returns:
            Dictionary of extracted traits
        """
        if not contacts:
            return {}

        # Initialize metrics
        total_contacts = len(contacts)
        contact_categories = {
            "family": 0,
            "friend": 0,
            "work": 0,
            "acquaintance": 0,
            "other": 0
        }
        
        contact_frequency = {
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
            "rarely": 0,
            "never": 0
        }
        
        # Process each contact
        for contact in contacts:
            category = contact.get("category", "").lower()
            frequency = contact.get("contact_frequency", "").lower()
            
            # Update category counters
            if category in contact_categories:
                contact_categories[category] += 1
            else:
                contact_categories["other"] += 1
                
            # Update frequency counters
            if frequency in contact_frequency:
                contact_frequency[frequency] += 1
            else:
                contact_frequency["rarely"] += 1
        
        # Calculate derived metrics
        category_percentages = {cat: count / total_contacts for cat, count in contact_categories.items()}
        frequency_percentages = {freq: count / total_contacts for freq, count in contact_frequency.items()}
        
        # Calculate active contacts percentage
        active_contacts = contact_frequency["daily"] + contact_frequency["weekly"]
        active_percentage = active_contacts / total_contacts
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_contacts(
            total_contacts,
            active_percentage,
            category_percentages["friend"]
        )
        
        # Agreeableness traits
        traits["agreeableness"] = self._calculate_agreeableness_from_contacts(
            category_percentages["family"],
            active_percentage
        )
        
        # Additional traits
        traits["social_network_size"] = min(1.0, total_contacts / 200)  # Normalize to 200 contacts
        traits["social_activity"] = active_percentage
        traits["work_orientation"] = category_percentages["work"]
        traits["family_orientation"] = category_percentages["family"]
        traits["friendship_orientation"] = category_percentages["friend"]
        
        return traits

    async def _process_interactions(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process interaction data to extract traits.

        Args:
            interactions: List of interaction records

        Returns:
            Dictionary of extracted traits
        """
        if not interactions:
            return {}

        # Initialize metrics
        total_interactions = len(interactions)
        interaction_types = {
            "message": 0,
            "call": 0,
            "meeting": 0,
            "email": 0,
            "social": 0,
            "other": 0
        }
        
        initiated_count = 0
        response_times = []
        interaction_durations = []
        
        # Process each interaction
        for interaction in interactions:
            interaction_type = interaction.get("type", "").lower()
            initiated = interaction.get("initiated", False)
            duration = interaction.get("duration", 0)  # in minutes
            response_time = interaction.get("response_time", 0)  # in minutes
            
            # Update type counters
            if interaction_type in interaction_types:
                interaction_types[interaction_type] += 1
            else:
                interaction_types["other"] += 1
                
            # Update initiated count
            if initiated:
                initiated_count += 1
                
            # Update duration and response time lists
            if duration > 0:
                interaction_durations.append(duration)
                
            if response_time > 0:
                response_times.append(response_time)
        
        # Calculate derived metrics
        type_percentages = {t: count / total_interactions for t, count in interaction_types.items()}
        initiation_rate = initiated_count / total_interactions
        
        avg_duration = sum(interaction_durations) / max(1, len(interaction_durations))
        avg_response_time = sum(response_times) / max(1, len(response_times))
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_interactions(
            initiation_rate,
            type_percentages["call"] + type_percentages["meeting"],
            avg_duration
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_interactions(
            avg_response_time,
            type_percentages["email"]
        )
        
        # Agreeableness traits
        traits["agreeableness"] = self._calculate_agreeableness_from_interactions(
            avg_duration,
            avg_response_time
        )
        
        # Additional traits
        traits["social_initiation"] = initiation_rate
        traits["responsiveness"] = min(1.0, 60 / max(1, avg_response_time))  # Higher score for faster response
        traits["conversation_depth"] = min(1.0, avg_duration / 60)  # Normalize to 1 hour
        traits["communication_preference_text"] = type_percentages["message"] + type_percentages["email"]
        traits["communication_preference_verbal"] = type_percentages["call"] + type_percentages["meeting"]
        
        return traits

    async def _process_groups(self, groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process group data to extract traits.

        Args:
            groups: List of group records

        Returns:
            Dictionary of extracted traits
        """
        if not groups:
            return {}

        # Initialize metrics
        total_groups = len(groups)
        group_types = {
            "social": 0,
            "professional": 0,
            "interest": 0,
            "family": 0,
            "community": 0,
            "other": 0
        }
        
        leadership_count = 0
        active_participation_count = 0
        group_sizes = []
        
        # Process each group
        for group in groups:
            group_type = group.get("type", "").lower()
            role = group.get("role", "").lower()
            participation_level = group.get("participation_level", "").lower()
            size = group.get("size", 0)
            
            # Update type counters
            if group_type in group_types:
                group_types[group_type] += 1
            else:
                group_types["other"] += 1
                
            # Update leadership count
            if role in ["leader", "admin", "organizer", "founder"]:
                leadership_count += 1
                
            # Update active participation count
            if participation_level in ["high", "active", "regular"]:
                active_participation_count += 1
                
            # Update group sizes
            if size > 0:
                group_sizes.append(size)
        
        # Calculate derived metrics
        type_percentages = {t: count / total_groups for t, count in group_types.items()}
        leadership_rate = leadership_count / total_groups
        active_participation_rate = active_participation_count / total_groups
        
        avg_group_size = sum(group_sizes) / max(1, len(group_sizes))
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_groups(
            total_groups,
            active_participation_rate,
            type_percentages["social"]
        )
        
        # Agreeableness traits
        traits["agreeableness"] = self._calculate_agreeableness_from_groups(
            type_percentages["community"],
            active_participation_rate
        )
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_groups(
            type_percentages["interest"],
            total_groups
        )
        
        # Additional traits
        traits["leadership_tendency"] = leadership_rate
        traits["group_participation"] = active_participation_rate
        traits["social_group_preference"] = type_percentages["social"]
        traits["professional_group_preference"] = type_percentages["professional"]
        traits["community_orientation"] = type_percentages["community"]
        
        return traits

    def _calculate_extraversion_from_social_media(self, activity_level: float, network_size: int, 
                                                mention_rate: float) -> float:
        """
        Calculate extraversion score from social media metrics.

        Args:
            activity_level: Level of posting/commenting activity
            network_size: Size of social network
            mention_rate: Rate of mentioning others

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        # Normalize network size
        network_size_score = min(1.0, network_size / 1000)
        
        extraversion_score = (
            min(1.0, activity_level / 30) * 0.4 +  # Normalize to 30 activities per month
            network_size_score * 0.4 +
            mention_rate * 0.2
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_agreeableness_from_social_media(self, comment_ratio: float, like_ratio: float) -> float:
        """
        Calculate agreeableness score from social media metrics.

        Args:
            comment_ratio: Ratio of comments to posts
            like_ratio: Ratio of likes to posts

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        agreeableness_score = (
            min(1.0, comment_ratio) * 0.6 +
            min(1.0, like_ratio / 5) * 0.4  # Normalize to 5 likes per post
        )
        
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_neuroticism_from_social_media(self, hashtag_rate: float, avg_post_length: float) -> float:
        """
        Calculate neuroticism score from social media metrics.

        Args:
            hashtag_rate: Rate of hashtag usage
            avg_post_length: Average post length in words

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        # This is a simplified calculation - in reality, content analysis would be more important
        neuroticism_score = (
            min(1.0, hashtag_rate / 3) * 0.5 +  # Normalize to 3 hashtags per post
            (1.0 - min(1.0, avg_post_length / 100)) * 0.5  # Shorter posts might indicate higher neuroticism
        )
        
        return self._normalize_trait_value(neuroticism_score)

    def _calculate_extraversion_from_contacts(self, total_contacts: int, active_percentage: float, 
                                            friend_percentage: float) -> float:
        """
        Calculate extraversion score from contacts metrics.

        Args:
            total_contacts: Total number of contacts
            active_percentage: Percentage of actively contacted people
            friend_percentage: Percentage of friends in contacts

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            min(1.0, total_contacts / 200) * 0.4 +  # Normalize to 200 contacts
            active_percentage * 0.3 +
            friend_percentage * 0.3
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_agreeableness_from_contacts(self, family_percentage: float, active_percentage: float) -> float:
        """
        Calculate agreeableness score from contacts metrics.

        Args:
            family_percentage: Percentage of family members in contacts
            active_percentage: Percentage of actively contacted people

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        agreeableness_score = (
            family_percentage * 0.5 +
            active_percentage * 0.5
        )
        
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_extraversion_from_interactions(self, initiation_rate: float, verbal_percentage: float, 
                                                avg_duration: float) -> float:
        """
        Calculate extraversion score from interaction metrics.

        Args:
            initiation_rate: Rate of initiating interactions
            verbal_percentage: Percentage of verbal interactions
            avg_duration: Average interaction duration

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            initiation_rate * 0.4 +
            verbal_percentage * 0.4 +
            min(1.0, avg_duration / 60) * 0.2  # Normalize to 1 hour
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_conscientiousness_from_interactions(self, avg_response_time: float, email_percentage: float) -> float:
        """
        Calculate conscientiousness score from interaction metrics.

        Args:
            avg_response_time: Average response time in minutes
            email_percentage: Percentage of email interactions

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # Convert response time to a score (faster = higher conscientiousness, up to a point)
        response_time_score = 0.0
        if avg_response_time <= 60:  # Within an hour
            response_time_score = 1.0
        elif avg_response_time <= 240:  # Within 4 hours
            response_time_score = 0.8
        elif avg_response_time <= 720:  # Within 12 hours
            response_time_score = 0.6
        elif avg_response_time <= 1440:  # Within 24 hours
            response_time_score = 0.4
        else:
            response_time_score = 0.2
        
        conscientiousness_score = (
            response_time_score * 0.7 +
            email_percentage * 0.3  # Email usage may correlate with conscientiousness
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_agreeableness_from_interactions(self, avg_duration: float, avg_response_time: float) -> float:
        """
        Calculate agreeableness score from interaction metrics.

        Args:
            avg_duration: Average interaction duration
            avg_response_time: Average response time in minutes

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        # Convert response time to a score (faster = higher agreeableness)
        response_time_score = min(1.0, 240 / max(1, avg_response_time))  # Normalize to 4 hours
        
        agreeableness_score = (
            min(1.0, avg_duration / 30) * 0.6 +  # Normalize to 30 minutes
            response_time_score * 0.4
        )
        
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_extraversion_from_groups(self, total_groups: int, active_participation_rate: float, 
                                          social_percentage: float) -> float:
        """
        Calculate extraversion score from group metrics.

        Args:
            total_groups: Total number of groups
            active_participation_rate: Rate of active participation
            social_percentage: Percentage of social groups

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            min(1.0, total_groups / 10) * 0.3 +  # Normalize to 10 groups
            active_participation_rate * 0.4 +
            social_percentage * 0.3
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_agreeableness_from_groups(self, community_percentage: float, active_participation_rate: float) -> float:
        """
        Calculate agreeableness score from group metrics.

        Args:
            community_percentage: Percentage of community groups
            active_participation_rate: Rate of active participation

        Returns:
            Agreeableness score (0.0 to 1.0)
        """
        agreeableness_score = (
            community_percentage * 0.6 +
            active_participation_rate * 0.4
        )
        
        return self._normalize_trait_value(agreeableness_score)

    def _calculate_openness_from_groups(self, interest_percentage: float, total_groups: int) -> float:
        """
        Calculate openness score from group metrics.

        Args:
            interest_percentage: Percentage of interest-based groups
            total_groups: Total number of groups

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            interest_percentage * 0.7 +
            min(1.0, total_groups / 10) * 0.3  # Normalize to 10 groups
        )
        
        return self._normalize_trait_value(openness_score)