from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.database import get_db
from app.models import Order, OrderItem, Cart, CartItem, Product, User, Address
from app.schemas.orders import (
    OrderCreate, OrderResponse, OrderItemResponse, 
    OrderCalculationResponse, CheckoutRequest
)
from app.utils.auth import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/calculate", response_model=OrderCalculationResponse)
async def calculate_order(
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate order totals including tax and shipping"""
    try:
        # Get user's cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart or cart.total_items == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Get cart items with product details
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        
        # Calculate subtotal
        subtotal = sum(item.total_price for item in cart_items)
        
        # Calculate tax (8% for now)
        tax_rate = 0.08
        tax_amount = subtotal * tax_rate
        
        # Calculate shipping (free over $100, otherwise $15)
        shipping_cost = 0.0 if subtotal >= 100 else 15.0
        
        # Calculate total
        total_amount = subtotal + tax_amount + shipping_cost
        
        return OrderCalculationResponse(
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            currency="USD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate order"
        )

@router.post("/", response_model=OrderResponse)
async def create_order(
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new order from cart"""
    try:
        # Get user's cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart or cart.total_items == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Get cart items
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        
        # Validate inventory
        for cart_item in cart_items:
            product = db.query(Product).filter(Product.id == cart_item.product_id).first()
            if not product or product.available_quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient inventory for product: {product.name if product else 'Unknown'}"
                )
        
        # Calculate order totals
        subtotal = sum(item.total_price for item in cart_items)
        tax_rate = 0.08
        tax_amount = subtotal * tax_rate
        shipping_cost = 0.0 if subtotal >= 100 else 15.0
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Create shipping address
        shipping_address = Address(
            user_id=current_user.id,
            street_address=checkout_data.shipping_address.street_address,
            city=checkout_data.shipping_address.city,
            state=checkout_data.shipping_address.state,
            postal_code=checkout_data.shipping_address.postal_code,
            country=checkout_data.shipping_address.country,
            is_default=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(shipping_address)
        db.flush()
        
        # Create billing address
        billing_address = Address(
            user_id=current_user.id,
            street_address=checkout_data.billing_address.street_address,
            city=checkout_data.billing_address.city,
            state=checkout_data.billing_address.state,
            postal_code=checkout_data.billing_address.postal_code,
            country=checkout_data.billing_address.country,
            is_default=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(billing_address)
        db.flush()
        
        # Create order
        order = Order(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            status="pending",
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            currency="USD",
            shipping_address_id=shipping_address.id,
            billing_address_id=billing_address.id,
            payment_method=checkout_data.payment_method,
            notes=checkout_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()
        
        # Create order items and update inventory
        order_items = []
        for cart_item in cart_items:
            product = db.query(Product).filter(Product.id == cart_item.product_id).first()
            
            # Create order item
            order_item = OrderItem(
                id=str(uuid.uuid4()),
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total_price,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(order_item)
            order_items.append(order_item)
            
            # Update product inventory
            product.available_quantity -= cart_item.quantity
            product.updated_at = datetime.utcnow()
        
        # Clear cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        cart.total_items = 0
        cart.total_price = 0.0
        cart.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(order)
        
        # Get order items with product details for response
        order_items_with_products = []
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            order_items_with_products.append(OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                created_at=item.created_at
            ))
        
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            currency=order.currency,
            payment_method=order.payment_method,
            notes=order.notes,
            items=order_items_with_products,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's orders"""
    try:
        orders = db.query(Order).filter(
            Order.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        order_responses = []
        for order in orders:
            # Get order items
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            order_items_with_products = []
            
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                order_items_with_products.append(OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=product.name if product else "Unknown Product",
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    created_at=item.created_at
                ))
            
            order_responses.append(OrderResponse(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                shipping_cost=order.shipping_cost,
                total_amount=order.total_amount,
                currency=order.currency,
                payment_method=order.payment_method,
                notes=order.notes,
                items=order_items_with_products,
                created_at=order.created_at,
                updated_at=order.updated_at
            ))
        
        return order_responses
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders"
        )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific order details"""
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Get order items
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        order_items_with_products = []
        
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            order_items_with_products.append(OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name if product else "Unknown Product",
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                created_at=item.created_at
            ))
        
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            currency=order.currency,
            payment_method=order.payment_method,
            notes=order.notes,
            items=order_items_with_products,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order"
        )
