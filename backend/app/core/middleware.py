"""
Custom middleware for authentication and request processing.
"""

from typing import Optional, List
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User, UserRole
from app.utils.auth import verify_token, get_user_from_token
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class RoleBasedAuth:
    """Role-based authentication and authorization."""
    
    def __init__(self, required_roles: Optional[List[UserRole]] = None):
        self.required_roles = required_roles or []
    
    def __call__(self, request: Request):
        """Check authentication and authorization for the request."""
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            
            # Get user from database
            db = next(get_db())
            try:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if not user:
                    raise AuthenticationError("User not found")
                
                if not user.is_active:
                    raise AuthenticationError("User account is deactivated")
                
                # Check role-based authorization
                if self.required_roles and user.role not in self.required_roles:
                    raise AuthorizationError(f"Required roles: {[role.value for role in self.required_roles]}")
                
                # Add user to request state
                request.state.user = user
                request.state.user_id = user.id
                request.state.user_role = user.role
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError("Authentication failed")


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, 'user'):
        raise AuthenticationError("User not authenticated")
    return request.state.user


def get_current_user_id(request: Request) -> int:
    """Get current authenticated user ID from request state."""
    if not hasattr(request.state, 'user_id'):
        raise AuthenticationError("User not authenticated")
    return request.state.user_id


def get_current_user_role(request: Request) -> UserRole:
    """Get current authenticated user role from request state."""
    if not hasattr(request.state, 'user_role'):
        raise AuthenticationError("User not authenticated")
    return request.state.user_role


def require_roles(*roles: UserRole):
    """Decorator to require specific roles for an endpoint."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be used with dependency injection in FastAPI
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Security scheme for OpenAPI documentation
security = HTTPBearer()


def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token."""
    token = credentials.credentials
    db = next(get_db())
    try:
        user = get_user_from_token(db, token)
        if not user:
            raise AuthenticationError("Invalid token")
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        return user
    finally:
        db.close()
