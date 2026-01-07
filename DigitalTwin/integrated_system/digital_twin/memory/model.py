"""
Memory model for the digital twin.

This module provides a more sophisticated memory model for the digital twin,
extending the basic memory system with advanced modeling capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
import numpy as np
from datetime import datetime, timedelta
import json
import os
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)

class MemoryModel:
    """Advanced memory model for the digital twin."""
    
    def __init__(self):
        """Initialize the memory model."""
        self.memory_categories = {
            'personal': [],    # Personal experiences and information
            'social': [],      # Social interactions and relationships
            'factual': [],     # Facts and knowledge
            'procedural': [],  # Skills and procedures
            'emotional': []    # Emotional experiences
        }
        
        self.memory_strength = {}  # Memory strength (0.0 to 1.0)
        self.memory_decay_rates = {}  # How quickly memories decay
        self.memory_last_recalled = {}  # When memories were last recalled
        self.memory_recall_count = {}  # How many times memories have been recalled
        
        self.memory_embeddings = {}  # Vector embeddings for memories
        self.memory_clusters = {}  # Clusters of related memories
        
        self.initialized = False
        self.model_path = "data/memory_model.json"
        
        # Memory decay parameters
        self.base_decay_rate = 0.01  # Base rate of memory decay per day
        self.min_strength = 0.1  # Minimum memory strength
        self.recall_boost = 0.2  # Strength boost when memory is recalled
        
        # Try to import vector embedding libraries
        self.embeddings_available = False
        try:
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            self.vectorizer = TfidfVectorizer(max_features=100)
            self.embeddings_available = True
            logger.info("Vector embeddings available for memory model")
        except ImportError:
            logger.warning("Vector embeddings not available for memory model")
    
    async def initialize(self):
        """Initialize the memory model."""
        logger.info("Initializing advanced memory model")
        
        # Try to load model from file
        if await self._load_model():
            logger.info("Loaded memory model from file")
        else:
            logger.info("Starting with empty memory model")
        
        self.initialized = True
        logger.info("Advanced memory model initialized")
    
    async def _load_model(self) -> bool:
        """
        Load model from file.
        
        Returns:
            True if model was loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'r') as f:
                    model_data = json.load(f)
                
                # Load memory categories
                if 'memory_categories' in model_data:
                    self.memory_categories = model_data['memory_categories']
                
                # Load memory strength
                if 'memory_strength' in model_data:
                    self.memory_strength = model_data['memory_strength']
                
                # Load memory decay rates
                if 'memory_decay_rates' in model_data:
                    self.memory_decay_rates = model_data['memory_decay_rates']
                
                # Load memory last recalled
                if 'memory_last_recalled' in model_data:
                    self.memory_last_recalled = model_data['memory_last_recalled']
                
                # Load memory recall count
                if 'memory_recall_count' in model_data:
                    self.memory_recall_count = model_data['memory_recall_count']
                
                # Load memory clusters
                if 'memory_clusters' in model_data:
                    self.memory_clusters = model_data['memory_clusters']
                
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error loading memory model: {str(e)}")
            return False
    
    async def _save_model(self):
        """Save model to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Create model data
            model_data = {
                'memory_categories': self.memory_categories,
                'memory_strength': self.memory_strength,
                'memory_decay_rates': self.memory_decay_rates,
                'memory_last_recalled': self.memory_last_recalled,
                'memory_recall_count': self.memory_recall_count,
                'memory_clusters': self.memory_clusters,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to file
            with open(self.model_path, 'w') as f:
                json.dump(model_data, f, indent=2)
            
            logger.info("Saved memory model to file")
            return True
        except Exception as e:
            logger.error(f"Error saving memory model: {str(e)}")
            return False
    
    async def register_memory(self, memory_id: str, content: Any, 
                             categories: List[str] = None, 
                             initial_strength: float = 0.5) -> Dict[str, Any]:
        """
        Register a memory with the model.
        
        Args:
            memory_id: Memory ID
            content: Memory content
            categories: List of categories (personal, social, factual, procedural, emotional)
            initial_strength: Initial memory strength (0.0 to 1.0)
            
        Returns:
            Dictionary of registration results
        """
        logger.info(f"Registering memory {memory_id} with model")
        
        if not self.initialized:
            await self.initialize()
        
        # Validate categories
        if not categories:
            categories = ['personal']  # Default category
        
        valid_categories = [cat for cat in categories if cat in self.memory_categories]
        if not valid_categories:
            valid_categories = ['personal']  # Default if no valid categories
        
        # Add memory to categories
        for category in valid_categories:
            if memory_id not in self.memory_categories[category]:
                self.memory_categories[category].append(memory_id)
        
        # Set memory strength
        self.memory_strength[memory_id] = initial_strength
        
        # Set decay rate based on categories
        decay_rate = self.base_decay_rate
        if 'emotional' in valid_categories:
            decay_rate *= 0.8  # Emotional memories decay slower
        if 'procedural' in valid_categories:
            decay_rate *= 0.7  # Procedural memories decay slower
        if 'factual' in valid_categories:
            decay_rate *= 0.9  # Factual memories decay at moderate rate
        
        self.memory_decay_rates[memory_id] = decay_rate
        
        # Set last recalled to now
        self.memory_last_recalled[memory_id] = datetime.now().isoformat()
        
        # Initialize recall count
        self.memory_recall_count[memory_id] = 1
        
        # Create embedding if available
        if self.embeddings_available:
            await self._create_embedding(memory_id, content)
        
        # Save model
        await self._save_model()
        
        return {
            'memory_id': memory_id,
            'categories': valid_categories,
            'strength': initial_strength,
            'decay_rate': decay_rate
        }
    
    async def recall_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Recall a memory, updating its strength and last recalled time.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Dictionary of recall results
        """
        logger.info(f"Recalling memory {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if memory_id not in self.memory_strength:
            return {'error': f"Memory {memory_id} not found in model"}
        
        # Update last recalled time
        self.memory_last_recalled[memory_id] = datetime.now().isoformat()
        
        # Increment recall count
        if memory_id in self.memory_recall_count:
            self.memory_recall_count[memory_id] += 1
        else:
            self.memory_recall_count[memory_id] = 1
        
        # Boost memory strength
        current_strength = self.memory_strength[memory_id]
        new_strength = min(1.0, current_strength + self.recall_boost * (1 - current_strength))
        self.memory_strength[memory_id] = new_strength
        
        # Save model
        await self._save_model()
        
        return {
            'memory_id': memory_id,
            'previous_strength': current_strength,
            'new_strength': new_strength,
            'recall_count': self.memory_recall_count[memory_id]
        }
    
    async def update_memory_decay(self):
        """Update memory strength based on decay rates."""
        logger.info("Updating memory decay")
        
        if not self.initialized:
            await self.initialize()
        
        now = datetime.now()
        updated_count = 0
        
        for memory_id, strength in list(self.memory_strength.items()):
            if memory_id in self.memory_last_recalled:
                # Calculate days since last recall
                last_recalled = datetime.fromisoformat(self.memory_last_recalled[memory_id])
                days_since_recall = (now - last_recalled).days
                
                if days_since_recall > 0:
                    # Get decay rate
                    decay_rate = self.memory_decay_rates.get(memory_id, self.base_decay_rate)
                    
                    # Calculate decay
                    decay = decay_rate * days_since_recall
                    
                    # Apply decay
                    new_strength = max(self.min_strength, strength - decay)
                    self.memory_strength[memory_id] = new_strength
                    updated_count += 1
        
        # Save model
        if updated_count > 0:
            await self._save_model()
        
        logger.info(f"Updated decay for {updated_count} memories")
    
    async def find_similar_memories(self, memory_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Find memories similar to the given memory.
        
        Args:
            memory_id: Memory ID
            limit: Maximum number of results
            
        Returns:
            List of tuples (memory_id, similarity_score)
        """
        logger.info(f"Finding memories similar to {memory_id}")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.embeddings_available:
            logger.warning("Vector embeddings not available for similarity search")
            return []
        
        if memory_id not in self.memory_embeddings:
            logger.warning(f"No embedding found for memory {memory_id}")
            return []
        
        # Get embedding for target memory
        target_embedding = self.memory_embeddings[memory_id]
        
        # Calculate similarity with all other memories
        similarities = []
        for other_id, embedding in self.memory_embeddings.items():
            if other_id != memory_id:
                similarity = self._calculate_similarity(target_embedding, embedding)
                similarities.append((other_id, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results
        return similarities[:limit]
    
    async def _create_embedding(self, memory_id: str, content: Any):
        """
        Create vector embedding for a memory.
        
        Args:
            memory_id: Memory ID
            content: Memory content
        """
        if not self.embeddings_available:
            return
        
        try:
            # Convert content to string
            if isinstance(content, dict):
                content_str = json.dumps(content)
            else:
                content_str = str(content)
            
            # Create embedding
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            # Fit vectorizer if not already fit
            if not hasattr(self.vectorizer, 'vocabulary_'):
                self.vectorizer.fit([content_str])
            
            # Transform content to vector
            vector = self.vectorizer.transform([content_str]).toarray()[0]
            
            # Store embedding
            self.memory_embeddings[memory_id] = vector.tolist()
            
        except Exception as e:
            logger.error(f"Error creating memory embedding: {str(e)}")
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(vec1, vec2)[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    async def cluster_memories(self):
        """Cluster memories based on similarity."""
        logger.info("Clustering memories")
        
        if not self.initialized:
            await self.initialize()
        
        if not self.embeddings_available:
            logger.warning("Vector embeddings not available for clustering")
            return
        
        try:
            from sklearn.cluster import DBSCAN
            import numpy as np
            
            # Need at least 2 memories for clustering
            if len(self.memory_embeddings) < 2:
                logger.info("Not enough memories for clustering")
                return
            
            # Extract memory IDs and embeddings
            memory_ids = list(self.memory_embeddings.keys())
            embeddings = np.array([self.memory_embeddings[mid] for mid in memory_ids])
            
            # Perform clustering
            clustering = DBSCAN(eps=0.3, min_samples=2).fit(embeddings)
            
            # Extract clusters
            labels = clustering.labels_
            
            # Group memories by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(labels):
                if label >= 0:  # Ignore noise points (label = -1)
                    clusters[int(label)].append(memory_ids[i])
            
            # Store clusters
            self.memory_clusters = {f"cluster_{i}": members for i, members in clusters.items()}
            
            # Save model
            await self._save_model()
            
            logger.info(f"Created {len(clusters)} memory clusters")
            
        except Exception as e:
            logger.error(f"Error clustering memories: {str(e)}")
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory model.
        
        Returns:
            Dictionary of memory statistics
        """
        logger.info("Getting memory model statistics")
        
        if not self.initialized:
            await self.initialize()
        
        # Count memories by category
        category_counts = {category: len(memories) for category, memories in self.memory_categories.items()}
        
        # Calculate average memory strength
        avg_strength = 0.0
        if self.memory_strength:
            avg_strength = sum(self.memory_strength.values()) / len(self.memory_strength)
        
        # Calculate average recall count
        avg_recall_count = 0.0
        if self.memory_recall_count:
            avg_recall_count = sum(self.memory_recall_count.values()) / len(self.memory_recall_count)
        
        # Count memories by strength range
        strength_ranges = {
            'very_weak': 0,   # 0.0-0.2
            'weak': 0,        # 0.2-0.4
            'moderate': 0,    # 0.4-0.6
            'strong': 0,      # 0.6-0.8
            'very_strong': 0  # 0.8-1.0
        }
        
        for strength in self.memory_strength.values():
            if strength < 0.2:
                strength_ranges['very_weak'] += 1
            elif strength < 0.4:
                strength_ranges['weak'] += 1
            elif strength < 0.6:
                strength_ranges['moderate'] += 1
            elif strength < 0.8:
                strength_ranges['strong'] += 1
            else:
                strength_ranges['very_strong'] += 1
        
        # Count clusters
        cluster_count = len(self.memory_clusters)
        
        # Calculate average cluster size
        avg_cluster_size = 0.0
        if self.memory_clusters:
            avg_cluster_size = sum(len(members) for members in self.memory_clusters.values()) / len(self.memory_clusters)
        
        return {
            'total_memories': len(self.memory_strength),
            'category_counts': category_counts,
            'avg_strength': avg_strength,
            'avg_recall_count': avg_recall_count,
            'strength_distribution': strength_ranges,
            'cluster_count': cluster_count,
            'avg_cluster_size': avg_cluster_size
        }