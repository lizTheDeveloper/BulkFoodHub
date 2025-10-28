from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ShippingAddress(BaseModel):
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    company: Optional[str] = Field(None, description="Company name")
    street_address: str = Field(..., description="Street address")
    apartment: Optional[str] = Field(None, description="Apartment, suite, etc.")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(default="US", description="Country code")
    phone: Optional[str] = Field(None, description="Phone number")

class BillingAddress(ShippingAddress):
    pass

class CheckoutRequest(BaseModel):
    shipping_address: ShippingAddress
    billing_address: BillingAddress
    payment_method: str = Field(..., description="Payment method")
    notes: Optional[str] = Field(None, description="Order notes")

class OrderItemResponse(BaseModel):
    id: str
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    created_at: datetime

class OrderCalculationResponse(BaseModel):
    subtotal: float
    tax_amount: float
    shipping_cost: float
    total_amount: float
    currency: str

class OrderResponse(BaseModel):
    id: str
    user_id: int
    status: str
    subtotal: float
    tax_amount: float
    shipping_cost: float
    total_amount: float
    currency: str
    payment_method: str
    notes: Optional[str]
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
