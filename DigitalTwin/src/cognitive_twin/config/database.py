"""
Database Configuration

Centralized database connection and configuration management
for PostgreSQL, MongoDB, Redis, and Neo4j.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration container"""
    
    # PostgreSQL Configuration
    postgres_url: Optional[str] = None
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20
    postgres_pool_timeout: int = 30
    postgres_pool_recycle: int = 3600
    
    # MongoDB Configuration
    mongodb_url: Optional[str] = None
    mongodb_database: str = "cognitive_twin"
    mongodb_max_pool_size: int = 100
    mongodb_min_pool_size: int = 10
    mongodb_server_selection_timeout: int = 5000
    
    # Redis Configuration
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_max_connections: int = 100
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_retry_on_timeout: bool = True
    
    # Neo4j Configuration
    neo4j_url: Optional[str] = None
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None
    neo4j_max_connection_lifetime: int = 3600
    neo4j_max_connection_pool_size: int = 100
    neo4j_connection_acquisition_timeout: int = 60
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        self._validate_urls()
        self._setup_connection_strings()
    
    def _validate_urls(self):
        """Validate database URLs"""
        if self.postgres_url:
            try:
                parsed = urlparse(self.postgres_url)
                if parsed.scheme not in ['postgresql', 'postgresql+asyncpg']:
                    logger.warning(f"PostgreSQL URL scheme should be 'postgresql' or 'postgresql+asyncpg', got: {parsed.scheme}")
            except Exception as e:
                logger.error(f"Invalid PostgreSQL URL: {e}")
        
        if self.mongodb_url:
            try:
                parsed = urlparse(self.mongodb_url)
                if parsed.scheme not in ['mongodb', 'mongodb+srv']:
                    logger.warning(f"MongoDB URL scheme should be 'mongodb' or 'mongodb+srv', got: {parsed.scheme}")
            except Exception as e:
                logger.error(f"Invalid MongoDB URL: {e}")
        
        if self.redis_url:
            try:
                parsed = urlparse(self.redis_url)
                if parsed.scheme not in ['redis', 'rediss']:
                    logger.warning(f"Redis URL scheme should be 'redis' or 'rediss', got: {parsed.scheme}")
            except Exception as e:
                logger.error(f"Invalid Redis URL: {e}")
        
        if self.neo4j_url:
            try:
                parsed = urlparse(self.neo4j_url)
                if parsed.scheme not in ['bolt', 'bolt+s', 'neo4j', 'neo4j+s']:
                    logger.warning(f"Neo4j URL scheme should be 'bolt', 'bolt+s', 'neo4j', or 'neo4j+s', got: {parsed.scheme}")
            except Exception as e:
                logger.error(f"Invalid Neo4j URL: {e}")
    
    def _setup_connection_strings(self):
        """Setup default connection strings if not provided"""
        if not self.postgres_url:
            self.postgres_url = "postgresql://cognitive_twin:password@localhost:5432/cognitive_twin"
            logger.info("Using default PostgreSQL connection string")
        
        if not self.mongodb_url:
            self.mongodb_url = "mongodb://cognitive_twin:password@localhost:27017/cognitive_twin"
            logger.info("Using default MongoDB connection string")
        
        if not self.redis_url:
            self.redis_url = "redis://localhost:6379"
            logger.info("Using default Redis connection string")
        
        if not self.neo4j_url:
            self.neo4j_url = "bolt://localhost:7687"
            logger.info("Using default Neo4j connection string")
    
    @property
    def postgres_config(self) -> Dict[str, Any]:
        """Get PostgreSQL configuration"""
        return {
            "url": self.postgres_url,
            "pool_size": self.postgres_pool_size,
            "max_overflow": self.postgres_max_overflow,
            "pool_timeout": self.postgres_pool_timeout,
            "pool_recycle": self.postgres_pool_recycle,
            "echo": False,  # Set to True for SQL debugging
            "future": True
        }
    
    @property
    def mongodb_config(self) -> Dict[str, Any]:
        """Get MongoDB configuration"""
        return {
            "url": self.mongodb_url,
            "database": self.mongodb_database,
            "maxPoolSize": self.mongodb_max_pool_size,
            "minPoolSize": self.mongodb_min_pool_size,
            "serverSelectionTimeoutMS": self.mongodb_server_selection_timeout,
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 10000,
            "maxIdleTimeMS": 30000,
            "retryWrites": True,
            "retryReads": True
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        config = {
            "url": self.redis_url,
            "db": self.redis_db,
            "max_connections": self.redis_max_connections,
            "socket_timeout": self.redis_socket_timeout,
            "socket_connect_timeout": self.redis_socket_connect_timeout,
            "retry_on_timeout": self.redis_retry_on_timeout,
            "decode_responses": True,
            "health_check_interval": 30
        }
        
        if self.redis_password:
            config["password"] = self.redis_password
        
        return config
    
    @property
    def neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration"""
        return {
            "uri": self.neo4j_url,
            "auth": (self.neo4j_user, self.neo4j_password) if self.neo4j_password else None,
            "max_connection_lifetime": self.neo4j_max_connection_lifetime,
            "max_connection_pool_size": self.neo4j_max_connection_pool_size,
            "connection_acquisition_timeout": self.neo4j_connection_acquisition_timeout,
            "encrypted": self.neo4j_url.startswith(('bolt+s://', 'neo4j+s://')) if self.neo4j_url else False
        }
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all database configurations"""
        return {
            "postgres": self.postgres_config,
            "mongodb": self.mongodb_config,
            "redis": self.redis_config,
            "neo4j": self.neo4j_config
        }
    
    def validate_connections(self) -> Dict[str, bool]:
        """Validate all database connections (without actually connecting)"""
        validation_results = {}
        
        # Validate PostgreSQL
        try:
            if self.postgres_url:
                parsed = urlparse(self.postgres_url)
                validation_results["postgres"] = bool(parsed.hostname and parsed.port)
            else:
                validation_results["postgres"] = False
        except Exception:
            validation_results["postgres"] = False
        
        # Validate MongoDB
        try:
            if self.mongodb_url:
                parsed = urlparse(self.mongodb_url)
                validation_results["mongodb"] = bool(parsed.hostname)
            else:
                validation_results["mongodb"] = False
        except Exception:
            validation_results["mongodb"] = False
        
        # Validate Redis
        try:
            if self.redis_url:
                parsed = urlparse(self.redis_url)
                validation_results["redis"] = bool(parsed.hostname)
            else:
                validation_results["redis"] = False
        except Exception:
            validation_results["redis"] = False
        
        # Validate Neo4j
        try:
            if self.neo4j_url:
                parsed = urlparse(self.neo4j_url)
                validation_results["neo4j"] = bool(parsed.hostname and parsed.port)
            else:
                validation_results["neo4j"] = False
        except Exception:
            validation_results["neo4j"] = False
        
        return validation_results
    
    def get_connection_summary(self) -> Dict[str, str]:
        """Get summary of database connections"""
        summary = {}
        
        if self.postgres_url:
            parsed = urlparse(self.postgres_url)
            summary["postgres"] = f"{parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}"
        
        if self.mongodb_url:
            parsed = urlparse(self.mongodb_url)
            summary["mongodb"] = f"{parsed.hostname}:{parsed.port or 27017}/{self.mongodb_database}"
        
        if self.redis_url:
            parsed = urlparse(self.redis_url)
            summary["redis"] = f"{parsed.hostname}:{parsed.port or 6379}/{self.redis_db}"
        
        if self.neo4j_url:
            parsed = urlparse(self.neo4j_url)
            summary["neo4j"] = f"{parsed.hostname}:{parsed.port or 7687}"
        
        return summary


def create_database_config(**kwargs) -> DatabaseConfig:
    """
    Create database configuration from keyword arguments.
    
    Args:
        **kwargs: Database configuration parameters
        
    Returns:
        DatabaseConfig instance
    """
    return DatabaseConfig(**kwargs)
