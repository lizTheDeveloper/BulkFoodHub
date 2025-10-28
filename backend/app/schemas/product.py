"""
Product schemas for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models import ProductCategory
from app.schemas.common import BaseResponse, PaginatedResponse


class ProductImageSchema(BaseModel):
    """Product image schema."""
    id: int
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBaseSchema(BaseModel):
    """Base product schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    sku: Optional[str] = Field(None, max_length=100, description="Product SKU")
    price_per_unit: Decimal = Field(..., gt=0, description="Price per unit")
    unit_type: str = Field(..., min_length=1, max_length=20, description="Unit type (lb, kg, bag, etc.)")
    available_quantity: Decimal = Field(..., ge=0, description="Available quantity")
    minimum_order_quantity: Decimal = Field(..., gt=0, description="Minimum order quantity")
    nutritional_info: Optional[Dict[str, Any]] = Field(None, description="Nutritional information")
    ingredients: Optional[str] = Field(None, description="Product ingredients")
    allergens: Optional[str] = Field(None, description="Allergen information")
    expiration_date: Optional[datetime] = Field(None, description="Product expiration date")
    is_active: bool = Field(True, description="Whether product is active")
    is_approved: bool = Field(False, description="Whether product is approved")


class ProductCreateSchema(ProductBaseSchema):
    """Schema for creating a new product."""
    pass


class ProductUpdateSchema(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    sku: Optional[str] = Field(None, max_length=100)
    price_per_unit: Optional[Decimal] = Field(None, gt=0)
    unit_type: Optional[str] = Field(None, min_length=1, max_length=20)
    available_quantity: Optional[Decimal] = Field(None, ge=0)
    minimum_order_quantity: Optional[Decimal] = Field(None, gt=0)
    nutritional_info: Optional[Dict[str, Any]] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    expiration_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None


class ProductResponseSchema(ProductBaseSchema):
    """Schema for product response."""
    id: int
    supplier_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[ProductImageSchema] = []
    
    # Supplier information
    supplier_name: Optional[str] = None
    supplier_business_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductListResponseSchema(PaginatedResponse):
    """Schema for paginated product list response."""
    products: List[ProductResponseSchema]


class ProductSearchParams(BaseModel):
    """Parameters for product search."""
    query: Optional[str] = Field(None, description="Search query for name, description, or ingredients")
    category: Optional[ProductCategory] = Field(None, description="Filter by category")
    supplier_id: Optional[int] = Field(None, description="Filter by supplier ID")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter")
    min_quantity: Optional[Decimal] = Field(None, ge=0, description="Minimum available quantity")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_approved: Optional[bool] = Field(None, description="Filter by approval status")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower() if v else 'desc'
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'name', 'price_per_unit', 'created_at', 'updated_at', 
            'available_quantity', 'category'
        ]
        if v and v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v


class ProductBulkUploadSchema(BaseModel):
    """Schema for bulk product upload."""
    products: List[ProductCreateSchema] = Field(..., min_items=1, max_items=1000)


class ProductApprovalSchema(BaseModel):
    """Schema for product approval."""
    is_approved: bool = Field(..., description="Approval status")
    notes: Optional[str] = Field(None, description="Approval notes")


class CategoryResponseSchema(BaseModel):
    """Schema for category response."""
    name: str
    value: str
    description: Optional[str] = None
    product_count: int = 0

    class Config:
        from_attributes = True


class ProductStatsSchema(BaseModel):
    """Schema for product statistics."""
    total_products: int
    active_products: int
    approved_products: int
    pending_approval: int
    total_categories: int
    products_by_category: Dict[str, int]
    average_price: Optional[Decimal] = None
    total_inventory_value: Optional[Decimal] = None
