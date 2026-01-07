"""
Vector Memory System using ChromaDB

Provides vector-based storage and retrieval for conversation history,
personality data, and contextual information with semantic search capabilities.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import logging
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

from ..ai.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

class VectorMemory:
    """
    Vector-based memory system using ChromaDB for semantic storage and retrieval.
    
    Provides persistent storage for conversations, personality data, and contextual
    information with semantic search capabilities.
    """
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 api_key: Optional[str] = None,
                 collection_name: str = "cognitive_twin_memory"):
        """
        Initialize vector memory system.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            api_key: OpenRouter API key for embeddings
            collection_name: Name of the ChromaDB collection
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.api_key = api_key
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize OpenRouter client for embeddings
        self.embedding_client = OpenRouterClient(api_key) if api_key else None
        
        # Get or create collection
        self.collection = None
        self._initialize_collection()
        
        # Memory categories
        self.categories = {
            "conversation": "conversation_memory",
            "personality": "personality_memory", 
            "context": "context_memory",
            "insights": "insights_memory",
            "preferences": "preferences_memory"
        }
        
        # Initialize category collections
        self._initialize_category_collections()
    
    def _initialize_collection(self):
        """Initialize the main collection"""
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function()
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function(),
                metadata={"description": "Cognitive-Twin vector memory"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def _initialize_category_collections(self):
        """Initialize category-specific collections"""
        self.category_collections = {}
        
        for category, collection_name in self.categories.items():
            try:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self._get_embedding_function()
                )
                self.category_collections[category] = collection
                logger.info(f"Loaded category collection: {collection_name}")
            except Exception:
                # Create new category collection
                collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self._get_embedding_function(),
                    metadata={"category": category, "description": f"Cognitive-Twin {category} memory"}
                )
                self.category_collections[category] = collection
                logger.info(f"Created category collection: {collection_name}")
    
    def _get_embedding_function(self):
        """Get embedding function for ChromaDB"""
        if self.embedding_client:
            # Use OpenRouter embeddings
            return self._openrouter_embedding_function()
        else:
            # Use default ChromaDB embeddings
            return None
    
    def _openrouter_embedding_function(self):
        """Create embedding function using OpenRouter"""
        class OpenRouterEmbeddingFunction:
            def __init__(self, client):
                self.client = client
            
            def __call__(self, input_texts):
                # This is a synchronous wrapper for async embedding generation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._generate_embeddings(input_texts))
                finally:
                    loop.close()
            
            async def _generate_embeddings(self, texts):
                try:
                    async with self.client as client:
                        response = await client.embeddings(texts)
                        return response["data"]
                except Exception as e:
                    logger.error(f"Error generating embeddings: {e}")
                    # Fallback to zero embeddings
                    return [[0.0] * 1536 for _ in texts]
        
        return OpenRouterEmbeddingFunction(self.embedding_client)
    
    async def store_memory(
        self,
        content: str,
        category: str = "conversation",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """
        Store a memory in vector database.
        
        Args:
            content: Content to store
            category: Memory category (conversation, personality, context, etc.)
            user_id: User identifier
            metadata: Additional metadata
            memory_id: Custom memory ID (auto-generated if None)
            
        Returns:
            Memory ID
        """
        if not memory_id:
            memory_id = str(uuid.uuid4())
        
        # Prepare metadata
        store_metadata = {
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id or "anonymous"
        }
        
        if metadata:
            store_metadata.update(metadata)
        
        # Get appropriate collection
        collection = self.category_collections.get(category, self.collection)
        
        try:
            # Store in ChromaDB
            collection.add(
                documents=[content],
                metadatas=[store_metadata],
                ids=[memory_id]
            )
            
            logger.info(f"Stored memory {memory_id} in category {category}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories using semantic search.
        
        Args:
            query: Search query
            category: Memory category to search (None for all)
            user_id: User identifier to filter by
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of matching memories with metadata
        """
        try:
            # Determine which collections to search
            if category and category in self.category_collections:
                collections_to_search = [self.category_collections[category]]
            else:
                collections_to_search = list(self.category_collections.values()) + [self.collection]
            
            all_results = []
            
            # Search each collection
            for collection in collections_to_search:
                try:
                    # Build where clause for filtering
                    where_clause = {}
                    if user_id:
                        where_clause["user_id"] = user_id
                    
                    # Perform semantic search
                    results = collection.query(
                        query_texts=[query],
                        n_results=limit,
                        where=where_clause if where_clause else None
                    )
                    
                    # Process results
                    if results["documents"] and results["documents"][0]:
                        for i, doc in enumerate(results["documents"][0]):
                            similarity = 1.0 - results["distances"][0][i]  # Convert distance to similarity
                            
                            if similarity >= similarity_threshold:
                                memory = {
                                    "id": results["ids"][0][i],
                                    "content": doc,
                                    "metadata": results["metadatas"][0][i],
                                    "similarity": similarity,
                                    "category": results["metadatas"][0][i].get("category", "unknown")
                                }
                                all_results.append(memory)
                
                except Exception as e:
                    logger.warning(f"Error searching collection {collection.name}: {e}")
                    continue
            
            # Sort by similarity and limit results
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def get_user_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific user.
        
        Args:
            user_id: User identifier
            category: Memory category (None for all)
            limit: Maximum number of results
            
        Returns:
            List of user memories
        """
        try:
            # Determine which collections to search
            if category and category in self.category_collections:
                collections_to_search = [self.category_collections[category]]
            else:
                collections_to_search = list(self.category_collections.values()) + [self.collection]
            
            all_memories = []
            
            for collection in collections_to_search:
                try:
                    # Get all memories for user
                    results = collection.get(
                        where={"user_id": user_id},
                        limit=limit
                    )
                    
                    if results["documents"]:
                        for i, doc in enumerate(results["documents"]):
                            memory = {
                                "id": results["ids"][i],
                                "content": doc,
                                "metadata": results["metadatas"][i],
                                "category": results["metadatas"][i].get("category", "unknown")
                            }
                            all_memories.append(memory)
                
                except Exception as e:
                    logger.warning(f"Error getting memories from {collection.name}: {e}")
                    continue
            
            # Sort by timestamp
            all_memories.sort(
                key=lambda x: x["metadata"].get("timestamp", ""), 
                reverse=True
            )
            
            return all_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            return []
    
    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory ID to update
            content: New content (None to keep existing)
            metadata: New metadata (None to keep existing)
            category: Memory category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the memory first
            memory = await self.get_memory_by_id(memory_id)
            if not memory:
                return False
            
            # Determine which collection to update
            memory_category = category or memory["category"]
            collection = self.category_collections.get(memory_category, self.collection)
            
            # Prepare update data
            update_content = content if content is not None else memory["content"]
            update_metadata = memory["metadata"].copy()
            
            if metadata:
                update_metadata.update(metadata)
            
            # Update timestamp
            update_metadata["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in ChromaDB
            collection.update(
                ids=[memory_id],
                documents=[update_content] if content is not None else None,
                metadatas=[update_metadata]
            )
            
            logger.info(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False
    
    async def delete_memory(self, memory_id: str, category: Optional[str] = None) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID to delete
            category: Memory category (optional, will search if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if category and category in self.category_collections:
                # Delete from specific category
                collection = self.category_collections[category]
                collection.delete(ids=[memory_id])
            else:
                # Search and delete from all collections
                for collection in list(self.category_collections.values()) + [self.collection]:
                    try:
                        collection.delete(ids=[memory_id])
                        break
                    except Exception:
                        continue
            
            logger.info(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory data or None if not found
        """
        try:
            # Search all collections
            for collection in list(self.category_collections.values()) + [self.collection]:
                try:
                    results = collection.get(ids=[memory_id])
                    if results["documents"]:
                        return {
                            "id": results["ids"][0],
                            "content": results["documents"][0],
                            "metadata": results["metadatas"][0],
                            "category": results["metadatas"][0].get("category", "unknown")
                        }
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            return None
    
    async def get_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Args:
            user_id: User identifier (None for all users)
            
        Returns:
            Memory statistics
        """
        try:
            stats = {
                "total_memories": 0,
                "memories_by_category": {},
                "recent_memories": 0,
                "oldest_memory": None,
                "newest_memory": None
            }
            
            # Count memories in each collection
            for category, collection in self.category_collections.items():
                try:
                    where_clause = {"user_id": user_id} if user_id else None
                    results = collection.get(where=where_clause)
                    
                    count = len(results["documents"]) if results["documents"] else 0
                    stats["memories_by_category"][category] = count
                    stats["total_memories"] += count
                    
                    # Find oldest and newest memories
                    if results["metadatas"]:
                        timestamps = [
                            meta.get("timestamp", "") 
                            for meta in results["metadatas"] 
                            if meta.get("timestamp")
                        ]
                        
                        if timestamps:
                            if not stats["oldest_memory"] or min(timestamps) < stats["oldest_memory"]:
                                stats["oldest_memory"] = min(timestamps)
                            if not stats["newest_memory"] or max(timestamps) > stats["newest_memory"]:
                                stats["newest_memory"] = max(timestamps)
                
                except Exception as e:
                    logger.warning(f"Error getting stats for {category}: {e}")
                    continue
            
            # Count recent memories (last 24 hours)
            if user_id:
                recent_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
                recent_memories = await self.retrieve_memories(
                    query="recent",
                    user_id=user_id,
                    limit=1000
                )
                stats["recent_memories"] = len([
                    m for m in recent_memories 
                    if m["metadata"].get("timestamp", "") > recent_cutoff
                ])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}
    
    async def clear_user_memories(self, user_id: str, category: Optional[str] = None) -> int:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier
            category: Memory category (None for all)
            
        Returns:
            Number of memories deleted
        """
        try:
            deleted_count = 0
            
            # Determine which collections to clear
            if category and category in self.category_collections:
                collections_to_clear = [self.category_collections[category]]
            else:
                collections_to_clear = list(self.category_collections.values()) + [self.collection]
            
            for collection in collections_to_clear:
                try:
                    # Get all memories for user
                    results = collection.get(where={"user_id": user_id})
                    
                    if results["ids"]:
                        # Delete all memories
                        collection.delete(ids=results["ids"])
                        deleted_count += len(results["ids"])
                
                except Exception as e:
                    logger.warning(f"Error clearing memories from {collection.name}: {e}")
                    continue
            
            logger.info(f"Cleared {deleted_count} memories for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing user memories: {e}")
            return 0
