"""
Conversation AI Module

Provides intelligent conversation capabilities using multiple AI providers
through OpenRouter, with personality-aware responses and context management.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from .openrouter_client import OpenRouterClient, ModelProvider

logger = logging.getLogger(__name__)

class ConversationAI:
    """
    Intelligent conversation system with personality awareness and context management.
    
    Uses optimal AI models for different conversation types and maintains
    personality-consistent responses.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize conversation AI.
        
        Args:
            api_key: OpenRouter API key
        """
        self.client = OpenRouterClient(api_key)
        self.conversation_history = {}
        self.personality_profiles = {}
        
    async def generate_response(
        self,
        message: str,
        user_id: str,
        personality_profile: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        response_style: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Generate intelligent response to user message.
        
        Args:
            message: User's message
            user_id: Unique user identifier
            personality_profile: User's personality traits
            conversation_context: Additional context
            response_style: Style of response (balanced, analytical, creative, empathetic)
            
        Returns:
            Response dictionary with text and metadata
        """
        async with self.client as client:
            # Get or create conversation history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Build system prompt with personality
            system_prompt = self._build_system_prompt(
                personality_profile, 
                conversation_context,
                response_style
            )
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add recent conversation history (last 10 exchanges)
            recent_history = self.conversation_history[user_id][-10:]
            for exchange in recent_history:
                messages.append({"role": "user", "content": exchange["user_message"]})
                messages.append({"role": "assistant", "content": exchange["assistant_response"]})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Select optimal model for conversation
            model = self._select_conversation_model(response_style, personality_profile)
            
            try:
                # Generate response
                response = await client.chat_completion(
                    messages=messages,
                    model=model,
                    task_type="conversation",
                    requirements={
                        "quality_optimized": response_style in ["analytical", "creative"],
                        "cost_optimized": response_style == "balanced"
                    }
                )
                
                # Extract response content
                response_text = response["choices"][0]["message"]["content"]
                
                # Store in conversation history
                self.conversation_history[user_id].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_message": message,
                    "assistant_response": response_text,
                    "model_used": response["model_used"],
                    "context": conversation_context
                })
                
                # Analyze response characteristics
                response_analysis = await self._analyze_response(response_text, personality_profile)
                
                return {
                    "text": response_text,
                    "metadata": {
                        "model_used": response["model_used"],
                        "provider": response["provider"],
                        "cost_estimate": response["cost_estimate"],
                        "response_style": response_style,
                        "personality_applied": personality_profile is not None,
                        "context_used": conversation_context is not None,
                        "response_analysis": response_analysis,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error generating conversation response: {str(e)}")
                # Fallback response
                return {
                    "text": "I apologize, but I'm having trouble processing your message right now. Could you please try again?",
                    "metadata": {
                        "error": str(e),
                        "fallback": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
    
    def _build_system_prompt(
        self,
        personality_profile: Optional[Dict[str, Any]],
        conversation_context: Optional[Dict[str, Any]],
        response_style: str
    ) -> str:
        """Build system prompt with personality and context"""
        
        base_prompt = """You are a sophisticated digital twin AI assistant. You have deep understanding of human psychology, communication patterns, and can provide insightful, personalized responses."""
        
        # Add personality awareness
        if personality_profile:
            traits = personality_profile.get("big_five", {})
            communication_style = personality_profile.get("communication_style", {})
            
            personality_instruction = f"""
            
PERSONALITY PROFILE:
- Openness: {traits.get('openness', 0.5):.2f} (0=conventional, 1=creative)
- Conscientiousness: {traits.get('conscientiousness', 0.5):.2f} (0=flexible, 1=organized)
- Extraversion: {traits.get('extraversion', 0.5):.2f} (0=introverted, 1=outgoing)
- Agreeableness: {traits.get('agreeableness', 0.5):.2f} (0=competitive, 1=cooperative)
- Neuroticism: {traits.get('neuroticism', 0.5):.2f} (0=calm, 1=anxious)

COMMUNICATION STYLE:
- Assertiveness: {communication_style.get('assertiveness', 0.5):.2f}
- Emotionality: {communication_style.get('emotionality', 0.5):.2f}
- Formality: {communication_style.get('formality', 0.5):.2f}

Adapt your responses to match this personality profile. Be consistent with these traits in your communication style."""
        
        else:
            personality_instruction = "\n\nYou should be warm, professional, and insightful in your responses."
        
        # Add response style
        style_instructions = {
            "balanced": "Provide balanced, thoughtful responses that consider multiple perspectives.",
            "analytical": "Focus on logical analysis, data-driven insights, and systematic thinking.",
            "creative": "Be imaginative, explore unconventional ideas, and think outside the box.",
            "empathetic": "Prioritize emotional understanding, validation, and supportive communication."
        }
        
        style_instruction = style_instructions.get(response_style, style_instructions["balanced"])
        
        # Add context awareness
        context_instruction = ""
        if conversation_context:
            context_instruction = f"""
            
CURRENT CONTEXT:
{json.dumps(conversation_context, indent=2)}

Use this context to provide more relevant and personalized responses."""
        
        return f"{base_prompt}{personality_instruction}\n\nRESPONSE STYLE: {style_instruction}{context_instruction}"
    
    def _select_conversation_model(
        self, 
        response_style: str, 
        personality_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Select optimal model for conversation type"""
        
        if response_style == "analytical":
            return "claude-3-opus"  # Best for reasoning
        elif response_style == "creative":
            return "gpt-4-turbo"  # Best for creativity
        elif personality_profile and personality_profile.get("complexity", 0) > 0.7:
            return "claude-3-sonnet"  # Good balance for complex personalities
        else:
            return "gemini-pro"  # Cost-effective for general conversation
    
    async def _analyze_response(
        self, 
        response_text: str, 
        personality_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze response characteristics"""
        
        analysis = {
            "length": len(response_text),
            "sentiment": "neutral",  # Could add sentiment analysis here
            "complexity": len(response_text.split()) / max(len(response_text.split('.')) - 1, 1),
            "personality_consistency": 0.8  # Placeholder
        }
        
        # Check personality consistency if profile exists
        if personality_profile:
            # Simple consistency check based on response length vs personality
            expected_length = personality_profile.get("communication_style", {}).get("verbosity", 0.5)
            actual_length = min(len(response_text) / 500, 1.0)  # Normalize to 0-1
            
            analysis["personality_consistency"] = 1.0 - abs(expected_length - actual_length)
        
        return analysis
    
    async def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of conversation history"""
        if user_id not in self.conversation_history:
            return {"message": "No conversation history found"}
        
        history = self.conversation_history[user_id]
        
        return {
            "total_exchanges": len(history),
            "first_conversation": history[0]["timestamp"] if history else None,
            "last_conversation": history[-1]["timestamp"] if history else None,
            "models_used": list(set([h["model_used"] for h in history])),
            "recent_topics": self._extract_recent_topics(history[-5:]) if history else []
        }
    
    def _extract_recent_topics(self, recent_history: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from recent conversation"""
        # Simple keyword extraction - could be enhanced with NLP
        topics = []
        for exchange in recent_history:
            words = exchange["user_message"].lower().split()
            # Extract potential topics (simplified)
            for word in words:
                if len(word) > 4 and word not in ["that", "this", "with", "from", "they", "have", "been"]:
                    topics.append(word)
        
        # Return most common topics
        from collections import Counter
        return [topic for topic, count in Counter(topics).most_common(5)]
    
    async def clear_conversation_history(self, user_id: str) -> bool:
        """Clear conversation history for user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            return True
        return False
    
    async def export_conversation_history(self, user_id: str) -> Dict[str, Any]:
        """Export conversation history for analysis"""
        if user_id not in self.conversation_history:
            return {"error": "No conversation history found"}
        
        return {
            "user_id": user_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "conversation_history": self.conversation_history[user_id],
            "summary": await self.get_conversation_summary(user_id)
        }
