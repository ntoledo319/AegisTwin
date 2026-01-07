"""
Enhanced Memory System for the Digital Twin.

This module extends the core MemorySystem with SpiderMind Omega adapters
for more sophisticated memory management and analysis.
"""

import logging
import uuid
import datetime
from typing import Dict, Any, List, Optional

from .system import MemorySystem
from ..adapters.temporal_analysis import TemporalAnalysisEngine
from ..adapters.enhanced_temporal_analysis import EnhancedTemporalAnalysisEngine
from ..adapters.void_analyzer import VoidAnalyzerAdapter
from ..adapters.predictive_engine import EnhancedPredictiveEngineAdapter

logger = logging.getLogger(__name__)


class EnhancedMemorySystem(MemorySystem):
    """
    Enhanced system for managing digital twin memories with SpiderMind Omega adapters.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced memory system.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        
        # Initialize SpiderMind Omega adapters
        self.temporal_analysis_engine = TemporalAnalysisEngine(config)
        self.enhanced_temporal_analysis_engine = EnhancedTemporalAnalysisEngine(config)
        self.void_analyzer_adapter = VoidAnalyzerAdapter(config)
        self.predictive_engine_adapter = EnhancedPredictiveEngineAdapter(config)
        
        logger.info("Enhanced Memory System initialized with SpiderMind Omega adapters")

    async def store_memory(self, user_id: str, memory_type: str, content: Dict[str, Any]) -> str:
        """
        Store a memory with enhanced processing.

        Args:
            user_id: User ID
            memory_type: Type of memory (episodic, semantic, procedural)
            content: Memory content

        Returns:
            Memory ID
        """
        # Store memory using parent class method
        memory_id = await super().store_memory(user_id, memory_type, content)
        
        # Perform temporal analysis on the new memory
        if memory_type == "episodic":
            # Get recent memories for context
            recent_memories = await self.retrieve_memory(
                user_id, 
                {"memory_type": "episodic"}, 
                limit=10
            )
            
            # Convert memories to temporal data format
            temporal_data = self._convert_memories_to_temporal_data(recent_memories)
            
            # Perform temporal analysis
            temporal_analysis = await self.enhanced_temporal_analysis_engine.analyze_temporal_patterns(temporal_data)
            
            # Store analysis results as metadata on the memory
            await self.update_memory(memory_id, {"temporal_analysis": temporal_analysis})
        
        return memory_id

    async def retrieve_memory_with_context(self, user_id: str, query: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve memories with enhanced contextual information.

        Args:
            user_id: User ID
            query: Query dictionary
            limit: Maximum number of memories to retrieve

        Returns:
            Dictionary containing memories and contextual information
        """
        # Retrieve memories using parent class method
        memories = await self.retrieve_memory(user_id, query, limit)
        
        # Add contextual information
        result = {
            "memories": memories,
            "context": {}
        }
        
        if memories:
            # Perform temporal analysis
            temporal_data = self._convert_memories_to_temporal_data(memories)
            temporal_analysis = await self.enhanced_temporal_analysis_engine.analyze_temporal_patterns(temporal_data)
            result["context"]["temporal_analysis"] = temporal_analysis
            
            # Detect memory gaps
            memory_data = self._convert_memories_to_memory_data(memories)
            void_analysis = await self.void_analyzer_adapter.analyze_understanding_gaps(memory_data)
            result["context"]["memory_gaps"] = void_analysis
        
        return result

    async def predict_memory_recall(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Predict which memories are likely to be recalled in a given context.

        Args:
            user_id: User ID
            context: Context dictionary

        Returns:
            List of predicted memories to recall
        """
        # Retrieve recent memories
        recent_memories = await self.retrieve_memory(
            user_id, 
            {"memory_type": "episodic"}, 
            limit=20
        )
        
        if not recent_memories:
            return []
        
        # Convert memories to training data format
        training_data = []
        for memory in recent_memories:
            training_data.append({
                "timestamp": memory.get("created_at", ""),
                "content": memory.get("content", {}),
                "context": memory.get("context", {}),
                "recall_probability": memory.get("recall_count", 0) / 10.0  # Normalize
            })
        
        # Train prediction models
        await self.predictive_engine_adapter.train_prediction_models(training_data)
        
        # Predict recall probabilities
        predictions = await self.predictive_engine_adapter.predict_future_states(context)
        
        # Sort memories by predicted recall probability
        predicted_memories = []
        for memory in recent_memories:
            # Calculate recall probability based on predictions
            recall_probability = self._calculate_recall_probability(memory, predictions)
            
            predicted_memories.append({
                "memory_id": memory.get("memory_id", ""),
                "content": memory.get("content", {}),
                "recall_probability": recall_probability
            })
        
        # Sort by recall probability (highest first)
        predicted_memories.sort(key=lambda x: x["recall_probability"], reverse=True)
        
        return predicted_memories

    async def analyze_memory_trajectory(self, user_id: str, memory_type: str = "episodic") -> Dict[str, Any]:
        """
        Analyze the trajectory of memories over time.

        Args:
            user_id: User ID
            memory_type: Type of memory to analyze

        Returns:
            Trajectory analysis results
        """
        # Retrieve memories
        memories = await self.retrieve_memory(
            user_id, 
            {"memory_type": memory_type}, 
            limit=50
        )
        
        if not memories:
            return {"error": "No memories found"}
        
        # Convert memories to temporal data format
        temporal_data = self._convert_memories_to_temporal_data(memories)
        
        # Sort by timestamp
        history = sorted(temporal_data, key=lambda x: x.get("timestamp", ""))
        
        # Predict trajectory
        trajectory = await self.enhanced_temporal_analysis_engine.predict_memory_trajectory(history)
        
        return trajectory

    async def detect_memory_gaps(self, user_id: str) -> Dict[str, Any]:
        """
        Detect gaps in the user's memory.

        Args:
            user_id: User ID

        Returns:
            Memory gap analysis results
        """
        # Retrieve memories for different types
        episodic_memories = await self.retrieve_memory(
            user_id, 
            {"memory_type": "episodic"}, 
            limit=50
        )
        
        semantic_memories = await self.retrieve_memory(
            user_id, 
            {"memory_type": "semantic"}, 
            limit=50
        )
        
        procedural_memories = await self.retrieve_memory(
            user_id, 
            {"memory_type": "procedural"}, 
            limit=50
        )
        
        # Convert memories to memory data format
        memory_data = {
            "episodic": self._convert_memories_to_memory_data_list(episodic_memories),
            "semantic": self._convert_memories_to_memory_data_list(semantic_memories),
            "procedural": self._convert_memories_to_memory_data_list(procedural_memories)
        }
        
        # Analyze understanding gaps
        void_analysis = await self.void_analyzer_adapter.analyze_understanding_gaps(memory_data)
        
        # Generate recovery recommendations
        recovery_recommendations = await self.void_analyzer_adapter.generate_void_recovery_recommendations(
            void_analysis.get("detected_voids", [])
        )
        
        # Combine results
        result = {
            "void_analysis": void_analysis,
            "recovery_recommendations": recovery_recommendations
        }
        
        return result

    def _convert_memories_to_temporal_data(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert memories to temporal data format for temporal analysis.

        Args:
            memories: List of memories

        Returns:
            List of temporal data points
        """
        temporal_data = []
        
        for memory in memories:
            # Extract timestamp
            timestamp = memory.get("created_at", datetime.datetime.now().isoformat())
            
            # Extract content
            content = memory.get("content", {})
            
            # Create temporal data point
            data_point = {
                "timestamp": timestamp,
                "memory_id": memory.get("memory_id", ""),
                "memory_type": memory.get("memory_type", ""),
                "content": content,
                "importance": memory.get("importance", 0.5),
                "emotional_valence": content.get("emotional_valence", 0.0),
                "emotional_arousal": content.get("emotional_arousal", 0.0)
            }
            
            temporal_data.append(data_point)
        
        return temporal_data

    def _convert_memories_to_memory_data(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert memories to memory data format for void analysis.

        Args:
            memories: List of memories

        Returns:
            Dictionary of memory data categorized by memory type
        """
        memory_data = {}
        
        # Group memories by type
        for memory in memories:
            memory_type = memory.get("memory_type", "unknown")
            
            if memory_type not in memory_data:
                memory_data[memory_type] = []
            
            # Extract relevant data
            data_point = {
                "timestamp": memory.get("created_at", datetime.datetime.now().isoformat()),
                "memory_id": memory.get("memory_id", ""),
                "content": memory.get("content", {})
            }
            
            memory_data[memory_type].append(data_point)
        
        return memory_data

    def _convert_memories_to_memory_data_list(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert memories to a list of memory data points.

        Args:
            memories: List of memories

        Returns:
            List of memory data points
        """
        memory_data = []
        
        for memory in memories:
            # Extract relevant data
            data_point = {
                "timestamp": memory.get("created_at", datetime.datetime.now().isoformat()),
                "memory_id": memory.get("memory_id", ""),
                "content": memory.get("content", {})
            }
            
            memory_data.append(data_point)
        
        return memory_data

    def _calculate_recall_probability(self, memory: Dict[str, Any], predictions: Dict[str, Any]) -> float:
        """
        Calculate recall probability for a memory based on predictions.

        Args:
            memory: Memory dictionary
            predictions: Prediction results

        Returns:
            Recall probability (0.0 to 1.0)
        """
        # Base probability based on recency
        created_at = memory.get("created_at", "")
        if not created_at:
            return 0.5
        
        try:
            memory_time = datetime.datetime.fromisoformat(created_at)
            now = datetime.datetime.now()
            days_old = (now - memory_time).days
            
            # Recency factor (more recent = higher probability)
            recency_factor = max(0.1, min(1.0, 1.0 - (days_old / 30.0)))
        except:
            recency_factor = 0.5
        
        # Importance factor
        importance_factor = memory.get("importance", 0.5)
        
        # Emotional factor
        content = memory.get("content", {})
        emotional_valence = abs(content.get("emotional_valence", 0.0))
        emotional_arousal = content.get("emotional_arousal", 0.0)
        emotional_factor = (emotional_valence + emotional_arousal) / 2.0
        
        # Recall count factor
        recall_count = memory.get("recall_count", 0)
        recall_factor = min(1.0, recall_count / 10.0)
        
        # Combine factors
        probability = (recency_factor * 0.3 + 
                      importance_factor * 0.2 + 
                      emotional_factor * 0.3 + 
                      recall_factor * 0.2)
        
        return probability