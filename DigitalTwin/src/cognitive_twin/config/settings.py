"""
Main Settings Configuration

Centralized configuration management using Pydantic for validation
and environment variable handling.
"""

import os
from typing import List, Optional, Dict, Any
from functools import lru_cache
from pydantic import Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Main application settings with environment variable support and validation.
    """
    
    # Application Settings
    app_name: str = Field(default="Cognitive-Twin", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")
    
    # Security Settings
    secret_key: str = Field(default="change-me-in-production", description="Secret key for JWT")
    jwt_secret_key: str = Field(default="jwt-secret-key", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=30, description="JWT expiration in minutes")
    
    # AI/ML Settings
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY", description="OpenRouter API key")
    ai_model_timeout: int = Field(default=30, description="AI model timeout in seconds")
    ai_max_tokens: int = Field(default=4000, description="Maximum tokens for AI models")
    ai_temperature: float = Field(default=0.7, description="AI model temperature")
    ai_cost_optimization: bool = Field(default=True, description="Enable AI cost optimization")
    
    # Database Settings
    postgres_url: Optional[str] = Field(default=None, env="POSTGRES_URL", description="PostgreSQL connection URL")
    mongodb_url: Optional[str] = Field(default=None, env="MONGODB_URL", description="MongoDB connection URL")
    neo4j_url: Optional[str] = Field(default=None, env="NEO4J_URL", description="Neo4j connection URL")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER", description="Neo4j username")
    neo4j_password: Optional[str] = Field(default=None, env="NEO4J_PASSWORD", description="Neo4j password")
    
    # Redis Settings
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_max_connections: int = Field(default=100, description="Redis max connections")
    
    # Vector Memory Settings
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY", description="ChromaDB persist directory")
    vector_memory_size: int = Field(default=10000, description="Vector memory size limit")
    embedding_model: str = Field(default="text-embedding-3-large", description="Embedding model for vector memory")
    
    # Event System Settings
    event_bus_enabled: bool = Field(default=True, description="Enable event bus")
    event_persistence: bool = Field(default=True, description="Enable event persistence")
    event_ttl: int = Field(default=86400, description="Event TTL in seconds")
    event_retry_attempts: int = Field(default=3, description="Event retry attempts")
    
    # WebSocket Settings
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket support")
    websocket_heartbeat_interval: int = Field(default=30, description="WebSocket heartbeat interval")
    websocket_max_connections: int = Field(default=1000, description="Maximum WebSocket connections")
    websocket_message_size_limit: int = Field(default=1024*1024, description="WebSocket message size limit")
    
    # Memory System Settings
    memory_cache_size: int = Field(default=1000, description="Memory cache size")
    memory_ttl: int = Field(default=3600, description="Memory TTL in seconds")
    memory_cleanup_interval: int = Field(default=300, description="Memory cleanup interval")
    
    # Performance Settings
    max_connections: int = Field(default=100, description="Maximum connections")
    worker_processes: int = Field(default=4, description="Worker processes")
    timeout: int = Field(default=30, description="Request timeout")
    max_request_size: int = Field(default=100*1024*1024, description="Max request size (100MB)")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # File Upload Settings
    max_upload_size: int = Field(default=100*1024*1024, description="Max upload size")
    allowed_file_types: List[str] = Field(
        default=["json", "csv", "txt", "pdf", "doc", "docx"],
        description="Allowed file types for upload"
    )
    upload_directory: str = Field(default="./uploads", description="Upload directory")
    
    # Monitoring Settings
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    grafana_enabled: bool = Field(default=True, description="Enable Grafana dashboards")
    elasticsearch_enabled: bool = Field(default=True, description="Enable Elasticsearch logging")
    health_check_interval: int = Field(default=30, description="Health check interval")
    
    # Backup Settings
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_schedule: str = Field(default="0 2 * * *", description="Backup schedule (cron)")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    backup_directory: str = Field(default="./backups", description="Backup directory")
    
    # SSL/TLS Settings
    ssl_enabled: bool = Field(default=False, description="Enable SSL/TLS")
    ssl_cert_path: Optional[str] = Field(default=None, env="SSL_CERT_PATH", description="SSL certificate path")
    ssl_key_path: Optional[str] = Field(default=None, env="SSL_KEY_PATH", description="SSL key path")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level setting"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        """Parse CORS origins from string if needed"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def validate_allowed_file_types(cls, v):
        """Parse allowed file types from string if needed"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("ai_temperature")
    def validate_ai_temperature(cls, v):
        """Validate AI temperature"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("AI temperature must be between 0.0 and 2.0")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    @property
    def database_urls(self) -> Dict[str, Optional[str]]:
        """Get all database URLs"""
        return {
            "postgres": self.postgres_url,
            "mongodb": self.mongodb_url,
            "neo4j": self.neo4j_url,
            "redis": self.redis_url
        }
    
    @property
    def redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        config = {
            "url": self.redis_url or "redis://localhost:6379",
            "db": self.redis_db,
            "max_connections": self.redis_max_connections
        }
        if self.redis_password:
            config["password"] = self.redis_password
        return config
    
    @property
    def cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_credentials,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    
    def get_database_url(self, db_type: str) -> Optional[str]:
        """Get database URL by type"""
        return self.database_urls.get(db_type)
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required settings for production
        if self.is_production:
            if not self.openrouter_api_key:
                issues.append("OPENROUTER_API_KEY is required for production")
            if self.secret_key == "change-me-in-production":
                issues.append("SECRET_KEY must be changed for production")
            if not self.postgres_url:
                issues.append("POSTGRES_URL is required for production")
            if not self.redis_url:
                issues.append("REDIS_URL is required for production")
        
        # Check SSL configuration
        if self.ssl_enabled:
            if not self.ssl_cert_path or not self.ssl_key_path:
                issues.append("SSL_CERT_PATH and SSL_KEY_PATH required when SSL is enabled")
        
        # Check directories exist
        directories = [
            self.chroma_persist_directory,
            self.upload_directory,
            self.backup_directory
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    logger.info(f"Created directory: {directory}")
                except Exception as e:
                    issues.append(f"Cannot create directory {directory}: {e}")
        
        return issues
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "default" if self.is_production else "detailed",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": self.log_level,
                    "formatter": "detailed",
                    "filename": "logs/cognitive_twin.log",
                    "mode": "a"
                }
            },
            "loggers": {
                "cognitive_twin": {
                    "level": self.log_level,
                    "handlers": ["console", "file"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"]
            }
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    
    # Validate configuration
    issues = settings.validate_configuration()
    if issues:
        if settings.is_production:
            # Fail fast in production
            raise ValueError(f"Configuration issues in production: {'; '.join(issues)}")
        else:
            # Warn in development
            for issue in issues:
                logger.warning(f"Configuration issue: {issue}")
    
    return settings


def refresh_settings():
    """Refresh cached settings"""
    get_settings.cache_clear()


# Global settings instance
settings = get_settings()
