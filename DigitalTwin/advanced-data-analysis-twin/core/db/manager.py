"""
Database manager for the Advanced Data Analysis & Digital Twin System.
Handles initialization and management of all database connections.
"""

import logging
from typing import Dict, Any, Optional
from .mongodb import mongodb_manager
from .neo4j import neo4j_client
from .redis import redis_client
from .vector_db import vector_db_client

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager for handling all database connections.
    """
    
    def __init__(self):
        """
        Initialize the database manager.
        """
        self.mongodb = mongodb_manager
        self.neo4j = neo4j_client
        self.redis = redis_client
        self.vector_db = vector_db_client
        self.initialized = False
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize all database connections.
        
        Parameters:
        - config: Optional configuration dictionary
        
        Raises:
        - Exception: If initialization fails
        """
        if self.initialized:
            logger.warning("Database manager is already initialized")
            return
        
        config = config or {}
        
        try:
            # Initialize MongoDB
            logger.info("Initializing MongoDB connection...")
            await self.mongodb.connect()
            
            # Initialize Neo4j
            logger.info("Initializing Neo4j connection...")
            await self.neo4j.connect()
            
            # Initialize Redis
            logger.info("Initializing Redis connection...")
            await self.redis.connect()
            
            # Initialize Vector DB
            logger.info("Initializing Vector DB connection...")
            await self.vector_db.initialize()
            
            self.initialized = True
            logger.info("All database connections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            # Clean up any connections that were established
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown all database connections.
        """
        logger.info("Shutting down database connections...")
        
        try:
            await self.mongodb.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
        
        try:
            await self.neo4j.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from Neo4j: {e}")
        
        try:
            await self.redis.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
        
        self.initialized = False
        logger.info("All database connections shut down")
    
    def check_health(self) -> Dict[str, bool]:
        """
        Check the health of all database connections.
        
        Returns:
        - Dictionary with health status of each database
        """
        health = {
            "mongodb": False,
            "neo4j": False,
            "redis": False,
            "vector_db": False
        }
        
        # Check MongoDB
        try:
            if self.mongodb.client:
                self.mongodb.client.admin.command('ping')
                health["mongodb"] = True
        except Exception:
            pass
        
        # Check Neo4j
        try:
            if self.neo4j.driver:
                with self.neo4j.driver.session() as session:
                    session.run("RETURN 1")
                health["neo4j"] = True
        except Exception:
            pass
        
        # Check Redis
        try:
            if self.redis.client:
                self.redis.client.ping()
                health["redis"] = True
        except Exception:
            pass
        
        # Check Vector DB
        try:
            health["vector_db"] = self.vector_db.initialized
        except Exception:
            pass
        
        return health

# Singleton instance
db_manager = DatabaseManager()