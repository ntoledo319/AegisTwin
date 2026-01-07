"""
Data processors for the Advanced Data Analysis & Digital Twin System.
"""

from typing import Dict, Type, Any

from .text import TextProcessor
from .entity import EntityProcessor
from .normalization import NormalizationProcessor

# Register all processors here
PROCESSOR_REGISTRY = {
    "text": TextProcessor,
    "entity": EntityProcessor,
    "normalization": NormalizationProcessor,
}

def get_processor_class(processor_type: str):
    """
    Get processor class by type.
    
    Args:
        processor_type: Type of processor
        
    Returns:
        Processor class
        
    Raises:
        ValueError: If processor type is not found
    """
    if processor_type not in PROCESSOR_REGISTRY:
        raise ValueError(f"Processor type not found: {processor_type}")
    
    return PROCESSOR_REGISTRY[processor_type]

def get_available_processors() -> Dict[str, str]:
    """
    Get a dictionary of available processor types and their descriptions.
    
    Returns:
        Dictionary mapping processor types to descriptions
    """
    return {
        "text": "Processor for analyzing and processing textual content",
        "entity": "Processor for entity extraction and linking",
        "normalization": "Processor for data normalization",
    }

async def create_processor(processor_type: str, config: Dict[str, Any] = None):
    """
    Create a processor instance.
    
    Args:
        processor_type: Type of processor
        config: Configuration dictionary
        
    Returns:
        Processor instance
    """
    processor_class = get_processor_class(processor_type)
    return processor_class(config or {})

__all__ = [
    "TextProcessor",
    "EntityProcessor",
    "NormalizationProcessor",
    "get_processor_class",
    "get_available_processors",
    "create_processor",
    "PROCESSOR_REGISTRY",
]