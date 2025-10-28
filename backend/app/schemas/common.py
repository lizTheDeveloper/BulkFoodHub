"""
Common schemas used across the application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = datetime.utcnow()


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[dict] = None


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = 1
    size: int = 20
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    page: int
    size: int
    total: int
    pages: int
    
    @classmethod
    def create(cls, page: int, size: int, total: int, **kwargs):
        """Create a paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            **kwargs
        )
