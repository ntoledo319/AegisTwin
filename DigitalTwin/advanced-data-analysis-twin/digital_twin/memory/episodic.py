"""
Episodic Memory for the Digital Twin.

This module provides functionality for storing and retrieving episodic memories,
which are memories of specific events or experiences.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
import datetime

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Module for managing episodic memories.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the episodic memory module.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.memory_dir = self.config.get("episodic_memory_dir", "episodic_memories")
        self.mongodb = None
        self._initialize_mongodb()
        logger.info("Episodic Memory module initialized")

    def _initialize_mongodb(self) -> None:
        """
        Initialize MongoDB connection for memory storage.
        """
        try:
            # Try to import the MongoDB client
            from ....core.db.mongodb import MongoDBClient
            
            # Initialize the MongoDB client
            self.mongodb = MongoDBClient()
            logger.info("MongoDB client initialized for episodic memory")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {str(e)}")
            logger.warning("Using fallback file-based storage for episodic memory")
            self.mongodb = None
            
            # Create memory directory if it doesn't exist
            os.makedirs(self.memory_dir, exist_ok=True)

    async def store(self, memory: Dict[str, Any]) -> None:
        """
        Store an episodic memory.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            logger.warning("Cannot store episodic memory: missing memory_id or user_id")
            return
            
        # Add memory type if not present
        if "memory_type" not in memory:
            memory["memory_type"] = "episodic"
            
        # Add importance score if not present
        if "importance" not in memory:
            memory["importance"] = await self._calculate_importance(memory)
            
        # Add tags if not present
        if "tags" not in memory:
            memory["tags"] = await self._extract_tags(memory)
            
        # Add entities if not present
        if "entities" not in memory:
            memory["entities"] = await self._extract_entities(memory)
            
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                await self.mongodb.insert_one(
                    collection="episodic_memories",
                    document=memory
                )
                
                logger.debug(f"Stored episodic memory {memory_id} in MongoDB")
            except Exception as e:
                logger.error(f"Error storing episodic memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based storage")
                await self._fallback_store(memory)
        else:
            # Use fallback file-based storage
            await self._fallback_store(memory)

    async def _fallback_store(self, memory: Dict[str, Any]) -> None:
        """
        Fallback method to store an episodic memory using file-based storage.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            return
            
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.memory_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save memory to file
        memory_path = os.path.join(user_dir, f"{memory_id}.json")
        
        with open(memory_path, 'w') as f:
            json.dump(memory, f)
            
        logger.debug(f"Stored episodic memory {memory_id} using file-based storage")

    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an episodic memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memory = await self.mongodb.find_one(
                    collection="episodic_memories",
                    query={"memory_id": memory_id}
                )
                
                if memory:
                    logger.debug(f"Retrieved episodic memory {memory_id} from MongoDB")
                    return memory
                    
            except Exception as e:
                logger.error(f"Error retrieving episodic memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get(memory_id)

    async def _fallback_get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to get an episodic memory using file-based storage.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # Search for the memory file in all user directories
        for user_dir in os.listdir(self.memory_dir):
            user_dir_path = os.path.join(self.memory_dir, user_dir)
            
            if os.path.isdir(user_dir_path):
                memory_path = os.path.join(user_dir_path, f"{memory_id}.json")
                
                if os.path.exists(memory_path):
                    try:
                        with open(memory_path, 'r') as f:
                            memory = json.load(f)
                            logger.debug(f"Retrieved episodic memory {memory_id} from file-based storage")
                            return memory
                    except Exception as e:
                        logger.error(f"Error reading memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Episodic memory {memory_id} not found")
        return None

    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an episodic memory.

        Args:
            memory_id: Memory ID
            updates: Updates to apply

        Returns:
            True if successful, False otherwise
        """
        # Get the current memory
        memory = await self.get(memory_id)
        if not memory:
            logger.warning(f"Cannot update episodic memory {memory_id}: not found")
            return False
            
        # Apply updates
        for key, value in updates.items():
            # Don't update memory_id, user_id, or memory_type
            if key not in ["memory_id", "user_id", "memory_type"]:
                memory[key] = value
                
        # Update importance if relevant fields changed
        importance_fields = ["title", "description", "emotions", "context"]
        if any(field in updates for field in importance_fields):
            memory["importance"] = await self._calculate_importance(memory)
            
        # Update tags if relevant fields changed
        tag_fields = ["title", "description", "context", "emotions"]
        if any(field in updates for field in tag_fields):
            memory["tags"] = await self._extract_tags(memory)
            
        # Update entities if relevant fields changed
        entity_fields = ["title", "description", "context", "people", "locations"]
        if any(field in updates for field in entity_fields):
            memory["entities"] = await self._extract_entities(memory)
            
        # Update timestamp
        memory["updated_at"] = datetime.datetime.now().isoformat()
        
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.update_one(
                    collection="episodic_memories",
                    query={"memory_id": memory_id},
                    update={"$set": memory}
                )
                
                if result and result.modified_count > 0:
                    logger.debug(f"Updated episodic memory {memory_id} in MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to update episodic memory {memory_id} in MongoDB")
                    
            except Exception as e:
                logger.error(f"Error updating episodic memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based update")
                
        # Use fallback file-based update
        return await self._fallback_update(memory)

    async def _fallback_update(self, memory: Dict[str, Any]) -> bool:
        """
        Fallback method to update an episodic memory using file-based storage.

        Args:
            memory: Updated memory dictionary

        Returns:
            True if successful, False otherwise
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            return False
            
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.memory_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save updated memory to file
        memory_path = os.path.join(user_dir, f"{memory_id}.json")
        
        try:
            with open(memory_path, 'w') as f:
                json.dump(memory, f)
                
            logger.debug(f"Updated episodic memory {memory_id} using file-based storage")
            return True
        except Exception as e:
            logger.error(f"Error updating memory file {memory_path}: {str(e)}")
            return False

    async def delete(self, memory_id: str) -> bool:
        """
        Delete an episodic memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.delete_one(
                    collection="episodic_memories",
                    query={"memory_id": memory_id}
                )
                
                if result and result.deleted_count > 0:
                    logger.debug(f"Deleted episodic memory {memory_id} from MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to delete episodic memory {memory_id} from MongoDB")
                    
            except Exception as e:
                logger.error(f"Error deleting episodic memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based deletion")
                
        # Use fallback file-based deletion
        return await self._fallback_delete(memory_id)

    async def _fallback_delete(self, memory_id: str) -> bool:
        """
        Fallback method to delete an episodic memory using file-based storage.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # Search for the memory file in all user directories
        for user_dir in os.listdir(self.memory_dir):
            user_dir_path = os.path.join(self.memory_dir, user_dir)
            
            if os.path.isdir(user_dir_path):
                memory_path = os.path.join(user_dir_path, f"{memory_id}.json")
                
                if os.path.exists(memory_path):
                    try:
                        os.remove(memory_path)
                        logger.debug(f"Deleted episodic memory {memory_id} from file-based storage")
                        return True
                    except Exception as e:
                        logger.error(f"Error deleting memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Episodic memory {memory_id} not found for deletion")
        return False

    async def consolidate(self, user_id: str) -> Dict[str, Any]:
        """
        Consolidate episodic memories for a user.

        Args:
            user_id: User ID

        Returns:
            Consolidation results
        """
        # Get all episodic memories for the user
        memories = await self._get_user_memories(user_id)
        
        # Group memories by context
        context_groups = {}
        for memory in memories:
            context = json.dumps(memory.get("context", {}))
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(memory)
            
        # Group memories by time period
        time_groups = self._group_by_time_period(memories)
        
        # Identify recurring patterns
        patterns = await self._identify_patterns(memories)
        
        # Generate insights
        insights = await self._generate_insights(memories, patterns)
        
        # Update memory importance based on patterns
        await self._update_importance_based_on_patterns(memories, patterns)
        
        logger.info(f"Consolidated {len(memories)} episodic memories for user {user_id}")
        
        return {
            "memory_count": len(memories),
            "context_groups": len(context_groups),
            "time_groups": len(time_groups),
            "patterns": patterns,
            "insights": insights
        }

    async def _get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all episodic memories for a user.

        Args:
            user_id: User ID

        Returns:
            List of memory dictionaries
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memories = await self.mongodb.find(
                    collection="episodic_memories",
                    query={"user_id": user_id}
                )
                
                if memories:
                    logger.debug(f"Retrieved {len(memories)} episodic memories for user {user_id} from MongoDB")
                    return memories
                    
            except Exception as e:
                logger.error(f"Error retrieving episodic memories from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get_user_memories(user_id)

    async def _fallback_get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fallback method to get all episodic memories for a user using file-based storage.

        Args:
            user_id: User ID

        Returns:
            List of memory dictionaries
        """
        memories = []
        
        # Check if user directory exists
        user_dir = os.path.join(self.memory_dir, user_id)
        if not os.path.exists(user_dir):
            return memories
            
        # Get all memory files
        memory_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
        
        # Load all memories
        for file_name in memory_files:
            file_path = os.path.join(user_dir, file_name)
            try:
                with open(file_path, 'r') as f:
                    memory = json.load(f)
                    memories.append(memory)
            except Exception as e:
                logger.error(f"Error loading memory file {file_path}: {str(e)}")
                
        logger.debug(f"Retrieved {len(memories)} episodic memories for user {user_id} from file-based storage")
        return memories

    def _group_by_time_period(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group memories by time period.

        Args:
            memories: List of memory dictionaries

        Returns:
            Dictionary of time period groups
        """
        time_groups = {
            "today": [],
            "yesterday": [],
            "this_week": [],
            "this_month": [],
            "this_year": [],
            "older": []
        }
        
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - datetime.timedelta(days=1)
        this_week = today - datetime.timedelta(days=today.weekday())
        this_month = today.replace(day=1)
        this_year = today.replace(month=1, day=1)
        
        for memory in memories:
            try:
                created_at = datetime.datetime.fromisoformat(memory.get("created_at", ""))
                
                if created_at >= today:
                    time_groups["today"].append(memory)
                elif created_at >= yesterday:
                    time_groups["yesterday"].append(memory)
                elif created_at >= this_week:
                    time_groups["this_week"].append(memory)
                elif created_at >= this_month:
                    time_groups["this_month"].append(memory)
                elif created_at >= this_year:
                    time_groups["this_year"].append(memory)
                else:
                    time_groups["older"].append(memory)
            except (ValueError, TypeError):
                time_groups["older"].append(memory)
                
        return time_groups

    async def _identify_patterns(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify recurring patterns in episodic memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Count occurrences of entities
        entity_counts = {}
        for memory in memories:
            entities = memory.get("entities", [])
            for entity in entities:
                if entity not in entity_counts:
                    entity_counts[entity] = 0
                entity_counts[entity] += 1
                
        # Identify frequent entities
        frequent_entities = [entity for entity, count in entity_counts.items() if count >= 3]
        
        if frequent_entities:
            patterns.append({
                "type": "frequent_entities",
                "entities": frequent_entities,
                "description": f"Frequently mentioned entities: {', '.join(frequent_entities[:5])}"
            })
            
        # Count occurrences of emotions
        emotion_counts = {}
        for memory in memories:
            emotions = memory.get("emotions", [])
            for emotion in emotions:
                if emotion not in emotion_counts:
                    emotion_counts[emotion] = 0
                emotion_counts[emotion] += 1
                
        # Identify frequent emotions
        frequent_emotions = [emotion for emotion, count in emotion_counts.items() if count >= 3]
        
        if frequent_emotions:
            patterns.append({
                "type": "frequent_emotions",
                "emotions": frequent_emotions,
                "description": f"Frequently experienced emotions: {', '.join(frequent_emotions[:5])}"
            })
            
        # Identify location patterns
        location_counts = {}
        for memory in memories:
            context = memory.get("context", {})
            location = context.get("location", "")
            if location:
                if location not in location_counts:
                    location_counts[location] = 0
                location_counts[location] += 1
                
        # Identify frequent locations
        frequent_locations = [location for location, count in location_counts.items() if count >= 3]
        
        if frequent_locations:
            patterns.append({
                "type": "frequent_locations",
                "locations": frequent_locations,
                "description": f"Frequently visited locations: {', '.join(frequent_locations[:5])}"
            })
            
        return patterns

    async def _generate_insights(self, memories: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Generate insights from episodic memories and patterns.

        Args:
            memories: List of memory dictionaries
            patterns: List of identified patterns

        Returns:
            List of insights
        """
        insights = []
        
        # Generate insights based on patterns
        for pattern in patterns:
            if pattern["type"] == "frequent_entities":
                insights.append(f"You frequently interact with {', '.join(pattern['entities'][:3])}")
                
            elif pattern["type"] == "frequent_emotions":
                positive_emotions = ["happy", "joy", "excited", "content", "grateful", "satisfied", "proud"]
                negative_emotions = ["sad", "angry", "frustrated", "anxious", "stressed", "disappointed", "fearful"]
                
                positive_count = sum(1 for emotion in pattern["emotions"] if emotion.lower() in positive_emotions)
                negative_count = sum(1 for emotion in pattern["emotions"] if emotion.lower() in negative_emotions)
                
                if positive_count > negative_count:
                    insights.append("Your memories tend to be associated with positive emotions")
                elif negative_count > positive_count:
                    insights.append("Your memories tend to be associated with negative emotions")
                    
            elif pattern["type"] == "frequent_locations":
                insights.append(f"You spend significant time at {', '.join(pattern['locations'][:3])}")
                
        # Generate insights based on memory importance
        important_memories = [m for m in memories if m.get("importance", 0) >= 0.8]
        if important_memories:
            insights.append(f"You have {len(important_memories)} highly important memories")
            
        # Generate insights based on memory recency
        try:
            recent_cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
            recent_memories = [m for m in memories if datetime.datetime.fromisoformat(m.get("created_at", "")) >= recent_cutoff]
            if recent_memories:
                insights.append(f"You have {len(recent_memories)} memories from the past month")
        except (ValueError, TypeError):
            pass
            
        return insights

    async def _update_importance_based_on_patterns(self, memories: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> None:
        """
        Update memory importance based on identified patterns.

        Args:
            memories: List of memory dictionaries
            patterns: List of identified patterns
        """
        # Extract pattern entities
        pattern_entities = set()
        for pattern in patterns:
            if pattern["type"] == "frequent_entities":
                pattern_entities.update(pattern["entities"])
                
        # Extract pattern emotions
        pattern_emotions = set()
        for pattern in patterns:
            if pattern["type"] == "frequent_emotions":
                pattern_emotions.update(pattern["emotions"])
                
        # Extract pattern locations
        pattern_locations = set()
        for pattern in patterns:
            if pattern["type"] == "frequent_locations":
                pattern_locations.update(pattern["locations"])
                
        # Update importance for each memory
        for memory in memories:
            memory_id = memory.get("memory_id")
            if not memory_id:
                continue
                
            importance_boost = 0.0
            
            # Check if memory contains pattern entities
            memory_entities = set(memory.get("entities", []))
            entity_overlap = memory_entities.intersection(pattern_entities)
            if entity_overlap:
                importance_boost += 0.1 * len(entity_overlap)
                
            # Check if memory contains pattern emotions
            memory_emotions = set(memory.get("emotions", []))
            emotion_overlap = memory_emotions.intersection(pattern_emotions)
            if emotion_overlap:
                importance_boost += 0.1 * len(emotion_overlap)
                
            # Check if memory contains pattern locations
            context = memory.get("context", {})
            location = context.get("location", "")
            if location in pattern_locations:
                importance_boost += 0.1
                
            # Apply importance boost if significant
            if importance_boost >= 0.1:
                current_importance = memory.get("importance", 0.5)
                new_importance = min(1.0, current_importance + importance_boost)
                
                # Update memory if importance changed significantly
                if new_importance - current_importance >= 0.1:
                    await self.update(memory_id, {"importance": new_importance})

    async def _calculate_importance(self, memory: Dict[str, Any]) -> float:
        """
        Calculate importance score for an episodic memory.

        Args:
            memory: Memory dictionary

        Returns:
            Importance score (0.0 to 1.0)
        """
        importance_score = 0.5  # Default importance
        
        # Check for explicit importance
        if "importance" in memory and isinstance(memory["importance"], (int, float)):
            return max(0.0, min(1.0, float(memory["importance"])))
            
        # Factor 1: Emotional intensity
        emotions = memory.get("emotions", [])
        intense_emotions = ["love", "grief", "ecstatic", "devastated", "furious", "terrified", "overjoyed"]
        emotion_score = 0.0
        
        if emotions:
            # Check for intense emotions
            intense_count = sum(1 for e in emotions if e.lower() in intense_emotions)
            emotion_score = min(1.0, intense_count * 0.2 + len(emotions) * 0.1)
            
        # Factor 2: People involvement
        people = memory.get("people", [])
        people_score = min(1.0, len(people) * 0.1)
        
        # Factor 3: Duration
        context = memory.get("context", {})
        duration = context.get("duration", 0)
        duration_score = 0.0
        
        if duration > 0:
            # Longer events might be more important
            duration_score = min(1.0, duration / 480)  # Normalize to 8 hours
            
        # Factor 4: Recency
        recency_score = 0.0
        created_at = memory.get("created_at", "")
        
        if created_at:
            try:
                created_datetime = datetime.datetime.fromisoformat(created_at)
                now = datetime.datetime.now()
                days_ago = (now - created_datetime).days
                
                # More recent memories might be more important
                recency_score = max(0.0, 1.0 - (days_ago / 30))  # Normalize to 30 days
            except (ValueError, TypeError):
                pass
                
        # Factor 5: Explicit tags
        tags = memory.get("tags", [])
        important_tags = ["important", "significant", "milestone", "achievement", "special"]
        tag_score = 0.0
        
        if tags:
            # Check for importance-indicating tags
            important_count = sum(1 for t in tags if t.lower() in important_tags)
            tag_score = min(1.0, important_count * 0.2)
            
        # Combine factors with weights
        importance_score = (
            emotion_score * 0.3 +
            people_score * 0.2 +
            duration_score * 0.1 +
            recency_score * 0.2 +
            tag_score * 0.2
        )
        
        return max(0.1, min(1.0, importance_score))

    async def _extract_tags(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract tags from an episodic memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of tags
        """
        tags = set()
        
        # Check for explicit tags
        if "tags" in memory and isinstance(memory["tags"], list):
            tags.update(memory["tags"])
            
        # Extract tags from title
        title = memory.get("title", "")
        if title:
            # Add significant words from title
            words = title.lower().split()
            significant_words = [w for w in words if len(w) > 3 and w not in ["this", "that", "with", "from", "about"]]
            tags.update(significant_words[:3])  # Add up to 3 significant words
            
        # Extract tags from emotions
        emotions = memory.get("emotions", [])
        tags.update(emotions)
        
        # Extract tags from context
        context = memory.get("context", {})
        
        # Add activity as tag
        activity = context.get("activity", "")
        if activity:
            tags.add(activity.lower())
            
        # Add location as tag
        location = context.get("location", "")
        if location:
            tags.add(location.lower())
            
        # Add time of day as tag
        time_of_day = context.get("time_of_day", "")
        if time_of_day:
            tags.add(time_of_day.lower())
            
        return list(tags)

    async def _extract_entities(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract entities from an episodic memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of entities
        """
        entities = set()
        
        # Extract people
        people = memory.get("people", [])
        entities.update(people)
        
        # Extract locations
        context = memory.get("context", {})
        location = context.get("location", "")
        if location:
            entities.add(location)
            
        # Extract organizations
        organizations = memory.get("organizations", [])
        entities.update(organizations)
        
        # Extract objects
        objects = memory.get("objects", [])
        entities.update(objects)
        
        return list(entities)