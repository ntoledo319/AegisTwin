"""
Consumption Trait Extractor for the Digital Twin.

This module provides functionality for extracting personality traits from
consumption data (purchases, media consumption, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..traits import PersonalityTraitExtractor

logger = logging.getLogger(__name__)


class ConsumptionTraitExtractor(PersonalityTraitExtractor):
    """
    Extractor for personality traits from consumption data.
    """

    async def extract_traits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from consumption data.

        Args:
            data: Consumption data dictionary containing purchases, media, etc.

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        # Extract different types of consumption data
        purchases = data.get("purchases", [])
        media_consumption = data.get("media_consumption", {})
        subscriptions = data.get("subscriptions", [])
        preferences = data.get("preferences", {})
        
        if not purchases and not media_consumption and not subscriptions and not preferences:
            logger.warning("No consumption data found")
            return traits

        # Process purchase data
        if purchases:
            purchase_traits = await self._process_purchases(purchases)
            traits.update(purchase_traits)

        # Process media consumption data
        if media_consumption:
            media_traits = await self._process_media_consumption(media_consumption)
            
            # Combine traits
            for trait, value in media_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process subscription data
        if subscriptions:
            subscription_traits = await self._process_subscriptions(subscriptions)
            
            # Combine traits
            for trait, value in subscription_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process preference data
        if preferences:
            preference_traits = await self._process_preferences(preferences)
            
            # Combine traits
            for trait, value in preference_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        logger.debug(f"Extracted {len(traits)} traits from consumption data")
        return traits

    async def _process_purchases(self, purchases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process purchase data to extract traits.

        Args:
            purchases: List of purchase records

        Returns:
            Dictionary of extracted traits
        """
        if not purchases:
            return {}

        # Initialize category counters
        categories = {
            "clothing": 0,
            "electronics": 0,
            "books": 0,
            "food": 0,
            "travel": 0,
            "entertainment": 0,
            "home": 0,
            "health": 0,
            "beauty": 0,
            "gifts": 0,
            "other": 0
        }
        
        # Initialize metrics
        total_purchases = len(purchases)
        total_amount = 0
        impulse_purchases = 0
        luxury_purchases = 0
        research_based_purchases = 0
        online_purchases = 0
        in_store_purchases = 0
        
        # Process each purchase
        for purchase in purchases:
            category = purchase.get("category", "").lower()
            amount = purchase.get("amount", 0)
            is_impulse = purchase.get("is_impulse", False)
            is_luxury = purchase.get("is_luxury", False)
            is_researched = purchase.get("is_researched", False)
            channel = purchase.get("channel", "").lower()
            
            # Update category counters
            if category in categories:
                categories[category] += amount
            else:
                categories["other"] += amount
                
            # Update amount
            total_amount += amount
            
            # Update purchase type counters
            if is_impulse:
                impulse_purchases += 1
                
            if is_luxury:
                luxury_purchases += 1
                
            if is_researched:
                research_based_purchases += 1
                
            # Update channel counters
            if channel in ["online", "web", "app", "mobile"]:
                online_purchases += 1
            else:
                in_store_purchases += 1
        
        # Calculate derived metrics
        category_percentages = {cat: amount / max(1, total_amount) for cat, amount in categories.items()}
        impulse_rate = impulse_purchases / total_purchases
        luxury_rate = luxury_purchases / total_purchases
        research_rate = research_based_purchases / total_purchases
        online_rate = online_purchases / total_purchases
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_purchases(
            category_percentages["books"],
            category_percentages["travel"],
            category_percentages["entertainment"]
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_purchases(
            research_rate,
            1.0 - impulse_rate
        )
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_purchases(
            category_percentages["clothing"],
            category_percentages["entertainment"],
            category_percentages["gifts"]
        )
        
        # Additional traits
        traits["impulsivity"] = impulse_rate
        traits["luxury_preference"] = luxury_rate
        traits["research_tendency"] = research_rate
        traits["online_shopping_preference"] = online_rate
        traits["fashion_interest"] = category_percentages["clothing"] + category_percentages["beauty"]
        traits["tech_interest"] = category_percentages["electronics"]
        traits["home_focus"] = category_percentages["home"]
        traits["health_focus"] = category_percentages["health"]
        
        return traits

    async def _process_media_consumption(self, media_consumption: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process media consumption data to extract traits.

        Args:
            media_consumption: Dictionary of media consumption data

        Returns:
            Dictionary of extracted traits
        """
        if not media_consumption:
            return {}

        # Initialize genre counters
        genres = {
            "action": 0,
            "adventure": 0,
            "comedy": 0,
            "drama": 0,
            "fantasy": 0,
            "horror": 0,
            "mystery": 0,
            "romance": 0,
            "sci_fi": 0,
            "thriller": 0,
            "documentary": 0,
            "news": 0,
            "educational": 0,
            "other": 0
        }
        
        # Initialize media type counters
        media_types = {
            "movies": 0,
            "tv_shows": 0,
            "books": 0,
            "music": 0,
            "podcasts": 0,
            "news": 0,
            "other": 0
        }
        
        # Initialize metrics
        total_consumption_time = 0
        consumption_by_hour = [0] * 24
        binge_watching_count = 0
        
        # Process each media type
        for media_type, data in media_consumption.items():
            # Skip if empty data
            if not data:
                continue
                
            # Update media type counter
            if media_type.lower() in media_types:
                media_types[media_type.lower()] += data.get("total_time", 0)
            else:
                media_types["other"] += data.get("total_time", 0)
                
            # Update total consumption time
            total_consumption_time += data.get("total_time", 0)
            
            # Process genre data
            genre_data = data.get("genres", {})
            for genre, time in genre_data.items():
                if genre.lower() in genres:
                    genres[genre.lower()] += time
                else:
                    genres["other"] += time
                    
            # Update consumption by hour
            hourly_data = data.get("hourly_distribution", {})
            for hour_str, time in hourly_data.items():
                try:
                    hour = int(hour_str)
                    if 0 <= hour < 24:
                        consumption_by_hour[hour] += time
                except (ValueError, TypeError):
                    pass
                    
            # Update binge watching count
            binge_watching_count += data.get("binge_watching_sessions", 0)
        
        # Calculate derived metrics
        genre_percentages = {genre: time / max(1, total_consumption_time) for genre, time in genres.items()}
        media_type_percentages = {media: time / max(1, total_consumption_time) for media, time in media_types.items()}
        
        # Determine peak consumption hours
        peak_hour = consumption_by_hour.index(max(consumption_by_hour))
        night_consumption = sum(consumption_by_hour[22:] + consumption_by_hour[:5])  # 10 PM to 5 AM
        night_consumption_percentage = night_consumption / max(1, total_consumption_time)
        
        # Calculate content diversity
        non_zero_genres = sum(1 for time in genres.values() if time > 0)
        genre_diversity = non_zero_genres / len(genres)
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_media(
            genre_percentages["documentary"] + genre_percentages["educational"],
            genre_diversity,
            media_type_percentages["books"] + media_type_percentages["podcasts"]
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_media(
            media_type_percentages["news"] + media_type_percentages["educational"],
            1.0 - night_consumption_percentage,
            1.0 - (binge_watching_count / 10)  # Normalize to 10 binge sessions
        )
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_media(
            genre_percentages["action"] + genre_percentages["comedy"],
            1.0 - media_type_percentages["books"]
        )
        
        # Neuroticism traits
        traits["neuroticism"] = self._calculate_neuroticism_from_media(
            genre_percentages["horror"] + genre_percentages["thriller"],
            night_consumption_percentage
        )
        
        # Additional traits
        traits["intellectual_curiosity"] = genre_percentages["documentary"] + genre_percentages["educational"] + genre_percentages["news"]
        traits["escapism_tendency"] = genre_percentages["fantasy"] + genre_percentages["sci_fi"] + genre_percentages["adventure"]
        traits["emotional_content_preference"] = genre_percentages["drama"] + genre_percentages["romance"]
        traits["thrill_seeking"] = genre_percentages["action"] + genre_percentages["horror"] + genre_percentages["thriller"]
        traits["night_owl"] = night_consumption_percentage
        traits["binge_watching_tendency"] = min(1.0, binge_watching_count / 10)  # Normalize to 10 binge sessions
        
        return traits

    async def _process_subscriptions(self, subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process subscription data to extract traits.

        Args:
            subscriptions: List of subscription records

        Returns:
            Dictionary of extracted traits
        """
        if not subscriptions:
            return {}

        # Initialize category counters
        categories = {
            "entertainment": 0,
            "news": 0,
            "education": 0,
            "productivity": 0,
            "health": 0,
            "fitness": 0,
            "shopping": 0,
            "food": 0,
            "other": 0
        }
        
        # Initialize metrics
        total_subscriptions = len(subscriptions)
        total_monthly_cost = 0
        auto_renew_count = 0
        long_term_count = 0
        
        # Process each subscription
        for subscription in subscriptions:
            category = subscription.get("category", "").lower()
            monthly_cost = subscription.get("monthly_cost", 0)
            auto_renew = subscription.get("auto_renew", False)
            duration_months = subscription.get("duration_months", 0)
            
            # Update category counters
            if category in categories:
                categories[category] += 1
            else:
                categories["other"] += 1
                
            # Update cost
            total_monthly_cost += monthly_cost
            
            # Update auto-renew count
            if auto_renew:
                auto_renew_count += 1
                
            # Update long-term count
            if duration_months >= 12:
                long_term_count += 1
        
        # Calculate derived metrics
        category_percentages = {cat: count / total_subscriptions for cat, count in categories.items()}
        auto_renew_rate = auto_renew_count / total_subscriptions
        long_term_rate = long_term_count / total_subscriptions
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_subscriptions(
            category_percentages["education"],
            category_percentages["news"]
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_subscriptions(
            auto_renew_rate,
            long_term_rate,
            category_percentages["productivity"]
        )
        
        # Additional traits
        traits["entertainment_focus"] = category_percentages["entertainment"]
        traits["health_focus"] = category_percentages["health"] + category_percentages["fitness"]
        traits["educational_focus"] = category_percentages["education"]
        traits["news_focus"] = category_percentages["news"]
        traits["commitment_tendency"] = long_term_rate
        traits["convenience_preference"] = auto_renew_rate
        
        return traits

    async def _process_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process preference data to extract traits.

        Args:
            preferences: Dictionary of preference data

        Returns:
            Dictionary of extracted traits
        """
        if not preferences:
            return {}

        # Extract preference data
        food_preferences = preferences.get("food", {})
        travel_preferences = preferences.get("travel", {})
        entertainment_preferences = preferences.get("entertainment", {})
        shopping_preferences = preferences.get("shopping", {})
        
        traits = {}
        
        # Process food preferences
        if food_preferences:
            food_traits = self._process_food_preferences(food_preferences)
            traits.update(food_traits)
            
        # Process travel preferences
        if travel_preferences:
            travel_traits = self._process_travel_preferences(travel_preferences)
            
            # Combine traits
            for trait, value in travel_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value
                    
        # Process entertainment preferences
        if entertainment_preferences:
            entertainment_traits = self._process_entertainment_preferences(entertainment_preferences)
            
            # Combine traits
            for trait, value in entertainment_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value
                    
        # Process shopping preferences
        if shopping_preferences:
            shopping_traits = self._process_shopping_preferences(shopping_preferences)
            
            # Combine traits
            for trait, value in shopping_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value
        
        return traits

    def _process_food_preferences(self, food_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process food preference data to extract traits.

        Args:
            food_preferences: Dictionary of food preference data

        Returns:
            Dictionary of extracted traits
        """
        # Extract metrics
        cuisine_diversity = food_preferences.get("cuisine_diversity", 0.5)
        adventurousness = food_preferences.get("adventurousness", 0.5)
        health_focus = food_preferences.get("health_focus", 0.5)
        price_sensitivity = food_preferences.get("price_sensitivity", 0.5)
        social_dining = food_preferences.get("social_dining", 0.5)
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._normalize_trait_value(
            cuisine_diversity * 0.5 +
            adventurousness * 0.5
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._normalize_trait_value(
            health_focus * 0.7 +
            (1.0 - price_sensitivity) * 0.3
        )
        
        # Extraversion traits
        traits["extraversion"] = self._normalize_trait_value(
            social_dining * 0.7 +
            adventurousness * 0.3
        )
        
        # Additional traits
        traits["food_adventurousness"] = adventurousness
        traits["health_consciousness"] = health_focus
        traits["social_dining_preference"] = social_dining
        
        return traits

    def _process_travel_preferences(self, travel_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process travel preference data to extract traits.

        Args:
            travel_preferences: Dictionary of travel preference data

        Returns:
            Dictionary of extracted traits
        """
        # Extract metrics
        destination_diversity = travel_preferences.get("destination_diversity", 0.5)
        adventure_seeking = travel_preferences.get("adventure_seeking", 0.5)
        planning_level = travel_preferences.get("planning_level", 0.5)
        luxury_preference = travel_preferences.get("luxury_preference", 0.5)
        social_travel = travel_preferences.get("social_travel", 0.5)
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._normalize_trait_value(
            destination_diversity * 0.5 +
            adventure_seeking * 0.5
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._normalize_trait_value(
            planning_level * 0.8 +
            (1.0 - adventure_seeking) * 0.2
        )
        
        # Extraversion traits
        traits["extraversion"] = self._normalize_trait_value(
            social_travel * 0.7 +
            adventure_seeking * 0.3
        )
        
        # Additional traits
        traits["travel_adventurousness"] = adventure_seeking
        traits["planning_tendency"] = planning_level
        traits["luxury_preference"] = luxury_preference
        
        return traits

    def _process_entertainment_preferences(self, entertainment_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process entertainment preference data to extract traits.

        Args:
            entertainment_preferences: Dictionary of entertainment preference data

        Returns:
            Dictionary of extracted traits
        """
        # Extract metrics
        content_diversity = entertainment_preferences.get("content_diversity", 0.5)
        social_entertainment = entertainment_preferences.get("social_entertainment", 0.5)
        intellectual_content = entertainment_preferences.get("intellectual_content", 0.5)
        active_vs_passive = entertainment_preferences.get("active_vs_passive", 0.5)
        novelty_seeking = entertainment_preferences.get("novelty_seeking", 0.5)
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._normalize_trait_value(
            content_diversity * 0.4 +
            intellectual_content * 0.4 +
            novelty_seeking * 0.2
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._normalize_trait_value(
            intellectual_content * 0.5 +
            active_vs_passive * 0.5
        )
        
        # Extraversion traits
        traits["extraversion"] = self._normalize_trait_value(
            social_entertainment * 0.7 +
            active_vs_passive * 0.3
        )
        
        # Additional traits
        traits["intellectual_curiosity"] = intellectual_content
        traits["social_entertainment_preference"] = social_entertainment
        traits["active_engagement"] = active_vs_passive
        traits["novelty_seeking"] = novelty_seeking
        
        return traits

    def _process_shopping_preferences(self, shopping_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process shopping preference data to extract traits.

        Args:
            shopping_preferences: Dictionary of shopping preference data

        Returns:
            Dictionary of extracted traits
        """
        # Extract metrics
        research_level = shopping_preferences.get("research_level", 0.5)
        brand_loyalty = shopping_preferences.get("brand_loyalty", 0.5)
        price_sensitivity = shopping_preferences.get("price_sensitivity", 0.5)
        impulse_buying = shopping_preferences.get("impulse_buying", 0.5)
        ethical_shopping = shopping_preferences.get("ethical_shopping", 0.5)
        
        # Map metrics to personality traits
        traits = {}
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._normalize_trait_value(
            research_level * 0.4 +
            (1.0 - impulse_buying) * 0.4 +
            ethical_shopping * 0.2
        )
        
        # Openness traits
        traits["openness"] = self._normalize_trait_value(
            (1.0 - brand_loyalty) * 0.5 +
            ethical_shopping * 0.5
        )
        
        # Additional traits
        traits["research_tendency"] = research_level
        traits["brand_loyalty"] = brand_loyalty
        traits["price_sensitivity"] = price_sensitivity
        traits["impulsivity"] = impulse_buying
        traits["ethical_consciousness"] = ethical_shopping
        
        return traits

    def _calculate_openness_from_purchases(self, books_percentage: float, travel_percentage: float, 
                                         entertainment_percentage: float) -> float:
        """
        Calculate openness score from purchase metrics.

        Args:
            books_percentage: Percentage spent on books
            travel_percentage: Percentage spent on travel
            entertainment_percentage: Percentage spent on entertainment

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            books_percentage * 0.4 +
            travel_percentage * 0.4 +
            entertainment_percentage * 0.2
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_conscientiousness_from_purchases(self, research_rate: float, non_impulse_rate: float) -> float:
        """
        Calculate conscientiousness score from purchase metrics.

        Args:
            research_rate: Rate of researched purchases
            non_impulse_rate: Rate of non-impulse purchases

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        conscientiousness_score = (
            research_rate * 0.6 +
            non_impulse_rate * 0.4
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_extraversion_from_purchases(self, clothing_percentage: float, entertainment_percentage: float, 
                                             gifts_percentage: float) -> float:
        """
        Calculate extraversion score from purchase metrics.

        Args:
            clothing_percentage: Percentage spent on clothing
            entertainment_percentage: Percentage spent on entertainment
            gifts_percentage: Percentage spent on gifts

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            clothing_percentage * 0.4 +
            entertainment_percentage * 0.3 +
            gifts_percentage * 0.3
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_openness_from_media(self, educational_percentage: float, genre_diversity: float, 
                                     books_podcasts_percentage: float) -> float:
        """
        Calculate openness score from media consumption metrics.

        Args:
            educational_percentage: Percentage of educational content
            genre_diversity: Diversity of genres consumed
            books_podcasts_percentage: Percentage of books and podcasts

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            educational_percentage * 0.4 +
            genre_diversity * 0.3 +
            books_podcasts_percentage * 0.3
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_conscientiousness_from_media(self, educational_news_percentage: float, 
                                              daytime_consumption_percentage: float, 
                                              non_binge_rate: float) -> float:
        """
        Calculate conscientiousness score from media consumption metrics.

        Args:
            educational_news_percentage: Percentage of educational and news content
            daytime_consumption_percentage: Percentage of daytime consumption
            non_binge_rate: Rate of non-binge watching

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        conscientiousness_score = (
            educational_news_percentage * 0.4 +
            daytime_consumption_percentage * 0.3 +
            non_binge_rate * 0.3
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_extraversion_from_media(self, action_comedy_percentage: float, 
                                         non_books_percentage: float) -> float:
        """
        Calculate extraversion score from media consumption metrics.

        Args:
            action_comedy_percentage: Percentage of action and comedy content
            non_books_percentage: Percentage of non-book media

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            action_comedy_percentage * 0.6 +
            non_books_percentage * 0.4
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_neuroticism_from_media(self, horror_thriller_percentage: float, 
                                        night_consumption_percentage: float) -> float:
        """
        Calculate neuroticism score from media consumption metrics.

        Args:
            horror_thriller_percentage: Percentage of horror and thriller content
            night_consumption_percentage: Percentage of night consumption

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        neuroticism_score = (
            horror_thriller_percentage * 0.6 +
            night_consumption_percentage * 0.4
        )
        
        return self._normalize_trait_value(neuroticism_score)

    def _calculate_openness_from_subscriptions(self, education_percentage: float, 
                                             news_percentage: float) -> float:
        """
        Calculate openness score from subscription metrics.

        Args:
            education_percentage: Percentage of educational subscriptions
            news_percentage: Percentage of news subscriptions

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            education_percentage * 0.6 +
            news_percentage * 0.4
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_conscientiousness_from_subscriptions(self, auto_renew_rate: float, 
                                                      long_term_rate: float, 
                                                      productivity_percentage: float) -> float:
        """
        Calculate conscientiousness score from subscription metrics.

        Args:
            auto_renew_rate: Rate of auto-renewing subscriptions
            long_term_rate: Rate of long-term subscriptions
            productivity_percentage: Percentage of productivity subscriptions

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        conscientiousness_score = (
            auto_renew_rate * 0.3 +
            long_term_rate * 0.3 +
            productivity_percentage * 0.4
        )
        
        return self._normalize_trait_value(conscientiousness_score)