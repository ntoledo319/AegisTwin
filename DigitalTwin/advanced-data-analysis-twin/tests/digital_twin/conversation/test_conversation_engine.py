"""
Tests for the ConversationEngine.

This module contains tests for the ConversationEngine class and its components.
"""

import pytest
from typing import Dict, Any
import asyncio

# Import the ConversationEngine
from digital_twin import ConversationEngine


class TestConversationEngine:
    """
    Tests for the ConversationEngine class.
    """

    def test_initialization(self, conversation_engine, personality_engine, memory_system):
        """
        Test that the ConversationEngine initializes correctly.
        """
        assert conversation_engine is not None
        assert conversation_engine.personality_engine is personality_engine
        assert conversation_engine.memory_system is memory_system
        assert conversation_engine.context_manager is not None
        assert conversation_engine.response_generator is not None
        assert conversation_engine.conversation_analyzer is not None

    @pytest.mark.asyncio
    async def test_process_message(self, conversation_engine):
        """
        Test processing a message.
        """
        user_id = "test_user_123"
        message = "Tell me about hiking trails in the Rocky Mountains."
        context = {}
        
        # Process message
        response = await conversation_engine.process_message(user_id, message, context)
        
        # Check response
        assert response is not None
        assert isinstance(response, dict)
        assert "response" in response
        assert isinstance(response["response"], str)
        assert len(response["response"]) > 0
        assert "context" in response
        assert isinstance(response["context"], dict)
        assert "analysis" in response
        assert isinstance(response["analysis"], dict)

    @pytest.mark.asyncio
    async def test_start_conversation(self, conversation_engine):
        """
        Test starting a conversation.
        """
        user_id = "test_user_123"
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id)
        
        # Check context
        assert context is not None
        assert isinstance(context, dict)
        assert "conversation_id" in context
        assert "start_time" in context
        assert "turn_count" in context
        assert context["turn_count"] == 0
        assert "conversation_state" in context
        assert context["conversation_state"] == "greeting"

    @pytest.mark.asyncio
    async def test_end_conversation(self, conversation_engine):
        """
        Test ending a conversation.
        """
        user_id = "test_user_123"
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id)
        
        # End conversation
        result = await conversation_engine.end_conversation(user_id, context)
        
        # Check result
        assert result is not None
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "ended"
        assert "end_time" in result

    @pytest.mark.asyncio
    async def test_conversation_flow(self, conversation_engine):
        """
        Test a complete conversation flow.
        """
        user_id = "test_user_123"
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id)
        
        # First message
        message1 = "Hello, how are you?"
        response1 = await conversation_engine.process_message(user_id, message1, context)
        
        # Check response
        assert response1 is not None
        assert "response" in response1
        assert "context" in response1
        
        # Update context
        context = response1["context"]
        
        # Second message
        message2 = "I'm interested in hiking. Can you recommend some trails?"
        response2 = await conversation_engine.process_message(user_id, message2, context)
        
        # Check response
        assert response2 is not None
        assert "response" in response2
        assert "context" in response2
        
        # Update context
        context = response2["context"]
        
        # Check that turn count has increased
        assert "turn_count" in context
        assert context["turn_count"] > 1
        
        # End conversation
        result = await conversation_engine.end_conversation(user_id, context)
        
        # Check result
        assert result is not None
        assert "status" in result
        assert result["status"] == "ended"

    @pytest.mark.asyncio
    async def test_context_management(self, conversation_engine):
        """
        Test context management in conversation.
        """
        user_id = "test_user_123"
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id)
        
        # First message about hiking
        message1 = "I love hiking in the mountains."
        response1 = await conversation_engine.process_message(user_id, message1, context)
        
        # Update context
        context = response1["context"]
        
        # Check that context contains topic information
        assert "current_topic" in context
        
        # Second message continuing the topic
        message2 = "What's your favorite trail?"
        response2 = await conversation_engine.process_message(user_id, message2, context)
        
        # Update context
        context = response2["context"]
        
        # Check that context maintains topic continuity
        assert "current_topic" in context
        assert "previous_topics" in context
        
        # Third message changing the topic
        message3 = "Let's talk about books instead. Have you read any good science fiction lately?"
        response3 = await conversation_engine.process_message(user_id, message3, context)
        
        # Update context
        context = response3["context"]
        
        # Check that topic has changed
        assert "current_topic" in context
        assert "previous_topics" in context
        assert len(context["previous_topics"]) > 0

    @pytest.mark.asyncio
    async def test_memory_integration(self, conversation_engine, memory_system, sample_memory_content):
        """
        Test integration with memory system.
        """
        user_id = "test_user_123"
        
        # Store a memory
        await memory_system.store_memory(user_id, "episodic", sample_memory_content)
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id)
        
        # Message related to the memory
        message = "Tell me about my hiking experiences in the Rocky Mountains."
        response = await conversation_engine.process_message(user_id, message, context)
        
        # Check response
        assert response is not None
        assert "response" in response
        assert isinstance(response["response"], str)
        assert len(response["response"]) > 0