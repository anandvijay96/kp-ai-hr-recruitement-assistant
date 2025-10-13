"""Authentication API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from models.auth_schemas import (
    UserRegistrationRequest, UserLoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, ChangePasswordRequest, UpdateProfileRequest,
    ResendVerificationRequest, LoginResponse, RegistrationResponse,
    StandardResponse
)
from services.auth_service import AuthService
from services.token_service import TokenService
from core.dependencies import get_current_user, get_auth_service, get_token_service
from core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# TEMPORARY: Remove this endpoint after setting admin
@router.post("/make-admin/{email}")
async def make_user_admin(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    TEMPORARY ENDPOINT: Make a user admin
    Remove this endpoint after use for security
    """
    from sqlalchemy import select, update
    from models.database import User
    
    try:
        # Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with email '{email}' not found"
            )
        
        # Update role
        old_role = user.role
        user.role = "admin"
        await db.commit()
        
        return {
            "success": True,
            "message": f"User {email} is now an admin",
            "old_role": old_role,
            "new_role": "admin"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user: {str(e)}"
        )
security = HTTPBearer()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegistrationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user
    
    - **full_name**: User's full name (2-100 characters)
    - **email**: Valid email address (unique)
    - **mobile**: Mobile number (10-15 digits)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **confirm_password**: Must match password
    """
    try:
        # Get client IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Register user
        result = await auth_service.register_user(
            full_name=user_data.full_name,
            email=user_data.email,
            mobile=user_data.mobile,
            password=user_data.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return RegistrationResponse(
            success=True,
            message="Registration successful! You can now login with your credentials.",
            data=result
        )
    
    except ValueError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    credentials: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password
    
    - **email**: Registered email address
    - **password**: User password
    - **remember_me**: Keep session active for longer (optional)
    """
    try:
        # Get client IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Authenticate user
        result = await auth_service.login_user(
            email=credentials.email,
            password=credentials.password,
            remember_me=credentials.remember_me,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Set refresh token as HTTP-only cookie (optional, more secure)
        if credentials.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=result["tokens"]["refresh_token"],
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data=result
        )
    
    except ValueError as e:
        logger.warning(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/refresh", response_model=StandardResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Refresh access token using refresh token
    
    Requires: Bearer token (refresh token) in Authorization header
    """
    try:
        refresh_token = credentials.credentials
        result = await token_service.refresh_access_token(refresh_token, current_user)
        
        return StandardResponse(
            success=True,
            message="Token refreshed successfully",
            data=result
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )


@router.post("/set-session", response_model=StandardResponse)
async def set_session(
    request: Request,
    session_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Set session data for page authentication
    This bridges JWT auth (for APIs) with session auth (for pages)
    """
    try:
        # Set session data
        request.session["user_id"] = session_data.get("user_id")
        request.session["user_email"] = session_data.get("user_email")
        request.session["user_name"] = session_data.get("user_name")
        request.session["user_role"] = session_data.get("user_role")
        
        return StandardResponse(
            success=True,
            message="Session set successfully"
        )
    except Exception as e:
        logger.error(f"Error setting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set session"
        )


@router.post("/logout", response_model=StandardResponse)
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service)
):
    """
    Logout current user
    
    Requires: Bearer token (access token) in Authorization header
    """
    try:
        access_token = credentials.credentials
        await token_service.blacklist_token(access_token, current_user["id"])
        
        # Clear refresh token cookie
        response.delete_cookie(key="refresh_token")
        
        # Clear session
        request.session.clear()
        
        return StandardResponse(
            success=True,
            message="Logout successful"
        )
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.post("/forgot-password", response_model=StandardResponse)
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset
    
    - **email**: Registered email address
    
    Note: Always returns success to prevent email enumeration
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        await auth_service.request_password_reset(data.email, client_ip)
        
        return StandardResponse(
            success=True,
            message="If an account exists with this email, a password reset link has been sent."
        )
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        # Still return success to prevent email enumeration
        return StandardResponse(
            success=True,
            message="If an account exists with this email, a password reset link has been sent."
        )


@router.post("/reset-password", response_model=StandardResponse)
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token from email
    - **new_password**: New password
    - **confirm_password**: Must match new_password
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        await auth_service.reset_password(
            token=data.token,
            new_password=data.new_password,
            ip_address=client_ip
        )
        
        return StandardResponse(
            success=True,
            message="Password reset successful. Please login with your new password."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset"
        )


@router.get("/verify-email", response_model=StandardResponse)
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify email address
    
    - **token**: Email verification token from registration email
    """
    try:
        await auth_service.verify_email(token)
        
        return StandardResponse(
            success=True,
            message="Email verified successfully. You can now login."
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during email verification"
        )


@router.get("/profile", response_model=StandardResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user profile
    
    Requires: Bearer token (access token) in Authorization header
    """
    return StandardResponse(
        success=True,
        message="Profile retrieved successfully",
        data=current_user
    )


@router.put("/profile", response_model=StandardResponse)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update user profile
    
    - **full_name**: New full name (optional)
    - **mobile**: New mobile number (optional)
    
    Requires: Bearer token (access token) in Authorization header
    """
    try:
        result = await auth_service.update_profile(
            user_id=current_user["id"],
            full_name=data.full_name,
            mobile=data.mobile
        )
        
        return StandardResponse(
            success=True,
            message="Profile updated successfully",
            data=result
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )


@router.post("/change-password", response_model=StandardResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password
    
    - **current_password**: Current password
    - **new_password**: New password
    - **confirm_password**: Must match new_password
    
    Requires: Bearer token (access token) in Authorization header
    """
    try:
        await auth_service.change_password(
            user_id=current_user["id"],
            current_password=data.current_password,
            new_password=data.new_password
        )
        
        return StandardResponse(
            success=True,
            message="Password changed successfully"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )
