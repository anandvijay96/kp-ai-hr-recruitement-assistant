# Feature 1: User Creation & Authentication - Technical Implementation

**Feature ID:** F001  
**Version:** 1.0  
**Date:** 2025-10-01  

---

## 1. DATABASE DESIGN

### Migration Script: `migrations/001_create_auth_tables.sql`

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'recruiter',
    is_active BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_role CHECK (role IN ('admin', 'manager', 'recruiter'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Password history
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_password_history_user_id ON password_history(user_id);

-- Verification tokens
CREATE TABLE verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_token_type CHECK (token_type IN ('email_verification', 'password_reset'))
);

CREATE INDEX idx_verification_tokens_token_hash ON verification_tokens(token_hash);
CREATE INDEX idx_verification_tokens_user_id ON verification_tokens(user_id);

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_token ON user_sessions(session_token);

-- Activity log
CREATE TABLE user_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_status CHECK (status IN ('success', 'failure'))
);

CREATE INDEX idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX idx_user_activity_log_timestamp ON user_activity_log(timestamp);
```

---

## 2. API DESIGN

### Pydantic Models: `models/auth_schemas.py`

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum
import re

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    RECRUITER = "recruiter"

class UserRegistrationRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    mobile: Optional[str] = Field(None, min_length=10, max_length=15)

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
```

### API Endpoints: `api/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.auth_schemas import *
from services.auth_service import AuthService
from core.dependencies import get_current_user, get_auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegistrationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register new user"""
    try:
        result = await auth_service.register_user(
            full_name=user_data.full_name,
            email=user_data.email,
            mobile=user_data.mobile,
            password=user_data.password,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        return StandardResponse(success=True, message="Registration successful", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    request: Request,
    credentials: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """User login"""
    try:
        result = await auth_service.login_user(
            email=credentials.email,
            password=credentials.password,
            remember_me=credentials.remember_me,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        return StandardResponse(success=True, message="Login successful", data=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """User logout"""
    await auth_service.logout_user(current_user["id"])
    return StandardResponse(success=True, message="Logout successful")

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    await auth_service.request_password_reset(data.email, request.client.host)
    return StandardResponse(success=True, message="Password reset email sent")

@router.post("/reset-password")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password with token"""
    try:
        await auth_service.reset_password(data.token, data.new_password, request.client.host)
        return StandardResponse(success=True, message="Password reset successful")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify-email")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify email address"""
    try:
        await auth_service.verify_email(token)
        return StandardResponse(success=True, message="Email verified successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return StandardResponse(success=True, message="Profile retrieved", data=current_user)

@router.put("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update user profile"""
    try:
        result = await auth_service.update_profile(current_user["id"], data.full_name, data.mobile)
        return StandardResponse(success=True, message="Profile updated", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        await auth_service.change_password(current_user["id"], data.current_password, data.new_password)
        return StandardResponse(success=True, message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 3. SERVICE LAYER

### Password Service: `services/password_service.py`

```python
import bcrypt
import re
from typing import List, Tuple

class PasswordService:
    def __init__(self, cost_factor: int = 12):
        self.cost_factor = cost_factor
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.cost_factor)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except:
            return False
    
    def validate_password_requirements(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password meets requirements"""
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("Must contain uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Must contain lowercase letter")
        if not re.search(r'\d', password):
            errors.append("Must contain digit")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Must contain special character")
        return (len(errors) == 0, errors)
    
    def check_password_history(self, new_password: str, password_hashes: List[str]) -> bool:
        """Check if password was used before"""
        for old_hash in password_hashes:
            if self.verify_password(new_password, old_hash):
                return True
        return False
```

### Token Service: `services/token_service.py`

```python
import jwt
from datetime import datetime, timedelta
from typing import Dict, Tuple
import uuid
from core.config import settings

class TokenService:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def generate_access_token(self, user_id: str, email: str, role: str) -> Tuple[str, datetime]:
        """Generate JWT access token"""
        expiry = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": expiry,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expiry
    
    def generate_refresh_token(self, user_id: str) -> Tuple[str, datetime]:
        """Generate JWT refresh token"""
        expiry = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expiry,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expiry
    
    def validate_token(self, token: str, token_type: str = "access") -> Dict:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise ValueError(f"Invalid token type")
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                raise ValueError("Token has been revoked")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def blacklist_token(self, token: str, user_id: str) -> None:
        """Add token to blacklist"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{jti}", ttl, user_id)
        except:
            pass
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            return self.redis_client.exists(f"blacklist:{jti}") > 0
        except:
            return False
```

### Email Service: `services/email_service.py`

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.sender_email = settings.sender_email
        self.sender_name = settings.sender_name
        self.frontend_url = settings.frontend_url
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None
    
    async def send_verification_email(self, to_email: str, full_name: str, token: str) -> bool:
        """Send email verification email"""
        try:
            verification_link = f"{self.frontend_url}/verify-email?token={token}"
            subject = "Verify Your Email - HR Recruitment System"
            html_content = f"""
            <html><body>
                <h2>Welcome {full_name}!</h2>
                <p>Please verify your email address:</p>
                <a href="{verification_link}">Verify Email</a>
                <p>Link expires in 24 hours.</p>
            </body></html>
            """
            return await self._send_email(to_email, subject, html_content)
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False
    
    async def send_password_reset_email(self, to_email: str, full_name: str, token: str) -> bool:
        """Send password reset email"""
        try:
            reset_link = f"{self.frontend_url}/reset-password?token={token}"
            subject = "Reset Your Password - HR Recruitment System"
            html_content = f"""
            <html><body>
                <h2>Password Reset Request</h2>
                <p>Hi {full_name},</p>
                <p>Click below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>Link expires in 1 hour.</p>
            </body></html>
            """
            return await self._send_email(to_email, subject, html_content)
        except Exception as e:
            logger.error(f"Error sending reset email: {str(e)}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid"""
        try:
            if not self.client:
                logger.info(f"[DEV] Email to {to_email}: {subject}")
                return True
            message = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.client.send(message)
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
```

---

## 4. UI/UX DESIGN

### Registration Page: `templates/auth/register.html`

Key features:
- Real-time password strength indicator
- Client-side validation
- Toggle password visibility
- Responsive Bootstrap 5 design

### Login Page: `templates/auth/login.html`

Key features:
- Remember me checkbox
- Forgot password link
- Error message display
- Token storage in localStorage

---

## 5. INTEGRATION POINTS

### Update `core/config.py`:
```python
# Add to Settings class:
database_url: str = "postgresql+asyncpg://user:pass@localhost/hr_db"
redis_url: str = "redis://localhost:6379/0"
jwt_secret_key: str = "change-in-production"
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 15
jwt_refresh_token_expire_days: int = 7
sendgrid_api_key: Optional[str] = None
sender_email: str = "noreply@company.com"
frontend_url: str = "http://localhost:8000"
```

### Update `main.py`:
```python
from api import auth
from core.redis_client import redis_client

@app.on_event("startup")
async def startup():
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    await redis_client.disconnect()

app.include_router(auth.router)
```

---

## 6. FILE STRUCTURE

**New Files:**
```
api/auth.py
models/auth_schemas.py
models/database.py
services/auth_service.py
services/password_service.py
services/token_service.py
services/email_service.py
core/database.py
core/redis_client.py
core/dependencies.py
templates/auth/register.html
templates/auth/login.html
migrations/001_create_auth_tables.sql
tests/test_password_service.py
tests/test_token_service.py
```

**Modified Files:**
- `core/config.py` - Add auth settings
- `main.py` - Add startup/shutdown, include router
- `requirements.txt` - Add dependencies

---

## 7. TESTING STRATEGY

### Unit Tests:
- `test_password_service.py` - Hash, verify, validate
- `test_token_service.py` - Generate, validate, blacklist
- `test_email_service.py` - Email sending

### Integration Tests:
- Complete registration flow
- Login/logout flow
- Password reset flow
- Token refresh flow

### Manual Testing:
- Register → verify → login
- Failed login attempts → lockout
- Password reset end-to-end
- Session expiry

---

## 8. DEPLOYMENT CONSIDERATIONS

### Environment Variables (`.env`):
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/hr_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=<generate-secure-key>
SENDGRID_API_KEY=<your-key>
SENDER_EMAIL=noreply@company.com
FRONTEND_URL=https://yourapp.com
```

### Dependencies (`requirements.txt`):
```
PyJWT==2.8.0
bcrypt==4.1.1
email-validator==2.1.0
sendgrid==6.11.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
redis==5.0.1
```

### Migration:
```bash
# Run migration
psql -U user -d hr_db -f migrations/001_create_auth_tables.sql
```

### Generate JWT Secret:
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

**Implementation Ready** ✓
