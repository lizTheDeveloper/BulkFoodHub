"""
Authentication API endpoints for user registration, login, and token management.
"""

from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models import User, UserRole
from app.schemas.auth import (
    UserRegistration, UserLogin, PasswordResetRequest, PasswordResetConfirm,
    TokenResponse, UserProfile, UserProfileUpdate, PasswordChange
)
from app.schemas.common import BaseResponse, ErrorResponse
from app.utils.auth import (
    verify_password, get_password_hash, create_tokens_for_user,
    authenticate_user, get_user_from_token
)
from app.utils.email import email_service
from app.core.middleware import get_current_user_dependency
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send welcome email
        try:
            email_service.send_welcome_email(user.email, user.first_name)
        except Exception as e:
            logger.warning(f"Failed to send welcome email to {user.email}: {str(e)}")
        
        logger.info(f"User registered successfully: {user.email}")
        return BaseResponse(
            message="User registered successfully. Please check your email for verification instructions."
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens."""
    try:
        # Authenticate user
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        # Create tokens
        tokens = create_tokens_for_user(user)
        
        logger.info(f"User logged in successfully: {user.email}")
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=30 * 60  # 30 minutes in seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        from app.utils.auth import verify_token
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        tokens = create_tokens_for_user(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=30 * 60  # 30 minutes in seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_dependency)
):
    """Get current user profile."""
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    try:
        # Update user fields
        if profile_data.first_name is not None:
            current_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            current_user.last_name = profile_data.last_name
        if profile_data.phone is not None:
            current_user.phone = profile_data.phone
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User profile updated: {current_user.email}")
        return UserProfile.from_orm(current_user)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        return BaseResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/request-password-reset", response_model=BaseResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == reset_data.email).first()
        if not user:
            # Don't reveal if email exists or not
            return BaseResponse(
                message="If the email exists, a password reset link has been sent"
            )
        
        # Generate reset token (in a real app, this would be stored in database with expiration)
        from app.utils.auth import create_access_token
        reset_token = create_access_token(
            {"sub": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # Send reset email
        try:
            email_service.send_password_reset_email(user.email, reset_token, user.first_name)
        except Exception as e:
            logger.warning(f"Failed to send password reset email to {user.email}: {str(e)}")
        
        logger.info(f"Password reset requested for: {user.email}")
        return BaseResponse(
            message="If the email exists, a password reset link has been sent"
        )
        
    except Exception as e:
        logger.error(f"Password reset request failed for {reset_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token."""
    try:
        # Verify reset token
        from app.utils.auth import verify_token
        payload = verify_token(reset_data.token, token_type="password_reset")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Update password
        user.hashed_password = get_password_hash(reset_data.new_password)
        db.commit()
        
        logger.info(f"Password reset completed for user: {user.email}")
        return BaseResponse(message="Password reset successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout_user(
    current_user: User = Depends(get_current_user_dependency)
):
    """Logout user (client should discard tokens)."""
    logger.info(f"User logged out: {current_user.email}")
    return BaseResponse(message="Logged out successfully")
