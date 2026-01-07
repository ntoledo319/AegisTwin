"""
Insights endpoints for the integrated system.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import db_manager
from core.engine import Engine
from core.models.base import InsightResponse

router = APIRouter()

# Create engine instance
engine = Engine()

@router.get("/", response_model=List[InsightResponse])
async def get_insights(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Get insights for the current user.
    """
    # This is a placeholder implementation
    # In a real implementation, we would query the database
    
    # Simulate insights
    user_id = "123e4567-e89b-12d3-a456-426614174001"
    insights = await engine.generate_insights(user_id)
    
    # Convert to InsightResponse format
    insight_responses = []
    for i, insight in enumerate(insights):
        insight_responses.append({
            "id": f"insight_{i+1}",
            "analysis_job_id": "523e4567-e89b-12d3-a456-426614174000",
            "title": insight["title"],
            "description": insight["description"],
            "category": insight["category"],
            "score": insight["score"],
            "metadata": {"source": "engine"},
            "created_at": "2023-01-03T00:15:00Z"
        })
    
    # Apply filters if provided
    if category:
        insight_responses = [i for i in insight_responses if i["category"] == category]
    if min_score:
        insight_responses = [i for i in insight_responses if i["score"] >= min_score]
    
    return insight_responses

@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: str,
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Get a specific insight by ID.
    """
    # This is a placeholder implementation
    # In a real implementation, we would query the database
    
    return {
        "id": insight_id,
        "analysis_job_id": "523e4567-e89b-12d3-a456-426614174000",
        "title": "Communication Peak Times",
        "description": "You're most responsive and engaged in communications between 9am-11am. Consider scheduling important meetings during this time.",
        "category": "productivity",
        "score": 0.92,
        "metadata": {"source": "engine"},
        "created_at": "2023-01-03T00:15:00Z"
    }

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_insight_categories(
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Get all insight categories.
    """
    # This is a placeholder implementation
    # In a real implementation, we would query the database
    
    return [
        {"id": "productivity", "name": "Productivity", "description": "Insights related to productivity and efficiency"},
        {"id": "relationships", "name": "Relationships", "description": "Insights related to personal and professional relationships"},
        {"id": "work-life-balance", "name": "Work-Life Balance", "description": "Insights related to balancing work and personal life"},
        {"id": "personal-growth", "name": "Personal Growth", "description": "Insights related to personal development and growth"},
        {"id": "communication", "name": "Communication", "description": "Insights related to communication patterns and habits"}
    ]

@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_insights(
    db: AsyncSession = Depends(db_manager.get_postgres_session)
):
    """
    Refresh insights for the current user.
    """
    # This is a placeholder implementation
    # In a real implementation, we would:
    # 1. Create a new analysis job
    # 2. Generate new insights
    
    return {
        "job_id": "723e4567-e89b-12d3-a456-426614174000",
        "status": "pending",
        "message": "Insight refresh started"
    }