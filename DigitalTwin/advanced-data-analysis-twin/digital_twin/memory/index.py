"""
Memory Index for the Digital Twin.

This module provides functionality for indexing and searching memories.
"""

import logging
from typing import Dict, Any, List, Optional
import json
import os
import datetime

logger = logging.getLogger(__name__)


class MemoryIndex:
    """
    Index for efficient memory retrieval.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the memory index.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.index_dir = self.config.get("index_dir", "memory_index")
        self.vector_db = None
        self._initialize_vector_db()
        logger.info("Memory Index initialized")

    def _initialize_vector_db(self) -> None:
        """
        Initialize the vector database for memory indexing.
        """
        try:
            # Try to import the vector database client
            from ....core.db.vector_db import VectorDBClient
            
            # Initialize the vector database client
            self.vector_db = VectorDBClient()
            logger.info("Vector database client initialized")
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            logger.warning("Using fallback in-memory index")
            self.vector_db = None
            
            # Create index directory if it doesn't exist
            os.makedirs(self.index_dir, exist_ok=True)

    async def index_memory(self, memory: Dict[str, Any]) -> None:
        """
        Index a memory for efficient retrieval.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            logger.warning("Cannot index memory: missing memory_id or user_id")
            return
            
        # If vector database is available, use it
        if self.vector_db:
            try:
                # Extract text content from memory for embedding
                text_content = self._extract_text_content(memory)
                
                # Create metadata for filtering
                metadata = {
                    "user_id": user_id,
                    "memory_type": memory.get("memory_type", "unknown"),
                    "created_at": memory.get("created_at", ""),
                    "tags": json.dumps(memory.get("tags", [])),
                    "entities": json.dumps(memory.get("entities", [])),
                    "importance": str(memory.get("importance", 0.5))
                }
                
                # Index the memory in the vector database
                await self.vector_db.index(
                    collection=f"memories_{user_id}",
                    id=memory_id,
                    text=text_content,
                    metadata=metadata
                )
                
                logger.debug(f"Indexed memory {memory_id} in vector database")
            except Exception as e:
                logger.error(f"Error indexing memory in vector database: {str(e)}")
                logger.warning("Falling back to file-based index")
                await self._fallback_index_memory(memory)
        else:
            # Use fallback file-based indexing
            await self._fallback_index_memory(memory)

    async def _fallback_index_memory(self, memory: Dict[str, Any]) -> None:
        """
        Fallback method to index a memory using file-based storage.

        Args:
            memory: Memory dictionary
        """
        memory_id = memory.get("memory_id")
        user_id = memory.get("user_id")
        
        if not memory_id or not user_id:
            return
            
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.index_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save memory index entry
        index_path = os.path.join(user_dir, f"{memory_id}.json")
        
        # Create index entry
        index_entry = {
            "memory_id": memory_id,
            "user_id": user_id,
            "memory_type": memory.get("memory_type", "unknown"),
            "created_at": memory.get("created_at", ""),
            "tags": memory.get("tags", []),
            "entities": memory.get("entities", []),
            "importance": memory.get("importance", 0.5),
            "text_content": self._extract_text_content(memory)
        }
        
        # Write index entry to file
        with open(index_path, 'w') as f:
            json.dump(index_entry, f)
            
        logger.debug(f"Indexed memory {memory_id} using file-based index")

    def _extract_text_content(self, memory: Dict[str, Any]) -> str:
        """
        Extract text content from a memory for indexing.

        Args:
            memory: Memory dictionary

        Returns:
            Text content for indexing
        """
        # Extract text content based on memory type
        memory_type = memory.get("memory_type", "unknown")
        
        if memory_type == "episodic":
            # For episodic memories, combine title, description, and context
            title = memory.get("title", "")
            description = memory.get("description", "")
            context = memory.get("context", {})
            context_str = " ".join(f"{k}: {v}" for k, v in context.items() if isinstance(v, (str, int, float)))
            
            return f"{title} {description} {context_str}".strip()
            
        elif memory_type == "semantic":
            # For semantic memories, combine concept and information
            concept = memory.get("concept", "")
            information = memory.get("information", "")
            
            return f"{concept} {information}".strip()
            
        elif memory_type == "procedural":
            # For procedural memories, combine task and steps
            task = memory.get("task", "")
            steps = memory.get("steps", [])
            steps_str = " ".join(steps)
            
            return f"{task} {steps_str}".strip()
            
        else:
            # For unknown memory types, try to extract any text content
            text_fields = ["content", "text", "description", "title", "message"]
            content = []
            
            for field in text_fields:
                if field in memory and isinstance(memory[field], str):
                    content.append(memory[field])
                    
            return " ".join(content).strip()

    async def search(self, user_id: str, query: Dict[str, Any], limit: int = 10) -> List[str]:
        """
        Search for memories based on a query.

        Args:
            user_id: User ID
            query: Query dictionary
            limit: Maximum number of results

        Returns:
            List of memory IDs
        """
        # If vector database is available, use it
        if self.vector_db:
            try:
                # Extract text query
                text_query = query.get("text", "")
                
                # Extract filter criteria
                filter_criteria = {}
                
                if "memory_type" in query:
                    filter_criteria["memory_type"] = query["memory_type"]
                    
                if "tags" in query and query["tags"]:
                    filter_criteria["tags"] = {"$contains": json.dumps(query["tags"][0])}
                    
                if "entities" in query and query["entities"]:
                    filter_criteria["entities"] = {"$contains": json.dumps(query["entities"][0])}
                    
                if "start_date" in query:
                    filter_criteria["created_at"] = {"$gte": query["start_date"]}
                    
                if "end_date" in query:
                    if "created_at" in filter_criteria:
                        filter_criteria["created_at"]["$lte"] = query["end_date"]
                    else:
                        filter_criteria["created_at"] = {"$lte": query["end_date"]}
                        
                if "min_importance" in query:
                    filter_criteria["importance"] = {"$gte": str(query["min_importance"])}
                
                # Always filter by user_id
                filter_criteria["user_id"] = user_id
                
                # Search the vector database
                results = await self.vector_db.search(
                    collection=f"memories_{user_id}",
                    query=text_query,
                    filter=filter_criteria,
                    limit=limit
                )
                
                # Extract memory IDs from results
                memory_ids = [result["id"] for result in results]
                
                logger.debug(f"Found {len(memory_ids)} memories in vector database")
                return memory_ids
                
            except Exception as e:
                logger.error(f"Error searching vector database: {str(e)}")
                logger.warning("Falling back to file-based search")
                return await self._fallback_search(user_id, query, limit)
        else:
            # Use fallback file-based search
            return await self._fallback_search(user_id, query, limit)

    async def _fallback_search(self, user_id: str, query: Dict[str, Any], limit: int = 10) -> List[str]:
        """
        Fallback method to search for memories using file-based storage.

        Args:
            user_id: User ID
            query: Query dictionary
            limit: Maximum number of results

        Returns:
            List of memory IDs
        """
        # Check if user directory exists
        user_dir = os.path.join(self.index_dir, user_id)
        if not os.path.exists(user_dir):
            return []
            
        # Get all index files
        index_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
        
        # Load all index entries
        index_entries = []
        for file_name in index_files:
            file_path = os.path.join(user_dir, file_name)
            try:
                with open(file_path, 'r') as f:
                    entry = json.load(f)
                    index_entries.append(entry)
            except Exception as e:
                logger.error(f"Error loading index entry {file_path}: {str(e)}")
                
        # Filter entries based on query
        filtered_entries = self._filter_entries(index_entries, query)
        
        # Sort by relevance or recency
        if "text" in query and query["text"]:
            # Sort by text relevance
            text_query = query["text"].lower()
            for entry in filtered_entries:
                text_content = entry.get("text_content", "").lower()
                # Simple relevance score based on word overlap
                query_words = set(text_query.split())
                content_words = set(text_content.split())
                overlap = len(query_words.intersection(content_words))
                entry["_relevance"] = overlap / max(1, len(query_words))
                
            filtered_entries.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        else:
            # Sort by recency
            filtered_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        # Limit results
        filtered_entries = filtered_entries[:limit]
        
        # Extract memory IDs
        memory_ids = [entry.get("memory_id") for entry in filtered_entries]
        
        logger.debug(f"Found {len(memory_ids)} memories in file-based index")
        return memory_ids

    def _filter_entries(self, entries: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter index entries based on query criteria.

        Args:
            entries: List of index entries
            query: Query dictionary

        Returns:
            Filtered list of index entries
        """
        filtered = entries
        
        # Filter by memory type
        if "memory_type" in query:
            filtered = [e for e in filtered if e.get("memory_type") == query["memory_type"]]
            
        # Filter by tags
        if "tags" in query and query["tags"]:
            filtered = [e for e in filtered if any(tag in e.get("tags", []) for tag in query["tags"])]
            
        # Filter by entities
        if "entities" in query and query["entities"]:
            filtered = [e for e in filtered if any(entity in e.get("entities", []) for entity in query["entities"])]
            
        # Filter by date range
        if "start_date" in query:
            try:
                start_date = datetime.datetime.fromisoformat(query["start_date"])
                filtered = [e for e in filtered if "created_at" in e and datetime.datetime.fromisoformat(e["created_at"]) >= start_date]
            except (ValueError, TypeError):
                pass
                
        if "end_date" in query:
            try:
                end_date = datetime.datetime.fromisoformat(query["end_date"])
                filtered = [e for e in filtered if "created_at" in e and datetime.datetime.fromisoformat(e["created_at"]) <= end_date]
            except (ValueError, TypeError):
                pass
                
        # Filter by importance
        if "min_importance" in query:
            min_importance = float(query["min_importance"])
            filtered = [e for e in filtered if e.get("importance", 0) >= min_importance]
            
        # Filter by text content
        if "text" in query and query["text"]:
            text_query = query["text"].lower()
            filtered = [e for e in filtered if text_query in e.get("text_content", "").lower()]
            
        return filtered

    async def update_memory(self, memory: Dict[str, Any]) -> None:
        """
        Update a memory in the index.

        Args:
            memory: Updated memory dictionary
        """
        # Delete the old index entry and create a new one
        memory_id = memory.get("memory_id")
        
        if not memory_id:
            logger.warning("Cannot update memory index: missing memory_id")
            return
            
        await self.delete_memory(memory_id)
        await self.index_memory(memory)
        
        logger.debug(f"Updated memory {memory_id} in index")

    async def delete_memory(self, memory_id: str) -> None:
        """
        Delete a memory from the index.

        Args:
            memory_id: Memory ID
        """
        # If vector database is available, use it
        if self.vector_db:
            try:
                # Delete from all user collections (we don't know which user it belongs to)
                collections = await self.vector_db.list_collections()
                
                for collection in collections:
                    if collection.startswith("memories_"):
                        await self.vector_db.delete(
                            collection=collection,
                            id=memory_id
                        )
                        
                logger.debug(f"Deleted memory {memory_id} from vector database")
            except Exception as e:
                logger.error(f"Error deleting memory from vector database: {str(e)}")
                logger.warning("Falling back to file-based deletion")
                await self._fallback_delete_memory(memory_id)
        else:
            # Use fallback file-based deletion
            await self._fallback_delete_memory(memory_id)

    async def _fallback_delete_memory(self, memory_id: str) -> None:
        """
        Fallback method to delete a memory from file-based storage.

        Args:
            memory_id: Memory ID
        """
        # Search for the memory index file in all user directories
        for user_dir in os.listdir(self.index_dir):
            user_dir_path = os.path.join(self.index_dir, user_dir)
            
            if os.path.isdir(user_dir_path):
                index_path = os.path.join(user_dir_path, f"{memory_id}.json")
                
                if os.path.exists(index_path):
                    try:
                        os.remove(index_path)
                        logger.debug(f"Deleted memory {memory_id} from file-based index")
                    except Exception as e:
                        logger.error(f"Error deleting index file {index_path}: {str(e)}")