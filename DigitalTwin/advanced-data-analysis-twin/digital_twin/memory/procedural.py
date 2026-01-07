"""
Procedural Memory for the Digital Twin.

This module provides functionality for storing and retrieving procedural memories,
which are memories of how to perform tasks or skills.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
import datetime

logger = logging.getLogger(__name__)


class ProceduralMemory:
    """
    Module for managing procedural memories.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the procedural memory module.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.memory_dir = self.config.get("procedural_memory_dir", "procedural_memories")
        self.mongodb = None
        self._initialize_mongodb()
        logger.info("Procedural Memory module initialized")

    def _initialize_mongodb(self) -> None:
        """
        Initialize MongoDB connection for memory storage.
        """
        try:
            # Try to import the MongoDB client
            from ....core.db.mongodb import MongoDBClient
            
            # Initialize the MongoDB client
            self.mongodb = MongoDBClient()
            logger.info("MongoDB client initialized for procedural memory")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {str(e)}")
            logger.warning("Using fallback file-based storage for procedural memory")
            self.mongodb = None
            
            # Create memory directory if it doesn't exist
            os.makedirs(self.memory_dir, exist_ok=True)

    async def store(self, memory: Dict[str, Any]) -> None:
        """
        Store a procedural memory.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            logger.warning("Cannot store procedural memory: missing memory_id or user_id")
            return
            
        # Add memory type if not present
        if "memory_type" not in memory:
            memory["memory_type"] = "procedural"
            
        # Add proficiency level if not present
        if "proficiency" not in memory:
            memory["proficiency"] = await self._calculate_proficiency(memory)
            
        # Add tags if not present
        if "tags" not in memory:
            memory["tags"] = await self._extract_tags(memory)
            
        # Add prerequisites if not present
        if "prerequisites" not in memory:
            memory["prerequisites"] = await self._extract_prerequisites(memory)
            
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                await self.mongodb.insert_one(
                    collection="procedural_memories",
                    document=memory
                )
                
                logger.debug(f"Stored procedural memory {memory_id} in MongoDB")
            except Exception as e:
                logger.error(f"Error storing procedural memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based storage")
                await self._fallback_store(memory)
        else:
            # Use fallback file-based storage
            await self._fallback_store(memory)

    async def _fallback_store(self, memory: Dict[str, Any]) -> None:
        """
        Fallback method to store a procedural memory using file-based storage.

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
            
        logger.debug(f"Stored procedural memory {memory_id} using file-based storage")

    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a procedural memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dictionary or None if not found
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memory = await self.mongodb.find_one(
                    collection="procedural_memories",
                    query={"memory_id": memory_id}
                )
                
                if memory:
                    logger.debug(f"Retrieved procedural memory {memory_id} from MongoDB")
                    return memory
                    
            except Exception as e:
                logger.error(f"Error retrieving procedural memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get(memory_id)

    async def _fallback_get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to get a procedural memory using file-based storage.

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
                            logger.debug(f"Retrieved procedural memory {memory_id} from file-based storage")
                            return memory
                    except Exception as e:
                        logger.error(f"Error reading memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Procedural memory {memory_id} not found")
        return None

    async def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a procedural memory.

        Args:
            memory_id: Memory ID
            updates: Updates to apply

        Returns:
            True if successful, False otherwise
        """
        # Get the current memory
        memory = await self.get(memory_id)
        if not memory:
            logger.warning(f"Cannot update procedural memory {memory_id}: not found")
            return False
            
        # Apply updates
        for key, value in updates.items():
            # Don't update memory_id, user_id, or memory_type
            if key not in ["memory_id", "user_id", "memory_type"]:
                memory[key] = value
                
        # Update proficiency if relevant fields changed
        proficiency_fields = ["task", "steps", "execution_count", "success_rate"]
        if any(field in updates for field in proficiency_fields):
            memory["proficiency"] = await self._calculate_proficiency(memory)
            
        # Update tags if relevant fields changed
        tag_fields = ["task", "category", "context"]
        if any(field in updates for field in tag_fields):
            memory["tags"] = await self._extract_tags(memory)
            
        # Update prerequisites if relevant fields changed
        prerequisite_fields = ["task", "steps", "prerequisites"]
        if any(field in updates for field in prerequisite_fields):
            memory["prerequisites"] = await self._extract_prerequisites(memory)
            
        # Update timestamp
        memory["updated_at"] = datetime.datetime.now().isoformat()
        
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.update_one(
                    collection="procedural_memories",
                    query={"memory_id": memory_id},
                    update={"$set": memory}
                )
                
                if result and result.modified_count > 0:
                    logger.debug(f"Updated procedural memory {memory_id} in MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to update procedural memory {memory_id} in MongoDB")
                    
            except Exception as e:
                logger.error(f"Error updating procedural memory in MongoDB: {str(e)}")
                logger.warning("Falling back to file-based update")
                
        # Use fallback file-based update
        return await self._fallback_update(memory)

    async def _fallback_update(self, memory: Dict[str, Any]) -> bool:
        """
        Fallback method to update a procedural memory using file-based storage.

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
                
            logger.debug(f"Updated procedural memory {memory_id} using file-based storage")
            return True
        except Exception as e:
            logger.error(f"Error updating memory file {memory_path}: {str(e)}")
            return False

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a procedural memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                result = await self.mongodb.delete_one(
                    collection="procedural_memories",
                    query={"memory_id": memory_id}
                )
                
                if result and result.deleted_count > 0:
                    logger.debug(f"Deleted procedural memory {memory_id} from MongoDB")
                    return True
                else:
                    logger.warning(f"Failed to delete procedural memory {memory_id} from MongoDB")
                    
            except Exception as e:
                logger.error(f"Error deleting procedural memory from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based deletion")
                
        # Use fallback file-based deletion
        return await self._fallback_delete(memory_id)

    async def _fallback_delete(self, memory_id: str) -> bool:
        """
        Fallback method to delete a procedural memory using file-based storage.

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
                        logger.debug(f"Deleted procedural memory {memory_id} from file-based storage")
                        return True
                    except Exception as e:
                        logger.error(f"Error deleting memory file {memory_path}: {str(e)}")
                        
        logger.warning(f"Procedural memory {memory_id} not found for deletion")
        return False

    async def consolidate(self, user_id: str) -> Dict[str, Any]:
        """
        Consolidate procedural memories for a user.

        Args:
            user_id: User ID

        Returns:
            Consolidation results
        """
        # Get all procedural memories for the user
        memories = await self._get_user_memories(user_id)
        
        # Group memories by category
        category_groups = {}
        for memory in memories:
            category = memory.get("category", "general")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(memory)
            
        # Identify skill hierarchies
        skill_hierarchies = await self._identify_skill_hierarchies(memories)
        
        # Identify skill gaps
        skill_gaps = await self._identify_skill_gaps(memories)
        
        # Update memory proficiency based on usage
        await self._update_proficiency_based_on_usage(memories)
        
        # Build skill graph
        skill_graph = await self._build_skill_graph(memories)
        
        logger.info(f"Consolidated {len(memories)} procedural memories for user {user_id}")
        
        return {
            "memory_count": len(memories),
            "category_groups": len(category_groups),
            "skill_hierarchies": skill_hierarchies,
            "skill_gaps": skill_gaps,
            "skill_graph": {
                "nodes": len(skill_graph["nodes"]),
                "edges": len(skill_graph["edges"])
            }
        }

    async def _get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all procedural memories for a user.

        Args:
            user_id: User ID

        Returns:
            List of memory dictionaries
        """
        # If MongoDB is available, use it
        if self.mongodb:
            try:
                memories = await self.mongodb.find(
                    collection="procedural_memories",
                    query={"user_id": user_id}
                )
                
                if memories:
                    logger.debug(f"Retrieved {len(memories)} procedural memories for user {user_id} from MongoDB")
                    return memories
                    
            except Exception as e:
                logger.error(f"Error retrieving procedural memories from MongoDB: {str(e)}")
                logger.warning("Falling back to file-based retrieval")
                
        # Use fallback file-based retrieval
        return await self._fallback_get_user_memories(user_id)

    async def _fallback_get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Fallback method to get all procedural memories for a user using file-based storage.

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
                
        logger.debug(f"Retrieved {len(memories)} procedural memories for user {user_id} from file-based storage")
        return memories

    async def _identify_skill_hierarchies(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify skill hierarchies in procedural memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of identified skill hierarchies
        """
        hierarchies = []
        
        # Create a map of tasks to memories
        task_map = {}
        for memory in memories:
            task = memory.get("task", "").lower()
            if task:
                task_map[task] = memory
                
        # Identify prerequisite relationships
        for memory in memories:
            task = memory.get("task", "").lower()
            prerequisites = memory.get("prerequisites", [])
            
            if task and prerequisites:
                # Check if prerequisites exist as tasks
                existing_prerequisites = []
                for prereq in prerequisites:
                    prereq_lower = prereq.lower()
                    if prereq_lower in task_map:
                        existing_prerequisites.append({
                            "task": prereq,
                            "memory_id": task_map[prereq_lower].get("memory_id")
                        })
                        
                if existing_prerequisites:
                    hierarchies.append({
                        "task": task,
                        "memory_id": memory.get("memory_id"),
                        "prerequisites": existing_prerequisites
                    })
                    
        return hierarchies

    async def _identify_skill_gaps(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify skill gaps in procedural memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of identified skill gaps
        """
        skill_gaps = []
        
        # Create a map of tasks to memories
        task_map = {}
        for memory in memories:
            task = memory.get("task", "").lower()
            if task:
                task_map[task] = memory
                
        # Identify missing prerequisites
        for memory in memories:
            task = memory.get("task", "").lower()
            prerequisites = memory.get("prerequisites", [])
            
            if task and prerequisites:
                # Check for missing prerequisites
                missing_prerequisites = []
                for prereq in prerequisites:
                    prereq_lower = prereq.lower()
                    if prereq_lower not in task_map:
                        missing_prerequisites.append(prereq)
                        
                if missing_prerequisites:
                    skill_gaps.append({
                        "task": task,
                        "memory_id": memory.get("memory_id"),
                        "missing_prerequisites": missing_prerequisites,
                        "gap_type": "missing_prerequisites"
                    })
                    
        # Identify low proficiency skills
        low_proficiency_threshold = 0.4
        for memory in memories:
            proficiency = memory.get("proficiency", 0.5)
            if proficiency < low_proficiency_threshold:
                skill_gaps.append({
                    "task": memory.get("task", ""),
                    "memory_id": memory.get("memory_id"),
                    "proficiency": proficiency,
                    "gap_type": "low_proficiency"
                })
                
        # Identify incomplete procedures
        for memory in memories:
            steps = memory.get("steps", [])
            if len(steps) < 2:  # A procedure with fewer than 2 steps might be incomplete
                skill_gaps.append({
                    "task": memory.get("task", ""),
                    "memory_id": memory.get("memory_id"),
                    "steps_count": len(steps),
                    "gap_type": "incomplete_procedure"
                })
                
        return skill_gaps

    async def _update_proficiency_based_on_usage(self, memories: List[Dict[str, Any]]) -> None:
        """
        Update memory proficiency based on usage patterns.

        Args:
            memories: List of memory dictionaries
        """
        for memory in memories:
            memory_id = memory.get("memory_id")
            if not memory_id:
                continue
                
            # Check if usage metrics are available
            execution_count = memory.get("execution_count", 0)
            success_rate = memory.get("success_rate", 0.0)
            last_execution = memory.get("last_execution", "")
            
            # Skip if no usage data
            if execution_count == 0:
                continue
                
            # Calculate proficiency adjustment based on usage
            proficiency_adjustment = 0.0
            
            # Factor 1: Execution count
            if execution_count >= 10:
                proficiency_adjustment += 0.1
            elif execution_count >= 5:
                proficiency_adjustment += 0.05
                
            # Factor 2: Success rate
            if success_rate >= 0.9:
                proficiency_adjustment += 0.1
            elif success_rate >= 0.7:
                proficiency_adjustment += 0.05
            elif success_rate < 0.5:
                proficiency_adjustment -= 0.1
                
            # Factor 3: Recency
            if last_execution:
                try:
                    last_execution_datetime = datetime.datetime.fromisoformat(last_execution)
                    now = datetime.datetime.now()
                    days_since_last_execution = (now - last_execution_datetime).days
                    
                    # Decay proficiency if not used recently
                    if days_since_last_execution > 90:  # More than 3 months
                        proficiency_adjustment -= 0.1
                    elif days_since_last_execution > 30:  # More than 1 month
                        proficiency_adjustment -= 0.05
                except (ValueError, TypeError):
                    pass
                    
            # Apply proficiency adjustment if significant
            if abs(proficiency_adjustment) >= 0.05:
                current_proficiency = memory.get("proficiency", 0.5)
                new_proficiency = max(0.1, min(1.0, current_proficiency + proficiency_adjustment))
                
                # Update memory if proficiency changed significantly
                if abs(new_proficiency - current_proficiency) >= 0.05:
                    await self.update(memory_id, {"proficiency": new_proficiency})

    async def _build_skill_graph(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a skill graph from procedural memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            Skill graph dictionary
        """
        nodes = []
        edges = []
        
        # Add nodes for all tasks
        for memory in memories:
            task = memory.get("task", "")
            if task:
                nodes.append({
                    "id": memory.get("memory_id"),
                    "task": task,
                    "proficiency": memory.get("proficiency", 0.5),
                    "category": memory.get("category", "general")
                })
                
        # Add edges for prerequisite relationships
        for memory in memories:
            task = memory.get("task", "").lower()
            memory_id = memory.get("memory_id")
            prerequisites = memory.get("prerequisites", [])
            
            if task and memory_id and prerequisites:
                # Find memory IDs for prerequisites
                for prereq in prerequisites:
                    prereq_lower = prereq.lower()
                    for other_memory in memories:
                        other_task = other_memory.get("task", "").lower()
                        other_id = other_memory.get("memory_id")
                        
                        if other_task == prereq_lower and other_id:
                            edges.append({
                                "source": other_id,
                                "target": memory_id,
                                "type": "prerequisite"
                            })
                            
        # Add edges for related tasks
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                memory1 = memories[i]
                memory2 = memories[j]
                
                # Check if tasks are in the same category
                if memory1.get("category") == memory2.get("category"):
                    memory1_id = memory1.get("memory_id")
                    memory2_id = memory2.get("memory_id")
                    
                    if memory1_id and memory2_id:
                        edges.append({
                            "source": memory1_id,
                            "target": memory2_id,
                            "type": "related"
                        })
                        
        return {
            "nodes": nodes,
            "edges": edges
        }

    async def _calculate_proficiency(self, memory: Dict[str, Any]) -> float:
        """
        Calculate proficiency level for a procedural memory.

        Args:
            memory: Memory dictionary

        Returns:
            Proficiency level (0.0 to 1.0)
        """
        proficiency_level = 0.5  # Default proficiency
        
        # Check for explicit proficiency
        if "proficiency" in memory and isinstance(memory["proficiency"], (int, float)):
            return max(0.0, min(1.0, float(memory["proficiency"])))
            
        # Factor 1: Execution count
        execution_count = memory.get("execution_count", 0)
        execution_score = min(1.0, execution_count / 10)  # Normalize to 10 executions
        
        # Factor 2: Success rate
        success_rate = memory.get("success_rate", 0.0)
        
        # Factor 3: Complexity
        steps = memory.get("steps", [])
        complexity_score = 0.0
        
        if steps:
            # More complex procedures might be harder to master
            complexity = len(steps)
            complexity_score = max(0.0, 1.0 - (complexity / 20))  # Normalize to 20 steps
            
        # Factor 4: Last execution recency
        recency_score = 0.5  # Default recency
        last_execution = memory.get("last_execution", "")
        
        if last_execution:
            try:
                last_execution_datetime = datetime.datetime.fromisoformat(last_execution)
                now = datetime.datetime.now()
                days_ago = (now - last_execution_datetime).days
                
                # More recent executions might indicate higher proficiency
                recency_score = max(0.0, 1.0 - (days_ago / 30))  # Normalize to 30 days
            except (ValueError, TypeError):
                pass
                
        # Factor 5: Learning curve
        learning_curve = memory.get("learning_curve", "medium")
        learning_curve_score = 0.5  # Default learning curve
        
        if learning_curve == "easy":
            learning_curve_score = 0.7
        elif learning_curve == "medium":
            learning_curve_score = 0.5
        elif learning_curve == "hard":
            learning_curve_score = 0.3
            
        # Combine factors with weights
        proficiency_level = (
            execution_score * 0.3 +
            success_rate * 0.3 +
            complexity_score * 0.1 +
            recency_score * 0.2 +
            learning_curve_score * 0.1
        )
        
        return max(0.1, min(1.0, proficiency_level))

    async def _extract_tags(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract tags from a procedural memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of tags
        """
        tags = set()
        
        # Check for explicit tags
        if "tags" in memory and isinstance(memory["tags"], list):
            tags.update(memory["tags"])
            
        # Add task as tag
        task = memory.get("task", "")
        if task:
            tags.add(task.lower())
            
        # Add category as tag
        category = memory.get("category", "")
        if category:
            tags.add(category.lower())
            
        # Add context as tag
        context = memory.get("context", "")
        if context:
            tags.add(context.lower())
            
        # Extract tags from steps
        steps = memory.get("steps", [])
        if steps:
            # Extract key verbs from steps
            common_verbs = ["click", "open", "create", "save", "delete", "move", "copy", "paste", "select", "type"]
            for step in steps:
                for verb in common_verbs:
                    if verb in step.lower():
                        tags.add(verb)
                        break
                        
        return list(tags)

    async def _extract_prerequisites(self, memory: Dict[str, Any]) -> List[str]:
        """
        Extract prerequisites from a procedural memory.

        Args:
            memory: Memory dictionary

        Returns:
            List of prerequisites
        """
        prerequisites = set()
        
        # Check for explicit prerequisites
        if "prerequisites" in memory and isinstance(memory["prerequisites"], list):
            prerequisites.update(memory["prerequisites"])
            
        # Extract prerequisites from steps
        steps = memory.get("steps", [])
        if steps:
            # Look for phrases like "first X" or "before Y" or "requires Z"
            prerequisite_patterns = [
                "first ",
                "before ",
                "requires ",
                "need to ",
                "must have ",
                "prerequisite "
            ]
            
            for step in steps:
                for pattern in prerequisite_patterns:
                    if pattern in step.lower():
                        # Extract the word or phrase after the pattern
                        parts = step.lower().split(pattern)
                        if len(parts) > 1:
                            prereq = parts[1].split()[0].strip(",.;:!?")
                            if prereq:
                                prerequisites.add(prereq)
                                
        return list(prerequisites)