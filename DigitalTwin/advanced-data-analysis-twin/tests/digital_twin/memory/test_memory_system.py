"""
Tests for the MemorySystem.

This module contains tests for the MemorySystem class and its components.
"""

import pytest
from typing import Dict, Any
import asyncio
import os

# Import the MemorySystem
from digital_twin import MemorySystem


class TestMemorySystem:
    """
    Tests for the MemorySystem class.
    """

    def test_initialization(self, memory_system):
        """
        Test that the MemorySystem initializes correctly.
        """
        assert memory_system is not None
        assert memory_system.episodic_memory is not None
        assert memory_system.semantic_memory is not None
        assert memory_system.procedural_memory is not None
        assert memory_system.memory_index is not None

    @pytest.mark.asyncio
    async def test_store_episodic_memory(self, memory_system, sample_memory_content):
        """
        Test storing an episodic memory.
        """
        user_id = "test_user_123"
        memory_type = "episodic"
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, sample_memory_content)
        
        # Check memory ID
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_store_semantic_memory(self, memory_system):
        """
        Test storing a semantic memory.
        """
        user_id = "test_user_123"
        memory_type = "semantic"
        content = {
            "concept": "Rocky Mountains",
            "definition": "A major mountain range in western North America",
            "facts": [
                "Extends from British Columbia to New Mexico",
                "Contains over 100 separate mountain ranges",
                "Highest peak is Mount Elbert at 14,440 feet"
            ],
            "categories": ["geography", "mountains", "nature"],
            "related_concepts": ["mountain range", "hiking", "national parks"]
        }
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, content)
        
        # Check memory ID
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_store_procedural_memory(self, memory_system):
        """
        Test storing a procedural memory.
        """
        user_id = "test_user_123"
        memory_type = "procedural"
        content = {
            "skill": "Setting up a tent",
            "steps": [
                "Find a flat, dry area",
                "Lay out the tent footprint",
                "Assemble the tent poles",
                "Attach the poles to the tent body",
                "Secure the tent with stakes",
                "Attach the rain fly if needed"
            ],
            "difficulty": "beginner",
            "context": "camping",
            "tools_required": ["tent", "stakes", "poles"],
            "estimated_time": "10 minutes"
        }
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, content)
        
        # Check memory ID
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_get_memory(self, memory_system, sample_memory_content):
        """
        Test retrieving a memory by ID.
        """
        user_id = "test_user_123"
        memory_type = "episodic"
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, sample_memory_content)
        
        # Get memory
        memory = await memory_system.get_memory(memory_id)
        
        # Check memory
        assert memory is not None
        assert isinstance(memory, dict)
        assert "memory_id" in memory
        assert memory["memory_id"] == memory_id
        assert "user_id" in memory
        assert memory["user_id"] == user_id
        assert "memory_type" in memory
        assert memory["memory_type"] == memory_type
        assert "title" in memory
        assert memory["title"] == sample_memory_content["title"]

    @pytest.mark.asyncio
    async def test_retrieve_memory(self, memory_system, sample_memory_content):
        """
        Test retrieving memories based on a query.
        """
        user_id = "test_user_123"
        memory_type = "episodic"
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, sample_memory_content)
        
        # Query for memories
        query = {
            "keywords": ["hiking", "mountains"]
        }
        memories = await memory_system.retrieve_memory(user_id, query)
        
        # Check memories
        assert memories is not None
        assert isinstance(memories, list)
        assert len(memories) > 0
        
        # Check first memory
        memory = memories[0]
        assert "memory_id" in memory
        assert "user_id" in memory
        assert memory["user_id"] == user_id
        assert "memory_type" in memory
        assert "title" in memory

    @pytest.mark.asyncio
    async def test_update_memory(self, memory_system, sample_memory_content):
        """
        Test updating a memory.
        """
        user_id = "test_user_123"
        memory_type = "episodic"
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, sample_memory_content)
        
        # Update memory
        updates = {
            "title": "Updated hiking trip",
            "details": "Updated details about the hiking trip"
        }
        success = await memory_system.update_memory(memory_id, updates)
        
        # Check success
        assert success is True
        
        # Get updated memory
        memory = await memory_system.get_memory(memory_id)
        
        # Check updated memory
        assert memory is not None
        assert "title" in memory
        assert memory["title"] == "Updated hiking trip"
        assert "details" in memory
        assert memory["details"] == "Updated details about the hiking trip"

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_system, sample_memory_content):
        """
        Test deleting a memory.
        """
        user_id = "test_user_123"
        memory_type = "episodic"
        
        # Store memory
        memory_id = await memory_system.store_memory(user_id, memory_type, sample_memory_content)
        
        # Delete memory
        success = await memory_system.delete_memory(memory_id)
        
        # Check success
        assert success is True
        
        # Try to get deleted memory
        memory = await memory_system.get_memory(memory_id)
        
        # Check that memory is None
        assert memory is None

    @pytest.mark.asyncio
    async def test_consolidate_memories(self, memory_system, sample_memory_content):
        """
        Test consolidating memories.
        """
        user_id = "test_user_123"
        
        # Store multiple memories
        await memory_system.store_memory(user_id, "episodic", sample_memory_content)
        await memory_system.store_memory(user_id, "episodic", {
            "title": "Second hiking trip",
            "description": "Went hiking in Yosemite National Park",
            "date": "2025-09-01",
            "location": "Yosemite National Park",
            "people": ["Alex", "Jamie", "Taylor"],
            "emotions": ["excited", "challenged", "inspired"],
            "details": "Hiked the Mist Trail to Vernal Fall. Very challenging but rewarding."
        })
        await memory_system.store_memory(user_id, "semantic", {
            "concept": "Hiking",
            "definition": "The activity of walking for long distances in the countryside",
            "facts": [
                "Hiking is a form of exercise",
                "Hiking can be done on trails or off-trail",
                "Hiking is popular in national parks"
            ],
            "categories": ["outdoor activities", "exercise", "recreation"],
            "related_concepts": ["walking", "trekking", "backpacking"]
        })
        
        # Consolidate memories
        results = await memory_system.consolidate_memories(user_id)
        
        # Check results
        assert results is not None
        assert isinstance(results, dict)
        assert "consolidated_count" in results
        assert results["consolidated_count"] >= 0