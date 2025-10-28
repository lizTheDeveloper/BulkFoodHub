"""
SQLAlchemy models for BulkFoodHub.
Defines all database tables and relationships.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Numeric, Enum, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    CUSTOMER = "customer"
    WHOLESALE_BUYER = "wholesale_buyer"
    SUPPLIER = "supplier"
    ADMIN = "admin"


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ProductCategory(str, enum.Enum):
    """Product category enumeration."""
    NUTS = "nuts"
    GRAINS = "grains"
    LEGUMES = "legumes"
    DRIED_FRUITS = "dried_fruits"
    CEREALS = "cereals"


class SupplierStatus(str, enum.Enum):
    """Supplier status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class User(Base):
    """User model for all user types."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False, foreign_keys="Supplier.user_id")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
    )


class Address(Base):
    """Address model for user shipping addresses."""
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(50), nullable=False)  # Home, Work, etc.
    street_address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False, default="US")
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="shipping_address")
    
    # Indexes
    __table_args__ = (
        Index('idx_address_user', 'user_id'),
        Index('idx_address_default', 'user_id', 'is_default'),
    )


class Supplier(Base):
    """Supplier model for business suppliers."""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    business_name = Column(String(255), nullable=False)
    business_license = Column(String(100), nullable=True)
    tax_id = Column(String(50), nullable=True)
    food_safety_certification = Column(String(100), nullable=True)
    insurance_documentation = Column(String(100), nullable=True)
    bank_account_info = Column(Text, nullable=True)  # Encrypted
    business_references = Column(Text, nullable=True)  # JSON
    status = Column(Enum(SupplierStatus), default=SupplierStatus.PENDING, nullable=False)
    verification_notes = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="supplier_profile", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by], overlaps="supplier_profile")
    products = relationship("Product", back_populates="supplier", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_supplier_user', 'user_id'),
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_business_name', 'business_name'),
    )


class Product(Base):
    """Product model for bulk food items."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ProductCategory), nullable=False)
    sku = Column(String(100), nullable=True)
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    unit_type = Column(String(20), nullable=False)  # lb, kg, bag, etc.
    available_quantity = Column(Numeric(10, 2), nullable=False, default=0)
    minimum_order_quantity = Column(Numeric(10, 2), nullable=False, default=1)
    nutritional_info = Column(Text, nullable=True)  # JSON
    ingredients = Column(Text, nullable=True)
    allergens = Column(Text, nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_product_supplier', 'supplier_id'),
        Index('idx_product_category', 'category'),
        Index('idx_product_active', 'is_active'),
        Index('idx_product_approved', 'is_approved'),
        Index('idx_product_name', 'name'),
        CheckConstraint('price_per_unit > 0', name='check_positive_price'),
        CheckConstraint('available_quantity >= 0', name='check_non_negative_quantity'),
        CheckConstraint('minimum_order_quantity > 0', name='check_positive_min_order'),
    )


class ProductImage(Base):
    """Product image model."""
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="images")
    
    # Indexes
    __table_args__ = (
        Index('idx_image_product', 'product_id'),
        Index('idx_image_primary', 'product_id', 'is_primary'),
    )


class Order(Base):
    """Order model for customer orders."""
    __tablename__ = "orders"
    
    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shipping_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    billing_address_id = Column(Integer, ForeignKey("addresses.id"), nullable=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_intent_id = Column(String(255), nullable=True)  # Stripe payment intent
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    shipping_address = relationship("Address", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user', 'user_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_payment_status', 'payment_status'),
        Index('idx_order_created', 'created_at'),
        CheckConstraint('subtotal >= 0', name='check_non_negative_subtotal'),
        CheckConstraint('tax_amount >= 0', name='check_non_negative_tax'),
        CheckConstraint('shipping_cost >= 0', name='check_non_negative_shipping'),
        CheckConstraint('total_amount >= 0', name='check_non_negative_total'),
    )


class OrderItem(Base):
    """Order item model for individual products in orders."""
    __tablename__ = "order_items"
    
    id = Column(String(255), primary_key=True, index=True)
    order_id = Column(String(255), ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_product', 'product_id'),
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
        CheckConstraint('unit_price >= 0', name='check_non_negative_unit_price'),
        CheckConstraint('total_price >= 0', name='check_non_negative_total_price'),
    )


class PricingTier(Base):
    """Pricing tier model for wholesale pricing."""
    __tablename__ = "pricing_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    min_order_value = Column(Numeric(10, 2), nullable=False)
    max_order_value = Column(Numeric(10, 2), nullable=True)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_pricing_tier_active', 'is_active'),
        Index('idx_pricing_tier_range', 'min_order_value', 'max_order_value'),
        CheckConstraint('min_order_value >= 0', name='check_non_negative_min_order'),
        CheckConstraint('discount_percentage >= 0 AND discount_percentage <= 100', name='check_valid_discount'),
    )


class Cart(Base):
    """Shopping cart model for users."""
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    total_items = Column(Integer, default=0, nullable=False)
    total_price = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_cart_user', 'user_id'),
        CheckConstraint('total_items >= 0', name='check_non_negative_total_items'),
        CheckConstraint('total_price >= 0', name='check_non_negative_total_price'),
    )


class CartItem(Base):
    """Cart item model for individual products in cart."""
    __tablename__ = "cart_items"
    
    id = Column(String(255), primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_cart_item_cart', 'cart_id'),
        Index('idx_cart_item_product', 'product_id'),
        CheckConstraint('quantity > 0', name='check_positive_cart_quantity'),
        CheckConstraint('unit_price >= 0', name='check_non_negative_cart_unit_price'),
        CheckConstraint('total_price >= 0', name='check_non_negative_cart_total_price'),
    )


class AuditLog(Base):
    """Audit log model for tracking changes."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_table', 'table_name'),
        Index('idx_audit_created', 'created_at'),
    )
