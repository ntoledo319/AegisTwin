"""
Configuration management for the Advanced Data Analysis & Digital Twin System.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "Advanced Data Analysis & Digital Twin"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API settings
    API_PREFIX: str = "/api"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Database settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "advanced_data_analysis")
    
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    REDIS_URI: str = os.getenv("REDIS_URI", "redis://localhost:6379")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    
    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")
    
    # Storage settings
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "./temp"))
    
    # SpiderMind Omega integration
    SPIDERMIND_DIR: Path = Path(os.getenv("SPIDERMIND_DIR", "../ct_omega"))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings

def initialize_directories():
    """Initialize required directories."""
    directories = [
        settings.DATA_DIR,
        settings.TEMP_DIR,
        settings.DATA_DIR / "profiles",
        settings.DATA_DIR / "imports",
        settings.DATA_DIR / "exports",
        settings.DATA_DIR / "reports",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)