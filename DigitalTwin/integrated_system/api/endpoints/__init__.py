"""
API endpoints for the integrated system.
"""

from fastapi import APIRouter
from .users import router as users_router
from .data import router as data_router
from .analysis import router as analysis_router
from .insights import router as insights_router
from .digital_twin import router as digital_twin_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(data_router, prefix="/data", tags=["data"])
router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
router.include_router(insights_router, prefix="/insights", tags=["insights"])
router.include_router(digital_twin_router, prefix="/twin", tags=["digital_twin"])