"""
API v1 router configuration.
"""

from fastapi import APIRouter
from .auth import auth_router
from .users import users_router

# Create main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(users_router)

__all__ = ["api_router"]
