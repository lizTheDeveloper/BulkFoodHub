"""
API v1 router configuration.
"""

from fastapi import APIRouter
from .auth import auth_router
from .users import users_router
from .products import router as products_router
from .cart.cart import router as cart_router
from .orders.orders import router as orders_router

# Create main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(products_router)
api_router.include_router(cart_router, prefix="/cart", tags=["cart"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])

__all__ = ["api_router"]
