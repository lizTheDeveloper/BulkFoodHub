"""
User-related schemas for profile management and user operations.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models import UserRole
from .auth import UserProfile


class AddressCreate(BaseModel):
    """Address creation schema."""
    label: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    is_default: bool = False


class AddressUpdate(BaseModel):
    """Address update schema."""
    label: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    """Address response schema."""
    id: int
    label: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithAddresses(UserProfile):
    """User profile with addresses."""
    addresses: List[AddressResponse] = []
