"""
API routes for Digital Twin interaction.

This module provides API endpoints for interacting with the Digital Twin,
including conversation, personality profile management, and memory management.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from pydantic import BaseModel, Field

from ...digital_twin import PersonalityEngine, MemorySystem, ConversationEngine

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/digital-twin",
    tags=["digital-twin"],
    responses={404: {"description": "Not found"}},
)

# Initialize Digital Twin components
# In a real implementation, these would be initialized with proper configuration
# and dependency injection
personality_engine = None
memory_system = None
conversation_engine = None


# Models for request and response
class MessageRequest(BaseModel):
    """Request model for sending a message to the Digital Twin."""
    message: str = Field(..., description="User message")
    context: Dict[str, Any] = Field(default={}, description="Conversation context")


class MessageResponse(BaseModel):
    """Response model for Digital Twin messages."""
    response: str = Field(..., description="Digital Twin response")
    context: Dict[str, Any] = Field(..., description="Updated conversation context")
    analysis: Dict[str, Any] = Field(..., description="Message analysis")


class MemoryRequest(BaseModel):
    """Request model for storing a memory."""
    memory_type: str = Field(..., description="Type of memory (episodic, semantic, procedural)")
    content: Dict[str, Any] = Field(..., description="Memory content")


class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    memory_id: str = Field(..., description="Memory ID")
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation message")


class MemoryQueryRequest(BaseModel):
    """Request model for querying memories."""
    query: Dict[str, Any] = Field(..., description="Memory query")
    limit: int = Field(default=10, description="Maximum number of results")


class MemoryQueryResponse(BaseModel):
    """Response model for memory queries."""
    memories: List[Dict[str, Any]] = Field(..., description="Retrieved memories")
    count: int = Field(..., description="Number of memories retrieved")


class PersonalityProfileResponse(BaseModel):
    """Response model for personality profile."""
    profile: Dict[str, Any] = Field(..., description="Personality profile")


# Dependency to initialize Digital Twin components
async def get_digital_twin_components():
    """
    Initialize Digital Twin components if not already initialized.
    """
    global personality_engine, memory_system, conversation_engine
    
    if personality_engine is None:
        # Initialize personality engine
        personality_engine = PersonalityEngine()
        
    if memory_system is None:
        # Initialize memory system
        memory_system = MemorySystem()
        
    if conversation_engine is None:
        # Initialize conversation engine
        conversation_engine = ConversationEngine(personality_engine, memory_system)
        
    return {
        "personality_engine": personality_engine,
        "memory_system": memory_system,
        "conversation_engine": conversation_engine
    }


# Routes for conversation
@router.post("/conversation/message", response_model=MessageResponse)
async def process_message(
    request: MessageRequest,
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Process a user message and generate a response.
    """
    try:
        # Get conversation engine
        conversation_engine = components["conversation_engine"]
        
        # Process message
        result = await conversation_engine.process_message(
            user_id=user_id,
            message=request.message,
            context=request.context
        )
        
        return MessageResponse(
            response=result["response"],
            context=result["context"],
            analysis=result["analysis"]
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/conversation/start", response_model=Dict[str, Any])
async def start_conversation(
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Start a new conversation.
    """
    try:
        # Get conversation engine
        conversation_engine = components["conversation_engine"]
        
        # Start conversation
        context = await conversation_engine.start_conversation(user_id=user_id)
        
        return context
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")


@router.post("/conversation/end")
async def end_conversation(
    user_id: str = Query(..., description="User ID"),
    context: Dict[str, Any] = Body(..., description="Conversation context"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    End a conversation.
    """
    try:
        # Get conversation engine
        conversation_engine = components["conversation_engine"]
        
        # End conversation
        await conversation_engine.end_conversation(user_id=user_id, context=context)
        
        return {"message": "Conversation ended successfully"}
    except Exception as e:
        logger.error(f"Error ending conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ending conversation: {str(e)}")


# Routes for memory management
@router.post("/memory", response_model=MemoryResponse)
async def store_memory(
    request: MemoryRequest,
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Store a memory.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Store memory
        memory_id = await memory_system.store_memory(
            user_id=user_id,
            memory_type=request.memory_type,
            content=request.content
        )
        
        return MemoryResponse(
            memory_id=memory_id,
            success=True,
            message="Memory stored successfully"
        )
    except ValueError as e:
        logger.error(f"Invalid memory request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid memory request: {str(e)}")
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing memory: {str(e)}")


@router.get("/memory/{memory_id}", response_model=Dict[str, Any])
async def get_memory(
    memory_id: str = Path(..., description="Memory ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Get a memory by ID.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Get memory
        memory = await memory_system.get_memory(memory_id=memory_id)
        
        if memory is None:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
            
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving memory: {str(e)}")


@router.put("/memory/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str = Path(..., description="Memory ID"),
    updates: Dict[str, Any] = Body(..., description="Memory updates"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Update a memory.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Update memory
        success = await memory_system.update_memory(memory_id=memory_id, updates=updates)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
            
        return MemoryResponse(
            memory_id=memory_id,
            success=True,
            message="Memory updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating memory: {str(e)}")


@router.delete("/memory/{memory_id}", response_model=MemoryResponse)
async def delete_memory(
    memory_id: str = Path(..., description="Memory ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Delete a memory.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Delete memory
        success = await memory_system.delete_memory(memory_id=memory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
            
        return MemoryResponse(
            memory_id=memory_id,
            success=True,
            message="Memory deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting memory: {str(e)}")


@router.post("/memory/query", response_model=MemoryQueryResponse)
async def query_memories(
    request: MemoryQueryRequest,
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Query memories.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Query memories
        memories = await memory_system.retrieve_memory(
            user_id=user_id,
            query=request.query,
            limit=request.limit
        )
        
        return MemoryQueryResponse(
            memories=memories,
            count=len(memories)
        )
    except Exception as e:
        logger.error(f"Error querying memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying memories: {str(e)}")


@router.post("/memory/consolidate", response_model=Dict[str, Any])
async def consolidate_memories(
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Consolidate memories for a user.
    """
    try:
        # Get memory system
        memory_system = components["memory_system"]
        
        # Consolidate memories
        results = await memory_system.consolidate_memories(user_id=user_id)
        
        return results
    except Exception as e:
        logger.error(f"Error consolidating memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consolidating memories: {str(e)}")


# Routes for personality profile
@router.get("/personality/profile", response_model=PersonalityProfileResponse)
async def get_personality_profile(
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Get a user's personality profile.
    """
    try:
        # Get personality engine
        personality_engine = components["personality_engine"]
        
        # This is a placeholder - in a real implementation, this would retrieve the profile from a database
        profile = await personality_engine._get_user_profile(user_id)
        
        return PersonalityProfileResponse(profile=profile)
    except Exception as e:
        logger.error(f"Error retrieving personality profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving personality profile: {str(e)}")


@router.post("/personality/extract", response_model=Dict[str, Any])
async def extract_personality_traits(
    user_data: Dict[str, Any] = Body(..., description="User data"),
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Extract personality traits from user data.
    """
    try:
        # Get personality engine
        personality_engine = components["personality_engine"]
        
        # Extract traits
        traits = await personality_engine.extract_traits(user_data)
        
        return {"user_id": user_id, "traits": traits}
    except Exception as e:
        logger.error(f"Error extracting personality traits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting personality traits: {str(e)}")


@router.post("/personality/create-profile", response_model=Dict[str, Any])
async def create_personality_profile(
    traits: Dict[str, Any] = Body(..., description="Personality traits"),
    user_id: str = Query(..., description="User ID"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Create a personality profile from traits.
    """
    try:
        # Get personality engine
        personality_engine = components["personality_engine"]
        
        # Create profile
        profile = await personality_engine.create_personality_profile(user_id, traits)
        
        return profile
    except Exception as e:
        logger.error(f"Error creating personality profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating personality profile: {str(e)}")


@router.put("/personality/update-profile", response_model=Dict[str, Any])
async def update_personality_profile(
    profile: Dict[str, Any] = Body(..., description="Existing personality profile"),
    new_data: Dict[str, Any] = Body(..., description="New user data"),
    components: Dict[str, Any] = Depends(get_digital_twin_components)
):
    """
    Update a personality profile with new data.
    """
    try:
        # Get personality engine
        personality_engine = components["personality_engine"]
        
        # Update profile
        updated_profile = await personality_engine.update_personality_profile(profile, new_data)
        
        return updated_profile
    except Exception as e:
        logger.error(f"Error updating personality profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating personality profile: {str(e)}")