"""
Vector store for the integrated system.
"""

import os
import logging
import json
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime

from core.config import config
from core.db import db_manager

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for storing and retrieving vector embeddings."""
    
    def __init__(self):
        """Initialize the vector store."""
        self.redis_client = None
        self.storage_dir = config.get("storage.data_dir", "data")
        
    async def initialize(self):
        """Initialize the vector store."""
        logger.info("Initializing vector store...")
        
        # Create storage directory if it doesn't exist
        vector_dir = os.path.join(self.storage_dir, "vectors")
        os.makedirs(vector_dir, exist_ok=True)
        
        # Get Redis client
        self.redis_client = await db_manager.get_redis_client()
        
        logger.info("Vector store initialization complete")
        
    async def store_vector(self, 
                          collection: str, 
                          vector_id: str,
                          vector: List[float],
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a vector.
        
        Args:
            collection: Collection name
            vector_id: Vector ID
            vector: Vector embedding
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add metadata
            metadata = metadata or {}
            metadata["created_at"] = datetime.now().isoformat()
            
            # Store in Redis
            if self.redis_client:
                # Convert vector to string
                vector_str = ",".join([str(x) for x in vector])
                
                # Store vector
                key = f"vector:{collection}:{vector_id}"
                await self.redis_client.hset(key, "vector", vector_str)
                
                # Store metadata
                for k, v in metadata.items():
                    await self.redis_client.hset(key, k, json.dumps(v))
                    
                # Add to collection index
                await self.redis_client.sadd(f"collection:{collection}", vector_id)
                
            # Store in file system
            vector_data = {
                "id": vector_id,
                "collection": collection,
                "vector": vector,
                "metadata": metadata
            }
            
            collection_dir = os.path.join(self.storage_dir, "vectors", collection)
            os.makedirs(collection_dir, exist_ok=True)
            
            vector_path = os.path.join(collection_dir, f"{vector_id}.json")
            
            with open(vector_path, 'w', encoding='utf-8') as f:
                json.dump(vector_data, f, default=self._json_serializer)
                
            logger.info(f"Stored vector: {collection}/{vector_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector: {str(e)}")
            return False
            
    async def get_vector(self, 
                        collection: str, 
                        vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a vector by ID.
        
        Args:
            collection: Collection name
            vector_id: Vector ID
            
        Returns:
            Vector data or None if not found
        """
        try:
            # Try to get from Redis
            if self.redis_client:
                key = f"vector:{collection}:{vector_id}"
                
                # Check if key exists
                exists = await self.redis_client.exists(key)
                
                if exists:
                    # Get vector
                    vector_str = await self.redis_client.hget(key, "vector")
                    vector = [float(x) for x in vector_str.split(",")]
                    
                    # Get metadata
                    metadata = {}
                    all_fields = await self.redis_client.hgetall(key)
                    
                    for k, v in all_fields.items():
                        if k != "vector":
                            metadata[k] = json.loads(v)
                            
                    return {
                        "id": vector_id,
                        "collection": collection,
                        "vector": vector,
                        "metadata": metadata
                    }
                    
            # Try to get from file system
            vector_path = os.path.join(self.storage_dir, "vectors", collection, f"{vector_id}.json")
            
            if os.path.exists(vector_path):
                with open(vector_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            logger.warning(f"Vector not found: {collection}/{vector_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting vector: {str(e)}")
            return None
            
    async def search_vectors(self, 
                            collection: str,
                            query_vector: List[float],
                            limit: int = 10,
                            metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            collection: Collection name
            query_vector: Query vector
            limit: Maximum number of results
            metadata_filter: Optional metadata filter
            
        Returns:
            List of similar vectors with similarity scores
        """
        try:
            # Convert query vector to numpy array
            query_np = np.array(query_vector)
            
            # Get all vectors in collection
            vectors = []
            
            # Try to get from Redis
            if self.redis_client:
                # Get all vector IDs in collection
                vector_ids = await self.redis_client.smembers(f"collection:{collection}")
                
                for vector_id in vector_ids:
                    # Get vector
                    vector_data = await self.get_vector(collection, vector_id)
                    
                    if vector_data:
                        # Apply metadata filter
                        if metadata_filter:
                            match = True
                            for k, v in metadata_filter.items():
                                if k not in vector_data["metadata"] or vector_data["metadata"][k] != v:
                                    match = False
                                    break
                                    
                            if not match:
                                continue
                                
                        vectors.append(vector_data)
            else:
                # Get from file system
                collection_dir = os.path.join(self.storage_dir, "vectors", collection)
                
                if os.path.exists(collection_dir):
                    for filename in os.listdir(collection_dir):
                        if filename.endswith(".json"):
                            vector_path = os.path.join(collection_dir, filename)
                            
                            with open(vector_path, 'r', encoding='utf-8') as f:
                                vector_data = json.load(f)
                                
                                # Apply metadata filter
                                if metadata_filter:
                                    match = True
                                    for k, v in metadata_filter.items():
                                        if k not in vector_data["metadata"] or vector_data["metadata"][k] != v:
                                            match = False
                                            break
                                            
                                    if not match:
                                        continue
                                        
                                vectors.append(vector_data)
                                
            # Calculate similarity scores
            results = []
            
            for vector_data in vectors:
                # Convert vector to numpy array
                vector_np = np.array(vector_data["vector"])
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_np, vector_np)
                
                results.append({
                    "id": vector_data["id"],
                    "collection": collection,
                    "vector": vector_data["vector"],
                    "metadata": vector_data["metadata"],
                    "similarity": similarity
                })
                
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Apply limit
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
            
    async def update_vector_metadata(self, 
                                    collection: str, 
                                    vector_id: str,
                                    metadata: Dict[str, Any]) -> bool:
        """
        Update vector metadata.
        
        Args:
            collection: Collection name
            vector_id: Vector ID
            metadata: Metadata to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get vector
            vector_data = await self.get_vector(collection, vector_id)
            
            if not vector_data:
                logger.warning(f"Vector not found for update: {collection}/{vector_id}")
                return False
                
            # Update metadata
            vector_data["metadata"].update(metadata)
            
            # Update in Redis
            if self.redis_client:
                key = f"vector:{collection}:{vector_id}"
                
                # Update metadata
                for k, v in metadata.items():
                    await self.redis_client.hset(key, k, json.dumps(v))
                    
            # Update in file system
            vector_path = os.path.join(self.storage_dir, "vectors", collection, f"{vector_id}.json")
            
            with open(vector_path, 'w', encoding='utf-8') as f:
                json.dump(vector_data, f, default=self._json_serializer)
                
            logger.info(f"Updated vector metadata: {collection}/{vector_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating vector metadata: {str(e)}")
            return False
            
    async def delete_vector(self, 
                           collection: str, 
                           vector_id: str) -> bool:
        """
        Delete a vector.
        
        Args:
            collection: Collection name
            vector_id: Vector ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from Redis
            if self.redis_client:
                key = f"vector:{collection}:{vector_id}"
                
                # Delete vector
                await self.redis_client.delete(key)
                
                # Remove from collection index
                await self.redis_client.srem(f"collection:{collection}", vector_id)
                
            # Delete from file system
            vector_path = os.path.join(self.storage_dir, "vectors", collection, f"{vector_id}.json")
            
            if os.path.exists(vector_path):
                os.remove(vector_path)
                
            logger.info(f"Deleted vector: {collection}/{vector_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector: {str(e)}")
            return False
            
    async def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = set()
            
            # Get from Redis
            if self.redis_client:
                keys = await self.redis_client.keys("collection:*")
                
                for key in keys:
                    collection = key.split(":")[-1]
                    collections.add(collection)
                    
            # Get from file system
            vectors_dir = os.path.join(self.storage_dir, "vectors")
            
            if os.path.exists(vectors_dir):
                for dirname in os.listdir(vectors_dir):
                    dir_path = os.path.join(vectors_dir, dirname)
                    if os.path.isdir(dir_path):
                        collections.add(dirname)
                        
            return list(collections)
            
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
            
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Collection statistics
        """
        try:
            # Count vectors
            count = 0
            
            # Get from Redis
            if self.redis_client:
                count = await self.redis_client.scard(f"collection:{collection}")
            else:
                # Get from file system
                collection_dir = os.path.join(self.storage_dir, "vectors", collection)
                
                if os.path.exists(collection_dir):
                    count = len([f for f in os.listdir(collection_dir) if f.endswith(".json")])
                    
            return {
                "collection": collection,
                "vector_count": count
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "collection": collection,
                "vector_count": 0,
                "error": str(e)
            }
            
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def _json_serializer(self, obj):
        """
        JSON serializer for objects not serializable by default json code.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")