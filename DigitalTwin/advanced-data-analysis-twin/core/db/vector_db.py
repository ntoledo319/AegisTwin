"""
Vector database client for the Advanced Data Analysis & Digital Twin System.
Uses Pinecone for storing and querying vector embeddings.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import pinecone
from pinecone import PineconeException

logger = logging.getLogger(__name__)

class VectorDBClient:
    """
    Vector database client for storing and querying vector embeddings.
    """
    
    def __init__(self, api_key: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize the vector database client.
        
        Parameters:
        - api_key: Pinecone API key
        - environment: Pinecone environment
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
        self.initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the Pinecone client.
        
        Raises:
        - PineconeException: If initialization fails
        """
        try:
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.initialized = True
            logger.info(f"Initialized Pinecone client in environment: {self.environment}")
        except PineconeException as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise
    
    def _check_initialized(self) -> None:
        """
        Check if the client is initialized.
        
        Raises:
        - ValueError: If client is not initialized
        """
        if not self.initialized:
            raise ValueError("Pinecone client is not initialized")
    
    async def list_indexes(self) -> List[str]:
        """
        List all indexes.
        
        Returns:
        - List of index names
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            return pinecone.list_indexes()
        except PineconeException as e:
            logger.error(f"Failed to list Pinecone indexes: {e}")
            raise
    
    async def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """
        Create a new index.
        
        Parameters:
        - name: Index name
        - dimension: Vector dimension
        - metric: Distance metric (cosine, euclidean, dotproduct)
        
        Returns:
        - True if successful
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            if name in pinecone.list_indexes():
                logger.warning(f"Pinecone index {name} already exists")
                return True
            
            pinecone.create_index(name=name, dimension=dimension, metric=metric)
            logger.info(f"Created Pinecone index: {name}, dimension: {dimension}, metric: {metric}")
            return True
        except PineconeException as e:
            logger.error(f"Failed to create Pinecone index {name}: {e}")
            raise
    
    async def delete_index(self, name: str) -> bool:
        """
        Delete an index.
        
        Parameters:
        - name: Index name
        
        Returns:
        - True if successful
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            if name not in pinecone.list_indexes():
                logger.warning(f"Pinecone index {name} does not exist")
                return False
            
            pinecone.delete_index(name)
            logger.info(f"Deleted Pinecone index: {name}")
            return True
        except PineconeException as e:
            logger.error(f"Failed to delete Pinecone index {name}: {e}")
            raise
    
    async def get_index_stats(self, name: str) -> Dict[str, Any]:
        """
        Get statistics for an index.
        
        Parameters:
        - name: Index name
        
        Returns:
        - Index statistics
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            index = pinecone.Index(name)
            stats = index.describe_index_stats()
            return stats
        except PineconeException as e:
            logger.error(f"Failed to get stats for Pinecone index {name}: {e}")
            raise
    
    async def upsert_vectors(self, index_name: str, vectors: List[Tuple[str, List[float], Optional[Dict[str, Any]]]]) -> int:
        """
        Upsert vectors into an index.
        
        Parameters:
        - index_name: Index name
        - vectors: List of tuples (id, vector, metadata)
        
        Returns:
        - Number of vectors upserted
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            index = pinecone.Index(index_name)
            
            # Format vectors for Pinecone
            pinecone_vectors = []
            for vector_id, vector, metadata in vectors:
                pinecone_vectors.append({
                    "id": vector_id,
                    "values": vector,
                    "metadata": metadata or {}
                })
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i:i+batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone index {index_name}")
            return len(vectors)
        except PineconeException as e:
            logger.error(f"Failed to upsert vectors to Pinecone index {index_name}: {e}")
            raise
    
    async def query_vectors(self, index_name: str, query_vector: List[float], top_k: int = 10, filter: Optional[Dict[str, Any]] = None, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Query vectors from an index.
        
        Parameters:
        - index_name: Index name
        - query_vector: Query vector
        - top_k: Number of results to return
        - filter: Metadata filter
        - include_metadata: Whether to include metadata in results
        
        Returns:
        - List of query results
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            index = pinecone.Index(index_name)
            
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=include_metadata,
                filter=filter
            )
            
            # Format results
            formatted_results = []
            for match in results["matches"]:
                result = {
                    "id": match["id"],
                    "score": match["score"]
                }
                
                if include_metadata and "metadata" in match:
                    result["metadata"] = match["metadata"]
                
                formatted_results.append(result)
            
            return formatted_results
        except PineconeException as e:
            logger.error(f"Failed to query vectors from Pinecone index {index_name}: {e}")
            raise
    
    async def fetch_vectors(self, index_name: str, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch vectors by IDs.
        
        Parameters:
        - index_name: Index name
        - ids: Vector IDs
        
        Returns:
        - Dictionary of vectors
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            index = pinecone.Index(index_name)
            
            results = index.fetch(ids=ids)
            
            return results["vectors"]
        except PineconeException as e:
            logger.error(f"Failed to fetch vectors from Pinecone index {index_name}: {e}")
            raise
    
    async def delete_vectors(self, index_name: str, ids: List[str]) -> bool:
        """
        Delete vectors by IDs.
        
        Parameters:
        - index_name: Index name
        - ids: Vector IDs
        
        Returns:
        - True if successful
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            index = pinecone.Index(index_name)
            
            # Delete in batches of 100
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i+batch_size]
                index.delete(ids=batch)
            
            logger.info(f"Deleted {len(ids)} vectors from Pinecone index {index_name}")
            return True
        except PineconeException as e:
            logger.error(f"Failed to delete vectors from Pinecone index {index_name}: {e}")
            raise
    
    async def update_vector_metadata(self, index_name: str, id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update vector metadata.
        
        Parameters:
        - index_name: Index name
        - id: Vector ID
        - metadata: New metadata
        
        Returns:
        - True if successful
        
        Raises:
        - ValueError: If client is not initialized
        - PineconeException: If operation fails
        """
        self._check_initialized()
        
        try:
            # Fetch the vector first
            index = pinecone.Index(index_name)
            vector_data = index.fetch(ids=[id])
            
            if id not in vector_data["vectors"]:
                logger.warning(f"Vector {id} not found in Pinecone index {index_name}")
                return False
            
            # Get the vector values
            vector = vector_data["vectors"][id]["values"]
            
            # Upsert with new metadata
            index.upsert(vectors=[{
                "id": id,
                "values": vector,
                "metadata": metadata
            }])
            
            logger.info(f"Updated metadata for vector {id} in Pinecone index {index_name}")
            return True
        except PineconeException as e:
            logger.error(f"Failed to update metadata for vector {id} in Pinecone index {index_name}: {e}")
            raise

# Singleton instance
vector_db_client = VectorDBClient()