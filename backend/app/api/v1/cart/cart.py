from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.database import get_db
from app.models import Cart, CartItem, Product, User
from app.schemas.cart import CartResponse, CartItemCreate, CartItemUpdate, CartItemResponse
from app.utils.auth import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's cart"""
    try:
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        
        if not cart:
            # Create empty cart if none exists
            cart = Cart(
                user_id=current_user.id,
                total_items=0,
                total_price=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        # Get cart items with product details
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=[CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_price=item.product.price_per_unit,
                quantity=item.quantity,
                total_price=item.total_price,
                added_at=item.added_at
            ) for item in cart_items],
            total_items=cart.total_items,
            total_price=cart.total_price,
            created_at=cart.created_at,
            updated_at=cart.updated_at
        )
    except Exception as e:
        logger.error(f"Error getting cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart"
        )

@router.post("/items", response_model=CartItemResponse)
async def add_cart_item(
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add item to cart"""
    try:
        # Get or create cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart:
            cart = Cart(
                user_id=current_user.id,
                total_items=0,
                total_price=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        # Check if product exists and is available
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.is_active == True,
            Product.is_approved == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or not available"
            )
        
        # Check available quantity
        if product.available_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.available_quantity} units available"
            )
        
        # Check if item already exists in cart
        existing_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id
        ).first()
        
        if existing_item:
            # Update existing item
            new_quantity = existing_item.quantity + item_data.quantity
            if new_quantity > product.available_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total quantity ({new_quantity}) exceeds available quantity ({product.available_quantity})"
                )
            
            existing_item.quantity = new_quantity
            existing_item.total_price = new_quantity * product.price_per_unit
            existing_item.updated_at = datetime.utcnow()
            
            cart_item = existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                id=str(uuid.uuid4()),
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=product.price_per_unit,
                total_price=item_data.quantity * product.price_per_unit,
                added_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(cart_item)
        
        # Update cart totals
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        cart.total_items = sum(item.quantity for item in cart_items)
        cart.total_price = sum(item.total_price for item in cart_items)
        cart.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(cart_item)
        
        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product.name,
            product_price=cart_item.unit_price,
            quantity=cart_item.quantity,
            total_price=cart_item.total_price,
            added_at=cart_item.added_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding cart item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )

@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: str,
    item_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update cart item quantity"""
    try:
        # Get cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Get cart item
        cart_item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        # Get product to check availability
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Validate quantity
        if item_data.quantity <= 0:
            # Remove item if quantity is 0 or negative
            db.delete(cart_item)
        else:
            if item_data.quantity > product.available_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {product.available_quantity} units available"
                )
            
            cart_item.quantity = item_data.quantity
            cart_item.total_price = item_data.quantity * cart_item.unit_price
            cart_item.updated_at = datetime.utcnow()
        
        # Update cart totals
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        cart.total_items = sum(item.quantity for item in cart_items)
        cart.total_price = sum(item.total_price for item in cart_items)
        cart.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(cart_item)
        
        if cart_item.quantity <= 0:
            return None
        
        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product.name,
            product_price=cart_item.unit_price,
            quantity=cart_item.quantity,
            total_price=cart_item.total_price,
            added_at=cart_item.added_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )

@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove item from cart"""
    try:
        # Get cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Get cart item
        cart_item = db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        # Remove item
        db.delete(cart_item)
        
        # Update cart totals
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
        cart.total_items = sum(item.quantity for item in cart_items)
        cart.total_price = sum(item.total_price for item in cart_items)
        cart.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove cart item"
        )

@router.delete("/")
async def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all items from cart"""
    try:
        # Get cart
        cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Remove all cart items
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        # Reset cart totals
        cart.total_items = 0
        cart.total_price = 0.0
        cart.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Cart cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )
