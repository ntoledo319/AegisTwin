"""
MongoDB connection manager for the Advanced Data Analysis & Digital Twin System.
"""

import os
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)

class MongoDBManager:
    """
    MongoDB connection manager.
    """
    
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize the MongoDB manager.
        
        Parameters:
        - uri: MongoDB connection URI
        - db_name: Database name
        """
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGODB_DB", "advanced_data_analysis_twin")
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
    
    async def connect(self) -> None:
        """
        Connect to MongoDB.
        
        Raises:
        - ConnectionFailure: If connection fails
        """
        try:
            self.client = MongoClient(self.uri)
            # Ping the server to check connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.uri}, database: {self.db_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from MongoDB.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.
        
        Parameters:
        - collection_name: Name of the collection
        
        Returns:
        - MongoDB collection
        
        Raises:
        - ValueError: If not connected to MongoDB
        """
        if not self.db:
            raise ValueError("Not connected to MongoDB")
        return self.db[collection_name]
    
    async def create_indexes(self, collection_name: str, indexes: list) -> None:
        """
        Create indexes for a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - indexes: List of index specifications
        
        Raises:
        - OperationFailure: If index creation fails
        """
        try:
            collection = self.get_collection(collection_name)
            for index in indexes:
                collection.create_index(**index)
            logger.info(f"Created indexes for collection: {collection_name}")
        except OperationFailure as e:
            logger.error(f"Failed to create indexes for collection {collection_name}: {e}")
            raise
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a document into a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - document: Document to insert
        
        Returns:
        - ID of the inserted document
        
        Raises:
        - OperationFailure: If insert fails
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except OperationFailure as e:
            logger.error(f"Failed to insert document into {collection_name}: {e}")
            raise
    
    async def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a document in a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - query: Query to find the document
        
        Returns:
        - Document if found, None otherwise
        
        Raises:
        - OperationFailure: If query fails
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.find_one(query)
        except OperationFailure as e:
            logger.error(f"Failed to find document in {collection_name}: {e}")
            raise
    
    async def find_many(self, collection_name: str, query: Dict[str, Any], limit: int = 0, skip: int = 0, sort: Optional[list] = None) -> list:
        """
        Find multiple documents in a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - query: Query to find the documents
        - limit: Maximum number of documents to return (0 for no limit)
        - skip: Number of documents to skip
        - sort: Sort specification
        
        Returns:
        - List of documents
        
        Raises:
        - OperationFailure: If query fails
        """
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(query)
            
            if skip:
                cursor = cursor.skip(skip)
            
            if limit:
                cursor = cursor.limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            return list(cursor)
        except OperationFailure as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            raise
    
    async def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """
        Update a document in a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - query: Query to find the document
        - update: Update to apply
        - upsert: Whether to insert if document doesn't exist
        
        Returns:
        - Number of documents modified
        
        Raises:
        - OperationFailure: If update fails
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(query, update, upsert=upsert)
            return result.modified_count
        except OperationFailure as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            raise
    
    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete a document from a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - query: Query to find the document
        
        Returns:
        - Number of documents deleted
        
        Raises:
        - OperationFailure: If delete fails
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(query)
            return result.deleted_count
        except OperationFailure as e:
            logger.error(f"Failed to delete document from {collection_name}: {e}")
            raise
    
    async def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count documents in a collection.
        
        Parameters:
        - collection_name: Name of the collection
        - query: Query to count documents
        
        Returns:
        - Number of documents
        
        Raises:
        - OperationFailure: If count fails
        """
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(query)
        except OperationFailure as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            raise

# Singleton instance
mongodb_manager = MongoDBManager()