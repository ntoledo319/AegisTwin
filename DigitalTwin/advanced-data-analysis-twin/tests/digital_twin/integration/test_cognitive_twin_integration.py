"""
Integration tests for SpiderMind Omega adapters with Digital Twin core components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from digital_twin.personality.engine_enhanced import EnhancedPersonalityEngine
from digital_twin.memory.system_enhanced import EnhancedMemorySystem
from digital_twin.conversation.engine_enhanced import EnhancedConversationEngine


@pytest.fixture
def config():
    """Create a configuration dictionary for testing."""
    return {
        "ct_omega": {
            "enabled": True,
            "path": "../../../ct_omega"
        }
    }


@pytest.fixture
def enhanced_personality_engine(config):
    """Create an enhanced personality engine for testing."""
    return EnhancedPersonalityEngine(config)


@pytest.fixture
def enhanced_memory_system(config):
    """Create an enhanced memory system for testing."""
    return EnhancedMemorySystem(config)


@pytest.fixture
def enhanced_conversation_engine(enhanced_personality_engine, enhanced_memory_system, config):
    """Create an enhanced conversation engine for testing."""
    return EnhancedConversationEngine(enhanced_personality_engine, enhanced_memory_system, config)


@pytest.fixture
def sample_user_data():
    """Create sample user data for testing."""
    # Create timestamps
    now = datetime.now()
    user_data = {
        "communication": [],
        "activity": [],
        "mood": [],
        "social": []
    }
    
    # Generate data for each day
    for i in range(10):
        timestamp = (now - timedelta(days=10-i)).isoformat()
        
        # Communication data
        user_data["communication"].append({
            "timestamp": timestamp,
            "message_count": 10 + i,
            "response_time": 30 - i,
            "channels": 2
        })
        
        # Activity data
        user_data["activity"].append({
            "timestamp": timestamp,
            "activity_level": 0.5 + (i * 0.05),
            "duration": 45 + (i * 5),
            "type": "work" if i % 3 == 0 else "leisure"
        })
        
        # Mood data
        user_data["mood"].append({
            "timestamp": timestamp,
            "happiness": 0.6 + (i * 0.03),
            "energy": 0.5 + (i * 0.02),
            "stress": 0.4 - (i * 0.02)
        })
        
        # Social data
        user_data["social"].append({
            "timestamp": timestamp,
            "interactions": 3 + i,
            "quality": 0.7 + (i * 0.02),
            "duration": 60 + (i * 10)
        })
    
    return user_data


@pytest.fixture
def sample_traits():
    """Create sample personality traits for testing."""
    return {
        "openness": 0.8,
        "conscientiousness": 0.6,
        "extraversion": 0.7,
        "agreeableness": 0.9,
        "neuroticism": 0.3,
        "creativity": 0.8,
        "resilience": 0.7,
        "adaptability": 0.6,
        "empathy": 0.9,
        "curiosity": 0.8
    }


@pytest.mark.asyncio
async def test_enhanced_personality_engine_create_profile(enhanced_personality_engine, sample_traits):
    """Test creating an enhanced personality profile."""
    # Create profile
    profile = await enhanced_personality_engine.create_personality_profile("test_user", sample_traits)
    
    # Check that the profile has the expected fields
    assert "user_id" in profile
    assert "traits" in profile
    assert "dimensions" in profile
    assert "patterns" in profile
    assert "communication_style" in profile
    
    # Check that the enhanced fields are present
    assert "quantum_profile" in profile
    assert "enhanced_quantum_profile" in profile
    assert "consciousness_topology" in profile
    assert "knowledge_gaps" in profile
    
    # Check that the quantum profile has the expected structure
    assert "quantum_dimensions" in profile["quantum_profile"]
    assert "quantum_state" in profile["quantum_profile"]
    
    # Check that the enhanced quantum profile has the expected structure
    assert "superposition_states" in profile["enhanced_quantum_profile"]
    assert "entanglement_map" in profile["enhanced_quantum_profile"]
    
    # Check that the consciousness topology has the expected structure
    assert "regions" in profile["consciousness_topology"]
    assert "transitions" in profile["consciousness_topology"]
    
    # Check that knowledge gaps were detected
    assert isinstance(profile["knowledge_gaps"], list)


@pytest.mark.asyncio
async def test_enhanced_memory_system_store_retrieve(enhanced_memory_system):
    """Test storing and retrieving memories with enhanced capabilities."""
    # Create a memory
    memory_content = {
        "content": "Test memory content",
        "importance": 0.8,
        "emotional_valence": 0.6,
        "emotional_arousal": 0.7
    }
    
    # Store memory
    memory_id = await enhanced_memory_system.store_memory("test_user", "episodic", memory_content)
    
    # Check that the memory was stored
    assert memory_id is not None
    
    # Retrieve memory with context
    if hasattr(enhanced_memory_system, "retrieve_memory_with_context"):
        result = await enhanced_memory_system.retrieve_memory_with_context(
            "test_user", 
            {"memory_type": "episodic"}, 
            limit=10
        )
        
        # Check that the result has the expected structure
        assert "memories" in result
        assert "context" in result
        assert len(result["memories"]) > 0
        assert result["memories"][0]["memory_id"] == memory_id
    else:
        # Fallback to standard retrieval
        memories = await enhanced_memory_system.retrieve_memory(
            "test_user", 
            {"memory_type": "episodic"}, 
            limit=10
        )
        
        # Check that the memory was retrieved
        assert len(memories) > 0
        assert memories[0]["memory_id"] == memory_id


@pytest.mark.asyncio
async def test_enhanced_conversation_engine_process_message(enhanced_conversation_engine):
    """Test processing a message with enhanced capabilities."""
    # Start a conversation
    context = await enhanced_conversation_engine.start_conversation("test_user")
    
    # Process a message
    result = await enhanced_conversation_engine.process_message(
        "test_user", 
        "Hello, how are you today?", 
        context
    )
    
    # Check that the result has the expected structure
    assert "response" in result
    assert "context" in result
    assert "analysis" in result
    
    # Check that the enhanced fields are present
    assert "consciousness_topology" in result
    assert "understanding_gaps" in result
    assert "conversation_trajectory" in result
    
    # Check that the consciousness topology has the expected structure
    assert "regions" in result["consciousness_topology"]
    assert "transitions" in result["consciousness_topology"]
    
    # Check that understanding gaps were detected
    assert "detected_voids" in result["understanding_gaps"]
    
    # Check that a conversation trajectory was predicted
    assert "predicted_states" in result["conversation_trajectory"]


@pytest.mark.asyncio
async def test_integration_personality_memory(enhanced_personality_engine, enhanced_memory_system, sample_user_data, sample_traits):
    """Test integration between enhanced personality engine and memory system."""
    # Create personality profile
    profile = await enhanced_personality_engine.create_personality_profile("test_user", sample_traits)
    
    # Store profile in memory
    memory_id = await enhanced_memory_system.store_memory(
        "test_user", 
        "semantic", 
        {"type": "personality_profile", "profile": profile}
    )
    
    # Retrieve profile from memory
    memories = await enhanced_memory_system.retrieve_memory(
        "test_user", 
        {"type": "personality_profile"}, 
        limit=1
    )
    
    # Check that the profile was retrieved
    assert len(memories) > 0
    assert "profile" in memories[0]["content"]
    retrieved_profile = memories[0]["content"]["profile"]
    
    # Check that the retrieved profile has the same structure
    assert "quantum_profile" in retrieved_profile
    assert "enhanced_quantum_profile" in retrieved_profile
    assert "consciousness_topology" in retrieved_profile
    
    # Analyze personality structure
    structure_analysis = await enhanced_personality_engine.analyze_personality_structure(profile)
    
    # Check that the structure analysis has the expected fields
    assert "structure_analysis" in structure_analysis
    assert "emergent_properties" in structure_analysis
    
    # Detect personality gaps
    gap_analysis = await enhanced_personality_engine.detect_personality_gaps(profile, sample_user_data)
    
    # Check that the gap analysis has the expected fields
    assert "void_analysis" in gap_analysis
    assert "recovery_recommendations" in gap_analysis


@pytest.mark.asyncio
async def test_integration_memory_conversation(enhanced_memory_system, enhanced_conversation_engine):
    """Test integration between enhanced memory system and conversation engine."""
    # Store some memories
    for i in range(5):
        memory_content = {
            "content": f"Memory content {i}",
            "importance": 0.5 + (i * 0.1),
            "emotional_valence": 0.5 + (i * 0.05),
            "emotional_arousal": 0.5 + (i * 0.05)
        }
        
        await enhanced_memory_system.store_memory("test_user", "episodic", memory_content)
    
    # Start a conversation
    context = await enhanced_conversation_engine.start_conversation("test_user")
    
    # Process a message that should trigger memory retrieval
    result = await enhanced_conversation_engine.process_message(
        "test_user", 
        "Tell me about my memories", 
        context
    )
    
    # Check that the response was generated
    assert "response" in result
    assert isinstance(result["response"], str)
    
    # End the conversation
    await enhanced_conversation_engine.end_conversation("test_user", result["context"])
    
    # Check that a conversation memory was stored
    memories = await enhanced_memory_system.retrieve_memory(
        "test_user", 
        {"type": "conversation_summary"}, 
        limit=1
    )
    
    # Check that the conversation summary was stored
    assert len(memories) > 0
    assert "summary" in memories[0]["content"]


@pytest.mark.asyncio
async def test_integration_full_pipeline(enhanced_personality_engine, enhanced_memory_system, enhanced_conversation_engine, sample_traits, sample_user_data):
    """Test the full integration pipeline."""
    # Create personality profile
    profile = await enhanced_personality_engine.create_personality_profile("test_user", sample_traits)
    
    # Store profile in memory
    await enhanced_memory_system.store_memory(
        "test_user", 
        "semantic", 
        {"type": "personality_profile", "profile": profile}
    )
    
    # Store user data as memories
    for category, data_points in sample_user_data.items():
        for data_point in data_points:
            await enhanced_memory_system.store_memory(
                "test_user", 
                "episodic", 
                {"type": category, "data": data_point}
            )
    
    # Start a conversation
    context = await enhanced_conversation_engine.start_conversation("test_user")
    
    # Process a series of messages
    messages = [
        "Hello, how are you today?",
        "Tell me about my personality",
        "What patterns have you noticed in my behavior?",
        "What do you predict for my future mood?"
    ]
    
    for message in messages:
        result = await enhanced_conversation_engine.process_message(
            "test_user", 
            message, 
            context
        )
        
        # Update context for next message
        context = result["context"]
        
        # Check that the response was generated
        assert "response" in result
        assert isinstance(result["response"], str)
        
        # Check that enhanced data is present
        assert "consciousness_topology" in result
        assert "understanding_gaps" in result
        assert "conversation_trajectory" in result
    
    # End the conversation
    await enhanced_conversation_engine.end_conversation("test_user", context)
    
    # Check that a conversation summary was stored
    memories = await enhanced_memory_system.retrieve_memory(
        "test_user", 
        {"type": "conversation_summary"}, 
        limit=1
    )
    
    assert len(memories) > 0
    assert "summary" in memories[0]["content"]