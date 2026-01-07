"""
Response Generator for the Digital Twin's Conversation Engine.

This module provides functionality for generating responses based on user messages,
conversation context, memories, and personality profile.
"""

import logging
import json
from typing import Dict, Any, List, Optional
import os
import sys

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generator for conversation responses.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the response generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.llm_provider = self.config.get("llm_provider", "openai")
        self.llm_model = self.config.get("llm_model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 500)
        self.langchain_client = None
        self._initialize_langchain()
        logger.info("Response Generator initialized")

    def _initialize_langchain(self) -> None:
        """
        Initialize LangChain for LLM integration.
        """
        try:
            # Try to import LangChain
            import langchain
            from langchain.llms import OpenAI
            from langchain.chat_models import ChatOpenAI
            from langchain.prompts import PromptTemplate
            from langchain.chains import LLMChain
            
            # Check if API key is available
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found in environment variables")
                self.langchain_client = None
                return
                
            # Initialize LangChain client
            if self.llm_provider == "openai":
                if self.llm_model.startswith("gpt-3.5") or self.llm_model.startswith("gpt-4"):
                    self.langchain_client = ChatOpenAI(
                        model_name=self.llm_model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                else:
                    self.langchain_client = OpenAI(
                        model_name=self.llm_model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    
                logger.info(f"LangChain initialized with {self.llm_provider} {self.llm_model}")
            else:
                logger.warning(f"Unsupported LLM provider: {self.llm_provider}")
                self.langchain_client = None
                
        except ImportError:
            logger.warning("LangChain not available, using fallback response generation")
            self.langchain_client = None
        except Exception as e:
            logger.error(f"Error initializing LangChain: {str(e)}")
            self.langchain_client = None

    async def generate_response(self, message: str, context: Dict[str, Any], 
                              memories: List[Dict[str, Any]], profile: Dict[str, Any],
                              analysis: Dict[str, Any]) -> str:
        """
        Generate a response based on the user message and context.

        Args:
            message: User message
            context: Conversation context
            memories: Relevant memories
            profile: User personality profile
            analysis: Message analysis

        Returns:
            Generated response
        """
        # If LangChain is available, use it
        if self.langchain_client:
            try:
                return await self._generate_with_langchain(message, context, memories, profile, analysis)
            except Exception as e:
                logger.error(f"Error generating response with LangChain: {str(e)}")
                logger.warning("Falling back to rule-based response generation")
                
        # Use fallback rule-based response generation
        return await self._generate_rule_based(message, context, memories, profile, analysis)

    async def _generate_with_langchain(self, message: str, context: Dict[str, Any],
                                     memories: List[Dict[str, Any]], profile: Dict[str, Any],
                                     analysis: Dict[str, Any]) -> str:
        """
        Generate a response using LangChain.

        Args:
            message: User message
            context: Conversation context
            memories: Relevant memories
            profile: User personality profile
            analysis: Message analysis

        Returns:
            Generated response
        """
        # This is a placeholder implementation
        # In a real implementation, this would use LangChain to generate a response
        
        # Create prompt
        prompt = self._create_prompt(message, context, memories, profile, analysis)
        
        # Generate response
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        prompt_template = PromptTemplate(
            input_variables=["prompt"],
            template="{prompt}"
        )
        
        chain = LLMChain(llm=self.langchain_client, prompt=prompt_template)
        response = chain.run(prompt=prompt)
        
        logger.debug("Generated response using LangChain")
        return response

    async def _generate_rule_based(self, message: str, context: Dict[str, Any],
                                 memories: List[Dict[str, Any]], profile: Dict[str, Any],
                                 analysis: Dict[str, Any]) -> str:
        """
        Generate a response using rule-based methods.

        Args:
            message: User message
            context: Conversation context
            memories: Relevant memories
            profile: User personality profile
            analysis: Message analysis

        Returns:
            Generated response
        """
        # This is a simplified implementation
        # In a real implementation, this would use more sophisticated rules
        
        # Get intent
        intent = analysis.get("intent", "")
        
        # Get conversation state
        conversation_state = context.get("conversation_state", "greeting")
        
        # Get sentiment
        sentiment = analysis.get("sentiment", "neutral")
        
        # Generate response based on intent and state
        if conversation_state == "greeting":
            return self._generate_greeting(message, profile)
        elif conversation_state == "ending":
            return self._generate_farewell(message, profile)
        elif conversation_state == "helping":
            return self._generate_help_response(message, profile)
        elif conversation_state == "de-escalating":
            return self._generate_de_escalation(message, profile, sentiment)
        elif intent == "question":
            return await self._generate_question_response(message, memories, profile)
        elif intent == "statement":
            return self._generate_statement_response(message, profile, sentiment)
        elif intent == "request":
            return self._generate_request_response(message, profile)
        else:
            return self._generate_default_response(message, profile)

    def _create_prompt(self, message: str, context: Dict[str, Any],
                      memories: List[Dict[str, Any]], profile: Dict[str, Any],
                      analysis: Dict[str, Any]) -> str:
        """
        Create a prompt for the language model.

        Args:
            message: User message
            context: Conversation context
            memories: Relevant memories
            profile: User personality profile
            analysis: Message analysis

        Returns:
            Prompt string
        """
        # Format the personality profile
        personality_str = json.dumps(profile.get("dimensions", {}), indent=2)
        communication_style_str = json.dumps(profile.get("communication_style", {}), indent=2)
        
        # Format the conversation context
        context_str = f"Current topic: {context.get('current_topic', 'None')}\n"
        context_str += f"Conversation state: {context.get('conversation_state', 'ongoing')}\n"
        context_str += f"Turn count: {context.get('turn_count', 0)}\n"
        
        # Format the message analysis
        analysis_str = f"Intent: {analysis.get('intent', 'None')}\n"
        analysis_str += f"Sentiment: {analysis.get('sentiment', 'neutral')}\n"
        analysis_str += f"Topics: {', '.join(analysis.get('topics', ['None']))}\n"
        analysis_str += f"Entities: {', '.join(analysis.get('entities', ['None']))}\n"
        
        # Format the relevant memories
        memories_str = ""
        if memories:
            memories_str = "Relevant memories:\n"
            for i, memory in enumerate(memories[:3]):  # Limit to 3 memories
                memory_type = memory.get("memory_type", "unknown")
                if memory_type == "episodic":
                    memories_str += f"Memory {i+1} (Episodic): {memory.get('title', 'No title')} - {memory.get('description', 'No description')}\n"
                elif memory_type == "semantic":
                    memories_str += f"Memory {i+1} (Semantic): {memory.get('concept', 'No concept')} - {memory.get('information', 'No information')}\n"
                elif memory_type == "procedural":
                    memories_str += f"Memory {i+1} (Procedural): {memory.get('task', 'No task')}\n"
        else:
            memories_str = "No relevant memories found.\n"
            
        # Create the full prompt
        prompt = f"""
        You are a digital twin assistant with a specific personality profile and communication style.
        
        Personality Profile:
        {personality_str}
        
        Communication Style:
        {communication_style_str}
        
        Conversation Context:
        {context_str}
        
        Message Analysis:
        {analysis_str}
        
        {memories_str}
        
        User message: "{message}"
        
        Generate a response that is consistent with the personality profile and communication style,
        takes into account the conversation context, and incorporates relevant memories when appropriate.
        The response should be natural, helpful, and engaging.
        
        Response:
        """
        
        return prompt

    def _generate_greeting(self, message: str, profile: Dict[str, Any]) -> str:
        """
        Generate a greeting response.

        Args:
            message: User message
            profile: User personality profile

        Returns:
            Greeting response
        """
        # Get communication style
        formality = profile.get("communication_style", {}).get("formality", 0.5)
        verbosity = profile.get("communication_style", {}).get("verbosity", 0.5)
        
        # Generate greeting based on formality and verbosity
        if formality > 0.7:
            if verbosity > 0.7:
                return "Hello! It's a pleasure to speak with you. How may I assist you today?"
            else:
                return "Hello. How may I assist you?"
        else:
            if verbosity > 0.7:
                return "Hi there! Great to chat with you. What can I help you with today?"
            else:
                return "Hi! What can I help with?"

    def _generate_farewell(self, message: str, profile: Dict[str, Any]) -> str:
        """
        Generate a farewell response.

        Args:
            message: User message
            profile: User personality profile

        Returns:
            Farewell response
        """
        # Get communication style
        formality = profile.get("communication_style", {}).get("formality", 0.5)
        verbosity = profile.get("communication_style", {}).get("verbosity", 0.5)
        
        # Generate farewell based on formality and verbosity
        if formality > 0.7:
            if verbosity > 0.7:
                return "Thank you for the conversation. It was a pleasure assisting you. Have a wonderful day!"
            else:
                return "Thank you. Have a good day."
        else:
            if verbosity > 0.7:
                return "Thanks for chatting! Let me know if you need anything else. Take care!"
            else:
                return "Bye! Talk to you later!"

    def _generate_help_response(self, message: str, profile: Dict[str, Any]) -> str:
        """
        Generate a help response.

        Args:
            message: User message
            profile: User personality profile

        Returns:
            Help response
        """
        # Get communication style
        formality = profile.get("communication_style", {}).get("formality", 0.5)
        verbosity = profile.get("communication_style", {}).get("verbosity", 0.5)
        
        # Generate help response based on formality and verbosity
        if verbosity > 0.7:
            return "I'm your digital twin assistant. I can help you with conversations, answer questions based on your data, and provide personalized assistance. What would you like to know or discuss?"
        else:
            return "I'm your digital twin assistant. I can help with questions, conversations, and personalized assistance. What do you need?"

    def _generate_de_escalation(self, message: str, profile: Dict[str, Any], sentiment: str) -> str:
        """
        Generate a de-escalation response.

        Args:
            message: User message
            profile: User personality profile
            sentiment: Message sentiment

        Returns:
            De-escalation response
        """
        # Get communication style
        formality = profile.get("communication_style", {}).get("formality", 0.5)
        emotionality = profile.get("communication_style", {}).get("emotionality", 0.5)
        
        # Generate de-escalation response based on formality and emotionality
        if formality > 0.7:
            if emotionality > 0.7:
                return "I understand this may be frustrating. I'm here to help resolve this situation. Could you please tell me more about your concerns so I can assist you better?"
            else:
                return "I apologize for any inconvenience. How can I better assist you with your request?"
        else:
            if emotionality > 0.7:
                return "I can see you're upset, and that's totally valid. Let's figure this out together. What's bothering you the most right now?"
            else:
                return "Sorry about that. Let's try a different approach. What do you need help with?"

    async def _generate_question_response(self, message: str, memories: List[Dict[str, Any]], profile: Dict[str, Any]) -> str:
        """
        Generate a response to a question.

        Args:
            message: User message
            memories: Relevant memories
            profile: User personality profile

        Returns:
            Question response
        """
        # Check if there are relevant memories
        if memories:
            # Find the most relevant memory
            memory = memories[0]
            memory_type = memory.get("memory_type", "unknown")
            
            # Generate response based on memory type
            if memory_type == "episodic":
                return f"Based on your past experiences, {memory.get('description', 'I have some information that might help.')} Does that help answer your question?"
            elif memory_type == "semantic":
                return f"According to what I know, {memory.get('information', 'I have some information that might help.')} Is there anything else you'd like to know about this?"
            elif memory_type == "procedural":
                return f"I know how to {memory.get('task', 'do that')}. Would you like me to explain the steps?"
            else:
                return "I have some information that might help answer your question. Would you like me to share it?"
        else:
            # No relevant memories
            return "I don't have specific information about that. Would you like me to learn more about this topic?"

    def _generate_statement_response(self, message: str, profile: Dict[str, Any], sentiment: str) -> str:
        """
        Generate a response to a statement.

        Args:
            message: User message
            profile: User personality profile
            sentiment: Message sentiment

        Returns:
            Statement response
        """
        # Get communication style
        emotionality = profile.get("communication_style", {}).get("emotionality", 0.5)
        
        # Generate response based on sentiment and emotionality
        if sentiment == "positive":
            if emotionality > 0.7:
                return "That's wonderful to hear! I'm really glad about that. Would you like to tell me more?"
            else:
                return "That's good to know. Is there anything else you'd like to discuss?"
        elif sentiment == "negative":
            if emotionality > 0.7:
                return "I'm sorry to hear that. It sounds challenging. Would you like to talk more about it?"
            else:
                return "I understand. Is there anything I can help with regarding this situation?"
        else:
            return "I see. Would you like to elaborate on that?"

    def _generate_request_response(self, message: str, profile: Dict[str, Any]) -> str:
        """
        Generate a response to a request.

        Args:
            message: User message
            profile: User personality profile

        Returns:
            Request response
        """
        # Get communication style
        assertiveness = profile.get("communication_style", {}).get("assertiveness", 0.5)
        
        # Generate response based on assertiveness
        if assertiveness > 0.7:
            return "I'll help you with that right away. What specific details do you need?"
        else:
            return "I'd be happy to help with that. Could you provide a bit more information about what you need?"

    def _generate_default_response(self, message: str, profile: Dict[str, Any]) -> str:
        """
        Generate a default response when no specific type is determined.

        Args:
            message: User message
            profile: User personality profile

        Returns:
            Default response
        """
        # Get communication style
        verbosity = profile.get("communication_style", {}).get("verbosity", 0.5)
        
        # Generate default response based on verbosity
        if verbosity > 0.7:
            return "That's an interesting point. I'd like to understand more about what you're thinking. Could you elaborate on that?"
        else:
            return "Interesting. Can you tell me more?"