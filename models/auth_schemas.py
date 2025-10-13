"""Pydantic models for authentication"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    RECRUITER = "recruiter"


class TokenType(str, Enum):
    """Token types"""
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


# Request Models

class UserRegistrationRequest(BaseModel):
    """User registration request"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('full_name')
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v.strip()
    
    @validator('mobile')
    def validate_mobile(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('Mobile number must be between 10 and 15 digits')
        return digits
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    mobile: Optional[str] = Field(None, min_length=10, max_length=15)
    
    @validator('full_name')
    def validate_name(cls, v):
        if v and not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v.strip() if v else v
    
    @validator('mobile')
    def validate_mobile(cls, v):
        if v:
            digits = re.sub(r'\D', '', v)
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError('Mobile number must be between 10 and 15 digits')
            return digits
        return v


class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""
    email: EmailStr


# Response Models

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User response"""
    id: str
    full_name: str
    email: str
    mobile: str
    role: UserRole
    department: Optional[str]
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response"""
    success: bool
    message: str
    data: dict


class RegistrationResponse(BaseModel):
    """Registration response"""
    success: bool
    message: str
    data: dict


class StandardResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    message: str
    errors: Optional[dict] = None


class SessionInfo(BaseModel):
    """Session information"""
    id: str
    device_info: str
    ip_address: Optional[str]
    location: Optional[str]
    last_activity: datetime
    is_current: bool


class SessionsResponse(BaseModel):
    """Sessions response"""
    success: bool
    data: dict
