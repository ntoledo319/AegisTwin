"""
Personality Memory System

Specialized memory management for personality data and trait evolution.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)

class PersonalityMemory:
    """
    Specialized memory system for personality data and trait evolution.
    
    Manages personality profiles, trait changes over time, and
    personality-based insights.
    """
    
    def __init__(self, vector_memory: VectorMemory):
        """
        Initialize personality memory.
        
        Args:
            vector_memory: Vector memory instance
        """
        self.vector_memory = vector_memory
        self.personality_cache = {}
        self.cache_ttl = 600  # 10 minutes
    
    async def store_profile(
        self,
        user_id: str,
        profile: Dict[str, Any],
        source: str = "analysis"
    ) -> str:
        """
        Store a personality profile.
        
        Args:
            user_id: User identifier
            profile: Personality profile data
            source: Source of personality data
            
        Returns:
            Profile ID
        """
        # Create profile content
        profile_content = self._serialize_profile(profile)
        
        # Prepare metadata
        profile_metadata = {
            "profile_data": json.dumps(profile),
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "profile_type": "personality_profile"
        }
        
        # Store in vector memory
        profile_id = await self.vector_memory.store_memory(
            content=profile_content,
            category="personality",
            user_id=user_id,
            metadata=profile_metadata
        )
        
        # Clear cache for this user
        if user_id in self.personality_cache:
            del self.personality_cache[user_id]
        
        logger.info(f"Stored personality profile {profile_id} for user {user_id}")
        return profile_id
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest personality profile for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Latest personality profile or None
        """
        # Check cache first
        if user_id in self.personality_cache:
            cached_data, timestamp = self.personality_cache[user_id]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Get personality memories
        personality_memories = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="personality",
            limit=1
        )
        
        if not personality_memories:
            return None
        
        # Get the most recent profile
        latest_memory = personality_memories[0]
        
        try:
            # Deserialize profile data
            profile_data = json.loads(latest_memory["metadata"]["profile_data"])
            
            # Cache result
            self.personality_cache[user_id] = (profile_data, datetime.utcnow())
            
            return profile_data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error deserializing personality profile: {e}")
            return None
    
    async def get_profile_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get personality profile history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of profiles
            
        Returns:
            List of personality profiles with timestamps
        """
        # Get personality memories
        personality_memories = await self.vector_memory.get_user_memories(
            user_id=user_id,
            category="personality",
            limit=limit
        )
        
        profiles = []
        
        for memory in personality_memories:
            try:
                profile_data = json.loads(memory["metadata"]["profile_data"])
                
                profile_entry = {
                    "id": memory["id"],
                    "profile": profile_data,
                    "timestamp": memory["metadata"]["timestamp"],
                    "source": memory["metadata"].get("source", "unknown")
                }
                
                profiles.append(profile_entry)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error processing personality memory {memory['id']}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        profiles.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return profiles
    
    async def analyze_trait_evolution(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze how personality traits have evolved over time.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Trait evolution analysis
        """
        # Get profile history
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        profiles = await self.get_profile_history(user_id, limit=100)
        
        # Filter by date
        recent_profiles = [
            profile for profile in profiles
            if profile["timestamp"] > cutoff_date
        ]
        
        if len(recent_profiles) < 2:
            return {"error": "Insufficient profile history for evolution analysis"}
        
        # Analyze trait changes
        evolution = {
            "analysis_period_days": days,
            "profile_count": len(recent_profiles),
            "trait_changes": {},
            "overall_stability": 0.0,
            "most_changing_traits": [],
            "most_stable_traits": []
        }
        
        # Get Big Five traits from first and last profiles
        first_profile = recent_profiles[-1]  # Oldest
        last_profile = recent_profiles[0]    # Newest
        
        first_traits = first_profile["profile"].get("big_five", {})
        last_traits = last_profile["profile"].get("big_five", {})
        
        # Calculate trait changes
        trait_changes = {}
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            first_value = first_traits.get(trait, 0.5)
            last_value = last_traits.get(trait, 0.5)
            
            change = last_value - first_value
            trait_changes[trait] = {
                "initial_value": first_value,
                "current_value": last_value,
                "change": change,
                "change_percentage": (change / first_value * 100) if first_value > 0 else 0
            }
        
        evolution["trait_changes"] = trait_changes
        
        # Calculate overall stability
        total_change = sum(abs(change["change"]) for change in trait_changes.values())
        evolution["overall_stability"] = max(0.0, 1.0 - (total_change / 5.0))
        
        # Identify most changing and stable traits
        sorted_traits = sorted(
            trait_changes.items(),
            key=lambda x: abs(x[1]["change"]),
            reverse=True
        )
        
        evolution["most_changing_traits"] = [trait for trait, _ in sorted_traits[:2]]
        evolution["most_stable_traits"] = [trait for trait, _ in sorted_traits[-2:]]
        
        return evolution
    
    async def get_trait_insights(
        self,
        user_id: str,
        trait: str
    ) -> Dict[str, Any]:
        """
        Get insights about a specific personality trait.
        
        Args:
            user_id: User identifier
            trait: Trait to analyze
            
        Returns:
            Trait insights
        """
        # Get current profile
        current_profile = await self.get_profile(user_id)
        if not current_profile:
            return {"error": "No personality profile found"}
        
        # Get trait value
        big_five = current_profile.get("big_five", {})
        trait_value = big_five.get(trait, 0.5)
        
        # Get trait evolution
        evolution = await self.analyze_trait_evolution(user_id, days=30)
        trait_change = evolution.get("trait_changes", {}).get(trait, {})
        
        # Generate insights
        insights = {
            "trait": trait,
            "current_value": trait_value,
            "trait_level": self._get_trait_level(trait, trait_value),
            "description": self._get_trait_description(trait, trait_value),
            "change_over_time": trait_change,
            "implications": self._get_trait_implications(trait, trait_value),
            "recommendations": self._get_trait_recommendations(trait, trait_value)
        }
        
        return insights
    
    def _serialize_profile(self, profile: Dict[str, Any]) -> str:
        """Serialize personality profile for storage"""
        # Create a readable summary of the profile
        big_five = profile.get("big_five", {})
        communication_style = profile.get("communication_style", {})
        
        summary_parts = []
        
        # Add Big Five summary
        for trait, value in big_five.items():
            level = self._get_trait_level(trait, value)
            summary_parts.append(f"{trait.title()}: {level} ({value:.2f})")
        
        # Add communication style summary
        if communication_style:
            style_parts = []
            for key, value in communication_style.items():
                if isinstance(value, (int, float)):
                    style_parts.append(f"{key}: {value:.2f}")
            if style_parts:
                summary_parts.append(f"Communication: {', '.join(style_parts)}")
        
        return " | ".join(summary_parts)
    
    def _get_trait_level(self, trait: str, value: float) -> str:
        """Get trait level description"""
        if value < 0.3:
            return "Very Low"
        elif value < 0.5:
            return "Low"
        elif value < 0.7:
            return "Moderate"
        elif value < 0.9:
            return "High"
        else:
            return "Very High"
    
    def _get_trait_description(self, trait: str, value: float) -> str:
        """Get trait description based on value"""
        descriptions = {
            "openness": {
                "low": "Prefers routine and conventional approaches",
                "high": "Creative, curious, and open to new experiences"
            },
            "conscientiousness": {
                "low": "Flexible and spontaneous",
                "high": "Organized, disciplined, and goal-oriented"
            },
            "extraversion": {
                "low": "Quiet, reserved, and introspective",
                "high": "Outgoing, social, and energetic"
            },
            "agreeableness": {
                "low": "Competitive and skeptical",
                "high": "Cooperative, trusting, and helpful"
            },
            "neuroticism": {
                "low": "Emotionally stable and calm",
                "high": "Sensitive to stress and emotional"
            }
        }
        
        level = "low" if value < 0.5 else "high"
        return descriptions.get(trait, {}).get(level, "Moderate level")
    
    def _get_trait_implications(self, trait: str, value: float) -> List[str]:
        """Get implications of trait level"""
        implications = {
            "openness": {
                "low": [
                    "Prefers structured environments",
                    "Values tradition and stability",
                    "May be resistant to change"
                ],
                "high": [
                    "Thrives in creative environments",
                    "Enjoys learning new things",
                    "May struggle with routine tasks"
                ]
            },
            "conscientiousness": {
                "low": [
                    "Adapts well to changing situations",
                    "May struggle with long-term planning",
                    "Values flexibility over structure"
                ],
                "high": [
                    "Excellent at planning and organization",
                    "Reliable and dependable",
                    "May be inflexible at times"
                ]
            },
            "extraversion": {
                "low": [
                    "Prefers quiet, focused environments",
                    "Thinks before speaking",
                    "May need time to recharge after social interaction"
                ],
                "high": [
                    "Energized by social interaction",
                    "Comfortable in group settings",
                    "May struggle with solitary tasks"
                ]
            },
            "agreeableness": {
                "low": [
                    "Comfortable with conflict and competition",
                    "May be more critical and skeptical",
                    "Values independence"
                ],
                "high": [
                    "Excellent at building relationships",
                    "Avoids conflict and seeks harmony",
                    "May struggle with difficult decisions"
                ]
            },
            "neuroticism": {
                "low": [
                    "Handles stress well",
                    "Remains calm under pressure",
                    "May seem emotionally distant"
                ],
                "high": [
                    "Highly aware of emotions",
                    "May be sensitive to criticism",
                    "Experiences emotions intensely"
                ]
            }
        }
        
        level = "low" if value < 0.5 else "high"
        return implications.get(trait, {}).get(level, ["Moderate implications"])
    
    def _get_trait_recommendations(self, trait: str, value: float) -> List[str]:
        """Get recommendations based on trait level"""
        recommendations = {
            "openness": {
                "low": [
                    "Consider trying new approaches gradually",
                    "Look for structured ways to be creative",
                    "Value your preference for stability"
                ],
                "high": [
                    "Channel creativity into productive projects",
                    "Balance exploration with completion",
                    "Help others see new possibilities"
                ]
            },
            "conscientiousness": {
                "low": [
                    "Use tools and systems to stay organized",
                    "Set small, achievable goals",
                    "Leverage your adaptability"
                ],
                "high": [
                    "Share your organizational skills with others",
                    "Be flexible when plans need to change",
                    "Use your reliability as a strength"
                ]
            },
            "extraversion": {
                "low": [
                    "Communicate your need for quiet time",
                    "Prepare for social situations in advance",
                    "Value your thoughtful approach"
                ],
                "high": [
                    "Use your energy to motivate others",
                    "Balance social time with reflection",
                    "Help create inclusive environments"
                ]
            },
            "agreeableness": {
                "low": [
                    "Use your critical thinking constructively",
                    "Be direct while remaining respectful",
                    "Value your independence"
                ],
                "high": [
                    "Use your empathy to help others",
                    "Practice saying no when needed",
                    "Help resolve conflicts diplomatically"
                ]
            },
            "neuroticism": {
                "low": [
                    "Use your calmness to help others",
                    "Don't dismiss others' emotional needs",
                    "Value your emotional stability"
                ],
                "high": [
                    "Develop stress management techniques",
                    "Use your emotional awareness as a strength",
                    "Seek support when needed"
                ]
            }
        }
        
        level = "low" if value < 0.5 else "high"
        return recommendations.get(trait, {}).get(level, ["Continue developing this trait"])
    
    async def compare_profiles(
        self,
        user_id: str,
        profile1_id: str,
        profile2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two personality profiles.
        
        Args:
            user_id: User identifier
            profile1_id: First profile ID
            profile2_id: Second profile ID
            
        Returns:
            Profile comparison
        """
        # Get both profiles
        profile1_memory = await self.vector_memory.get_memory_by_id(profile1_id)
        profile2_memory = await self.vector_memory.get_memory_by_id(profile2_id)
        
        if not profile1_memory or not profile2_memory:
            return {"error": "One or both profiles not found"}
        
        try:
            profile1_data = json.loads(profile1_memory["metadata"]["profile_data"])
            profile2_data = json.loads(profile2_memory["metadata"]["profile_data"])
        except (json.JSONDecodeError, KeyError) as e:
            return {"error": f"Error parsing profile data: {e}"}
        
        # Compare Big Five traits
        big_five1 = profile1_data.get("big_five", {})
        big_five2 = profile2_data.get("big_five", {})
        
        comparison = {
            "profile1_timestamp": profile1_memory["metadata"]["timestamp"],
            "profile2_timestamp": profile2_memory["metadata"]["timestamp"],
            "trait_comparison": {},
            "overall_similarity": 0.0,
            "significant_changes": []
        }
        
        # Compare each trait
        trait_differences = []
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            value1 = big_five1.get(trait, 0.5)
            value2 = big_five2.get(trait, 0.5)
            difference = abs(value2 - value1)
            
            comparison["trait_comparison"][trait] = {
                "profile1_value": value1,
                "profile2_value": value2,
                "difference": difference,
                "change_direction": "increase" if value2 > value1 else "decrease" if value2 < value1 else "stable"
            }
            
            trait_differences.append(difference)
            
            # Flag significant changes (>0.2 difference)
            if difference > 0.2:
                comparison["significant_changes"].append({
                    "trait": trait,
                    "change": difference,
                    "direction": comparison["trait_comparison"][trait]["change_direction"]
                })
        
        # Calculate overall similarity
        comparison["overall_similarity"] = 1.0 - (sum(trait_differences) / len(trait_differences))
        
        return comparison
