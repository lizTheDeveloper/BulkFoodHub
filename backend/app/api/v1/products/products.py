"""
Product API endpoints for CRUD operations, search, and filtering.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from decimal import Decimal

from app.db.database import get_db
from app.models import Product, ProductImage, ProductCategory, Supplier, User
from app.schemas.product import (
    ProductCreateSchema, ProductUpdateSchema, ProductResponseSchema,
    ProductListResponseSchema, ProductSearchParams, ProductBulkUploadSchema,
    ProductApprovalSchema, CategoryResponseSchema, ProductStatsSchema
)
from app.schemas.common import BaseResponse, PaginationParams
from app.utils.auth import get_current_user, require_roles
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductListResponseSchema)
async def get_products(
    pagination: PaginationParams = Depends(),
    search_params: ProductSearchParams = Depends(),
    db: Session = Depends(get_db)
):
    """Get paginated list of products with search and filtering."""
    try:
        # Build query
        query = db.query(Product).options(
            joinedload(Product.supplier).joinedload(Supplier.user),
            joinedload(Product.images)
        )
        
        # Apply filters
        if search_params.category:
            query = query.filter(Product.category == search_params.category)
        
        if search_params.supplier_id:
            query = query.filter(Product.supplier_id == search_params.supplier_id)
        
        if search_params.min_price is not None:
            query = query.filter(Product.price_per_unit >= search_params.min_price)
        
        if search_params.max_price is not None:
            query = query.filter(Product.price_per_unit <= search_params.max_price)
        
        if search_params.min_quantity is not None:
            query = query.filter(Product.available_quantity >= search_params.min_quantity)
        
        if search_params.is_active is not None:
            query = query.filter(Product.is_active == search_params.is_active)
        
        if search_params.is_approved is not None:
            query = query.filter(Product.is_approved == search_params.is_approved)
        
        # Apply search query
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.ingredients.ilike(search_term)
                )
            )
        
        # Apply sorting
        sort_field = getattr(Product, search_params.sort_by, Product.created_at)
        if search_params.sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        products = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Format response
        product_responses = []
        for product in products:
            product_data = ProductResponseSchema.from_orm(product)
            product_data.supplier_name = f"{product.supplier.user.first_name} {product.supplier.user.last_name}"
            product_data.supplier_business_name = product.supplier.business_name
            product_responses.append(product_data)
        
        return ProductListResponseSchema.create(
            page=pagination.page,
            size=pagination.size,
            total=total,
            products=product_responses
        )
        
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products"
        )


@router.get("/{product_id}", response_model=ProductResponseSchema)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID."""
    try:
        product = db.query(Product).options(
            joinedload(Product.supplier).joinedload(Supplier.user),
            joinedload(Product.images)
        ).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product_data = ProductResponseSchema.from_orm(product)
        product_data.supplier_name = f"{product.supplier.user.first_name} {product.supplier.user.last_name}"
        product_data.supplier_business_name = product.supplier.business_name
        
        return product_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product"
        )


@router.post("/", response_model=ProductResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product (suppliers only)."""
    try:
        # Check if user is a supplier
        if not current_user.supplier_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only suppliers can create products"
            )
        
        # Create product
        product = Product(
            supplier_id=current_user.supplier_profile.id,
            **product_data.dict()
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        # Load with relationships
        product = db.query(Product).options(
            joinedload(Product.supplier).joinedload(Supplier.user),
            joinedload(Product.images)
        ).filter(Product.id == product.id).first()
        
        product_response = ProductResponseSchema.from_orm(product)
        product_response.supplier_name = f"{product.supplier.user.first_name} {product.supplier.user.last_name}"
        product_response.supplier_business_name = product.supplier.business_name
        
        logger.info(f"Product {product.id} created by supplier {current_user.id}")
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.put("/{product_id}", response_model=ProductResponseSchema)
async def update_product(
    product_id: int,
    product_data: ProductUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product (suppliers can update their own products, admins can update any)."""
    try:
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check permissions
        is_admin = current_user.role.value == "admin"
        is_owner = (current_user.supplier_profile and 
                   current_user.supplier_profile.id == product.supplier_id)
        
        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product"
            )
        
        # Update product
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        # Load with relationships
        product = db.query(Product).options(
            joinedload(Product.supplier).joinedload(Supplier.user),
            joinedload(Product.images)
        ).filter(Product.id == product.id).first()
        
        product_response = ProductResponseSchema.from_orm(product)
        product_response.supplier_name = f"{product.supplier.user.first_name} {product.supplier.user.last_name}"
        product_response.supplier_business_name = product.supplier.business_name
        
        logger.info(f"Product {product.id} updated by user {current_user.id}")
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}", response_model=BaseResponse)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product (suppliers can delete their own products, admins can delete any)."""
    try:
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check permissions
        is_admin = current_user.role.value == "admin"
        is_owner = (current_user.supplier_profile and 
                   current_user.supplier_profile.id == product.supplier_id)
        
        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product"
            )
        
        # Soft delete (set is_active to False)
        product.is_active = False
        db.commit()
        
        logger.info(f"Product {product.id} deleted by user {current_user.id}")
        return BaseResponse(message="Product deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.get("/categories/", response_model=List[CategoryResponseSchema])
async def get_categories(db: Session = Depends(get_db)):
    """Get all product categories with counts."""
    try:
        categories = []
        for category in ProductCategory:
            count = db.query(Product).filter(
                Product.category == category,
                Product.is_active == True
            ).count()
            
            categories.append(CategoryResponseSchema(
                name=category.value.replace('_', ' ').title(),
                value=category.value,
                description=f"Products in {category.value.replace('_', ' ')} category",
                product_count=count
            ))
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.get("/stats/", response_model=ProductStatsSchema)
async def get_product_stats(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Get product statistics (admin only)."""
    try:
        # Basic counts
        total_products = db.query(Product).count()
        active_products = db.query(Product).filter(Product.is_active == True).count()
        approved_products = db.query(Product).filter(Product.is_approved == True).count()
        pending_approval = db.query(Product).filter(
            Product.is_approved == False,
            Product.is_active == True
        ).count()
        
        # Category counts
        products_by_category = {}
        for category in ProductCategory:
            count = db.query(Product).filter(
                Product.category == category,
                Product.is_active == True
            ).count()
            products_by_category[category.value] = count
        
        # Price statistics
        price_stats = db.query(
            func.avg(Product.price_per_unit).label('avg_price'),
            func.sum(Product.price_per_unit * Product.available_quantity).label('total_value')
        ).filter(Product.is_active == True).first()
        
        return ProductStatsSchema(
            total_products=total_products,
            active_products=active_products,
            approved_products=approved_products,
            pending_approval=pending_approval,
            total_categories=len(ProductCategory),
            products_by_category=products_by_category,
            average_price=price_stats.avg_price,
            total_inventory_value=price_stats.total_value
        )
        
    except Exception as e:
        logger.error(f"Error fetching product stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product statistics"
        )


@router.post("/bulk-upload/", response_model=BaseResponse)
async def bulk_upload_products(
    upload_data: ProductBulkUploadSchema,
    current_user: User = Depends(require_roles(["supplier", "admin"])),
    db: Session = Depends(get_db)
):
    """Upload multiple products at once (suppliers and admins only)."""
    try:
        supplier_id = current_user.supplier_profile.id if current_user.supplier_profile else None
        if not supplier_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only suppliers and admins can upload products"
            )
        
        created_count = 0
        for product_data in upload_data.products:
            product = Product(
                supplier_id=supplier_id or product_data.supplier_id,
                **product_data.dict()
            )
            db.add(product)
            created_count += 1
        
        db.commit()
        
        logger.info(f"Bulk uploaded {created_count} products by user {current_user.id}")
        return BaseResponse(
            message=f"Successfully uploaded {created_count} products",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload products"
        )


@router.patch("/{product_id}/approve", response_model=BaseResponse)
async def approve_product(
    product_id: int,
    approval_data: ProductApprovalSchema,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """Approve or reject a product (admin only)."""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        product.is_approved = approval_data.is_approved
        db.commit()
        
        action = "approved" if approval_data.is_approved else "rejected"
        logger.info(f"Product {product.id} {action} by admin {current_user.id}")
        
        return BaseResponse(
            message=f"Product {action} successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving product {product_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve product"
        )
