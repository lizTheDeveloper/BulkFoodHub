"""
User management API endpoints for address management and user operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User, Address, UserRole
from app.schemas.user import AddressCreate, AddressUpdate, AddressResponse, UserWithAddresses
from app.schemas.common import BaseResponse, PaginatedResponse
from app.core.middleware import get_current_user_dependency, require_roles
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/addresses", response_model=List[AddressResponse])
async def get_user_addresses(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user's addresses."""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return [AddressResponse.from_orm(addr) for addr in addresses]


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create a new address for current user."""
    try:
        # If this is set as default, unset other defaults
        if address_data.is_default:
            db.query(Address).filter(
                Address.user_id == current_user.id,
                Address.is_default == True
            ).update({"is_default": False})
        
        # Create new address
        address = Address(
            user_id=current_user.id,
            label=address_data.label,
            street_address=address_data.street_address,
            city=address_data.city,
            state=address_data.state,
            postal_code=address_data.postal_code,
            country=address_data.country,
            is_default=address_data.is_default
        )
        
        db.add(address)
        db.commit()
        db.refresh(address)
        
        logger.info(f"Address created for user {current_user.email}: {address.label}")
        return AddressResponse.from_orm(address)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Address creation failed for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address creation failed"
        )


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_user_address(
    address_id: int,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Update a user's address."""
    try:
        # Get address
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == current_user.id
        ).first()
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # If setting as default, unset other defaults
        if address_data.is_default:
            db.query(Address).filter(
                Address.user_id == current_user.id,
                Address.is_default == True,
                Address.id != address_id
            ).update({"is_default": False})
        
        # Update address fields
        for field, value in address_data.dict(exclude_unset=True).items():
            setattr(address, field, value)
        
        db.commit()
        db.refresh(address)
        
        logger.info(f"Address updated for user {current_user.email}: {address.label}")
        return AddressResponse.from_orm(address)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Address update failed for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address update failed"
        )


@router.delete("/me/addresses/{address_id}", response_model=BaseResponse)
async def delete_user_address(
    address_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Delete a user's address."""
    try:
        # Get address
        address = db.query(Address).filter(
            Address.id == address_id,
            Address.user_id == current_user.id
        ).first()
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        # Check if this is the only address
        address_count = db.query(Address).filter(Address.user_id == current_user.id).count()
        if address_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only address"
            )
        
        db.delete(address)
        db.commit()
        
        logger.info(f"Address deleted for user {current_user.email}: {address.label}")
        return BaseResponse(message="Address deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Address deletion failed for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Address deletion failed"
        )


@router.get("/me/profile", response_model=UserWithAddresses)
async def get_user_profile_with_addresses(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user's profile with addresses."""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    address_responses = [AddressResponse.from_orm(addr) for addr in addresses]
    
    profile_data = UserWithAddresses.from_orm(current_user)
    profile_data.addresses = address_responses
    
    return profile_data


# Admin-only endpoints
@router.get("/", response_model=PaginatedResponse)
async def list_users(
    page: int = 1,
    size: int = 20,
    role: UserRole = None,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Build query
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset((page - 1) * size).limit(size).all()
        
        # Convert to response format
        user_profiles = [UserWithAddresses.from_orm(user) for user in users]
        
        return PaginatedResponse.create(
            page=page,
            size=size,
            total=total,
            data=user_profiles
        )
        
    except Exception as e:
        logger.error(f"User listing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User listing failed"
        )


@router.put("/{user_id}/activate", response_model=BaseResponse)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Activate a user account (admin only)."""
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        db.commit()
        
        logger.info(f"User activated by admin {current_user.email}: {user.email}")
        return BaseResponse(message="User activated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"User activation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User activation failed"
        )


@router.put("/{user_id}/deactivate", response_model=BaseResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.commit()
        
        logger.info(f"User deactivated by admin {current_user.email}: {user.email}")
        return BaseResponse(message="User deactivated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"User deactivation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deactivation failed"
        )
