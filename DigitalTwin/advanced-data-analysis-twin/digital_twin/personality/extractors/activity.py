"""
Activity Trait Extractor for the Digital Twin.

This module provides functionality for extracting personality traits from
activity data (app usage, browsing history, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time

from ..traits import PersonalityTraitExtractor

logger = logging.getLogger(__name__)


class ActivityTraitExtractor(PersonalityTraitExtractor):
    """
    Extractor for personality traits from activity data.
    """

    async def extract_traits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract personality traits from activity data.

        Args:
            data: Activity data dictionary containing app usage, browsing, etc.

        Returns:
            Dictionary of extracted traits
        """
        traits = {}

        # Extract different types of activity data
        app_usage = data.get("app_usage", [])
        browsing_history = data.get("browsing_history", [])
        productivity_data = data.get("productivity", {})
        schedule_data = data.get("schedule", [])
        
        if not app_usage and not browsing_history and not productivity_data and not schedule_data:
            logger.warning("No activity data found")
            return traits

        # Process app usage data
        if app_usage:
            app_traits = await self._process_app_usage(app_usage)
            traits.update(app_traits)

        # Process browsing history
        if browsing_history:
            browsing_traits = await self._process_browsing_history(browsing_history)
            
            # Combine traits from app usage and browsing
            for trait, value in browsing_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process productivity data
        if productivity_data:
            productivity_traits = await self._process_productivity_data(productivity_data)
            
            # Combine traits
            for trait, value in productivity_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        # Process schedule data
        if schedule_data:
            schedule_traits = await self._process_schedule_data(schedule_data)
            
            # Combine traits
            for trait, value in schedule_traits.items():
                if trait in traits:
                    traits[trait] = (traits[trait] + value) / 2
                else:
                    traits[trait] = value

        logger.debug(f"Extracted {len(traits)} traits from activity data")
        return traits

    async def _process_app_usage(self, app_usage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process app usage data to extract traits.

        Args:
            app_usage: List of app usage records

        Returns:
            Dictionary of extracted traits
        """
        if not app_usage:
            return {}

        # Initialize app category counters
        categories = {
            "social": 0,
            "productivity": 0,
            "entertainment": 0,
            "gaming": 0,
            "news": 0,
            "education": 0,
            "health": 0,
            "finance": 0,
            "shopping": 0,
            "travel": 0,
            "utility": 0
        }
        
        # Initialize time metrics
        total_usage_time = 0
        usage_by_hour = [0] * 24
        
        # Process each app usage record
        for record in app_usage:
            app_name = record.get("app_name", "")
            category = record.get("category", "")
            duration = record.get("duration", 0)  # in minutes
            timestamp = record.get("timestamp")
            
            # Skip if missing essential data
            if not app_name or not category or duration <= 0:
                continue
                
            # Update category counters
            if category.lower() in categories:
                categories[category.lower()] += duration
                
            # Update total usage time
            total_usage_time += duration
            
            # Update usage by hour
            if timestamp:
                try:
                    usage_time = datetime.fromisoformat(timestamp)
                    usage_by_hour[usage_time.hour] += duration
                except (ValueError, TypeError):
                    pass
        
        # Calculate derived metrics
        if total_usage_time > 0:
            category_percentages = {cat: time / total_usage_time for cat, time in categories.items()}
        else:
            category_percentages = {cat: 0 for cat in categories}
        
        # Determine peak usage hours
        peak_hour = usage_by_hour.index(max(usage_by_hour))
        night_usage = sum(usage_by_hour[22:] + usage_by_hour[:5])  # 10 PM to 5 AM
        night_usage_percentage = night_usage / max(1, total_usage_time)
        
        # Calculate app switching frequency (if available)
        app_switches = len(app_usage)
        app_switching_rate = app_switches / max(1, total_usage_time / 60)  # switches per hour
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_apps(
            category_percentages["social"],
            category_percentages["entertainment"],
            app_switching_rate
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_apps(
            category_percentages["productivity"],
            category_percentages["education"],
            category_percentages["finance"],
            night_usage_percentage
        )
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_apps(
            category_percentages["education"],
            category_percentages["news"],
            category_percentages["travel"]
        )
        
        # Additional traits
        traits["productivity_focus"] = category_percentages["productivity"] + category_percentages["education"]
        traits["social_focus"] = category_percentages["social"]
        traits["entertainment_focus"] = category_percentages["entertainment"] + category_percentages["gaming"]
        traits["night_owl"] = night_usage_percentage
        traits["app_switching_tendency"] = min(1.0, app_switching_rate / 10)  # Normalize to max 10 switches per hour
        
        return traits

    async def _process_browsing_history(self, browsing_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process browsing history data to extract traits.

        Args:
            browsing_history: List of browsing history records

        Returns:
            Dictionary of extracted traits
        """
        if not browsing_history:
            return {}

        # Initialize category counters
        categories = {
            "social": 0,
            "productivity": 0,
            "entertainment": 0,
            "news": 0,
            "education": 0,
            "shopping": 0,
            "finance": 0,
            "technology": 0,
            "health": 0,
            "travel": 0
        }
        
        # Initialize metrics
        total_sites = len(browsing_history)
        unique_domains = set()
        reading_time = 0
        browsing_by_hour = [0] * 24
        
        # Process each browsing record
        for record in browsing_history:
            url = record.get("url", "")
            category = record.get("category", "")
            duration = record.get("duration", 0)  # in seconds
            timestamp = record.get("timestamp")
            
            # Skip if missing essential data
            if not url:
                continue
                
            # Extract domain
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                unique_domains.add(domain)
            except:
                pass
                
            # Update category counters
            if category.lower() in categories:
                categories[category.lower()] += 1
                
            # Update reading time
            reading_time += duration
            
            # Update browsing by hour
            if timestamp:
                try:
                    browse_time = datetime.fromisoformat(timestamp)
                    browsing_by_hour[browse_time.hour] += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate derived metrics
        category_percentages = {cat: count / max(1, total_sites) for cat, count in categories.items()}
        domain_diversity = len(unique_domains) / max(1, total_sites)
        avg_reading_time = reading_time / max(1, total_sites)
        
        # Determine peak browsing hours
        peak_hour = browsing_by_hour.index(max(browsing_by_hour))
        night_browsing = sum(browsing_by_hour[22:] + browsing_by_hour[:5])  # 10 PM to 5 AM
        night_browsing_percentage = night_browsing / max(1, total_sites)
        
        # Map metrics to personality traits
        traits = {}
        
        # Openness traits
        traits["openness"] = self._calculate_openness_from_browsing(
            category_percentages["education"],
            category_percentages["news"],
            category_percentages["technology"],
            domain_diversity
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_browsing(
            category_percentages["productivity"],
            category_percentages["education"],
            category_percentages["finance"],
            night_browsing_percentage
        )
        
        # Additional traits
        traits["information_seeking"] = category_percentages["news"] + category_percentages["education"] + category_percentages["technology"]
        traits["shopping_tendency"] = category_percentages["shopping"]
        traits["reading_depth"] = min(1.0, avg_reading_time / 300)  # Normalize to 5 minutes
        traits["browsing_diversity"] = domain_diversity
        
        return traits

    async def _process_productivity_data(self, productivity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process productivity data to extract traits.

        Args:
            productivity_data: Dictionary of productivity metrics

        Returns:
            Dictionary of extracted traits
        """
        if not productivity_data:
            return {}

        # Extract productivity metrics
        tasks_completed = productivity_data.get("tasks_completed", 0)
        tasks_total = productivity_data.get("tasks_total", 0)
        focus_time = productivity_data.get("focus_time", 0)  # in minutes
        distractions = productivity_data.get("distractions", 0)
        task_switching = productivity_data.get("task_switching", 0)
        deep_work_sessions = productivity_data.get("deep_work_sessions", 0)
        
        # Calculate derived metrics
        task_completion_rate = tasks_completed / max(1, tasks_total)
        distraction_rate = distractions / max(1, focus_time / 60)  # distractions per hour
        task_switching_rate = task_switching / max(1, focus_time / 60)  # switches per hour
        deep_work_ratio = deep_work_sessions / max(1, focus_time / 60)  # sessions per hour
        
        # Map metrics to personality traits
        traits = {}
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_productivity(
            task_completion_rate,
            distraction_rate,
            deep_work_ratio
        )
        
        # Neuroticism traits
        traits["neuroticism"] = self._calculate_neuroticism_from_productivity(
            distraction_rate,
            task_switching_rate
        )
        
        # Additional traits
        traits["focus_ability"] = max(0.0, min(1.0, 1.0 - (distraction_rate / 10)))  # Normalize to max 10 distractions per hour
        traits["task_persistence"] = max(0.0, min(1.0, 1.0 - (task_switching_rate / 5)))  # Normalize to max 5 switches per hour
        traits["deep_work_tendency"] = min(1.0, deep_work_ratio)
        traits["productivity"] = task_completion_rate
        
        return traits

    async def _process_schedule_data(self, schedule_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process schedule data to extract traits.

        Args:
            schedule_data: List of schedule entries

        Returns:
            Dictionary of extracted traits
        """
        if not schedule_data:
            return {}

        # Initialize metrics
        total_events = len(schedule_data)
        social_events = 0
        work_events = 0
        personal_events = 0
        planned_duration = 0
        advance_planning = 0  # total days events were planned in advance
        
        # Time of day distribution
        time_distribution = {
            "morning": 0,    # 5:00 - 11:59
            "afternoon": 0,  # 12:00 - 16:59
            "evening": 0,    # 17:00 - 21:59
            "night": 0       # 22:00 - 4:59
        }
        
        # Process each schedule entry
        for event in schedule_data:
            event_type = event.get("type", "").lower()
            start_time = event.get("start_time")
            end_time = event.get("end_time")
            created_time = event.get("created_time")
            
            # Categorize event
            if event_type in ["meeting", "work", "business", "conference", "presentation"]:
                work_events += 1
            elif event_type in ["party", "gathering", "meetup", "date", "social"]:
                social_events += 1
            else:
                personal_events += 1
                
            # Calculate duration
            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time)
                    end = datetime.fromisoformat(end_time)
                    duration = (end - start).total_seconds() / 60  # in minutes
                    planned_duration += duration
                    
                    # Update time distribution
                    hour = start.hour
                    if 5 <= hour < 12:
                        time_distribution["morning"] += 1
                    elif 12 <= hour < 17:
                        time_distribution["afternoon"] += 1
                    elif 17 <= hour < 22:
                        time_distribution["evening"] += 1
                    else:
                        time_distribution["night"] += 1
                except (ValueError, TypeError):
                    pass
                    
            # Calculate planning advance
            if start_time and created_time:
                try:
                    start = datetime.fromisoformat(start_time)
                    created = datetime.fromisoformat(created_time)
                    days_in_advance = (start - created).total_seconds() / (86400)  # in days
                    advance_planning += max(0, days_in_advance)
                except (ValueError, TypeError):
                    pass
        
        # Calculate derived metrics
        social_ratio = social_events / max(1, total_events)
        work_ratio = work_events / max(1, total_events)
        personal_ratio = personal_events / max(1, total_events)
        avg_advance_planning = advance_planning / max(1, total_events)
        
        # Determine preferred time of day
        total_time_events = sum(time_distribution.values())
        time_preferences = {time: count / max(1, total_time_events) for time, count in time_distribution.items()}
        preferred_time = max(time_preferences, key=time_preferences.get)
        
        # Map metrics to personality traits
        traits = {}
        
        # Extraversion traits
        traits["extraversion"] = self._calculate_extraversion_from_schedule(
            social_ratio,
            time_preferences["evening"] + time_preferences["night"]
        )
        
        # Conscientiousness traits
        traits["conscientiousness"] = self._calculate_conscientiousness_from_schedule(
            avg_advance_planning,
            work_ratio,
            time_preferences["morning"]
        )
        
        # Additional traits
        traits["planning_tendency"] = min(1.0, avg_advance_planning / 7)  # Normalize to 1 week
        traits["social_tendency"] = social_ratio
        traits["work_focus"] = work_ratio
        traits["morning_person"] = time_preferences["morning"]
        traits["night_owl"] = time_preferences["night"]
        
        return traits

    def _calculate_extraversion_from_apps(self, social_percentage: float, entertainment_percentage: float, 
                                         app_switching_rate: float) -> float:
        """
        Calculate extraversion score from app usage metrics.

        Args:
            social_percentage: Percentage of time spent on social apps
            entertainment_percentage: Percentage of time spent on entertainment apps
            app_switching_rate: Rate of switching between apps

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            social_percentage * 0.5 +
            entertainment_percentage * 0.3 +
            min(1.0, app_switching_rate / 10) * 0.2
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_conscientiousness_from_apps(self, productivity_percentage: float, education_percentage: float, 
                                             finance_percentage: float, night_usage_percentage: float) -> float:
        """
        Calculate conscientiousness score from app usage metrics.

        Args:
            productivity_percentage: Percentage of time spent on productivity apps
            education_percentage: Percentage of time spent on education apps
            finance_percentage: Percentage of time spent on finance apps
            night_usage_percentage: Percentage of usage during night hours

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        conscientiousness_score = (
            productivity_percentage * 0.4 +
            education_percentage * 0.3 +
            finance_percentage * 0.2 +
            (1.0 - night_usage_percentage) * 0.1  # Less night usage = higher conscientiousness
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_openness_from_apps(self, education_percentage: float, news_percentage: float, 
                                    travel_percentage: float) -> float:
        """
        Calculate openness score from app usage metrics.

        Args:
            education_percentage: Percentage of time spent on education apps
            news_percentage: Percentage of time spent on news apps
            travel_percentage: Percentage of time spent on travel apps

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            education_percentage * 0.4 +
            news_percentage * 0.3 +
            travel_percentage * 0.3
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_openness_from_browsing(self, education_percentage: float, news_percentage: float, 
                                        technology_percentage: float, domain_diversity: float) -> float:
        """
        Calculate openness score from browsing metrics.

        Args:
            education_percentage: Percentage of education sites visited
            news_percentage: Percentage of news sites visited
            technology_percentage: Percentage of technology sites visited
            domain_diversity: Diversity of domains visited

        Returns:
            Openness score (0.0 to 1.0)
        """
        openness_score = (
            education_percentage * 0.3 +
            news_percentage * 0.2 +
            technology_percentage * 0.2 +
            domain_diversity * 0.3
        )
        
        return self._normalize_trait_value(openness_score)

    def _calculate_conscientiousness_from_browsing(self, productivity_percentage: float, education_percentage: float, 
                                                 finance_percentage: float, night_browsing_percentage: float) -> float:
        """
        Calculate conscientiousness score from browsing metrics.

        Args:
            productivity_percentage: Percentage of productivity sites visited
            education_percentage: Percentage of education sites visited
            finance_percentage: Percentage of finance sites visited
            night_browsing_percentage: Percentage of browsing during night hours

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        conscientiousness_score = (
            productivity_percentage * 0.4 +
            education_percentage * 0.3 +
            finance_percentage * 0.2 +
            (1.0 - night_browsing_percentage) * 0.1  # Less night browsing = higher conscientiousness
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_conscientiousness_from_productivity(self, task_completion_rate: float, distraction_rate: float, 
                                                     deep_work_ratio: float) -> float:
        """
        Calculate conscientiousness score from productivity metrics.

        Args:
            task_completion_rate: Rate of task completion
            distraction_rate: Rate of distractions
            deep_work_ratio: Ratio of deep work sessions

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # Normalize distraction rate (lower is better)
        distraction_score = max(0.0, 1.0 - (distraction_rate / 10))
        
        conscientiousness_score = (
            task_completion_rate * 0.4 +
            distraction_score * 0.3 +
            min(1.0, deep_work_ratio) * 0.3
        )
        
        return self._normalize_trait_value(conscientiousness_score)

    def _calculate_neuroticism_from_productivity(self, distraction_rate: float, task_switching_rate: float) -> float:
        """
        Calculate neuroticism score from productivity metrics.

        Args:
            distraction_rate: Rate of distractions
            task_switching_rate: Rate of task switching

        Returns:
            Neuroticism score (0.0 to 1.0)
        """
        # Higher distraction and task switching rates may indicate higher neuroticism
        neuroticism_score = (
            min(1.0, distraction_rate / 10) * 0.6 +
            min(1.0, task_switching_rate / 5) * 0.4
        )
        
        return self._normalize_trait_value(neuroticism_score)

    def _calculate_extraversion_from_schedule(self, social_ratio: float, evening_night_preference: float) -> float:
        """
        Calculate extraversion score from schedule metrics.

        Args:
            social_ratio: Ratio of social events
            evening_night_preference: Preference for evening/night activities

        Returns:
            Extraversion score (0.0 to 1.0)
        """
        extraversion_score = (
            social_ratio * 0.7 +
            evening_night_preference * 0.3
        )
        
        return self._normalize_trait_value(extraversion_score)

    def _calculate_conscientiousness_from_schedule(self, avg_advance_planning: float, work_ratio: float, 
                                                 morning_preference: float) -> float:
        """
        Calculate conscientiousness score from schedule metrics.

        Args:
            avg_advance_planning: Average days events are planned in advance
            work_ratio: Ratio of work events
            morning_preference: Preference for morning activities

        Returns:
            Conscientiousness score (0.0 to 1.0)
        """
        # Normalize advance planning (higher is better)
        planning_score = min(1.0, avg_advance_planning / 7)  # Normalize to 1 week
        
        conscientiousness_score = (
            planning_score * 0.5 +
            work_ratio * 0.3 +
            morning_preference * 0.2
        )
        
        return self._normalize_trait_value(conscientiousness_score)