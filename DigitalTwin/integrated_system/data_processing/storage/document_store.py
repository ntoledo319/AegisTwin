"""
Document store for the integrated system.
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from core.config import config
from core.db import db_manager

logger = logging.getLogger(__name__)

class DocumentStore:
    """Document store for storing and retrieving documents."""
    
    def __init__(self):
        """Initialize the document store."""
        self.mongodb_collection = None
        self.storage_dir = config.get("storage.data_dir", "data")
        
    async def initialize(self):
        """Initialize the document store."""
        logger.info("Initializing document store...")
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Get MongoDB collection
        self.mongodb_collection = db_manager.get_mongodb_collection("documents")
        
        logger.info("Document store initialization complete")
        
    async def store_document(self, 
                            document_type: str, 
                            document: Dict[str, Any],
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a document.
        
        Args:
            document_type: Type of document
            document: Document to store
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        try:
            # Generate document ID
            document_id = f"{document_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(document))}"
            
            # Add metadata
            metadata = metadata or {}
            metadata["document_type"] = document_type
            metadata["created_at"] = datetime.now()
            
            # Store in MongoDB
            if self.mongodb_collection:
                await self.mongodb_collection.insert_one({
                    "_id": document_id,
                    "document_type": document_type,
                    "document": document,
                    "metadata": metadata
                })
                
            # Store in file system
            document_dir = os.path.join(self.storage_dir, document_type)
            os.makedirs(document_dir, exist_ok=True)
            
            document_path = os.path.join(document_dir, f"{document_id}.json")
            
            with open(document_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "document_id": document_id,
                    "document_type": document_type,
                    "document": document,
                    "metadata": metadata
                }, f, default=self._json_serializer)
                
            logger.info(f"Stored document: {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise
            
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        try:
            # Try to get from MongoDB
            if self.mongodb_collection:
                document = await self.mongodb_collection.find_one({"_id": document_id})
                if document:
                    return document
                    
            # Try to get from file system
            document_type = document_id.split("_")[0]
            document_path = os.path.join(self.storage_dir, document_type, f"{document_id}.json")
            
            if os.path.exists(document_path):
                with open(document_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            logger.warning(f"Document not found: {document_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
            
    async def search_documents(self, 
                              document_type: Optional[str] = None,
                              query: Optional[Dict[str, Any]] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for documents.
        
        Args:
            document_type: Optional document type filter
            query: Optional query
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        try:
            # Build query
            search_query = {}
            
            if document_type:
                search_query["document_type"] = document_type
                
            if query:
                search_query.update(query)
                
            # Try to search in MongoDB
            if self.mongodb_collection:
                cursor = self.mongodb_collection.find(search_query).limit(limit)
                documents = await cursor.to_list(length=limit)
                if documents:
                    return documents
                    
            # Search in file system
            documents = []
            
            if document_type:
                document_dir = os.path.join(self.storage_dir, document_type)
                if os.path.exists(document_dir):
                    for filename in os.listdir(document_dir):
                        if filename.endswith(".json"):
                            document_path = os.path.join(document_dir, filename)
                            with open(document_path, 'r', encoding='utf-8') as f:
                                document = json.load(f)
                                
                                # Apply query filter
                                if query:
                                    match = True
                                    for key, value in query.items():
                                        if key not in document or document[key] != value:
                                            match = False
                                            break
                                            
                                    if not match:
                                        continue
                                        
                                documents.append(document)
                                
                                if len(documents) >= limit:
                                    break
            else:
                # Search all document types
                for dir_name in os.listdir(self.storage_dir):
                    dir_path = os.path.join(self.storage_dir, dir_name)
                    if os.path.isdir(dir_path):
                        for filename in os.listdir(dir_path):
                            if filename.endswith(".json"):
                                document_path = os.path.join(dir_path, filename)
                                with open(document_path, 'r', encoding='utf-8') as f:
                                    document = json.load(f)
                                    
                                    # Apply query filter
                                    if query:
                                        match = True
                                        for key, value in query.items():
                                            if key not in document or document[key] != value:
                                                match = False
                                                break
                                                
                                        if not match:
                                            continue
                                            
                                    documents.append(document)
                                    
                                    if len(documents) >= limit:
                                        break
                                        
                        if len(documents) >= limit:
                            break
                            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
            
    async def update_document(self, 
                             document_id: str, 
                             updates: Dict[str, Any]) -> bool:
        """
        Update a document.
        
        Args:
            document_id: Document ID
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get document
            document = await self.get_document(document_id)
            
            if not document:
                logger.warning(f"Document not found for update: {document_id}")
                return False
                
            # Update document
            for key, value in updates.items():
                if key in document:
                    document[key] = value
                    
            # Update metadata
            document["metadata"]["updated_at"] = datetime.now()
            
            # Store updated document
            document_type = document["document_type"]
            
            # Update in MongoDB
            if self.mongodb_collection:
                await self.mongodb_collection.update_one(
                    {"_id": document_id},
                    {"$set": document}
                )
                
            # Update in file system
            document_path = os.path.join(self.storage_dir, document_type, f"{document_id}.json")
            
            with open(document_path, 'w', encoding='utf-8') as f:
                json.dump(document, f, default=self._json_serializer)
                
            logger.info(f"Updated document: {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False
            
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get document type
            document_type = document_id.split("_")[0]
            
            # Delete from MongoDB
            if self.mongodb_collection:
                await self.mongodb_collection.delete_one({"_id": document_id})
                
            # Delete from file system
            document_path = os.path.join(self.storage_dir, document_type, f"{document_id}.json")
            
            if os.path.exists(document_path):
                os.remove(document_path)
                
            logger.info(f"Deleted document: {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
            
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
        raise TypeError(f"Type {type(obj)} not serializable")