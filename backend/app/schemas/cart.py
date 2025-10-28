from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CartItemCreate(BaseModel):
    product_id: int = Field(..., description="Product ID to add to cart")
    quantity: int = Field(..., gt=0, description="Quantity to add")

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, description="New quantity")

class CartItemResponse(BaseModel):
    id: str
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    total_price: float
    added_at: datetime

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_items: int
    total_price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
