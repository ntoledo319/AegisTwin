"""
Logging configuration for the Advanced Data Analysis & Digital Twin System.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from loguru import logger
from .config import settings

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward Loguru.
    
    This handler intercepts all standard logging calls and redirects them to Loguru.
    """
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """
    Configure logging for the application.
    
    This sets up Loguru as the main logging system and intercepts standard logging calls.
    """
    # Remove default loguru handler
    logger.remove()
    
    # Configure log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # Add file handler if configured
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.LOG_FILE,
            format=log_format,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            compression="zip",
            retention="30 days",
        )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Intercept specific libraries
    for lib_logger in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "neo4j",
        "httpx",
    ]:
        logging.getLogger(lib_logger).handlers = [InterceptHandler()]
    
    # Set Loguru as the root logger
    logging.getLogger().handlers = [InterceptHandler()]
    
    logger.info("Logging system initialized")
    
    return logger

# Create global logger instance
app_logger = setup_logging()

def get_logger(name: Optional[str] = None):
    """Get a logger instance."""
    if name:
        return logger.bind(name=name)
    return logger