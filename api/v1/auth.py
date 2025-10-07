"""
Authentication and OAuth API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from models.database import get_db
from models.user import User, UserAPICredential
from services.auth_service import AuthService
from core.security import decode_access_token, credential_encryptor
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class APIKeyAdd(BaseModel):
    api_key: str
    engine_id: Optional[str] = None


# Dependency to get current user from JWT token
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # If not in header, try cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


# Auth endpoints
@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = auth_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = auth_service.create_user(
        db,
        email=user_data.email,
        name=user_data.name,
        password=user_data.password
    )
    
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = auth_service.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create token
    token = auth_service.create_user_token(user)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,  # 30 days
        samesite="lax"
    )
    
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
def logout(response: Response):
    """Logout user"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


# Google OAuth endpoints
@router.get("/google/connect")
def google_oauth_connect():
    """Initiate Google OAuth flow"""
    try:
        oauth_data = auth_service.initiate_google_oauth()
        return RedirectResponse(url=oauth_data['authorization_url'])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth not configured: {str(e)}"
        )
    except Exception as e:
        logger.error(f"OAuth initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth"
        )


@router.get("/google/callback")
def google_oauth_callback(
    code: str,
    state: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens and get/create user
        result = auth_service.handle_google_oauth_callback(db, code, state)
        
        # Set JWT cookie
        response.set_cookie(
            key="access_token",
            value=result['token'],
            httponly=True,
            max_age=30 * 24 * 60 * 60,  # 30 days
            samesite="lax"
        )
        
        # Return success page with redirect
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth Success</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }}
                .success-icon {{
                    font-size: 60px;
                    color: #4CAF50;
                }}
                h1 {{
                    color: #333;
                    margin: 20px 0;
                }}
                p {{
                    color: #666;
                    margin: 10px 0;
                }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Google Account Connected!</h1>
                <p>Welcome, {result['name'] or result['email']}</p>
                <p>You can now use your Google API quota for LinkedIn verification.</p>
                <div class="spinner"></div>
                <p>Redirecting to settings...</p>
            </div>
            <script>
                setTimeout(function() {{
                    window.location.href = '/settings';
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth failed: {str(e)}"
        )


@router.delete("/google/disconnect")
def google_oauth_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Google OAuth"""
    try:
        auth_service.remove_credentials(db, str(current_user.id))
        return {"message": "Google account disconnected successfully"}
    except Exception as e:
        logger.error(f"Failed to disconnect OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect account"
        )


# Manual API key management
@router.post("/api-keys")
def add_api_key(
    key_data: APIKeyAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add manual API key"""
    try:
        credential = auth_service.add_manual_api_key(
            db,
            str(current_user.id),
            key_data.api_key,
            key_data.engine_id
        )
        return {
            "message": "API key added successfully",
            "id": str(credential.id)
        }
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add API key"
        )


@router.get("/api-keys")
def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's API credentials (masked)"""
    credentials = db.query(UserAPICredential).filter(
        UserAPICredential.user_id == current_user.id,
        UserAPICredential.service_type == 'google_search'
    ).first()
    
    if not credentials:
        return {
            "connected": False,
            "service": "google_search"
        }
    
    # Decrypt and mask API key
    if credentials.api_key and credential_encryptor:
        try:
            decrypted_key = credential_encryptor.decrypt(credentials.api_key)
            masked_key = decrypted_key[:8] + "..." + decrypted_key[-4:] if len(decrypted_key) > 12 else "***"
        except:
            masked_key = "***"
    else:
        masked_key = None
    
    return {
        "connected": True,
        "service": "google_search",
        "oauth_connected": bool(credentials.oauth_access_token),
        "manual_key_added": bool(credentials.api_key),
        "masked_key": masked_key,
        "engine_id": credentials.api_engine_id,
        "quota_used_today": credentials.quota_used_today,
        "quota_limit": credentials.quota_limit_daily,
        "expires_at": credentials.oauth_expires_at.isoformat() if credentials.oauth_expires_at else None
    }


@router.delete("/api-keys")
def delete_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete API credentials"""
    try:
        auth_service.remove_credentials(db, str(current_user.id))
        return {"message": "API credentials removed successfully"}
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credentials"
        )
