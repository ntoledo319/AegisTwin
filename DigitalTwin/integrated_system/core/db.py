"""
Database management for the integrated system.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase

from core.config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for the integrated system."""
    
    def __init__(self):
        """Initialize the database manager."""
        self.postgres_engine = None
        self.postgres_session_factory = None
        self.mongodb_client = None
        self.mongodb_db = None
        self.redis_client = None
        self.neo4j_driver = None
        
    async def initialize(self, create_tables: bool = False):
        """
        Initialize database connections.
        
        Args:
            create_tables: Whether to create database tables
        """
        logger.info("Initializing database connections...")
        
        # Initialize PostgreSQL
        await self._init_postgres(create_tables)
        
        # Initialize MongoDB
        await self._init_mongodb()
        
        # Initialize Redis
        await self._init_redis()
        
        # Initialize Neo4j
        await self._init_neo4j()
        
        logger.info("Database connections initialized")
        
    async def _init_postgres(self, create_tables: bool):
        """Initialize PostgreSQL connection."""
        postgres_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/integrated_system")
        
        try:
            self.postgres_engine = create_async_engine(
                postgres_url,
                echo=config.get("database.postgres.echo", False),
                pool_size=config.get("database.postgres.pool_size", 5),
                max_overflow=config.get("database.postgres.max_overflow", 10)
            )
            
            self.postgres_session_factory = sessionmaker(
                self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables if requested
            if create_tables:
                from core.models.base import Base
                async with self.postgres_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    
            logger.info("PostgreSQL connection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL: {str(e)}")
            self.postgres_engine = None
            self.postgres_session_factory = None
            
    async def _init_mongodb(self):
        """Initialize MongoDB connection."""
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        mongodb_db_name = os.getenv("MONGODB_DB", "integrated_system")
        
        try:
            self.mongodb_client = AsyncIOMotorClient(mongodb_uri)
            self.mongodb_db = self.mongodb_client[mongodb_db_name]
            
            # Test connection
            await self.mongodb_client.admin.command('ping')
            
            logger.info("MongoDB connection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {str(e)}")
            self.mongodb_client = None
            self.mongodb_db = None
            
    async def _init_redis(self):
        """Initialize Redis connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("Redis connection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Redis: {str(e)}")
            self.redis_client = None
            
    async def _init_neo4j(self):
        """Initialize Neo4j connection."""
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
            
            # Test connection
            await self.neo4j_driver.verify_connectivity()
            
            logger.info("Neo4j connection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Neo4j: {str(e)}")
            self.neo4j_driver = None
            
    async def shutdown(self):
        """Close database connections."""
        logger.info("Closing database connections...")
        
        # Close PostgreSQL
        if self.postgres_engine:
            await self.postgres_engine.dispose()
            
        # Close MongoDB
        if self.mongodb_client:
            self.mongodb_client.close()
            
        # Close Redis
        if self.redis_client:
            await self.redis_client.close()
            
        # Close Neo4j
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            
        logger.info("Database connections closed")
        
    async def get_postgres_session(self):
        """Get PostgreSQL session."""
        if not self.postgres_session_factory:
            raise Exception("PostgreSQL not initialized")
            
        async with self.postgres_session_factory() as session:
            yield session
            
    def get_mongodb_collection(self, collection_name: str):
        """Get MongoDB collection."""
        if not self.mongodb_db:
            raise Exception("MongoDB not initialized")
            
        return self.mongodb_db[collection_name]
        
    async def get_redis_client(self):
        """Get Redis client."""
        if not self.redis_client:
            raise Exception("Redis not initialized")
            
        return self.redis_client
        
    async def run_neo4j_query(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Run Neo4j query."""
        if not self.neo4j_driver:
            raise Exception("Neo4j not initialized")
            
        async with self.neo4j_driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

# Create singleton instance
db_manager = DatabaseManager()