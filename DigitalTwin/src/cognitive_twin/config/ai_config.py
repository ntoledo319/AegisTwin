"""
AI Configuration

Configuration for AI models, providers, and processing parameters.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """AI provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"

class TaskType(Enum):
    """AI task types"""
    CONVERSATION = "conversation"
    ANALYSIS = "analysis"
    PERSONALITY = "personality"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    CREATIVE = "creative"

@dataclass
class ModelConfig:
    """Configuration for a specific AI model"""
    name: str
    provider: AIProvider
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float
    capabilities: List[str]
    timeout: int = 30
    retries: int = 3
    fallback_model: Optional[str] = None

@dataclass
class AIConfig:
    """AI system configuration"""
    
    # API Configuration
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Model Selection
    default_conversation_model: str = "claude-3-sonnet"
    default_analysis_model: str = "claude-3-opus"
    default_personality_model: str = "gpt-4-turbo"
    default_embedding_model: str = "text-embedding-3-large"
    
    # Performance Settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Cost Management
    cost_optimization_enabled: bool = True
    max_cost_per_request: float = 0.50
    daily_cost_limit: float = 100.0
    cost_tracking_enabled: bool = True
    
    # Quality Settings
    min_confidence_threshold: float = 0.7
    quality_monitoring_enabled: bool = True
    fallback_enabled: bool = True
    
    # Caching
    response_caching_enabled: bool = True
    cache_ttl: int = 3600
    cache_size_limit: int = 1000
    
    def __post_init__(self):
        """Post-initialization setup"""
        self._setup_model_configs()
        self._validate_configuration()
    
    def _setup_model_configs(self):
        """Setup model configurations"""
        self.model_configs = {
            # OpenAI Models
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                provider=AIProvider.OPENAI,
                max_tokens=128000,
                temperature=0.7,
                cost_per_1k_tokens=0.01,
                capabilities=["conversation", "reasoning", "analysis", "code"],
                fallback_model="gpt-4"
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider=AIProvider.OPENAI,
                max_tokens=8192,
                temperature=0.7,
                cost_per_1k_tokens=0.03,
                capabilities=["conversation", "reasoning", "analysis"],
                fallback_model="gpt-3.5-turbo"
            ),
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider=AIProvider.OPENAI,
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.002,
                capabilities=["conversation", "analysis"]
            ),
            
            # Anthropic Models
            "claude-3-opus": ModelConfig(
                name="claude-3-opus",
                provider=AIProvider.ANTHROPIC,
                max_tokens=200000,
                temperature=0.7,
                cost_per_1k_tokens=0.015,
                capabilities=["analysis", "reasoning", "safety", "long_context"],
                fallback_model="claude-3-sonnet"
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet",
                provider=AIProvider.ANTHROPIC,
                max_tokens=200000,
                temperature=0.7,
                cost_per_1k_tokens=0.003,
                capabilities=["conversation", "analysis", "reasoning"],
                fallback_model="claude-3-haiku"
            ),
            "claude-3-haiku": ModelConfig(
                name="claude-3-haiku",
                provider=AIProvider.ANTHROPIC,
                max_tokens=200000,
                temperature=0.7,
                cost_per_1k_tokens=0.00025,
                capabilities=["conversation", "fast_analysis"]
            ),
            
            # Google Models
            "gemini-pro": ModelConfig(
                name="gemini-pro",
                provider=AIProvider.GOOGLE,
                max_tokens=32768,
                temperature=0.7,
                cost_per_1k_tokens=0.0005,
                capabilities=["multimodal", "embeddings", "analysis"],
                fallback_model="gemini-pro-vision"
            ),
            "gemini-pro-vision": ModelConfig(
                name="gemini-pro-vision",
                provider=AIProvider.GOOGLE,
                max_tokens=16384,
                temperature=0.7,
                cost_per_1k_tokens=0.0005,
                capabilities=["multimodal", "vision", "analysis"]
            ),
            
            # Embedding Models
            "text-embedding-3-large": ModelConfig(
                name="text-embedding-3-large",
                provider=AIProvider.OPENAI,
                max_tokens=8191,
                temperature=0.0,
                cost_per_1k_tokens=0.00013,
                capabilities=["embedding"]
            ),
            "text-embedding-3-small": ModelConfig(
                name="text-embedding-3-small",
                provider=AIProvider.OPENAI,
                max_tokens=8191,
                temperature=0.0,
                cost_per_1k_tokens=0.00002,
                capabilities=["embedding"]
            )
        }
    
    def _validate_configuration(self):
        """Validate AI configuration"""
        issues = []
        
        # Check API keys
        if not any([self.openrouter_api_key, self.openai_api_key, self.anthropic_api_key, self.google_api_key]):
            issues.append("At least one AI API key must be configured")
        
        # Check default models exist
        default_models = [
            self.default_conversation_model,
            self.default_analysis_model,
            self.default_personality_model,
            self.default_embedding_model
        ]
        
        for model in default_models:
            if model not in self.model_configs:
                issues.append(f"Default model '{model}' not found in model configurations")
        
        # Check thresholds
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            issues.append("Confidence threshold must be between 0.0 and 1.0")
        
        if self.max_cost_per_request <= 0:
            issues.append("Max cost per request must be positive")
        
        if issues:
            for issue in issues:
                logger.warning(f"AI configuration issue: {issue}")
    
    def get_model_for_task(self, task_type: TaskType, requirements: Optional[Dict[str, Any]] = None) -> str:
        """
        Get optimal model for a specific task.
        
        Args:
            task_type: Type of task
            requirements: Task requirements (cost_optimized, quality_optimized, etc.)
            
        Returns:
            Model name
        """
        requirements = requirements or {}
        
        # Task-specific model selection
        if task_type == TaskType.CONVERSATION:
            base_model = self.default_conversation_model
        elif task_type == TaskType.ANALYSIS:
            base_model = self.default_analysis_model
        elif task_type == TaskType.PERSONALITY:
            base_model = self.default_personality_model
        elif task_type == TaskType.EMBEDDING:
            base_model = self.default_embedding_model
        else:
            base_model = self.default_conversation_model
        
        # Apply requirements
        if requirements.get("cost_optimized", False):
            # Find cheapest model with required capabilities
            task_capability = task_type.value
            suitable_models = [
                name for name, config in self.model_configs.items()
                if task_capability in config.capabilities
            ]
            if suitable_models:
                base_model = min(suitable_models, key=lambda m: self.model_configs[m].cost_per_1k_tokens)
        
        elif requirements.get("quality_optimized", False):
            # Find highest quality model for task
            if task_type == TaskType.ANALYSIS:
                base_model = "claude-3-opus"
            elif task_type == TaskType.CONVERSATION:
                base_model = "gpt-4-turbo"
            elif task_type == TaskType.PERSONALITY:
                base_model = "claude-3-opus"
        
        elif requirements.get("speed_optimized", False):
            # Find fastest model for task
            if task_type == TaskType.CONVERSATION:
                base_model = "claude-3-haiku"
            elif task_type == TaskType.ANALYSIS:
                base_model = "gemini-pro"
        
        return base_model
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.model_configs.get(model_name)
    
    def get_available_models(self, capability: Optional[str] = None) -> List[str]:
        """
        Get list of available models, optionally filtered by capability.
        
        Args:
            capability: Required capability
            
        Returns:
            List of model names
        """
        if capability:
            return [
                name for name, config in self.model_configs.items()
                if capability in config.capabilities
            ]
        return list(self.model_configs.keys())
    
    def estimate_cost(self, model_name: str, token_count: int) -> float:
        """
        Estimate cost for a request.
        
        Args:
            model_name: Model name
            token_count: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        config = self.get_model_config(model_name)
        if not config:
            return 0.0
        
        return (token_count / 1000) * config.cost_per_1k_tokens
    
    def get_provider_config(self, provider: AIProvider) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        configs = {
            AIProvider.OPENAI: {
                "api_key": self.openai_api_key,
                "base_url": "https://api.openai.com/v1",
                "timeout": self.request_timeout,
                "max_retries": self.retry_attempts
            },
            AIProvider.ANTHROPIC: {
                "api_key": self.anthropic_api_key,
                "base_url": "https://api.anthropic.com",
                "timeout": self.request_timeout,
                "max_retries": self.retry_attempts
            },
            AIProvider.GOOGLE: {
                "api_key": self.google_api_key,
                "timeout": self.request_timeout,
                "max_retries": self.retry_attempts
            }
        }
        
        return configs.get(provider, {})
    
    def get_openrouter_config(self) -> Dict[str, Any]:
        """Get OpenRouter configuration"""
        return {
            "api_key": self.openrouter_api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": self.request_timeout,
            "max_retries": self.retry_attempts,
            "cost_optimization": self.cost_optimization_enabled,
            "max_cost_per_request": self.max_cost_per_request
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "caching_enabled": self.response_caching_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_size_limit": self.cache_size_limit
        }


def create_ai_config(**kwargs) -> AIConfig:
    """
    Create AI configuration from keyword arguments.
    
    Args:
        **kwargs: AI configuration parameters
        
    Returns:
        AIConfig instance
    """
    return AIConfig(**kwargs)
