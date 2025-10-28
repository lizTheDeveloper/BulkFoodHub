"""
API v1 router configuration.
"""

from fastapi import APIRouter
from .auth import auth_router
from .users import users_router
from .products import router as products_router

# Create main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(products_router)

__all__ = ["api_router"]
