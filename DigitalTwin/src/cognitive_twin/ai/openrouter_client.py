"""
OpenRouter Client for Multi-Provider AI Access

Provides unified interface to GPT-4, Claude, and Google AI models
through OpenRouter's API for optimal model selection and cost efficiency.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """AI model providers available through OpenRouter"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"

@dataclass
class ModelConfig:
    """Configuration for AI models"""
    name: str
    provider: ModelProvider
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float
    capabilities: List[str]

class OpenRouterClient:
    """
    Unified client for accessing multiple AI providers through OpenRouter.
    
    Automatically selects optimal model based on task requirements and cost.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter. Get your key at https://openrouter.ai/keys"
            )
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None
        
        # Model configurations
        self.models = {
            # OpenAI Models
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                provider=ModelProvider.OPENAI,
                max_tokens=128000,
                temperature=0.7,
                cost_per_1k_tokens=0.01,
                capabilities=["conversation", "reasoning", "analysis", "code"]
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider=ModelProvider.OPENAI,
                max_tokens=8192,
                temperature=0.7,
                cost_per_1k_tokens=0.03,
                capabilities=["conversation", "reasoning", "analysis"]
            ),
            
            # Anthropic Models
            "claude-3-opus": ModelConfig(
                name="claude-3-opus",
                provider=ModelProvider.ANTHROPIC,
                max_tokens=200000,
                temperature=0.7,
                cost_per_1k_tokens=0.015,
                capabilities=["analysis", "reasoning", "safety", "long_context"]
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet", 
                provider=ModelProvider.ANTHROPIC,
                max_tokens=200000,
                temperature=0.7,
                cost_per_1k_tokens=0.003,
                capabilities=["conversation", "analysis", "reasoning"]
            ),
            
            # Google Models
            "gemini-pro": ModelConfig(
                name="gemini-pro",
                provider=ModelProvider.GOOGLE,
                max_tokens=32768,
                temperature=0.7,
                cost_per_1k_tokens=0.0005,
                capabilities=["multimodal", "embeddings", "analysis"]
            ),
            "gemini-pro-vision": ModelConfig(
                name="gemini-pro-vision",
                provider=ModelProvider.GOOGLE,
                max_tokens=16384,
                temperature=0.7,
                cost_per_1k_tokens=0.0005,
                capabilities=["multimodal", "vision", "analysis"]
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_optimal_model(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """
        Select optimal model based on task requirements.
        
        Args:
            task_type: Type of task (conversation, analysis, reasoning, etc.)
            requirements: Task requirements (max_tokens, cost_limit, etc.)
            
        Returns:
            Optimal model name
        """
        # Filter models by capabilities
        suitable_models = [
            model for model, config in self.models.items()
            if task_type in config.capabilities
        ]
        
        if not suitable_models:
            # Fallback to general purpose models
            suitable_models = ["gpt-4-turbo", "claude-3-sonnet", "gemini-pro"]
        
        # Select based on requirements
        if requirements.get("cost_optimized", False):
            # Choose cheapest suitable model
            return min(suitable_models, key=lambda m: self.models[m].cost_per_1k_tokens)
        elif requirements.get("quality_optimized", False):
            # Choose highest capability model
            return "claude-3-opus" if "claude-3-opus" in suitable_models else "gpt-4-turbo"
        elif requirements.get("speed_optimized", False):
            # Choose fastest model (usually smaller)
            return "gemini-pro" if "gemini-pro" in suitable_models else "gpt-4"
        else:
            # Balanced selection
            return "claude-3-sonnet" if "claude-3-sonnet" in suitable_models else "gpt-4-turbo"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        task_type: str = "conversation",
        requirements: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion using optimal model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Specific model to use (if None, will auto-select)
            task_type: Type of task for model selection
            requirements: Task requirements for model selection
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response dictionary with content and metadata
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Select model if not specified
        if not model:
            requirements = requirements or {}
            model = self.get_optimal_model(task_type, requirements)
        
        # Get model config
        model_config = self.models.get(model)
        if not model_config:
            raise ValueError(f"Unknown model: {model}")
        
        # Prepare request
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", model_config.temperature),
            "max_tokens": kwargs.get("max_tokens", model_config.max_tokens),
            "stream": kwargs.get("stream", False)
        }
        
        # Add provider-specific parameters
        if model_config.provider == ModelProvider.ANTHROPIC:
            request_data["stop"] = kwargs.get("stop", ["Human:", "Assistant:"])
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cognitive-twin.ai",
            "X-Title": "Cognitive-Twin AI System"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Add metadata
                result["model_used"] = model
                result["provider"] = model_config.provider.value
                result["cost_estimate"] = self._estimate_cost(result, model_config)
                
                return result
                
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    async def embeddings(
        self,
        text: Union[str, List[str]],
        model: str = "text-embedding-3-large"
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text or list of texts to embed
            model: Embedding model to use
            
        Returns:
            Embeddings response
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Convert single text to list
        if isinstance(text, str):
            text = [text]
        
        request_data = {
            "model": model,
            "input": text
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/embeddings",
                json=request_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                
                return await response.json()
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _estimate_cost(self, response: Dict[str, Any], model_config: ModelConfig) -> float:
        """Estimate cost of API call"""
        usage = response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        return (total_tokens / 1000) * model_config.cost_per_1k_tokens
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health and available models"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            async with self.session.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status == 200:
                    models_data = await response.json()
                    return {
                        "status": "healthy",
                        "available_models": len(models_data.get("data", [])),
                        "models": models_data.get("data", [])[:10]  # First 10 models
                    }
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Convenience functions for common tasks
async def get_conversation_ai(api_key: Optional[str] = None) -> 'ConversationAI':
    """Get conversation AI instance"""
    from .conversation_ai import ConversationAI
    return ConversationAI(api_key)

async def get_personality_ai(api_key: Optional[str] = None) -> 'PersonalityAI':
    """Get personality AI instance"""
    from .personality_ai import PersonalityAI
    return PersonalityAI(api_key)

async def get_analysis_ai(api_key: Optional[str] = None) -> 'AnalysisAI':
    """Get analysis AI instance"""
    from .analysis_ai import AnalysisAI
    return AnalysisAI(api_key)
