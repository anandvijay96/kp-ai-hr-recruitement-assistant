"""FastAPI dependencies for dependency injection"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from core.database import get_db
from core.redis_client import redis_client
from services.auth_service import AuthService
from services.password_service import PasswordService
from services.token_service import TokenService
from services.email_service import EmailService
from models.database import User
from sqlalchemy import select

security = HTTPBearer()


def get_password_service() -> PasswordService:
    """Get password service instance"""
    # Use lower cost factor for development to speed up hashing
    return PasswordService(cost_factor=10)


def get_token_service() -> TokenService:
    """Get token service instance"""
    return TokenService(redis_client)


def get_email_service() -> EmailService:
    """Get email service instance"""
    return EmailService()


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
    token_service: TokenService = Depends(get_token_service),
    email_service: EmailService = Depends(get_email_service)
) -> AuthService:
    """Get auth service instance with dependencies"""
    return AuthService(db, password_service, token_service, email_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get current authenticated user from JWT token
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = token_service.validate_token(token, token_type="access")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and await token_service.is_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Fetch user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


def require_role(required_roles: list):
    """
    Dependency to check if user has required role
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
