"""
Unit tests for digital twin components.

This module provides unit tests for the digital twin components of the integrated system.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from digital_twin.personality import PersonalityManager
from digital_twin.memory import MemoryManager
from digital_twin.conversation import ConversationManager
from digital_twin.integration import IntegrationManager
from digital_twin import DigitalTwin

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def personality_manager():
    """Create a PersonalityManager instance for testing."""
    manager = PersonalityManager()
    return manager

@pytest.fixture
def memory_manager():
    """Create a MemoryManager instance for testing."""
    manager = MemoryManager()
    return manager

@pytest.fixture
def conversation_manager():
    """Create a ConversationManager instance for testing."""
    manager = ConversationManager()
    return manager

@pytest.fixture
def integration_manager(personality_manager, memory_manager, conversation_manager):
    """Create an IntegrationManager instance for testing."""
    manager = IntegrationManager(
        personality_manager=personality_manager,
        memory_manager=memory_manager,
        conversation_manager=conversation_manager
    )
    return manager

@pytest.fixture
def digital_twin():
    """Create a DigitalTwin instance for testing."""
    twin = DigitalTwin()
    return twin

class TestPersonalityManager:
    """Test cases for PersonalityManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, personality_manager):
        """Test that the manager initializes correctly."""
        assert hasattr(personality_manager, 'engine')
        assert hasattr(personality_manager, 'model')
        assert not personality_manager.initialized
        
        # Initialize
        await personality_manager.initialize()
        
        # Check initialized
        assert personality_manager.initialized
    
    @pytest.mark.asyncio
    async def test_analyze_personality(self, personality_manager):
        """Test the analyze_personality method."""
        # Initialize
        await personality_manager.initialize()
        
        # Mock the engine's analyze_personality method
        personality_manager.engine.analyze_personality = MagicMock(return_value=asyncio.Future())
        personality_manager.engine.analyze_personality.return_value.set_result({
            'openness': 0.7,
            'conscientiousness': 0.8,
            'extraversion': 0.6,
            'agreeableness': 0.9,
            'neuroticism': 0.3
        })
        
        # Mock the model's update method
        personality_manager.model.update = MagicMock(return_value=asyncio.Future())
        personality_manager.model.update.return_value.set_result(True)
        
        # Set model attributes
        personality_manager.model.traits = {
            'openness': 0.7,
            'conscientiousness': 0.8,
            'extraversion': 0.6,
            'agreeableness': 0.9,
            'neuroticism': 0.3
        }
        personality_manager.model.facets = {
            'openness': {
                'imagination': 0.7,
                'artistic_interests': 0.8
            }
        }
        personality_manager.model.values = {
            'achievement': 0.8,
            'benevolence': 0.9
        }
        personality_manager.model.interests = {
            'artistic': 0.7,
            'scientific': 0.8
        }
        
        # Analyze personality
        result = await personality_manager.analyze_personality({'messages': []})
        
        # Check result
        assert 'traits' in result
        assert 'facets' in result
        assert 'values' in result
        assert 'interests' in result
        
        assert result['traits']['openness'] == 0.7
        assert result['facets']['openness']['imagination'] == 0.7
        assert result['values']['achievement'] == 0.8
        assert result['interests']['artistic'] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_response(self, personality_manager):
        """Test the generate_response method."""
        # Initialize
        await personality_manager.initialize()
        
        # Mock the engine's generate_response method
        personality_manager.engine.generate_response = MagicMock(return_value=asyncio.Future())
        personality_manager.engine.generate_response.return_value.set_result({
            'text': 'Hello, how can I help you?',
            'confidence': 0.9,
            'personality_influence': 0.7
        })
        
        # Generate response
        result = await personality_manager.generate_response('Hello', {'session_id': 'test'})
        
        # Check result
        assert result['text'] == 'Hello, how can I help you?'
        assert result['confidence'] == 0.9
        assert result['personality_influence'] == 0.7
    
    @pytest.mark.asyncio
    async def test_adapt_personality(self, personality_manager):
        """Test the adapt_personality method."""
        # Initialize
        await personality_manager.initialize()
        
        # Mock the engine's adapt_personality method
        personality_manager.engine.adapt_personality = MagicMock(return_value=asyncio.Future())
        personality_manager.engine.adapt_personality.return_value.set_result({
            'previous_traits': {
                'openness': 0.7,
                'conscientiousness': 0.8
            },
            'current_traits': {
                'openness': 0.75,
                'conscientiousness': 0.85
            },
            'changes': {
                'openness': 0.05,
                'conscientiousness': 0.05
            }
        })
        
        # Mock the model's update method
        personality_manager.model.update = MagicMock(return_value=asyncio.Future())
        personality_manager.model.update.return_value.set_result(True)
        
        # Adapt personality
        result = await personality_manager.adapt_personality({'feedback': 'positive'})
        
        # Check result
        assert 'previous_traits' in result
        assert 'current_traits' in result
        assert 'changes' in result
        
        assert result['previous_traits']['openness'] == 0.7
        assert result['current_traits']['openness'] == 0.75
        assert result['changes']['openness'] == 0.05

class TestMemoryManager:
    """Test cases for MemoryManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, memory_manager):
        """Test that the manager initializes correctly."""
        assert hasattr(memory_manager, 'system')
        assert hasattr(memory_manager, 'model')
        assert not memory_manager.initialized
        
        # Initialize
        await memory_manager.initialize()
        
        # Check initialized
        assert memory_manager.initialized
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager):
        """Test the store_memory method."""
        # Initialize
        await memory_manager.initialize()
        
        # Mock the system's store_memory method
        memory_manager.system.store_memory = MagicMock(return_value=asyncio.Future())
        memory_manager.system.store_memory.return_value.set_result({
            'id': 'memory1',
            'content': 'Test memory',
            'type': 'episodic',
            'timestamp': '2023-01-01T10:00:00Z',
            'importance': 0.7
        })
        
        # Mock the model's register_memory method
        memory_manager.model.register_memory = MagicMock(return_value=asyncio.Future())
        memory_manager.model.register_memory.return_value.set_result({
            'memory_id': 'memory1',
            'strength': 0.7,
            'categories': ['personal']
        })
        
        # Store memory
        result = await memory_manager.store_memory(
            content='Test memory',
            memory_type='episodic',
            importance=0.7,
            metadata={'source': 'test'},
            categories=['personal']
        )
        
        # Check result
        assert 'memory' in result
        assert 'model' in result
        
        assert result['memory']['id'] == 'memory1'
        assert result['memory']['content'] == 'Test memory'
        assert result['memory']['type'] == 'episodic'
        assert result['memory']['importance'] == 0.7
        
        assert result['model']['memory_id'] == 'memory1'
        assert result['model']['strength'] == 0.7
        assert result['model']['categories'] == ['personal']
    
    @pytest.mark.asyncio
    async def test_retrieve_memory(self, memory_manager):
        """Test the retrieve_memory method."""
        # Initialize
        await memory_manager.initialize()
        
        # Mock the system's retrieve_memory method
        memory_manager.system.retrieve_memory = MagicMock(return_value=asyncio.Future())
        memory_manager.system.retrieve_memory.return_value.set_result({
            'id': 'memory1',
            'content': 'Test memory',
            'type': 'episodic',
            'timestamp': '2023-01-01T10:00:00Z',
            'importance': 0.7
        })
        
        # Mock the model's recall_memory method
        memory_manager.model.recall_memory = MagicMock(return_value=asyncio.Future())
        memory_manager.model.recall_memory.return_value.set_result({
            'memory_id': 'memory1',
            'strength': 0.8,
            'last_recalled': '2023-01-02T10:00:00Z',
            'recall_count': 2
        })
        
        # Retrieve memory
        result = await memory_manager.retrieve_memory('memory1')
        
        # Check result
        assert 'memory' in result
        assert 'model' in result
        
        assert result['memory']['id'] == 'memory1'
        assert result['memory']['content'] == 'Test memory'
        assert result['memory']['type'] == 'episodic'
        assert result['memory']['importance'] == 0.7
        
        assert result['model']['memory_id'] == 'memory1'
        assert result['model']['strength'] == 0.8
        assert result['model']['recall_count'] == 2
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_manager):
        """Test the search_memories method."""
        # Initialize
        await memory_manager.initialize()
        
        # Mock the system's search_memories method
        memory_manager.system.search_memories = MagicMock(return_value=asyncio.Future())
        memory_manager.system.search_memories.return_value.set_result([
            {
                'id': 'memory1',
                'content': 'Test memory 1',
                'type': 'episodic',
                'timestamp': '2023-01-01T10:00:00Z',
                'importance': 0.7
            },
            {
                'id': 'memory2',
                'content': 'Test memory 2',
                'type': 'episodic',
                'timestamp': '2023-01-02T10:00:00Z',
                'importance': 0.8
            }
        ])
        
        # Mock the model's get_memory_strength method
        memory_manager.model.get_memory_strength = MagicMock(return_value=asyncio.Future())
        memory_manager.model.get_memory_strength.return_value.set_result({
            'memory1': 0.7,
            'memory2': 0.8
        })
        
        # Search memories
        results = await memory_manager.search_memories('test', limit=10)
        
        # Check results
        assert len(results) == 2
        assert results[0]['id'] == 'memory1'
        assert results[0]['content'] == 'Test memory 1'
        assert results[0]['strength'] == 0.7
        assert results[1]['id'] == 'memory2'
        assert results[1]['content'] == 'Test memory 2'
        assert results[1]['strength'] == 0.8

class TestConversationManager:
    """Test cases for ConversationManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, conversation_manager):
        """Test that the manager initializes correctly."""
        assert hasattr(conversation_manager, 'engine')
        assert hasattr(conversation_manager, 'enhancer')
        assert not conversation_manager.initialized
        
        # Initialize
        await conversation_manager.initialize()
        
        # Check initialized
        assert conversation_manager.initialized
    
    @pytest.mark.asyncio
    async def test_process_message(self, conversation_manager):
        """Test the process_message method."""
        # Initialize
        await conversation_manager.initialize()
        
        # Mock the engine's process_message method
        conversation_manager.engine.process_message = MagicMock(return_value=asyncio.Future())
        conversation_manager.engine.process_message.return_value.set_result({
            'id': 'msg1',
            'text': 'Hello, how can I help you?',
            'timestamp': '2023-01-01T10:00:00Z',
            'metadata': {'source': 'engine'}
        })
        
        # Mock the engine's get_conversation_history method
        conversation_manager.engine.get_conversation_history = MagicMock(return_value=asyncio.Future())
        conversation_manager.engine.get_conversation_history.return_value.set_result([
            {
                'id': 'user_msg1',
                'text': 'Hello',
                'sender': 'user',
                'timestamp': '2023-01-01T09:59:00Z'
            },
            {
                'id': 'msg1',
                'text': 'Hello, how can I help you?',
                'sender': 'system',
                'timestamp': '2023-01-01T10:00:00Z'
            }
        ])
        
        # Mock the enhancer's enhance_response method
        conversation_manager.enhancer.enhance_response = MagicMock(return_value=asyncio.Future())
        conversation_manager.enhancer.enhance_response.return_value.set_result({
            'text': 'Hello! How can I assist you today?',
            'entities': ['greeting'],
            'topics': ['assistance'],
            'metrics': {'engagement': 0.8}
        })
        
        # Process message
        result = await conversation_manager.process_message(
            message='Hello',
            user_id='user1',
            metadata={'source': 'chat'},
            personality_profile={'traits': {'openness': 0.7}},
            memory_context={'recent_topics': ['project']}
        )
        
        # Check result
        assert 'text' in result
        assert 'entities' in result
        assert 'topics' in result
        assert 'metrics' in result
        assert 'metadata' in result
        
        assert result['text'] == 'Hello! How can I assist you today?'
        assert result['entities'] == ['greeting']
        assert result['topics'] == ['assistance']
        assert result['metrics']['engagement'] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, conversation_manager):
        """Test the get_conversation_history method."""
        # Initialize
        await conversation_manager.initialize()
        
        # Mock the engine's get_conversation_history method
        conversation_manager.engine.get_conversation_history = MagicMock(return_value=asyncio.Future())
        conversation_manager.engine.get_conversation_history.return_value.set_result([
            {
                'id': 'user_msg1',
                'text': 'Hello',
                'sender': 'user',
                'timestamp': '2023-01-01T09:59:00Z'
            },
            {
                'id': 'msg1',
                'text': 'Hello, how can I help you?',
                'sender': 'system',
                'timestamp': '2023-01-01T10:00:00Z'
            }
        ])
        
        # Get conversation history
        history = await conversation_manager.get_conversation_history(limit=10)
        
        # Check history
        assert len(history) == 2
        assert history[0]['id'] == 'user_msg1'
        assert history[0]['text'] == 'Hello'
        assert history[0]['sender'] == 'user'
        assert history[1]['id'] == 'msg1'
        assert history[1]['text'] == 'Hello, how can I help you?'
        assert history[1]['sender'] == 'system'

class TestIntegrationManager:
    """Test cases for IntegrationManager."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, integration_manager):
        """Test that the manager initializes correctly."""
        assert hasattr(integration_manager, 'personality_manager')
        assert hasattr(integration_manager, 'memory_manager')
        assert hasattr(integration_manager, 'conversation_manager')
        assert hasattr(integration_manager, 'cognitive_twin')
        assert hasattr(integration_manager, 'interface')
        assert not integration_manager.initialized
        
        # Mock the interface's initialize method
        integration_manager.interface.initialize = MagicMock(return_value=asyncio.Future())
        integration_manager.interface.initialize.return_value.set_result(True)
        
        # Initialize
        await integration_manager.initialize()
        
        # Check initialized
        assert integration_manager.initialized
    
    @pytest.mark.asyncio
    async def test_interact(self, integration_manager):
        """Test the interact method."""
        # Mock the interface's interact method
        integration_manager.interface.interact = MagicMock(return_value=asyncio.Future())
        integration_manager.interface.interact.return_value.set_result({
            'response': 'Hello! How can I assist you today?',
            'session_id': 'session1',
            'timestamp': '2023-01-01T10:00:00Z'
        })
        
        # Mock the initialized property
        integration_manager.initialized = True
        
        # Interact
        result = await integration_manager.interact(
            input_data='Hello',
            input_type='message',
            session_id='session1'
        )
        
        # Check result
        assert 'response' in result
        assert 'session_id' in result
        assert 'timestamp' in result
        
        assert result['response'] == 'Hello! How can I assist you today?'
        assert result['session_id'] == 'session1'
    
    @pytest.mark.asyncio
    async def test_create_session(self, integration_manager):
        """Test the create_session method."""
        # Mock the interface's create_session method
        integration_manager.interface.create_session = MagicMock(return_value=asyncio.Future())
        integration_manager.interface.create_session.return_value.set_result({
            'session_id': 'session1',
            'created_at': '2023-01-01T10:00:00Z',
            'status': 'active'
        })
        
        # Mock the initialized property
        integration_manager.initialized = True
        
        # Create session
        result = await integration_manager.create_session(
            session_id='session1',
            metadata={'user_id': 'user1'}
        )
        
        # Check result
        assert 'session_id' in result
        assert 'created_at' in result
        assert 'status' in result
        
        assert result['session_id'] == 'session1'
        assert result['status'] == 'active'

class TestDigitalTwin:
    """Test cases for DigitalTwin."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, digital_twin):
        """Test that the digital twin initializes correctly."""
        assert hasattr(digital_twin, 'personality_manager')
        assert hasattr(digital_twin, 'memory_manager')
        assert hasattr(digital_twin, 'conversation_manager')
        assert hasattr(digital_twin, 'integration_manager')
        assert not digital_twin.initialized
        
        # Mock the integration_manager's initialize method
        digital_twin.integration_manager.initialize = MagicMock(return_value=asyncio.Future())
        digital_twin.integration_manager.initialize.return_value.set_result(True)
        
        # Initialize
        await digital_twin.initialize()
        
        # Check initialized
        assert digital_twin.initialized
    
    @pytest.mark.asyncio
    async def test_interact(self, digital_twin):
        """Test the interact method."""
        # Mock the integration_manager's interact method
        digital_twin.integration_manager.interact = MagicMock(return_value=asyncio.Future())
        digital_twin.integration_manager.interact.return_value.set_result({
            'response': 'Hello! How can I assist you today?',
            'session_id': 'session1',
            'timestamp': '2023-01-01T10:00:00Z'
        })
        
        # Mock the initialized property
        digital_twin.initialized = True
        
        # Interact
        result = await digital_twin.interact(
            input_data='Hello',
            input_type='message',
            session_id='session1'
        )
        
        # Check result
        assert 'response' in result
        assert 'session_id' in result
        assert 'timestamp' in result
        
        assert result['response'] == 'Hello! How can I assist you today?'
        assert result['session_id'] == 'session1'
    
    @pytest.mark.asyncio
    async def test_create_session(self, digital_twin):
        """Test the create_session method."""
        # Mock the integration_manager's create_session method
        digital_twin.integration_manager.create_session = MagicMock(return_value=asyncio.Future())
        digital_twin.integration_manager.create_session.return_value.set_result({
            'session_id': 'session1',
            'created_at': '2023-01-01T10:00:00Z',
            'status': 'active'
        })
        
        # Mock the initialized property
        digital_twin.initialized = True
        
        # Create session
        result = await digital_twin.create_session(
            session_id='session1',
            metadata={'user_id': 'user1'}
        )
        
        # Check result
        assert 'session_id' in result
        assert 'created_at' in result
        assert 'status' in result
        
        assert result['session_id'] == 'session1'
        assert result['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_get_state(self, digital_twin):
        """Test the get_state method."""
        # Mock the integration_manager's get_twin_state method
        digital_twin.integration_manager.get_twin_state = MagicMock(return_value=asyncio.Future())
        digital_twin.integration_manager.get_twin_state.return_value.set_result({
            'personality': {
                'traits': {
                    'openness': 0.7,
                    'conscientiousness': 0.8,
                    'extraversion': 0.6,
                    'agreeableness': 0.9,
                    'neuroticism': 0.3
                }
            },
            'memory': {
                'count': 10,
                'categories': {
                    'personal': 5,
                    'factual': 3,
                    'procedural': 2
                }
            },
            'conversation': {
                'sessions': 2,
                'messages': 15
            }
        })
        
        # Mock the initialized property
        digital_twin.initialized = True
        
        # Get state
        result = await digital_twin.get_state()
        
        # Check result
        assert 'personality' in result
        assert 'memory' in result
        assert 'conversation' in result
        
        assert result['personality']['traits']['openness'] == 0.7
        assert result['memory']['count'] == 10
        assert result['conversation']['sessions'] == 2